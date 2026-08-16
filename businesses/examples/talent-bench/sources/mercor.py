"""Fetch live listings from work.mercor.com."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from .common import (
    RawJob,
    bullets_from_html,
    fetch,
    infer_region,
    infer_verticals,
    job_posting_from_page,
    next_data,
    parse_json_ld_blocks,
    slugify,
    strip_html,
)

EXPLORE_URL = "https://work.mercor.com/explore"


def list_job_urls() -> list[str]:
    page = fetch(EXPLORE_URL)
    urls = []
    for block in parse_json_ld_blocks(page):
        if block.get("@type") == "ItemList":
            for item in block.get("itemListElement", []):
                url = item.get("url")
                if url:
                    urls.append(url)
    return urls


def _listing_id(url: str) -> str:
    m = re.search(r"/jobs/(list_[^/]+)/", url)
    return m.group(1) if m else url


def fetch_job(url: str, referral_url: str | None = None) -> RawJob | None:
    try:
        page = fetch(url)
    except Exception:
        return None

    ld = job_posting_from_page(page)
    nd = next_data(page)
    role = (nd or {}).get("props", {}).get("pageProps", {}).get("role", {})

    if role.get("status") not in (None, "active"):
        return None
    if role.get("deletedAt"):
        return None

    listing_id = role.get("listingId") or _listing_id(url)
    title = (ld or {}).get("title") or role.get("title") or "Mercor role"
    desc_html = (ld or {}).get("description") or ""
    desc_text = strip_html(desc_html)
    markdown_desc = role.get("description") or desc_text

    requirements = bullets_from_html(desc_html)
    if not requirements and markdown_desc:
        requirements = [
            line.lstrip("- ").strip()
            for line in markdown_desc.splitlines()
            if line.strip().startswith("-")
        ][:12]

    pay = (ld or {}).get("baseSalary", {})
    val = pay.get("value", {})
    pay_min = role.get("rateMin") or val.get("minValue")
    pay_max = role.get("rateMax") or val.get("maxValue")

    loc_req = (ld or {}).get("applicantLocationRequirements")
    region = "Worldwide"
    if isinstance(loc_req, list) and loc_req:
        region = loc_req[0].get("name", region)
    elif isinstance(loc_req, dict):
        region = loc_req.get("name", region)

    verticals = infer_verticals(title, desc_text, markdown_desc)
    region = infer_region(title, desc_text, region)

    apply = referral_url or url
    if referral_url and "referralCode" in referral_url and "?" not in url:
        apply = url  # keep direct job link; referral applied at signup

    summary_bits = []
    if pay_min or pay_max:
        lo, hi = pay_min or pay_max, pay_max or pay_min
        summary_bits.append(f"${lo:g}–${hi:g}/hr" if lo != hi else f"${lo:g}/hr")
    summary_bits.append("Remote contract")
    if "music" in title.lower() or "lyrics" in title.lower():
        summary_bits.append("Music & AI training")

    category = "Music" if "music" in verticals else "AI Training"

    return RawJob(
        source="mercor",
        source_id=listing_id,
        source_url=url,
        title=title,
        summary=f"{title}. {' · '.join(summary_bits)}.",
        description=[p for p in re.split(r"\n\s*\n", markdown_desc) if p.strip()][:6]
        or [desc_text[:500]],
        requirements=requirements,
        category=category,
        region=region,
        pay_min=pay_min,
        pay_max=pay_max,
        currency=pay.get("currency", "USD"),
        date_posted=(ld or {}).get("datePosted") or role.get("createdAt") or "",
        valid_through=(ld or {}).get("validThrough") or "",
        apply_url=apply,
        verticals=verticals,
        tags=["mercor"],
    )


def fetch_all(
    referral_url: str | None = None,
    max_workers: int = 12,
    url_keywords: list[str] | None = None,
) -> list[RawJob]:
    urls = list_job_urls()
    if url_keywords:
        keys = [k.lower() for k in url_keywords]
        urls = [u for u in urls if any(k in u.lower() for k in keys)]
    jobs: list[RawJob] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fetch_job, u, referral_url): u for u in urls}
        for fut in as_completed(futures):
            job = fut.result()
            if job:
                jobs.append(job)
    return jobs

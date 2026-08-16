"""Fetch role landing pages from outlier.ai."""

from __future__ import annotations

import re

from .common import RawJob, fetch, infer_verticals, slugify, strip_html

SITEMAP = "https://outlier.ai/sitemap.xml"
APPLY_BASE = "https://app.outlier.ai/opportunities"

# Paths that represent actual hiring funnels, not blog/legal pages.
ROLE_PREFIXES = ("/experts/", "/coding/", "/generalists/", "/content-creation")


def list_role_urls() -> list[str]:
    xml = fetch(SITEMAP)
    urls = re.findall(r"<loc>(https://outlier\.ai[^<]+)</loc>", xml)
    role_urls = []
    for url in urls:
        path = url.replace("https://outlier.ai", "")
        if any(path.startswith(p) for p in ROLE_PREFIXES):
            if "/legal/" not in path and "/blog/" not in path:
                role_urls.append(url)
    return sorted(set(role_urls))


def _pay_from_page(page: str) -> tuple[float | None, float | None]:
    m = re.search(r"\$(\d+(?:\.\d+)?)\s*(?:USD?\s*)?[/]?\s*hr", page, re.I)
    if not m:
        m = re.search(r"Earn up to \$(\d+)", page, re.I)
    if m:
        val = float(m.group(1))
        return val * 0.7, val
    m = re.search(r"\$(\d+)\s*[–-]\s*\$(\d+)", page)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


def fetch_role(url: str) -> RawJob | None:
    try:
        page = fetch(url)
    except Exception:
        return None

    title_m = re.search(r"<title>([^<|]+)", page)
    title = strip_html(title_m.group(1)) if title_m else "Outlier expert role"
    title = re.sub(r"\s*[-|].*$", "", title).strip() or "Outlier expert role"

    h1 = re.search(r"<h1[^>]*>([^<]+)", page)
    if h1:
        title = strip_html(h1.group(1))

    desc_blocks = re.findall(
        r"<p[^>]*class=\"[^\"]*(?:description|body)[^\"]*\"[^>]*>(.*?)</p>",
        page,
        re.S | re.I,
    )
    if not desc_blocks:
        desc_blocks = re.findall(r"<p[^>]*>(.*?)</p>", page, re.S)
    paragraphs = [strip_html(p) for p in desc_blocks if len(strip_html(p)) > 40][:5]
    if not paragraphs:
        meta = re.search(r'<meta name="description" content="([^"]+)"', page)
        if meta:
            paragraphs = [meta.group(1)]

    reqs = []
    for li in re.findall(r"<li[^>]*>(.*?)</li>", page, re.S)[:12]:
        text = strip_html(li)
        if len(text) > 20:
            reqs.append(text)

    pay_min, pay_max = _pay_from_page(page)
    slug = slugify(url.replace("https://outlier.ai/", ""))
    verticals = infer_verticals(title, " ".join(paragraphs))

    if "video" in url or "creator" in title.lower():
        verticals = list(set(verticals + ["video", "production"]))

    return RawJob(
        source="outlier",
        source_id=slug,
        source_url=url,
        title=title,
        summary=(paragraphs[0][:220] + "…") if paragraphs else f"Remote Outlier AI training role: {title}.",
        description=paragraphs or [f"Train frontier AI models with Outlier as a {title}."],
        requirements=reqs,
        category="Music" if "music" in verticals else "AI Training",
        pay_min=pay_min,
        pay_max=pay_max,
        apply_url=APPLY_BASE,
        verticals=verticals,
        tags=["outlier"],
    )


def fetch_all() -> list[RawJob]:
    jobs = []
    for url in list_role_urls():
        job = fetch_role(url)
        if job:
            jobs.append(job)
    return jobs

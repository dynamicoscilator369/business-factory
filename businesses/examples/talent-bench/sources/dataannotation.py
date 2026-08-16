"""Fetch open roles from dataannotation.tech."""

from __future__ import annotations

import re

from .common import RawJob, fetch, infer_verticals, slugify, strip_html

HOME = "https://dataannotation.tech"
ROLE_PATHS = [
    "/coding",
    "/generalist",
    "/law",
    "/math",
    "/medicine",
    "/physics",
    "/finance",
    "/accounting",
    "/language-directory",
    "/chemistry",
    "/biology",
]
APPLY = "https://app.dataannotation.tech/worker_signup"


def _role_from_path(path: str, page: str) -> RawJob | None:
    slug = slugify(path.strip("/") or "general")
    title_m = re.search(r"<title>([^<]+)</title>", page, re.I)
    title = strip_html(title_m.group(1)) if title_m else slug.replace("-", " ").title()
    title = re.sub(r"\s*\|\s*DataAnnotation.*", "", title, flags=re.I).strip()

    h2_roles = re.findall(r'<h3[^>]*class="[^"]*"[^>]*>([^<]+)</h3>', page)
    if h2_roles:
        title = strip_html(h2_roles[0])

    meta = re.search(r'<meta name="description" content="([^"]+)"', page)
    summary = meta.group(1) if meta else f"Remote AI training contract via DataAnnotation — {title}."

    pay_min, pay_max = None, None
    pay_m = re.search(r"\$(\d+)\s*[–-]\s*\$(\d+)", page)
    if pay_m:
        pay_min, pay_max = float(pay_m.group(1)), float(pay_m.group(2))
    else:
        pay_m = re.search(r"Starting at \$(\d+)", page, re.I)
        if pay_m:
            pay_min = float(pay_m.group(1))
            pay_max = pay_min + 25

    paragraphs = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", page, re.S):
        text = strip_html(p)
        if len(text) > 50 and "cookie" not in text.lower():
            paragraphs.append(text)
    paragraphs = paragraphs[:4]

    verticals = infer_verticals(title, summary, " ".join(paragraphs))
    if path == "/language-directory":
        verticals = list(set(verticals + ["music"]))  # bilingual roles often include Turkish

    category = "Language" if "language" in path else "AI Training"

    return RawJob(
        source="dataannotation",
        source_id=slug,
        source_url=HOME + path,
        title=f"DataAnnotation — {title}",
        summary=summary[:240],
        description=paragraphs or [summary],
        requirements=[
            "Complete a skills assessment aligned with your expertise",
            "Work remotely on a flexible schedule",
            "Strong written English; domain expertise required",
        ],
        category=category,
        pay_min=pay_min,
        pay_max=pay_max,
        apply_url=APPLY,
        verticals=verticals,
        tags=["dataannotation"],
        region="US, CA, UK, IE, AU, NZ",
    )


def fetch_all() -> list[RawJob]:
    jobs = []
    for path in ROLE_PATHS:
        try:
            page = fetch(HOME + path)
        except Exception:
            continue
        job = _role_from_path(path, page)
        if job:
            jobs.append(job)
    return jobs

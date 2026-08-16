"""Shared helpers for job source scrapers. Stdlib only."""

from __future__ import annotations

import html as html_lib
import json
import re
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (compatible; TalentBenchSync/1.0; +https://example.com/bot)"
)


@dataclass
class RawJob:
    source: str
    source_id: str
    source_url: str
    title: str
    summary: str = ""
    description: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    category: str = "Other"
    employment_type: str = "CONTRACTOR"
    remote: bool = True
    region: str = "Worldwide"
    pay_min: float | None = None
    pay_max: float | None = None
    pay_unit: str = "HOUR"
    currency: str = "USD"
    date_posted: str = ""
    valid_through: str = ""
    apply_url: str | None = None
    verticals: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: str = "active"

    def to_job_dict(self, slug: str) -> dict[str, Any]:
        posted = self.date_posted[:10] if self.date_posted else date.today().isoformat()
        valid = self.valid_through[:10] if self.valid_through else (
            date.fromisoformat(posted) + timedelta(days=90)
        ).isoformat()
        return {
            "id": slug,
            "title": self.title,
            "category": self.category,
            "employmentType": self.employment_type,
            "remote": self.remote,
            "region": self.region,
            "payMin": self.pay_min,
            "payMax": self.pay_max,
            "payUnit": self.pay_unit,
            "currency": self.currency,
            "datePosted": posted,
            "validThrough": valid,
            "summary": self.summary or self.title,
            "description": self.description or [self.summary or self.title],
            "requirements": self.requirements,
            "applyUrl": self.apply_url,
            "source": self.source,
            "sourceId": self.source_id,
            "sourceUrl": self.source_url,
            "verticals": self.verticals,
            "tags": self.tags,
        }


def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", str(s)).strip("-").lower()
    return s or "job"


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_json_ld_blocks(page_html: str) -> list[dict]:
    blocks = []
    for m in re.finditer(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
        page_html,
        re.S,
    ):
        try:
            blocks.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            continue
    return blocks


def job_posting_from_page(page_html: str) -> dict | None:
    for block in parse_json_ld_blocks(page_html):
        if block.get("@type") == "JobPosting":
            return block
    return None


def next_data(page_html: str) -> dict | None:
    m = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        page_html,
        re.S,
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def markdown_to_paragraphs(text: str) -> list[str]:
    lines = []
    for block in re.split(r"\n\s*\n", text or ""):
        block = re.sub(r"\*\*([^*]+)\*\*", r"\1", block)
        block = re.sub(r"^[-*]\s+", "", block, flags=re.M)
        block = block.strip()
        if block and not block.startswith("#"):
            lines.append(block)
    return lines[:8]


def bullets_from_html(description_html: str) -> list[str]:
    items = re.findall(r"<li[^>]*>(.*?)</li>", description_html, re.S)
    return [strip_html(x) for x in items if strip_html(x)][:12]


def infer_verticals(*texts: str, extra_keywords: list[str] | None = None) -> list[str]:
    blob = " ".join(texts).lower()
    verticals = []
    rules = {
        "music": ["music", "lyrics", "songwriter", "composer", "musician", "audio"],
        "production": ["production", "mix", "master", "studio", "sound engineer", "daw"],
        "video": ["video", "creator", "filmmaker"],
        "turkey": ["turkish", "turkey", "türkiye", "turkiye"],
    }
    if extra_keywords:
        rules["custom"] = [k.lower() for k in extra_keywords]
    for name, keys in rules.items():
        if any(k in blob for k in keys):
            verticals.append(name)
    return verticals


def infer_region(title: str, description: str, fallback: str = "Worldwide") -> str:
    blob = f"{title} {description}".lower()
    if "turkish" in blob or "turkey" in blob:
        return "Turkey"
    if "worldwide" in blob or "global" in blob:
        return "Worldwide"
    return fallback


def matches_filter(job: RawJob, keywords: list[str]) -> bool:
    if not keywords:
        return True
    blob = " ".join([
        job.title, job.summary, " ".join(job.description),
        " ".join(job.requirements), " ".join(job.verticals),
        job.region,
    ]).lower()
    return any(k.lower() in blob for k in keywords)

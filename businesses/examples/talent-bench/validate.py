#!/usr/bin/env python3
"""Check every generated job page against Google's JobPosting requirements."""
import json
import pathlib
import re
import sys

SITE = pathlib.Path(__file__).parent / "site"
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)

REQUIRED = ["title", "description", "hiringOrganization", "datePosted"]
fails = []
checked = 0

for page in sorted((SITE / "jobs").glob("*.html")):
    txt = page.read_text(encoding="utf-8")
    m = LD.search(txt)
    if not m:
        fails.append(f"{page.name}: no JSON-LD block")
        continue
    try:
        ld = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        fails.append(f"{page.name}: JSON-LD does not parse — {e}")
        continue

    checked += 1
    if ld.get("@type") != "JobPosting":
        fails.append(f"{page.name}: @type is {ld.get('@type')!r}, expected JobPosting")
    for f in REQUIRED:
        if not ld.get(f):
            fails.append(f"{page.name}: missing required field {f!r}")

    # location signal: remote roles need BOTH of these or Google drops them
    if ld.get("jobLocationType") == "TELECOMMUTE":
        if not ld.get("applicantLocationRequirements"):
            fails.append(f"{page.name}: TELECOMMUTE without applicantLocationRequirements")
    elif not ld.get("jobLocation"):
        fails.append(f"{page.name}: no jobLocation and not marked remote")

    # dates must be ISO-8601 and validThrough must be in the future relative to posted
    for f in ("datePosted", "validThrough"):
        v = ld.get(f)
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}", str(v)):
            fails.append(f"{page.name}: {f} {v!r} is not ISO-8601")
    if ld.get("validThrough") and ld["validThrough"] <= ld["datePosted"]:
        fails.append(f"{page.name}: validThrough is not after datePosted")

    if len(re.sub(r"<[^>]+>", "", ld.get("description", ""))) < 100:
        fails.append(f"{page.name}: description under 100 chars (LinkedIn/Google minimum)")

    bs = ld.get("baseSalary")
    if bs:
        val = bs.get("value", {})
        if not val.get("unitText"):
            fails.append(f"{page.name}: baseSalary missing unitText")
        if val.get("minValue") and val.get("maxValue") and val["minValue"] > val["maxValue"]:
            fails.append(f"{page.name}: baseSalary minValue > maxValue")

    # apply link must actually be present and not a placeholder
    if 'class="btn"' not in txt:
        fails.append(f"{page.name}: no apply button rendered")

# index sanity
idx = (SITE / "index.html").read_text(encoding="utf-8")
n_cards = idx.count('class="card"')
if n_cards != checked:
    fails.append(f"index.html lists {n_cards} cards but {checked} job pages exist")

sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
for page in (SITE / "jobs").glob("*.html"):
    if f"/jobs/{page.name}" not in sitemap:
        fails.append(f"sitemap.xml missing {page.name}")

print(f"Validated {checked} job pages, {n_cards} index cards.")
if fails:
    print("\nFAILURES:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("All JobPosting structured data passes Google's required-field checks.")

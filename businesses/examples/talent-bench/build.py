#!/usr/bin/env python3
"""
Static job board generator.

Reads config.json + jobs.json and writes a complete static site to ./site:

    site/index.html          searchable, filterable listing index
    site/jobs/<id>.html      one dedicated page per job, each with
                             schema.org JobPosting JSON-LD
    site/sitemap.xml         every job URL, for Search Console
    site/robots.txt

Why one page per job: Google for Jobs will only index a posting that lives at
its own crawlable URL with JobPosting structured data on it. A single-page app
that swaps jobs in JavaScript will not be indexed. That indexing is the whole
point, so the generator emits real pages.

Usage:  python3 build.py
No third-party dependencies.
"""

import html
import json
import pathlib
import re
import shutil
from datetime import date

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "site"


# ---------------------------------------------------------------- helpers

def esc(s):
    return html.escape(str(s), quote=True)


def slugify(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", str(s)).strip("-").lower()
    return s or "job"


def money(job):
    """Human-readable pay range, or None."""
    lo, hi = job.get("payMin"), job.get("payMax")
    if not lo and not hi:
        return None
    cur = {"USD": "$", "EUR": "€", "GBP": "£"}.get(job.get("currency", "USD"), "")
    unit = {"HOUR": "/hr", "DAY": "/day", "WEEK": "/wk",
            "MONTH": "/mo", "YEAR": "/yr"}.get(job.get("payUnit", "HOUR"), "")
    if lo and hi and lo != hi:
        return f"{cur}{lo:g}–{cur}{hi:g}{unit}"
    return f"{cur}{(lo or hi):g}{unit}"


def apply_url(job, cfg):
    return job.get("applyUrl") or cfg["referralUrl"]


# ------------------------------------------------------------ structured data

def job_ld(job, cfg):
    """
    schema.org JobPosting.

    Google requires: title, description, hiringOrganization, datePosted, and a
    location signal. For remote roles that signal is jobLocationType REMOTE
    plus applicantLocationRequirements -- omitting both is the single most
    common reason remote postings silently fail to index.
    """
    desc_parts = [f"<p>{esc(p)}</p>" for p in job.get("description", [])]
    reqs = job.get("requirements") or []
    if reqs:
        desc_parts.append("<p><strong>Requirements</strong></p><ul>"
                          + "".join(f"<li>{esc(r)}</li>" for r in reqs)
                          + "</ul>")

    ld = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": job["title"],
        "description": "".join(desc_parts),
        "identifier": {
            "@type": "PropertyValue",
            "name": cfg["hiringOrganization"]["name"],
            "value": job["id"],
        },
        "datePosted": job["datePosted"],
        "employmentType": job.get("employmentType", "CONTRACTOR"),
        "hiringOrganization": {
            "@type": "Organization",
            "name": cfg["hiringOrganization"]["name"],
            "sameAs": cfg["hiringOrganization"]["url"],
            "logo": cfg["hiringOrganization"].get("logo"),
        },
        "directApply": False,
    }

    if job.get("validThrough"):
        ld["validThrough"] = job["validThrough"]

    if job.get("remote", True):
        ld["jobLocationType"] = "TELECOMMUTE"
        region = job.get("region", "Worldwide")
        ld["applicantLocationRequirements"] = {
            "@type": "Country" if region.lower() != "worldwide" else "AdministrativeArea",
            "name": region,
        }
    else:
        ld["jobLocation"] = {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": job.get("city", ""),
                "addressCountry": job.get("country", ""),
            },
        }

    if job.get("payMin") or job.get("payMax"):
        lo = job.get("payMin") or job.get("payMax")
        hi = job.get("payMax") or job.get("payMin")
        ld["baseSalary"] = {
            "@type": "MonetaryAmount",
            "currency": job.get("currency", "USD"),
            "value": {
                "@type": "QuantitativeValue",
                "minValue": lo,
                "maxValue": hi,
                "unitText": job.get("payUnit", "HOUR"),
            },
        }

    return json.dumps(ld, indent=2, ensure_ascii=False)


# ------------------------------------------------------------------- styles

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --hue:HUE;
  --bg:#fbfbfd; --surface:#fff; --line:#e6e6ec;
  --ink:#16161d; --muted:#6b6b7b;
  --accent:hsl(var(--hue) 72% 52%); --accent-soft:hsl(var(--hue) 84% 96%);
  --radius:14px;
  --shadow:0 1px 2px rgba(16,16,29,.04),0 8px 24px rgba(16,16,29,.06);
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#0e0e13; --surface:#17171f; --line:#2a2a36;
    --ink:#f0f0f5; --muted:#9a9aae;
    --accent:hsl(var(--hue) 82% 68%); --accent-soft:hsl(var(--hue) 40% 18%);
    --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.35);
  }
}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
}
a{color:inherit}
.wrap{max-width:960px;margin:0 auto;padding:0 24px}

header.site{border-bottom:1px solid var(--line);background:var(--surface)}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;
  gap:16px;padding-top:20px;padding-bottom:20px;flex-wrap:wrap}
.brand{font-weight:650;letter-spacing:-.02em;font-size:18px;text-decoration:none}
.brand span{color:var(--accent)}
.hdr-note{color:var(--muted);font-size:14px}

.hero{padding:56px 0 32px}
.hero h1{font-size:clamp(30px,5vw,44px);line-height:1.1;letter-spacing:-.03em;margin:0 0 14px}
.hero p{color:var(--muted);font-size:18px;margin:0;max-width:60ch}

.controls{display:flex;gap:12px;flex-wrap:wrap;margin:28px 0 8px}
.search{flex:1 1 260px;position:relative}
.search input{
  width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:10px;
  background:var(--surface);color:var(--ink);font-size:15px;font-family:inherit;
}
.search input:focus{outline:2px solid var(--accent);outline-offset:-1px;border-color:transparent}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0 28px}
.chip{
  padding:7px 14px;border:1px solid var(--line);border-radius:999px;background:var(--surface);
  color:var(--muted);font-size:14px;cursor:pointer;font-family:inherit;transition:.15s;
}
.chip:hover{color:var(--ink);border-color:var(--muted)}
.chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:550}

.count{color:var(--muted);font-size:14px;margin-bottom:14px}

.grid{display:grid;gap:14px;padding-bottom:64px}
.card{
  display:block;text-decoration:none;background:var(--surface);border:1px solid var(--line);
  border-radius:var(--radius);padding:22px;transition:.18s;
}
.card:hover{transform:translateY(-2px);box-shadow:var(--shadow);border-color:var(--accent)}
.card h2{margin:0 0 6px;font-size:18px;letter-spacing:-.015em}
.card .sum{color:var(--muted);font-size:15px;margin:0 0 14px}
.meta{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.tag{
  font-size:12.5px;padding:4px 10px;border-radius:999px;
  background:var(--accent-soft);color:var(--accent);font-weight:550;
}
.tag.plain{background:transparent;color:var(--muted);border:1px solid var(--line);font-weight:450}
.empty{color:var(--muted);padding:48px 0;text-align:center}

/* ---- job detail ---- */
.back{display:inline-block;color:var(--muted);text-decoration:none;font-size:14px;margin:32px 0 20px}
.back:hover{color:var(--accent)}
article h1{font-size:clamp(26px,4.4vw,38px);line-height:1.15;letter-spacing:-.03em;margin:0 0 14px}
article .meta{margin-bottom:28px}
article h2{font-size:17px;margin:32px 0 10px;letter-spacing:-.01em}
article p{margin:0 0 16px;max-width:70ch}
article ul{margin:0 0 16px;padding-left:22px;max-width:70ch}
article li{margin-bottom:7px}
.apply-bar{
  position:sticky;bottom:0;background:var(--surface);border-top:1px solid var(--line);
  padding:16px 0;margin-top:44px;
}
.apply-bar .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
.btn{
  display:inline-block;background:var(--accent);color:#fff;text-decoration:none;
  padding:13px 30px;border-radius:10px;font-weight:600;font-size:15px;transition:.15s;
}
.btn:hover{filter:brightness(1.08);transform:translateY(-1px)}
.apply-note{color:var(--muted);font-size:13.5px;max-width:44ch}
.source-note{color:var(--muted);font-size:14px;margin-top:-8px}
.source-note a{color:var(--accent)}

footer.site{border-top:1px solid var(--line);padding:32px 0 48px;color:var(--muted);font-size:14px}
footer.site a{color:var(--accent)}
"""


def shell(cfg, title, description, canonical, body, head_extra=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta name="twitter:card" content="summary_large_image">
<style>{CSS.replace('HUE', str(cfg.get('accentHue', 231)))}</style>
{head_extra}
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="{esc(cfg['baseUrl'])}/">{esc(cfg['siteName'])}<span>.</span></a>
  <div class="hdr-note">{esc(cfg['tagline'])}</div>
</div></header>
{body}
<footer class="site"><div class="wrap">
  &copy; {date.today().year} {esc(cfg['hiringOrganization']['name'])} &middot;
  <a href="mailto:{esc(cfg['contactEmail'])}">{esc(cfg['contactEmail'])}</a>
</div></footer>
</body>
</html>
"""


# -------------------------------------------------------------------- pages

def build_index(cfg, jobs):
    cats = sorted({j.get("category", "Other") for j in jobs})
    chips = "".join(
        f'<button class="chip" data-cat="{esc(c)}" aria-pressed="false">{esc(c)}</button>'
        for c in cats
    )
    verticals = sorted({v for j in jobs for v in j.get("verticals", [])})
    vchips = "".join(
        f'<button class="chip" data-vert="{esc(v)}" aria-pressed="false">{esc(v.title())}</button>'
        for v in verticals
    )

    cards = []
    for j in jobs:
        tags = [f'<span class="tag">{esc(j.get("category", "Other"))}</span>']
        if j.get("source"):
            tags.append(f'<span class="tag plain">{esc(j["source"].title())}</span>')
        pay = money(j)
        if pay:
            tags.append(f'<span class="tag plain">{esc(pay)}</span>')
        if j.get("remote", True):
            tags.append('<span class="tag plain">Remote</span>')
        tags.append(f'<span class="tag plain">{esc(j.get("region", "Worldwide"))}</span>')
        for v in j.get("verticals", [])[:2]:
            tags.append(f'<span class="tag plain">{esc(v.title())}</span>')
        blob = " ".join([j["title"], j.get("summary", ""), j.get("category", ""),
                         j.get("source", ""), " ".join(j.get("verticals", [])),
                         " ".join(j.get("requirements", []))]).lower()
        vert_attr = ",".join(j.get("verticals", []))
        cards.append(
            f'<a class="card" href="jobs/{esc(j["id"])}.html" '
            f'data-cat="{esc(j.get("category", "Other"))}" data-vert="{esc(vert_attr)}" data-blob="{esc(blob)}">'
            f'<h2>{esc(j["title"])}</h2>'
            f'<p class="sum">{esc(j.get("summary", ""))}</p>'
            f'<div class="meta">{"".join(tags)}</div></a>'
        )

    body = f"""
<main class="wrap">
  <section class="hero">
    <h1>{esc(cfg['tagline'])}</h1>
    <p>{esc(cfg['description'])}</p>
  </section>

  <div class="controls">
    <div class="search">
      <input id="q" type="search" placeholder="Search roles, skills, or keywords…"
             autocomplete="off" aria-label="Search roles">
    </div>
  </div>
  <div class="chips" id="chips">
    <button class="chip" data-cat="" aria-pressed="true">All roles</button>
    {chips}
  </div>
  <div class="chips" id="vchips">
    <button class="chip" data-vert="" aria-pressed="true">All verticals</button>
    {vchips}
  </div>

  <p class="count" id="count"></p>
  <div class="grid" id="grid">
    {"".join(cards)}
  </div>
  <p class="empty" id="empty" hidden>No roles match that search.</p>
</main>

<script>
(function(){{
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var q = document.getElementById('q');
  var chips = Array.prototype.slice.call(document.querySelectorAll('#chips .chip'));
  var vchips = Array.prototype.slice.call(document.querySelectorAll('#vchips .chip'));
  var count = document.getElementById('count');
  var empty = document.getElementById('empty');
  var cat = '';
  var vert = '';

  function render(){{
    var term = q.value.trim().toLowerCase();
    var n = 0;
    cards.forEach(function(c){{
      var okCat = !cat || c.dataset.cat === cat;
      var okVert = !vert || (c.dataset.vert || '').split(',').indexOf(vert) !== -1;
      var okTerm = !term || c.dataset.blob.indexOf(term) !== -1;
      var show = okCat && okVert && okTerm;
      c.style.display = show ? '' : 'none';
      if (show) n++;
    }});
    count.textContent = n + (n === 1 ? ' open role' : ' open roles');
    empty.hidden = n !== 0;
  }}

  q.addEventListener('input', render);
  chips.forEach(function(ch){{
    ch.addEventListener('click', function(){{
      cat = ch.dataset.cat || '';
      chips.forEach(function(o){{ o.setAttribute('aria-pressed', o === ch ? 'true' : 'false'); }});
      render();
    }});
  }});
  vchips.forEach(function(ch){{
    ch.addEventListener('click', function(){{
      vert = ch.dataset.vert || '';
      vchips.forEach(function(o){{ o.setAttribute('aria-pressed', o === ch ? 'true' : 'false'); }});
      render();
    }});
  }});
  render();
}})();
</script>
"""
    return shell(cfg, f"{cfg['siteName']} — {cfg['tagline']}",
                 cfg["description"], cfg["baseUrl"] + "/", body)


def build_job(cfg, job):
    tags = [f'<span class="tag">{esc(job.get("category", "Other"))}</span>']
    pay = money(job)
    if pay:
        tags.append(f'<span class="tag plain">{esc(pay)}</span>')
    if job.get("remote", True):
        tags.append('<span class="tag plain">Remote</span>')
    tags.append(f'<span class="tag plain">{esc(job.get("region", "Worldwide"))}</span>')
    tags.append('<span class="tag plain">Contract</span>')
    if job.get("source"):
        tags.append(f'<span class="tag plain">{esc(job["source"].title())}</span>')

    paras = "".join(f"<p>{esc(p)}</p>" for p in job.get("description", []))
    source_note = ""
    if job.get("sourceUrl"):
        source_note = (
            f'<p class="source-note">Sourced from '
            f'<a href="{esc(job["sourceUrl"])}" rel="noopener" target="_blank">'
            f'{esc(job.get("source", "platform").title())}</a>. '
            f'Apply through our listing to get matched.</p>'
        )
    reqs = job.get("requirements") or []
    req_html = ""
    if reqs:
        req_html = ("<h2>What we look for</h2><ul>"
                    + "".join(f"<li>{esc(r)}</li>" for r in reqs) + "</ul>")

    url = apply_url(job, cfg)
    canonical = f"{cfg['baseUrl']}/jobs/{job['id']}.html"

    body = f"""
<main class="wrap">
  <a class="back" href="../index.html">&larr; All roles</a>
  <article>
    <h1>{esc(job['title'])}</h1>
    <div class="meta">{"".join(tags)}</div>
    {paras}
    {source_note}
    {req_html}
    <h2>How it works</h2>
    <p>Apply once and complete a short skills assessment. Once approved you are matched to
       projects that fit your background, set your own weekly hours, and are paid on a
       regular cycle for the work you complete.</p>
  </article>
</main>
<div class="apply-bar"><div class="wrap">
  <span class="apply-note">Applications are reviewed on a rolling basis.</span>
  <a class="btn" href="{esc(url)}" rel="nofollow noopener" target="_blank">Apply for this role</a>
</div></div>
"""
    head = f'<script type="application/ld+json">\n{job_ld(job, cfg)}\n</script>'
    return shell(cfg, f"{job['title']} — {cfg['siteName']}",
                 job.get("summary", ""), canonical, body, head)


def build_sitemap(cfg, jobs):
    today = date.today().isoformat()
    urls = [f"  <url><loc>{esc(cfg['baseUrl'])}/</loc><lastmod>{today}</lastmod>"
            f"<changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for j in jobs:
        urls.append(
            f"  <url><loc>{esc(cfg['baseUrl'])}/jobs/{esc(j['id'])}.html</loc>"
            f"<lastmod>{esc(j.get('datePosted', today))}</lastmod>"
            f"<changefreq>weekly</changefreq><priority>0.8</priority></url>"
        )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


# --------------------------------------------------------------------- main

def main():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    jobs = json.loads((ROOT / "jobs.json").read_text(encoding="utf-8"))
    cfg["baseUrl"] = cfg["baseUrl"].rstrip("/")

    seen = set()
    for j in jobs:
        j["id"] = slugify(j.get("id") or j["title"])
        if j["id"] in seen:
            raise SystemExit(f"Duplicate job id: {j['id']} — ids must be unique.")
        seen.add(j["id"])

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "jobs").mkdir(parents=True)

    (OUT / "index.html").write_text(build_index(cfg, jobs), encoding="utf-8")
    for j in jobs:
        (OUT / "jobs" / f"{j['id']}.html").write_text(build_job(cfg, j), encoding="utf-8")
    (OUT / "sitemap.xml").write_text(build_sitemap(cfg, jobs), encoding="utf-8")
    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {cfg['baseUrl']}/sitemap.xml\n", encoding="utf-8")

    print(f"Built {len(jobs)} job pages + index -> {OUT}")
    if "YOUR_CODE_HERE" in cfg["referralUrl"]:
        print("\n  !  referralUrl in config.json is still the placeholder.")
        print("     Every Apply button is currently a dead link. Set it before publishing.")
    if "example.com" in cfg["baseUrl"]:
        print("  !  baseUrl is still example.com — canonical URLs and the sitemap")
        print("     need your real domain or Google will not index the postings.")


if __name__ == "__main__":
    main()

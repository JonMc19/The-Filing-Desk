#!/usr/bin/env python3
"""Build The Filing Desk static site into ./docs from ./src.

Each report lives in src/reports/<slug>/ with:
  meta.json   headline, dates, summary, key figures for the home page
  body.html   the article markup
  data.json   the figures (US$ millions) used by the charts and tables
  charts.js   page-specific chart and table calls (uses assets/report.js)
"""
import csv, datetime, html, json, shutil
from pathlib import Path

ROOT = Path(__file__).parent
SRC, OUT = ROOT / "src", ROOT / "docs"  # GitHub Pages serves the docs folder
PREFIX = "/The-Filing-Desk"  # GitHub Pages project site lives under the repo name
BASE = "https://jonmc19.github.io" + PREFIX
SITE = "The Filing Desk"
REPO = "https://github.com/JonMc19/The-Filing-Desk"

MARK = ('<svg viewBox="0 0 24 20" aria-hidden="true"><path class="body" d="M1 3a2 2 0 0 1 2-2h6.2l2 2.6H21a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2z"/>'
        '<path class="line" d="M6 10.5h12M6 14h8" stroke-width="1.6" stroke-linecap="round" fill="none"/></svg>')
FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 20"><path fill="#1d4b73" d="M1 3a2 2 0 0 1 2-2h6.2l2 2.6H21a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2z"/>'
           '<path d="M6 10.5h12M6 14h8" stroke="#fff" stroke-width="1.6" stroke-linecap="round" fill="none"/></svg>\n')

def esc(s): return html.escape(s, quote=True)

def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")

def page(*, title, description, path, body, current=None, og_type="website", head_extra="", scripts=""):
    url = BASE + path
    cur = ' aria-current="page"'
    nav = "".join(
        f'<a href="{href}"{cur if current == key else ""}>{label}</a>'
        for key, href, label in (("reports", "/", "Reports"), ("about", "/about/", "About")))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta name="color-scheme" content="light dark">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="preload" href="/assets/fonts/libre-franklin-latin-800-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/source-serif-4-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css">
{head_extra}</head>
<body>
<header class="site-head">
  <div class="wrap head-in">
    <a class="wordmark" href="/">{MARK}{SITE}</a>
    <nav aria-label="Main">{nav}</nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <div><b>{SITE}</b> · Company results, read from the filings.</div>
    <div>Figures come from filings with the US Securities and Exchange Commission and from company releases. Information only, not investment advice. <a href="/about/">About and method</a></div>
  </div>
</footer>
{scripts}</body>
</html>
"""

def load_reports():
    reps = []
    for d in sorted((SRC / "reports").iterdir()):
        if (d / "meta.json").exists():
            m = json.loads((d / "meta.json").read_text())
            m["dir"] = d
            reps.append(m)
    return sorted(reps, key=lambda m: m["published"], reverse=True)

def write(rel, text):
    if rel.endswith(".html"):  # root-relative links must include the project prefix
        text = text.replace(' href="/', f' href="{PREFIX}/').replace(' src="/', f' src="{PREFIX}/')
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

ROWS = [  # (csv label, data key)
    ("Revenue", "revenue"), ("Gross profit", "gross"), ("Research and development", "rnd"),
    ("Operating income", "op_inc"), ("Other income (expense), net", "nonop"), ("Income tax", "tax"),
    ("Net income", "net_inc"), ("Diluted EPS (US$)", "eps"), ("Diluted shares (millions)", "shares"),
    ("Cash from operations", "ocf"), ("Additions to property and equipment", "capex"), ("Free cash flow", "fcf"),
    ("Dividends paid", "dividends"), ("Share buybacks", "buybacks"), ("Stock-based compensation", "sbc"),
    ("Cash and short-term investments", "cash"), ("Long-term debt incl. current portion", "debt"),
    ("Finance lease liabilities", "leases"), ("Property and equipment, net", "ppe"), ("Shareholders' equity", "equity"),
]

def build_report(m):
    d = m["dir"]
    data = json.loads((d / "data.json").read_text())
    path = f"/reports/{m['slug']}/"
    ld = {
        "@context": "https://schema.org", "@type": "Article", "headline": m["headline"],
        "description": m["description"], "datePublished": m["published"], "dateModified": m.get("updated", m["published"]),
        "author": {"@type": "Organization", "name": SITE}, "publisher": {"@type": "Organization", "name": SITE},
        "mainEntityOfPage": BASE + path, "about": {"@type": "Corporation", "name": m["legal_name"], "tickerSymbol": m["ticker"]},
    }
    head = f'<script type="application/ld+json">{json.dumps(ld)}</script>\n'
    body = f'<div class="wrap report-page">\n<article class="sheet">\n{(d / "body.html").read_text()}</article>\n</div>'
    scripts = (f'<script>window.REPORT_DATA = {json.dumps(data, separators=(",", ":"))};</script>\n'
               '<script src="/assets/report.js"></script>\n<script src="charts.js"></script>\n')
    write(f"reports/{m['slug']}/index.html", page(
        title=f"{m['seo_title']} | {SITE}", description=m["description"], path=path,
        body=body, current="reports", og_type="article", head_extra=head, scripts=scripts))
    shutil.copy(d / "charts.js", OUT / f"reports/{m['slug']}/charts.js")
    with open(OUT / f"reports/{m['slug']}/figures.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([f"{m['legal_name']} ({m['ticker']}), US$ millions unless stated; fiscal years end June 30; source: SEC EDGAR XBRL (Form 10-K)"])
        w.writerow(["Item"] + [f"FY{y}" for y in data["FY"]])
        for label, key in ROWS:
            w.writerow([label] + data[key])
    return path

def build_home(reps):
    items = []
    for m in reps:
        figs = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)} <span class="{c}">{esc(dv)}</span></dd></div>' for k, v, dv, c in m["figures"])
        items.append(f"""    <li class="rep">
      <div class="rep-meta"><span class="co">{esc(m['company'])} · {esc(m['ticker'])}</span><span>{esc(m['period'])} · {esc(m['form'])}</span><time datetime="{m['published']}">{nice_date(m['published'])}</time></div>
      <h3><a href="/reports/{m['slug']}/">{esc(m['headline'])}</a></h3>
      <p>{esc(m['summary'])}</p>
      <dl class="rep-figs">{figs}</dl>
    </li>""")
    body = f"""<div class="wrap">
  <section class="intro">
    <p class="kicker">Reports on US-listed companies</p>
    <h1>Company results, read from the filings</h1>
    <p>Each report takes a company's annual or quarterly filing with the US Securities and Exchange Commission and sets out what changed, with charts, tables and a link to every source. The reports describe results. They don't rate stocks or tell anyone what to buy.</p>
  </section>
  <h2 class="section-label">Latest reports</h2>
  <ol class="reports">
{chr(10).join(items)}
  </ol>
  <h2 class="section-label">How the reports work</h2>
  <div class="principles">
    <div><b>From the filing</b>Figures come from the company's SEC filings and its own releases. Nothing is estimated.</div>
    <div><b>Checkable</b>Each report names the filing, links the source data and offers its figures as a download.</div>
    <div><b>Descriptive</b>No price targets, ratings or recommendations. Just what the company reported and what changed.</div>
  </div>
</div>"""
    write("index.html", page(
        title=f"{SITE}: company results, read from the filings",
        description="Plain-language reports on listed companies' results, built from their SEC filings, with charts, tables and sources.",
        path="/", body=body, current="reports"))

def build_about():
    body = f"""<div class="wrap plain">
  <h1>About {SITE}</h1>
  <p>{SITE} publishes short reports on what listed companies' results show. Each one starts from the company's own filings with the US Securities and Exchange Commission (SEC), sets out what changed in the business, and links to every source.</p>

  <h2>Where the numbers come from</h2>
  <ul>
    <li>Annual and quarterly reports (Forms 10-K and 10-Q) filed with the SEC, taken from the structured XBRL data on <a href="https://www.sec.gov/search-filings" rel="noopener">EDGAR</a>.</li>
    <li>Company earnings releases, for items the filings don't break out.</li>
  </ul>
  <p>When a later filing restates an earlier year, the reports use the latest figure the company filed.</p>

  <h2>How figures are calculated</h2>
  <ul>
    <li>Free cash flow is net cash from operating activities minus additions to property and equipment.</li>
    <li>Margins are the item divided by revenue for the same period.</li>
    <li>Years are the company's fiscal years, which may not match calendar years.</li>
  </ul>
  <p>Each report lists any other definitions it uses.</p>

  <h2>What the reports don't do</h2>
  <p>They don't cover share prices, valuation or analyst forecasts, and they don't rate stocks or recommend buying, selling or holding anything. They describe what companies reported.</p>

  <h2>Corrections</h2>
  <p>If a figure doesn't match the filing, <a href="{REPO}/issues" rel="noopener">open an issue on the site's GitHub page</a>. Confirmed errors are corrected in the report, with a note saying what changed.</p>

  <h2>Disclaimer</h2>
  <p>Everything on this site is for information only. It is not investment advice or a recommendation to buy, sell or hold any security. Figures may contain errors, so check the original filings before relying on them. {SITE} is not affiliated with the SEC or with any company it covers.</p>
</div>"""
    write("about/index.html", page(
        title=f"About {SITE}", description=f"What {SITE} publishes, where its figures come from and how they are calculated.",
        path="/about/", body=body, current="about"))

def build_404():
    body = """<div class="wrap plain">
  <h1>Page not found</h1>
  <p>That page doesn't exist or has moved. <a href="/">Go to the latest reports</a>.</p>
</div>"""
    write("404.html", page(title=f"Page not found | {SITE}", description="Page not found.", path="/404.html", body=body))

def main():
    if OUT.exists():
        for p in OUT.iterdir():
            if p.name == ".git":
                continue
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    OUT.mkdir(exist_ok=True)
    shutil.copytree(SRC / "assets", OUT / "assets", dirs_exist_ok=True)
    reps = load_reports()
    paths = [("/", max(m["published"] for m in reps)), ("/about/", None)]
    for m in reps:
        paths.append((build_report(m), m.get("updated", m["published"])))
    build_home(reps)
    build_about()
    build_404()
    write("favicon.svg", FAVICON)
    write(".nojekyll", "")
    urls = "".join(f"  <url><loc>{BASE}{p}</loc>{f'<lastmod>{lm}</lastmod>' if lm else ''}</url>\n" for p, lm in paths)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    print(f"built {len(reps)} report(s) into {OUT}")

if __name__ == "__main__":
    main()

"""Synthetic journal-style layouts used by the tests (no copyrighted content).

Each page has: a header and footer (must stay visible), an <article> with text and a
wide figure (must stay visible and get wider), and zero or more sidebars marked
data-sidebar (must be hidden).
"""

PARA = (
    "Kidney organoids recapitulate several aspects of nephron development, yet their "
    "maturation remains incomplete. Here we profile thousands of single cells across "
    "differentiation time points and identify transcriptional programs associated with "
    "podocyte and tubular specification. We further show that perturbing these programs "
    "alters segment proportions, suggesting routes to more faithful in vitro models. "
)

ARTICLE = f"""
<article id="article">
  <h1>A synthetic article for layout testing</h1>
  <p class="authors">A. Author, B. Author &amp; C. Author</p>
  <h2>Abstract</h2>
  {''.join(f'<p>{PARA * 2}</p>' for _ in range(3))}
  <figure id="fig1">
    <img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='2000' height='800'><rect width='2000' height='800' fill='%2399c'/></svg>" width="2000" height="800" alt="Figure 1">
    <figcaption>Figure 1. A deliberately oversized figure (2000 px wide).</figcaption>
  </figure>
  <h2>Results</h2>
  {''.join(f'<p>{PARA * 3}</p>' for _ in range(6))}
</article>
"""

SIDEBAR = """<aside data-sidebar id="{id}" style="{style}">
  <h3>Related articles</h3><ul><li>Something else</li><li>Another thing</li></ul>
  <a href="#">Download PDF</a>
</aside>"""

NAV = """<nav data-sidebar id="{id}" style="{style}">
  <h3>Contents</h3><ol><li>Abstract</li><li>Results</li><li>Methods</li></ol>
</nav>"""

HEAD = """<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{margin:0;font:16px/1.5 Arial,sans-serif}} header,footer{{background:#eee;padding:16px}}
img{{max-width:100%;height:auto}}</style></head><body>
<header id="header"><b>Journal of Testing</b> &middot; <a href="#">Log in</a></header>"""
FOOT = """<footer id="footer">&copy; Journal of Testing</footer></body></html>"""


def page(title, body):
    return HEAD.format(title=title) + body + FOOT


LAYOUTS = {
    # Nature-style: flex container, main column + right sidebar
    "flex-right": page("flex-right", f"""
      <div style="display:flex;gap:32px;max-width:1280px;margin:0 auto;padding:0 16px">
        <main style="flex:0 0 66%">{ARTICLE}</main>
        {SIDEBAR.format(id="side", style="flex:0 0 30%")}
      </div>"""),
    # PMC/Cell-style: left table-of-contents nav
    "flex-left": page("flex-left", f"""
      <div style="display:flex;gap:24px;max-width:1280px;margin:0 auto">
        {NAV.format(id="toc", style="flex:0 0 220px")}
        <div style="flex:1;max-width:760px">{ARTICLE}</div>
      </div>"""),
    # CSS grid with TOC on the left and extras on the right
    "grid-3col": page("grid-3col", f"""
      <div style="display:grid;grid-template-columns:200px minmax(0,720px) 280px;gap:24px;justify-content:center">
        {NAV.format(id="toc", style="")}
        <main>{ARTICLE}</main>
        {SIDEBAR.format(id="side", style="")}
      </div>"""),
    # Old-school floats
    "float": page("float", f"""
      <div style="width:1200px;margin:0 auto;overflow:hidden">
        <div style="float:left;width:65%">{ARTICLE}</div>
        {SIDEBAR.format(id="side", style="float:right;width:30%")}
      </div>"""),
    # Sidebar nested a few levels deep (wrapper divs around both columns)
    "nested": page("nested", f"""
      <div class="outer" style="max-width:1200px;margin:0 auto"><div class="row" style="display:flex">
        <div class="col-main" style="width:70%"><div class="inner"><div>{ARTICLE}</div></div></div>
        <div class="col-side" style="width:30%"><div>{SIDEBAR.format(id="side", style="")}</div></div>
      </div></div>"""),
    # Single column, nothing to hide
    "no-sidebar": page("no-sidebar", f"""
      <div style="max-width:720px;margin:0 auto">{ARTICLE}</div>"""),
    # Sidebar that appears 800 ms after load (ads / "related content" widgets)
    "late-sidebar": page("late-sidebar", f"""
      <div id="row" style="display:flex;max-width:1280px;margin:0 auto">
        <main style="flex:0 0 66%">{ARTICLE}</main>
      </div>
      <script>setTimeout(() => document.getElementById('row').insertAdjacentHTML('beforeend',
        `{SIDEBAR.format(id="side", style="flex:0 0 30%")}`), 800);</script>"""),
    # ScienceDirect-style: body paragraphs are <div>s, while the "recommended
    # articles" sidebar uses <p> abstracts (so a <p>-only heuristic picks the sidebar)
    "div-paragraphs": page("div-paragraphs", """
      <div class="Article" style="display:flex;max-width:1280px;margin:0 auto;gap:24px">
        <div class="center" style="flex:0 0 62%">
          <div id="article">
            <h1>A synthetic article for layout testing</h1>
            <div class="abstract"><h2>Abstract</h2><div class="u-margin-s-bottom">""" + PARA * 2 + """</div></div>
            <section><h2>Introduction</h2>""" + "".join(f'<div class="u-margin-s-bottom">{PARA * 2}</div>' for _ in range(4)) + """</section>
            <figure id="fig1"><img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='2000' height='800'><rect width='2000' height='800' fill='%2399c'/></svg>" width="2000" height="800" alt=""><figcaption>Figure 1.</figcaption></figure>
            <section><h2>Results</h2>""" + "".join(f'<div class="u-margin-s-bottom">{PARA * 2}</div>' for _ in range(4)) + """</section>
          </div>
        </div>
        <div data-sidebar id="side" class="rhs" style="flex:0 0 34%">
          <h3>Recommended articles</h3>""" + "".join(f'<p>{PARA}</p>' for _ in range(6)) + """
        </div>
      </div>"""),
    # eLife-style named-area grid (grid-template-areas defines extra columns)
    "grid-areas": page("grid-areas", f"""
      <div style="display:grid;grid-template-columns:repeat(12,1fr);gap:24px;max-width:1344px;margin:0 auto;
                  grid-template-areas:'main main main main main main main main side side side side'">
        <div style="grid-area:main">{ARTICLE}</div>
        {SIDEBAR.format(id="side", style="grid-area:side")}
      </div>"""),
    # Frontiers-style sticky action rail that only appears after the first pass
    "late-floating-rail": page("late-floating-rail", f"""
      <div style="max-width:1280px;margin:0 auto;padding:0 60px;position:relative">
        <main style="width:75%">{ARTICLE}</main>
      </div>
      <script>setTimeout(() => document.body.insertAdjacentHTML('beforeend',
        `<div data-sidebar id="rail" style="position:fixed;top:150px;right:130px;width:96px;height:380px;
          background:#fff;border:1px solid #ccc;border-radius:12px"><div>PDF</div><div>Cite</div></div>`), 2500);</script>"""),
}

SIDEBAR_LAYOUTS = [k for k in LAYOUTS if k not in ("no-sidebar",)]

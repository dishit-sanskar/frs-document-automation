"""Capture ERPNext list / form screenshots and render Excel-style report mockups for an FRS.

Usage:
    FRAPPE_USER=Administrator FRAPPE_PASSWORD=*** python capture.py <frs_content.py> --out <shots_dir>
        [--base-url http://localhost:8000] [--only screens|mockups] [--keys 2.4,2.7]

Reads SCREENS and REPORTS from the content file (see examples/washing/frs_content.py). Output names:
    <key>-a-<doctype-slug>-list.png, <key>-b-<doctype-slug>-form.png, <report no>-report-mockup.png
"""
import argparse
import html
import json
import os
import runpy
import urllib.parse

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("content")
ap.add_argument("--out", required=True)
ap.add_argument("--base-url", default=os.getenv("FRAPPE_URL", "http://localhost:8000"))
ap.add_argument("--only", choices=["screens", "mockups"])
ap.add_argument("--keys", help="comma-separated screen keys / report numbers to (re)capture")
ap.add_argument("--channel", default="chrome", help="'chrome' uses installed Google Chrome; '' uses Playwright's Chromium")
a = ap.parse_args()

C = runpy.run_path(a.content)
SCREENS, REPORTS = C.get("SCREENS", []), C.get("REPORTS", [])
KEYS = set(a.keys.split(",")) if a.keys else None
os.makedirs(a.out, exist_ok=True)
HIDE = ".body-sidebar-container,.form-footer{display:none!important}"


def slug(dt):
	return dt.lower().replace(" ", "-")


# ------------------------------------------------------------------ report mockups
def fmt(v):
	if isinstance(v, bool):
		return "Yes" if v else ""
	if isinstance(v, int):
		return f"{v:,}"
	if isinstance(v, float):
		return f"{v:,.3f}".rstrip("0").rstrip(".") if v % 1 else f"{v:,.0f}"
	return html.escape(str(v))


def is_num(v):
	return isinstance(v, (int, float)) or (isinstance(v, str) and v.replace(",", "").replace(".", "").replace("%", "").isdigit())


def mockup_html(r):
	"""Excel look: column letters, row numbers, orange code cell + title, italic filter row, yellow header & total.

	Report keys: code, name, filters, cols, rows, optional head_rows (label rows above the header), group_row
	(band above the header), total (sum numeric columns), flag (KPI style: column 2 is the objective, higher = red),
	no_total_cols (column names never summed). A cell value "Yes" is shown in red.
	"""
	cols, n = r["cols"], len(r["cols"])
	out, rn = [], 0

	def row(cells, cls=""):
		nonlocal rn
		rn += 1
		out.append(f'<tr class="{cls}"><td class="rn">{rn}</td>{cells}</tr>')

	row(f'<td class="code" colspan="2">{html.escape(r["code"])}</td><td class="title" colspan="{n - 2}">{html.escape(r["name"].upper())}</td>')
	row(f'<td class="filt" colspan="{n}">Filters: {html.escape(r["filters"])}</td>')
	for hr in r.get("head_rows", []):
		row("".join(f'<td class="{"lbl" if i == 0 else "hv"}">{html.escape(str(c))}</td>' for i, c in enumerate(hr)))
	if r.get("group_row"):
		row("".join(f'<td class="grp">{html.escape(c)}</td>' for c in r["group_row"]))
	row("".join(f"<th>{html.escape(c)}</th>" for c in cols))
	for data in r["rows"]:
		cells = []
		for i, v in enumerate(data):
			cls = "num" if i and is_num(v) else ""
			if r.get("flag") and i >= 3 and data[2] not in ("", None):
				try:
					if float(str(v).replace("%", "").replace(",", "")) > float(str(data[2]).replace("%", "").replace(",", "").split("–")[-1]):
						cls += " bad"
				except ValueError:
					pass
			if v == "Yes":
				cls += " bad"
			cells.append(f'<td class="{cls}">{fmt(v)}</td>')
		row("".join(cells))
	if r.get("total"):
		skip = {c.lower() for c in r.get("no_total_cols", [])}
		tot = []
		for i in range(n):
			vals = [d[i] for d in r["rows"]]
			if i == 0:
				tot.append("Total")
			elif all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals) and cols[i].lower() not in skip:
				s = sum(vals)
				tot.append(fmt(round(s, 3) if isinstance(s, float) else s))
			else:
				tot.append("")
		row("".join(f'<td class="{"num" if i else ""}">{t}</td>' for i, t in enumerate(tot)), "tot")
	head = '<tr><td class="hd"></td>' + "".join(f'<td class="hd">{chr(65 + i)}</td>' for i in range(n)) + "</tr>"
	return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:#fff;font-family:Calibri,Carlito,'Liberation Sans',Arial,sans-serif}}
table{{border-collapse:collapse;font-size:15px}} td,th{{border:1px solid #bfbfbf;padding:6px 10px;white-space:nowrap}}
.hd,.rn{{background:#f2f2f2;color:#555;text-align:center;font-size:13px}} .rn{{width:28px}}
.code{{background:#f4b183;font-weight:bold;text-align:center;font-size:17px}} .title{{font-weight:bold;text-align:center;font-size:19px}}
.filt{{font-style:italic;color:#444}} th{{background:#fff2cc;font-weight:bold}}
.lbl{{font-weight:bold;background:#f2f2f2}} .hv{{background:#fafafa}} .grp{{background:#dde8f5;font-weight:bold;text-align:center;font-size:13px}}
.num{{text-align:right}} .bad{{color:#c00000;font-weight:bold}} .tot td{{background:#fff2cc;font-weight:bold;border-top:2px solid #777}}
</style></head><body><table>{head}{''.join(out)}</table></body></html>"""


# ------------------------------------------------------------------ desk screenshots
def resolve(ctx, s):
	if s.get("single") or s.get("record"):
		return s.get("record")
	q = urllib.parse.urlencode({"filters": json.dumps(s.get("filters", {})), "order_by": "creation asc", "limit_page_length": 1})
	r = ctx.request.get(f"{a.base_url}/api/resource/{urllib.parse.quote(s['doctype'])}?{q}")
	data = r.json().get("data", [])
	if not data:
		raise SystemExit(f"No {s['doctype']} record matches {s.get('filters')} — seed dummy data first")
	return data[0]["name"]


def full_height_shot(page, path):
	page.add_style_tag(content=HIDE)
	page.mouse.move(5, 5)
	page.wait_for_timeout(400)
	# Frappe desk scrolls inside .main-section, so full_page=True only captures the viewport.
	h = page.evaluate("(document.querySelector('.main-section')||document.body).scrollHeight")
	page.set_viewport_size({"width": 1440, "height": max(900, h)})
	page.wait_for_timeout(800)
	page.screenshot(path=path)
	page.set_viewport_size({"width": 1440, "height": 900})


with sync_playwright() as p:
	try:
		browser = p.chromium.launch(channel=a.channel or None, headless=True)
	except Exception:
		browser = p.chromium.launch(headless=True)
	ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
	page = ctx.new_page()

	if a.only in (None, "mockups"):
		for r in REPORTS:
			if KEYS and r["no"] not in KEYS:
				continue
			tmp = os.path.abspath(os.path.join(a.out, f".{r['no']}.html"))
			open(tmp, "w").write(mockup_html(r))
			page.set_viewport_size({"width": 2600, "height": 600})
			page.goto(f"file://{tmp}")
			page.locator("table").screenshot(path=os.path.join(a.out, f"{r['no']}-report-mockup.png"))
			os.remove(tmp)
			print("mockup", r["no"], r["name"])
		page.set_viewport_size({"width": 1440, "height": 900})

	if a.only in (None, "screens"):
		user, pwd = os.getenv("FRAPPE_USER", "Administrator"), os.getenv("FRAPPE_PASSWORD")
		if not pwd:
			raise SystemExit("Set FRAPPE_PASSWORD (and FRAPPE_USER if not Administrator)")
		# API login works across Frappe versions; the /login form selectors differ between v14 / v15 / v16.
		res = ctx.request.post(f"{a.base_url}/api/method/login", data={"usr": user, "pwd": pwd})
		if not res.ok:
			raise SystemExit(f"Login failed: {res.status} {res.text()[:200]}")
		for s in SCREENS:
			if KEYS and s["key"] not in KEYS:
				continue
			sl = slug(s["doctype"])
			if s.get("list"):
				page.goto(f"{a.base_url}/app/{sl}")
				page.wait_for_selector(".frappe-list .result, .no-result", timeout=30000)
				page.wait_for_timeout(2200)
				page.add_style_tag(content=HIDE)
				page.wait_for_timeout(400)
				page.screenshot(path=os.path.join(a.out, f"{s['key']}-a-{sl}-list.png"))
			rec = resolve(ctx, s)
			page.goto(f"{a.base_url}/app/{sl}" + ("" if s.get("single") else f"/{urllib.parse.quote(rec)}"))
			page.wait_for_selector(".form-layout", timeout=30000)
			page.wait_for_timeout(2500)
			for sec in s.get("expand", []):
				page.locator(f".section-head:has-text('{sec}')").first.click()
				page.wait_for_timeout(400)
			full_height_shot(page, os.path.join(a.out, f"{s['key']}-b-{sl}-form.png"))
			print("screen", s["key"], s["doctype"], rec or "")
	browser.close()

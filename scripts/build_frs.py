"""Build a Sanskar Technolab FRS (.docx + .pdf) from a content file, screenshots and the FRS template.

Usage:
    python build_frs.py <frs_content.py> --shots <shots_dir> --out "<dir>/<Client>-<Module>-FRS-V1.0.docx"
        [--template ../templates/sanskar_frs_template.docx] [--no-pdf]

Pass 1 builds the docx, renders it with LibreOffice and reads each heading's page from the PDF;
pass 2 rebuilds with those page numbers in the Table of Contents and renders the final PDF.

Content file (see examples/washing/frs_content.py) defines:
    META      client, module, process_name, process_ids, process_desc[], versions[], flowchart, flowchart_caption,
              report_source, brd_images_dir (optional)
    SECTIONS  [{no, title, shots: [(file, caption)], items: [("b"|"s", label, text)]}]  -> Chapter 2
    REPORTS   [{no, name, purpose, filters, brd (optional image), map: [(field, doctype, fieldname, remark)], ...}] -> Chapter 3
Relative paths in META / REPORTS are resolved against the content file's folder.
"""
import argparse
import copy
import json
import os
import re
import runpy
import shutil
import subprocess
import tempfile

import docx
from docx.oxml.ns import qn
from docx.table import Table
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
EMU = 914400
MAX_W, MAX_H = 6.2, 8.3
PROTO_ORDER = ["ch1", "ch2", "ch3", "h2", "img", "cap", "b0", "b1", "pb", "spacer", "map"]


def build(C, base, shots, template, out, pages):
	meta = C["META"]
	rel = lambda p: p if not p or os.path.isabs(p) else os.path.join(base, p)  # noqa: E731
	doc = docx.Document(template)
	body = doc.element.body
	B = list(body.iterchildren())
	marker_i = next(i for i, el in enumerate(B) if "{{PROTOTYPES}}" in "".join(el.itertext()))
	T = dict(zip(PROTO_ORDER, [copy.deepcopy(el) for el in B[marker_i + 1: marker_i + 1 + len(PROTO_ORDER)]]))
	for el in B[marker_i:-1]:
		body.remove(el)

	# cover + document control
	for t in body.iter(qn("w:t")):
		if t.text and "{{CLIENT}}" in t.text:
			t.text = t.text.replace("{{CLIENT}}", meta["client"])
	# client logo slot on the cover: replaced by META["client_logo"], removed when not given
	for dp in list(body.iter(qn("wp:docPr"))):
		if dp.get("name") != "{{CLIENT_LOGO}}":
			continue
		drawing = dp.getparent().getparent()
		logo = rel(meta.get("client_logo"))
		if logo and os.path.exists(logo):
			rid, _ = doc.part.get_or_add_image(logo)
			drawing.find(".//" + qn("a:blip")).set(qn("r:embed"), rid)
			w, h = Image.open(logo).size
			ext = drawing.find(".//" + qn("wp:extent"))
			cy = int(int(ext.get("cx")) * h / w)
			for tag in ("wp:extent", "a:ext"):
				drawing.find(".//" + qn(tag)).set("cy", str(cy))
			dp.set("name", "Client Logo")
		else:
			run_el = drawing.getparent()
			run_el.getparent().remove(run_el)
	tbls = [el for el in B[:marker_i] if el.tag == qn("w:tbl")]
	ctrl, ver = Table(tbls[0], doc.part), Table(tbls[1], doc.part)

	def set_cell(cell, lines):
		ps = cell._tc.findall(qn("w:p"))
		tpl = next((p for p in ps if p.findall(".//" + qn("w:t"))), ps[0])
		for p in ps:
			cell._tc.remove(p)
		for line in lines:
			p = copy.deepcopy(tpl)
			p.findall(".//" + qn("w:t"))[0].text = line
			cell._tc.append(p)

	set_cell(ctrl.rows[0].cells[1], [meta["module"]])
	set_cell(ctrl.rows[1].cells[1], [meta["process_name"]])
	set_cell(ctrl.rows[2].cells[1], [meta["process_ids"]])
	set_cell(ctrl.rows[2].cells[2], meta["process_desc"])
	proto_tr = copy.deepcopy(ver._tbl.tr_lst[1])
	ver._tbl.remove(ver._tbl.tr_lst[1])
	for v in meta["versions"]:
		tr = copy.deepcopy(proto_tr)
		ver._tbl.append(tr)
		cells = Table(ver._tbl, doc.part).rows[-1].cells
		desc = v["description"] if isinstance(v["description"], list) else [v["description"]]
		for c, val in zip(cells, ([v["version"]], [v["date"]], desc, [v["created_by"]], [v["approved_by"]])):
			set_cell(c, val)

	toc, bm = [], [900]

	def add(el):
		body.insert(len(body) - 1, el)
		return el

	def bookmark(el, text, level):
		anchor = f"_Toc_frs_{len(toc)}"
		for tag in ("w:bookmarkStart", "w:bookmarkEnd"):
			for b in el.iter(qn(tag)):
				b.set(qn("w:id"), str(bm[0]))
				if tag == "w:bookmarkStart":
					b.set(qn("w:name"), anchor)
				break
		bm[0] += 1
		toc.append((level, text, anchor))

	def banner(key, text):
		el = copy.deepcopy(T[key])
		bookmark(el, text, 1)
		add(el)

	def heading(text):
		el = copy.deepcopy(T["h2"])
		el.findall(".//" + qn("w:t"))[0].text = text
		bookmark(el, text, 2)
		add(el)

	def run(proto, text, bold):
		r = copy.deepcopy(proto)
		rpr = r.find(qn("w:rPr"))
		for tag in ("w:b", "w:bCs"):
			e = rpr.find(qn(tag))
			if e is not None:
				rpr.remove(e)
		if bold:
			for tag in ("w:bCs", "w:b"):
				rpr.insert(1, rpr.makeelement(qn(tag), {qn("w:val"): "1"}))
		t = r.find(qn("w:t"))
		t.text = text
		t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
		return r

	def bullet(level, label, text):
		el = copy.deepcopy(T["b0" if level == 0 else "b1"])
		runs = el.findall(qn("w:r"))
		proto = runs[-1]
		for r in runs:
			el.remove(r)
		if label:
			el.append(run(proto, label, True))
			if text:
				el.append(run(proto, " " + text, False))
		else:
			el.append(run(proto, text, False))
		add(el)

	small_dir = tempfile.mkdtemp(prefix="frs_img_")
	pic = [1000]

	def picture(path, max_w=MAX_W, max_h=MAX_H):
		if not os.path.exists(path):
			print("  ! missing image", path)
			return
		im = Image.open(path).convert("RGB")
		if im.width > 1700:
			im = im.resize((1700, round(im.height * 1700 / im.width)), Image.LANCZOS)
		small = os.path.join(small_dir, f"{pic[0]}.png")
		im.save(small, "PNG", optimize=True)
		w, h = im.size
		width = min(max_w, max_h * w / h)
		cx, cy = int(width * EMU), int(width * EMU * h / w)
		rid, _ = doc.part.get_or_add_image(small)
		el = copy.deepcopy(T["img"])
		el.find(".//" + qn("a:blip")).set(qn("r:embed"), rid)
		for tag in ("wp:extent", "a:ext"):
			e = el.find(".//" + qn(tag))
			e.set("cx", str(cx))
			e.set("cy", str(cy))
		dp = el.find(".//" + qn("wp:docPr"))
		dp.set("id", str(pic[0]))
		dp.set("name", f"Picture {pic[0]}")
		el.find(".//" + qn("pic:cNvPr")).set("name", os.path.basename(path))
		pic[0] += 1
		add(el)

	def caption(text):
		el = copy.deepcopy(T["cap"])
		el.findall(".//" + qn("w:t"))[0].text = text
		add(el)

	def mapping_table(rows):
		add(copy.deepcopy(T["spacer"]))
		tbl = copy.deepcopy(T["map"])
		trs = tbl.findall(qn("w:tr"))
		proto = trs[1]
		tbl.remove(proto)
		for values in rows:
			tr = copy.deepcopy(proto)
			for tc, val in zip(tr.findall(qn("w:tc")), values):
				p = tc.find(qn("w:p"))
				ts = p.findall(".//" + qn("w:t"))
				if ts:
					ts[0].text = val
				else:
					r = p.makeelement(qn("w:r"), {})
					t = r.makeelement(qn("w:t"), {})
					t.text = val
					r.append(t)
					p.append(r)
			tbl.append(tr)
		add(tbl)

	# Chapter 1
	banner("ch1", "Chapter 1 Flowcharts")
	heading("1.1 To Be Process Flow")
	picture(rel(meta["flowchart"]), max_h=8.0)
	caption(meta.get("flowchart_caption", "To Be Process Flow"))
	add(copy.deepcopy(T["pb"]))

	# Chapter 2
	banner("ch2", "Chapter 2 Masters & Transactions")
	for sec in C["SECTIONS"]:
		heading(f"{sec['no']} {sec['title']}")
		for fname, cap in sec.get("shots", []):
			picture(os.path.join(shots, fname))
			caption(cap)
		for kind, label, text in sec["items"]:
			bullet(0 if kind == "b" else 1, label, text)
		add(copy.deepcopy(T["pb"]))

	# Chapter 3
	banner("ch3", "Chapter 3 Reports Mapping")
	brd_dir = rel(meta.get("brd_images_dir", ""))
	src = meta.get("report_source", f"submitted transactions of the {meta['module']} module and the upstream records listed in the mapping table.")
	for i, r in enumerate(C["REPORTS"]):
		heading(f"{r['no']} {r['name']}")
		bullet(0, "Purpose:", r["purpose"])
		bullet(0, "Filters:", r["filters"])
		bullet(0, "Source:", r.get("source", src))
		if r.get("brd"):
			picture(os.path.join(brd_dir, r["brd"]), max_h=4.2)
			caption("Current format (BRD)")
		picture(os.path.join(shots, f"{r['no']}-report-mockup.png"), max_h=4.5)
		caption("Proposed report layout with sample data")
		mapping_table(r["map"])
		if i < len(C["REPORTS"]) - 1:
			add(copy.deepcopy(T["pb"]))

	# Table of Contents
	sdt = next(el for el in B if el.tag == qn("w:sdt"))
	content = sdt.find(qn("w:sdtContent"))
	ps = content.findall(qn("w:p"))
	first, l2_tpl, l1_tpl, last = ps[0], ps[1], ps[2], ps[-1]
	end_run = [r for r in last.findall(qn("w:r")) if r.find(qn("w:fldChar")) is not None][-1]
	for p in ps[1:]:
		content.remove(p)

	def entry(p, text, anchor):
		h = p.find(qn("w:hyperlink"))
		h.set(qn("w:anchor"), anchor)
		ts = h.findall(".//" + qn("w:t"))
		ts[0].text, ts[-1].text = text, str(pages.get(anchor, ""))

	entry(first, toc[0][1], toc[0][2])
	p = first
	for lvl, text, anchor in toc[1:]:
		p = copy.deepcopy(l1_tpl if lvl == 1 else l2_tpl)
		entry(p, text, anchor)
		content.append(p)
	p.append(copy.deepcopy(end_run))

	xml = doc.element.xml
	for r in [r for r, x in doc.part.rels.items() if "image" in x.reltype and f'"{r}"' not in xml]:
		doc.part.drop_rel(r)
	doc.save(out)
	shutil.rmtree(small_dir, ignore_errors=True)
	return toc


def to_pdf(path):
	outdir = os.path.dirname(os.path.abspath(path))
	subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, path], check=True, capture_output=True)
	return os.path.splitext(path)[0] + ".pdf"


def heading_pages(pdf, toc):
	n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
	norm = lambda s: re.sub(r"\s+", " ", s)  # noqa: E731
	texts = [norm(subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-"], capture_output=True, text=True).stdout)
	         for i in range(1, n + 1)]
	cur = next(i for i, t in enumerate(texts) if "Table of Contents" in t) + 1
	pages = {}
	for lvl, text, anchor in toc:
		key = norm(text.split(" ", 2)[-1] if lvl == 1 else text)
		for i in range(cur, n):
			if key in texts[i]:
				pages[anchor], cur = i + 1, i
				break
	return pages


if __name__ == "__main__":
	ap = argparse.ArgumentParser()
	ap.add_argument("content")
	ap.add_argument("--shots", required=True)
	ap.add_argument("--out", required=True)
	ap.add_argument("--template", default=os.path.join(HERE, "..", "templates", "sanskar_frs_template.docx"))
	ap.add_argument("--no-pdf", action="store_true")
	a = ap.parse_args()
	C = runpy.run_path(a.content)
	base = os.path.dirname(os.path.abspath(a.content))
	os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
	toc = build(C, base, a.shots, a.template, a.out, {})
	if a.no_pdf or not shutil.which("soffice"):
		print("saved", a.out, "(TOC page numbers blank: LibreOffice not used)")
	else:
		pages = heading_pages(to_pdf(a.out), toc)
		build(C, base, a.shots, a.template, a.out, pages)
		pdf = to_pdf(a.out)
		missing = [t for _, t, anc in toc if anc not in pages]
		print("saved", a.out, "and", pdf)
		print(json.dumps({t: pages.get(anc) for _, t, anc in toc}, indent=1))
		if missing:
			print("  ! headings not found in PDF (TOC page left blank):", missing)

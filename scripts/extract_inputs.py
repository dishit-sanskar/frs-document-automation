"""Turn BRD / To-Be / Process List inputs into text + images Claude can read.

Usage:
    python extract_inputs.py --out <work>/inputs  <file.pdf|.docx|.xlsx> [more files...]

Per input it writes into --out:
    <stem>.txt                      text (PDF: layout-preserved; DOCX: paragraphs with [Style] and <IMAGE n>
                                    markers in reading order, tables as | rows; XLSX: each sheet as | rows)
    <stem>-img/NN.png               embedded images. DOCX: numbered in document order, so the To-Be
                                    flowchart is the image after the "(To Be)" heading. PDF: images wider
                                    than 600px as p<page>-<n>.png (report formats, flowcharts).
Requires: poppler-utils (pdftotext, pdfimages) for PDFs.
"""
import argparse
import os
import shutil
import subprocess
import zipfile

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("files", nargs="+")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)


def stem(path):
	return os.path.splitext(os.path.basename(path))[0].replace(" ", "_")


def do_pdf(path):
	s = stem(path)
	subprocess.run(["pdftotext", "-layout", path, os.path.join(a.out, f"{s}.txt")], check=True)
	img_dir = os.path.join(a.out, f"{s}-img")
	os.makedirs(img_dir, exist_ok=True)
	listing = subprocess.run(["pdfimages", "-list", path], capture_output=True, text=True).stdout.splitlines()[2:]
	pages = sorted({int(l.split()[0]) for l in listing if l.split()[2] == "image" and int(l.split()[3]) > 600})
	for pg in pages:
		subprocess.run(["pdfimages", "-f", str(pg), "-l", str(pg), "-png", path, os.path.join(img_dir, f"p{pg:03d}")], check=True)
	for f in os.listdir(img_dir):  # drop masks / tiny images
		fp = os.path.join(img_dir, f)
		if os.path.getsize(fp) < 20000:
			os.remove(fp)
	print(f"{path}: text + {len(os.listdir(img_dir))} images (pages {pages})")


def do_docx(path):
	import docx
	from docx.oxml.ns import qn
	from docx.table import Table
	from docx.text.paragraph import Paragraph

	s = stem(path)
	d = docx.Document(path)
	img_dir = os.path.join(a.out, f"{s}-img")
	os.makedirs(img_dir, exist_ok=True)
	lines, n = [], 0
	for el in d.element.body.iterchildren():
		if el.tag == qn("w:p"):
			p = Paragraph(el, d)
			if p.text.strip():
				lines.append(f"[{p.style.name}] {p.text.strip()}")
			for blip in el.iter(qn("a:blip")):
				part = d.part.related_parts.get(blip.get(qn("r:embed")))
				if part is None or len(part.blob) < 2000:
					continue
				n += 1
				ext = os.path.splitext(part.partname)[1]
				open(os.path.join(img_dir, f"{n:02d}{ext}"), "wb").write(part.blob)
				lines.append(f"  <IMAGE {n:02d}{ext}>")
		elif el.tag == qn("w:tbl"):
			for r in Table(el, d).rows:
				cells = []
				for c in r.cells:
					t = c.text.strip().replace("\n", " / ")
					if not cells or cells[-1] != t:
						cells.append(t)
				lines.append("  | " + " | ".join(cells))
	open(os.path.join(a.out, f"{s}.txt"), "w").write("\n".join(lines))
	print(f"{path}: {len(lines)} lines + {n} images")


def do_xlsx(path):
	import openpyxl

	s = stem(path)
	wb = openpyxl.load_workbook(path, data_only=True)
	lines = []
	for ws in wb:
		lines.append(f"## {ws.title} {ws.dimensions}")
		for r in ws.iter_rows(values_only=True):
			if any(c is not None for c in r):
				lines.append(" | ".join("" if c is None else str(c) for c in r))
	open(os.path.join(a.out, f"{s}.txt"), "w").write("\n".join(lines))
	print(f"{path}: {len(lines)} lines")


for f in a.files:
	ext = os.path.splitext(f)[1].lower()
	if ext == ".pdf":
		do_pdf(f)
	elif ext == ".docx":
		do_docx(f)
	elif ext in (".xlsx", ".xlsm"):
		do_xlsx(f)
	elif ext == ".doc":
		tmp = os.path.join(a.out, ".conv")
		subprocess.run(["soffice", "--headless", "--convert-to", "docx", "--outdir", tmp, f], check=True, capture_output=True)
		do_docx(os.path.join(tmp, os.path.splitext(os.path.basename(f))[0] + ".docx"))
		shutil.rmtree(tmp, ignore_errors=True)
	else:
		print("skipped (unsupported):", f)

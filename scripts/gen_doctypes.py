"""Generate Frappe DocType files (schema only, empty controllers) into a custom app module.

Usage:
    python gen_doctypes.py <spec.py> --app-path <bench>/apps/<app>/<app> --module "<Module Name>"

The spec file is plain Python that imports the helpers from this file and calls `doctype(...)`:

    from gen_doctypes import F, cb, sb, series, amended, doctype, std_perms, states, status_field

Then run `bench --site <site> migrate`. Re-running overwrites the generated JSON/py files of the spec's DocTypes only.
"""
import argparse
import json
import os
import runpy
import sys

TS = "2026-01-01 12:00:00.000000"
MODULE = {"name": "Custom"}
DOCTYPES = []

FULL = dict(read=1, write=1, create=1, delete=1, report=1, export=1, print=1, email=1, share=1)
SUB = dict(submit=1, cancel=1, amend=1)
RO = dict(read=1, report=1, print=1)
STATUS_COLORS = {
	"Draft": "Gray", "Open": "Gray", "Pending": "Orange", "Submitted": "Blue", "Received": "Green", "Released": "Green",
	"Work In Progress": "Orange", "In Process": "Orange", "Completed": "Green", "Approved": "Green", "Passed": "Green",
	"Transferred": "Blue", "Recorded": "Green", "Issued": "Green", "Recovered": "Green", "On Hold": "Red", "Held": "Red",
	"Rejected": "Red", "Cancelled": "Red", "Returned to DC": "Red", "Objective Exceeded": "Red",
	"Defect Raised": "Orange", "Disposition Approved": "Green", "Deviation Approved": "Orange", "Partly Written Off": "Orange",
	"Partly Unallocated": "Orange",
}


# ------------------------------------------------------------------ field helpers
def F(fieldname, fieldtype, label=None, options=None, **kw):
	"""One field. Extra keyword args go straight into the DocField (reqd=1, in_list_view=1, fetch_from=..., ...)."""
	d = {"fieldname": fieldname, "fieldtype": fieldtype}
	if label:
		d["label"] = label
	if options is not None:
		d["options"] = options
	d.update(kw)
	return d


def cb(n):
	return F(f"column_break_{n}", "Column Break")


def sb(n, label=None, **kw):
	return F(f"section_break_{n}", "Section Break", label, **kw)


def series(prefix):
	return F("naming_series", "Select", "Series", prefix, default=prefix, reqd=1, no_copy=1, print_hide=1, set_only_once=1)


def amended(doctype_name):
	return F("amended_from", "Link", "Amended From", doctype_name, no_copy=1, print_hide=1, read_only=1)


def status_field(options, default):
	"""Read-only Status select shown in list view; set by dummy data / future logic."""
	return F("status", "Select", "Status", "\n".join(options), default=default, read_only=1, allow_on_submit=1,
	         in_list_view=1, in_standard_filter=1, no_copy=1)


def states(*names):
	"""List-view indicator colours for status values."""
	return [{"title": n, "color": STATUS_COLORS.get(n, "Gray")} for n in names]


def std_perms(manager_roles=(), user_roles=(), read_roles=(), submittable=False):
	"""System Manager + managers: full (+submit/cancel/amend); users: create/write (+submit); readers: read/report/print."""
	ps = [{"role": "System Manager", **FULL, **(SUB if submittable else {})}]
	ps += [{"role": r, **FULL, **(SUB if submittable else {})} for r in manager_roles]
	ps += [{"role": r, **{k: v for k, v in FULL.items() if k != "delete"}, **({"submit": 1} if submittable else {})} for r in user_roles]
	ps += [{"role": r, **RO} for r in read_roles]
	return ps


def doctype(name, fields, description="", submittable=False, istable=False, issingle=False, autoname=None, perms=None,
            title_field=None, search_fields=None, image_field=None, states=None):
	"""Register one DocType. Child tables: istable=True (no perms). Singles: issingle=True."""
	if submittable and not any(f["fieldname"] == "amended_from" for f in fields):
		fields = fields + [amended(name)]
	d = {
		"actions": [], "creation": TS, "description": description, "doctype": "DocType", "engine": "InnoDB",
		"field_order": [f["fieldname"] for f in fields], "fields": fields, "index_web_pages_for_search": 0, "links": [],
		"modified": TS, "modified_by": "Administrator", "module": None, "name": name, "owner": "Administrator",
		"permissions": [] if istable else (perms or std_perms(submittable=submittable)), "sort_field": "modified",
		"sort_order": "DESC", "states": states or [],
	}
	if istable:
		d.update(istable=1, editable_grid=1)
	else:
		d["track_changes"] = 1
	if issingle:
		d["issingle"] = 1
	if submittable:
		d["is_submittable"] = 1
	if autoname:
		d["autoname"] = autoname
		if autoname.startswith("naming_series"):
			d["naming_rule"] = 'By "Naming Series" field'
		elif autoname.startswith("field:"):
			d["naming_rule"] = "By fieldname"
		elif autoname.startswith("format:"):
			d["naming_rule"] = "Expression"
	if title_field:
		d.update(title_field=title_field, show_title_field_in_link=1)
	if search_fields:
		d["search_fields"] = search_fields
	if image_field:
		d["image_field"] = image_field
	DOCTYPES.append(d)
	return d


# ------------------------------------------------------------------ writer
def scrub(name):
	return name.lower().replace(" ", "_").replace("-", "_")


def write(app_path, module):
	mod_dir = os.path.join(app_path, scrub(module))
	os.makedirs(os.path.join(mod_dir, "doctype"), exist_ok=True)
	for p in (os.path.join(mod_dir, "__init__.py"), os.path.join(mod_dir, "doctype", "__init__.py")):
		open(p, "a").close()
	modules_txt = os.path.join(app_path, "modules.txt")
	lines = open(modules_txt).read().splitlines() if os.path.exists(modules_txt) else []
	if module not in lines:
		with open(modules_txt, "w") as f:
			f.write("\n".join([*lines, module]) + "\n")
	for d in DOCTYPES:
		d["module"] = module
		s = scrub(d["name"])
		folder = os.path.join(mod_dir, "doctype", s)
		os.makedirs(folder, exist_ok=True)
		open(os.path.join(folder, "__init__.py"), "a").close()
		with open(os.path.join(folder, f"{s}.json"), "w") as f:
			json.dump(d, f, indent=1, ensure_ascii=False)
			f.write("\n")
		cls = d["name"].replace(" ", "").replace("-", "")
		with open(os.path.join(folder, f"{s}.py"), "w") as f:
			f.write("# Copyright (c) 2026, Sanskar Technolab and contributors\n"
			        "# For license information, please see license.txt\n\n"
			        "from frappe.model.document import Document\n\n\n"
			        f"class {cls}(Document):\n\tpass\n")
	print(f"{len(DOCTYPES)} doctypes written to {mod_dir}")


if __name__ == "__main__":
	ap = argparse.ArgumentParser()
	ap.add_argument("spec")
	ap.add_argument("--app-path", required=True, help="<bench>/apps/<app>/<app> (the python package folder)")
	ap.add_argument("--module", required=True)
	a = ap.parse_args()
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	sys.modules["gen_doctypes"] = sys.modules[__name__]
	runpy.run_path(a.spec, run_name="spec")
	write(a.app_path, a.module)

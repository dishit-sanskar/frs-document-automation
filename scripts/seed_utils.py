"""Helpers for dummy-data seed scripts (run through run_in_site.py).

Seed scripts must be re-runnable: call `clear()` for the module's transactions first, `ensure()` for masters
that may already exist, and `make()` for new transactions.
"""
import io
import random

import frappe
from frappe.utils import get_datetime


def ensure(doctype, name, values):
	"""Insert or update a record by name (masters shared with other modules: Workstation, Item, Operation...)."""
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		doc.update(values)
		doc.save(ignore_permissions=True)
		return doc
	return frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)


def make(doctype, values, submit=False, status=None):
	"""Insert a transaction; optionally submit it and force the read-only Status field (no business logic exists)."""
	doc = frappe.get_doc({"doctype": doctype, **values})
	doc.insert(ignore_permissions=True)
	if submit:
		doc.submit()
	if status:
		doc.db_set("status", status, update_modified=False)
	return doc


def clear(doctypes, series_prefixes=()):
	"""Hard-delete all records (and child rows) of the given DocTypes and reset their naming series."""
	for dt in doctypes:
		for child in frappe.get_all("DocField", filters={"parent": dt, "fieldtype": "Table"}, pluck="options"):
			frappe.db.delete(child, {"parenttype": dt})
		frappe.db.delete(dt)
	for prefix in series_prefixes:
		frappe.db.delete("Series", {"name": ["like", f"{prefix}%"]})


def at(date, time):
	return get_datetime(f"{date} {time}")


def employee(first, last, designation, company, department=None, gender="Male"):
	"""Get or create an Employee by full name."""
	full = f"{first} {last}"
	name = frappe.db.get_value("Employee", {"employee_name": full})
	if name:
		return name
	if not frappe.db.exists("Designation", designation):
		frappe.get_doc({"doctype": "Designation", "designation_name": designation}).insert(ignore_permissions=True)
	return frappe.get_doc({
		"doctype": "Employee", "first_name": first, "last_name": last, "gender": gender, "date_of_birth": "1990-05-12",
		"date_of_joining": "2022-01-10", "company": company, "department": department, "designation": designation,
		"status": "Active",
	}).insert(ignore_permissions=True).name


def swatch_image(name, rgb, seed=7):
	"""Create (once) a public PNG that looks like a fabric swatch and return its file_url — for Attach Image fields."""
	from PIL import Image, ImageDraw, ImageFilter

	existing = frappe.db.get_value("File", {"file_name": f"{name}.png"}, "file_url")
	if existing:
		return existing
	rnd = random.Random(seed)
	img = Image.new("RGB", (480, 360), rgb)
	draw = ImageDraw.Draw(img)
	for i in range(0, 600, 3):
		shade = tuple(min(255, max(0, c + rnd.randint(-18, 18))) for c in rgb)
		draw.line([(i, 0), (i - 120, 360)], fill=shade, width=2)
	for _ in range(6):
		x, y = rnd.randint(60, 420), rnd.randint(40, 320)
		draw.ellipse([x - 40, y - 12, x + 40, y + 12], fill=tuple(min(255, c + 45) for c in rgb))
	buf = io.BytesIO()
	img.filter(ImageFilter.GaussianBlur(1.2)).save(buf, "PNG")
	f = frappe.get_doc({"doctype": "File", "file_name": f"{name}.png", "content": buf.getvalue(), "is_private": 0})
	return f.insert(ignore_permissions=True).file_url


def show_employee_names():
	"""Show employee names instead of HR-EMP-xxxxx in link fields (site-level Property Setter, display only).

	Undo: delete the Employee Property Setter 'show_title_field_in_link'.
	"""
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	make_property_setter("Employee", None, "show_title_field_in_link", 1, "Check", for_doctype=True)
	frappe.clear_cache(doctype="Employee")

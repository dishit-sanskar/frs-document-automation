"""Run a Python script inside a Frappe site context (as Administrator) and commit.

Must be executed with the bench's own Python so frappe/erpnext import:

    <bench>/env/bin/python run_in_site.py --bench <bench> --site <site> <script.py> [script args...]

The script runs with `frappe` connected; this scripts/ folder is on sys.path so it can `import seed_utils`.
"""
import argparse
import os
import runpy
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--bench", required=True)
ap.add_argument("--site", required=True)
ap.add_argument("script")
ap.add_argument("args", nargs=argparse.REMAINDER)
a = ap.parse_args()

script = os.path.abspath(a.script)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(script))
os.chdir(os.path.join(a.bench, "sites"))

import frappe  # noqa: E402

frappe.init(site=a.site, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	sys.argv = [script, *a.args]
	runpy.run_path(script, run_name="__main__")
	frappe.db.commit()
finally:
	frappe.destroy()

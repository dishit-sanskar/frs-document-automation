"""Dummy data for the Washing FRS screenshots — worked example of a seed script. Re-runnable.

    <bench>/env/bin/python ../../scripts/run_in_site.py --bench <bench> --site <site> seed.py
"""
import random

import frappe
from frappe.utils import add_days, get_datetime, getdate
from seed_utils import clear as clear_doctypes
from seed_utils import ensure, make, show_employee_names
from seed_utils import swatch_image as swatch

COMPANY = "Sanskar Technolab"
ABBR = "ST"
D = getdate("2026-10-28")
random.seed(7)

WASH_TX = [
	"Laundry Output Transfer", "Utility Consumption Entry", "Chemical Issue Entry", "Rework and Rewash Entry",
	"Wash Rejection Entry", "Stage Inspection Entry", "Machine Counter Reading", "Laser Daily Plan Entry",
	"Wet Job Card", "Dry Job Card", "Bin Card", "Laundry Receipt Entry", "Wash Recipe",
]


def dt(s):
	return get_datetime(f"{D} {s}") if len(s) <= 8 else get_datetime(s)


# ------------------------------------------------------------------ referenced masters
def seed_reference():
	for wt in ("Wet Machine", "Laser", "Spray Cabin", "Mannequin", "Tent", "Dryer"):
		ensure("Workstation Type", wt, {"workstation_type": wt})

	ws = [
		("TN1", "Wet Machine", 50, 1, "A, B"), ("TN2", "Wet Machine", 50, 1, "A, B"),
		("TNS5", "Wet Machine", 175, 1, "A, B, C"), ("TNS6", "Wet Machine", 175, 1, "A, B, C"),
		("TO2", "Wet Machine", 100, 1, "A, B"), ("BW3", "Wet Machine", 150, 0, "A"),
		("DYE-T1", "Tent", 120, 0, "A, B"),
		("LR-01", "Laser", 0, 0, "A, B"), ("LR-02", "Laser", 0, 0, "A, B"), ("LR-03", "Laser", 0, 0, "A, B"),
		("LR-04", "Laser", 0, 0, "A"), ("LR-FLAT3", "Laser", 0, 0, "A"),
		("SC-01", "Spray Cabin", 60, 0, "A, B"), ("SC-02", "Spray Cabin", 60, 0, "A"),
		("MQ-01", "Mannequin", 40, 0, "A, B"), ("MQ-02", "Mannequin", 40, 0, "A"),
	]
	for code, wt, cap, counter, shifts in ws:
		ensure("Workstation", code, {
			"workstation_name": code, "workstation_type": wt, "load_capacity_pcs": cap, "counter_enabled": counter,
			"machine_api_enabled": 1 if code.startswith(("TNS", "LR")) else 0, "shift_coverage": shifts,
			"machine_barcode": f"MC-{code}",
		})

	ops = [
		("Laser", "Laser", "Laser 1", "Laser", 0, 1), ("Laser D.S 2", "Laser", "Laser 2", "Laser", 0, 1),
		("M.Whisker", "Dry", "Dry 1", "Mannequin", 20, 1), ("M.Handsand", "Dry", "Dry 1", "Mannequin", 25, 1),
		("Tacking", "Dry", "Dry 1", "Mannequin", 15, 0), ("PP Spray", "Dry", "Dry 2", "Spray Cabin", 30, 1),
		("Grinding", "Dry", "Dry 2", "Mannequin", 20, 1), ("M.Des", "Dry", "Dry 2", "Mannequin", 20, 1),
		("Foil", "Dry", "Foil", "Mannequin", 25, 1),
		("1st Bath", "Wet", "Wash 1", "Wet Machine", 45, 0), ("Enzyme", "Wet", "Wash 1", "Wet Machine", 60, 1),
		("Bleach", "Wet", "Wash 1", "Wet Machine", 40, 1), ("Sodium", "Wet", "Wash 2", "Wet Machine", 35, 0),
		("Acid Wash & Foam", "Wet", "Foam", "Wet Machine", 60, 1), ("Silicon", "Wet", "Wash 2", "Wet Machine", 25, 0),
		("Rinse", "Wet", "Wash 2", "Wet Machine", 15, 0), ("Final Wash", "Wet", "Wash 2", "Wet Machine", 45, 1),
		("Rewash", "Wet", "Wash 2", "Wet Machine", 45, 1), ("Dyeing", "Dyeing", "Dyeing", "Tent", 90, 1),
	]
	for name, grp, stage, wsg, ct, insp in ops:
		ensure("Operation", name, {
			"name": name, "washing_operation_group": grp, "washing_stage": stage, "default_workstation_group": wsg,
			"standard_cycle_time": ct, "inspection_required": insp, "workstation": None,
		})

	for wh in ("Chemical Store CS02", "Laundry WIP", "DC 3 - Finishing"):
		if not frappe.db.exists("Warehouse", f"{wh} - {ABBR}"):
			frappe.get_doc({"doctype": "Warehouse", "warehouse_name": wh, "company": COMPANY}).insert(ignore_permissions=True)

	ensure("Item Group", "Washing Chemicals", {"item_group_name": "Washing Chemicals", "parent_item_group": "All Item Groups"})
	chems = [
		("150000344", "Sodium Hydrosulphite", "Wet", 1.85), ("151076", "Kemzyme Max 15-1076", "Wet", 6.40),
		("150000192", "Potassium Permanganate (PP)", "Spray", 4.20), ("150000210", "Sodium Hypochlorite Bleach", "Wet", 0.65),
		("150000377", "Silicone Softener HC", "Wet", 3.10), ("150000455", "Anti-Backstain AB-30", "Wet", 2.75),
		("150000512", "Neutraliser Acid N-4", "Wet", 1.20), ("150000618", "Pumice Stone 2-3 cm", "Wet", 0.40),
		("160000101", "Lava Dye Black GLF", "Dye", 9.80), ("160000233", "Fluo Pigment HB-11 Pink", "Dye", 12.50),
		("160000310", "Dye Fixer DF-2", "Dye", 3.60),
	]
	for code, name, grp, rate in chems:
		ensure("Item", f"CHM-{code}", {
			"item_code": f"CHM-{code}", "item_name": name, "item_group": "Washing Chemicals", "stock_uom": "Kg",
			"is_stock_item": 1, "valuation_rate": rate, "standard_rate": rate, "sap_material_number": code,
			"chemical_function_group": grp,
		})

	emps = [
		("Hany", "Fawzy", "Laundry Manager"), ("Mostafa", "Adel", "Dry Manager"), ("Ahmed", "Refaey", "Laundry Supervisor"),
		("Amr", "Sliem", "Laundry Supervisor"), ("Mohamed", "Sayed", "Laundry Operator"), ("Ibrahim", "Hassan", "Laundry Operator"),
		("Mahmoud", "Semsem", "Laundry Operator"), ("Rania", "Kamal", "Quality Manager"), ("Yasser", "Fathy", "Quality Inspector"),
		("Walid", "Nabil", "DC Agent"), ("Samy", "Tarek", "Chemical Store Keeper"), ("Karim", "Lotfy", "Laser Operator"),
	]
	ensure("Department", f"Laundry - {ABBR}", {"department_name": "Laundry", "company": COMPANY, "parent_department": "All Departments"})
	out = {}
	for first, last, desig in emps:
		ensure("Designation", desig, {"designation_name": desig})
		full = f"{first} {last}"
		name = frappe.db.get_value("Employee", {"employee_name": full})
		if not name:
			e = frappe.get_doc({
				"doctype": "Employee", "first_name": first, "last_name": last, "gender": "Male" if first != "Rania" else "Female",
				"date_of_birth": "1990-05-12", "date_of_joining": "2022-01-10", "company": COMPANY,
				"department": f"Laundry - {ABBR}", "designation": desig, "status": "Active",
			}).insert(ignore_permissions=True)
			name = e.name
		out[first] = name
	return out


# ------------------------------------------------------------------ washing masters
def seed_masters(E):
	s = frappe.get_single("Washing Settings")
	s.update({
		"default_load_size": 100, "cycle_time_variance_tolerance": 10, "machine_counter_frequency": "Per Shift",
		"machine_downtime_threshold": 30, "rejection_percentage_objective": 1, "cost_per_piece_objective": 0.1,
		"water_per_piece_objective": 0.05, "gas_per_piece_objective": 0.5, "electricity_per_piece_objective": 1.8,
		"overtime_percentage_objective": 3, "time_per_piece_objective": 10, "second_quality_threshold": 2,
		"wip_target_min": 20000, "wip_target_max": 25000, "pallet_bin_mandatory": 1, "bin_card_mandatory": 1,
		"excess_scan_needs_approval": 1, "shade_tolerance_needs_approval": 1,
		"chemical_store_warehouse": f"Chemical Store CS02 - {ABBR}", "laundry_wip_warehouse": f"Laundry WIP - {ABBR}",
		"finishing_warehouse": f"DC 3 - Finishing - {ABBR}", "security_stock_average_days": 15, "chemical_lead_time_days": 35,
		"purchase_requisition_cover_days": 60, "high_cost_chemical_share": 80,
	})
	s.set("stage_thresholds", [
		{"stage": "Foam", "wip_threshold": 2000}, {"stage": "Laser 1", "wip_threshold": 5000},
		{"stage": "Dry 1", "wip_threshold": 4000}, {"stage": "Wash 1", "wip_threshold": 3000},
	])
	s.set("shifts", [
		{"shift": "A", "start_time": "07:00:00", "end_time": "15:00:00"},
		{"shift": "B", "start_time": "15:00:00", "end_time": "23:00:00"},
		{"shift": "C", "start_time": "23:00:00", "end_time": "07:00:00"},
	])
	s.save(ignore_permissions=True)

	reasons = [
		("WR-01", "Damage Laundry", "Wet", "Washing", "Scrap", 1), ("WR-02", "Leg to Leg Variation", "Wet", "Washing", "Rewash", 0),
		("WR-03", "Out of Shade", "Dyeing", "Washing", "Rewash", 1), ("WR-04", "Spot - Laundry", "Wet", "Washing", "Rewash", 0),
		("WR-05", "Streaks", "Wet", "Washing", "Rewash", 0), ("WR-06", "Wrong Wash", "Wet", "Washing", "Second Quality", 1),
		("WR-07", "Stain", "Wet", "Handling", "Rework", 0), ("WR-08", "Damage Dry Process", "Dry", "Dry Process", "Scrap", 1),
		("WR-09", "Spot - Dry Process", "Dry", "Dry Process", "Rework", 0), ("WR-10", "Grinding", "Dry", "Dry Process", "Rework", 0),
		("WR-11", "Wrong Process - Dry", "Dry", "Dry Process", "Second Quality", 1), ("WR-12", "Laser", "Laser", "Laser", "Rework", 0),
		("WR-13", "Zipper Broken", "Wet", "Sewing", "Rework", 0), ("WR-14", "Leckra - Washing", "Wet", "Washing", "Second Quality", 1),
		("WR-15", "Testing", "Washing Test", "Washing Test", "Scrap", 0), ("WR-16", "Pilot Run", "Washing Test", "Washing Test", "Scrap", 0),
		("WR-17", "Fabric Defect", "Wet", "Fabric", "Second Quality", 1),
	]
	for code, name, grp, dept, disp, charge in reasons:
		frappe.get_doc({
			"doctype": "Wash Rejection Reason", "reason_code": code, "reason_name": name, "stage_group": grp,
			"responsible_department": dept, "default_disposition": disp, "chargeable": charge, "active": 0 if code == "WR-16" else 1,
		}).insert(ignore_permissions=True)

	img_bucksin = swatch("sample-bucksin", (52, 74, 110))
	img_camino = swatch("sample-camino", (88, 116, 152))
	img_lawson = swatch("sample-lawson", (70, 92, 128))
	img_dye = swatch("sample-bleach-dye", (40, 40, 44))
	img_night = swatch("sample-nighthawk", (30, 42, 70))

	def recipe(code, wash, rtype, buyer, style, fabric, status, ver, wsg, load, ct, steps, chems, img, laser_ct=0,
	           shade="", sample_req="Not Required", band="Not Required", prev=None):
		return frappe.get_doc({
			"doctype": "Wash Recipe", "recipe_code": code, "wash_name": wash, "recipe_type": rtype, "buyer": buyer,
			"style": style, "fabric_reference": fabric, "recipe_status": status, "version_no": ver, "previous_version": prev,
			"default_workstation_group": wsg, "standard_load_size": load, "standard_cycle_time": ct, "laser_cycle_time": laser_ct,
			"shade_standard": shade, "recipe_barcode": f"RCP-{code}-V{ver}", "sample_image": img,
			"approved_sample_reference": f"SMP-{code}-{ver:02d}", "sample_request_status": sample_req, "shade_band_status": band,
			"approved_by": "Administrator" if status in ("Approved", "Locked", "Superseded") else None,
			"approval_date": add_days(D, -40 + ver * 12) if status in ("Approved", "Locked", "Superseded") else None,
			"steps": [dict(zip(("step_no", "operation", "temperature", "duration", "liquor_ratio", "step_remarks"), x)) for x in steps],
			"chemicals": [dict(zip(("step_no", "chemical_item", "dosage"), x)) for x in chems],
		}).insert(ignore_permissions=True)

	wet_steps = [
		(1, "1st Bath", 40, 10, "1:8", "Desize, drain"), (2, "Enzyme", 55, 45, "1:6", "Add pumice 2 kg / load"),
		(3, "Bleach", 50, 20, "1:8", "Check shade at 15 min"), (4, "Rinse", 30, 5, "1:10", "Twice"),
		(5, "Silicon", 40, 15, "1:8", "Final hand feel"),
	]
	wet_chems = [
		(1, "CHM-150000455", 0.4), (2, "CHM-151076", 1.2), (2, "CHM-150000618", 2.0), (3, "CHM-150000210", 3.5),
		(3, "CHM-150000344", 0.8), (5, "CHM-150000377", 0.9),
	]
	v1 = recipe("WR-BUCK", "BUCKSIN", "Wet Wash", "Levant Denim Co", "J09HAMSHACK9649", "SS24260CK", "Superseded", 1,
	            "Wet Machine", 75, 95, wet_steps, wet_chems, img_bucksin)
	recipe("WR-BUCK", "BUCKSIN", "Wet Wash", "Levant Denim Co", "J09HAMSHACK9649", "SS24260CK", "Locked", 2, "Wet Machine",
	       75, 90, wet_steps[:2] + [(3, "Bleach", 50, 15, "1:8", "Reduced bleach time V2")] + wet_steps[3:],
	       wet_chems[:3] + [(3, "CHM-150000210", 3.0)] + wet_chems[4:], img_bucksin, prev=v1.name, band="Approved")
	recipe("WR-CAMI", "CAMINO", "Wet Wash", "Northwind Apparel", "D07CHINO2215", "SS23303A", "Approved", 1, "Wet Machine",
	       100, 60, [(1, "1st Bath", 40, 10, "1:8", ""), (2, "Enzyme", 50, 30, "1:6", "Light abrasion"),
	                 (3, "Final Wash", 40, 15, "1:8", "Softener in last bath")],
	       [(1, "CHM-150000455", 0.3), (2, "CHM-151076", 0.8), (3, "CHM-150000377", 0.7)], img_camino, band="Approved")
	recipe("DR-LAWS", "LAWSON", "Dry Process", "Northwind Apparel", "J09HAMSHACK9649", "DEN-9760A-50", "Approved", 1, "Mannequin",
	       40, 35, [(1, "Laser", 0, 0, "", "W/S + H/S laser file LAWSON-03"), (2, "M.Whisker", 0, 8, "", "6 whiskers per leg"),
	                (3, "PP Spray", 0, 6, "", "Thigh & seat area only"), (4, "Grinding", 0, 4, "", "Hem and pocket edges")],
	       [(3, "CHM-150000192", 0.25)], img_lawson, laser_ct=36)
	recipe("DY-BLDY", "BLEACH+DYE", "Dyeing", "Urban Threads Retail", "T12POLO4410", "PQ-4410-WHT", "Approved", 1, "Tent", 120, 110,
	       [(1, "Bleach", 50, 20, "1:8", ""), (2, "Dyeing", 80, 60, "1:10", "Shade card BLK-02"), (3, "Rinse", 30, 10, "1:10", "")],
	       [(1, "CHM-150000210", 2.5), (2, "CHM-160000101", 1.8), (2, "CHM-160000310", 0.4)], img_dye, shade="BLK-02 Jet Black")
	recipe("WR-NIGH", "NIGHTHAWK", "Wet Wash", "Northwind Apparel", "J09HAMSHACK9649", "RR7216-JLC CRISPY", "Under Trial", 1,
	       "Wet Machine", 50, 120, [(1, "Enzyme", 55, 60, "1:6", "Trial on GT130 - 50 pcs"), (2, "Acid Wash & Foam", 45, 40, "1:4", "")],
	       [(1, "CHM-151076", 1.5), (2, "CHM-150000192", 0.6)], img_night, sample_req="Requested from Merchandising",
	       band="Pilot Run - 100 Pcs")


# ------------------------------------------------------------------ transactions
def seed_transactions(E):
	SO1, SO2, SO3, SO4 = "SAL-ORD-2026-00001", "SAL-ORD-2026-00002", "SAL-ORD-2026-00003", "SAL-ORD-2026-00004"
	BUCK, CAMI, LAWS, BLDY = "WR-BUCK-V2", "WR-CAMI-V1", "DR-LAWS-V1", "DY-BLDY-V1"
	W = lambda n: f"{n} - {ABBR}"  # noqa: E731

	rec = {}
	for so, style, fabric, wash, recipe, src, sizes, shade, status, verify in [
		(SO1, "J09HAMSHACK9649", "SS24260CK", "BUCKSIN", BUCK, "Sewing Line", [("M", 120), ("L", 260), ("XL", 140)], "Indigo 2", "Received", "Verified"),
		(SO2, "D07CHINO2215", "SS23303A", "CAMINO", CAMI, "Sewing Line", [("32", 400), ("34", 400), ("36", 200)], "Stone 1", "Received", "Verified"),
		(SO4, "J09HAMSHACK9649", "DEN-9760A-50", "LAWSON", LAWS, "Laser", [("M", 100), ("L", 100), ("XL", 80)], "Mid Blue", "Received", "Verified"),
		(SO3, "T12POLO4410", "PQ-4410-WHT", "BLEACH+DYE", BLDY, "Sewing Line", [("L", 150), ("XL", 150), ("XXL", 50)], "White RFD", "Received", "Verified"),
		(SO2, "D07CHINO2215", "SS23303A", "CAMINO", CAMI, "Sub-Contract", [("32", 180), ("34", 20)], "Stone 1", "Returned to DC", "Mismatch"),
	]:
		items = [{"size": s, "shade": shade, "received_qty": q, "pallet_no": f"PLT-{random.randint(1100, 1999)}",
		          "bin": f"LS-{random.choice('ABC')}{random.randint(1, 12):02d}"} for s, q in sizes]
		doc = make("Laundry Receipt Entry", {
			"receipt_datetime": dt("07:40:00"), "shift": "A", "source_stage": src, "sales_order": so, "style": style,
			"fabric_name": fabric, "wash_name": wash, "wash_recipe": recipe, "dc_agent": E["Walid"],
			"verification_status": verify, "items": items, "total_received_qty": sum(q for _, q in sizes),
			"discrepancy_type": "PO Number Mismatch" if verify == "Mismatch" else None,
			"discrepancy_remarks": "Size label shows PO NWA-PO-5531; Sale Order carries NWA-PO-5530. Pallet returned to DC." if verify == "Mismatch" else None,
		}, submit=True, status=status)
		rec.setdefault(so, doc)

	colours = {"Indigo 2": "Blue", "Stone 1": "Yellow", "Mid Blue": "Green", "White RFD": "White"}
	bins = {}
	for so, style, po, shade, size, pcs, recipe, stage, status, ops in [
		(SO1, "J09HAMSHACK9649", "LDC-PO-24117", "Indigo 2", "L", 150, BUCK, "Wash 1", "In Process", ["1st Bath", "Enzyme", "Bleach", "Rinse", "Silicon"]),
		(SO1, "J09HAMSHACK9649", "LDC-PO-24117", "Indigo 2", "XL", 140, BUCK, "Wash 2", "In Process", ["1st Bath", "Enzyme", "Bleach", "Rinse", "Silicon"]),
		(SO2, "D07CHINO2215", "NWA-PO-5530", "Stone 1", "32", 200, CAMI, "Bend for Quality", "Completed", ["1st Bath", "Enzyme", "Final Wash"]),
		(SO4, "J09HAMSHACK9649", "NWA-PO-5561", "Mid Blue", "M", 100, LAWS, "Dry 1", "In Process", ["Laser", "M.Whisker", "PP Spray", "Grinding"]),
		(SO3, "T12POLO4410", "UTR-PO-0912", "White RFD", "L", 120, BLDY, "Dyeing", "Open", ["Bleach", "Dyeing", "Rinse"]),
	]:
		done = {"Wash 1": 2, "Wash 2": 4, "Bend for Quality": 3, "Dry 1": 1, "Dyeing": 1}[stage]
		n = len(bins) + 1
		doc = make("Bin Card", {
			"laundry_receipt": rec[so].name, "sales_order": so, "style": style, "po_no": po, "shade": shade,
			"card_colour": colours[shade], "size": size, "pieces": pcs, "lot_size": pcs, "wash_recipe": recipe,
			"current_stage": stage, "bin_barcode": f"BIN{n:05d}", "first_cycle_barcode": f"CYC{n:05d}-01",
			"fifo_in_time": dt("08:05:00"),
			"operations": [{
				"sequence": i + 1, "operation": op, "cycle_barcode": f"CYC{n:05d}-{i + 1:02d}",
				"barcode_on": "Bin Card" if i == 0 else "Sticker in Pouch", "quality_passed": 1 if i < done else 0,
				"checked_by": E["Yasser"] if i < done else None, "checked_on": dt(f"{9 + i}:15:00") if i < done else None,
			} for i, op in enumerate(ops)],
		}, status=status)
		bins.setdefault(so, []).append(doc.name)

	wo = frappe.get_all("Work Order", pluck="name", limit=3)
	djc = []
	for so, op, ws, qty, verified, status, outs in [
		(SO4, "M.Whisker", "MQ-01", 100, 1, "Completed", [("Mohamed", "08:00", "11:20", 98, 2)]),
		(SO4, "PP Spray", "SC-01", 100, 1, "Work In Progress", [("Ibrahim", "11:40", "14:30", 60, 0)]),
		(SO1, "M.Handsand", "MQ-02", 150, 0, "On Hold", []),
	]:
		doc = make("Dry Job Card", {
			"work_order": wo[0] if wo else None, "sales_order": so, "style": "J09HAMSHACK9649", "operation": op,
			"wash_recipe": LAWS if so == SO4 else BUCK, "bin_card": bins[so][0], "workstation": ws, "shift": "A",
			"posting_date": D, "planned_qty": qty, "supervisor": E["Ahmed"], "po_verified": 1, "sample_verified": verified,
			"sample_request_raised": 0 if verified else 1, "from_stage": "Dry 1" if op != "PP Spray" else "Dry 2",
			"outputs": [{"operator": E[o], "start_time": dt(f"{a}:00"), "end_time": dt(f"{b}:00"), "produced_qty": p,
			             "rejected_qty": r} for o, a, b, p, r in outs],
			"total_produced_qty": sum(x[3] for x in outs), "total_rejected_qty": sum(x[4] for x in outs),
		}, submit=verified == 1, status=status)
		djc.append(doc.name)

	def loads(spec, std):
		rows = []
		for i, (bc, q, wt, op, a, b) in enumerate(spec):
			ct = int((dt(b) - dt(a)).total_seconds() // 60)
			gap = int((dt(spec[i + 1][4]) - dt(b)).total_seconds() // 60) if i + 1 < len(spec) else 0
			rows.append({"load_no": i + 1, "bin_card": bc, "scan_verified": 1, "load_qty": q, "wash_type": wt,
			             "operator": E[op], "supervisor": E["Ahmed"], "in_time": dt(a), "out_time": dt(b), "cycle_time": ct,
			             "standard_cycle_time": std, "gap_to_next_load": gap, "cycle_overrun": 1 if ct > std * 1.1 else 0})
		return rows

	wjc = []
	for so, op, ws, recipe, std, spec, status, extra in [
		(SO1, "Enzyme", "TNS5", BUCK, 90, [(bins[SO1][0], 75, "Enzyme", "Mahmoud", "07:00", "08:30"),
		                                    (bins[SO1][0], 75, "Enzyme", "Mahmoud", "08:45", "10:20"),
		                                    (bins[SO1][1], 70, "Enzyme", "Mahmoud", "10:40", "12:25")], "Completed", {}),
		(SO2, "Final Wash", "TO2", CAMI, 60, [(bins[SO2][0], 100, "Final", "Mohamed", "07:25", "08:10"),
		                                       (bins[SO2][0], 100, "Final", "Mohamed", "08:30", "09:20")], "Completed", {}),
		(SO1, "Bleach", "TN1", BUCK, 90, [(bins[SO1][1], 50, "Bleach", "Ibrahim", "13:00", "13:45")], "Work In Progress", {}),
		(SO3, "Dyeing", "DYE-T1", BLDY, 110, [(bins[SO3][0], 120, "Dyeing", "Ibrahim", "07:30", "09:35")], "Completed",
		 {"shade_standard": "BLK-02 Jet Black", "dye_consumption_kg": 2.2, "shade_result": "Approved"}),
	]:
		rows = loads(spec, std)
		doc = make("Wet Job Card", {
			"work_order": wo[1] if len(wo) > 1 else None, "sales_order": so, "style": {SO1: "J09HAMSHACK9649", SO2: "D07CHINO2215", SO3: "T12POLO4410"}[so],
			"operation": op, "wash_recipe": recipe, "bin_card": spec[0][0], "workstation": ws, "shift": "A", "posting_date": D,
			"recipe_type": frappe.db.get_value("Wash Recipe", recipe, "recipe_type"),
			"load_capacity": frappe.db.get_value("Workstation", ws, "load_capacity_pcs"), "loads": rows,
			"total_loads": len(rows), "total_load_qty": sum(r["load_qty"] for r in rows),
			"total_cycle_time": sum(r["cycle_time"] for r in rows), "total_idle_time": sum(r["gap_to_next_load"] for r in rows), **extra,
		}, submit=status == "Completed", status=status)
		wjc.append(doc.name)

	slots = ["7 AM - 8 AM", "8 AM - 9 AM", "9 AM - 10 AM", "10 AM - 11 AM"]
	for shift, rows in [
		("1st Shift", [("LR-01", "Northwind Apparel", "J09HAMSHACK9649", "W/S + H/S", 36), ("LR-02", "Levant Denim Co", "J09HAMSHACK9649", "W/S + H/S", 48),
		               ("LR-03", "Northwind Apparel", "D07CHINO2215", "Repair", 20)]),
		("2nd Shift", [("LR-01", "Northwind Apparel", "J09HAMSHACK9649", "W/S + H/S", 36), ("LR-FLAT3", "Levant Denim Co", "J09HAMSHACK9649", "Flat W/S", 24)]),
	]:
		items = []
		for ws, buyer, style, toop, ct in rows:
			for sl in slots[:3]:
				plan = 3600 // ct
				items.append({"workstation": ws, "buyer": buyer, "style": style, "type_of_operation": toop, "cycle_time": ct,
				              "hour_slot": sl, "planned_qty": plan, "actual_qty": plan - random.randint(0, 12)})
		tp, ta = sum(i["planned_qty"] for i in items), sum(i["actual_qty"] for i in items)
		make("Laser Daily Plan Entry", {"plan_date": D, "shift": shift, "items": items, "total_plan": tp, "total_actual": ta,
		                                "efficiency": round(ta * 100 / tp, 1)}, submit=True, status="Submitted")

	for shift, base in (("Shift 1", 0), ("Shift 2", 7.5)):
		items = []
		for ws, run, rot in (("TN1", 7.6, 6.1), ("TN2", 7.2, 5.4), ("TNS5", 7.9, 6.9), ("TNS6", 7.5, 6.2), ("TO2", 7.0, 5.0)):
			items.append({"workstation": ws, "running_counter": 4120.5 + base + run, "rotation_counter": 3210.2 + base + rot,
			              "running_hours": run, "rotation_hours": rot, "shift_efficiency": round(rot * 100 / run, 1),
			              "day_efficiency": round((rot + rot - 0.3) * 100 / (run * 2), 1),
			              "source": "Machine API" if ws.startswith("TNS") else "Manual"})
		make("Machine Counter Reading", {"reading_date": D, "shift": shift, "reading_taken_by": E["Amr"], "items": items},
		     submit=True, status="Submitted")

	insp = []
	for jt, jc, so, op, recipe, bc, ins, passed, final, status in [
		("Dry Job Card", djc[0], SO4, "M.Whisker", LAWS, bins[SO4][0], 100, 98, 0, "Defect Raised"),
		("Wet Job Card", wjc[0], SO1, "Enzyme", BUCK, bins[SO1][0], 220, 212, 0, "Defect Raised"),
		("Wet Job Card", wjc[1], SO2, "Final Wash", CAMI, bins[SO2][0], 200, 200, 1, "Passed"),
		("Wet Job Card", wjc[3], SO3, "Dyeing", BLDY, bins[SO3][0], 120, 114, 0, "Defect Raised"),
	]:
		doc = make("Stage Inspection Entry", {
			"inspection_datetime": dt("12:30:00"), "shift": "A", "job_card_type": jt, "job_card": jc, "bin_card": bc,
			"sales_order": so, "style": frappe.db.get_value(jt, jc, "style"), "operation": op, "wash_recipe": recipe,
			"inspector": E["Rania"] if final else E["Yasser"], "is_final_validation": final, "inspected_qty": ins,
			"passed_qty": passed, "defect_qty": ins - passed, "verdict": "Pass" if ins == passed else "Defect",
			"bin_card_ticked": 1 if ins == passed else 0,
		}, submit=True, status=status)
		insp.append(doc)

	so_meta = {SO1: (720, 756, 0, "SS24260CK", "BUCKSIN"), SO4: (300, 315, 0, "DEN-9760A-50", "LAWSON"),
	           SO3: (1200, 1260, 0, "PQ-4410-WHT", "BLEACH+DYE")}
	rej = []
	for ins_doc, lines in [
		(insp[0], [("WR-10", "M", 1, "Back Pocket"), ("WR-09", "M", 1, "Front Pocket")]),
		(insp[1], [("WR-02", "L", 4, "Inseam"), ("WR-04", "L", 2, "Back Rise"), ("WR-01", "XL", 2, "Pocket Bag")]),
		(insp[3], [("WR-03", "L", 6, "Leg Panel")]),
	]:
		so = ins_doc.sales_order
		oq, cq, sq, fab, wash = so_meta[so]
		tot = sum(x[2] for x in lines)
		doc = make("Wash Rejection Entry", {
			"rejection_date": D, "shift": "A", "stage_inspection": ins_doc.name, "job_card_type": ins_doc.job_card_type,
			"job_card": ins_doc.job_card, "sales_order": so, "style": ins_doc.style, "fabric_name": fab, "wash_name": wash,
			"order_qty": oq, "cut_qty": cq, "ship_qty": sq,
			# Set disposition explicitly: a Select's default wins over fetch_if_empty on insert.
			"items": [{"wash_rejection_reason": r, "size": s, "rejected_qty": q, "defect_position": p,
			           "disposition": frappe.db.get_value("Wash Rejection Reason", r, "default_disposition"),
			           "remarks": "Checked against approved sample"} for r, s, q, p in lines],
			"total_rejected_qty": tot, "rejection_to_cut_pct": round(tot * 100 / cq, 2),
			"rejection_to_order_pct": round(tot * 100 / oq, 2), "approved_by": E["Rania"],
		}, submit=True, status="Disposition Approved")
		rej.append(doc)

	for src, rtype, op, ws, recipe, qty, rec_, off_to, status in [
		(rej[1], "Rewash", "Rewash", "TO2", BUCK, 6, 5, "Second Quality", "Partly Written Off"),
		(rej[0], "Rework", "Grinding", "MQ-01", None, 2, 2, None, "Recovered"),
		(rej[2], "Re-dye", "Dyeing", "DYE-T1", BLDY, 6, 6, None, "Recovered"),
	]:
		make("Rework and Rewash Entry", {
			"rework_date": D, "source_rejection": src.name, "sales_order": src.sales_order, "style": src.style,
			"rework_type": rtype, "operation": op, "workstation": ws, "wash_recipe": recipe,
			"rewash_chemicals_approved": 1 if recipe else 0, "approved_by": E["Rania"], "rework_qty": qty,
			"recovered_qty": rec_, "written_off_qty": qty - rec_, "written_off_to": off_to,
		}, submit=True, status=status)

	for jc, load_no, recipe, so, style, load_qty, lines, above in [
		(wjc[0], 1, BUCK, SO1, "J09HAMSHACK9649", 75, [("CHM-150000455", 0.40, 0.40), ("CHM-151076", 1.20, 1.25), ("CHM-150000618", 2.0, 2.0)], 0),
		(wjc[0], 3, BUCK, SO1, "J09HAMSHACK9649", 70, [("CHM-150000455", 0.37, 0.40), ("CHM-151076", 1.12, 1.50), ("CHM-150000618", 1.87, 1.9)], 1),
		(wjc[3], 1, BLDY, SO3, "T12POLO4410", 120, [("CHM-150000210", 2.50, 2.50), ("CHM-160000101", 1.80, 2.20), ("CHM-160000310", 0.40, 0.40)], 1),
		(djc[1], 1, LAWS, SO4, "J09HAMSHACK9649", 40, [("CHM-150000192", 0.25, 0.25)], 0),
	]:
		items = []
		for item, dose, issued in lines:
			rate = frappe.db.get_value("Item", item, "valuation_rate")
			items.append({"chemical_item": item, "recipe_dosage": dose, "issued_qty": issued, "variance": round(issued - dose, 3),
			              "price_per_unit": rate, "issue_value": round(issued * rate, 2)})
		jt = "Dry Job Card" if jc.startswith("WSH-DJC") else "Wet Job Card"
		make("Chemical Issue Entry", {
			"issue_datetime": dt("06:50:00"), "shift": "A", "job_card_type": jt, "job_card": jc, "load_no": load_no,
			"sales_order": so, "style": style, "wash_recipe": recipe, "load_qty": load_qty,
			"source_warehouse": W("Chemical Store CS02"), "issued_by": E["Samy"], "received_by": E["Mahmoud"], "items": items,
			"total_issue_value": sum(i["issue_value"] for i in items), "above_recipe": above,
			"deviation_approved_by": E["Hany"] if above else None,
		}, submit=True, status="Deviation Approved" if above else "Issued")

	for i, (dy, dn, wl, wd, wb, dis, el, gas) in enumerate([
		(1450, 3920, 205.0, 96.0, 18.0, 291.0, 10850, 2390), (1380, 4105, 214.0, 90.0, 17.5, 300.5, 11240, 2510),
		(1520, 3870, 199.5, 101.0, 18.2, 288.0, 10620, 2350), (1295, 4010, 221.0, 88.5, 19.0, 305.0, 11980, 2795),
	]):
		tp, tw = dy + dn, wl + wd + wb
		elpp, gpp = round(el / tp, 3), round(gas / tp, 3)
		make("Utility Consumption Entry", {
			"reading_date": add_days(D, -i), "recorded_by": E["Amr"], "dyeing_production": dy, "denim_production": dn,
			"total_production": tp, "water_laundry": wl, "water_dyeing": wd, "water_boiler": wb, "total_water": tw,
			"water_discharge": dis, "water_in_out_difference": round((tw - dis) * 100 / tw, 2),
			"water_ratio_dyeing": round(wd / dy, 3), "water_ratio_denim": round(wl / dn, 3), "total_water_ratio": round(tw / tp, 3),
			"total_electricity": el, "power_cost_dry": round(el * 0.35 * 1.6, 2), "power_cost_wet": round(el * 0.65 * 1.6, 2),
			"total_gas": gas, "electricity_per_piece": elpp, "gas_per_piece": gpp, "chemical_cost_per_piece": round(0.06 + i * 0.012, 3),
		}, submit=True, status="Objective Exceeded" if elpp > 1.8 or gpp > 0.5 else "Recorded")

	for so, style, wash, ins_doc, sizes, status in [
		(SO2, "D07CHINO2215", "CAMINO", insp[2], [("32", "PLT-1402", bins[SO2][0], 200), ("34", "PLT-1403", None, 196)], "Transferred"),
		(SO2, "D07CHINO2215", "CAMINO", insp[2], [("36", "PLT-1410", None, 198)], "Draft"),
	]:
		tot = sum(x[3] for x in sizes)
		make("Laundry Output Transfer", {
			"transfer_datetime": dt("15:20:00"), "shift": "A", "dc_agent": E["Walid"], "sales_order": so, "style": style,
			"wash_name": wash, "source_warehouse": W("Laundry WIP"), "target_warehouse": W("DC 3 - Finishing"),
			"quality_validation": ins_doc.name, "validated_by": E["Rania"],
			"items": [{"size": s, "pallet_no": p, "bin_card": b, "transferred_qty": q} for s, p, b, q in sizes],
			"total_transferred_qty": tot, "received_in_laundry": 1000, "rejected_in_laundry": 4, "wip_in_laundry": 402 if status == "Transferred" else 204,
		}, submit=status == "Transferred", status=status)


def clear():
	clear_doctypes(WASH_TX + ["Wash Rejection Reason"], ("WSH-", "BIN-"))


def run():
	clear()
	show_employee_names()
	E = seed_reference()
	seed_masters(E)
	seed_transactions(E)
	frappe.db.commit()
	for d in WASH_TX + ["Wash Rejection Reason"]:
		print(d, frappe.db.count(d))


run()

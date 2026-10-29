---
name: frs-doctype-automation
description: Produce a Sanskar Technolab Functional Requirement Document (FRS .docx + .pdf) for an ERPNext module from the client's BRD, To-Be Process and Process List — builds the module's DocTypes (schema only) in a custom Frappe app, seeds dummy data, captures list/form screenshots and Excel-style report mockups, and assembles the document in the exact Sanskar template (cover, version history, TOC, Chapter 1 Flowcharts, Chapter 2 Masters & Transactions, Chapter 3 Reports Mapping). Use when asked to create an FRS / FRD, or to build doctypes and screenshots for an FRS, from BRD / To-Be documents.
---

# FRS from BRD + To-Be → DocTypes, dummy data, screenshots, Sanskar FRS

The output is one FRS per module, in the Sanskar layout:

- **Cover + Document Version History:** client, module, process name, process IDs and descriptions, and the version table.
- **Table of Contents:** real page numbers.
- **Chapter 1 Flowcharts:** the To-Be flowchart from the To-Be document.
- **Chapter 2 Masters & Transactions:** per screen, the List View and Form View screenshots of a real record, then bullets covering overview, mandatory fields, auto-fetch, formulas, validation rules, approval workflow, integration, status, naming series and permissions. It ends with a Reference Masters section.
- **Chapter 3 Reports Mapping:** per report, purpose, filters and source; the current format from the BRD if it has one; an Excel-style proposed layout with sample data; and a mapping table (Field Name | ERPNext Doctype Name | ERPNext Field | Remark).

`examples/washing/` is a complete worked example: Vogue International, Washing module, 15 screens, 11 reports, 55 pages. **Read it before writing a new module.** Copy its structure and level of detail, not its content.

## Scope rules (agreed with the team)

- **DocTypes are schema only.** Write fields, child tables, naming, permissions and list/status indicators. Controllers stay `pass`. Write no client scripts, server scripts or hooks logic. Every rule, formula and workflow is written in the FRS text instead.
- **Always seed dummy data.** Every screen gets 3–5 realistic records that reuse the site's existing Sales Orders, Customers, Styles and Employees. Screenshots always show a saved record, never an empty "new" form.
- **Only screens the module owns.** Masters and transactions owned by the module get a section with screenshots. Data owned by other modules (Operation, Workstation, Item, Style, Sales Order, Work Order, Employee) is added as **Custom Fields** and listed in a final "Reference Masters and Records" section, with no screenshots. Records the system generates (scan logs, API logs) are described in text, not given screens. Planning-owned plans stay with Planning.
- **The To-Be overrides the BRD.** The To-Be document is often newer and contains items the BRD lacks (bin cards, scan control, KPI targets, replenishment rules…). Cover them, and label them "(To-Be)" in the text.
- **Ask the user** when scope is unclear, for example whether an item deserves its own screen. Don't guess big scope.

## Setup (once per machine)

```bash
python3 -m venv ~/.venvs/frs && ~/.venvs/frs/bin/pip install -r <skill>/requirements.txt
~/.venvs/frs/bin/playwright install chromium     # skip if Google Chrome is installed (capture.py uses it first)
sudo apt install libreoffice poppler-utils        # PDF render + TOC page numbers + BRD text/images
```

You also need:
- A running bench, e.g. `http://localhost:8000`, with the custom app installed and `developer_mode: 1` on the site.
- The site's login exported as `FRAPPE_USER` / `FRAPPE_PASSWORD`. **Never hard-code it or guess it — ask the user if it isn't set.**

Below, `PY=~/.venvs/frs/bin/python`, `SK=<skill folder>`, `BENCH=<bench path>`, and `W=<work folder>`. Use one work folder per module, outside the skill, for example `<bench>/outputs/work/<module>`.

## Pipeline

### 1. Read the inputs
```bash
$PY -I $SK/scripts/extract_inputs.py --out $W/inputs "<BRD>.pdf" "<To-Be>.docx" "<Process List>.xlsx"
```
- Read every `.txt` file in full: the BRD (masters, process, transaction fields, reports), the To-Be (process description and governing rules), and the process list (IDs and sub-processes).
- Look at the extracted images. In the To-Be, the image after the "(To Be)" heading is the flowchart; images are numbered in document order. In the BRD, the report-chapter pages hold the current report formats.
- Look at the existing app (`<app>/modules.txt`, `install.py`, other modules) and the site's data (Sales Orders, Customers, Styles, Employees, Warehouses).

### 2. Decide the screens and reports
List the masters and transactions that get screens, the custom fields on referenced masters, and the reports. That means the BRD reports, plus process-list reports, plus To-Be-only reports. Confirm with the user if anything is borderline.

### 3. DocTypes
Write `$W/doctypes_spec.py`; see `examples/washing/doctypes_spec.py` for the format. Then:
```bash
python3 $SK/scripts/gen_doctypes.py $W/doctypes_spec.py --app-path $BENCH/apps/<app>/<app> --module "<Module>"
```
- Add the module's roles and its custom fields on referenced masters to the app's `install.py` (see `examples/washing/custom_fields_example.py`).
- Then run `bench --site <site> migrate`.
- **Naming:** naming series per transaction (`WSH-LRE-.YY.-.#####`); `field:` or `format:` naming for masters.
- **Field conventions:**
  - Read-only `status` field with `states()` colours.
  - `fetch_from` for auto-fetched fields.
  - `depends_on` / `mandatory_depends_on` for conditional fields.
  - `Dynamic Link` when a transaction can point at more than one Job Card type.
- **Removing a DocType you dropped from scope:** `frappe.delete_doc("DocType", name, force=1)` (via `run_in_site.py`), and delete its folder.

### 4. Dummy data
Write `$W/seed.py`; see `examples/washing/seed.py`, which uses `scripts/seed_utils.py`. Then:
```bash
$BENCH/env/bin/python $SK/scripts/run_in_site.py --bench $BENCH --site <site> $W/seed.py
```
- Make the script re-runnable: `clear()` the module's transactions first, use `ensure()` for shared masters, and use `make(..., submit=True, status=...)` for transactions.
- Since there's no business logic, set computed fields (totals, percentages, cycle times) directly, and keep the numbers consistent with each other.
- Call `show_employee_names()` so link fields show names instead of `HR-EMP-…`. This creates a site-level Property Setter; tell the user.
- Use `swatch_image()` for Attach Image fields such as sample images.

### 5. Content
Write `$W/frs_content.py`; see the example for the format.
- **`META`:** client, optional client_logo, module, process name, process IDs and descriptions, versions, the flowchart path, and `brd_images_dir`.
- **`SCREENS`:** the record to capture for each screen, by name or filters. Pick records that show the interesting state, e.g. a Mismatch receipt or a rejection with several reasons.
- **`SECTIONS`:** Chapter 2 bullets in the fixed order: overview → Mandatory Fields → Auto-fetch → table / line fields → Formulas → Validation Rules → Approval Workflow (`Role =>` sub-bullets) → Integration → Status → Naming series → Print Format → Permissions, ending with "Final role mapping to be confirmed with the client."
- **`REPORTS`:** Chapter 3, with mockup rows that reuse the seeded data, `brd` set to the BRD image name when the BRD has a current format, and a mapping row for every column (use `—` for computed columns, with the formula in Remark).

### 6. Screenshots and mockups
```bash
cd $W && FRAPPE_USER=Administrator FRAPPE_PASSWORD=... $PY $SK/scripts/capture.py frs_content.py --out shots
```
- Use `--keys 2.4,3.1` to re-capture only some screens or reports.
- Before building, **view several screenshots**. Check for wrong data, IDs where names should be, and empty sections.

### 7. Build
```bash
cd $W && $PY $SK/scripts/build_frs.py frs_content.py --shots shots --out "<outputs>/<Client>-<Module>-FRS-V1.0.docx"
```
- This produces the `.docx` and `.pdf` (two passes, so the TOC page numbers are correct).
- Render a few pages (`pdftoppm -r 50 -png -f N -l N`) and look at them: cover, control tables, TOC, one screen section, one report.
- Copy the screenshots to `<app>/docs/frs_screens/<module>/`, as earlier modules did.

## Problems already hit (don't rediscover them)

- **v16 login:** the `/login` page selectors (`#login_email`, `.btn-login`) time out. `capture.py` logs in through `/api/method/login` instead.
- **Full-page screenshots:** Frappe desk scrolls inside `.main-section`, so Playwright's `full_page=True` only captures the viewport. `capture.py` resizes the viewport to the scroll height.
- **Sidebar and comments:** the left sidebar and the Comments/Activity footer are hidden in screenshots, matching earlier FRS documents.
- **Select field defaults:** on insert, a Select field's default (its first option) wins over `fetch_if_empty`. When seeding, set fetched Select values (e.g. disposition) explicitly.
- **Status on submittable DocTypes:** the list view shows "Draft" for any unsubmitted record, whatever its `status` is. Submit records that should show another status.
- **Wide reports:** mockups with more than about 12 columns become small at page width. The images are full resolution, so they stay readable when zoomed. Split very wide reports into two mockups if needed.
- **Site URL:** DocTypes exist on the site only after `migrate`. If the site isn't the default site, set `FRAPPE_URL`.

## Template

`templates/sanskar_frs_template.docx` is client-neutral. It holds the cover with `{{CLIENT}}` and a `{{CLIENT_LOGO}}` slot, the control and version tables, the TOC field, and after a `{{PROTOTYPES}}` marker one prototype of each element: the three chapter banners, heading, image, caption, bullet, sub-bullet, page break, spacer and mapping table. `build_frs.py` clones these prototypes. To restyle every FRS, edit the prototypes in Word and keep their order.

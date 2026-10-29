# FRS DocType Automation (Claude Code skill)

This skill turns a client's **BRD**, **To-Be Process** and **Process List** into a finished **Sanskar Technolab Functional Requirement Document (FRS)**, as both `.docx` and `.pdf`. Along the way it builds the module's **DocTypes** in your custom Frappe app, fills them with **dummy data**, and takes real **ERPNext screenshots**.

It was built and proven on the Vogue International **Washing** module: 15 screens, 11 reports, a 55-page FRS. That project is included as a worked example in `examples/washing/`.

---

## Contents

1. [What you get](#1-what-you-get)
2. [How it works (overview)](#2-how-it-works-overview)
3. [One-time setup](#3-one-time-setup)
4. [Using it with Claude Code (recommended)](#4-using-it-with-claude-code-recommended)
5. [The complete process, step by step](#5-the-complete-process-step-by-step)
6. [File formats you write per module](#6-file-formats-you-write-per-module)
7. [Folder structure](#7-folder-structure)
8. [The FRS template](#8-the-frs-template)
9. [Troubleshooting](#9-troubleshooting)
10. [Rules, scope and privacy](#10-rules-scope-and-privacy)

---

## 1. What you get

**An FRS document** in the standard Sanskar layout:

| Part | Content |
|---|---|
| Cover | "Functional Requirement Document", prepared for *Client* (optional client logo), submitted by Sanskar Technolab |
| Document Version History | Module name, process name, process IDs and descriptions, plus the version table (version, date, description, created by, approved by) |
| Table of Contents | Every chapter and section with **correct page numbers** |
| Chapter 1: Flowcharts | The To-Be process flowchart, taken from the To-Be document |
| Chapter 2: Masters & Transactions | For every screen: **List View** and **Form View** screenshots of a real saved record, then structured bullets (overview, mandatory fields, auto-fetch, formulas, validation rules, approval workflow, integration, status, naming series, print format, permissions). It ends with a "Reference Masters and Records" section |
| Chapter 3: Reports Mapping | For every report: purpose, filters and source; the **current format from the BRD** (when there is one); an **Excel-style proposed layout with sample data**; and a **field mapping table** (Field Name, ERPNext Doctype Name, ERPNext Field, Remark) |

**In your Frappe app:**
- A new module with all its DocTypes. These are **schema only**: fields, child tables, naming, permissions and status colours. There is no business logic.
- Roles and custom fields on shared masters (Operation, Workstation, Item…), added through `install.py`.
- 3–5 realistic dummy records per screen, linked to the site's existing Sales Orders, Customers, Styles and Employees.
- Screenshots copied to `<app>/docs/frs_screens/<module>/`.

---

## 2. How it works (overview)

```
 BRD.pdf ─┐
 To-Be.docx ─┼─▶ 1. extract_inputs.py ─▶ text + images (flowchart, current report formats)
 Process.xlsx ─┘                                   │
                                                   ▼
                                  2. Decide screens & reports (Claude + you)
                                                   │
                ┌──────────────────────────────────┼─────────────────────────────────┐
                ▼                                  ▼                                 ▼
     3. doctypes_spec.py                4. seed.py                         5. frs_content.py
        gen_doctypes.py                    run_in_site.py                     (META, SCREENS,
        + install.py + migrate             (dummy data)                        SECTIONS, REPORTS)
                │                                  │                                 │
                └──────────────► ERPNext site ◄────┘                                 │
                                     │                                               │
                                     ▼                                               │
                          6. capture.py ─▶ list/form screenshots + report mockups ◄──┘
                                     │
                                     ▼
                          7. build_frs.py + template ─▶ FRS .docx + .pdf (TOC page numbers)
```

The **scripts are generic**. For each module you write only **three small Python files**:
- `doctypes_spec.py`: which DocTypes and fields to create.
- `seed.py`: the dummy data.
- `frs_content.py`: the document text, which screens to capture, and the report mockups.

When you use Claude Code, Claude writes these three files for you from the BRD and To-Be.

---

## 3. One-time setup

### 3.1 System packages (Ubuntu / Debian)

```bash
sudo apt install libreoffice poppler-utils
```
- **LibreOffice** renders the `.docx` to PDF and works out the TOC page numbers.
- **poppler-utils** provides `pdftotext` and `pdfimages`, used to read the BRD PDF.

### 3.2 Python environment for the scripts

The scripts that run *outside* the bench use their own virtualenv:

```bash
python3 -m venv ~/.venvs/frs
~/.venvs/frs/bin/pip install -r <skill-folder>/requirements.txt
```

### 3.3 Browser for screenshots

If **Google Chrome** is installed, nothing more is needed; `capture.py` uses it automatically. Otherwise:

```bash
~/.venvs/frs/bin/playwright install chromium
```

### 3.4 Frappe bench

- A running bench, e.g. `bench start`, reachable at `http://localhost:8000`. Set `FRAPPE_URL` if it runs somewhere else.
- Your custom app (e.g. `garment_erp`) installed on the site.
- `"developer_mode": 1` in the site's `site_config.json`, so DocTypes are saved as files in the app.
- A user that can log in to the desk, usually `Administrator`.

### 3.5 Installing the skill

Copy (or clone) this folder to either location:
- `<your-bench>/.claude/skills/frs-doctype-automation/`: available when Claude Code runs inside that bench.
- `~/.claude/skills/frs-doctype-automation/`: available in every project.

To check that it loaded, type `/` in Claude Code and look for `frs-doctype-automation`.

---

## 4. Using it with Claude Code (recommended)

1. Put the client's documents somewhere on disk: BRD (`.pdf`/`.docx`), To-Be Process (`.docx`), Process List (`.xlsx`).
2. Start Claude Code in your bench folder (`cd ~/project/frappe-bench && claude`).
3. Ask, for example:

   > Here are the Cutting BRD, To-Be Process and Process List in ~/project/. Create the FRS for the Cutting module in garment_erp. Don't add logic, just DocTypes with dummy data. Only masters and processes owned by Cutting.

4. Claude will:
   - read all three documents, including the images;
   - propose the list of screens and reports, and **ask you** about anything borderline;
   - write the spec, seed and content files, generate the DocTypes, run migrate and seed the data;
   - **ask you for the site password** if `FRAPPE_PASSWORD` isn't set (it is never stored);
   - capture the screenshots, check them visually, build the FRS and show you the result.

5. Review the document. Ask for changes in plain language, for example "drop the Machine Scan Log screen", "add a section for Shade Band Approval", or "the rejection screenshot shows the wrong disposition". Claude edits the three files and re-runs only the steps that are needed.

**Tip:** you can save Claude a question by setting the login before you start:
```bash
export FRAPPE_USER=Administrator
export FRAPPE_PASSWORD='<your password>'
```

---

## 5. The complete process, step by step

These are the same steps Claude follows. Run them by hand when you want full control or need to fix one stage.

The commands use these shortcuts:

```bash
PY=~/.venvs/frs/bin/python                         # script venv
SK=<path>/frs-doctype-automation                   # this skill
BENCH=~/project/frappe-bench                       # your bench
W=$BENCH/outputs/work/cutting                      # one work folder per module
mkdir -p $W
```

### Step 1: Extract the inputs

```bash
$PY -I $SK/scripts/extract_inputs.py --out $W/inputs \
    "Client - Cutting - BRD.pdf" "Client - Cutting - To Be Process.docx" "Client-Cutting-Process List.xlsx"
```

It produces, for each input:
- **`<name>.txt`** with the full text.
  - **PDF:** layout preserved.
  - **DOCX:** every paragraph is tagged `[Heading 2]`, `[normal]` and so on; tables appear as `| a | b |` rows; each image appears as an `<IMAGE 03.png>` marker at the exact place it sits in the document.
  - **XLSX:** every sheet, row by row.
- **`<name>-img/`** with the embedded images.
  - **To-Be:** `01.png`, `02.png`… in document order. The image after the "(To Be)" heading is the flowchart.
  - **BRD:** `p038-000.png`… (page number + index) for every large image. These are usually the process flowcharts and the **current report formats** in the reports chapter.

Read all of it. The **To-Be is usually newer than the BRD** and adds requirements the BRD doesn't have. For Washing, these were the Bin Card, scan control, shade segregation, KPI targets and the chemical replenishment rule.

### Step 2: Decide screens and reports

Write down three lists:
- **Screens** (each gets a Chapter 2 section with screenshots): the module's own **masters** (e.g. Wash Recipe, Wash Rejection Reason, Washing Settings) and **transactions** (e.g. Laundry Receipt Entry, Job Cards, Inspection, Rejection, Transfer).
- **Custom fields on shared masters** owned by other modules (Operation, Workstation, Item…). These are described in the "Reference Masters" section, without screenshots.
- **Reports** (Chapter 3): the BRD reports chapter, plus reports in the process list, plus reports the To-Be mentions.

Leave out screens for data owned by other modules, and for records the system generates by itself (scan logs, API logs). Describe those in text instead.

### Step 3: Generate the DocTypes

1. Write `$W/doctypes_spec.py`. Copy the style of `examples/washing/doctypes_spec.py`, and see [§6.1](#61-doctypes_specpy) for the format.
2. Generate the files into your app:
   ```bash
   python3 $SK/scripts/gen_doctypes.py $W/doctypes_spec.py \
       --app-path $BENCH/apps/garment_erp/garment_erp --module "Cutting"
   ```
   This creates `garment_erp/cutting/doctype/<doctype>/` with `.json`, an empty `.py` controller and `__init__.py`, and adds `Cutting` to `modules.txt`.
3. In the app's `install.py`, add the module's **roles** to the `ROLES` tuple, and its **custom fields** on shared masters (see `examples/washing/custom_fields_example.py`).
4. Apply everything to the site:
   ```bash
   cd $BENCH && bench --site erp.localhost migrate
   ```

**To drop a DocType later:** remove it from the spec, delete its folder, and delete it from the site with `frappe.delete_doc("DocType", "<Name>", force=1)` run through `run_in_site.py`.

### Step 4: Seed dummy data

1. Write `$W/seed.py`, following `examples/washing/seed.py`.
2. Run it **with the bench's own Python**:
   ```bash
   $BENCH/env/bin/python $SK/scripts/run_in_site.py --bench $BENCH --site erp.localhost $W/seed.py
   ```

Guidelines:
- **Make it re-runnable.** Start with `clear([...transactions...], ("PREFIX-",))`, which deletes the module's records and resets their naming series.
- Use `ensure(doctype, name, values)` for shared masters (Workstation, Operation, Item, Warehouse) so existing ones are updated, not duplicated.
- Use `make(doctype, values, submit=True, status="Completed")` for transactions. With no business logic, **you set the computed values yourself** (totals, percentages, cycle times), so keep them consistent with each other.
- Reuse the site's existing Sales Orders, Customers and Styles. Create a few named Employees with `employee()`.
- `swatch_image()` creates a fabric-like picture for image fields such as sample images.
- `show_employee_names()` makes link fields show "Rania Kamal" instead of "HR-EMP-00031". It adds a site-level Property Setter on Employee; to undo it, delete that Property Setter.
- Pick a mix of states that makes the screenshots meaningful: some submitted, one draft, one "Mismatch", one "On Hold".

### Step 5: Write the content

Write `$W/frs_content.py` (see [§6.3](#63-frs_contentpy)). It has four parts:
- **`META`:** cover and control-table data, plus the path to the flowchart image.
- **`SCREENS`:** which record to screenshot for each section.
- **`SECTIONS`:** the Chapter 2 text, as bullets.
- **`REPORTS`:** the Chapter 3 mockup data and field mapping.

### Step 6: Capture screenshots and mockups

```bash
cd $W
FRAPPE_USER=Administrator FRAPPE_PASSWORD='...' $PY $SK/scripts/capture.py frs_content.py --out shots
```

- **Screens:** logs in through the API, resolves each record, and takes the list view plus a **full-height** form view with the left sidebar and the comments/activity footer hidden.
  - Files: `2.4-a-laundry-receipt-entry-list.png`, `2.4-b-laundry-receipt-entry-form.png`.
- **Mockups:** renders each report as an Excel-looking sheet with column letters, row numbers, an orange code cell, a yellow header and a total row.
  - Files: `3.1-report-mockup.png`.
- **Options:**
  - `--only screens` or `--only mockups` runs one half.
  - `--keys 2.4,2.11,3.1` re-captures only those items.
  - `--channel ''` uses Playwright's Chromium instead of Chrome.

**Look at the screenshots before building.** Check for wrong values, missing data, IDs instead of names, and empty child tables. Fix the seed, re-run step 4, then re-capture only the affected keys.

### Step 7: Build the FRS

```bash
cd $W
$PY $SK/scripts/build_frs.py frs_content.py --shots shots \
    --out "$BENCH/outputs/Client-Cutting-FRS-V1.0.docx"
```

1. **Pass 1** builds the `.docx`, renders it to PDF with LibreOffice, and finds the page of every heading.
2. **Pass 2** rebuilds with those page numbers in the TOC and renders the final `.pdf`.

The script prints the page of each heading and warns if one could not be found. Use `--no-pdf` for a quick docx-only build (the TOC page numbers stay blank).

**Check the result.** Render a few pages and look at them:
```bash
pdftoppm -r 50 -png -f 1 -l 4 "Client-Cutting-FRS-V1.0.pdf" /tmp/page
```

Finally, copy `shots/*.png` to `<app>/docs/frs_screens/<module>/`.

### Making changes later

| Change | Re-run |
|---|---|
| FRS wording only | Edit `SECTIONS` / `REPORTS` text → step 7 |
| Report sample data | Edit `REPORTS` rows → step 6 with `--only mockups` → step 7 |
| Dummy data | Edit `seed.py` → step 4 → step 6 (`--keys …`) → step 7 |
| Fields / new screen | Edit spec → step 3 (+ migrate) → step 4 → step 6 → step 7 |
| New version of the FRS | Add a row to `META["versions"]`, change the `--out` file name → step 7 |

---

## 6. File formats you write per module

### 6.1 `doctypes_spec.py`

Plain Python that calls the helpers from `gen_doctypes.py`:

```python
from gen_doctypes import F, cb, sb, series, doctype, std_perms, states, status_field

# child table
doctype("Bin Card Operation", [
    F("sequence", "Int", "Seq", reqd=1, in_list_view=1, columns=1),
    F("operation", "Link", "Operation", "Operation", reqd=1, in_list_view=1, columns=2),
    F("quality_passed", "Check", "QC Passed", in_list_view=1, columns=1),
], "Operation sequence with quality tick box.", istable=True)

# transaction
doctype("Bin Card", [
    series("BIN-.YY.-.#####"),
    F("sales_order", "Link", "Sale Order", "Sales Order", reqd=1, in_list_view=1, in_standard_filter=1),
    F("customer", "Link", "Buyer", "Customer", fetch_from="sales_order.customer", read_only=1),
    cb(1),
    F("shade", "Data", "Shade", reqd=1, in_list_view=1),
    status_field(["Open", "In Process", "Completed"], "Open"),
    sb(1, "Operation Sequence"),
    F("operations", "Table", "Operations", "Bin Card Operation"),
], "Physical bin per shade, PO and lot.",
    autoname="naming_series:", title_field="shade",
    states=states("Open", "In Process", "Completed"),
    perms=std_perms(("Laundry Manager",), ("DC Agent",), ("Quality Manager",)))
```

| Helper | Purpose |
|---|---|
| `F(fieldname, fieldtype, label, options, **props)` | One field; any DocField property as a keyword (`reqd`, `read_only`, `fetch_from`, `depends_on`, `mandatory_depends_on`, `in_list_view`, `columns`, `description`, `default`, …) |
| `cb(n)` / `sb(n, "Label")` | Column break / section break (n just keeps names unique) |
| `series("PFX-.YY.-.#####")` | Naming series field |
| `status_field(options, default)` | Read-only Status shown in the list view |
| `states(...)` | List-view status colours |
| `std_perms(managers, users, readers, submittable)` | Standard permission rows (System Manager always included) |
| `doctype(name, fields, description, submittable=, istable=, issingle=, autoname=, perms=, title_field=, search_fields=, image_field=, states=)` | Registers a DocType |

### 6.2 `seed.py`

Normal Python run inside the site (it can use `frappe` directly), plus the helpers in `seed_utils.py`: `ensure`, `make`, `clear`, `employee`, `swatch_image`, `show_employee_names`, `at`. See `examples/washing/seed.py`.

### 6.3 `frs_content.py`

```python
META = {
    "client": "Vogue International",
    "client_logo": "client_logo.png",          # optional; omit = no logo on the cover
    "module": "Washing",
    "process_name": "End-to-End Washing Process",
    "process_ids": "1.1.1, 1.2.1, 1.3.1, ...",
    "process_desc": ["Washing Masters", "Wash Recipe and Sample Approval", ...],
    "versions": [{"version": "V 1.0", "date": "29-10-2026",
                  "description": ["To Be Process Flow", "Masters & Transactions", "Reports Mapping"],
                  "created_by": "<author>", "approved_by": "<approver>"}],
    "flowchart": "inputs/<To-Be name>-img/03.png",
    "flowchart_caption": "To Be Process – Washing (V 1.2)",
    "brd_images_dir": "inputs/<BRD name>-img",
}

SCREENS = [                                    # what capture.py screenshots
    {"key": "2.1", "doctype": "Wash Recipe", "record": "WR-BUCK-V2", "list": True},   # by name
    {"key": "2.3", "doctype": "Washing Settings", "single": True},                     # Single DocType
    {"key": "2.4", "doctype": "Laundry Receipt Entry", "list": True},                  # oldest record
    {"key": "2.7d", "doctype": "Wet Job Card", "filters": {"operation": "Dyeing"}},    # by filters, extra form only
]

SECTIONS = [                                   # Chapter 2
    {"no": "2.4", "title": "Laundry Receipt Entry",
     "shots": [("2.4-a-laundry-receipt-entry-list.png", "List View"),
               ("2.4-b-laundry-receipt-entry-form.png", "Form View")],
     "items": [
         ("b", "", "Overview sentence ..."),                 # bullet, no bold label
         ("b", "Mandatory Fields:", "Sale Order, ..."),      # bullet with bold label
         ("b", "Approval Workflow:", ""),
         ("s", "DC Agent =>", "posts the receipt ..."),      # sub-bullet with bold label
         ("s", "", "Final role mapping to be confirmed with the client."),
     ]},
]

REPORTS = [                                    # Chapter 3
    {"no": "3.1", "name": "Laundry Status & WIP Report", "code": "LSW",
     "brd": "p038-000.png",                    # optional: current format image from the BRD
     "purpose": "...", "filters": "Date, Buyer, Sale Order",
     "cols": ["SO", "Buyer", "Qty", ...],
     "rows": [["SAL-ORD-2026-00001", "Levant Denim Co", 720, ...], ...],
     "total": True,                            # adds a Total row (numeric columns)
     "map": [("SO", "Sales Order", "name", "Orders with a submitted receipt"), ...]},
]
```

Optional mockup keys:
- `head_rows`: label rows above the header, e.g. Buyer, Style or Cycle Time per machine.
- `group_row`: a band above the header, e.g. stage groups.
- `flag: True`: KPI style. Column 3 is the objective, and higher values show in red.
- `no_total_cols`: columns never summed.
- Any cell with the value `"Yes"` shows in red.

**Order of Chapter 2 bullets** (keep it consistent across every FRS):
1. Overview
2. Mandatory Fields
3. Auto-fetch
4. Table / line fields
5. Formulas
6. Validation Rules
7. Approval Workflow (`Role =>` sub-bullets)
8. Integration
9. Status
10. Naming series
11. Print Format
12. Permissions, ending with "Final role mapping to be confirmed with the client."

---

## 7. Folder structure

```
frs-doctype-automation/
├── README.md                     ← this file (for people)
├── SKILL.md                      ← instructions Claude follows
├── requirements.txt              ← python-docx, openpyxl, playwright, pillow, lxml
├── scripts/
│   ├── extract_inputs.py         ← BRD / To-Be / Process List → text + images
│   ├── gen_doctypes.py           ← DocType DSL + generator (writes into the app)
│   ├── run_in_site.py            ← runs a script inside the Frappe site
│   ├── seed_utils.py             ← helpers for dummy-data scripts
│   ├── capture.py                ← list/form screenshots + report mockups
│   └── build_frs.py              ← assembles the FRS (.docx + .pdf, TOC page numbers)
├── templates/
│   └── sanskar_frs_template.docx ← client-neutral Sanskar template
└── examples/
    └── washing/                  ← complete worked example (Vogue International)
        ├── doctypes_spec.py
        ├── custom_fields_example.py
        ├── seed.py
        ├── frs_content.py
        └── client_logo.png
```

**Work folder per module** (outside the skill; not committed):
```
outputs/work/<module>/
├── inputs/            ← from extract_inputs.py
├── doctypes_spec.py
├── seed.py
├── frs_content.py
└── shots/             ← from capture.py
```

---

## 8. The FRS template

`templates/sanskar_frs_template.docx` contains the cover page (with `{{CLIENT}}` text and a `{{CLIENT_LOGO}}` picture slot), the document control and version tables, and the Table of Contents field.

After a `{{PROTOTYPES}}` marker comes one sample of each building block, **in this order**:
1. Chapter 1 banner
2. Chapter 2 banner
3. Chapter 3 banner
4. Section heading
5. Picture
6. Caption
7. Bullet
8. Sub-bullet
9. Page break
10. Spacer
11. Mapping table

`build_frs.py` copies these blocks, so the output keeps the exact fonts, colours, numbering and table styles.

**To change the house style for every future FRS**, open the template in Word, restyle those blocks, and save. **Don't** reorder or delete them, or the builder will pick up the wrong block.

---

## 9. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Login failed` / `Set FRAPPE_PASSWORD` | Export `FRAPPE_USER` and `FRAPPE_PASSWORD`; check the bench is running and `FRAPPE_URL` is right |
| `No <DocType> record matches …` | Seed data missing, or the `filters` in `SCREENS` match nothing |
| Screenshot shows only the top of the form | You're not using `capture.py` (it resizes to the full scroll height of `.main-section`) |
| Link fields show `HR-EMP-000xx` | Call `show_employee_names()` in the seed |
| A Select field shows its first option instead of the fetched value | On insert, the Select default wins over `fetch_if_empty`; set the value explicitly in the seed |
| List shows "Draft" though status is set | Unsubmitted submittable records always show Draft; submit them in the seed |
| DocType missing on the site | Run `bench --site <site> migrate`; check the module is in `modules.txt` |
| TOC page numbers blank | LibreOffice (`soffice`) not installed, or `--no-pdf` used |
| `headings not found in PDF` warning | A heading wrapped oddly in the PDF; shorten the section title or check that page |
| Report mockup too small in the document | Report has too many columns; split it into two mockups, or accept it (full resolution, zoomable) |
| `missing image …` while building | Wrong file name in `SECTIONS["shots"]`, `META["flowchart"]` or a report's `brd` |
| Chrome not found | `playwright install chromium` and pass `--channel ''` |

---

## 10. Rules, scope and privacy

- **No business logic in ERPNext.** DocTypes are schema only, with empty controllers and no client or server scripts. All rules, formulas and workflows go in the FRS text. Logic is built later, from the approved FRS.
- **Always dummy data**, so every screenshot shows a saved, realistic record.
- **Only module-owned screens.** Shared masters get custom fields and a mention in "Reference Masters"; they don't get screenshots.
- **The To-Be counts.** Items that are only in the To-Be are covered and marked "(To-Be)".
- **Credentials:** never put passwords in any file. The scripts read them from environment variables only.
- **Client data:** `examples/washing/` contains Vogue International's logo, order numbers and process details. **Keep this repository private**, or delete `examples/` before publishing it anywhere public. Never commit work folders (`inputs/`, `shots/`) or generated FRS files to a public repository.

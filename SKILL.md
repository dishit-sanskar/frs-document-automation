---
name: frs-doctype-automation
description: Automate creating ERPNext DocTypes, dummy records, UI & report screenshots, and compiling Functional Requirement Specification (FRS) documents adhering strictly to Sanskar Technolab's exact document template layout (Cover Page, History Table, Flowcharts, Masters & Transactions with List/Form View screenshots, and Reports Mapping with excel tables). Use when asked to generate FRS documentation, build ERPNext doctypes, or draft FRS content with screenshots.
---

# FRS to ERPNext DocType, Screenshots & Google Doc Generator

Automate the end-to-end workflow of reading Business Requirement Documents (BRD) and To-Be Process documents, writing FRS content in Sanskar Technolab's exact document structure, creating DocTypes and dummy records on local ERPNext (`http://localhost:8000`), capturing List View, Form View, and Report screenshots, and assembling the final document.

## Document Structure & Template Rules

Every generated FRS document MUST follow this exact 3-chapter structure:

### 1. Cover Page & Document Control
- **Header / Branding**: Prepared for *Client Name* (e.g., Vogue International), Submitted by *Sanskar Technolab Pvt. Ltd*.
- **Document Control Block**:
  - `Module Name` | `Process Name` | `Process ID & Description`
- **Document Version History Table**:
  - `Document Version` | `Issue Date` | `Description` | `Created By` | `Approved By`
- **Table of Contents**: Formatted hierarchy linking Chapter 1, Chapter 2, and Chapter 3.

---

### 2. Chapter 1: Flowcharts
- **1.1 To Be Process Flow**: Embed high-resolution To-Be workflow process diagram / flowchart showing end-to-end operational decisions, system triggers, and manual touchpoints.

---

### 3. Chapter 2: Masters & Transactions
For EACH Doctype / Transaction / Master in the module:
1. **List View Screenshot**: Captured directly from local ERPNext showing list records.
2. **Form View Screenshot(s)**: Captured from local ERPNext showing main form fields, child tables, and action buttons.
3. **Structured Explanation**:
   - High-level overview and ownership.
   - **Mandatory Fields**: Key required fields.
   - **Auto-fetch & Formulas**: Fields populated from upstream masters/orders.
   - **Validation Rules**: Data constraints, blocking triggers, logic checks.
   - **Approval Workflow**: Operational roles (Supervisor, Manager, QC, etc.) and permission steps.
   - **Integration & Alerts**: Downstream triggers, notifications, and stock/ledger movements.
   - **Permissions & Status**: Role access matrix and document status lifecycle (`Draft`, `Submitted`, `Completed`, etc.).

---

### 4. Chapter 3: Reports Mapping
For EACH report identified in the To-Be process:
1. **Excel Sheet Mockup / Report Screenshot**: Showing sample tabular data layout with dummy values.
2. **ERPNext Field Mapping Table**:
   | Field Name | ERPNext Doctype Name | ERPNext Field | Remark |
   | :--- | :--- | :--- | :--- |

---

## Technical Execution Pipeline

1. **Parse Requirements**: Extract module name, doctypes, process IDs, field definitions, validation rules, and report structures from BRD & To-Be documents.
2. **Draft FRS Content**: Write all explanatory text, field rules, and report mapping tables using the standard Sanskar Technolab template structure above.
3. **ERPNext DocType & Data Creation**: Execute Python scripts (`frappe_api.py`) via REST API on `http://localhost:8000` to create DocTypes, build custom fields, and populate dummy test records.
4. **Capture UI & Report Screenshots**: Use Playwright (`capture_screenshots.py`) to log in, navigate to each DocType list view, form view, and report view, and save PNG screenshots.
5. **Assemble Document**: Use `python-docx` / Google Docs API (`generate_docx.py`) to merge text, tables, and screenshots into the final `.docx` or Google Doc file matching Sanskar Technolab formatting.

---

## Gotchas & Format Guidelines

- **Exact Formatting**: Maintain Sanskar Technolab branding, corporate header/footer styling, and table schemas as seen in the sample FRS files.
- **Report Screenshots**: Always ensure report screenshots display filled dummy data and clear column headers.
- **ERPNext Naming**: Match `fieldname` standards (lowercase, underscores).
- **Page Wait**: Wait 2–2.5 seconds for ERPNext desk tables and report layouts to completely render before capturing screenshots.

# FRS Generator for Claude Code

This skill lets Claude Code create a complete **Functional Requirement Document (FRS)** in the Sanskar Technolab format. You give it the client's **BRD**, **To-Be Process** and **Process List**, and Claude:

- creates the screens (DocTypes) for that module in our ERPNext app, with sample data;
- takes screenshots of every screen;
- prepares the report layouts;
- writes the full FRS document as Word and PDF, ready to review.

---

## Setup (one time only)

### 1. Install the required tools

Open a terminal and run:

```bash
sudo apt install libreoffice poppler-utils
python3 -m venv ~/.venvs/frs
~/.venvs/frs/bin/pip install -r ~/project/frappe-bench/.claude/skills/frs-doctype-automation/requirements.txt
```

If Google Chrome is **not** installed on your machine, also run:

```bash
~/.venvs/frs/bin/playwright install chromium
```

### 2. Add the skill to your bench

Copy this whole `frs-doctype-automation` folder into your bench:

```
~/project/frappe-bench/.claude/skills/frs-doctype-automation/
```

### 3. Start your bench

```bash
cd ~/project/frappe-bench
bench start
```

Make sure you can open ERPNext in the browser (for example `http://localhost:8000`) and log in.

### 4. Check that Claude Code can see the skill

Open a new terminal and run:

```bash
cd ~/project/frappe-bench
claude
```

Type `/` and look for **frs-doctype-automation** in the list. If it's there, setup is done.

---

## How to use it

### 1. Keep the client documents ready

Save the three files somewhere on your computer, for example in `~/project/`:

- BRD (PDF or Word)
- To-Be Process (Word)
- Process List (Excel)

### 2. Ask Claude

In Claude Code (started inside your bench folder), type something like:

> Here are the Cutting BRD, To-Be Process and Process List in ~/project/. Please create the FRS for the Cutting module in garment_erp. Only add DocTypes with dummy data, no logic. Only include masters and processes owned by Cutting.

Change the module name and file location to match your project.

### 3. Answer Claude's questions

While it works, Claude may ask you:

- **Which screens to include**, if something in the documents is unclear.
- **Your ERPNext login password**, so it can take screenshots. You can avoid this question by setting the password before starting Claude:

  ```bash
  export FRAPPE_PASSWORD='your-password'
  claude
  ```

### 4. Get your document

When Claude finishes, it tells you where the FRS is saved, usually in the `outputs` folder of your bench:

```
~/project/frappe-bench/outputs/<Client>-<Module>-FRS-V1.0.docx
~/project/frappe-bench/outputs/<Client>-<Module>-FRS-V1.0.pdf
```

### 5. Ask for changes

Open the document and review it. If something needs to change, just tell Claude in plain words, for example:

- "Remove the Machine Scan Log section."
- "Add a screen for Shade Band Approval."
- "The rejection screenshot shows the wrong value, please fix it."
- "Make version 1.1 with the updated To-Be document."

Claude updates only what is needed and rebuilds the document.

---

## Good to know

- **No business logic is built.** Claude only creates the screens and sample data needed for the screenshots. All rules and calculations are written in the FRS document.
- **The To-Be document is considered too.** Things that appear only in the To-Be and not in the BRD are also covered in the FRS.
- **Never share your password in a file.** Give it to Claude when it asks, or set it as shown above.
- **This repository contains client examples.** Keep it **private**.

---

## Need help?

If something doesn't work, ask Claude directly in the same session, for example: *"The screenshots failed, what went wrong?"* For technical details, see `SKILL.md` in this folder.

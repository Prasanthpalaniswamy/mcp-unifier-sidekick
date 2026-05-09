# MCP Unifier Sidekick - User Guide

## 1. What this agent is

This project is a **smart assistant server** that connects to **Oracle Unifier** and helps you do useful business tasks around the data you fetch.

In simple words, this agent can:

- connect to Unifier
- fetch data from Unifier
- export that data into files like **CSV, Excel, PDF, and Word**
- create **charts, dashboards, and table images**
- **compress** files into ZIP
- **split large files** into smaller parts for email transfer
- **send emails** with attachments
- help rebuild split files at the receiver side

You can think of it as a **data assistant + reporting assistant + file handling assistant + email assistant** all in one.

---

## 2. Main purpose of this agent

The main purpose of this agent is to make it easy to:

1. **get information from Unifier**
2. **turn that information into usable files**
3. **visualize it in charts and dashboards**
4. **share it through email**
5. **handle large files safely** by compressing and splitting them

This means even a non-technical user can use the same flow:

**Fetch -> Export -> Visualize -> Compress if needed -> Email**

---

## 3. High-level features available today

### Unifier connection and data access
- Start a Unifier session
- Clear a Unifier session
- Check whether the current session is active
- List projects
- List data elements
- List data definitions
- Create data elements
- Bulk-create data elements from Excel
- List users
- List BP records

### Exporting and document generation
- Export JSON-style data to **CSV**
- Export JSON-style data to **XLSX**
- Export JSON-style data to **PDF**
- Export JSON-style data to **DOCX**
- Convert a **DOCX file into a PDF** using a machine-independent content-based approach

### Visualization
- Generate **chart images**
- Generate **summary dashboards**
- Generate **table images**

### Email and file delivery
- Send plain-text emails
- Send emails with attachments

### File size management
- Compress files into ZIP
- Split large files into smaller parts
- Provide instructions to rebuild split files later

---

## 4. Project structure

Here is the important file structure in plain language:

- `server.py`
  - the main MCP server
  - exposes all the tools that users can call

- `tools/unifier_tools.py`
  - contains Unifier API logic
  - handles authentication and requests to Unifier

- `tools/supporting_tools.py`
  - contains export, conversion, compression, splitting, and email logic

- `tools/visualization_tools.py`
  - contains chart, dashboard, and table-image generation logic

- `tools/session_store.py`
  - stores current session information for each connected client

- `requirements.txt`
  - Python package dependencies

---

## 5. How the agent works overall

This agent runs as an **MCP server**.

That means other clients or assistants can call the tools defined in `server.py`.

Every tool is exposed with `@mcp.tool()`.

So when someone asks the assistant to:

- connect to Unifier
- fetch definitions
- export to CSV
- make a chart
- email the result

the server can perform those actions through the matching tool functions.

---

## 6. Unifier-related tools

These are the tools used to work directly with Oracle Unifier.

### 6.1 `init_unifier`

**Purpose:**
Starts a Unifier session.

**What it needs:**
- `base_url`
- `username`
- `password`

**What it does:**
- validates the URL
- validates the username
- validates the password
- stores the session for the current client

**Why it matters:**
This is the starting point before most Unifier actions.

---

### 6.2 `clear_unifier_session`

**Purpose:**
Removes the currently stored Unifier session.

**Use case:**
- when changing environments
- when changing user credentials
- when you want a clean reset

---

### 6.3 `get_current_unifier_session`

**Purpose:**
Shows whether the current client is connected.

**Returns safe information only:**
- connected or not
- base URL
- username
- whether token exists

It does **not** expose the password.

---

### 6.4 `list_projects`

**Purpose:**
Returns projects from Unifier.

**Common use case:**
- fetch projects for reporting
- inspect available shells/projects

---

### 6.5 `list_data_elements`

**Purpose:**
Returns custom data elements from Unifier.

**Filters supported:**
- data element name
- data definition
- form label
- description
- tooltip

---

### 6.6 `list_data_definitions`

**Purpose:**
Returns data definitions from Unifier.

**Supported types:**
- Basic
- Cost Codes
- Data Picker

**Optional filters:**
- name
- data source

This tool was used earlier to fetch the Data Picker definitions successfully.

---

### 6.7 `create_data_element`

**Purpose:**
Creates a new custom data element in Unifier.

**Can handle special parameters for some definitions**, such as:
- decimal format
- height
- number of lines
- hide currency symbol

---

### 6.8 `bulk_create_data_elements_from_excel`

**Purpose:**
Reads an Excel file and bulk-creates data elements in Unifier.

**What it also does:**
- generates an Excel response report
- saves fallback report if the main output file is locked

---

### 6.9 `list_users`

**Purpose:**
Fetches users from Unifier.

**Use cases:**
- user reporting
- active/inactive user filtering

---

### 6.10 `list_bp_records`

**Purpose:**
Fetches Business Process records.

**Supports:**
- company level or project level record access
- record fields selection
- filter condition
- filter criteria
- optional line item fetching

---

## 7. Export tools

These tools turn fetched content into useful files.

All these export tools accept similar input styles:

- a JSON string
- a list of objects
- a single object
- a response object containing a `data` list

This makes the export tools flexible and easy to reuse.

---

### 7.1 `export_content`

**Purpose:**
Exports content to either:
- `.csv`
- `.xlsx`

**Typical use cases:**
- share raw tabular data
- prepare data for Excel users
- archive fetched JSON into a spreadsheet format

---

### 7.2 `export_content_to_pdf_tool`

**Purpose:**
Exports content into a simple PDF report.

**Important note:**
This is not a visually rich report generator.
It creates a practical text-based PDF representation of the data.

---

### 7.3 `export_content_to_docx_tool`

**Purpose:**
Exports content into a Word `.docx` file.

**What it creates:**
- heading
- row count
- data table

**Useful for:**
- management sharing
- documentation packs
- Word-based reporting workflows

---

## 8. Word-to-PDF conversion tool

### 8.1 `convert_docx_to_pdf_tool`

**Purpose:**
Converts a `.docx` file into a PDF in a machine-independent way.

**Important reality:**
This is **not a perfect Word renderer**.

Instead, it:
- reads the Word file
- extracts paragraphs
- extracts table content
- rebuilds that content in a simple PDF format

**What it is good for:**
- portable conversion
- no dependency on Microsoft Word
- readable content extraction

**What it is not good for:**
- exact page layout reproduction
- complex styling fidelity
- image-heavy or highly formatted documents
- headers/footers/page breaks matching the original Word file exactly

This is a **content-preserving conversion**, not a **visual clone conversion**.

---

## 9. Visualization tools

The project now has a dedicated visualization module:

- `tools/visualization_tools.py`

This module is used to turn structured data into charts and presentable visuals.

---

### 9.1 `generate_chart`

**Purpose:**
Creates chart images in `.png` format.

**Supported chart types:**
- `bar`
- `line`
- `pie`
- `horizontal_bar`

**Typical inputs:**
- content
- chart type
- output file
- x field
- optional y field
- optional title
- optional group by field

**How it behaves:**
- if `y_field` is given, it aggregates numeric values
- if `y_field` is not given, it counts category frequency

**Example use cases:**
- amount by category
- count of records by status
- trend line by month
- category distribution pie chart

---

### 9.2 `generate_summary_dashboard_tool`

**Purpose:**
Creates a PNG summary dashboard.

**What it can show:**
- total rows
- total columns
- numeric summaries like sum, average, min, max
- top category frequency chart

**Why this is useful:**
This is a very presentable output for business users who want a quick overview instead of raw data.

---

### 9.3 `generate_table_image_tool`

**Purpose:**
Creates a PNG image of tabular data.

**Why this is useful:**
- easy to embed in slides
- easy to include in Word or email
- useful when you want a readable snapshot of a table instead of a spreadsheet file

**Supports:**
- optional column selection
- max row control

---

## 10. Email tools

### 10.1 `send_email`

**Purpose:**
Sends a plain-text email using Gmail SMTP.

**Supports:**
- one or more recipients
- subject
- email body
- optional attachments

**What was tested successfully:**
- simple email sending
- email with CSV attachment
- email with PDF attachment
- email with XLSX attachment

This makes the server useful for **automated reporting and delivery**.

---

## 11. Compression and file splitting tools

These tools are designed for situations where exported reports become too large to share easily by email.

---

### 11.1 `compress_files`

**Purpose:**
Compresses one or more files into a ZIP archive.

**Why ZIP was chosen:**
- widely supported
- built-in compatibility on most systems
- easy for recipients to open

---

### 11.2 `split_large_file`

**Purpose:**
Splits a large file into smaller parts.

**Default size:**
- 10 MB per part

**Why this matters:**
If even the ZIP file is too large for email, it can be broken into smaller pieces.

---

### 11.3 Rebuilding split files

The tool also generates human-friendly instructions for rebuilding the file.

**Example Windows command:**

```cmd
copy /b archive.zip.part001+archive.zip.part002+archive.zip.part003 archive.zip
```

After rebuilding the ZIP, the receiver can extract it normally.

---

## 12. The intended big workflow this agent now supports

This is the larger business workflow the current system can support:

1. connect to Unifier
2. fetch records, users, projects, data elements, or data definitions
3. export the results to CSV / Excel / PDF / Word
4. create charts, dashboards, or table snapshots
5. compress the files if needed
6. split them into smaller parts if still too large
7. send them through email
8. provide receiver instructions to rebuild the original file

This is a very useful workflow for:

- reporting teams
- PMO teams
- integration users
- operations users
- non-technical management users

---

## 13. Dependencies used

The project currently relies on Python libraries such as:

- `mcp`
- `httpx`
- `python-dotenv`
- `uvicorn`
- `pandas`
- `requests`
- `python-docx`
- `matplotlib`

Also note:
- Excel export typically needs `openpyxl`

If Excel export fails, it usually means the Excel writer dependency is not installed in the active virtual environment.

---

## 14. Important practical notes

### 14.1 Credentials safety

Right now, the email tool is configured using values placed directly in `server.py`.

This works for testing, but it is **not ideal for long-term security**.

**Recommended improvement:**
move SMTP settings into environment variables such as:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_SENDER_EMAIL`

---

### 14.2 Layout fidelity for DOCX to PDF

The DOCX-to-PDF converter is intentionally machine-independent.

That means it favors **portability** over **layout accuracy**.

If someday you want exact Word appearance in PDF, that would require:
- Microsoft Word automation
- LibreOffice conversion
- or a commercial document rendering engine

---

### 14.3 Requirements file caution

During development, `requirements.txt` appears to have been re-saved in a corrupted/UTF-style format more than once.

So if installs behave strangely, check that `requirements.txt` is saved as **normal UTF-8 text**.

---

## 15. Example user-friendly scenarios

### Scenario A: Export Data Definitions for review

1. Connect to Unifier
2. Fetch data definitions
3. Export to CSV and Word
4. Email the files to the business team

---

### Scenario B: Send a dashboard to management

1. Fetch project or BP data
2. Create a summary dashboard PNG
3. Create a PDF report
4. Email both files to management

---

### Scenario C: Large file sharing

1. Export a large report to Excel
2. Compress it to ZIP
3. Split the ZIP into 10 MB parts
4. Send the parts across multiple emails
5. Receiver rebuilds the ZIP using the provided command

---

### Scenario D: Convert Word content into portable PDF

1. User uploads a Word file
2. Agent extracts readable text and tables
3. Agent creates a machine-independent PDF version
4. PDF is shared by email

---

## 16. Suggested next improvements

If you continue developing this agent, these are the best next enhancements:

1. move email credentials to `.env`
2. clean and stabilize `requirements.txt`
3. add automatic workflow tool:
   - export -> compress -> split -> email
4. add HTML email support
5. add inline chart embedding into Word/PDF/email workflows
6. add better PDF layout for dashboards and tables
7. add receiver-side automatic file recombination tool
8. add more chart styles like stacked bar and donut charts
9. add scheduled reporting in future

---

## 17. Plain-English summary

This agent is now much more than a simple Unifier connector.

It is effectively a **business reporting and delivery assistant** that can:

- fetch Unifier data
- create files from that data
- generate business-friendly visuals
- convert and package documents
- compress and split large outputs
- email results to people

For a layman, the easiest way to understand it is this:

> "It takes business data from Unifier, turns it into useful reports and visuals, and helps package and send those results safely to others."

---

## 18. Running the server

Run locally with:

```bash
python server.py
```

If using a virtual environment, make sure it is activated before running.

---

## 19. Final note

This documentation is written to be understandable for both:

- technical users who will maintain the project
- business users or stakeholders who want to understand what the agent can do

If you want, the next step I can do is create:

1. a **short executive summary version** for presentation slides, and
2. a **technical developer guide** for engineers.
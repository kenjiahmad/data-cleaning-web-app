# Data Cleaning & Summary Web App

**Live demo app:** [https://datacleaningwithsummary.streamlit.app](https://datacleaningwithsummary.streamlit.app)

A modular Python and Streamlit web application for cleaning tabular datasets (`.csv`, `.xlsx`, `.xls`), inspecting data quality and dataset distribution charts, downloading cleaned files, and exporting a PDF summary report.

## Features
- **Upload Dataset:** Drag-and-drop or browse CSV and Excel files.
- **Configurable Cleaning Pipeline:**
  - Remove exact duplicate rows
  - Trim leading, trailing, and redundant inner whitespace in text columns
  - Handle missing numeric values (`none`, `median`, `mean`, `drop`)
  - **Advanced Text Case (MS Word-style):** `Sentence case`, `lowercase`, `UPPERCASE`, `Capitalize Each Word`, and `tOGGLE cASE`
- **Summary & Visualization:** Before-vs-after cleaning metrics, interactive column selection for dataset distribution charts, and one-click PDF report export.
- **Export Cleaned Data:** Download results as `.csv` or `.xlsx` with custom output filenames.

## Project Structure
```text
data-cleaning-web/
├── notebooks/
├── src/
│   ├── __init__.py
│   ├── cleaner.py
│   ├── charts.py
│   └── pdf_report.py
├── app.py
├── requirements.txt
├── .gitignore
└── README.md

from io import BytesIO
import pandas as pd
import streamlit as st

from src.charts import build_summary_chart_bytes
from src.cleaner import CASE_MODE_LABELS, clean_dataset
from src.pdf_report import build_summary_pdf_bytes
from src.charts import build_summary_chart_bytes, suggest_distribution_column

st.set_page_config(page_title="Data Cleaning Tool", page_icon="🧹", layout="wide")

st.title("🧹 Data Cleaning & Summary Web App")
st.caption("Upload a CSV or Excel file, choose cleaning steps, download cleaned data, and export a PDF summary.")

# --- Sidebar: Cleaning Options & Advanced Settings ---
st.sidebar.header("Cleaning Settings")

preset = st.sidebar.radio(
    "Quick Mode",
    options=["Recommended", "Select All", "Custom"],
    index=0,
    help="Recommended enables safe defaults. Select All enables all cleaning options.",
)

if preset == "Select All":
    default_dedup = True
    default_trim = True
    default_missing = "median"
elif preset == "Recommended":
    default_dedup = True
    default_trim = True
    default_missing = "median"
else:
    default_dedup = False
    default_trim = True
    default_missing = "none"

remove_duplicates = st.sidebar.checkbox(
    "Remove duplicate rows",
    value=default_dedup,
    help="Deletes identical rows across the dataset.",
)

trim_whitespace = st.sidebar.checkbox(
    "Trim whitespace",
    value=default_trim,
    help="Removes leading/trailing spaces and collapses extra inner spaces in text columns.",
)

missing_options = ["none", "median", "mean", "drop"]
missing_strategy = st.sidebar.selectbox(
    "Handle missing values (numeric)",
    options=missing_options,
    index=missing_options.index(default_missing),
    help="Choose how empty numeric cells or missing rows are handled.",
)

with st.sidebar.expander("Advanced Settings (Text Case)", expanded=False):
    case_modes = list(CASE_MODE_LABELS.keys())
    case_mode = st.selectbox(
        "Change text case",
        options=case_modes,
        index=0,
        format_func=lambda m: CASE_MODE_LABELS[m],
        help="MS Word-style text case transformation applied to text columns.",
    )

# --- Main Upload Area ---
uploaded_file = st.file_uploader(
    "Drag and drop or browse your dataset (.csv, .xlsx, .xls)",
    type=["csv", "xlsx", "xls"],
)

df_raw = None
selected_case_cols = None

if uploaded_file is not None:
    try:
        file_name_lower = uploaded_file.name.lower()
        if file_name_lower.endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)

        text_cols_available = df_raw.select_dtypes(include=["object", "string"]).columns.tolist()
        if case_mode != "none" and text_cols_available:
            selected_case_cols = st.multiselect(
                "Target text columns for case conversion (leave empty for all text columns)",
                options=text_cols_available,
                default=[],
            )
    except Exception as e:
        st.error(f"Failed to read file: {e}")

run_clean = st.button("Clean Data", type="primary", disabled=(df_raw is None))

if run_clean and df_raw is not None:
    config = {
        "remove_duplicates": remove_duplicates,
        "trim_whitespace": trim_whitespace,
        "missing_strategy": missing_strategy,
        "case_mode": case_mode,
        "case_columns": selected_case_cols if selected_case_cols else None,
    }

    df_cleaned, summary = clean_dataset(df_raw, config)
    chart_bytes = build_summary_chart_bytes(df_cleaned, summary)
    pdf_bytes = build_summary_pdf_bytes(summary, chart_bytes=chart_bytes)

    st.session_state["cleaning_result"] = {
        "df_cleaned": df_cleaned,
        "summary": summary,
        "chart_bytes": chart_bytes,
        "pdf_bytes": pdf_bytes,
        "base_name": uploaded_file.name.rsplit(".", 1)[0],
    }

# --- Output Section (Download + Summary & Chart Preview) ---
if "cleaning_result" in st.session_state:
    res = st.session_state["cleaning_result"]
    df_cleaned = res["df_cleaned"]
    summary = res["summary"]
    base_name = res["base_name"]

    st.divider()
    st.subheader("Summary & Data Distribution Preview")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows", f"{summary['final_rows']}", delta=f"{summary['final_rows'] - summary['initial_rows']}")
    m2.metric("Columns", f"{summary['final_cols']}")
    m3.metric("Missing Cells", f"{summary['final_missing']}", delta=f"{summary['final_missing'] - summary['initial_missing']}")
    m4.metric("Duplicates Removed", f"{summary['removed_duplicates']}")

    available_cols = list(df_cleaned.columns)
    default_col = suggest_distribution_column(df_cleaned)
    default_idx = available_cols.index(default_col) if default_col in available_cols else 0

    selected_dist_col = st.selectbox(
        "Select column for dataset distribution chart (included in preview & PDF report)",
        options=available_cols,
        index=default_idx,
    )

    chart_bytes = build_summary_chart_bytes(df_cleaned, summary, dist_col=selected_dist_col)
    pdf_bytes = build_summary_pdf_bytes(summary, chart_bytes=chart_bytes)

    st.image(chart_bytes, caption="Data Quality & Dataset Distribution Chart", use_container_width=True)

    st.divider()
    st.subheader("Download Cleaned File & Summary")

    col_name, col_fmt = st.columns([2, 1])
    with col_name:
        output_stem = st.text_input("Output file name", value=f"{base_name}_cleaned")
    with col_fmt:
        export_format = st.selectbox("Output format", options=["CSV", "Excel (.xlsx)"])

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        if export_format == "CSV":
            csv_data = df_cleaned.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Cleaned CSV",
                data=csv_data,
                file_name=f"{output_stem}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            excel_buf = BytesIO()
            with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                df_cleaned.to_excel(writer, index=False, sheet_name="Cleaned_Data")
            st.download_button(
                label="⬇️ Download Cleaned Excel",
                data=excel_buf.getvalue(),
                file_name=f"{output_stem}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with dl_col2:
        st.download_button(
            label="📄 Download Summary (PDF)",
            data=pdf_bytes,
            file_name=f"{output_stem}_summary.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with st.expander("Preview Cleaned Dataset (First 20 Rows)", expanded=True):
        st.dataframe(df_cleaned.head(20), use_container_width=True)
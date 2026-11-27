from io import BytesIO
from fpdf import FPDF


def _safe_pdf_text(text: str) -> str:
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


def build_summary_pdf_bytes(summary: dict, chart_bytes: bytes | None = None) -> bytes:
    """Membuat laporan ringkasan Data Cleaning dalam format PDF dan mengembalikannya sebagai bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _safe_pdf_text("Data Cleaning Summary Report"), ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, _safe_pdf_text("Generated automatically from cleaned dataset"), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _safe_pdf_text("1. Dataset & Cleaning Metrics"), ln=True)
    pdf.set_font("Helvetica", "", 10)

    lines = [
        f"Rows: {summary['initial_rows']} -> {summary['final_rows']}",
        f"Columns: {summary['initial_cols']} -> {summary['final_cols']}",
        f"Duplicates Removed: {summary['removed_duplicates']} (Initial duplicates: {summary['initial_duplicates']})",
        f"Missing Cells: {summary['initial_missing']} -> {summary['final_missing']}",
        f"Numeric Missing Cells Filled: {summary['numeric_filled_cells']} | Rows Dropped (Missing): {summary['rows_dropped_missing']}",
    ]
    for line in lines:
        pdf.cell(0, 6.5, _safe_pdf_text(f"- {line}"), ln=True)

    pdf.ln(3)

    cfg = summary.get("applied_config", {})
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _safe_pdf_text("2. Applied Cleaning Options"), ln=True)
    pdf.set_font("Helvetica", "", 10)

    cfg_lines = [
        f"Remove Duplicates: {cfg.get('remove_duplicates')}",
        f"Missing Value Strategy: {cfg.get('missing_strategy')}",
        f"Trim Whitespace: {cfg.get('trim_whitespace')}",
        f"Text Case Mode: {cfg.get('case_mode')}",
    ]
    for c_line in cfg_lines:
        pdf.cell(0, 6.5, _safe_pdf_text(f"- {c_line}"), ln=True)

    pdf.ln(4)

    if chart_bytes:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _safe_pdf_text("3. Visual Summary"), ln=True)
        img_stream = BytesIO(chart_bytes)
        pdf.image(img_stream, w=180)

    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return str(out).encode("latin-1")   
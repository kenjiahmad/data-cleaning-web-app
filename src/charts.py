from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def suggest_distribution_column(df: pd.DataFrame) -> str | None:
    """Memilih kolom paling informatif untuk chart persebaran isi dataset."""
    if df.empty or len(df.columns) == 0:
        return None

    # Prioritaskan kolom kategorikal/teks dengan jumlah kategori wajar (2 s.d. 30 variasi)
    cat_cols = df.select_dtypes(include=["object", "string", "category", "bool"]).columns.tolist()
    scored_cats = []
    for col in cat_cols:
        nunique = df[col].nunique(dropna=True)
        if 2 <= nunique <= 30:
            # Hindari kolom yang hampir semuanya unik (seperti nama/ID bebas)
            unique_ratio = nunique / max(len(df), 1)
            if unique_ratio < 0.85:
                scored_cats.append((nunique, col))

    if scored_cats:
        # Pilih yang variasinya paling pas (misal di tengah-tengah, tidak terlalu sedikit/banyak)
        scored_cats.sort(key=lambda x: abs(x[0] - 8))
        return scored_cats[0][1]

    # Jika tidak ada kategori yang pas, cek kolom numerik (hindari kolom ID)
    num_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns.tolist()
        if "id" not in c.lower()
    ]
    if num_cols:
        return num_cols[0]

    # Fallback ke kolom pertama yang tersedia
    return df.columns[0]


def build_summary_chart_bytes(
    df_after: pd.DataFrame,
    summary: dict,
    dist_col: str | None = None,
) -> bytes:
    """Membuat chart perbandingan kualitas data + persebaran isi dataset hasil cleaning."""
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    fig.patch.set_facecolor("white")

    # --- Panel Kiri: Data Quality Comparison (Before vs After Cleaning) ---
    metrics = ["Rows", "Missing Cells", "Duplicates"]
    before_vals = [
        summary["initial_rows"],
        summary["initial_missing"],
        summary["initial_duplicates"],
    ]
    after_vals = [
        summary["final_rows"],
        summary["final_missing"],
        summary.get("final_duplicates", int(df_after.duplicated().sum())),
    ]

    x = np.arange(len(metrics))
    width = 0.35

    bars1 = axes[0].bar(x - width / 2, before_vals, width, label="Before Cleaning", color="#E07A5F")
    bars2 = axes[0].bar(x + width / 2, after_vals, width, label="After Cleaning", color="#3D405B")

    axes[0].set_title("Data Quality Comparison", fontsize=11, fontweight="bold")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics)
    axes[0].set_ylabel("Count")
    axes[0].legend()
    axes[0].grid(axis="y", linestyle="--", alpha=0.4)

    for bar in bars1:
        h = bar.get_height()
        axes[0].annotate(
            f"{int(h)}",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    for bar in bars2:
        h = bar.get_height()
        axes[0].annotate(
            f"{int(h)}",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # --- Panel Kanan: Persebaran Isi Dataset (Distribution) ---
    target_col = dist_col if dist_col in df_after.columns else suggest_distribution_column(df_after)

    if target_col is not None and len(df_after) > 0:
        series = df_after[target_col].dropna()

        if pd.api.types.is_numeric_dtype(series) and series.nunique() > 12:
            axes[1].hist(series, bins=min(15, max(5, int(np.sqrt(len(series))))), color="#2A9D8F", edgecolor="white")
            axes[1].set_title(f"Distribution of {target_col}", fontsize=11, fontweight="bold")
            axes[1].set_xlabel(target_col)
            axes[1].set_ylabel("Frequency")
            axes[1].grid(axis="y", linestyle="--", alpha=0.4)
        else:
            counts = series.astype(str).value_counts().head(8)
            axes[1].barh(counts.index, counts.values, color="#2A9D8F")
            axes[1].invert_yaxis()
            axes[1].set_title(f"Top {len(counts)} Values in '{target_col}'", fontsize=11, fontweight="bold")
            axes[1].set_xlabel("Count")
            axes[1].grid(axis="x", linestyle="--", alpha=0.4)

            for idx, val in enumerate(counts.values):
                axes[1].annotate(
                    f"{int(val)}",
                    xy=(val, idx),
                    xytext=(4, 0),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    fontsize=8.5,
                )
    else:
        axes[1].text(0.5, 0.5, "No data available for distribution chart", ha="center", va="center")
        axes[1].set_axis_off()

    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
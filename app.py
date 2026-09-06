from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from services.analytics import (
    calculate_business_kpis,
    enrich_business_metrics,
)
from services.data_loader import (
    detect_date_columns,
    make_demo_data,
    read_uploaded_file,
)

st.set_page_config(
    page_title="Business Copilot",
    page_icon="BC",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- State ----------
DEFAULT_STATE = {
    "page": "Overview",
    "selected_kpi": "Total",
    "dataset": None,
    "dataset_name": None,
    "dataset_source": None,
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------- Styling ----------
st.markdown(
    """
    <style>
    :root {
        --bg: #0b0d10;
        --surface: #111419;
        --surface-2: #15191f;
        --border: #232833;
        --text: #f5f7fa;
        --muted: #8c95a5;
        --subtle: #697180;
    }

    .stApp { background: var(--bg); color: var(--text); }
    [data-testid="stHeader"] {
        background: rgba(11, 13, 16, 0.78);
        backdrop-filter: blur(14px);
        border-bottom: 1px solid rgba(35, 40, 51, 0.7);
    }
    [data-testid="stSidebar"] {
        background: #0f1216;
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
    .block-container {
        max-width: 1480px;
        padding-top: 5.25rem;
        padding-bottom: 4rem;
        padding-left: 2.7rem;
        padding-right: 2.7rem;
    }
    html, body, [class*="css"] {
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-up { animation: fadeUp .42s ease-out both; }

    .eyebrow {
        font-size: 12px;
        font-weight: 650;
        letter-spacing: .14em;
        text-transform: uppercase;
        color: var(--subtle);
        margin-bottom: 12px;
    }
    .page-title {
        font-size: 42px;
        line-height: 1.08;
        letter-spacing: -.04em;
        font-weight: 680;
        margin: 0;
        color: var(--text);
    }
    .page-subtitle {
        margin-top: 12px;
        margin-bottom: 26px;
        max-width: 760px;
        color: var(--muted);
        line-height: 1.65;
        font-size: 15px;
    }
    .section-title {
        font-size: 18px;
        font-weight: 620;
        letter-spacing: -.015em;
        color: var(--text);
        margin: 10px 0 3px 0;
    }
    .section-subtitle {
        color: var(--muted);
        font-size: 13px;
        margin: 0 0 14px 0;
    }
    .panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 14px 34px rgba(0,0,0,.10);
    }
    .hero-panel {
        background: linear-gradient(180deg, #12161c 0%, #101318 100%);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 34px;
        margin-top: 8px;
        margin-bottom: 20px;
    }
    .hero-copy {
        font-size: 28px;
        line-height: 1.25;
        letter-spacing: -.03em;
        font-weight: 650;
        margin-bottom: 10px;
    }
    .hero-muted { color: var(--muted); line-height: 1.6; max-width: 720px; }
    .dataset-strip {
        display: flex;
        gap: 18px;
        flex-wrap: wrap;
        align-items: center;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 13px;
        padding: 13px 16px;
        margin-bottom: 22px;
    }
    .dataset-name { color: var(--text); font-size: 13px; font-weight: 620; }
    .dataset-meta { color: var(--subtle); font-size: 12px; }
    .insight {
        background: #101318;
        border: 1px solid var(--border);
        border-radius: 13px;
        padding: 15px 16px;
        margin-bottom: 10px;
    }
    .insight-title { color: var(--text); font-weight: 600; font-size: 13px; margin-bottom: 5px; }
    .insight-text { color: var(--muted); font-size: 13px; line-height: 1.55; }
    .footer-note { color: var(--subtle); font-size: 12px; line-height: 1.6; }

    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--text);
        border-radius: 11px;
        min-height: 42px;
        transition: transform .16s ease, border-color .16s ease, background .16s ease;
    }
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        transform: translateY(-1px);
        border-color: #46505f;
        background: var(--surface-2);
    }
    div[data-testid="stButton"] > button p { white-space: pre-line; }

    .kpi-row div[data-testid="stButton"] > button {
        min-height: 112px;
        justify-content: flex-start;
        text-align: left;
        padding: 17px 18px;
        font-size: 14px;
        line-height: 1.8;
    }

    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 13px;
        overflow: hidden;
    }
    [data-testid="stFileUploader"] {
        border-radius: 12px;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        border-radius: 9px;
        padding: 8px 9px;
        transition: background .15s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: #15191f;
    }

    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Presentation helpers ----------
def format_number(value: float) -> str:
    if pd.isna(value):
        return "–"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f} M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f} K"
    return f"{value:,.2f}"


def transparent_chart(fig, height=390):
    fig.update_layout(
        height=height,
        margin={"l": 8, "r": 8, "t": 18, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#a7afbb"},
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", zeroline=False)
    return fig


def summary_csv(df: pd.DataFrame, metric: str, dimension: str | None) -> bytes:
    if dimension and dimension != "None":
        export_df = (
            df.groupby(dimension)[metric]
            .agg(Total="sum", Average="mean", Maximum="max", Records="count")
            .reset_index()
            .sort_values("Total", ascending=False)
        )
    else:
        s = df[metric].dropna()
        export_df = pd.DataFrame(
            {
                "Metric": ["Total", "Average", "Median", "Minimum", "Maximum", "Records"],
                "Value": [s.sum(), s.mean(), s.median(), s.min(), s.max(), s.count()],
            }
        )
    return export_df.to_csv(index=False).encode("utf-8-sig")


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        """
        <div style="font-size:19px;font-weight:680;letter-spacing:-.02em;color:#f5f7fa;">Business Copilot</div>
        <div style="font-size:12px;color:#697180;margin-top:3px;margin-bottom:24px;">Analytics workspace</div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        ["Overview", "Analytics", "Data", "Data quality"],
        index=["Overview", "Analytics", "Data", "Data quality"].index(st.session_state.page),
        label_visibility="collapsed",
    )
    st.session_state.page = page

    st.divider()

    if st.session_state.dataset is not None:
        st.caption("Active dataset")
        st.write(st.session_state.dataset_name)
        if st.button("Clear dataset", use_container_width=True):
            st.session_state.dataset = None
            st.session_state.dataset_name = None
            st.session_state.dataset_source = None
            st.rerun()

    st.write("")
    st.caption("Legal")
    with st.popover("Datenschutz", use_container_width=True):
        st.markdown(
            """
            **Datenschutzhinweis für diesen Prototyp**

            Der bereitgestellte Code verarbeitet hochgeladene Dateien innerhalb der laufenden Streamlit-Anwendung. Er enthält keine externe KI-API und schreibt die hochgeladenen Unternehmensdaten nicht absichtlich in eine externe Datenbank.

            Sobald die Anwendung öffentlich gehostet wird, hängt die tatsächliche Datenverarbeitung zusätzlich vom Hosting-Anbieter, Server-Logs, Cookies und weiteren eingebundenen Diensten ab. Vor einem echten Produktivbetrieb in Deutschland sollte deshalb eine individuelle Datenschutzerklärung erstellt werden.
            """
        )

    with st.popover("Impressum", use_container_width=True):
        st.markdown(
            """
            **Impressum – Platzhalter**

            Betreiber: [Name / Unternehmen]  
            Anschrift: [Anschrift]  
            E-Mail: [E-Mail-Adresse]  
            Vertretungsberechtigte Person: [falls erforderlich]

            Diese Angaben sind nur Platzhalter und müssen vor einer öffentlichen Veröffentlichung durch die echten Pflichtangaben ersetzt werden.
            """
        )

# ---------- Top area / import ----------
left_head, right_head = st.columns([4.4, 1.25], vertical_alignment="center")

with left_head:
    st.markdown('<div class="eyebrow fade-up">Business intelligence platform</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="page-title fade-up">{st.session_state.page}</h1>', unsafe_allow_html=True)

with right_head, st.popover("Import data", use_container_width=True):
    uploaded = st.file_uploader(
        "CSV or Excel",
        type=["csv", "xlsx"],
        key="top_import",
        help="CSV and XLSX are supported.",
    )
    if uploaded is not None:
        try:
            loaded = read_uploaded_file(uploaded.getvalue(), uploaded.name)
            loaded.columns = [str(c).strip() for c in loaded.columns]
            st.session_state.dataset = loaded
            st.session_state.dataset_name = uploaded.name
            st.session_state.dataset_source = "upload"
            st.success("Dataset loaded.")
        except (ValueError, OSError) as exc:
            st.error(str(exc))

# ---------- Empty state ----------
if st.session_state.dataset is None:
    st.markdown(
        """
        <div class="hero-panel fade-up">
            <div class="hero-copy">From raw data to a usable management view.</div>
            <div class="hero-muted">
                Import a CSV or Excel file and Business Copilot will detect numerical metrics,
                categories and date fields. You can also open the demo workspace first to explore
                the interface without preparing a file.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="panel fade-up"><div class="section-title">Performance</div><div class="section-subtitle">Track totals, averages and trends across your core metrics.</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel fade-up"><div class="section-title">Segmentation</div><div class="section-subtitle">Compare products, regions, customers and other dimensions.</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="panel fade-up"><div class="section-title">Data quality</div><div class="section-subtitle">Find missing values, duplicates and structural issues.</div></div>', unsafe_allow_html=True)

    st.write("")
    action_left, action_right, _ = st.columns([1.2, 1.2, 4])
    with action_left:
        if st.button("Open demo workspace", use_container_width=True):
            st.session_state.dataset = make_demo_data()
            st.session_state.dataset_name = "BusinessCopilot_Demo.csv"
            st.session_state.dataset_source = "demo"
            st.rerun()
    with action_right:
        st.caption("Or use Import data in the upper-right corner.")

    st.write("")
    st.markdown('<div class="footer-note">Business Copilot prototype · No external AI service is connected in this version.</div>', unsafe_allow_html=True)
    st.stop()

# ---------- Dataset setup ----------
df = st.session_state.dataset.copy()
df, business_columns = enrich_business_metrics(df)

if df.empty:
    st.warning("The active dataset does not contain any rows.")
    st.stop()

numeric_columns = df.select_dtypes(include="number").columns.tolist()
categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()
date_columns = detect_date_columns(df)

if not numeric_columns:
    st.error("No numerical columns were detected. Add at least one numeric metric to analyse the dataset.")
    st.stop()

# Dataset strip
st.markdown(
    f"""
    <div class="dataset-strip fade-up">
        <div class="dataset-name">{st.session_state.dataset_name}</div>
        <div class="dataset-meta">{len(df):,} records</div>
        <div class="dataset-meta">{len(df.columns)} columns</div>
        <div class="dataset-meta">Source: {st.session_state.dataset_source}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Controls
control_a, control_b, control_c = st.columns(3)
with control_a:
    metric = st.selectbox("Primary metric", numeric_columns)
with control_b:
    dimensions = [c for c in categorical_columns if 1 < df[c].nunique(dropna=True) <= 100]
    dimension = st.selectbox("Dimension", ["None"] + dimensions)
with control_c:
    date_field = st.selectbox("Date field", ["None"] + date_columns)

filtered_df = df.copy()
if dimension != "None":
    filter_values = sorted(filtered_df[dimension].dropna().astype(str).unique().tolist())
    selected = st.multiselect("Filter", filter_values, default=filter_values)
    filtered_df = filtered_df[filtered_df[dimension].astype(str).isin(selected)]

series = filtered_df[metric].dropna()
if series.empty:
    st.warning("The current filter leaves no numeric records to analyse.")
    st.stop()

# ---------- Page: Overview ----------
if st.session_state.page == "Overview":
    total = series.sum()
    average = series.mean()
    maximum = series.max()
    business_kpis = calculate_business_kpis(filtered_df, business_columns)

    management_cards = []
    if "revenue" in business_kpis:
        management_cards.append(("Revenue", format_number(business_kpis["revenue"]), "Revenue"))
    if "cost" in business_kpis:
        management_cards.append(("Costs", format_number(business_kpis["cost"]), "Costs"))
    if "profit" in business_kpis:
        management_cards.append(("Profit", format_number(business_kpis["profit"]), "Profit"))
    if "margin" in business_kpis:
        management_cards.append(("Margin", f'{business_kpis["margin"]:.1f}%', "Margin"))

    st.markdown('<div class="section-title">Key metrics</div><div class="section-subtitle">Select a metric card to open its detail view.</div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)

    if len(management_cards) >= 3:
        visible_cards = management_cards[:4]
        if st.session_state.selected_kpi not in [card[2] for card in visible_cards]:
            st.session_state.selected_kpi = visible_cards[0][2]

        columns = st.columns(len(visible_cards))
        for column, (label, value, state_name) in zip(columns, visible_cards):
            with column:
                if st.button(
                    f"{label.upper()}\n{value}",
                    key=f"kpi_{state_name.lower()}",
                    use_container_width=True,
                ):
                    st.session_state.selected_kpi = state_name
    else:
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            if st.button(f"TOTAL\n{format_number(total)}", key="kpi_total", use_container_width=True):
                st.session_state.selected_kpi = "Total"
        with k2:
            if st.button(f"AVERAGE\n{format_number(average)}", key="kpi_average", use_container_width=True):
                st.session_state.selected_kpi = "Average"
        with k3:
            if st.button(f"MAXIMUM\n{format_number(maximum)}", key="kpi_maximum", use_container_width=True):
                st.session_state.selected_kpi = "Maximum"
        with k4:
            if st.button(f"RECORDS\n{len(filtered_df):,}", key="kpi_records", use_container_width=True):
                st.session_state.selected_kpi = "Records"

    st.markdown('</div>', unsafe_allow_html=True)

    detail_left, detail_right = st.columns([1.65, 1])
    with detail_left:
        st.markdown('<div class="section-title">Performance</div><div class="section-subtitle">Trend of the selected business metric.</div>', unsafe_allow_html=True)
        if date_field != "None":
            chart_df = filtered_df.copy()
            chart_df[date_field] = pd.to_datetime(chart_df[date_field], errors="coerce", dayfirst=True)
            chart_df = chart_df.dropna(subset=[date_field])
            chart_df = chart_df.groupby(date_field, as_index=False)[metric].sum().sort_values(date_field)
            fig = px.area(chart_df, x=date_field, y=metric)
            fig = transparent_chart(fig, 420)
            fig.update_layout(xaxis_title="", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            index_df = filtered_df[[metric]].reset_index(drop=True).reset_index(names="Record")
            fig = px.line(index_df, x="Record", y=metric)
            fig = transparent_chart(fig, 420)
            fig.update_layout(xaxis_title="Record", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

    with detail_right:
        st.markdown('<div class="section-title">Current selection</div><div class="section-subtitle">A compact explanation of the selected KPI.</div>', unsafe_allow_html=True)
        selected_kpi = st.session_state.selected_kpi
        if selected_kpi == "Revenue" and "revenue" in business_kpis:
            text = f"Revenue totals {format_number(business_kpis['revenue'])} across the current selection."
        elif selected_kpi == "Costs" and "cost" in business_kpis:
            text = f"Costs total {format_number(business_kpis['cost'])} across the current selection."
        elif selected_kpi == "Profit" and "profit" in business_kpis:
            text = f"Profit totals {format_number(business_kpis['profit'])} across the current selection."
        elif selected_kpi == "Margin" and "margin" in business_kpis:
            text = f"The current profit margin is {business_kpis['margin']:.1f}%."
        elif selected_kpi == "Total":
            text = f"{metric} totals {format_number(total)} across the current selection."
        elif selected_kpi == "Average":
            text = f"The average {metric} value is {format_number(average)}."
        elif selected_kpi == "Maximum":
            text = f"The highest single {metric} value is {format_number(maximum)}."
        else:
            text = f"The current view contains {len(filtered_df):,} records."
        st.markdown(f'<div class="insight"><div class="insight-title">{selected_kpi}</div><div class="insight-text">{text}</div></div>', unsafe_allow_html=True)

        if dimension != "None":
            grouped = filtered_df.groupby(dimension)[metric].sum().sort_values(ascending=False)
            if not grouped.empty:
                best_name = str(grouped.index[0])
                best_value = grouped.iloc[0]
                share = (best_value / grouped.sum() * 100) if grouped.sum() else 0
                st.markdown(f'<div class="insight"><div class="insight-title">Leading segment</div><div class="insight-text">{best_name} contributes {format_number(best_value)}, approximately {share:.1f}% of the grouped total.</div></div>', unsafe_allow_html=True)

        missing = int(filtered_df.isna().sum().sum())
        duplicates = int(filtered_df.duplicated().sum())
        st.markdown(f'<div class="insight"><div class="insight-title">Data health</div><div class="insight-text">{missing} missing values and {duplicates} duplicate rows are visible in the current dataset.</div></div>', unsafe_allow_html=True)

    if dimension != "None":
        st.markdown('<div class="section-title">Top dimensions</div><div class="section-subtitle">Largest contributors to the selected metric.</div>', unsafe_allow_html=True)
        grouped_df = (
            filtered_df.groupby(dimension)[metric]
            .agg(Total="sum", Average="mean", Records="count")
            .reset_index()
            .sort_values("Total", ascending=False)
        )
        chart_col, table_col = st.columns([1.4, 1])
        with chart_col:
            fig = px.bar(grouped_df.head(12), x="Total", y=dimension, orientation="h")
            fig = transparent_chart(fig, 390)
            fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        yaxis={"categoryorder": "total ascending"},
        )
            st.plotly_chart(fig, use_container_width=True)
        with table_col:
            st.dataframe(grouped_df.head(12), use_container_width=True, hide_index=True, height=390)

    st.download_button(
        "Export summary",
        data=summary_csv(filtered_df, metric, dimension),
        file_name="business_copilot_summary.csv",
        mime="text/csv",
    )

# ---------- Page: Analytics ----------
elif st.session_state.page == "Analytics":
    st.markdown('<div class="section-title">Advanced analysis</div><div class="section-subtitle">Compare the selected metric by business dimension and inspect its distribution.</div>', unsafe_allow_html=True)

    if dimension == "None":
        st.info("Select a dimension above to unlock grouped analysis.")
    else:
        grouped_df = (
            filtered_df.groupby(dimension)[metric]
            .agg(Total="sum", Average="mean", Median="median", Maximum="max", Records="count")
            .reset_index()
            .sort_values("Total", ascending=False)
        )
        left, right = st.columns([1.45, 1])
        with left:
            fig = px.bar(grouped_df.head(20), x=dimension, y="Total", hover_data=["Average", "Median", "Maximum", "Records"])
            fig = transparent_chart(fig, 460)
            fig.update_layout(xaxis_title="", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        with right:
            st.dataframe(grouped_df, use_container_width=True, hide_index=True, height=460)

    st.markdown('<div class="section-title">Distribution</div><div class="section-subtitle">See how individual values of the selected metric are distributed.</div>', unsafe_allow_html=True)
    hist = px.histogram(filtered_df, x=metric, nbins=30)
    hist = transparent_chart(hist, 360)
    hist.update_layout(xaxis_title=metric, yaxis_title="Records")
    st.plotly_chart(hist, use_container_width=True)

# ---------- Page: Data ----------
elif st.session_state.page == "Data":
    st.markdown('<div class="section-title">Dataset explorer</div><div class="section-subtitle">Review, filter and export the current data.</div>', unsafe_allow_html=True)
    st.dataframe(filtered_df, use_container_width=True, height=600)
    st.download_button(
        "Export filtered CSV",
        filtered_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="business_copilot_filtered.csv",
        mime="text/csv",
    )

# ---------- Page: Data quality ----------
else:
    st.markdown('<div class="section-title">Data quality</div><div class="section-subtitle">Inspect completeness, duplication and column structure before drawing conclusions.</div>', unsafe_allow_html=True)

    missing = int(df.isna().sum().sum())
    duplicates = int(df.duplicated().sum())
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Rows", f"{len(df):,}")
    q2.metric("Columns", len(df.columns))
    q3.metric("Missing values", missing)
    q4.metric("Duplicate rows", duplicates)

    quality_df = pd.DataFrame(
        {
            "Column": df.columns,
            "Type": [str(df[c].dtype) for c in df.columns],
            "Missing": [int(df[c].isna().sum()) for c in df.columns],
            "Missing %": [round(df[c].isna().mean() * 100, 2) for c in df.columns],
            "Unique values": [int(df[c].nunique(dropna=True)) for c in df.columns],
        }
    )
    st.dataframe(quality_df, use_container_width=True, hide_index=True)

# ---------- Footer ----------
st.divider()
st.markdown(
    f'<div class="footer-note">Business Copilot prototype · Session generated {datetime.now(timezone.utc).strftime("%d.%m.%Y")} · Legal notices available in the sidebar.</div>',
    unsafe_allow_html=True,
)

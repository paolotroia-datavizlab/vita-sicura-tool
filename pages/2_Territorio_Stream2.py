import streamlit as st
import pandas as pd
import altair as alt

from src.data import get_df

st.set_page_config(layout="wide")

st.title("🗺️ Stream 2 — Potenziale Territoriale")
st.caption("Individuazione delle aree a maggior opportunità commerciale per Casa e Salute")

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
df = get_df("potential_score_comuni.csv")

# -------------------------------------------------
# BUSINESS LABELS (presentation layer)
# -------------------------------------------------
LABELS = {
    "luogo_di_residenza": "Comune",
    "n_clienti": "Numero clienti",
    "penetrazione_casa": "Penetrazione Casa",
    "penetrazione_salute": "Penetrazione Salute",
    "protection_gap_casa": "Protection Gap Casa",
    "protection_gap_salute": "Protection Gap Salute",
    "valore_immobiliare_medio": "Valore immobiliare medio (€)",
    "NDVI_mean": "Indice verde (NDVI)",
    "potential_score_casa": "Potenziale Casa",
    "potential_score_salute": "Potenziale Salute",
}

def rename_for_display(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in LABELS.items() if k in df.columns})

# -------------------------------------------------
# SIDEBAR FILTERS (GLOBALI)
# -------------------------------------------------

# Area di bisogno (contesto globale)
prodotto_sel = st.sidebar.radio(
    "🏠 Area di bisogno",
    ["Casa", "Salute"]
)

if prodotto_sel == "Casa":
    score_col = "potential_score_casa"
    gap_col = "protection_gap_casa"
    score_label = "Potenziale Casa"
else:
    score_col = "potential_score_salute"
    gap_col = "protection_gap_salute"
    score_label = "Potenziale Salute"

# Filtro Comune
zona_options = ["Tutte"] + sorted(df["luogo_di_residenza"].dropna().unique())

zona_sel = st.sidebar.selectbox(
    "🏘️ Comune",
    options=zona_options,
    index=0
)

if zona_sel == "Tutte":
    df_ctx = df.copy()
else:
    df_ctx = df[df["luogo_di_residenza"] == zona_sel].copy()

# -------------------------------------------------
# KPI HEADER
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("COMUNI", f"{len(df_ctx):,}")
c2.metric("CLIENTI", f"{df_ctx['n_clienti'].sum():,}")
c3.metric(f"{score_label.upper()} MEDIO", f"{df_ctx[score_col].mean():.2f}")
c4.metric("AFFORDABILITY MEDIA", f"{df_ctx['valore_immobiliare_medio'].mean():,.0f} €")

st.markdown("---")

# -------------------------------------------------
# TOP COMUNI PER POTENZIALE
# -------------------------------------------------
st.subheader(f"Top Comuni per {score_label}")

top_comuni = (
    df_ctx
    .sort_values(score_col, ascending=False)
    .head(10)
)

bar = alt.Chart(top_comuni).mark_bar().encode(
    y=alt.Y(
        "luogo_di_residenza:N",
        sort="-x",
        title="Comune",
        axis=alt.Axis(labelLimit=260)
    ),
    x=alt.X(
        f"{score_col}:Q",
        title=score_label
    ),
    color=alt.Color(
        f"{gap_col}:Q",
        scale=alt.Scale(scheme="blues"),
        legend=alt.Legend(title="Protection Gap")
    ),
    tooltip=[
        "luogo_di_residenza",
        alt.Tooltip(f"{score_col}:Q", format=".2f", title=score_label),
        alt.Tooltip(f"{gap_col}:Q", format=".2f", title="Protection Gap"),
        alt.Tooltip("valore_immobiliare_medio:Q", format=",.0f", title="Valore immobiliare"),
        "n_clienti"
    ]
).properties(height=360)

st.altair_chart(bar, use_container_width=True)

# -------------------------------------------------
# DOVE AGIRE: BISOGNO vs CAPACITÀ ECONOMICA
# -------------------------------------------------
st.subheader("Dove agire: bisogno vs capacità economica")

# Filtriamo rumore
df_plot = df_ctx[df_ctx[score_col] > 0.05].copy()

scatter = alt.Chart(df_plot).mark_circle(opacity=0.7).encode(
    x=alt.X(
        "valore_immobiliare_medio:Q",
        title="Valore immobiliare medio (€)",
        axis=alt.Axis(format=",.0f")
    ),
    y=alt.Y(
        f"{score_col}:Q",
        title=score_label
    ),
    size=alt.Size(
        "n_clienti:Q",
        legend=None
    ),
    color=alt.Color(
        f"{gap_col}:Q",
        scale=alt.Scale(scheme="blues"),
        legend=alt.Legend(title="Protection Gap")
    ),
    tooltip=[
        "luogo_di_residenza",
        alt.Tooltip(f"{score_col}:Q", format=".2f", title=score_label),
        alt.Tooltip(f"{gap_col}:Q", format=".2f", title="Protection Gap"),
        alt.Tooltip("valore_immobiliare_medio:Q", format=",.0f"),
        "n_clienti"
    ]
).properties(height=380)

# Linee guida decisionali
vline = alt.Chart(pd.DataFrame({"x": [300000]})).mark_rule(
    strokeDash=[4, 4], color="gray"
).encode(x="x:Q")

hline = alt.Chart(pd.DataFrame({"y": [0.6]})).mark_rule(
    strokeDash=[4, 4], color="gray"
).encode(y="y:Q")

st.altair_chart(scatter + vline + hline, use_container_width=True)

st.caption(
    "In alto a destra: alto potenziale e alta capacità economica → priorità commerciale. "
    "In alto a sinistra: potenziale alto ma affordability più bassa → approccio selettivo. "
    "In basso: monitoraggio."
)

# -------------------------------------------------
# TABELLA OPERATIVA COMUNI
# -------------------------------------------------
st.subheader("Comuni — priorità operative")

cols_show = [
    "luogo_di_residenza",
    "n_clienti",
    "penetrazione_casa",
    "penetrazione_salute",
    "protection_gap_casa",
    "protection_gap_salute",
    "valore_immobiliare_medio",
    "NDVI_mean",
    "potential_score_casa",
    "potential_score_salute",
]

df_table = (
    df_ctx[cols_show]
    .sort_values(score_col, ascending=False)
    .head(30)
)

st.dataframe(
    rename_for_display(df_table),
    use_container_width=True,
    height=420
)



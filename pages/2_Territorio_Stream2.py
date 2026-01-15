import streamlit as st
import pandas as pd
import altair as alt

from src.data import get_df

st.set_page_config(layout="wide")

st.title("🗺️ Dove investire ora — Priorità territoriali")
st.caption(
    "Capire dove concentrare l’attività commerciale combinando bisogno assicurativo, "
    "potenziale di mercato e capacità economica per Casa e Salute."
)

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

c1.metric("**COMUNI**", f"{len(df_ctx):,}")
c2.metric("**CLIENTI**", f"{df_ctx['n_clienti'].sum():,}")
c3.metric(f"**{score_label.upper()} MEDIO**", f"{df_ctx[score_col].mean():.2f}")
c4.metric("**VALORE IMMOBILIARE MEDIO (€)**", f"{df_ctx['valore_immobiliare_medio'].mean():,.0f} €")

st.markdown("---")

# -------------------------------------------------
# TOP COMUNI PER POTENZIALE
# -------------------------------------------------
st.markdown(
    f"<h3 style='text-align: center;'>Comuni con maggiore opportunità commerciale per {score_label}</h3>",
    unsafe_allow_html=True
)
st.caption(
    "I comuni in alto combinano alto potenziale e bisogno assicurativo ancora scoperto."
)

# ===== Grafico SINISTRA: focus prodotto selezionato (INVARIATO)
top_comuni = (
    df_ctx
    .sort_values(score_col, ascending=False)
    .head(10)
)

bar_focus = alt.Chart(top_comuni).mark_bar().encode(
    y=alt.Y(
        "luogo_di_residenza:N",
        sort="-x",
        title="Comune",
        axis=alt.Axis(labelLimit=260)
    ),
    x=alt.X(
        f"{score_col}:Q",
        title=f"{score_label} (indice sintetico)"
    ),
    color=alt.Color(
        f"{gap_col}:Q",
        scale=alt.Scale(scheme="blues"),
        legend=None
    ),
    tooltip=[
        "luogo_di_residenza",
        alt.Tooltip(f"{score_col}:Q", format=".2f", title=score_label),
        alt.Tooltip(f"{gap_col}:Q", format=".2f", title="Protection Gap"),
        alt.Tooltip("valore_immobiliare_medio:Q", format=",.0f", title="Valore immobiliare"),
        "n_clienti"
    ]
).properties(height=360)

# ===== Grafico DESTRA: barre cumulate Casa + Salute

# dati long
df_stack = (
    df_ctx[[
        "luogo_di_residenza",
        "potential_score_casa",
        "potential_score_salute"
    ]]
    .melt(
        id_vars="luogo_di_residenza",
        var_name="Prodotto",
        value_name="Potenziale"
    )
)

df_stack["Prodotto"] = df_stack["Prodotto"].map({
    "potential_score_casa": "Casa",
    "potential_score_salute": "Salute"
})

# top comuni per potenziale complessivo
top_comuni_mix = (
    df_stack
    .groupby("luogo_di_residenza", as_index=False)["Potenziale"]
    .sum()
    .sort_values("Potenziale", ascending=False)
    .head(10)["luogo_di_residenza"]
)

df_stack = df_stack[df_stack["luogo_di_residenza"].isin(top_comuni_mix)]

bar_stack = alt.Chart(df_stack).mark_bar().encode(
    y=alt.Y(
        "luogo_di_residenza:N",
        sort="-x",
        title="Comune",
        axis=alt.Axis(labelLimit=260)
    ),
    x=alt.X(
        "Potenziale:Q",
        title="Potenziale complessivo (Casa + Salute)"
    ),
    color=alt.Color(
        "Prodotto:N",
        scale=alt.Scale(range=["#4C78A8", "#72B7B2"]),
        legend=alt.Legend(title="Prodotto")
    ),
    tooltip=[
        "luogo_di_residenza",
        "Prodotto",
        alt.Tooltip("Potenziale:Q", format=".2f")
    ]
).properties(height=360)

# ===== Layout affiancato
c1, c2 = st.columns(2)

with c1:
    st.altair_chart(bar_focus, use_container_width=True)

with c2:
    st.altair_chart(bar_stack, use_container_width=True)


# -------------------------------------------------
# DOVE AGIRE: BISOGNO vs CAPACITÀ ECONOMICA
# -------------------------------------------------
st.subheader("Dove concentrare l’azione: bisogno vs capacità economica")
st.caption(
    "Il grafico confronta il bisogno assicurativo con la capacità economica dei territori. "
    "Le aree in alto a destra combinano alto potenziale e maggiore capacità di spesa "
    "→ sono le priorità per l’azione commerciale. "
    "In alto a sinistra il bisogno è alto ma la capacità economica è più contenuta "
    "→ approccio selettivo. "
    "Le aree in basso sono da monitorare."
)

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
        legend=None
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

# etichette dei quadranti
labels = alt.Chart(pd.DataFrame({
    "x": [560000, 140000, 560000, 140000],
    "y": [0.82, 0.82, 0.22, 0.22],
    "label": [
        "Priorità commerciale",
        "Bisogno alto · approccio selettivo",
        "Valore alto · potenziale limitato",
        "Monitoraggio"
    ]
})).mark_text(
    align="center",
    fontSize=13,
    fontWeight="bold",
    opacity=0.5
).encode(
    x="x:Q",
    y="y:Q",
    text="label:N"
)

# render finale
st.altair_chart(scatter + vline + hline + labels, use_container_width=True)


# -------------------------------------------------
# TABELLA OPERATIVA COMUNI
# -------------------------------------------------
st.subheader(f"Comuni prioritari ordinati per {score_label}")

cols_show = [
    "luogo_di_residenza",
    "n_clienti",
    "penetrazione_casa",
    "penetrazione_salute",
    "protection_gap_casa",
    "protection_gap_salute",
    "valore_immobiliare_medio",
    "potential_score_casa",
    "potential_score_salute",
]

df_table = (
    df_ctx[cols_show]
    .sort_values(score_col, ascending=False)
    .head(30)
    .rename(columns={
        "luogo_di_residenza": "Comune",
        "n_clienti": "Clienti attuali",
        "penetrazione_casa": "Penetrazione Casa",
        "penetrazione_salute": "Penetrazione Salute",
        "protection_gap_casa": "Bisogno Casa non coperto",
        "protection_gap_salute": "Bisogno Salute non coperto",
        "valore_immobiliare_medio": "Valore immobiliare medio (€)",
        "potential_score_casa": "Potenziale Casa",
        "potential_score_salute": "Potenziale Salute",
    })
    .reset_index(drop=True)
)

df_table = df_table.replace({
    "Penetrazione Casa": {0: "No", 1: "Sì"},
    "Penetrazione Salute": {0: "No", 1: "Sì"},
    "Bisogno Casa non coperto": {0: "No", 1: "Sì"},
    "Bisogno Salute non coperto": {0: "No", 1: "Sì"},
})

st.dataframe(
    df_table.style.format({
        "Valore immobiliare medio (€)": "€ {:,.0f}",
        "Potenziale Casa": "{:.2f}",
        "Potenziale Salute": "{:.2f}",
    }),
    use_container_width=True,
    height=420
)




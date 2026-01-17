import streamlit as st
import pandas as pd
import altair as alt

from src.data import get_df

st.set_page_config(
    page_title="Profili cliente",
    layout="wide"
)

# ---- GLOBAL CSS ----
st.markdown(
    """
    <style>
    /* Nasconde menu automatico */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Rimuove padding alto della sidebar */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.1rem;
    }

    /* Rimuove margine automatico sopra il primo elemento */
    section[data-testid="stSidebar"] img:first-of-type {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.image("assets/logo.png", use_container_width=True)
st.sidebar.markdown("")

st.sidebar.page_link("app.py", label="Home")
st.sidebar.page_link("pages/01_Profili_cliente.py", label="Profili cliente")
st.sidebar.page_link("pages/02_Territorio.py", label="Territorio")
st.sidebar.page_link("pages/03_Chi_contattare_adesso.py", label="Chi contattare adesso")

st.sidebar.markdown("---")

st.title("👥 CONOSCIAMO IL CLIENTE")
st.caption("Qui trovi una lettura chiara dei tuoi clienti: chi sono, che valore hanno per Vita Sicura e come si comportano nel tempo. Usa questi profili per adattare il tuo approccio, capire su chi investire più tempo e costruire una relazione coerente con i bisogni reali dei tuoi clienti.")

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
df = get_df("clienti_clusterizzati.csv")

# -------------------------------------------------
# BUSINESS LABELS (presentation layer)
# -------------------------------------------------

LABELS = {
    "nome": "Nome",
    "cognome": "Cognome",
    "codice_cliente": "Cliente ID",
    "persona_label": "Persona",
    "cluster_risposta": "Propensione alla risposta",
    "zona_di_residenza": "Zona",
    "clv_stimato": "Customer Lifetime Value (€)",
    "potenziale_crescita": "Potenziale di crescita",
    "engagement_score": "Livello di engagement",
    "satisfaction_score": "Soddisfazione cliente",
    "reclami_totali": "Numero reclami",
    "num_polizze_totali": "Numero polizze"
}

def rename_for_display(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in LABELS.items() if k in df.columns})

# -------------------------------------------------
# SIDEBAR FILTERS — consulente-first
# -------------------------------------------------

# 0) Crea subito la colonna (così df_ctx la eredita sempre)
cluster_resp_map = {
    "high_responder": "Alta",
    "moderate_responder": "Media",
    "low_responder": "Bassa"
}
df["probabilita_risposta"] = df["cluster_risposta"].map(cluster_resp_map)

# 1) Cliente (focus singolo vs vista aggregata)
df["cliente_label"] = (
    df["nome"].fillna("").astype(str).str.title() + " " +
    df["cognome"].fillna("").astype(str).str.title() +
    " — ID " + df["codice_cliente"].astype(str)
)

cliente_options = ["Tutti"] + sorted(df["cliente_label"].unique().tolist())

cliente_sel = st.sidebar.selectbox(
    "👤 Cliente",
    options=cliente_options,
    index=0
)

if cliente_sel == "Tutti":
    df_ctx = df.copy()
    cliente_row = None
else:
    cliente_id = int(cliente_sel.split("ID ")[-1])
    df_ctx = df[df["codice_cliente"] == cliente_id].copy()
    cliente_row = df_ctx.iloc[0]

st.sidebar.markdown("")

# 2) Probabilità di risposta
cluster_resp_options = ["Tutte", "Alta", "Media", "Bassa"]

cluster_resp_sel = st.sidebar.selectbox(
    "📈 Probabilità di risposta",
    options=cluster_resp_options
)

if cluster_resp_sel == "Tutte":
    cluster_resp_sel = df["probabilita_risposta"].dropna().unique().tolist()
else:
    cluster_resp_sel = [cluster_resp_sel]

st.sidebar.markdown("")

# 3) Area geografica
zona_options = ["Tutte"] + sorted(df["zona_di_residenza"].dropna().unique())

zona_sel = st.sidebar.selectbox(
    "🏘️ Area geografica",
    options=zona_options
)

if zona_sel == "Tutte":
    zona_sel = df["zona_di_residenza"].dropna().unique().tolist()
else:
    zona_sel = [zona_sel]

st.sidebar.markdown("")

# 4) Profilo cliente (Persona)
persona_options = ["Tutti"] + sorted(df["persona_label"].dropna().unique())

persona_sel = st.sidebar.selectbox(
    "🎭 Profilo cliente",
    options=persona_options,
    index=0
)

if persona_sel == "Tutti":
    persona_sel = df["persona_label"].dropna().unique().tolist()
else:
    persona_sel = [persona_sel]

# -------------------------------------------------
# APPLY FILTERS (cumulativi)
# -------------------------------------------------
df_ctx = df_ctx[
    df_ctx["persona_label"].isin(persona_sel)
    & df_ctx["probabilita_risposta"].isin(cluster_resp_sel)
    & df_ctx["zona_di_residenza"].isin(zona_sel)
]

# -------------------------------------------------
# KPI HEADER
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("**CLIENTI**", f"{len(df_ctx):,}")
c2.metric("**VALORE MEDIO CLIENTE (€)**", f"{df_ctx['clv_stimato'].mean():,.0f} €")
c3.metric("**ENGAGEMENT**", f"{df_ctx['engagement_score'].mean():.1f}")
c4.metric("**RECLAMI MEDI**", f"{df_ctx['reclami_totali'].mean():.2f}")

st.markdown("---")

# -------------------------------------------------
# DISTRIBUZIONE PERSONAS + CLV MEDIO
# -------------------------------------------------
st.markdown(
    "<h3 style='text-align: center;'>Dove sono i clienti e dove si genera valore</h3>",
    unsafe_allow_html=True
)

# Distribuzione clienti per persona
persona_dist = (
    df_ctx
    .groupby("persona_label")
    .size()
    .reset_index(name="n_clienti")
    .sort_values("n_clienti", ascending=False)
)

# CLV medio per persona
clv_persona = (
    df_ctx
    .groupby("persona_label", as_index=False)
    .agg(clv_medio=("clv_stimato", "mean"))
)

import altair as alt

bar_dist = alt.Chart(persona_dist).mark_bar().encode(
    y=alt.Y(
        "persona_label:N",
        title="Persona",
        sort="-x",
        axis=alt.Axis(labelLimit=300)
    ),
    x=alt.X(
        "n_clienti:Q",
        title="Clienti nel profilo"
    ),
    tooltip=["persona_label", "n_clienti"]
).properties(height=280)

bar_clv = alt.Chart(clv_persona).mark_bar().encode(
    y=alt.Y(
        "persona_label:N",
        title="Persona",
        sort="-x",
        axis=alt.Axis(labelLimit=300)
    ),
    x=alt.X(
        "clv_medio:Q",
        title="Valore medio per cliente (€)",
        axis=alt.Axis(format=",.0f")
    ),
    tooltip=[
        "persona_label",
        alt.Tooltip("clv_medio:Q", format=",.0f")
    ]
).properties(height=280)

c1, c2 = st.columns(2)
c1.altair_chart(bar_dist, use_container_width=True)
c2.altair_chart(bar_clv, use_container_width=True)


# -------------------------------------------------
# PROFILO MEDIO PER PERSONA
# -------------------------------------------------
st.subheader("Come si comportano i diversi profili di clienti")

profile_cols = [
    "clv_stimato",
    "potenziale_crescita",
    "engagement_score",
    "satisfaction_score",
    "reclami_totali",
    "num_polizze_totali",
]

profile = (
    df_ctx
    .groupby("persona_label")[profile_cols]
    .mean()
    .round(2)
)

profile_display = profile.rename(columns={
    "clv_stimato": "Valore medio cliente (€)",
    "potenziale_crescita": "Potenziale di crescita",
    "engagement_score": "Engagement (0–100)",
    "satisfaction_score": "Soddisfazione",
    "reclami_totali": "Reclami medi",
    "num_polizze_totali": "N° polizze medie"
})

profile_display = profile_display.rename_axis("Profilo cliente")

profile_display = profile_display.style.format({
    "Valore medio cliente (€)": "€ {:,.0f}",
    "Potenziale di crescita": "{:.1f}",
    "Engagement (0–100)": "{:.1f}",
    "Soddisfazione": "{:.1f}",
    "Reclami medi": "{:.2f}",
    "N° polizze medie": "{:.1f}",
})

st.dataframe(profile_display, use_container_width=True)

# -------------------------------------------------
# TABELLA OPERATIVA CLIENTI
# -------------------------------------------------
st.subheader("Clienti con maggiore potenziale")

cols_show = [
    "codice_cliente",
    "nome",
    "cognome",
    "persona_label",
    "cluster_risposta",
    "zona_di_residenza",
    "clv_stimato",
    "potenziale_crescita",
    "engagement_score",
    "satisfaction_score",
    "reclami_totali",
]

df_table = (
    df_ctx[cols_show]
    .sort_values("clv_stimato", ascending=False)
    .rename(columns={
        "codice_cliente": "ID Cliente",
        "nome": "Nome",
        "cognome": "Cognome",
        "persona_label": "Profilo cliente",
        "cluster_risposta": "Probabilità di risposta",
        "zona_di_residenza": "Zona",
        "clv_stimato": "Valore cliente (€)",
        "potenziale_crescita": "Potenziale",
        "engagement_score": "Engagement (0–100)",
        "satisfaction_score": "Soddisfazione",
        "reclami_totali": "Reclami"
    })
    .reset_index(drop=True)
)

st.dataframe(
    df_table,
    use_container_width=True,
    height=420
)

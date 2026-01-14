import streamlit as st
import pandas as pd
import altair as alt

from src.data import get_df

st.set_page_config(layout="wide")

st.title("👥 Stream 1 — Customer Personas")
st.caption("Segmentazione clienti e profili comportamentali per supporto consulenziale")

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
# SIDEBAR FILTERS (consulente-friendly)
# -------------------------------------------------
df["cliente_label"] = (
    df["nome"].fillna("").astype(str).str.title() + " " +
    df["cognome"].fillna("").astype(str).str.title() +
    " — ID " + df["codice_cliente"].astype(str)
)

cliente_options = ["Tutti"] + sorted(df["cliente_label"].unique().tolist())

cliente_sel = st.sidebar.selectbox(
    "👤 **Cliente**",
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

# -------------------------------------------------
cluster_resp_options = ["Tutte"] + sorted(df["cluster_risposta"].dropna().unique())
cluster_resp_sel = st.sidebar.selectbox(
    "**Propensione**",
    options=cluster_resp_options
)
if cluster_resp_sel == "Tutte":
    cluster_resp_sel = df["cluster_risposta"].dropna().unique().tolist()
else:
    cluster_resp_sel = [cluster_resp_sel]

# -------------------------------------------------
zona_options = ["Tutte"] + sorted(df["zona_di_residenza"].dropna().unique())
zona_sel = st.sidebar.selectbox(
    "🏘️ **Zona di residenza**",
    options=zona_options
)
if zona_sel == "Tutte":
    zona_sel = df["zona_di_residenza"].dropna().unique().tolist()
else:
    zona_sel = [zona_sel]

# --------------------------------------------------
st.sidebar.markdown("🎭 **Persona**")
persona_options = sorted(df["persona_label"].unique())
persona_sel = [
    p for p in persona_options
    if st.sidebar.checkbox(p, value=True, key=f"persona_{p}")]


# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------
# ===== Applicazione filtri cumulativi =====
df_ctx = df_ctx[
    df_ctx["persona_label"].isin(persona_sel)
    & df_ctx["cluster_risposta"].isin(cluster_resp_sel)
    & df_ctx["zona_di_residenza"].isin(zona_sel)
]

# -------------------------------------------------
# KPI HEADER
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("**CLIENTI**", f"{len(df_ctx):,}")
c2.metric("**CLV MEDIO**", f"{df_ctx['clv_stimato'].mean():,.0f} €")
c3.metric("**ENGAGEMENT**", f"{df_ctx['engagement_score'].mean():.1f}")
c4.metric("**RECLAMI MEDI**", f"{df_ctx['reclami_totali'].mean():.2f}")

st.markdown("---")

# -------------------------------------------------
# DISTRIBUZIONE PERSONAS + CLV MEDIO
# -------------------------------------------------
st.subheader("Distribuzione Personas")

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
        title="Numero clienti"
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
        title="CLV medio (€)",
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
st.subheader("Profilo medio per Persona")

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

st.dataframe(profile, use_container_width=True)

# -------------------------------------------------
# TABELLA OPERATIVA CLIENTI
# -------------------------------------------------
st.subheader("Clienti (vista operativa)")

cols_show = [
    "nome",
    "cognome",
    "codice_cliente",
    "persona_label",
    "cluster_risposta",
    "zona_di_residenza",
    "clv_stimato",
    "potenziale_crescita",
    "engagement_score",
    "satisfaction_score",
    "reclami_totali",
]

st.dataframe(
    df_ctx[cols_show]
    .sort_values("clv_stimato", ascending=False),
    use_container_width=True,
    height=420
)

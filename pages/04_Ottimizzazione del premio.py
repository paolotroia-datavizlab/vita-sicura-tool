import streamlit as st
import pandas as pd
import altair as alt

from src.data import get_df

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="💰 Ottimizzazione del premio",
    layout="wide"
)

st.title("💰 Come ottimizzare il premio per il cliente")
st.caption(
    "Valutazione dell’impatto delle azioni di pricing suggerite, "
    "per trovare il giusto equilibrio tra sostenibilità tecnica e valore per il cliente."
)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
df_pricing = get_df("pricing_ai_output.csv")
df_clienti = get_df("clienti_clusterizzati.csv")

# -------------------------------------------------
# MERGE NOME / COGNOME
# -------------------------------------------------
df = df_pricing.merge(
    df_clienti[["codice_cliente", "nome", "cognome"]],
    on="codice_cliente",
    how="left"
)

df["cliente"] = (
    df["nome"].fillna("").str.title() + " " +
    df["cognome"].fillna("").str.title() +
    " — ID " + df["codice_cliente"].astype(str)
)

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.header("Filtri")

cliente_options = ["Tutti"] + sorted(df["cliente"].unique())
cliente_sel = st.sidebar.selectbox("👤 Cliente", cliente_options)

prodotto_options = ["Tutti"] + sorted(df["prodotto"].unique())
prodotto_sel = st.sidebar.selectbox("📦 Prodotto", prodotto_options)

azione_options = ["Tutte"] + sorted(df["pricing_action"].unique())
azione_sel = st.sidebar.selectbox("⚖️ Azione pricing", azione_options)

# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------
df_ctx = df.copy()

if cliente_sel != "Tutti":
    cliente_id = int(cliente_sel.split("ID ")[-1])
    df_ctx = df_ctx[df_ctx["codice_cliente"] == cliente_id]

if prodotto_sel != "Tutti":
    df_ctx = df_ctx[df_ctx["prodotto"] == prodotto_sel]

if azione_sel != "Tutte":
    df_ctx = df_ctx[df_ctx["pricing_action"] == azione_sel]

# -------------------------------------------------
# 🔑 CALCOLO DELTA LOSS RATIO (PRIMA DEI KPI)
# -------------------------------------------------
df_ctx["delta_loss_ratio"] = (
    df_ctx["loss_ratio_post"] - df_ctx["loss_ratio_pred"]
)

# -------------------------------------------------
# KPI HEADER
# -------------------------------------------------
c1, c2, c3 = st.columns(3)

c1.metric("**CLIENTI MIGLIORATIVI**", f"{(df_ctx['delta_loss_ratio'] < 0).mean()*100:.0f}%")
c2.metric("**IMPATTO MEDIO**", f"{df_ctx['delta_loss_ratio'].mean():.2f}")
c3.metric("**CLIENTI PEGGIORATIVI**", f"{(df_ctx['delta_loss_ratio'] > 0).mean()*100:.0f}%")

st.markdown("---")

# -------------------------------------------------
# GRAFICI — IMPATTO PRICING
# -------------------------------------------------
st.subheader("Impatto del pricing sul Loss Ratio")

# ===============================
# GRAFICO 1 — PRIMA / DOPO
# ===============================
lr_dist = df_ctx.melt(
    value_vars=["loss_ratio_pred", "loss_ratio_post"],
    var_name="fase",
    value_name="loss_ratio"
)

lr_dist["fase"] = lr_dist["fase"].map({
    "loss_ratio_pred": "Prima",
    "loss_ratio_post": "Dopo"
})

lr_dist = lr_dist[lr_dist["loss_ratio"] <= 10]

hist_lr = alt.Chart(lr_dist).mark_bar(opacity=0.75).encode(
    x=alt.X(
        "loss_ratio:Q",
        bin=alt.Bin(maxbins=30),
        title="Loss Ratio (0–10)"
    ),
    y=alt.Y("count():Q", title="Numero clienti"),
    color=alt.Color("fase:N", title="Fase"),
    tooltip=["fase:N", "count():Q"]
).properties(height=300)

st.altair_chart(hist_lr, use_container_width=True)

st.markdown("---")

# ===============================
# GRAFICO 2 — DELTA LOSS RATIO
# ===============================
delta_lr = alt.Chart(df_ctx).mark_bar().encode(
    x=alt.X(
        "delta_loss_ratio:Q",
        bin=alt.Bin(maxbins=30),
        title="Δ Loss Ratio (Dopo − Prima)"
    ),
    y=alt.Y("count():Q", title="Numero clienti"),
    color=alt.condition(
        alt.datum.delta_loss_ratio < 0,
        alt.value("#2ecc71"),  # miglioramento
        alt.value("#e74c3c")   # peggioramento
    ),
    tooltip=["count():Q"]
).properties(height=260)

st.altair_chart(delta_lr, use_container_width=True)

st.caption(
    "Verde = miglioramento del Loss Ratio dopo il pricing · "
    "Rosso = peggioramento"
)

st.markdown("---")

# -------------------------------------------------
# TABELLA OPERATIVA — PRICING (vista consulente)
# -------------------------------------------------
st.subheader("Proposte di pricing — vista consulente")

df_table = (
    df_ctx[[
        "nome",
        "cognome",
        "prodotto",
        "premio_totale_annuo",
        "pricing_action",
        "loss_ratio_pred",
        "loss_ratio_post",
        "delta_loss_ratio",
    ]]
    .rename(columns={
        "nome": "Nome",
        "cognome": "Cognome",
        "prodotto": "Prodotto",
        "premio_totale_annuo": "Premio annuo (€)",
        "pricing_action": "Azione di pricing",
        "loss_ratio_pred": "Loss Ratio prima",
        "loss_ratio_post": "Loss Ratio dopo",
        "delta_loss_ratio": "Δ Loss Ratio",
    })
    .sort_values("Δ Loss Ratio")  # miglioramenti in alto
    .reset_index(drop=True)
)

def color_delta(val):
    if val < 0:
        return "color: #2ecc71; font-weight: 600;"  # verde
    elif val > 0:
        return "color: #e74c3c; font-weight: 600;"  # rosso
    return ""

st.dataframe(
    df_table.style
        .format({
            "Premio annuo (€)": "€ {:,.0f}",
            "Loss Ratio prima": "{:.2f}",
            "Loss Ratio dopo": "{:.2f}",
            "Δ Loss Ratio": "{:+.2f}",
        })
        .applymap(color_delta, subset=["Δ Loss Ratio"]),
    use_container_width=True,
    height=420
)



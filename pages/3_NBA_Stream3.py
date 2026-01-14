import streamlit as st
import pandas as pd
import altair as alt

from src.data import get_df
from src.llm import ask_llm

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(layout="wide")
st.title("🎯 Stream 3 — Next Best Action")
st.caption("Supporto operativo al consulente per azioni prioritarie sui clienti")

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
df_nba = get_df("nba_scores_clienti.csv")
df_clienti = get_df("clienti_clusterizzati.csv")

df = df_nba.merge(
    df_clienti[["codice_cliente", "nome", "cognome"]],
    on="codice_cliente",
    how="left"
)

df["cliente_label"] = (
    df["nome"].fillna("").str.title() + " " +
    df["cognome"].fillna("").str.title() +
    " — ID " + df["codice_cliente"].astype(str)
)

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.header("Filtri")

action_options = ["Tutte"] + sorted(df["next_best_action"].unique())
action_sel = st.sidebar.selectbox("Next Best Action", action_options)

cliente_options = ["Tutti"] + sorted(df["cliente_label"].unique())
cliente_sel = st.sidebar.selectbox("Cliente", cliente_options)

df_ctx = df.copy()

if action_sel != "Tutte":
    df_ctx = df_ctx[df_ctx["next_best_action"] == action_sel]

if cliente_sel != "Tutti":
    cliente_id = int(cliente_sel.split("ID ")[-1])
    df_ctx = df_ctx[df_ctx["codice_cliente"] == cliente_id]

# -------------------------------------------------
# KPI HEADER
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("CLIENTI", f"{len(df_ctx):,}")
c2.metric("VALORE ATTESO MEDIO (€)", f"{df_ctx['valore_atteso_euro'].mean():,.0f}")
c3.metric("PRIORITY SCORE MEDIO", f"{df_ctx['priority_score'].mean():.0f}")
c4.metric("CLV MEDIO (€)", f"{df_ctx['clv_stimato'].mean():,.0f}")

st.markdown("---")

# -------------------------------------------------
# DISTRIBUZIONE NEXT BEST ACTION
# -------------------------------------------------
st.subheader("Distribuzione Next Best Action")

action_dist = (
    df.groupby("next_best_action")
    .agg(
        n_clienti=("codice_cliente", "count"),
        valore_totale=("valore_atteso_euro", "sum")
    )
    .reset_index()
)

action_dist["valore_medio"] = (
    action_dist["valore_totale"] / action_dist["n_clienti"]
)

bar_vol = alt.Chart(action_dist).mark_bar().encode(
    y=alt.Y("next_best_action:N", sort="-x", title="Azione", axis=alt.Axis(labelLimit=300)),
    x=alt.X("n_clienti:Q", title="Numero clienti"),
    tooltip=["next_best_action", "n_clienti"]
).properties(height=280)

bar_val = alt.Chart(action_dist).mark_bar().encode(
    y=alt.Y("next_best_action:N", sort="-x", title="Azione", axis=alt.Axis(labelLimit=300)),
    x=alt.X(
        "valore_medio:Q",
        title="Valore atteso medio per cliente (€)",
        axis=alt.Axis(format=",.0f")
    ),
    tooltip=["next_best_action", alt.Tooltip("valore_medio:Q", format=",.0f")]
).properties(height=280)

c1, c2 = st.columns(2)
c1.altair_chart(bar_vol, use_container_width=True)
c2.altair_chart(bar_val, use_container_width=True)

st.markdown("---")

# -------------------------------------------------
# CLIENTI PRIORITARI
# -------------------------------------------------
st.subheader("Clienti prioritari (vista consulente)")

cols_show = [
    "cliente_label",
    "next_best_action",
    "priority_score",
    "valore_atteso_euro",
    "churn_score_model",
    "cross_sell_score",
    "engagement_score",
    "mesi_da_ultima_visita",
    "clv_stimato",
]

df_table = (
    df_ctx[cols_show]
    .sort_values("priority_score", ascending=False)
    .head(30)
)

st.dataframe(df_table, use_container_width=True, height=380)

st.markdown("---")

# -------------------------------------------------
# AI COPILOT — LLM EXPLANATION & ACTION LAYER
# -------------------------------------------------
st.subheader("💬 AI Copilot — Supporto al consulente")

if cliente_sel == "Tutti" or df_ctx.empty:
    st.info("Seleziona un cliente per attivare l’AI Copilot.")
    st.stop()

row = df_ctx.iloc[0]

# ---------- CONTESTO CLIENTE (CHIUSO E CHIARO)
with st.expander("📌 Contesto cliente usato dall’AI", expanded=False):
    st.markdown(f"""
    **Cliente:** {row['cliente_label']}  
    **Azione suggerita:** {row['next_best_action']}  
    **Priority score:** {row['priority_score']:.0f}  
    **Valore atteso:** {row['valore_atteso_euro']:,.0f} €  
    **Churn score:** {row['churn_score_model']:.2f}  
    **Cross-sell score:** {row['cross_sell_score']:.2f}  
    **CLV:** {row['clv_stimato']:,.0f} €  
    **Engagement:** {row['engagement_score']:.1f}  
    **Mesi da ultima visita:** {row['mesi_da_ultima_visita']}
    """)

# ---------- STATO CHAT
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- AZIONI GUIDATE (UX KEY)
st.markdown("### ⚡ Azioni rapide")

q1, q2, q3, q4 = st.columns(4)

quick_prompt = None

with q1:
    if st.button("📞 Perché chiamarlo"):
        quick_prompt = "Perché questo cliente è prioritario?"

with q2:
    if st.button("🗣️ Apri la chiamata"):
        quick_prompt = "Come dovrei iniziare la conversazione?"

with q3:
    if st.button("🎯 Cosa proporre"):
        quick_prompt = "Qual è la proposta più adatta?"

with q4:
    if st.button("⚠️ Cosa evitare"):
        quick_prompt = "Cosa dovrei evitare con questo cliente?"

# ---------- INPUT LIBERO
user_input = st.chat_input(
    "Oppure scrivi una domanda personalizzata all’AI…"
)

if quick_prompt:
    user_input = quick_prompt

# ---------- CHIAMATA LLM
if user_input:
    st.session_state.chat_history.append(("user", user_input))

    prompt = f"""
Sei un AI Copilot per consulenti assicurativi Generali.

PROFILO CLIENTE:
- Azione suggerita: {row['next_best_action']}
- Priority score: {row['priority_score']:.0f}
- Valore atteso: {row['valore_atteso_euro']:,.0f} €
- Churn score: {row['churn_score_model']:.2f}
- Cross-sell score: {row['cross_sell_score']:.2f}
- CLV: {row['clv_stimato']:,.0f} €
- Engagement: {row['engagement_score']:.1f}
- Mesi da ultima visita: {row['mesi_da_ultima_visita']}

ISTRUZIONI:
- Non ricalcolare i dati
- Spiegare la logica decisionale
- Dare suggerimenti concreti per una chiamata reale
- Tono professionale, chiaro, pratico
- Risposta max 8–10 righe

DOMANDA DEL CONSULENTE:
{user_input}
"""

    with st.spinner("L’AI sta preparando la risposta…"):
        ai_response = ask_llm(prompt)

    st.session_state.chat_history.append(("assistant", ai_response))

# ---------- RENDER CHAT
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

# ---------- RESET
if st.button("🔄 Reset conversazione"):
    st.session_state.chat_history = []
    st.experimental_rerun()





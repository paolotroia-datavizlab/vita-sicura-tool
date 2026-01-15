import streamlit as st
import pandas as pd
import altair as alt

from src.data import get_df
from src.llm import ask_llm

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="🎯 Chi contattare adesso",
    layout="wide"
)

st.title("🎯 CHI CONTATTARE ADESSO?")
st.caption(
    "Indicazioni operative su quali clienti contattare e perché, combinando valore economico, "
    "rischio di abbandono e opportunità commerciali. "
    "I clienti a rischio churn hanno una probabilità stimata di abbandono ≥ 70%."
)

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

pct_rischio_churn = ((df_ctx["churn_score_model"] > 0.7).mean() * 100)

c1.metric("**CLIENTI**", f"{len(df_ctx):,}")
c2.metric("**VALORE ECONOMICO STIMATO (€)**", f"{df_ctx['valore_atteso_euro'].mean():,.0f} €")
c3.metric("**CLIENTI A RISCHIO CHURN**", f"{pct_rischio_churn:.0f}%")
c4.metric("**VALORE MEDIO CLIENTE (€)**", f"{df_ctx['clv_stimato'].mean():,.0f} €")

st.markdown("---")

# -------------------------------------------------
# DISTRIBUZIONE NEXT BEST ACTION
# -------------------------------------------------
st.markdown(
    "<h3 style='text-align: center;'>Come si distribuiscono le azioni consigliate</h3>",
    unsafe_allow_html=True
)
st.caption(
    "La vista mostra quante volte ciascuna azione è consigliata e il valore economico medio associato, "
    "per aiutare a capire dove si concentra l’impatto delle azioni suggerite."
)

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

# Second bar chart for average economic value
bar_val = alt.Chart(action_dist).mark_bar().encode(
    y=alt.Y(
        "next_best_action:N",
        sort="-x",
        title="Azione",
        axis=alt.Axis(labelLimit=300)
    ),
    x=alt.X(
        "valore_medio:Q",
        title="Valore economico stimato (€)",
        axis=alt.Axis(format=",.0f")
    ),
    tooltip=[
        "next_best_action",
        alt.Tooltip(
            "valore_medio:Q",
            format=",.0f",
            title="Valore economico stimato (€)"
        )
    ]
).properties(height=280)

c1, c2 = st.columns(2)
c1.altair_chart(bar_vol, use_container_width=True)
c2.altair_chart(bar_val, use_container_width=True)

st.markdown("---")

# ------------------------------------------------- # 
# CLIENTI PRIORITARI 
# -------------------------------------------------
st.subheader("Clienti su cui agire ora")

cols_show = [
    "cliente_label",
    "next_best_action",
    "valore_atteso_euro",
    "churn_score_model",
    "engagement_score",
    "mesi_da_ultima_visita",
    "clv_stimato",
]

df_table = (
    df_ctx[cols_show]
    .sort_values("valore_atteso_euro", ascending=False)
    .head(30)
    .rename(columns={
        "cliente_label": "Cliente",
        "next_best_action": "Azione consigliata",
        "valore_atteso_euro": "Valore economico stimato (€)",
        "churn_score_model": "Rischio churn (%)",
        "engagement_score": "Engagement (0–100)",
        "mesi_da_ultima_visita": "Ultimo contatto (mesi)",
        "clv_stimato": "Valore cliente (CLV €)",
    })
    .reset_index(drop=True)
)

df_table["Rischio churn (%)"] = df_table["Rischio churn (%)"] * 100

st.dataframe(
    df_table.style.format({
        "Valore economico stimato (€)": "€ {:,.0f}",
        "Valore cliente (CLV €)": "€ {:,.0f}",
        "Rischio churn (%)": "{:.0f} %",
        "Engagement (0–100)": "{:.1f}",
        "Ultimo contatto (mesi)": "{:.0f}",
    }),
    use_container_width=True,
    height=380
)

st.markdown("---")

# -------------------------------------------------
# 🧠 VITA — CONSULENTE AI
# -------------------------------------------------
st.markdown(
    "<h2 style='text-align: center;'>🧠 Vita — Consulente AI</h2>",
    unsafe_allow_html=True
)
st.caption(
    "Supporto operativo per preparare la chiamata con il cliente selezionato. "
    "Vita interpreta i dati disponibili e suggerisce come impostare la conversazione, "
    "cosa proporre e quali aspetti gestire con attenzione."
)

# -------------------------------------------------
# STATO VUOTO
# -------------------------------------------------
if cliente_sel == "Tutti" or df_ctx.empty:
    st.info("Seleziona un cliente dalla tabella per attivare Vita, il tuo Consulente AI.")
    st.stop()

row = df_ctx.iloc[0]

# -------------------------------------------------
# RIEPILOGO CLIENTE (BASE DECISIONALE)
# -------------------------------------------------
with st.expander("📌 Riepilogo cliente (base decisionale)", expanded=False):
    st.markdown(f"""
    **Cliente:** {row['cliente_label']}  
    **Azione consigliata:** {row['next_best_action']}  
    **Valore economico stimato:** {row['valore_atteso_euro']:,.0f} €  
    **Rischio di abbandono stimato:** {row['churn_score_model']*100:.0f}%  
    **Valore cliente (CLV):** {row['clv_stimato']:,.0f} €  
    **Livello di engagement:** {row['engagement_score']:.1f}/100  
    **Ultimo contatto:** {row['mesi_da_ultima_visita']:.0f} mesi fa
    """)

# -------------------------------------------------
# STATO CHAT
# -------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -------------------------------------------------
# AZIONI GUIDATE
# -------------------------------------------------
st.markdown("### ⚡ Come posso aiutarti ora?")
st.caption("Seleziona un’azione rapida oppure scrivi una domanda personalizzata.")

q1, q2 = st.columns(2)
quick_prompt = None

with q1:
    if st.button("📞 Prepara la chiamata"):
        quick_prompt = (
            "Preparami una sintesi operativa per la chiamata con questo cliente: "
            "obiettivo, messaggio chiave e proposta da fare."
        )
with q2:
    if st.button("⚠️ Gestire il rischio"):
        quick_prompt = (
            "Quali sono i principali rischi o criticità da considerare "
            "durante la conversazione con questo cliente?"
        )

# -------------------------------------------------
# INPUT LIBERO
# -------------------------------------------------
user_input = st.chat_input(
    "Scrivi una domanda specifica per preparare la chiamata…"
)

if quick_prompt:
    user_input = quick_prompt

# -------------------------------------------------
# CHIAMATA LLM
# -------------------------------------------------
if user_input:
    st.session_state.chat_history.append(("user", user_input))

    prompt = f"""
Agisci come un consulente senior di una compagnia assicurativa.

Il tuo obiettivo è supportare un collega nella preparazione di una chiamata con un cliente,
utilizzando esclusivamente le informazioni fornite di seguito.

PROFILO CLIENTE:
- Azione consigliata: {row['next_best_action']}
- Valore economico stimato: {row['valore_atteso_euro']:,.0f} €
- Rischio di abbandono stimato: {row['churn_score_model']*100:.0f}%
- Valore cliente (CLV): {row['clv_stimato']:,.0f} €
- Livello di engagement: {row['engagement_score']:.1f}/100
- Ultimo contatto: {row['mesi_da_ultima_visita']} mesi fa

LINEE GUIDA:
- Non ricalcolare né stimare nuovi dati
- Spiegare in modo chiaro il perché dell’azione suggerita
- Fornire indicazioni pratiche e concrete per una chiamata reale
- Linguaggio professionale, semplice, orientato all’azione
- Lunghezza massima: 8–10 righe

DOMANDA:
{user_input}
"""

    with st.spinner("Vita sta preparando il supporto alla chiamata…"):
        ai_response = ask_llm(prompt)

    st.session_state.chat_history.append(("assistant", ai_response))

# -------------------------------------------------
# RENDER CHAT
# -------------------------------------------------
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

# -------------------------------------------------
# RESET
# -------------------------------------------------
if st.button("🔄 Reset conversazione"):
    st.session_state.chat_history = []
    st.rerun()

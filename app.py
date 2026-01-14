# tool/app.py
import streamlit as st
import pandas as pd
from src.llm import ask_llm
from src.data import load_all

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Generali — AI Control Room",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Generali — AI Control Room")
st.caption(
    "I modelli predicono • l’AI interpreta • il consulente decide."
)

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
with st.spinner("Caricamento dati decisionali..."):
    data = load_all()

df_clients   = data["clienti_clusterizzati.csv"]
df_nba       = data["nba_scores_clienti.csv"]
df_pricing   = data["pricing_ai_output.csv"]
df_territory = data["potential_score_comuni.csv"]

# -------------------------------------------------
# KPI — COSA STA SUCCEDENDO OGGI
# -------------------------------------------------
st.markdown("## 📊 Situazione attuale (oggi)")

clienti_da_contattare = (
    df_nba["priority_score"] >
    df_nba["priority_score"].quantile(0.9)
).sum()

valore_a_rischio = (
    df_nba.loc[df_nba["churn_score_model"] > 0.7, "clv_stimato"]
    .sum()
)

azioni_pricing = (
    df_pricing["loss_ratio_post"] <
    df_pricing["loss_ratio_pred"]
).mean() * 100

comuni_potenziale = (
    df_territory["potential_score_casa"] > 0.6
).sum()

c1, c2, c3, c4 = st.columns(4)

c1.metric("📞 Clienti prioritari", f"{clienti_da_contattare:,}")
c2.metric("💰 Valore a rischio (€)", f"{valore_a_rischio:,.0f}")
c3.metric("📉 Pricing migliorativo", f"{azioni_pricing:.0f}%")
c4.metric("🗺️ Comuni ad alto potenziale", f"{comuni_potenziale:,}")

st.markdown("---")

# -------------------------------------------------
# AI AGENT — ROUTING OPERATIVO
# -------------------------------------------------
st.markdown("## 🚦 Cosa fare adesso")

left, right = st.columns(2)

with left:
    st.markdown("### 🎯 Clienti")
    st.markdown(
        """
        - Chi contattare **oggi**
        - Perché l’AI suggerisce un’azione
        - Script e supporto con **AI Copilot**
        """
    )
    st.page_link(
        "pages/3_NBA_Stream3.py",
        label="Vai a Next Best Action",
        icon="🎯"
    )

    st.markdown("### 👥 Personas")
    st.markdown(
        """
        - Comprendere **chi sono i clienti**
        - Valore, bisogni e comportamento
        """
    )
    st.page_link(
        "pages/1_Personas_Stream1.py",
        label="Vai a Personas",
        icon="👥"
    )

with right:
    st.markdown("### 💰 Pricing")
    st.markdown(
        """
        - Valutare l’impatto economico
        - Simulare scenari di premio
        """
    )
    st.page_link(
        "pages/4_Pricing_Stream4.py",
        label="Vai a Pricing",
        icon="💰"
    )

    st.markdown("### 🗺️ Territorio")
    st.markdown(
        """
        - Dove investire commercialmente
        - Priorità geografiche
        """
    )
    st.page_link(
        "pages/2_Territorio_Stream2.py",
        label="Vai al Territorio",
        icon="🗺️"
    )

st.markdown("---")

# -------------------------------------------------
# AI AGENT — SINTESI DECISIONALE
# -------------------------------------------------
st.markdown("## 🤖 Sintesi dell’AI (Agent view)")

st.info(
    f"""
    **Priorità della giornata**
    - Prevenire il churn su clienti ad alto valore  
    - Contattare ~{clienti_da_contattare} clienti prioritari  
    - Proteggere oltre **{valore_a_rischio:,.0f} €** di valore  

    **Supporto AI**
    - Pricing migliora la sostenibilità nel **{azioni_pricing:.0f}%** dei casi  
    - **{comuni_potenziale} comuni** mostrano alto potenziale commerciale
    """
)

st.success("✅ AI Agent operativo. Seleziona uno stream per agire.")

# -------------------------------------------------
# 🤖 AI EXECUTIVE BRIEFING (LLM)
# -------------------------------------------------
st.markdown("---")
st.markdown("## 🧠 AI Executive Briefing")

st.caption(
    "Briefing generato dall’AI sulla base degli output dei modelli. "
    "L’AI **non ricalcola**, interpreta per supportare la decisione."
)

if st.button("🧠 Genera briefing AI"):
    with st.spinner("L’AI sta preparando il briefing..."):

        context = f"""
        DATI RIASSUNTIVI:

        - Clienti prioritari: {clienti_da_contattare}
        - Valore economico a rischio: {valore_a_rischio:,.0f} €
        - Pricing migliorativo: {azioni_pricing:.0f}%
        - Comuni ad alto potenziale: {comuni_potenziale}

        OBIETTIVO:
        Supportare un consulente assicurativo nelle decisioni operative quotidiane.
        """

        prompt = f"""
        Sei un AI senior advisor per una compagnia assicurativa.

        Usa SOLO il contesto seguente:
        {context}

        Scrivi un briefing operativo che includa:
        1. Priorità principale
        2. Rischio chiave
        3. Opportunità economica
        4. Azione immediata consigliata

        Stile:
        - chiaro
        - professionale
        - orientato all’azione
        - max 8–10 righe
        """

        ai_briefing = ask_llm(prompt)

    st.success("Briefing AI generato")
    st.markdown(ai_briefing)




# tool/app.py
import streamlit as st
import pandas as pd
from src.llm import ask_llm
from src.data import load_all

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="🎛️ Home",
    page_icon="🧠",
    layout="wide"
)

st.title("Vita Sicura — Overview")

st.markdown("")
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
#st.markdown("## 📊 Situazione attuale")

# Clienti prioritari = top 10% per priorità
clienti_prioritari = (
    df_nba["priority_score"] >
    df_nba["priority_score"].quantile(0.9)
).sum()

# Valore economico a rischio (clienti con churn ≥ 70%)
valore_a_rischio = (
    df_nba.loc[df_nba["churn_score_model"] >= 0.7, "clv_stimato"]
    .sum()
)

# Azioni pricing con miglioramento tecnico
azioni_pricing_ok = (
    df_pricing["loss_ratio_post"] <
    df_pricing["loss_ratio_pred"]
).mean() * 100

# Comuni con alto potenziale Casa
comuni_potenziale = (
    df_territory["potential_score_casa"] >= 0.6
).sum()

c1, c2, c3, c4 = st.columns(4)

c1.metric("📞 Clienti da contattare", f"{clienti_prioritari:,}")
c2.metric("💰 Valore economico a rischio", f"€ {valore_a_rischio:,.0f}")
c3.metric("📉 Pricing migliorativo", f"{azioni_pricing_ok:.0f}%")
c4.metric("🗺️ Comuni prioritari", f"{comuni_potenziale:,}")

st.markdown("---")

# -------------------------------------------------
# DOVE AGIRE — ROUTING OPERATIVO
# -------------------------------------------------

left, right = st.columns(2)

with left:
    st.markdown("### 👥 Profili cliente")
    st.markdown(
        """
        - Comprendi **chi sono i tuoi clienti**
        - Valore, bisogni e comportamento
        """
    )
    st.page_link(
        "pages/01_Profili cliente.py",
        label="Vai ai Profili cliente",
        icon="👥"
    )
    st.markdown("### 🎯 Clienti")
    st.markdown(
        """
        - Individua **chi contattare oggi**
        - Capisci **perché l’AI suggerisce un’azione**
        - Preparati alla chiamata con il **Consulente AI**
        """
    )
    st.page_link(
        "pages/03_Chi contattare adesso.py",
        label="Vai a Chi contattare adesso",
        icon="🎯"
    )

with right:
    st.markdown("### 🗺️ Territorio")
    st.markdown(
        """
        - Scopri **dove investire commercialmente**
        - Priorità geografiche basate su dati
        """
    )
    st.page_link(
        "pages/02_Territorio.py",
        label="Vai al Territorio",
        icon="🗺️"
    )
    st.markdown("### 💰 Premio")
    st.markdown(
        """
        - Valuta l’impatto delle azioni di pricing
        - Capisci **cosa cambia davvero** dopo il premio
        """
    )
    st.page_link(
        "pages/04_Ottimizzazione del premio.py",
        label="Vai a Ottimizzazione premio",
        icon="💰"
    )

st.markdown("---")

# -------------------------------------------------
# SINTESI DECISIONALE DELL’AI
# -------------------------------------------------
st.markdown("## 🤖 Sintesi decisionale dell’AI")

st.info(
    f"""
    **Cosa suggerisce l’AI oggi**

    - Concentrarsi su **clienti ad alto valore con rischio churn ≥ 70%**
    - Contattare **circa {clienti_prioritari} clienti prioritari**
    - Proteggere oltre **€ {valore_a_rischio:,.0f}** di valore potenziale

    **A supporto del consulente**
    - Il pricing migliora la sostenibilità tecnica nel **{azioni_pricing_ok:.0f}%** dei casi
    - **{comuni_potenziale} comuni** mostrano elevato potenziale commerciale
    """
)

st.success("✅ AI pronta. Seleziona uno stream per passare all’azione.")

# -------------------------------------------------
# AI EXECUTIVE BRIEFING
# -------------------------------------------------
st.markdown("---")
st.markdown("## 🧠 Briefing operativo dell’AI")

st.caption(
    "Sintesi generata dall’AI a partire dagli output dei modelli. "
    "L’AI **non ricalcola**, ma interpreta per supportare le decisioni quotidiane."
)

if st.button("🧠 Genera briefing AI"):
    with st.spinner("L’AI sta preparando il briefing..."):

        context = f"""
        DATI RIASSUNTIVI:

        - Clienti prioritari: {clienti_prioritari}
        - Valore economico a rischio: € {valore_a_rischio:,.0f}
        - Pricing migliorativo: {azioni_pricing_ok:.0f}%
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




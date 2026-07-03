import streamlit as st
from groq import Groq

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Innovation Process Navigator",
    page_icon="🧭",
    layout="centered",
)

MODEL = "llama-3.3-70b-versatile"  # free tier on Groq, strong instruction-following

GREETING = """👋 **Welcome to the Innovation Process Navigator**

I'm an AI innovation coach designed to guide you through the complete SEPT Innovation Process — from wherever you are today to a **validated innovation value proposition** you can present to any stakeholder.

This tool is part of the **Certified Innovation Manager (CIM)** program by iN4iN / CONOSCOPE, based on the innovation management framework developed at the SEPT Competence Center, Universität Leipzig.

---

**Which describes you best?**

**A)** I have a digital solution or technical concept already built.
**B)** I see a problem or opportunity, but I don't know the solution yet.
**C)** I have several ideas and I need to decide which one to pursue.
"""


@st.cache_resource
def load_system_prompt() -> str:
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def get_client() -> Groq:
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error(
            "No se encontró GROQ_API_KEY en los Secrets de Streamlit. "
            "Ve a Settings → Secrets en Streamlit Cloud y agrégala."
        )
        st.stop()
    return Groq(api_key=api_key)


# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": GREETING}]

# ---------------------------------------------------------------------------
# UI — SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧭 Innovation Process Navigator")
    st.caption(
        "Based on the SEPT Innovation Process framework · "
        "Universität Leipzig · Built for CIM by iN4iN / CONOSCOPE"
    )
    st.divider()
    if st.button("🔄 Reiniciar conversación"):
        st.session_state.messages = [{"role": "assistant", "content": GREETING}]
        st.rerun()
    st.caption(
        "Este agente es una herramienta educativa. Sus resultados son "
        "borradores estructurados, no asesoría profesional, legal ni financiera."
    )

st.title("🧭 Innovation Process Navigator")

# ---------------------------------------------------------------------------
# RENDER HISTORY
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------------------------------
user_input = st.chat_input("Escribe tu respuesta aquí...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    client = get_client()
    system_prompt = load_system_prompt()

    api_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=api_messages,
                temperature=0.6,
                max_tokens=1500,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full_response += delta
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"⚠️ Error al llamar a la API de Groq: {e}"
            placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

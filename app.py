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

I'm an AI innovation coach designed to guide you through the complete SEPT Innovation Process — from wherever you are today to a validated innovation value proposition you can present to any stakeholder.

This tool is part of the Certified Innovation Manager (CIM) program, based on the innovation management framework developed at the SEPT Competence Center, Universität Leipzig.

Along the way I connect with two companion tools — the **Value Proposition Canvas** and **Quality Function Deployment (QFD)** — and I give you a short **progress summary after every step**, so you can stop anytime and resume later without losing your work.

---

**▶️ Continuing a previous session?**
If you saved a **SESSION STATE** block last time, just paste it here and I'll pick up exactly where you left off.

**🆕 Starting fresh? Which describes you best?**

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
            "GROQ_API_KEY was not found in the Streamlit Secrets. "
            "Go to Settings → Secrets in Streamlit Cloud and add it."
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
    if st.button("🔄 Reset conversation"):
        st.session_state.messages = [{"role": "assistant", "content": GREETING}]
        st.rerun()
    st.caption(
        "This agent is an educational tool. Its outputs are structured "
        "drafts, not professional, legal, or financial advice."
    )
    st.divider()
    st.markdown("#### 🔗 Companion tools")
    st.link_button(
        "Value Proposition Canvas",
        "https://claude.ai/public/artifacts/eccc7f0a-e1e0-4e54-83d4-b6dfd12fb053",
    )
    st.link_button(
        "Quality Function Deployment (QFD)",
        "https://claude.ai/public/artifacts/f1d67075-84a6-46dc-920d-ef66531cf5fe",
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
user_input = st.chat_input("Type your answer here...")

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
            full_response = f"⚠️ Error calling the Groq API: {e}"
            placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

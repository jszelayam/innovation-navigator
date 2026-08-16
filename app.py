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

I'm an AI innovation coach designed to guide you from wherever you are today to a validated innovation value proposition you can present to any stakeholder.

This tool is part of the Certified Innovation Manager (CIM) program, based on the innovation management framework developed at the SEPT Competence Center, Universität Leipzig.

**How the process works**

The SEPT Innovation Process moves through three phases. In the **Fuzzy Front End** we frame the problem, explore the opportunity, and generate and select an idea. In **New Product Development** we turn that idea into a concrete concept, understand your customer, and plan a testable prototype. In **Commercialization** we build the go to market logic and articulate everything in business language.

Between these phases sit three **decision gates**: Idea Evaluation, Feasibility Evaluation, and Market Validation. At each gate I give you an honest verdict of Go, Conditional Go, or Stop. I will not simply wave you through.

Along the way I connect with two companion tools, the **Value Proposition Canvas** and **Quality Function Deployment (QFD)**, which you will find linked in the sidebar. I also give you a short **progress summary after every step**, so you can stop anytime and resume later without losing your work.

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
    # Prefer a key the user entered in the sidebar; otherwise fall back to the
    # shared default key from Streamlit Secrets.
    user_key = st.session_state.get("user_api_key", "").strip()
    api_key = user_key or st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error(
            "GROQ_API_KEY was not found in the Streamlit Secrets. "
            "Go to Settings → Secrets in Streamlit Cloud and add it."
        )
        st.stop()
    return Groq(api_key=api_key)


def build_api_messages(system_prompt: str, messages: list) -> list:
    """Build the trimmed payload sent to the API.

    Always sends the full system prompt, plus the most recent SESSION STATE
    block found anywhere in the assistant history (as compressed memory),
    plus only the last 10 messages of the conversation. The full history stays
    in st.session_state.messages and is still rendered in the UI.
    """
    api_messages = [{"role": "system", "content": system_prompt}]

    # If the conversation is short, behave as before: send everything.
    if len(messages) <= 10:
        api_messages += [
            {"role": m["role"], "content": m["content"]} for m in messages
        ]
        return api_messages

    # Find the most recent SESSION STATE block in the assistant history.
    latest_session_state = None
    for m in reversed(messages):
        if m["role"] != "assistant":
            continue
        content = m["content"]
        start = content.find("=== SESSION STATE")
        if start == -1:
            continue
        end = content.find("=== END SESSION STATE", start)
        if end == -1:
            continue
        end += len("=== END SESSION STATE")
        # Extend to the end of that marker line (include trailing "===").
        line_end = content.find("\n", end)
        latest_session_state = content[start:] if line_end == -1 else content[start:line_end]
        break

    if latest_session_state:
        api_messages.append(
            {
                "role": "system",
                "content": (
                    "CURRENT SESSION STATE (compressed memory of everything "
                    "decided so far):\n" + latest_session_state
                ),
            }
        )

    # Only the last 10 messages of the conversation.
    api_messages += [
        {"role": m["role"], "content": m["content"]} for m in messages[-10:]
    ]
    return api_messages


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
        "Based on the SEPT Innovation Process framework · Universität Leipzig"
    )
    st.divider()
    st.session_state.user_api_key = st.text_input(
        "Your Groq API key (optional)",
        value=st.session_state.get("user_api_key", ""),
        type="password",
        help=(
            "Each team can use their own free key from console.groq.com so you "
            "don't share a daily limit. Leave blank to use the default key."
        ),
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

    api_messages = build_api_messages(system_prompt, st.session_state.messages)

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
            error_text = str(e).lower()
            if "rate_limit" in error_text or "429" in error_text:
                full_response = (
                    "⚠️ Daily token limit reached for this API key. Two options: "
                    "(1) copy your latest SESSION STATE block and continue "
                    "tomorrow, or (2) enter your own free Groq API key in the "
                    "sidebar (get one at console.groq.com) to continue right now."
                )
            else:
                full_response = f"⚠️ Error calling the Groq API: {e}"
            placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

import streamlit as st
import os
import re
import plotly.graph_objs as go
from dotenv import load_dotenv
from openai import OpenAI
import sidebar 

# Page config
st.set_page_config(page_title="ZenBot - What If Simulator", page_icon="🤖")
st.title("💬 What-If Investment Simulator")

# Load shared sidebar
sidebar.load_sidebar()

# Load OpenAI API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# System prompt
system_msg = {
    "role": "system",
    "content": (
        "You are ZenBot, a financial education chatbot designed for beginners inside a simulation game called Zentra. "
        "You help users understand general personal finance topics, investing concepts, and common scenarios through short, simple answers.\n\n"

        "⚠️ Important Compliance Notice (Canadian Regulations):\n"
        "- Never give personalized financial advice.\n"
        "- Never recommend specific stocks, funds, or investment products.\n"
        "- Never predict future performance or guarantee returns.\n"
        "- Always encourage users to do their own research or consult a licensed Canadian financial advisor.\n"
        "- If a question asks for advice, respond with a disclaimer and offer general education instead.\n\n"

        "Formatting Rules:\n"
        "- Output must be plain text only. Do not use Markdown, LaTeX, asterisks, underscores, italics, bold, or emojis.\n"
        "- Use normal sentence spacing and punctuation. Always include a space between numbers and words (e.g., 'Year 2', '500 per month').\n"
        "- Use simple keyboard characters only.\n\n"

        "Response Guidelines:\n"
        "- Keep answers short and easy to understand (3–6 sentences max).\n"
        "- Use relatable examples, not real market data.\n"
        "- If growth over time is mentioned, give approximate numbers.\n"
        "- End with one general takeaway, and remind users it’s for education only.\n\n"

        "Always prioritize clarity, simplicity, and regulatory safety. You are here to educate — not advise."
    )
}

# --- Utility Functions ---
def sanitize_response(text):
    text = re.sub(r"`+", "", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"(?<=[a-zA-Z])(?=[A-Z])", " ", text)
    return text

def clean_user_input(text):
    text = re.sub(r"(\d),\s*(\d)", r"\1\2", text)  # Fix comma spacing: 1, 000 -> 1000
    text = re.sub(r"nowversus", "now versus ", text)  # Fix merged words
    text = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", text)  # 100now -> 100 now
    text = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", text)  # versus100 -> versus 100
    return text

def simulate_investment_growth(monthly_investment, years, annual_return):
    months = years * 12
    total = 0
    balance = []
    for i in range(months):
        total += monthly_investment
        total *= (1 + annual_return / 12)
        balance.append(total)
    return balance

def simulate_market_crash(monthly_investment, years, annual_return, crash_year=2, crash_percent=0.3):
    months = years * 12
    crash_month = crash_year * 12
    total = 0
    balance = []
    for i in range(1, months + 1):
        total += monthly_investment
        total *= (1 + annual_return / 12)
        if i == crash_month:
            total *= (1 - crash_percent)
        balance.append(total)
    return balance

def plot_growth_chart(growth, years, title):
    months = list(range(1, len(growth) + 1))
    milestones = list(range(12, len(growth) + 1, 12))
    milestone_vals = [growth[m - 1] for m in milestones]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months,
        y=growth,
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#4F8EF7', width=3),
        hovertemplate='Month %{x}<br>$%{y:,.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=milestones,
        y=milestone_vals,
        mode='markers',
        name='Yearly Milestones',
        marker=dict(color='orange', size=8),
        hovertemplate='Month %{x}<br>$%{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis_title="Portfolio Value ($)",
        plot_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=40, r=40, t=60, b=40)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    st.plotly_chart(fig, use_container_width=True)

def generate_follow_ups(user_input):
    lowered = user_input.lower()
    if "versus" in lowered:
        return [
            "What if I split my investment 50/50 between lump sum and monthly?",
            "What if I delay my lump sum investment by 6 months?",
            "What if markets crash right after my lump sum investment?"
        ]
    elif "stop investing" in lowered:
        return [
            "What if I resume investing after 5 years?",
            "What happens if I withdraw everything at retirement?",
            "What if I switch to safer assets after stopping?"
        ]
    else:
        return [
            "What if I increase my monthly contributions?",
            "What if returns average only 3 percent instead of 7 percent?",
            "What if inflation outpaces my investment returns?"
        ]

def get_chat_response(user_input):
    messages = [system_msg] + st.session_state.messages + [{"role": "user", "content": user_input}]
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content

# --- Main UI ---
user_input = st.text_input("What if I...", placeholder="e.g., invest $200/month and markets crash in year 2?")

if user_input:
    cleaned = clean_user_input(user_input)
    st.session_state.messages.append({"role": "user", "content": cleaned})
    response = get_chat_response(cleaned)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Show conversation
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.write(f"**You:** {msg['content']}")
    else:
        clean = sanitize_response(msg["content"])
        st.text(f"ZenBot: {clean}")

# Suggested follow-up questions
if user_input:
    st.markdown("#### 🤔 Suggested follow-up questions:")
    for q in generate_follow_ups(user_input):
        if st.button(q):
            st.session_state.messages.append({"role": "user", "content": q})
            response = get_chat_response(q)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

# Chart trigger based on keywords
if user_input and any(k in user_input.lower() for k in ["invest", "save", "compound", "interest", "return", "growth"]):
    amount_match = re.search(r"\$?(\d{2,5})", user_input)
    time_match = re.search(r"(\d{1,2})\s*(year|month)", user_input)

    if amount_match and time_match:
        amount = int(amount_match.group(1))
        unit = time_match.group(2)
        time_value = int(time_match.group(1))
        years = round(time_value / 12, 2) if "month" in unit else time_value

        if "crash" in user_input.lower():
            growth = simulate_market_crash(amount, years, 0.07)
            title = "Simulated Growth with Market Crash in Year 2"
        else:
            growth = simulate_investment_growth(amount, years, 0.07)
            title = "Simulated Growth (7% Annual Return)"

        st.markdown("### 📊 Projection Chart:")
        plot_growth_chart(growth, years, title)

        # Add summary stats
        total_invested = amount * years * 12
        final_balance = growth[-1]
        gain = final_balance - total_invested

        if total_invested > 0:
            gain_percent = (gain / total_invested) * 100
        else:
            gain_percent = 0

        st.markdown("#### 💡 Summary")
        st.markdown(f"- **Total Invested**: ${total_invested:,.0f}")
        st.markdown(f"- **Final Portfolio Value**: ${final_balance:,.0f}")
        st.markdown(f"- **Total Gain**: ${gain:,.0f} ({gain_percent:.2f}%)")

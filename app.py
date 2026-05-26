import streamlit as st
import json
import base64
from pathlib import Path
from datetime import datetime
import re
import os
from dotenv import load_dotenv
from researcher import run_research, run_deep_research, run_company_research
from pdf_export import generate_pdf, generate_company_pdf

# ── Load environment variables ───────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def clean_field(text):
    """Strip inline markdown links and citation noise from model field values."""
    if not text:
        return text
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', str(text))
    s = re.sub(r'\(https?://\S+\)', '', s)
    s = re.sub(r'\([a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}\)', '', s)
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s

def clean_url(url):
    """Strip UTM and tracking parameters from URLs for display."""
    if not url:
        return url
    return re.sub(r'[?&]utm_[^&\s)]+', '', str(url)).rstrip('?&')

st.set_page_config(
    page_title="LeaseCheck · Due Diligence Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Styles — using st.html() so CSS actually renders on Streamlit Cloud ──────
st.html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
    --bg: #0a0f1a;
    --surface-0: #0f1520;
    --surface-1: #141c2b;
    --surface-2: #1a2436;
    --border: #1e2d44;
    --border-subtle: #162031;
    --text: #eaf0fa;
    --text-secondary: #8899b4;
    --text-muted: #5b6f8d;
    --accent: #3b82f6;
    --accent-hover: #60a5fa;
    --accent-subtle: rgba(59, 130, 246, 0.08);
    --accent-border: rgba(59, 130, 246, 0.18);
    --green: #10b981;
    --green-subtle: rgba(16, 185, 129, 0.08);
    --green-border: rgba(16, 185, 129, 0.18);
    --yellow: #f59e0b;
    --yellow-subtle: rgba(245, 158, 11, 0.08);
    --yellow-border: rgba(245, 158, 11, 0.18);
    --red: #ef4444;
    --red-subtle: rgba(239, 68, 68, 0.08);
    --red-border: rgba(239, 68, 68, 0.18);
    --radius: 10px;
    --radius-lg: 14px;
    --shadow: 0 1px 3px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.15);
    --font: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --mono: 'JetBrains Mono', monospace;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text);
    font-family: var(--font) !important;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="collapsedControl"] { display: none !important; }

.block-container {
    padding: 1.5rem 2rem 3rem 2rem;
    max-width: 1280px;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    transform: none !important;
    min-width: 240px !important;
    background: var(--surface-0) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] input {
    background: var(--surface-1) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: var(--radius) !important;
}

/* ── Inputs ───────────────────────────────────────────────────────────────── */
div[data-testid="stTextInput"] input,
div[data-testid="stTextInput"] textarea,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    background: var(--surface-1) !important;
    background-color: var(--surface-1) !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-family: var(--font) !important;
    font-size: 0.9rem !important;
    caret-color: var(--text) !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
div[data-testid="stTextInput"] input::placeholder,
div[data-baseweb="input"] input::placeholder {
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
    opacity: 1 !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-baseweb="input"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-subtle) !important;
    outline: none !important;
}
div[data-testid="stTextInput"] input:-webkit-autofill,
div[data-testid="stTextInput"] input:-webkit-autofill:hover,
div[data-testid="stTextInput"] input:-webkit-autofill:focus,
div[data-baseweb="input"] input:-webkit-autofill {
    -webkit-box-shadow: 0 0 0 1000px var(--surface-1) inset !important;
    -webkit-text-fill-color: var(--text) !important;
    border: 1px solid var(--border) !important;
}
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-testid="stTextInput"] > div {
    background: var(--surface-1) !important;
    border-color: transparent !important;
}
div[data-testid="stTextInput"] input:disabled,
div[data-baseweb="input"] input:disabled {
    background: var(--surface-0) !important;
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
    opacity: 1 !important;
}

/* ── Labels ────────────────────────────────────────────────────────────────── */
div[data-testid="stTextInput"] label,
.stTextInput label {
    font-family: var(--font) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.01em !important;
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    border: none !important;
    border-radius: var(--radius) !important;
    color: white !important;
    font-family: var(--font) !important;
    font-weight: 600 !important;
    min-height: 46px !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent-hover) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59,130,246,0.25) !important;
}
.stDownloadButton > button {
    border-radius: var(--radius) !important;
    min-height: 44px !important;
    border: 1px solid var(--border) !important;
    background: var(--surface-1) !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
    font-weight: 600 !important;
    transition: all 0.15s ease !important;
}
.stDownloadButton > button:hover {
    border-color: var(--accent) !important;
    background: var(--accent-subtle) !important;
}

/* ── Tabs ──────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: var(--surface-0);
    border-radius: var(--radius-lg);
    padding: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius) !important;
    padding: 0.5rem 1.2rem !important;
    font-family: var(--font) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: var(--text-secondary) !important;
    background: transparent !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface-2) !important;
    color: var(--text) !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Expanders ────────────────────────────────────────────────────────────── */
div[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    background: var(--surface-0) !important;
}
div[data-testid="stExpander"] summary {
    font-family: var(--font) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}
</style>
""")


# ── Header ────────────────────────────────────────────────────────────────────
_logo_path = Path(__file__).parent / "KYC_logo_official.png"
if _logo_path.exists():
    _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
    logo_html = f'<img src="data:image/png;base64,{_logo_b64}" style="height:40px;width:auto;" alt="Logo" />'
else:
    logo_html = (
        '<div style="display:flex;align-items:center;gap:0.7rem">'
        '<div style="width:36px;height:36px;background:#3b82f6;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;color:white;font-weight:700">LC</div>'
        '<div style="font-size:1.05rem;font-weight:700;color:#eaf0fa;letter-spacing:-0.02em">LeaseCheck <span style="color:#5b6f8d;font-weight:400;margin-left:0.35rem;font-size:0.82rem">Due Diligence</span></div>'
        '</div>'
    )

st.markdown(
    f'<div style="display:flex;align-items:center;justify-content:space-between;padding:0.8rem 0;margin-bottom:1.2rem;border-bottom:1px solid #1e2d44">'
    f'{logo_html}'
    f'<div style="display:flex;align-items:center;gap:6px;color:#5b6f8d;font-size:0.78rem;font-weight:500">'
    f'<div style="width:7px;height:7px;border-radius:50%;background:#10b981;box-shadow:0 0 6px rgba(16,185,129,0.4)"></div>'
    f'Online</div></div>',
    unsafe_allow_html=True
)

# ── Notices ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="border-radius:14px;padding:0.75rem 1rem;margin-bottom:1rem;font-size:0.84rem;line-height:1.5;'
    'display:flex;gap:0.6rem;align-items:flex-start;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.18);color:#fde68a">'
    '<span>⚠️</span>'
    '<div><strong>AVG / GDPR:</strong> Deze tool verzamelt uitsluitend openbaar beschikbare informatie voor legitieme compliance-doeleinden bij leaseaanvragen. '
    'Alle resultaten vereisen beoordeling door een analist. Gebruik niet zonder geldige juridische grondslag.</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_person, tab_company = st.tabs(["Persoon Check", "Bedrijf Check"])

# ── Person tab ────────────────────────────────────────────────────────────────
with tab_person:
    st.markdown('<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#5b6f8d;margin:0 0 0.8rem 0">Gegevens aanvrager</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        full_name = st.text_input("Volledige naam *", placeholder="Jan de Vries")
        city_region = st.text_input("Woonplaats / Regio *", placeholder="Amsterdam")
        context = st.text_input("Context onderzoek (optioneel)", placeholder="Leaseaanvraag · Volvo XC60 · €650/mnd")
    with c2:
        age = st.text_input("Geboortedatum (optioneel)", placeholder="15-03-1985")
        employer = st.text_input("Werkgever (optioneel)", placeholder="Deloitte")
        analyst_name = st.text_input("Naam analist (audit log)", placeholder="Uw naam")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        run_btn = st.button("Start Screening", type="primary", use_container_width=True)
    with btn_col2:
        deep_btn = st.button("Deep Scan", type="primary", use_container_width=True)

# ── Company tab ───────────────────────────────────────────────────────────────
with tab_company:
    st.markdown('<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#5b6f8d;margin:0 0 0.8rem 0">Bedrijfsgegevens</div>', unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        company_name = st.text_input("Bedrijfsnaam *", placeholder="Pon Holdings B.V.")
        company_country = st.text_input("Land / Regio *", placeholder="Nederland")
        company_context = st.text_input("Context onderzoek (optioneel)", placeholder="Wagenparkbeheer · 250 voertuigen")
    with cc2:
        company_kvk = st.text_input("KvK-nummer (optioneel)", placeholder="bv. 27532543")
        company_sector = st.text_input("Sector (optioneel)", placeholder="Automotive · Leasing")
        company_analyst = st.text_input("Naam analist (audit log)", placeholder="Uw naam", key="company_analyst")

    company_run_btn = st.button("Onderzoek Bedrijf", type="primary", use_container_width=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def render_sources(sources):
    if not sources:
        return '<div style="color:#5b6f8d;font-size:0.82rem;font-style:italic;padding:0.5rem 0">Geen bronnen gevonden.</div>'
    rows = ""
    for s in sources:
        url = clean_url(s.get("url", "#"))
        name = clean_field(s.get("name", url))
        stype = clean_field(s.get("type", "web"))
        rows += (
            f'<div style="display:flex;align-items:center;gap:0.8rem;padding:0.55rem 0;border-bottom:1px solid #162031">'
            f'<div style="flex:1;min-width:0">'
            f'<a href="{url}" target="_blank" style="color:#3b82f6;font-weight:600;font-size:0.84rem;text-decoration:none;display:block;margin-bottom:2px">{name}</a>'
            f'<span style="color:#5b6f8d;font-size:0.7rem;word-break:break-all">{url}</span>'
            f'</div>'
            f'<span style="display:inline-block;background:rgba(59,130,246,0.08);color:#60a5fa;border:1px solid rgba(59,130,246,0.18);border-radius:5px;padding:2px 7px;font-size:0.68rem;font-weight:500">{stype}</span>'
            f'</div>'
        )
    return f'<div>{rows}</div>'


def render_data_items(items, title_key, sub_keys=None, url_key=None):
    if not items:
        return '<div style="color:#5b6f8d;font-size:0.82rem;font-style:italic;padding:0.5rem 0">Onvoldoende gegevens</div>'

    sub_keys = sub_keys or []
    html = ""
    for item in items:
        title = clean_field(item.get(title_key, "—"))
        subs = " · ".join(clean_field(item.get(k, "")) for k in sub_keys if item.get(k))
        url = item.get(url_key, "") if url_key else ""

        html += f'<div style="padding:0.65rem 0;border-bottom:1px solid #162031;font-size:0.86rem">'
        html += f'<div style="font-weight:600;color:#eaf0fa">{title}</div>'
        if subs:
            html += f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px;line-height:1.5">{subs}</div>'
        if url:
            html += f'<div style="color:#3b82f6;font-size:0.72rem;margin-top:3px;word-break:break-all">{clean_field(url)}</div>'
        html += '</div>'
    return html

def verdict_color(score: int) -> str:
    if score >= 80:
        return "#10b981"
    if score >= 55:
        return "#f59e0b"
    return "#ef4444"


def display_results(result, full_name, city_region, analyst_name):
    t1, t2 = st.columns([3, 2])
    with t1:
        st.markdown(f'<div style="font-size:1.8rem;font-weight:700;color:#eaf0fa;letter-spacing:-0.02em">{full_name} <span style="color:#5b6f8d">·</span> {city_region}</div>', unsafe_allow_html=True)
    with t2:
        st.markdown(
            f'<div style="text-align:right;color:#5b6f8d;font-size:0.76rem;padding-top:10px">{datetime.now().strftime("%d %b %Y %H:%M")} · Analist: {analyst_name or "—"}</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div style="height:1px;width:100%;background:#1e2d44;margin:1rem 0"></div>', unsafe_allow_html=True)

    # ── Confidence ────────────────────────────────────────────────────────────
    score = int(result.get("confidence_score", 0))
    verdict = result.get("confidence_verdict", "Low")
    reasoning = clean_field(result.get("confidence_reasoning", ""))
    color = verdict_color(score)

    st.markdown(f"""
    <div style="background:#0f1520;border:1px solid #1e2d44;border-radius:14px;padding:1.1rem 1.2rem;display:flex;align-items:center;gap:1.2rem;margin-bottom:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.3),0 4px 12px rgba(0,0,0,0.15)">
        <div>
            <div style="font-size:3rem;font-weight:700;line-height:1;color:{color}">{score}</div>
            <div style="font-size:0.68rem;color:#5b6f8d;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;margin-top:2px">/ 100 betrouwbaarheid</div>
        </div>
        <div style="flex:1">
            <div style="font-size:1rem;font-weight:700;margin-bottom:2px;color:{color}">{verdict}</div>
            <div style="font-size:0.82rem;color:#8899b4;line-height:1.45">{reasoning}</div>
            <div style="background:#1a2436;border-radius:999px;height:6px;margin-top:10px;overflow:hidden">
                <div style="height:100%;border-radius:999px;width:{score}%;background:{color};transition:width 0.4s ease"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Variations ────────────────────────────────────────────────────────────
    variations = result.get("name_variations_searched", [])
    if variations:
        chips = "".join([f'<span style="display:inline-block;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.18);color:#60a5fa;border-radius:6px;padding:3px 8px;font-size:0.72rem;margin:2px 4px 2px 0;font-weight:500">{v}</span>' for v in variations])
        st.markdown(
            f'<div style="margin-bottom:1rem"><div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#5b6f8d;margin-bottom:0.4rem">Gezochte variaties</div>{chips}</div>',
            unsafe_allow_html=True
        )

    # ── Risk flags ────────────────────────────────────────────────────────────
    flags = result.get("risk_flags", [])
    if not flags:
        flags_html = '<div style="color:#10b981;font-weight:600;font-size:0.88rem;padding:0.2rem 0">✓ Geen risicovlaggen geïdentificeerd.</div>'
    else:
        flags_html = ""
        for f in flags:
            sev = (f.get("severity") or "low").lower()
            if sev == "high":
                bg, bc, hc = "rgba(239,68,68,0.08)", "rgba(239,68,68,0.18)", "#fca5a5"
            elif sev == "medium":
                bg, bc, hc = "rgba(245,158,11,0.08)", "rgba(245,158,11,0.18)", "#fcd34d"
            else:
                bg, bc, hc = "rgba(16,185,129,0.08)", "rgba(16,185,129,0.18)", "#6ee7b7"
            icon = "⛔" if sev == "high" else "⚠️" if sev == "medium" else "ℹ️"
            flags_html += (
                f'<div style="border-radius:10px;padding:0.75rem 0.9rem;margin-bottom:0.5rem;border:1px solid {bc};background:{bg}">'
                f'<div style="font-size:0.74rem;letter-spacing:0.06em;font-weight:700;margin-bottom:3px;text-transform:uppercase;color:{hc}">{icon} [{sev.upper()}] {clean_field(f.get("category", ""))}</div>'
                f'<div style="font-size:0.82rem;color:#eaf0fa;line-height:1.5">{clean_field(f.get("description", ""))}</div>'
                f'</div>'
            )
    st.markdown(
        f'<div style="background:#0f1520;border:1px solid #1e2d44;border-radius:14px;padding:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.3),0 4px 12px rgba(0,0,0,0.15)">'
        f'<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#5b6f8d;margin:0 0 0.8rem 0">Risicovlaggen</div>{flags_html}</div>',
        unsafe_allow_html=True
    )

    # ── Grid layout ───────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        with st.expander("Identiteit", icon=":material/fingerprint:"):
            st.markdown(render_data_items(result.get("identity_matches", []), "name", ["description", "confidence"]), unsafe_allow_html=True)
        with st.expander("Professionele Profielen", icon=":material/work:"):
            st.markdown(render_data_items(result.get("professional_profiles", []), "role", ["company", "platform"], "url_hint"), unsafe_allow_html=True)
        with st.expander("Bedrijfsregistraties", icon=":material/business_center:"):
            st.markdown(render_data_items(result.get("business_records", []), "entity", ["role", "status"], "source"), unsafe_allow_html=True)

    with col_r:
        with st.expander("Media Vermeldingen", icon=":material/newspaper:"):
            media = result.get("media_mentions", [])
            if media:
                html = ""
                for m in media:
                    sentiment = (m.get("sentiment") or "").lower()
                    icon = {"positive": "🟢", "neutral": "⚪", "negative": "🔴"}.get(sentiment, "⚪")
                    html += (
                        f'<div style="padding:0.65rem 0;border-bottom:1px solid #162031;font-size:0.86rem">'
                        f'<div style="font-weight:600;color:#eaf0fa">{icon} {clean_field(m.get("title", "—"))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px">{clean_field(m.get("source", ""))} · {clean_field(m.get("date", ""))} · {clean_field(m.get("sentiment", ""))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px;line-height:1.5">{clean_field(m.get("summary", ""))}</div>'
                        f'</div>'
                    )
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#5b6f8d;font-size:0.82rem;font-style:italic">Onvoldoende gegevens</div>', unsafe_allow_html=True)
        with st.expander("Social Media", icon=":material/public:"):
            st.markdown(render_data_items(result.get("social_media_presence", []), "platform", ["description"]), unsafe_allow_html=True)
        with st.expander("Juridische Registraties", icon=":material/gavel:"):
            st.markdown(render_data_items(result.get("legal_public_records", []), "issue_type", ["date", "summary"], "source"), unsafe_allow_html=True)

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    with st.expander("Bronnen", icon=":material/link:"):
        st.markdown(render_sources(result.get("sources", [])), unsafe_allow_html=True)

    st.divider()
    try:
        pdf_bytes = generate_pdf(result, full_name, city_region, analyst_name)
        st.download_button(
            label="⬇️ Download PDF rapport",
            data=pdf_bytes,
            file_name=f"lease_screening_{full_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.warning(f"PDF generatie mislukt: {e}")


# ── Company results renderer ──────────────────────────────────────────────────
def display_company_results(result, company_name, country, analyst_name):
    profile = result.get("company_profile", {})

    t1, t2 = st.columns([3, 2])
    with t1:
        st.markdown(f'<div style="font-size:1.8rem;font-weight:700;color:#eaf0fa;letter-spacing:-0.02em">{clean_field(profile.get("name", company_name))}</div>', unsafe_allow_html=True)
        sector = clean_field(profile.get("sector"))
        legal = clean_field(profile.get("legal_form"))
        if sector or legal:
            subtitle = " · ".join(v for v in [sector, legal] if v)
            st.markdown(f'<div style="color:#8899b4;font-size:0.9rem;margin-top:2px">{subtitle}</div>', unsafe_allow_html=True)
    with t2:
        st.markdown(
            f'<div style="text-align:right;color:#5b6f8d;font-size:0.76rem;padding-top:10px">{datetime.now().strftime("%d %b %Y %H:%M")} · Analist: {analyst_name or "—"}</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div style="height:1px;width:100%;background:#1e2d44;margin:1rem 0"></div>', unsafe_allow_html=True)

    # ── Survey card ───────────────────────────────────────────────────────────
    directors = result.get("directors_shareholders", [])
    manager = clean_field(directors[0].get("name")) if directors else "—"
    survey_fields = [
        ("Vestigingsadres",     clean_field(profile.get("address")) or "—"),
        ("Rechtsvorm",          clean_field(profile.get("legal_form")) or "—"),
        ("Sector",              clean_field(profile.get("sector")) or "—"),
        ("KvK-nummer",          clean_field(profile.get("kvk_number")) or "—"),
        ("Directeur / manager", manager),
        ("Geschat aantal medewerkers", clean_field(profile.get("size")) or "—"),
    ]
    survey_html = "".join(
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;padding:0.4rem 0;border-bottom:1px solid rgba(16,185,129,0.1)">'
        f'<span style="color:#6ee7b7;font-size:0.74rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;min-width:200px">{label}</span>'
        f'<span style="color:#eaf0fa;font-size:0.85rem;text-align:right">{value}</span>'
        f'</div>'
        for label, value in survey_fields
    )
    st.markdown(
        f'<div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.18);border-radius:14px;padding:1rem 1.2rem;margin-bottom:1rem">'
        f'<div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#10b981;margin-bottom:0.6rem">Bedrijfsonderzoek · Lease Due Diligence</div>'
        f'{survey_html}</div>',
        unsafe_allow_html=True
    )

    # ── Risk flags ────────────────────────────────────────────────────────────
    flags = result.get("risk_flags", [])
    if not flags:
        flags_html = '<div style="color:#10b981;font-weight:600;font-size:0.88rem;padding:0.2rem 0">✓ Geen risicovlaggen geïdentificeerd.</div>'
    else:
        flags_html = ""
        for f in flags:
            sev = (f.get("severity") or "low").lower()
            if sev == "high":
                bg, bc, hc = "rgba(239,68,68,0.08)", "rgba(239,68,68,0.18)", "#fca5a5"
            elif sev == "medium":
                bg, bc, hc = "rgba(245,158,11,0.08)", "rgba(245,158,11,0.18)", "#fcd34d"
            else:
                bg, bc, hc = "rgba(16,185,129,0.08)", "rgba(16,185,129,0.18)", "#6ee7b7"
            icon = "⛔" if sev == "high" else "⚠️" if sev == "medium" else "ℹ️"
            flags_html += (
                f'<div style="border-radius:10px;padding:0.75rem 0.9rem;margin-bottom:0.5rem;border:1px solid {bc};background:{bg}">'
                f'<div style="font-size:0.74rem;letter-spacing:0.06em;font-weight:700;margin-bottom:3px;text-transform:uppercase;color:{hc}">{icon} [{sev.upper()}] {clean_field(f.get("category", ""))}</div>'
                f'<div style="font-size:0.82rem;color:#eaf0fa;line-height:1.5">{clean_field(f.get("description", ""))}</div>'
                f'</div>'
            )
    st.markdown(
        f'<div style="background:#0f1520;border:1px solid #1e2d44;border-radius:14px;padding:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.3),0 4px 12px rgba(0,0,0,0.15)">'
        f'<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#5b6f8d;margin:0 0 0.8rem 0">Risicovlaggen</div>{flags_html}</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

    # ── Grid ──────────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        with st.expander("Bedrijfsprofiel", icon=":material/business:"):
            fields = [
                ("Opgericht", profile.get("founded")),
                ("Rechtsvorm", profile.get("legal_form")),
                ("Omvang", profile.get("size")),
                ("KvK", profile.get("kvk_number")),
                ("Adres", profile.get("address")),
                ("Website", profile.get("website")),
            ]
            html = ""
            for label, value in fields:
                value = clean_field(value)
                if value:
                    html += (
                        f'<div style="padding:0.65rem 0;border-bottom:1px solid #162031;font-size:0.86rem">'
                        f'<span style="color:#5b6f8d;font-size:0.76rem">{label}</span>'
                        f'<div style="font-weight:600;color:#eaf0fa;font-size:0.86rem">{value}</div>'
                        f'</div>'
                    )
            desc = clean_field(profile.get("description"))
            if desc:
                html += f'<div style="color:#8899b4;font-size:0.86rem;padding:0.5rem 0">{desc}</div>'
            st.markdown(html or '<div style="color:#5b6f8d;font-size:0.82rem;font-style:italic">Geen profielgegevens</div>', unsafe_allow_html=True)

        with st.expander("Bestuurders & Aandeelhouders", icon=":material/group:"):
            items = result.get("directors_shareholders", [])
            if items:
                html = ""
                for p in items:
                    html += (
                        f'<div style="padding:0.65rem 0;border-bottom:1px solid #162031;font-size:0.86rem">'
                        f'<div style="font-weight:600;color:#eaf0fa">{clean_field(p.get("name","—"))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px">{clean_field(p.get("role",""))} · Sinds {clean_field(p.get("since","—"))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px">{clean_field(p.get("notes",""))}</div></div>'
                    )
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#5b6f8d;font-size:0.82rem;font-style:italic">Geen gegevens gevonden</div>', unsafe_allow_html=True)

        with st.expander("Financiën", icon=":material/bar_chart:"):
            items = result.get("financials", [])
            if items:
                html = ""
                for f in items:
                    html += (
                        f'<div style="padding:0.65rem 0;border-bottom:1px solid #162031;font-size:0.86rem">'
                        f'<div style="font-weight:600;color:#eaf0fa">{clean_field(f.get("year","—"))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px">Omzet: {clean_field(f.get("revenue","—"))} · Winst: {clean_field(f.get("profit","—"))} · Medewerkers: {clean_field(f.get("employees","—"))}</div>'
                        f'<div style="color:#3b82f6;font-size:0.72rem;margin-top:3px">{clean_field(f.get("source",""))}</div></div>'
                    )
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#5b6f8d;font-size:0.82rem;font-style:italic">Geen financiële gegevens gevonden</div>', unsafe_allow_html=True)

    with col_r:
        with st.expander("Groepsstructuur", icon=":material/account_tree:"):
            items = result.get("group_structure", [])
            if items:
                html = ""
                for g in items:
                    html += (
                        f'<div style="padding:0.65rem 0;border-bottom:1px solid #162031;font-size:0.86rem">'
                        f'<div style="font-weight:600;color:#eaf0fa">{clean_field(g.get("entity","—"))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px">{clean_field(g.get("relationship",""))} · {clean_field(g.get("country",""))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px">{clean_field(g.get("notes",""))}</div></div>'
                    )
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#5b6f8d;font-size:0.82rem;font-style:italic">Geen groepsstructuur gevonden</div>', unsafe_allow_html=True)

        with st.expander("Sleutelpersonen", icon=":material/badge:"):
            items = result.get("key_people", [])
            if items:
                html = ""
                for k in items:
                    html += (
                        f'<div style="padding:0.65rem 0;border-bottom:1px solid #162031;font-size:0.86rem">'
                        f'<div style="font-weight:600;color:#eaf0fa">{clean_field(k.get("name","—"))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px">{clean_field(k.get("role",""))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px">{clean_field(k.get("description",""))}</div></div>'
                    )
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#5b6f8d;font-size:0.82rem;font-style:italic">Geen sleutelpersonen gevonden</div>', unsafe_allow_html=True)

        with st.expander("Nieuws & Media", icon=":material/newspaper:"):
            items = result.get("news_media", [])
            if items:
                html = ""
                for m in items:
                    html += (
                        f'<div style="padding:0.65rem 0;border-bottom:1px solid #162031;font-size:0.86rem">'
                        f'<div style="font-weight:600;color:#eaf0fa">{clean_field(m.get("title","—"))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px">{clean_field(m.get("source",""))} · {clean_field(m.get("date",""))}</div>'
                        f'<div style="color:#8899b4;font-size:0.78rem;margin-top:2px;line-height:1.5">{clean_field(m.get("summary",""))}</div>'
                        f'<div style="color:#3b82f6;font-size:0.72rem;margin-top:3px;word-break:break-all">{m.get("url","")}</div></div>'
                    )
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#5b6f8d;font-size:0.82rem;font-style:italic">Geen nieuws gevonden</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    with st.expander("Bronnen", icon=":material/link:"):
        st.markdown(render_sources(result.get("sources", [])), unsafe_allow_html=True)

    st.divider()
    try:
        pdf_bytes = generate_company_pdf(result, profile.get("name", company_name), country, analyst_name)
        st.download_button(
            label="⬇️ Download PDF rapport",
            data=pdf_bytes,
            file_name=f"lease_bedrijf_{company_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.warning(f"PDF generatie mislukt: {e}")


# ── Run research ──────────────────────────────────────────────────────────────
if run_btn:
    if not full_name or not city_region:
        st.error("Volledige naam en woonplaats zijn verplicht.")
        st.stop()

    with st.status("Screening wordt uitgevoerd...", expanded=True) as status:
        st.write(f"Onderzoek gestart voor **{full_name}** · {city_region}...")
        st.write("Signalen worden verzameld uit openbare bronnen...")
        result, error = run_research(
            name=full_name,
            city=city_region,
            age=age,
            employer=employer,
            context=context
        )
        if error:
            status.update(label=f"Fout: {error}", state="error")
            st.stop()
        status.update(label="Screening afgerond.", state="complete")

    with open("audit_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "analyst": analyst_name or "unknown",
            "subject_name": full_name,
            "subject_city": city_region,
            "context": context,
            "type": "lease_person"
        }, ensure_ascii=False) + "\n")

    display_results(result, full_name, city_region, analyst_name)

# ── Deep Scan ─────────────────────────────────────────────────────────────────
if deep_btn:
    if not full_name or not city_region:
        st.error("Volledige naam en woonplaats zijn verplicht.")
        st.stop()

    st.markdown(
        '<div style="border-radius:14px;padding:0.75rem 1rem;margin-bottom:1rem;font-size:0.84rem;line-height:1.5;'
        'display:flex;gap:0.6rem;align-items:flex-start;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.18);color:#bfdbfe">'
        '<span>🔍</span>'
        '<div>Deep Scan voert een uitgebreide multi-source analyse uit en duurt doorgaans <strong>2–5 minuten</strong>.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    with st.status("Deep scan wordt uitgevoerd...", expanded=True) as status:
        st.write(f"Diepgaand onderzoek gestart voor **{full_name}** · {city_region}...")
        st.write("Uitgebreid bronnennetwerk wordt geanalyseerd...")
        result, error = run_deep_research(
            name=full_name,
            city=city_region,
            age=age,
            employer=employer,
            context=context
        )
        if error:
            status.update(label=f"Fout: {error}", state="error")
            st.stop()
        status.update(label="Deep scan afgerond.", state="complete")

    with open("audit_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "analyst": analyst_name or "unknown",
            "subject_name": full_name,
            "subject_city": city_region,
            "context": context,
            "scan_type": "deep",
            "type": "lease_person"
        }, ensure_ascii=False) + "\n")

    display_results(result, full_name, city_region, analyst_name)

# ── Company research run ───────────────────────────────────────────────────────
if company_run_btn:
    if not company_name or not company_country:
        st.error("Bedrijfsnaam en land/regio zijn verplicht.")
        st.stop()

    with st.status("Bedrijfsonderzoek wordt uitgevoerd...", expanded=True) as status:
        st.write(f"Onderzoek gestart voor **{company_name}** · {company_country}...")
        st.write("Signalen worden verzameld uit openbare bronnen...")
        company_result, company_error = run_company_research(
            company_name=company_name,
            country=company_country,
            kvk=company_kvk,
            sector=company_sector,
            context=company_context
        )
        if company_error:
            status.update(label=f"Fout: {company_error}", state="error")
            st.stop()
        status.update(label="Bedrijfsonderzoek afgerond.", state="complete")

    with open("audit_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "analyst": company_analyst or "unknown",
            "subject_name": company_name,
            "subject_city": company_country,
            "context": company_context,
            "scan_type": "company",
            "type": "lease_company"
        }, ensure_ascii=False) + "\n")

    display_company_results(company_result, company_name, company_country, company_analyst)

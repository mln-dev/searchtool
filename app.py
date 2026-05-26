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

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def clean_field(text):
    if not text: return text
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', str(text))
    s = re.sub(r'\(https?://\S+\)', '', s)
    s = re.sub(r'\([a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}\)', '', s)
    return re.sub(r'\s{2,}', ' ', s).strip()

def clean_url(url):
    if not url: return url
    return re.sub(r'[?&]utm_[^&\s)]+', '', str(url)).rstrip('?&')

st.set_page_config(page_title="LeaseCheck · Due Diligence", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.html("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],[data-testid="stMain"]{background:#fff!important;color:#1a1a2e!important;font-family:'Outfit',sans-serif!important}
[data-testid="stHeader"],#MainMenu,footer,header{display:none!important}
[data-testid="collapsedControl"],section[data-testid="stSidebar"]{display:none!important}
.block-container{padding:0!important;max-width:100%!important}
div[data-testid="stTextInput"] label,.stTextInput label{font-family:'Outfit',sans-serif!important;font-size:.72rem!important;font-weight:600!important;color:#6b7280!important;text-transform:uppercase!important;letter-spacing:.06em!important}
div[data-testid="stTextInput"] input,div[data-baseweb="input"] input{background:#f8f9fb!important;color:#1a1a2e!important;-webkit-text-fill-color:#1a1a2e!important;border:1px solid #e5e7eb!important;border-radius:8px!important;font-family:'Outfit',sans-serif!important;font-size:.88rem!important;padding:.55rem .75rem!important;transition:border-color .15s,box-shadow .15s}
div[data-testid="stTextInput"] input::placeholder,div[data-baseweb="input"] input::placeholder{color:#9ca3af!important;-webkit-text-fill-color:#9ca3af!important}
div[data-testid="stTextInput"] input:focus,div[data-baseweb="input"] input:focus{border-color:#2563eb!important;box-shadow:0 0 0 3px rgba(37,99,235,.08)!important;outline:none!important}
div[data-baseweb="input"],div[data-baseweb="base-input"],div[data-testid="stTextInput"]>div{background:#f8f9fb!important;border-color:transparent!important}
div[data-testid="stTextInput"] input:-webkit-autofill{-webkit-box-shadow:0 0 0 1000px #f8f9fb inset!important;-webkit-text-fill-color:#1a1a2e!important}
.stButton>button[kind="primary"]{background:#2563eb!important;border:none!important;border-radius:8px!important;color:#fff!important;font-family:'Outfit',sans-serif!important;font-weight:600!important;min-height:42px!important;font-size:.82rem!important;transition:all .15s!important}
.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;transform:translateY(-1px);box-shadow:0 4px 12px rgba(37,99,235,.2)!important}
.stButton>button:not([kind="primary"]){background:#fff!important;border:1px solid #e5e7eb!important;border-radius:8px!important;color:#374151!important;font-family:'Outfit',sans-serif!important;font-weight:500!important;min-height:42px!important;font-size:.82rem!important}
.stDownloadButton>button{border-radius:8px!important;border:1px solid #e5e7eb!important;background:#fff!important;color:#374151!important;font-family:'Outfit',sans-serif!important;font-weight:600!important}
.stDownloadButton>button:hover{border-color:#2563eb!important;color:#2563eb!important}
.stTabs [data-baseweb="tab-list"]{gap:0;background:#f3f4f6;border-radius:8px;padding:3px;border:none}
.stTabs [data-baseweb="tab"]{border-radius:6px!important;padding:.4rem 1rem!important;font-family:'Outfit',sans-serif!important;font-weight:500!important;font-size:.8rem!important;color:#6b7280!important;background:transparent!important;border:none!important}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1a1a2e!important;font-weight:600!important;box-shadow:0 1px 2px rgba(0,0,0,.06)!important}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none!important}
div[data-testid="stExpander"]{border:1px solid #e5e7eb!important;border-radius:10px!important;background:#fff!important;margin-bottom:.5rem!important}
div[data-testid="stExpander"] summary{font-family:'Outfit',sans-serif!important;font-weight:600!important;font-size:.84rem!important;color:#374151!important}
hr{border:none!important;border-top:1px solid #f0f0f0!important}
</style>
""")

# ── Header ───────────────────────────────────────────────────────────────────
_lp = Path(__file__).parent / "KYC_logo_official.png"
if _lp.exists():
    _lb = base64.b64encode(_lp.read_bytes()).decode()
    logo = f'<img src="data:image/png;base64,{_lb}" style="height:32px;width:auto" />'
else:
    logo = '<div style="display:flex;align-items:center;gap:8px"><div style="width:30px;height:30px;background:#2563eb;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.85rem">LC</div><span style="font-weight:700;font-size:1rem;color:#1a1a2e">LeaseCheck</span></div>'

st.markdown(f'<div style="display:flex;align-items:center;justify-content:space-between;padding:.9rem 2rem;border-bottom:1px solid #f0f0f0">{logo}<div style="display:flex;align-items:center;gap:16px"><span style="font-size:.72rem;color:#9ca3af;font-weight:500;text-transform:uppercase;letter-spacing:.08em">Due Diligence Platform</span><div style="display:flex;align-items:center;gap:5px;color:#10b981;font-size:.75rem;font-weight:500"><div style="width:6px;height:6px;border-radius:50%;background:#10b981"></div>Online</div></div></div>', unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_person, tab_company = st.tabs(["👤  Persoon", "🏢  Bedrijf"])

# ── Micro-helpers ────────────────────────────────────────────────────────────
def _lbl(t): return f'<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#9ca3af;margin:0 0 .6rem 0">{t}</div>'
def _hr(): return '<div style="height:1px;background:#f0f0f0;margin:1rem 0"></div>'
def _empty(t="Geen gegevens"): return f'<div style="color:#9ca3af;font-size:.82rem;font-style:italic;padding:.4rem 0">{t}</div>'
def _row(title, sub="", url=""):
    h = f'<div style="padding:.5rem 0;border-bottom:1px solid #f5f5f5"><div style="font-weight:600;color:#1a1a2e;font-size:.84rem">{title}</div>'
    if sub: h += f'<div style="color:#6b7280;font-size:.76rem;margin-top:1px;line-height:1.5">{sub}</div>'
    if url: h += f'<div style="color:#2563eb;font-size:.7rem;margin-top:2px;word-break:break-all;font-family:IBM Plex Mono,monospace">{clean_field(url)}</div>'
    return h + '</div>'

def _sources(sources):
    if not sources: return _empty("Geen bronnen.")
    r = ""
    for s in sources:
        u = clean_url(s.get("url","#")); n = clean_field(s.get("name",u)); t = clean_field(s.get("type","web"))
        r += f'<div style="display:flex;align-items:center;gap:.6rem;padding:.45rem 0;border-bottom:1px solid #f5f5f5"><div style="flex:1;min-width:0"><a href="{u}" target="_blank" style="color:#2563eb;font-weight:600;font-size:.82rem;text-decoration:none">{n}</a><div style="color:#9ca3af;font-size:.68rem;word-break:break-all;font-family:IBM Plex Mono,monospace;margin-top:1px">{u}</div></div><span style="flex-shrink:0;background:#f0f4ff;color:#2563eb;border-radius:4px;padding:2px 6px;font-size:.65rem;font-weight:600">{t}</span></div>'
    return r

def _items(items, tk, sks=None, uk=None):
    if not items: return _empty("Onvoldoende gegevens")
    sks = sks or []
    return "".join(_row(clean_field(i.get(tk,"—")), " · ".join(clean_field(i.get(k,"")) for k in sks if i.get(k)), i.get(uk,"") if uk else "") for i in items)

def _vc(s):
    if s >= 80: return "#10b981"
    if s >= 55: return "#f59e0b"
    return "#ef4444"
def _vb(s):
    if s >= 80: return "#f0fdf4"
    if s >= 55: return "#fffbeb"
    return "#fef2f2"

def _flags(flags):
    if not flags: return '<div style="display:flex;align-items:center;gap:6px;color:#10b981;font-weight:600;font-size:.84rem;padding:.6rem 0">✓ Geen risicovlaggen geïdentificeerd.</div>'
    h = ""
    for f in flags:
        sv = (f.get("severity") or "low").lower()
        bg, bc, hc = (("#fef2f2","#fecaca","#ef4444") if sv=="high" else ("#fffbeb","#fde68a","#f59e0b") if sv=="medium" else ("#f0fdf4","#bbf7d0","#10b981"))
        ic = "⛔" if sv=="high" else "⚠️" if sv=="medium" else "ℹ️"
        h += f'<div style="background:{bg};border:1px solid {bc};border-radius:8px;padding:.6rem .8rem;margin-bottom:.4rem"><div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#374151;margin-bottom:2px">{ic} {sv.upper()} — {clean_field(f.get("category",""))}</div><div style="font-size:.8rem;color:#4b5563;line-height:1.5">{clean_field(f.get("description",""))}</div></div>'
    return h

# ── Person results ───────────────────────────────────────────────────────────
def show_person(result, name, city, analyst):
    sc = int(result.get("confidence_score",0)); vd = result.get("confidence_verdict","Low"); rs = clean_field(result.get("confidence_reasoning","")); co = _vc(sc); bg = _vb(sc)
    st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.4rem"><div style="font-size:1.4rem;font-weight:700;color:#1a1a2e;letter-spacing:-.02em">{name} <span style="color:#d1d5db">·</span> {city}</div><div style="color:#9ca3af;font-size:.72rem">{datetime.now().strftime("%d %b %Y %H:%M")} · {analyst or "—"}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:{bg};border:1px solid #e5e7eb;border-radius:12px;padding:1rem 1.2rem;display:flex;align-items:center;gap:1.2rem;margin:.6rem 0 1rem"><div style="text-align:center"><div style="font-size:2.6rem;font-weight:700;line-height:1;color:{co}">{sc}</div><div style="font-size:.62rem;color:#6b7280;text-transform:uppercase;letter-spacing:.06em;font-weight:600;margin-top:2px">/ 100</div></div><div style="flex:1"><div style="font-size:.9rem;font-weight:700;color:{co};margin-bottom:2px">{vd}</div><div style="font-size:.78rem;color:#6b7280;line-height:1.45">{rs}</div><div style="background:#e5e7eb;border-radius:99px;height:4px;margin-top:8px;overflow:hidden"><div style="height:100%;border-radius:99px;width:{sc}%;background:{co}"></div></div></div></div>', unsafe_allow_html=True)
    vs = result.get("name_variations_searched",[])
    if vs:
        chips = "".join(f'<span style="display:inline-block;background:#f0f4ff;color:#2563eb;border-radius:4px;padding:2px 7px;font-size:.7rem;margin:2px 3px 2px 0;font-weight:500;font-family:IBM Plex Mono,monospace">{v}</span>' for v in vs)
        st.markdown(f'{_lbl("Gezochte variaties")}{chips}', unsafe_allow_html=True)
    st.markdown(f'{_hr()}{_lbl("Risicovlaggen")}{_flags(result.get("risk_flags",[]))}', unsafe_allow_html=True)
    st.markdown(_hr(), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("Identiteit", icon=":material/fingerprint:"): st.markdown(_items(result.get("identity_matches",[]),"name",["description","confidence"]), unsafe_allow_html=True)
        with st.expander("Professioneel", icon=":material/work:"): st.markdown(_items(result.get("professional_profiles",[]),"role",["company","platform"],"url_hint"), unsafe_allow_html=True)
        with st.expander("Bedrijfsregistraties", icon=":material/business_center:"): st.markdown(_items(result.get("business_records",[]),"entity",["role","status"],"source"), unsafe_allow_html=True)
    with c2:
        with st.expander("Media", icon=":material/newspaper:"):
            mm = result.get("media_mentions",[])
            if mm: st.markdown("".join(_row(f'{"🟢" if (m.get("sentiment") or "").lower()=="positive" else "🔴" if (m.get("sentiment") or "").lower()=="negative" else "⚪"} {clean_field(m.get("title","—"))}', f'{clean_field(m.get("source",""))} · {clean_field(m.get("date",""))} · {clean_field(m.get("summary",""))}') for m in mm), unsafe_allow_html=True)
            else: st.markdown(_empty(), unsafe_allow_html=True)
        with st.expander("Social Media", icon=":material/public:"): st.markdown(_items(result.get("social_media_presence",[]),"platform",["description"]), unsafe_allow_html=True)
        with st.expander("Juridisch", icon=":material/gavel:"): st.markdown(_items(result.get("legal_public_records",[]),"issue_type",["date","summary"],"source"), unsafe_allow_html=True)
    with st.expander("Bronnen", icon=":material/link:"): st.markdown(_sources(result.get("sources",[])), unsafe_allow_html=True)
    st.divider()
    try:
        pdf = generate_pdf(result, name, city, analyst)
        st.download_button("⬇️  Download PDF", data=pdf, file_name=f"lease_{name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf", use_container_width=True)
    except Exception as e: st.warning(f"PDF mislukt: {e}")

# ── Company results ──────────────────────────────────────────────────────────
def show_company(result, cname, country, analyst):
    pr = result.get("company_profile",{}); nm = clean_field(pr.get("name",cname)); sc = clean_field(pr.get("sector")); lg = clean_field(pr.get("legal_form")); sub = " · ".join(v for v in [sc,lg] if v)
    st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.2rem"><div><div style="font-size:1.4rem;font-weight:700;color:#1a1a2e">{nm}</div>{"<div style=color:#6b7280;font-size:.85rem;margin-top:2px>"+sub+"</div>" if sub else ""}</div><div style="color:#9ca3af;font-size:.72rem">{datetime.now().strftime("%d %b %Y %H:%M")} · {analyst or "—"}</div></div>', unsafe_allow_html=True)
    st.markdown(_hr(), unsafe_allow_html=True)
    ds = result.get("directors_shareholders",[]); mgr = clean_field(ds[0].get("name")) if ds else "—"
    flds = [("Vestigingsadres",clean_field(pr.get("address")) or "—"),("Rechtsvorm",clean_field(pr.get("legal_form")) or "—"),("Sector",clean_field(pr.get("sector")) or "—"),("KvK-nummer",clean_field(pr.get("kvk_number")) or "—"),("Directeur",mgr),("Medewerkers",clean_field(pr.get("size")) or "—")]
    rh = "".join(f'<div style="display:flex;justify-content:space-between;padding:.35rem 0;border-bottom:1px solid #ecfdf5"><span style="color:#059669;font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.04em">{l}</span><span style="color:#1a1a2e;font-size:.82rem;text-align:right">{v}</span></div>' for l,v in flds)
    st.markdown(f'<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:.8rem 1rem;margin-bottom:1rem"><div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#059669;margin-bottom:.5rem">Lease Due Diligence · Bedrijfsoverzicht</div>{rh}</div>', unsafe_allow_html=True)
    st.markdown(f'{_lbl("Risicovlaggen")}{_flags(result.get("risk_flags",[]))}', unsafe_allow_html=True)
    st.markdown(_hr(), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("Profiel", icon=":material/business:"):
            pf = [("Opgericht",pr.get("founded")),("Rechtsvorm",pr.get("legal_form")),("Omvang",pr.get("size")),("KvK",pr.get("kvk_number")),("Adres",pr.get("address")),("Website",pr.get("website"))]
            ph = "".join(_row(clean_field(v),l) for l,v in pf if clean_field(v))
            d = clean_field(pr.get("description")); ph += f'<div style="color:#6b7280;font-size:.82rem;padding:.5rem 0;line-height:1.5">{d}</div>' if d else ""
            st.markdown(ph or _empty(), unsafe_allow_html=True)
        with st.expander("Bestuurders", icon=":material/group:"):
            it = result.get("directors_shareholders",[])
            st.markdown("".join(_row(clean_field(p.get("name","—")),f'{clean_field(p.get("role",""))} · Sinds {clean_field(p.get("since","—"))}') for p in it) if it else _empty(), unsafe_allow_html=True)
        with st.expander("Financiën", icon=":material/bar_chart:"):
            it = result.get("financials",[])
            st.markdown("".join(_row(clean_field(f.get("year","—")),f'Omzet: {clean_field(f.get("revenue","—"))} · Winst: {clean_field(f.get("profit","—"))}',clean_field(f.get("source",""))) for f in it) if it else _empty(), unsafe_allow_html=True)
    with c2:
        with st.expander("Groepsstructuur", icon=":material/account_tree:"):
            it = result.get("group_structure",[])
            st.markdown("".join(_row(clean_field(g.get("entity","—")),f'{clean_field(g.get("relationship",""))} · {clean_field(g.get("country",""))}') for g in it) if it else _empty(), unsafe_allow_html=True)
        with st.expander("Sleutelpersonen", icon=":material/badge:"):
            it = result.get("key_people",[])
            st.markdown("".join(_row(clean_field(k.get("name","—")),clean_field(k.get("role",""))) for k in it) if it else _empty(), unsafe_allow_html=True)
        with st.expander("Nieuws", icon=":material/newspaper:"):
            it = result.get("news_media",[])
            st.markdown("".join(_row(clean_field(m.get("title","—")),f'{clean_field(m.get("source",""))} · {clean_field(m.get("date",""))}',m.get("url","")) for m in it) if it else _empty(), unsafe_allow_html=True)
    with st.expander("Bronnen", icon=":material/link:"): st.markdown(_sources(result.get("sources",[])), unsafe_allow_html=True)
    st.divider()
    try:
        pdf = generate_company_pdf(result, pr.get("name",cname), country, analyst)
        st.download_button("⬇️  Download PDF", data=pdf, file_name=f"lease_bedrijf_{cname.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf", use_container_width=True)
    except Exception as e: st.warning(f"PDF mislukt: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PERSON TAB — 1/3 left  |  2/3 right
# ══════════════════════════════════════════════════════════════════════════════
with tab_person:
    left, right = st.columns([1, 2], gap="large")
    with left:
        st.markdown('<div style="background:#f8f9fb;border:1px solid #e5e7eb;border-radius:12px;padding:1rem 1.2rem;margin-top:.5rem"><div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#9ca3af;margin-bottom:.8rem">Gegevens aanvrager</div></div>', unsafe_allow_html=True)
        pn = st.text_input("Volledige naam *", placeholder="Jan de Vries", key="pn")
        pc = st.text_input("Woonplaats *", placeholder="Amsterdam", key="pc")
        px = st.text_input("Context", placeholder="Lease · Volvo XC60 · €650/mnd", key="px")
        pa = st.text_input("Geboortedatum", placeholder="15-03-1985", key="pa")
        pe = st.text_input("Werkgever", placeholder="Deloitte", key="pe")
        py = st.text_input("Analist", placeholder="Uw naam", key="py")
        st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
        rb = st.button("▶  Start Screening", type="primary", use_container_width=True, key="rb")
        db = st.button("🔍  Deep Scan", use_container_width=True, key="db")
        st.markdown('<div style="margin-top:1rem;padding:.6rem .8rem;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;font-size:.74rem;color:#92400e;line-height:1.5">⚠️ <strong>AVG/GDPR</strong> — Uitsluitend voor legitieme compliance bij leaseaanvragen.</div>', unsafe_allow_html=True)
    with right:
        if rb:
            if not pn or not pc: st.error("Naam en woonplaats verplicht."); st.stop()
            with st.status("Screening...", expanded=True) as s:
                st.write(f"**{pn}** · {pc}"); r, e = run_research(name=pn, city=pc, age=pa, employer=pe, context=px)
                if e: s.update(label=f"Fout: {e}", state="error"); st.stop()
                s.update(label="Klaar.", state="complete")
            with open("audit_log.jsonl","a",encoding="utf-8") as f: f.write(json.dumps({"timestamp":datetime.now().isoformat(),"analyst":py or "?","name":pn,"city":pc,"ctx":px,"type":"lease_person"},ensure_ascii=False)+"\n")
            show_person(r, pn, pc, py)
        elif db:
            if not pn or not pc: st.error("Naam en woonplaats verplicht."); st.stop()
            st.markdown('<div style="padding:.6rem .8rem;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;font-size:.78rem;color:#1e40af;margin-bottom:.8rem">🔍 Deep Scan duurt <strong>2–5 min</strong>.</div>', unsafe_allow_html=True)
            with st.status("Deep scan...", expanded=True) as s:
                st.write(f"**{pn}** · {pc}"); r, e = run_deep_research(name=pn, city=pc, age=pa, employer=pe, context=px)
                if e: s.update(label=f"Fout: {e}", state="error"); st.stop()
                s.update(label="Klaar.", state="complete")
            with open("audit_log.jsonl","a",encoding="utf-8") as f: f.write(json.dumps({"timestamp":datetime.now().isoformat(),"analyst":py or "?","name":pn,"city":pc,"ctx":px,"scan":"deep","type":"lease_person"},ensure_ascii=False)+"\n")
            show_person(r, pn, pc, py)
        else:
            st.markdown('<div style="display:flex;align-items:center;justify-content:center;min-height:400px;flex-direction:column;gap:.8rem"><div style="font-size:2.5rem;opacity:.12">🔍</div><div style="font-size:.9rem;color:#9ca3af;font-weight:500">Vul de gegevens in en start een screening</div><div style="font-size:.78rem;color:#d1d5db">Resultaten verschijnen hier</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COMPANY TAB — 1/3 left  |  2/3 right
# ══════════════════════════════════════════════════════════════════════════════
with tab_company:
    lc, rc = st.columns([1, 2], gap="large")
    with lc:
        st.markdown('<div style="background:#f8f9fb;border:1px solid #e5e7eb;border-radius:12px;padding:1rem 1.2rem;margin-top:.5rem"><div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#9ca3af;margin-bottom:.8rem">Bedrijfsgegevens</div></div>', unsafe_allow_html=True)
        cn = st.text_input("Bedrijfsnaam *", placeholder="Pon Holdings B.V.", key="cn")
        cc = st.text_input("Land / Regio *", placeholder="Nederland", key="cc")
        cx = st.text_input("Context", placeholder="Wagenpark · 250 voertuigen", key="cx")
        ck = st.text_input("KvK-nummer", placeholder="27532543", key="ck")
        cs = st.text_input("Sector", placeholder="Automotive · Leasing", key="cs")
        ca = st.text_input("Analist", placeholder="Uw naam", key="ca")
        st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
        cb = st.button("▶  Onderzoek Bedrijf", type="primary", use_container_width=True, key="cb")
        st.markdown('<div style="margin-top:1rem;padding:.6rem .8rem;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;font-size:.74rem;color:#92400e;line-height:1.5">⚠️ <strong>AVG/GDPR</strong> — Uitsluitend voor legitieme compliance bij leaseaanvragen.</div>', unsafe_allow_html=True)
    with rc:
        if cb:
            if not cn or not cc: st.error("Bedrijfsnaam en land verplicht."); st.stop()
            with st.status("Bedrijfsonderzoek...", expanded=True) as s:
                st.write(f"**{cn}** · {cc}"); cr, ce = run_company_research(company_name=cn, country=cc, kvk=ck, sector=cs, context=cx)
                if ce: s.update(label=f"Fout: {ce}", state="error"); st.stop()
                s.update(label="Klaar.", state="complete")
            with open("audit_log.jsonl","a",encoding="utf-8") as f: f.write(json.dumps({"timestamp":datetime.now().isoformat(),"analyst":ca or "?","name":cn,"country":cc,"ctx":cx,"type":"lease_company"},ensure_ascii=False)+"\n")
            show_company(cr, cn, cc, ca)
        else:
            st.markdown('<div style="display:flex;align-items:center;justify-content:center;min-height:400px;flex-direction:column;gap:.8rem"><div style="font-size:2.5rem;opacity:.12">🏢</div><div style="font-size:.9rem;color:#9ca3af;font-weight:500">Vul de bedrijfsgegevens in en start het onderzoek</div><div style="font-size:.78rem;color:#d1d5db">Resultaten verschijnen hier</div></div>', unsafe_allow_html=True)


# investidata_pro.py
import io, re, math
from datetime import datetime
import pandas as pd
import streamlit as st
import altair as alt

# ============== CONFIG ==============
st.set_page_config(page_title="InvestiData – Panel Forense", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

KEYWORDS = {
    "Drogas/Sustancias": ["droga","cocaína","marihuana","pasto","blanca","cristal","tusi","pepa","keta","gramo"],
    "Armas/Violencia": ["arma","pistola","fierro","bala","munición","calibre","cañón","muerto","matar","plomo"],
    "Delitos Graves": ["secuestro","extorsión","plata","pago","rescate","vuelta"]
}
APPS_SOSPECHOSAS = ["vpn","proxy","hack","spy","tor","dark","sniff","keylogger"]

# ============== ESTILOS ==============
st.markdown("""
<style>
.kpi {background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px}
.kpi .t {font-size:13px;color:#334155;font-weight:700}
.kpi .v {font-size:28px;font-weight:900;color:#0f172a}
.kpi .s {font-size:12px;color:#64748b}
.grid4 {display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.grid3 {display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.card {background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px}
.label {font-size:12px;color:#64748b;font-weight:700}
.value {font-size:14px;color:#0f172a}
</style>
""", unsafe_allow_html=True)

# ============== UTILIDADES ==============
def list_sheets(file_bytes: bytes):
    return pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl").sheet_names

def read_sheet(file_bytes: bytes, sheet_name: str):
    xls = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
    return xls.parse(sheet_name)

def normalize_sheets(names):
    lower = {n.lower(): n for n in names}
    def find(keys):
        for k in keys:
            for low, real in lower.items():
                if k in low: return real
        return None
    return {
        "device": find(["resumen","summary","device","dispositivo","info"]),
        "accounts": find(["cuenta","account","perfil","usuario","profile"]),
        "messages": find(["message","mensaje","sms","chat","whatsapp","im","comunic","communications"]),
        "locations": find(["gps","location","ubicac","coordenada","map"]),
        "apps": find(["app","aplicac","installed","application","apk"]),
    }

def extract_device(df: pd.DataFrame):
    out = {"IMEI":"", "Marca":"", "Modelo":"", "Usuario":""}
    cols = [c.lower() for c in df.columns]
    def get(term_list):
        for t in term_list:
            for i,c in enumerate(cols):
                if t in c:
                    val = str(df.iloc[0, i]) if len(df) else ""
                    if val and val.lower()!="nan": return val
        return ""
    out["IMEI"]   = get(["imei"]) or re.search(r"\b\d{15}\b", " ".join(df.astype(str).values.flatten())) and re.search(r"\b\d{15}\b", " ".join(df.astype(str).values.flatten())).group(0) or ""
    out["Marca"]  = get(["brand","marca","fabricante"])
    out["Modelo"] = get(["model","modelo","device"])
    out["Usuario"]= get(["user","usuario","owner","nombre"])
    return out

def extract_accounts(df: pd.DataFrame):
    emails, phones, fb, ig = set(), set(), set(), set()
    for _, row in df.iterrows():
        txt = " ".join([str(x) for x in row.values])
        emails.update(re.findall(r"\b[\w.-]+@[\w.-]+\.[a-z]{2,}\b", txt, flags=re.IGNORECASE))
        phones.update(re.findall(r"(\+\d{1,3}[\s-]?\d{2,4}[\s-]?\d{3}[\s-]?\d{3,4})", txt))
        fb.update(re.findall(r"(?:facebook\.com/|fb\s*[:@]\s*)([A-Za-z0-9._-]{3,})", txt, flags=re.IGNORECASE))
        ig.update(re.findall(r"(?:instagram\.com/|ig\s*[:@]\s*|@)([A-Za-z0-9._-]{3,})", txt, flags=re.IGNORECASE))
    def first(s): return next(iter(s), "")
    return {"Correo": first(emails), "WhatsApp": first(phones), "Facebook": first(fb), "Instagram": first(ig)}

def find_cols(df, spec):
    lowers = [c.lower() for c in df.columns]
    res = {}
    for key, keys in spec.items():
        for k in keys:
            if k in lowers:
                res[key] = df.columns[lowers.index(k)]
                break
            # substring match
            cand = [i for i,low in enumerate(lowers) if k in low]
            if cand:
                res[key] = df.columns[cand[0]]
                break
    return res

def message_kpis(df):
    cmap = find_cols(df, {
        "date": ["date","fecha","time","hora","timestamp"],
        "body": ["body","mensaje","text","content","contenido"],
        "from": ["from","de","remitente","sender"],
        "to":   ["to","para","destinatario","receiver"]
    })
    total = len(df); hits = 0; suspicious_contacts = 0
    if "body" in cmap:
        pattern = "|".join([re.escape(w) for w in sum(KEYWORDS.values(), [])])
        mask = df[cmap["body"]].astype(str).str.contains(pattern, case=False, na=False)
        hits = int(mask.sum())
        # interlocutor si hay from/to
        if "from" in cmap and "to" in cmap:
            # suposición: el ID más frecuente en "from" es el dispositivo
            me = df[cmap["from"]].astype(str).value_counts().idxmax() if total else None
            inter = df.apply(lambda r: r[cmap["to"]] if me and str(r[cmap["from"]])==str(me) else r[cmap["from"]], axis=1)
            suspicious_contacts = inter[mask].astype(str).nunique()
    pct = (hits/total*100) if total else 0.0
    # horas pico (si hay tiempo)
    heat = None
    if "date" in cmap:
        ts = pd.to_datetime(df[cmap["date"]], errors="coerce")
        df_heat = pd.DataFrame({"dow": ts.dt.day_name(), "hour": ts.dt.hour}).dropna()
        heat = df_heat.value_counts().reset_index(name="count")
    return total, hits, pct, suspicious_contacts, heat

def nocturnal_patterns(df, date_col):
    ts = pd.to_datetime(df[date_col], errors="coerce")
    return int(((ts.dt.hour >= 0) & (ts.dt.hour < 6)).sum())

def apps_alerts(df):
    text_cols = [c for c in df.columns if any(t in c.lower() for t in ["name","apk","archivo","ruta","path","package"])]
    if not text_cols: return 0, 0.0

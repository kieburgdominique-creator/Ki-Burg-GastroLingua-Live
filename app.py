import streamlit as st
import sqlite3
import json
import requests
import os
import hashlib
import re
import secrets
from datetime import datetime, date

# ==============================================================================
# 1. PAGE CONFIG & B2B DESIGN SYSTEM
# ==============================================================================
st.set_page_config(
    page_title="KI-BURG GastroLingua Plattform | Mehrsprachige KI-Bestell- und Logistikplattform",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource(show_spinner=False)
def get_whisper_model(model_size="base"):
    """Load the local Whisper model once and reuse it across Streamlit reruns."""
    from faster_whisper import WhisperModel
    return WhisperModel(model_size, device="cpu", compute_type="int8")

st.markdown("## KI-BURG GastroLingua Plattform")
st.caption("Die mehrsprachige KI-Bestell- und Logistikplattform für die Gastronomie")


st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #8C4A32 100%);
        color: white;
        padding: 1.2rem 1.8rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    [data-testid="stImage"] img { object-fit: cover; border-radius: 10px; max-height: 150px; }
    .sticky-cart-anchor { position: sticky; top: 0; }
    .product-card-idle {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .product-card-added {
        background-color: #DCFCE7 !important;
        border: 2px solid #16A34A !important;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .cart-badge {
        background-color: #16A34A;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 0.4rem;
    }
    .order-card-idle {
        background-color: #FFFFFF;
        border: 2px solid #CBD5E1;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .order-card-active {
        background-color: #FEF3C7;
        border: 3px solid #D97706;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.25);
    }
    .active-badge {
        background-color: #D97706;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 0.8rem;
    }
    .done-badge {
        background-color: #DCFCE7;
        border: 2px solid #16A34A;
        color: #15803D;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .firewall-locked {
        background-color: #DCFCE7;
        border: 2px solid #16A34A;
        color: #15803D;
        padding: 1rem;
        border-radius: 8px;
        font-weight: bold;
    }
    .alert-card {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 6px;
    }
    .out-of-stock-card {
        background-color: #FFFBEB;
        border: 1px solid #FCD34D;
        padding: 0.8rem;
        border-radius: 6px;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .raw-box {
        background-color: #F8FAFC;
        border-left: 4px solid #0EA5E9;
        padding: 0.8rem;
        margin-top: 0.5rem;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


# Responsive GastroLingua UI refresh
st.markdown("""
<style>
:root { --gl-navy:#102b43; --gl-teal:#13a99a; --gl-bg:#f4f7f9; --gl-ink:#1d3343; }
.stApp { background:var(--gl-bg); color:var(--gl-ink); }
[data-testid="stSidebar"] { background:var(--gl-navy); }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] summary { color:#f3f8fb !important; }
[data-testid="stSidebar"] button, [data-testid="stSidebar"] button *, [data-testid="stSidebar"] [data-baseweb="select"] *, [data-testid="stSidebar"] [data-testid="stAlert"] *, [data-testid="stSidebar"] code { color:var(--gl-navy) !important; }
[data-testid="stSidebar"] label { color:#e1edf2 !important; font-weight:600; }
.block-container { max-width:1500px; padding-top:3rem !important; padding-bottom:7rem; }
/* Fix: prevent the page title/banner from sitting underneath Streamlit top chrome. */
[data-testid="stAppViewContainer"] .main .block-container { padding-top:3rem !important; }
[data-testid="stHeader"] { height:2.8rem; }
h1,h2,h3 { color:var(--gl-navy); letter-spacing:-.02em; }
.main-header { background:linear-gradient(120deg,#102b43 0%,#17475c 72%,#128b82 100%) !important; border-radius:16px !important; padding:1.3rem 1.5rem !important; box-shadow:0 8px 24px #102b4314; }
[data-testid="stImage"] { margin-bottom: .35rem; }
[data-testid="stImage"] img { border-radius:12px; object-fit:cover; }
.product-card-idle,.order-card-idle { background:#fff; border:1px solid #dce6eb; border-radius:14px; padding:1rem; margin:.4rem 0 1rem 0; box-shadow:0 3px 12px #102b4308; }
.product-card-added { background:#e3f8f3 !important; border:1px solid #13a99a !important; border-radius:14px; padding:1rem; }
.raw-box { background:#eaf8f5 !important; border-left:4px solid #13a99a !important; border-radius:10px; padding:1rem; }
.out-of-stock-card { background:#fff7e5 !important; border:1px solid #f4d58a !important; border-radius:10px; padding:.75rem; }
.cart-badge { background:#d9f7ef !important; color:#08786e !important; border-radius:99px; padding:.25rem .6rem; font-weight:700; }
.stButton > button,[data-testid="stFormSubmitButton"] button { min-height:2.7rem; border-radius:10px; font-weight:650; border:1px solid #d7e3e8; }
.stButton > button[kind="primary"] { background:#0d9f93; border-color:#0d9f93; color:white; }
[data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid #dce6ea; }
[data-baseweb="tab"] { background:#eaf0f3; border-radius:9px 9px 0 0; padding:9px 14px; }
[data-baseweb="tab"][aria-selected="true"] { background:#dff8f3; color:#087d73; font-weight:700; }
[data-baseweb="radio"] { background:#fff; border:1px solid #dce6eb; border-radius:999px; padding:.35rem .7rem; margin:.15rem; }
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-baseweb="select"] > div { border-radius:9px !important; min-height:2.6rem; }
[data-testid="stMetric"] { background:white; border:1px solid #e1e8eb; border-radius:12px; padding:14px; }

/* Accessibility fix: keep controls readable even when browser/theme overrides styles */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-baseweb="select"] input,
[data-baseweb="select"] > div,
[data-baseweb="popover"] *,
[role="listbox"] *,
[role="option"],
[data-testid="stSelectbox"] *,
[data-testid="stMultiSelect"] * {
  color: #173247 !important;
}
[data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
  background-color: #ffffff !important;
}
[data-baseweb="popover"], [role="listbox"] {
  background-color: #ffffff !important;
}
[role="option"]:hover, [role="option"][aria-selected="true"] {
  background-color: #dff8f3 !important;
  color: #102b43 !important;
}
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label {
  color: #173247 !important;
}

@media (max-width: 700px) {
  .block-container { padding-left:.8rem; padding-right:.8rem; padding-top:1.5rem !important; }
  [data-testid="stHorizontalBlock"] { gap:.5rem; }
  [data-testid="stSidebar"] { min-width:0; }
  .main-header { padding:1rem !important; }
  .main-header h2 { font-size:1.35rem !important; }
  .stButton > button { width:100%; min-height:2.9rem; }
  [data-baseweb="radio"] { border-radius:12px; }
}
.task-customer { font-size:1.65rem; font-weight:850; line-height:1.2; margin:.15rem 0 .55rem 0; color:#12344a; }
.task-meta { font-size:.95rem; color:#536575; margin-bottom:.35rem; }

/* Picker workspace */
.picking-hero { background:linear-gradient(120deg,#102b43 0%,#17475c 72%,#128b82 100%); color:#fff; border-radius:16px; padding:1.2rem 1.4rem; margin:.5rem 0 1.1rem 0; box-shadow:0 8px 22px #102b4318; }
.picking-hero h3 { color:#fff !important; margin:0 0 .3rem 0; }
.picking-hero p { color:#eaf6f8 !important; margin:0; }
.pick-order { background:#fff; border:1px solid #d9e5ea; border-left:6px solid #94a3b8; border-radius:14px; padding:1rem 1.15rem; margin:.8rem 0; box-shadow:0 3px 12px #102b4308; }
.pick-order.active { border-left-color:#d97706; background:#fffbeb; }
.pick-order.done { border-left-color:#16a34a; background:#f0fdf4; }
.pick-step { display:inline-block; padding:.25rem .65rem; border-radius:999px; background:#eaf0f3; color:#173247; font-weight:750; font-size:.82rem; margin-bottom:.45rem; }
.pick-step.active { background:#fef3c7; color:#92400e; }
.pick-step.done { background:#dcfce7; color:#166534; }
.picking-tip { border-radius:10px; background:#eaf8f5; border:1px solid #bde9df; padding:.75rem 1rem; margin:.5rem 0 1rem 0; color:#164e49; }

@media (max-width: 700px) {
  .task-customer { font-size:1.35rem; }
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SQLITE DATABASE ENGINE
# ==============================================================================
def return_reason_german(reason):
    """Normalize driver return reasons from DE/RO/SR to German for ramp and inside-sales users."""
    mapping = {
        "Problemă de calitate / ofilit": "Qualitätsmangel / welk",
        "Nedostatak kvaliteta / uvelo": "Qualitätsmangel / welk",
        "Livrare greșită": "Falschlieferung", "Pogrešna isporuka": "Falschlieferung",
        "Deteriorare la transport": "Transportschaden", "Oštećenje u transportu": "Transportschaden",
        "Termen de valabilitate prea scurt": "MHD zu kurz", "Prekratak rok trajanja": "MHD zu kurz",
    }
    return mapping.get(str(reason or ""), str(reason or "Nicht angegeben"))

OFFLINE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kiburg_offline_local.db")
def archive_demo_tasks(conn):
    conn.execute("UPDATE return_cases SET archived=1 WHERE COALESCE(archived,0)=0")
    conn.execute("UPDATE driver_alerts SET archived=1 WHERE COALESCE(archived,0)=0")

def init_offline_db():
    conn = sqlite3.connect(OFFLINE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS driver_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT,
                    customer_name TEXT,
                    category TEXT,
                    alert_text TEXT,
                    timestamp TEXT,
                    status TEXT,
                    translated_text TEXT DEFAULT '',
                    task_status TEXT DEFAULT 'NEU',
                    priority TEXT DEFAULT 'NORMAL',
                    appointment TEXT DEFAULT '',
                    sales_notes TEXT DEFAULT '',
                    assigned_to TEXT DEFAULT 'Dominique Kieburg (Außendienst)'
                )''')
    columns = {row[1] for row in c.execute("PRAGMA table_info(driver_alerts)").fetchall()}
    if "translated_text" not in columns:
        c.execute("ALTER TABLE driver_alerts ADD COLUMN translated_text TEXT DEFAULT ''")
    for _col, _definition in {
        "task_status": "TEXT DEFAULT 'NEU'",
        "priority": "TEXT DEFAULT 'NORMAL'",
        "appointment": "TEXT DEFAULT ''",
        "sales_notes": "TEXT DEFAULT ''",
        "assigned_to": "TEXT DEFAULT 'Dominique Kieburg (Außendienst)'",
        "archived": "INTEGER DEFAULT 0",
    }.items():
        if _col not in columns:
            c.execute(f"ALTER TABLE driver_alerts ADD COLUMN {_col} {_definition}")
    # One-time cleanup for the new release: hide legacy/demo feedback already present.
    # Newly submitted driver feedback remains visible and is not archived on reruns.
    c.execute("CREATE TABLE IF NOT EXISTS app_migrations (migration_key TEXT PRIMARY KEY, applied_at TEXT)")
    _legacy_cleanup_key = "v30_6_archive_existing_driver_alerts"
    _migration_done = c.execute("SELECT 1 FROM app_migrations WHERE migration_key=?", (_legacy_cleanup_key,)).fetchone()
    if not _migration_done:
        c.execute("UPDATE driver_alerts SET archived=1 WHERE COALESCE(archived,0)=0")
        c.execute("INSERT OR IGNORE INTO app_migrations (migration_key, applied_at) VALUES (?,?)", (_legacy_cleanup_key, datetime.now().isoformat(timespec="seconds")))
    c.execute("""CREATE TABLE IF NOT EXISTS return_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT, case_key TEXT UNIQUE, deal_id TEXT,
        customer_name TEXT, item_name TEXT, sku TEXT, quantity INTEGER DEFAULT 1,
        delivery_date TEXT, driver_reason TEXT, goods_condition TEXT DEFAULT '',
        credit_decision TEXT DEFAULT 'KLÄRUNG ERFORDERLICH', status TEXT DEFAULT 'NEU',
        sales_action TEXT DEFAULT '', sales_notes TEXT DEFAULT '', created_at TEXT, updated_at TEXT, archived INTEGER DEFAULT 0
    )""")
    # Schema migration: CREATE TABLE IF NOT EXISTS does not add columns to older databases.
    _return_columns = {row[1] for row in c.execute("PRAGMA table_info(return_cases)").fetchall()}
    _return_migrations = {
        "case_key": "TEXT", "deal_id": "TEXT", "customer_name": "TEXT", "item_name": "TEXT",
        "sku": "TEXT", "quantity": "INTEGER DEFAULT 1", "delivery_date": "TEXT",
        "driver_reason": "TEXT", "goods_condition": "TEXT DEFAULT ''",
        "credit_decision": "TEXT DEFAULT 'KLÄRUNG ERFORDERLICH'", "status": "TEXT DEFAULT 'NEU'",
        "sales_action": "TEXT DEFAULT ''", "sales_notes": "TEXT DEFAULT ''",
        "created_at": "TEXT", "updated_at": "TEXT", "archived": "INTEGER DEFAULT 0"
    }
    for _column, _definition in _return_migrations.items():
        if _column not in _return_columns:
            c.execute(f"ALTER TABLE return_cases ADD COLUMN {_column} {_definition}")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_return_cases_case_key ON return_cases(case_key)")
    # Archive demo records once per source revision, not on Streamlit reruns.
    with open(__file__, "rb") as source_file:
        source_revision = hashlib.sha256(source_file.read()).hexdigest()
    cleanup_key = f"demo_archive:{source_revision}"
    cleanup_claim = c.execute(
        "INSERT OR IGNORE INTO app_migrations (migration_key, applied_at) VALUES (?,?)",
        (cleanup_key, datetime.now().isoformat(timespec="seconds")),
    )
    if cleanup_claim.rowcount == 1:
        archive_demo_tasks(conn)
    c.execute('''CREATE TABLE IF NOT EXISTS demand_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT,
                    sku TEXT,
                    product_name TEXT,
                    timestamp TEXT
                )''')
    c.execute("""CREATE TABLE IF NOT EXISTS hubspot_demo_tasks (
        task_key TEXT PRIMARY KEY, task_id TEXT
    )""")
    c.execute("CREATE TABLE IF NOT EXISTS hubspot_pending_completion (task_id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

init_offline_db()

# ==============================================================================
# 3. HUBSPOT REST API CONNECTOR
# ==============================================================================
class HubSpotAPIConnector:
    """HubSpot connector. Uses real API responses; never reports mock orders as live."""
    def __init__(self, token: str):
        self.token = (token or "").strip()
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def _find_order_pipeline(self):
        if not self.token:
            return None, None, {"status": "MOCK", "msg": "Kein HubSpot-Zugangstoken konfiguriert."}
        try:
            res = requests.get("https://api.hubapi.com/crm/v3/pipelines/deals", headers=self.headers, timeout=10)
            if res.status_code != 200:
                return None, None, {"status": "ERROR", "msg": f"Pipeline-Abfrage fehlgeschlagen (HTTP {res.status_code}): {res.text[:300]}"}
            data = res.json().get("results", [])
            # Prefer the pipeline used for GastroLingua, otherwise any pipeline with an order-entry stage.
            candidates = []
            for pipe in data:
                for stage in pipe.get("stages", []):
                    label = str(stage.get("label", "")).casefold()
                    sid = str(stage.get("id", "")).casefold()
                    if "auftragseingang" in label or "auftragseingang" in sid or "comand" in label:
                        score = (3 if "gastro" in str(pipe.get("label", "")).casefold() else 0) + (2 if "vertrag" in str(pipe.get("label", "")).casefold() else 0) + (1 if "auftragseingang" in label else 0)
                        candidates.append((score, pipe, stage))
            if candidates:
                _, pipe, stage = sorted(candidates, key=lambda x: x[0], reverse=True)[0]
                return pipe, stage, None
            # Fallback: use the first pipeline's first stage rather than guessing an invalid ID.
            if data and data[0].get("stages"):
                return data[0], data[0]["stages"][0], {"status": "WARNING", "msg": "Keine Phase 'Auftragseingang' gefunden; erste HubSpot-Pipelinephase wird verwendet."}
            return None, None, {"status": "ERROR", "msg": "HubSpot hat keine Deal-Pipelines oder Phasen zurückgegeben."}
        except Exception as e:
            return None, None, {"status": "FAILED", "msg": f"Pipeline-Abfrage fehlgeschlagen: {e}"}

    def create_deal(self, deal_name: str, amount: float, items_summary: str):
        if not self.token:
            return {"status": "MOCK", "msg": "Kein HubSpot-Zugangstoken konfiguriert. Es wurde nichts an HubSpot gesendet."}
        pipe, stage, err = self._find_order_pipeline()
        if err and err.get("status") not in ("WARNING",):
            return err
        if not pipe or not stage:
            return err or {"status": "ERROR", "msg": "Keine passende HubSpot-Pipeline gefunden."}
        payload = {"properties": {"dealname": deal_name, "amount": f"{amount:.2f}", "pipeline": str(pipe.get("id")), "dealstage": str(stage.get("id")), "description": items_summary}}
        try:
            res = requests.post("https://api.hubapi.com/crm/v3/objects/deals", json=payload, headers=self.headers, timeout=10)
            if res.status_code in (200, 201):
                created_id = str(res.json().get("id") or "")
                if created_id:
                    try:
                        conn = sqlite3.connect(OFFLINE_DB)
                        with conn:
                            conn.execute("CREATE TABLE IF NOT EXISTS created_demo_deals (deal_id TEXT PRIMARY KEY, deal_name TEXT)")
                            conn.execute("INSERT OR REPLACE INTO created_demo_deals (deal_id, deal_name) VALUES (?, ?)", (created_id, deal_name))
                        conn.close()
                    except Exception:
                        pass
                return {"status": "SUCCESS", "deal_id": created_id, "pipeline": pipe.get("label"), "stage": stage.get("label"), "warning": err.get("msg") if err else None}
            return {"status": "ERROR", "msg": f"HubSpot-Deal konnte nicht angelegt werden (HTTP {res.status_code}): {res.text[:500]}"}
        except Exception as e:
            return {"status": "FAILED", "msg": f"HubSpot-Verbindung fehlgeschlagen: {e}"}

    def sync_stage(self, deal_id: str, stage_code: str, status_text: str):
        """Update a HubSpot deal using the REAL stage ID from that deal's pipeline.

        The app's internal codes (e.g. '2_kommissionierung') are not HubSpot stage IDs.
        Resolve the current deal pipeline and its stage IDs from the API before PATCHing.
        """
        if not self.token or not str(deal_id).isdigit():
            return {"status": "MOCK", "msg": "Kein bestätigter HubSpot-Deal vorhanden."}
        aliases = {
            "8_innendienst_offen": ("innendienst offen",),
            "9_auftrag_abgeschlossen": ("auftrag abgeschlossen",),
            "1_auftragseingang": ("auftragseingang", "auftragseingang"),
            "2_kommissionierung": ("kommissionierung", "kommission"),
            "3_gepackt": ("gepackt", "pack", "verpackt"),
            "4_verladen": ("verladen", "beladen", "loading"),
            "5_belieferung": ("belieferung", "lieferung", "delivery"),
            "6_geliefert": ("geliefert", "delivery", "pod"),
            # Ramp inspection must move the deal to a dedicated ramp/final-review stage
            # in the SAME HubSpot pipeline. Do not silently map it back to "Geliefert".
            # If the HubSpot pipeline has no matching phase, sync_stage returns an explicit
            # error listing available stage labels, so the user can configure the pipeline.
            "7_abgeschlossen": ("rampen-prüfung abgeschlossen", "rampenprüfung", "rampen-prüfung", "rampenkontrolle", "kontrolle rampe", "rampen", "rampe"),
        }
        try:
            deal_res = requests.get(
                f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}?properties=pipeline,dealstage",
                headers=self.headers, timeout=10,
            )
            if deal_res.status_code != 200:
                return {"status": "ERROR", "msg": f"Deal-Abfrage fehlgeschlagen (HTTP {deal_res.status_code}): {deal_res.text[:300]}"}
            current_props = deal_res.json().get("properties", {})
            pipeline_id = str(current_props.get("pipeline", ""))
            if not pipeline_id:
                return {"status": "ERROR", "msg": "Der HubSpot-Deal enthält keine Pipeline-ID; Phase wurde nicht geändert."}

            pipes_res = requests.get("https://api.hubapi.com/crm/v3/pipelines/deals", headers=self.headers, timeout=10)
            if pipes_res.status_code != 200:
                return {"status": "ERROR", "msg": f"Pipeline-Phasen konnten nicht gelesen werden (HTTP {pipes_res.status_code}): {pipes_res.text[:300]}"}
            pipelines = pipes_res.json().get("results", [])
            pipeline = next((p for p in pipelines if str(p.get("id")) == pipeline_id), None)
            if not pipeline:
                return {"status": "ERROR", "msg": f"Pipeline {pipeline_id} des Deals wurde in HubSpot nicht gefunden."}

            wanted = aliases.get(str(stage_code), ())
            stages = pipeline.get("stages", [])
            target = None
            # Match by semantic stage label, not by GastroLingua's internal code.
            for alias in wanted:
                target = next((stg for stg in stages if alias in str(stg.get("label", "")).casefold()), None)
                if target:
                    break
            if not target:
                labels = ", ".join(str(stg.get("label", "")) for stg in stages)
                return {"status": "ERROR", "msg": f"Keine passende HubSpot-Phase für '{status_text}' in Pipeline '{pipeline.get('label', pipeline_id)}' gefunden. Vorhandene Phasen: {labels}. Phase wurde nicht geändert."}

            res = requests.patch(
                f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}",
                json={"properties": {"dealstage": str(target.get("id"))}},
                headers=self.headers, timeout=10,
            )
            if res.status_code in (200, 201):
                return {"status": "SUCCESS", "msg": f"HubSpot-Phase aktualisiert: {target.get('label', target.get('id'))}", "stage": target.get("label"), "stage_id": target.get("id")}
            return {"status": "ERROR", "msg": f"HubSpot-Phase konnte nicht aktualisiert werden (HTTP {res.status_code}): {res.text[:300]}"}
        except Exception as e:
            return {"status": "FAILED", "msg": f"HubSpot-Phasenabgleich fehlgeschlagen: {e}"}

    def create_crm_task(self, title: str, body: str, category: str, *, deal_id=None):
        """Create a HubSpot task and optionally link it to its deal.

        HubSpot task creation requires a due timestamp in addition to the subject.
        Return the created task ID so the UI can distinguish a confirmed task from
        a merely locally stored alert.
        """
        if not self.token:
            return {"status": "MOCK", "msg": "Kein HubSpot-Zugangstoken konfiguriert; keine Aufgabe angelegt."}
        due_ms = int(datetime.now().timestamp() * 1000)
        payload = {"properties": {
            "hs_task_subject": (f"[INNENDIENST | {category}] {title}" if deal_id else f"[FAHRER-ALERT | {category}] {title}")[:250],
            "hs_task_body": body,
            "hs_timestamp": str(due_ms),
            "hs_task_status": "NOT_STARTED",
            # Demo owner for GastroLingua Demo.
            "hubspot_owner_id": "97076079",
            "hs_task_priority": "HIGH",
            "hs_task_type": "TODO",
        }}
        if deal_id:
            payload["associations"] = [{
                "to": {"id": str(deal_id)},
                "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 216}],
            }]
        try:
            res = requests.post(
                "https://api.hubapi.com/crm/v3/objects/tasks",
                json=payload, headers=self.headers, timeout=15,
            )
            if res.status_code in (200, 201):
                data = res.json()
                return {"status": "SUCCESS", "msg": "HubSpot-Aufgabe erfolgreich angelegt.", "task_id": data.get("id")}
            detail = res.text[:700]
            return {"status": "ERROR", "msg": f"HubSpot-Aufgabe konnte nicht angelegt werden (HTTP {res.status_code}): {detail}"}
        except Exception as e:
            return {"status": "FAILED", "msg": f"Verbindung zu HubSpot fehlgeschlagen: {e}"}

    def fetch_live_deals(self, limit: int = 20):
        """Read-only live query of HubSpot deals and their human-readable pipeline stage labels."""
        if not self.token:
            return {"status": "MOCK", "deals": [], "msg": "Kein HubSpot-Token konfiguriert."}
        try:
            stage_map = {}
            pipe_map = {}
            pipes_res = requests.get("https://api.hubapi.com/crm/v3/pipelines/deals", headers=self.headers, timeout=10)
            if pipes_res.status_code == 200:
                for p in pipes_res.json().get("results", []):
                    pid = str(p.get("id", ""))
                    pipe_map[pid] = str(p.get("label", pid))
                    for stg in p.get("stages", []):
                        sid = str(stg.get("id", ""))
                        stage_map[(pid, sid)] = str(stg.get("label", sid))
                        stage_map[("", sid)] = str(stg.get("label", sid))

            deals_res = requests.get(
                "https://api.hubapi.com/crm/v3/objects/deals",
                params={"limit": limit, "properties": "dealname,amount,pipeline,dealstage,hs_lastmodifieddate"},
                headers=self.headers,
                timeout=10,
            )
            if deals_res.status_code != 200:
                return {"status": "ERROR", "deals": [], "msg": f"HubSpot Deals-Abfrage HTTP {deals_res.status_code}"}

            raw_deals = deals_res.json().get("results", [])
            raw_deals.sort(key=lambda d: str((d.get("properties") or {}).get("hs_lastmodifieddate") or d.get("id") or ""), reverse=True)
            rows = []
            for d in raw_deals:
                props = d.get("properties") or {}
                pid = str(props.get("pipeline", ""))
                sid = str(props.get("dealstage", ""))
                try:
                    amt_str = f"{float(props.get('amount') or 0):.2f} €"
                except (ValueError, TypeError):
                    amt_str = str(props.get("amount") or "0.00 €")
                mod_raw = str(props.get("hs_lastmodifieddate") or "")[:19].replace("T", " ")
                did_str = str(d.get("id", ""))
                if did_str in self._get_cleared_ids("deal"):
                    continue
                rows.append({
                    "HubSpot Deal-ID": did_str,
                    "Auftrag / Deal": str(props.get("dealname", "—")),
                    "Betrag": amt_str,
                    "Pipeline": pipe_map.get(pid, pid or "—"),
                    "Aktuelle Dealphase (Live)": stage_map.get((pid, sid)) or stage_map.get(("", sid)) or sid or "—",
                    "Aktualisiert (UTC)": mod_raw or "—",
                })
            return {"status": "SUCCESS", "deals": rows}
        except Exception as e:
            return {"status": "FAILED", "deals": [], "msg": f"Verbindungsfehler: {e}"}

    def fetch_live_tasks(self, limit: int = 20):
        """Read-only live query of HubSpot tasks for inside and field sales."""
        if not self.token:
            return {"status": "MOCK", "tasks": [], "msg": "Kein HubSpot-Token konfiguriert."}
        try:
            res = requests.get(
                "https://api.hubapi.com/crm/v3/objects/tasks",
                params={"limit": limit, "properties": "hs_task_subject,hs_task_status,hs_task_priority,hs_lastmodifieddate"},
                headers=self.headers,
                timeout=10,
            )
            if res.status_code != 200:
                return {"status": "ERROR", "tasks": [], "msg": f"HubSpot Aufgaben-Abfrage HTTP {res.status_code}"}
            raw_tasks = res.json().get("results", [])
            raw_tasks.sort(key=lambda t: str((t.get("properties") or {}).get("hs_lastmodifieddate") or t.get("id") or ""), reverse=True)
            status_de = {
                "NOT_STARTED": "🟡 Offen (NOT_STARTED)",
                "IN_PROGRESS": "🔵 In Bearbeitung",
                "WAITING": "🟠 Wartend",
                "COMPLETED": "✅ Erledigt (COMPLETED)",
            }
            rows = []
            for t in raw_tasks:
                props = t.get("properties") or {}
                raw_st = str(props.get("hs_task_status") or "NOT_STARTED")
                tid_str = str(t.get("id", ""))
                if tid_str in self._get_cleared_ids("task"):
                    continue
                rows.append({
                    "HubSpot Task-ID": tid_str,
                    "Aufgabe / Betreff": str(props.get("hs_task_subject") or "—"),
                    "Status in HubSpot": status_de.get(raw_st, raw_st),
                    "Priorität": str(props.get("hs_task_priority") or "NORMAL"),
                })
            return {"status": "SUCCESS", "tasks": rows}
        except Exception as e:
            return {"status": "FAILED", "tasks": [], "msg": f"Verbindungsfehler: {e}"}

    def _get_cleared_ids(self, obj_type: str) -> set:
        try:
            conn = sqlite3.connect(OFFLINE_DB)
            conn.execute("CREATE TABLE IF NOT EXISTS cleared_hubspot_objects (obj_type TEXT, obj_id TEXT, PRIMARY KEY (obj_type, obj_id))")
            rows = conn.execute("SELECT obj_id FROM cleared_hubspot_objects WHERE obj_type=?", (obj_type,)).fetchall()
            conn.close()
            return {str(r[0]) for r in rows}
        except Exception:
            return set()

    def cleanup_demo_crm_data(self):
        """Delete ONLY exact GastroLingua app test deals (in the order pipeline) and exact app-generated demo tasks."""
        if not self.token:
            return {"deleted_deals": 0, "deleted_tasks": 0}
        deleted_deals = 0
        deleted_tasks = 0
        cleared_pairs = []

        # Exact demo account names used in the GastroLingua prototype
        demo_account_names = {
            "Brauhaus zum Hirschen",
            "Ristorante Bella Italia",
            "Restaurant Sarajevo",
            "Trattoria am Markt",
            "Hotel Rheinblick",
            "Restoran Dunav",
            "Ad Mina",
            "Petruta Guta",
            "Zoka Gredeljevic",
            "Nicolae Guta",
            "Friedrich Merz",
            "Anna Nass",
            "Paco Rabanne",
            "Dominique Kieburg (Außendienst)",
        }
        exact_demo_deal_names = {f"GastroLingua Auftrag – {name}".casefold() for name in demo_account_names}
        exact_demo_deal_names.update({f"GastroLingua Auftrag - {name}".casefold() for name in demo_account_names})

        # Load exact IDs created by this app from SQLite
        tracked_deal_ids = set()
        tracked_task_ids = set()
        try:
            conn = sqlite3.connect(OFFLINE_DB)
            conn.execute("CREATE TABLE IF NOT EXISTS created_demo_deals (deal_id TEXT PRIMARY KEY, deal_name TEXT)")
            tracked_deal_ids = {str(r[0]) for r in conn.execute("SELECT deal_id FROM created_demo_deals WHERE deal_id IS NOT NULL").fetchall()}
            tracked_task_ids = {str(r[0]) for r in conn.execute("SELECT task_id FROM hubspot_demo_tasks WHERE task_id IS NOT NULL").fetchall()}
            conn.close()
        except Exception:
            pass

        # Resolve the exact GastroLingua order pipeline ID so other pipelines are never touched
        order_pipe, _, _ = self._find_order_pipeline()
        target_pipeline_id = str(order_pipe.get("id", "")) if order_pipe else ""
        target_pipeline_label = str(order_pipe.get("label", "")).casefold() if order_pipe else ""

        if target_pipeline_id and ("gastro" in target_pipeline_label or "auftrag" in target_pipeline_label):
            try:
                d_res = requests.get(
                    "https://api.hubapi.com/crm/v3/objects/deals",
                    params={"limit": 100, "properties": "dealname,pipeline"},
                    headers=self.headers,
                    timeout=10,
                )
                if d_res.status_code == 200:
                    for d in d_res.json().get("results", []):
                        did = str(d.get("id", ""))
                        props = d.get("properties") or {}
                        dpipe = str(props.get("pipeline") or "")
                        dname = str(props.get("dealname") or "").strip()
                        is_exact_demo_deal = (
                            did in tracked_deal_ids
                            or dname.casefold() in exact_demo_deal_names
                        )
                        if did and dpipe == target_pipeline_id and is_exact_demo_deal:
                            cleared_pairs.append(("deal", did))
                            del_r = requests.delete(f"https://api.hubapi.com/crm/v3/objects/deals/{did}", headers=self.headers, timeout=8)
                            if del_r.status_code in (200, 204):
                                deleted_deals += 1
            except Exception:
                pass

        # Only delete tasks with exact GastroLingua app subjects for the demo customers (or tracked IDs)
        demo_customers_cf = {c.casefold() for c in demo_account_names}
        driver_prefixes = (
            "[FAHRER-ALERT | QUALITÄTSMANGEL] Kundenfeedback (",
            "[FAHRER-ALERT | PREISDRUCK] Kundenfeedback (",
            "[FAHRER-ALERT | UPSELLING_WUNSCH] Kundenfeedback (",
            "[FAHRER-ALERT | SONSTIGES] Kundenfeedback (",
        )
        office_prefixes = (
            "[INNENDIENST | RETOURE] Retoure prüfen · ",
            "[INNENDIENST | LEERGUT] Leergutgutschrift buchen · ",
        )
        try:
            t_res = requests.get(
                "https://api.hubapi.com/crm/v3/objects/tasks",
                params={"limit": 100, "properties": "hs_task_subject"},
                headers=self.headers,
                timeout=10,
            )
            if t_res.status_code == 200:
                for t in t_res.json().get("results", []):
                    tid = str(t.get("id", ""))
                    subj = str((t.get("properties") or {}).get("hs_task_subject") or "").strip()
                    subj_cf = subj.casefold()
                    has_demo_customer = any(c in subj_cf for c in demo_customers_cf)
                    is_exact_demo_task = (
                        tid in tracked_task_ids
                        or (subj.startswith(driver_prefixes) and has_demo_customer)
                        or (subj.startswith(office_prefixes) and has_demo_customer)
                    )
                    if tid and is_exact_demo_task:
                        cleared_pairs.append(("task", tid))
                        del_t = requests.delete(f"https://api.hubapi.com/crm/v3/objects/tasks/{tid}", headers=self.headers, timeout=8)
                        if del_t.status_code in (200, 204):
                            deleted_tasks += 1
        except Exception:
            pass

        if cleared_pairs:
            try:
                conn = sqlite3.connect(OFFLINE_DB)
                with conn:
                    conn.execute("CREATE TABLE IF NOT EXISTS cleared_hubspot_objects (obj_type TEXT, obj_id TEXT, PRIMARY KEY (obj_type, obj_id))")
                    conn.executemany("INSERT OR IGNORE INTO cleared_hubspot_objects (obj_type, obj_id) VALUES (?, ?)", cleared_pairs)
                conn.close()
            except Exception:
                pass
        return {"deleted_deals": deleted_deals, "deleted_tasks": deleted_tasks}

def sync_office_stage(hubspot, deal):
    if not deal.get("rampe_locked"):
        return
    deal_id = str(deal["deal_id"])
    conn = sqlite3.connect(OFFLINE_DB)
    try:
        open_return = conn.execute(
            """SELECT 1 FROM return_cases
            WHERE deal_id=? AND COALESCE(archived,0)=0
            AND COALESCE(status,'')<>'ERLEDIGT' LIMIT 1""",
            (deal_id,),
        ).fetchone()
    finally:
        conn.close()
    open_empties = deal.get("leergut_verified", {}).get("e2", 0) > 0 and not deal.get("gutschrift_gebucht")
    if open_return or open_empties:
        code, label = "8_innendienst_offen", "Innendienst offen"
    else:
        code, label = "9_auftrag_abgeschlossen", "Auftrag abgeschlossen"
    result = hubspot.sync_stage(deal.get("hs_id") or deal_id, code, label)
    deal["hubspot_office_stage_pending"] = result.get("status") != "SUCCESS"
    if deal["hubspot_office_stage_pending"]:
        st.toast(f"Auftrag #{deal_id}: HubSpot-Phase nicht bestätigt. {result.get('msg', '')}", icon="⚠️")
    else:
        deal["hubspot_office_stage_sent"] = True
        st.toast(f"HubSpot: {label}", icon="✅")


def sync_task_completion(hubspot, task_key=None):
    conn = sqlite3.connect(OFFLINE_DB, timeout=10)
    try:
        if task_key is not None:
            with conn:
                conn.execute(
                    """INSERT OR IGNORE INTO hubspot_pending_completion (task_id)
                    SELECT task_id FROM hubspot_demo_tasks WHERE task_key=? AND task_id IS NOT NULL""",
                    (task_key,),
                )
            row = conn.execute(
                "SELECT task_id FROM hubspot_demo_tasks WHERE task_key=?", (task_key,)
            ).fetchone()
            if not row or not row[0]:
                st.toast("Lokal erledigt. Keine HubSpot-Aufgabe mit diesem Vorgang verknüpft.", icon="ℹ️")
                return
            task_ids = [row[0]]
        else:
            task_ids = [row[0] for row in conn.execute("SELECT task_id FROM hubspot_pending_completion")]
        failed = 0
        for task_id in task_ids:
            if not hubspot.token:
                failed += 1
                continue
            try:
                response = requests.patch(
                    f"https://api.hubapi.com/crm/v3/objects/tasks/{task_id}",
                    json={"properties": {"hs_task_status": "COMPLETED"}},
                    headers=hubspot.headers, timeout=10,
                )
                if not response.ok:
                    failed += 1
                    continue
                with conn:
                    conn.execute("DELETE FROM hubspot_pending_completion WHERE task_id=?", (task_id,))
            except requests.RequestException:
                failed += 1
        if failed:
            st.toast("Lokal erledigt. HubSpot-Abschluss offen. Bitte in der Seitenleiste erneut senden.", icon="⚠️")
        elif task_ids:
            st.toast("Aufgabe in HubSpot abgeschlossen.", icon="✅")
        return bool(task_ids) and failed == 0
    finally:
        conn.close()


def sync_driver_task_details(hubspot, alert_id, body, appointment):
    if not hubspot.token:
        return "HubSpot-Token fehlt."
    conn = sqlite3.connect(OFFLINE_DB)
    try:
        task = conn.execute(
            "SELECT task_id FROM hubspot_demo_tasks WHERE task_key=?",
            (f"driver:{alert_id}",),
        ).fetchone()
    finally:
        conn.close()
    if not task or not task[0]:
        return "Keine HubSpot-Aufgabe mit diesem Fahrerhinweis verknüpft."
    properties = {"hs_task_body": body, "hs_task_status": "NOT_STARTED"}
    if appointment:
        properties["hs_timestamp"] = str(int(appointment.timestamp() * 1000))
    try:
        response = requests.patch(
            f"https://api.hubapi.com/crm/v3/objects/tasks/{task[0]}",
            json={"properties": properties}, headers=hubspot.headers, timeout=10,
        )
        if not response.ok:
            return f"HubSpot meldet HTTP {response.status_code}."
    except requests.RequestException:
        return "HubSpot war nicht erreichbar."
    return ""


def send_office_task(hubspot, task_key, deal_id, category, title, body):
    if not hubspot.token:
        st.toast("Lokal gespeichert. HubSpot-Token fehlt.", icon="⚠️")
        return
    conn = sqlite3.connect(OFFLINE_DB, timeout=10)
    try:
        with conn:
            claim = conn.execute(
                "INSERT OR IGNORE INTO hubspot_demo_tasks (task_key) VALUES (?)",
                (task_key,),
            )
        if claim.rowcount == 0:
            existing = conn.execute(
                "SELECT task_id FROM hubspot_demo_tasks WHERE task_key=?", (task_key,)
            ).fetchone()
            if existing and not existing[0]:
                st.toast("HubSpot-Aufgabe für diesen Vorgang bitte in HubSpot prüfen.", icon="⚠️")
            return
        result = hubspot.create_crm_task(title, body, category, deal_id=deal_id)
        if result.get("status") == "SUCCESS" and result.get("task_id"):
            with conn:
                conn.execute(
                    "UPDATE hubspot_demo_tasks SET task_id=? WHERE task_key=?",
                    (str(result["task_id"]), task_key),
                )
            st.toast(f"HubSpot-Aufgabe erstellt: {title}", icon="✅")
        else:
            if result.get("status") == "ERROR":
                with conn:
                    conn.execute("DELETE FROM hubspot_demo_tasks WHERE task_key=?", (task_key,))
            st.toast(f"Lokal gespeichert. {result.get('msg', 'HubSpot-Aufgabe nicht bestätigt.')}", icon="⚠️")
    except sqlite3.Error as error:
        st.toast(f"Lokal gespeichert. HubSpot-Aufgabenstatus konnte nicht gespeichert werden: {error}", icon="⚠️")
    finally:
        conn.close()


# ==============================================================================
# 4. SPRACHMATRIZEN & KATALOG
# ==============================================================================
LANG_PACK = {
    "de": {
        "logged_in": "Eingeloggt als:", "sys_lang": "System-Sprache:", "active_orders_cnt": "Echte aktive Aufträge:",
        "kundenportal_title": "🛒 B2B-Kundenportal & KI-Voice Order",
        "countdown": "⏳ Bestellfenster Kühlgut noch 2 Std. 15 Min. offen",
        "tab_voice": "🎙️ KI-Voice Order", "tab_cut": "🥦 Ready-Cut Rechner", "tab_cat": "📚 A-Z Produktkatalog", "tab_pfand": "📊 Pfand & GPS Status",
        "voice_header": "🎙️ Whisper Voice-NLU Sprachbestellung", "voice_placeholder": "Sprachnachricht frei einsprechen oder simulieren:", "voice_btn": "🚀 KI-Sprachextraktion ausführen",
        "cut_header": "🥗 Ready-Cut vs. Rohwaren-Splitting (Frische-Gemüseküche)", "cut_label": "Gewünschte Netto-Salatmenge (kg):", "cut_result": "Berechnete Brutto-Einsatzware:",
        "cut_btn1": "✂️ Als Ready-Cut für Morgen bestellen", "cut_btn2": "🥦 Als Rohware für HEUTE NACHT buchen",
        "cat_header": "📚 A-Z B2B Produktkatalog", "search_label": "🔍 Produkt suchen (z. B. 'to' für Tomaten oder 'bar' für Barolo):", "cat_filter_label": "Filter nach Kategorie:",
        "add_cart": "➕ In den Warenkorb", "add_more": "➕ Noch hinzufügen", "in_cart_badge": "✓ IM WARENKORB",
        "out_of_stock": "❌ ARTIKEL AKTUELL NICHT AUF LAGER", "alt_label": "💡 Direkt verfügbare Alternative auf Lager:", "alt_btn": "🔄 Alternative jetzt wählen",
        "alt_added_badge": "✅ ALTERNATIVE IM WARENKORB", "demand_btn": "📩 Bedarfsmeldung an Einkauf",
        "cart_title": "🛒 Aktueller Warenkorb:", "cart_empty": "Warenkorb ist noch leer.", "cart_total": "Gesamtsumme:",
        "submit_order": "🚀 1. Auftrag VERBINDLICH FREIGEBEN (Stage 1_auftragseingang)",
        "toast_added": "zum Warenkorb hinzugefügt!", "toast_order_sent": "Auftrag eingegangen & Live in HubSpot Stage 1 angelegt!",
        "stage_1": "1. Auftragseingang", "stage_2": "2. In Kommissionierung", "stage_3": "3. Gepackt am Tor", "stage_4": "4. Verladen im LKW", "stage_5": "5. In Belieferung", "stage_6": "6. Geliefert (POD)", "stage_7": "7. Rampen-Prüfung Abgeschlossen",
        "pfand_header": "📊 B2B-Pfandkonto & Live GPS Telemetrie", "e2_balance": "E2-Kisten Saldo", "eta": "LKW Ankunftszeit (ETA)", "temp": "Kühlraum Temperatur Frische",
        "picking_header": "📦 Kommissionierung (Pool-Pick)", "picking_info": "Laufweg: Trockengut ➔ Frische ➔ Tiefkühlhaus",
        "no_orders_pool": "ℹ️ Derzeit befinden sich keine offenen Kunden-Aufträge im Pool.", "pool_orders_title": "Eingehende echte Aufträge im Pool",
        "start_picking": "▶️ Kommissionierung STARTEN", "finish_packing": "✅ 3. Packen BEENDEN & an Tor übergeben",
        "driver_header": "🚚 LKW-Auslieferung & Belieferung", "no_driver_orders": "ℹ️ Keine versandbereiten Aufträge zur Auslieferung vorhanden.",
        "driver_alert_title": "📢 Instant Feedback-Bridge (Notiz an Außendienst):", "driver_alert_btn": "⚡ Alert an Außendienst senden",
        "rampe_header": "🛑 Rampen-Prüfung nach Tourenende (Prozess-Firewall)", "no_rampe_orders": "ℹ️ Keine zurückgekehrten LKWs zur Rampen-Prüfung vorhanden.",
        "innendienst_header": "💼 Innendienst: Gutschriften-Firewall & Churn Protection",
        "sales_header": "📱 Field Sales Engine & Driver Signal Radar", "no_alerts": "Keine ungelesenen Driver-Alerts vorhanden.",
        "admin_header": "👑 Admin Control Center & Offene Bedarfsmeldungen", "no_demands": "Keine offenen Bedarfsmeldungen im System.", "dispo_header": "⚙️ Disposition & Capacity Matching",
        "planned_tours_title": '🗺️ Meine geplanten Touren (Vorabinformation)', "planned_tours_info": 'Diese Touren wurden von der Disposition vorgeplant. Die Anzeige ist eine Demo-Simulation; eine Tour ist erst auslieferungsbereit, wenn die Ware kommissioniert und freigegeben wurde.', "tour_order": 'Auftrag', "tour_vehicle": 'Fahrzeug', "tour_stop": 'Tour-Stopp', "tour_status": 'Tourstatus (Simulation)', "not_set": 'Nicht festgelegt'
    },
    "ro": {
        "logged_in": "Autentificat ca:", "sys_lang": "Limba sistemului:", "active_orders_cnt": "Comenzi active reale:",
        "kundenportal_title": "🛒 Portal B2B Clienți & Comandă Vocală IA",
        "countdown": "⏳ Fereastra de comandă marfă rece: încă 2 ore 15 min deschisă",
        "tab_voice": "🎙️ Comandă Vocală IA", "tab_cut": "🥦 Calculator Ready-Cut", "tab_cat": "📚 Catalog Produse A-Z", "tab_pfand": "📊 Garanție & Status GPS",
        "voice_header": "🎙️ Procesare Comandă Vocală Whisper NLU", "voice_placeholder": "Înregistrează sau simulează mesajul vocal în limba română:", "voice_btn": "🚀 Execută extracția vocală IA",
        "cut_header": "🥗 Ready-Cut vs. Separare Materie Primă (Legume Proaspete)", "cut_label": "Cantitate netă salată dorită (kg):", "cut_result": "Materie primă brută calculată:",
        "cut_btn1": "✂️ Comandă ca Ready-Cut pentru mâine", "cut_btn2": "🥦 Comandă ca materie primă pentru DESEARĂ",
        "cat_header": "📚 Catalog B2B Produse A-Z", "search_label": "🔍 Caută produs (ex. 'to' sau 'bar'):", "cat_filter_label": "Filtrează după categorie:",
        "add_cart": "➕ În coș", "add_more": "➕ Mai adaugă", "in_cart_badge": "✓ ÎN COȘ",
        "out_of_stock": "❌ ARTICOLUL NU ESTE ÎN STOC ÎN PREZENT!", "alt_label": "💡 Alternativă disponibilă imediat în stoc:", "alt_btn": "🔄 Selectează alternativa acum",
        "alt_added_badge": "✅ ALTERNATIVA ADĂUGATĂ ÎN COȘ", "demand_btn": "📩 Notificare de necesar",
        "cart_title": "🛒 Coșul tău actual:", "cart_empty": "Coșul este gol.", "cart_total": "Total general:", "submit_order": "🚀 1. Trimite comanda fermă",
        "toast_added": "adăugat în coș!", "toast_order_sent": "Comandă primită și creată live în HubSpot Faza 1!",
        "stage_1": "1. Comandă primită", "stage_2": "2. În pregătire", "stage_3": "3. Impachetat la poartă", "stage_4": "4. Încărcat în camion", "stage_5": "5. În livrare", "stage_6": "6. Livrat (POD)", "stage_7": "7. Control Rampă Finalizat",
        "pfand_header": "📊 Cont Garanție B2B & Telemetrie GPS Live", "e2_balance": "Sold Navete E2", "eta": "Timp Sosire Camion (ETA)", "temp": "Temperatură Cameră Frigorifică",
        "picking_header": "📦 Pregătire Marfă (Pool-Pick)", "picking_info": "Traseu: Produse uscate ➔ Proaspete ➔ Congelator", "no_orders_pool": "ℹ️ În prezent nu există comenzi deschise în pool.",
        "pool_orders_title": "Comenzi reale primite în pool", "start_picking": "▶️ ÎNCEPE Pregătirea", "finish_packing": "✅ 3. FINALIZEAZĂ Pregătirea",
        "driver_header": "🚚 Livrare Camion", "no_driver_orders": "ℹ️ Nu există comenzi gata de livrare.", "driver_alert_title": "📢 Instant Feedback-Bridge (Notă vocală pentru agenți):", "driver_alert_btn": "⚡ Trimite alertă la agent",
        "rampe_header": "🛑 Inspecție Rampă după tură", "no_rampe_orders": "ℹ️ Nu există camioane returnate pentru inspecție la rampă.",
        "innendienst_header": "💼 Birou Vânzări: Firewall Note de Credit", "sales_header": "📱 Engine Agenți Teren & Radar Semnal Șofer", "no_alerts": "Nu există alerte necitite de la șoferi.",
        "admin_header": "👑 Centru Control Admin", "no_demands": "Nu există notificări de necesar în sistem.", "dispo_header": "⚙️ Dispecerat & Planificare Capacitate",
        "planned_tours_title": '🗺️ Traseele mele planificate (informare în avans)', "planned_tours_info": 'Aceste trasee au fost planificate în avans de dispecerat. Afișarea este o simulare demo; un traseu este gata de livrare numai după pregătirea și aprobarea mărfii.', "tour_order": 'Comandă', "tour_vehicle": 'Vehicul', "tour_stop": 'Oprire pe traseu', "tour_status": 'Status traseu (simulare)', "not_set": 'Nespecificat'
    },
    "sr": {
        "logged_in": "Prijavljeni kao:", "sys_lang": "Jezik sistema:", "active_orders_cnt": "Aktivne prave porudžbine:",
        "kundenportal_title": "🛒 B2B Portal za kupce & Glasovno naručivanje",
        "countdown": "⏳ Prozor za narudžbinu rashlađene robe otvoren još 2 sata 15 min",
        "tab_voice": "🎙️ AI Glasovno naručivanje", "tab_cut": "🥦 Ready-Cut Kalkulator", "tab_cat": "📚 A-Z Katalog proizvoda", "tab_pfand": "📊 Ambalaža & GPS Status",
        "voice_header": "🎙️ Whisper NLU Obrada glasovne porudžbine", "voice_placeholder": "Snimite ili simulirajte glasovnu poruku na srpskom jeziku:", "voice_btn": "🚀 Pokreni AI ekstrakciju glasa",
        "cut_header": "🥗 Ready-Cut vs. Sirova roba (Sveže povrće)", "cut_label": "Željena neto količina salate (kg):", "cut_result": "Izračunata bruto sirova roba:",
        "cut_btn1": "✂️ Naruči kao Ready-Cut za sutra", "cut_btn2": "🥦 Naruči kao sirovu robu za VEČERAS",
        "cat_header": "📚 A-Z B2B Katalog proizvoda", "search_label": "🔍 Pretraga proizvoda (npr. 'to' ili 'bar'):", "cat_filter_label": "Filtriraj po kategoriji:",
        "add_cart": "➕ U korpu", "add_more": "➕ Dodaj još", "in_cart_badge": "✓ U KORPI",
        "out_of_stock": "❌ ARTIKAL TRENUTNO NIJE NA LAGERU!", "alt_label": "💡 Odmah dostupna alternativa na lageru:", "alt_btn": "🔄 Izaberi alternativu sada",
        "alt_added_badge": "✅ ALTERNATIVA U KORPI", "demand_btn": "📩 Obaveštenje nabavci",
        "cart_title": "🛒 Vaša trenutna korpa:", "cart_empty": "Korpa je prazna.", "cart_total": "Ukupan iznos:", "submit_order": "🚀 1. Potvrdi i pošalji porudžbinu",
        "toast_added": "dodato u korpu!", "toast_order_sent": "Porudžbina primljena i kreirana uživo u HubSpot Fazi 1!",
        "stage_1": "1. Porudžbina primljena", "stage_2": "2. U pakovanju", "stage_3": "3. Spakovano na kapiji", "stage_4": "4. Utovareno u kamion", "stage_5": "5. U isporuci", "stage_6": "6. Isporučeno (POD)", "stage_7": "7. Kontrola Rampe Završena",
        "pfand_header": "📊 B2B Ambalažni nalog & GPS Praćenje uživo", "e2_balance": "Stanje E2 gajbi", "eta": "Vreme dolaska kamiona (ETA)", "temp": "Temperatura hladnjače",
        "picking_header": "📦 Pakovanje robe (Pool-Pick)", "picking_info": "Ruta: Suva roba ➔ Sveže ➔ Hladnjača", "no_orders_pool": "ℹ️ Trenutno nema otvorenih porudžbina u pool-u.",
        "pool_orders_title": "Prave primljene porudžbine u pool-u", "start_picking": "▶️ ZAPOČNI Pakovanje", "finish_packing": "✅ 3. ZAVRŠI Pakovanje",
        "driver_header": "🚚 Kamionska isporuka", "no_driver_orders": "ℹ️ Nema porudžbina spremnih za isporuku.", "driver_alert_title": "📢 Instant Feedback-Bridge (Glasovna poruka komercijalisti):", "driver_alert_btn": "⚡ Pošalji upozorenje komercijalisti",
        "rampe_header": "🛑 Kontrola Rampe", "no_rampe_orders": "ℹ️ Nema vraćenih kamiona za kontrolu na rampi.",
        "innendienst_header": "💼 Kancelarija: Firewall Odobrenja", "sales_header": "📱 Komercijalni Teren & Radar Signala Vozača", "no_alerts": "Nema nepročitanih upozorenja od vozača.",
        "admin_header": "👑 Admin Kontrolni Centar", "no_demands": "Nema otvorenih obaveštenja nabavci u sistemu.", "dispo_header": "⚙ Dispečer & Planiranje Kapaciteta",
        "planned_tours_title": '🗺️ Moje planirane rute (najava unapred)', "planned_tours_info": 'Ove rute je dispečer unapred isplanirao. Prikaz je demo-simulacija; ruta je spremna za isporuku tek kada roba bude pripremljena i odobrena.', "tour_order": 'Porudžbina', "tour_vehicle": 'Vozilo', "tour_stop": 'Stanica na ruti', "tour_status": 'Status rute (simulacija)', "not_set": 'Nije određeno'
    }
}

CATEGORIES_TRANS = {
    "Gemüse & Frische": {"de": "Gemüse & Frische", "ro": "Legume & Proaspete", "sr": "Povrće & Sveže"},
    "Getränke & Wein": {"de": "Getränke & Wein", "ro": "Băuturi & Vinuri", "sr": "Pića & Vina"},
    "Trockengut": {"de": "Trockengut", "ro": "Produse Uscate", "sr": "Suva Roba"},
    "Molkerei": {"de": "Molkerei", "ro": "Lactate", "sr": "Mlečni Proizvodi"},
    "Fleisch & Fisch": {"de": "Fleisch & Fisch", "ro": "Carne & Pește", "sr": "Meso & Riba"},
    "Pfandmittel": {"de": "Pfandmittel", "ro": "Ambalaje Garanție", "sr": "Ambalaža za povrat"}
}

UNITS_TRANS = {
    "Flasche": {"de": "Flasche", "ro": "Sticlă", "sr": "Boca"},
    "Sack": {"de": "Sack", "ro": "Sac", "sr": "Džak"},
    "Kiste": {"de": "Kiste", "ro": "Ladă", "sr": "Gajba"},
    "kg": {"de": "kg", "ro": "kg", "sr": "kg"},
    "kg (Catch-Weight)": {"de": "kg (Catch-Weight)", "ro": "kg (Cântărit)", "sr": "kg (Merenje)"},
    "Stück": {"de": "Stück", "ro": "Bucată", "sr": "Komad"}
}

def get_cart_qty(sku):
    return sum(item["qty"] for item in st.session_state.cart if item["sku"] == sku or item["sku"].startswith(sku))

# Produktbilder: thematisch passende öffentliche Bild-URLs für den Prototyp.
# Hinweis: Illustrationsbilder, keine verifizierten Rüther-Artikel-/Markenfotos.
PRODUCT_IMAGE_URLS = {
    # Illustrative stock photos, not verified supplier product packshots.
    "NAV-30210": "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=720&h=420&q=85", # tomatoes
    "NAV-10204": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=720&h=420&q=85", # salad
    "NAV-10205": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=720&h=420&q=85",
    "NAV-10206": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=720&h=420&q=85",
    "NAV-80105": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=720&h=420&q=85", # wine
    "NAV-70101": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=720&h=420&q=85",
    "NAV-90950": "https://images.unsplash.com/photo-1627485937980-221c88ac04f9?auto=format&fit=crop&w=720&h=420&q=85", # flour/baking
    "NAV-20101": "https://images.unsplash.com/photo-1559561853-08451507cbe7?auto=format&fit=crop&w=720&h=420&q=85", # mozzarella/cheese
    "NAV-40201": "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?auto=format&fit=crop&w=720&h=420&q=85", # beef
    "PFAND-E2": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=720&h=420&q=85", # crate
    "NAV-30211": "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?auto=format&fit=crop&w=720&h=420&q=85", # apples
    "NAV-30212": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=720&h=420&q=85", # bananas
    "NAV-30213": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=720&h=420&q=85", # potatoes
    "NAV-30214": "https://images.unsplash.com/photo-1582284540020-8acbe03f4924?auto=format&fit=crop&w=720&h=420&q=85", # peppers
    "NAV-30215": "https://images.unsplash.com/photo-1597362925123-77861d3fbac7?auto=format&fit=crop&w=720&h=420&q=85", # cucumbers
    "NAV-20102": "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?auto=format&fit=crop&w=720&h=420&q=85", # gouda/cheese
    "NAV-40202": "https://images.unsplash.com/photo-1510130387422-82bed34b37e9?auto=format&fit=crop&w=720&h=420&q=85", # fish
    "NAV-90951": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=720&h=420&q=85", # bakery
    "NAV-60101": "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=720&h=420&q=85", # passata/tomatoes
    "NAV-50101": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=720&h=420&q=85", # fries/potatoes
}

AZ_PRODUCT_CATALOG = [
    {"sku": "NAV-30210", "category": "Gemüse & Frische", "de": "Strauchtomaten Frische Class 1 (5kg Kiste)", "ro": "Roșii cu ciorchine Class 1 (Ladă 5kg)", "sr": "Paradajz na grani Class 1 (Gajba 5kg)", "price": 12.80, "unit": "Kiste", "in_stock": True},
    {"sku": "NAV-10204", "category": "Gemüse & Frische", "de": "Salatmischung Fitness (Ready-Cut 1kg)", "ro": "Amestec salată Fitness (Tăiat 1kg)", "sr": "Mešavina salate Fitness (1kg)", "price": 4.50, "unit": "kg", "in_stock": True, "is_salad": True},
    {"sku": "NAV-10205", "category": "Gemüse & Frische", "de": "Salatmischung Gourmet (Ready-Cut 1kg)", "ro": "Amestec salată Gourmet (Tăiat 1kg)", "sr": "Mešavina salate Gourmet (1kg)", "price": 5.20, "unit": "kg", "in_stock": True, "is_salad": True},
    {"sku": "NAV-10206", "category": "Gemüse & Frische", "de": "Salatmischung Toscana (Ready-Cut 1kg)", "ro": "Amestec salată Toscana (Tăiat 1kg)", "sr": "Mešavina salate Toscana (1kg)", "price": 4.90, "unit": "kg", "in_stock": True, "is_salad": True},
    {
        "sku": "NAV-80105", 
        "category": "Getränke & Wein", 
        "de": "Barolo Riserva DOCG 0.75L (Bella Italia) (28.50 €)", 
        "ro": "Vin Barolo Riserva DOCG 0.75L (28.50 €)", 
        "sr": "Vino Barolo Riserva DOCG 0.75L (28.50 €)", 
        "price": 28.50, 
        "unit": "Flasche", 
        "in_stock": False,
        "alternative_sku": "NAV-70101",
        "alternative_name": "Chianti Classico Riserva DOCG 0.75L (18.20 €)"
    },
    {"sku": "NAV-70101", "category": "Getränke & Wein", "de": "Chianti Classico Riserva DOCG 0.75L", "ro": "Vin Chianti Classico 0.75L", "sr": "Vino Chianti Classico 0.75L", "price": 18.20, "unit": "Flasche", "in_stock": True},
    {"sku": "NAV-90950", "category": "Trockengut", "de": "Weizenmehl Type 00 (25kg Sack)", "ro": "Făină de grâu Tip 00 (Sac 25kg)", "sr": "Pšenično brašno Tip 00 (25kg džak)", "price": 18.50, "unit": "Sack", "in_stock": True},
    {"sku": "NAV-20101", "category": "Molkerei", "de": "Mozzarella Fiori di Latte (1kg Block)", "ro": "Mozzarella Fiori di Latte (Bloc 1kg)", "sr": "Mocarela Fiori di Latte (Blok 1kg)", "price": 6.90, "unit": "kg", "in_stock": True},
    {"sku": "NAV-40201", "category": "Fleisch & Fisch", "de": "Rinderfilet Fresh Arg. (ca. 3kg)", "ro": "Mușchi de vită proaspăt Arg. (cca 3kg)", "sr": "Goveđi file svež Arg. (oko 3kg)", "price": 28.00, "unit": "kg (Catch-Weight)", "in_stock": True},
    {"sku": "PFAND-E2", "category": "Pfandmittel", "de": "E2-Fleischerkiste Rot", "ro": "Navetă E2 Roșie", "sr": "E2 Gajba Crvena", "price": 2.50, "unit": "Stück", "in_stock": True},
    {"sku": "NAV-30211", "category": "Gemüse & Frische", "de": "Äpfel Tafelware (6kg Kiste)", "ro": "Mere pentru consum (ladă 6kg)", "sr": "Jabuke za jelo (gajba 6kg)", "price": 14.90, "unit": "Kiste", "in_stock": True},
    {"sku": "NAV-30212", "category": "Gemüse & Frische", "de": "Bananen (18kg Karton)", "ro": "Banane (cutie 18kg)", "sr": "Banane (karton 18kg)", "price": 27.50, "unit": "Kiste", "in_stock": True},
    {"sku": "NAV-30213", "category": "Gemüse & Frische", "de": "Kartoffeln vorwiegend festkochend (10kg Sack)", "ro": "Cartofi (sac 10kg)", "sr": "Krompir (džak 10kg)", "price": 9.90, "unit": "Sack", "in_stock": True},
    {"sku": "NAV-30214", "category": "Gemüse & Frische", "de": "Rote Paprika (5kg Kiste)", "ro": "Ardei roșu (ladă 5kg)", "sr": "Crvena paprika (gajba 5kg)", "price": 16.50, "unit": "Kiste", "in_stock": True},
    {"sku": "NAV-30215", "category": "Gemüse & Frische", "de": "Salatgurken (Stück)", "ro": "Castraveți (bucată)", "sr": "Krastavci (komad)", "price": 1.20, "unit": "Stück", "in_stock": True},
    {"sku": "NAV-20102", "category": "Molkerei", "de": "Gouda Käse (1kg)", "ro": "Brânză Gouda (1kg)", "sr": "Gouda sir (1kg)", "price": 8.90, "unit": "kg", "in_stock": True},
    {"sku": "NAV-40202", "category": "Fleisch & Fisch", "de": "Lachsfilet (ca. 1kg)", "ro": "File de somon (cca 1kg)", "sr": "File lososa (oko 1kg)", "price": 21.90, "unit": "kg", "in_stock": True},
    {"sku": "NAV-90951", "category": "Trockengut", "de": "Pizzamehl Tipo 00 (10kg Sack)", "ro": "Făină pizza Tipo 00 (sac 10kg)", "sr": "Brašno za picu Tipo 00 (džak 10kg)", "price": 13.90, "unit": "Sack", "in_stock": True},
    {"sku": "NAV-60101", "category": "Trockengut", "de": "Passierte Tomaten (2.5kg Dose)", "ro": "Roșii pasate (conservă 2.5kg)", "sr": "Pasirani paradajz (konzerva 2.5kg)", "price": 4.20, "unit": "Stück", "in_stock": True},
    {"sku": "NAV-50101", "category": "Trockengut", "de": "Pommes frites (2.5kg Beutel)", "ro": "Cartofi prăjiți congelați (2.5kg)", "sr": "Pomfrit zamrznuti (2.5kg)", "price": 5.60, "unit": "Stück", "in_stock": True}
]



def catalog_product_display(name, lang="de", sku=None):
    """Return the catalog product name in the currently selected UI language."""
    for product in AZ_PRODUCT_CATALOG:
        if sku and str(product.get("sku", "")) == str(sku):
            return str(product.get(lang, product.get("de", name)))
        if str(name or "") in {str(product.get("de", "")), str(product.get("ro", "")), str(product.get("sr", ""))}:
            return str(product.get(lang, product.get("de", name)))
    return str(name or "—")


def translate_items_summary(summary, lang="de"):
    """Translate known catalog item names in a persisted order summary for the active profile language."""
    text = str(summary or "")
    # Replace longest names first to avoid partial replacements.
    for product in sorted(AZ_PRODUCT_CATALOG, key=lambda item: max(len(str(item.get(k, ""))) for k in ("de", "ro", "sr")), reverse=True):
        target = str(product.get(lang, product.get("de", "")))
        for source_lang in ("de", "ro", "sr"):
            source = str(product.get(source_lang, ""))
            if source and source in text:
                text = text.replace(source, target)
    # Translate common salad recipe details included in demo order summaries.
    detail_terms = {
        "Eisberg": {"de": "Eisberg", "ro": "salată iceberg", "sr": "ajsberg salata"},
        "Radicchio": {"de": "Radicchio", "ro": "radicchio", "sr": "radič"},
        "Karotten": {"de": "Karotten", "ro": "morcovi", "sr": "šargarepa"},
        "legume întregi": {"de": "ganzes Gemüse", "ro": "legume întregi", "sr": "celo povrće"},
    }
    for source, translations in detail_terms.items():
        target = translations.get(lang, source)
        text = text.replace(source, target)
    # Translate common substitute annotations stored in demo order summaries.
    annotation_terms = {
        "Alternative (Demo-Preis)": {"de": "Ersatzartikel (Demo-Preis)", "ro": "Produs înlocuitor (preț demo)", "sr": "Zamenski artikal (demo cena)"},
        "Alternative – vergleichbarer Artikel": {"de": "Ersatz – vergleichbarer Artikel", "ro": "Înlocuitor – produs comparabil", "sr": "Zamena – uporediv proizvod"},
        "Alternative A – vergleichbarer Artikel": {"de": "Ersatz A – vergleichbarer Artikel", "ro": "Înlocuitor A – produs comparabil", "sr": "Zamena A – uporediv proizvod"},
        "Alternative B – andere Marke": {"de": "Ersatz B – andere Marke", "ro": "Înlocuitor B – altă marcă", "sr": "Zamena B – drugi brend"},
        "Alternative C – ähnliche Größe": {"de": "Ersatz C – ähnliche Größe", "ro": "Înlocuitor C – dimensiune similară", "sr": "Zamena C – slična veličina"},
    }
    for source, translations in annotation_terms.items():
        text = text.replace(source, translations.get(lang, translations["de"]))
    return text


def rep_text(key, lang="de"):
    phrases = {
      "packed": ("Ersatz provisorisch gepackt und nicht freigegeben. Keine automatische Kundenzustimmung.", "Înlocuitorul a fost ambalat provizoriu și nu este aprobat. Acceptul clientului nu este presupus.", "Zamena je privremeno spakovana i nije odobrena. Prihvatanje kupca se ne podrazumeva."),
      "case": ("Ersatzfall", "Caz de înlocuire", "Slučaj zamene"),
      "status": ("Status", "Stare", "Status"),
      "waiting": ("Wartet auf Kundenentscheidung", "Se așteaptă decizia clientului", "Čeka se odluka kupca"),
      "heading": ("⚠️ Ersatzfälle – Kundenantwort und Dispositionsstatus", "⚠️ Cazuri de înlocuire – răspunsul clientului și statusul dispeceratului", "⚠️ Slučajevi zamene – odgovor kupca i status dispečera"),
      "none": ("Keine offenen Ersatzartikel-Entscheidungen.", "Nu există decizii deschise privind înlocuitorii.", "Nema otvorenih odluka o zamenskim artiklima."),
      "rejected": ("⛔ KUNDENENTSCHEIDUNG: ERSATZ ABGELEHNT", "⛔ DECIZIA CLIENTULUI: ÎNLOCUITOR RESPINS", "⛔ ODLUKA KUPCA: ZAMENA ODBIJENA"),
      "accepted": ("✅ KUNDENENTSCHEIDUNG: ERSATZ ANGENOMMEN", "✅ DECIZIA CLIENTULUI: ÎNLOCUITOR ACCEPTAT", "✅ ODLUKA KUPCA: ZAMENA PRIHVAĆENA"),
      "open": ("⏳ KUNDENENTSCHEIDUNG: NOCH OFFEN", "⏳ DECIZIA CLIENTULUI: ÎNCĂ DESCHISĂ", "⏳ ODLUKA KUPCA: JOŠ NIJE DONETA"),
      "future": ("Ersatz vor Tourfreigabe herausnehmen und Originalartikel für spätere Lieferung vormerken.", "Scoateți înlocuitorul înainte de aprobarea cursei și rezervați articolul original pentru livrare ulterioară.", "Ukloniti zamenu pre odobrenja ture i označiti original za kasniju isporuku."),
      "other": ("Ersatz herausnehmen und Kundenwunsch für einen anderen Ersatz bearbeiten.", "Scoateți înlocuitorul și procesați cererea clientului pentru altă alternativă.", "Ukloniti zamenu i obraditi zahtev kupca za drugu zamenu."),
      "check": ("Ersatz nicht als bestätigt behandeln; vor Tourfreigabe prüfen.", "Nu considerați înlocuitorul confirmat; verificați înainte de aprobarea cursei.", "Ne smatrati zamenu potvrđenom; proveriti pre odobrenja ture."),
      "accept_next": ("Kundenannahme dokumentiert; Disposition prüft die Tourfreigabe.", "Acceptul clientului a fost înregistrat; dispeceratul verifică aprobarea cursei.", "Prihvatanje kupca je evidentirano; dispečer proverava odobrenje ture."),
      "open_next": ("Vor Tourfreigabe aktiv entscheiden; keine automatische Kundenzustimmung annehmen.", "Decideți înainte de aprobarea cursei; nu presupuneți acceptul clientului.", "Odlučiti pre odobrenja ture; ne pretpostavljati prihvatanje kupca."),
      "original": ("Originalartikel", "Articol original", "Originalni artikal"),
      "alternative": ("Vorgeschlagener Ersatz", "Înlocuitor propus", "Predložena zamena"),
      "next": ("Nächster Schritt für die Disposition", "Următorul pas pentru dispecerat", "Sledeći korak za dispečera"),
      "reply": ("Kundenantwort", "Răspunsul clientului", "Odgovor kupca"),
      "pending": ("Dispositionsstatus: Noch nicht entschieden", "Status dispecerat: încă nedecis", "Status dispečera: još nije odlučeno"),
      "decision": ("Disposition-Entscheidung für Ersatzfall", "Decizia dispeceratului pentru cazul de înlocuire", "Odluka dispečera za slučaj zamene"),
      "opt0": ("Ersatz mit Tour ausliefern (Disposition entscheidet)", "Livrați înlocuitorul în cursă (decide dispeceratul)", "Isporučiti zamenu u turi (odlučuje dispečer)"),
      "opt1": ("Ersatz herausnehmen – Original für spätere Lieferung vormerken", "Scoateți înlocuitorul – originalul pentru livrare ulterioară", "Ukloniti zamenu – original za kasniju isporuku"),
      "opt2": ("Ersatz herausnehmen – Kunde soll anderen Ersatz wählen", "Scoateți înlocuitorul – clientul va alege altă alternativă", "Ukloniti zamenu – kupac bira drugu zamenu"),
      "save": ("Entscheidung dokumentieren", "Înregistrează decizia", "Evidentiraj odluku"),
      "saved": ("Dispositionsentscheidung dokumentiert; keine Kundenzustimmung.", "Decizia dispeceratului este înregistrată; nu reprezintă acceptul clientului.", "Odluka dispečera je evidentirana; ne predstavlja prihvatanje kupca."),
      "completed": ("Abgeschlossene Dispositionsentscheidungen anzeigen", "Afișează deciziile finalizate", "Prikaži završene odluke dispečera"),
      "all": ("Alle Ersatzfälle anzeigen", "Afișează toate cazurile de înlocuire", "Prikaži sve slučajeve zamene"),
      "order": ("Auftrag", "Comandă", "Porudžbina"),
      "dispo_answer": ("Dispositionsentscheidung", "Decizia dispeceratului", "Odluka dispečera"),
      "by": ("Entschieden von", "Decis de", "Odlučio"),
      "at": ("am", "la", "dana"),
      "unknown": ("Offen", "Deschis", "Otvoreno")
    }
    return phrases[key][{"de":0,"ro":1,"sr":2}.get(lang,0)]


def replacement_label_display(value, lang="de"):
    labels = {
        "Alternative A – vergleichbarer Artikel": {"de": "Alternative A – vergleichbarer Artikel", "ro": "Alternativa A – produs comparabil", "sr": "Alternativa A – uporediv proizvod"},
        "Alternative B – andere Marke": {"de": "Alternative B – andere Marke", "ro": "Alternativa B – altă marcă", "sr": "Alternativa B – drugi brend"},
        "Alternative C – ähnliche Größe": {"de": "Alternative C – ähnliche Größe", "ro": "Alternativa C – dimensiune similară", "sr": "Alternativa C – slična veličina"},
    }
    return labels.get(str(value), {}).get(lang, str(value or "—"))

ALL_ROLE_PROFILES = {
    "1. Gastronomie-Kunde": [
        {"name": "Marco Rossi (Trattoria Bella)", "lang": "de", "flag": "🇩🇪"},
        {"name": "Ionel Popescu (Gastro RO)", "lang": "ro", "flag": "🇷🇴"},
        {"name": "Dragan Petrović (Restoran SR)", "lang": "sr", "flag": "🇷🇸"}
    ],
    "2. Kommissionierer (Pool-Pick)": [
        {"name": "Petruta Guta", "lang": "de", "flag": "🇩🇪"},
        {"name": "Ionel Popescu (Comisionar)", "lang": "ro", "flag": "🇷🇴"},
        {"name": "Dragan Petrović (Magacin)", "lang": "sr", "flag": "🇷🇸"}
    ],
    "3. Auslieferungs-Fahrer": [
        {"name": "Markus Weber (Fahrer DE)", "lang": "de", "flag": "🇩🇪"},
        {"name": "Ionel Popescu (Șofer RO)", "lang": "ro", "flag": "🇷🇴"},
        {"name": "Dragan Petrović (Vozač SR)", "lang": "sr", "flag": "🇷🇸"}
    ],
    "4. Rampen-Kontrolleur": [
        {"name": "Friedrich Merz", "lang": "de", "flag": "🇩🇪"},
        {"name": "Ionel Popescu (Control Rampa)", "lang": "ro", "flag": "🇷🇴"},
        {"name": "Dragan Petrović (Kontrola Rampe)", "lang": "sr", "flag": "🇷🇸"}
    ],
    "5. Innendienst & Verkauf": [
        {"name": "Anna Nass", "lang": "de", "flag": "🇩🇪"},
        {"name": "Elena Popescu (Vânzări)", "lang": "ro", "flag": "🇷🇴"},
        {"name": "Milica Petrović (Prodaja)", "lang": "sr", "flag": "🇷🇸"}
    ],
    "6. Schichtleitung & Disposition": [
        {"name": "Paco Rabanne", "lang": "de", "flag": "🇩🇪"}
    ],
    "7. Vertrieb & Außendienst": [
        {"name": "Dominique Kieburg (Gebietsleiter)", "lang": "de", "flag": "🇩🇪"}
    ],
    "8. Admin & Pitch-Governance": [
        {"name": "Ad Mina", "lang": "de", "flag": "👑"}
    ]
}

# ==============================================================================
# PERSÖNLICHE KONTEN (DEMO) – separate SQLite-Datei, Originaldatei bleibt erhalten
# ==============================================================================
AUTH_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gastrolingua_konten_demo.sqlite3")
ROLE_MAP = {
    "Gastronom": "1. Gastronomie-Kunde",
    "Kommissionär": "2. Kommissionierer (Pool-Pick)",
    "Fahrer": "3. Auslieferungs-Fahrer",
    "Rampen-Kontrolleur": "4. Rampen-Kontrolleur",
    "Innendienst": "5. Innendienst & Verkauf",
    "Disposition": "6. Schichtleitung & Disposition",
    "Außendienst": "7. Vertrieb & Außendienst",
    "Admin": "8. Admin & Pitch-Governance",
}

def auth_db():
    con = sqlite3.connect(AUTH_DB)
    con.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL, role TEXT NOT NULL, lang TEXT NOT NULL, restaurant TEXT DEFAULT '', password_hash TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, is_owner INTEGER NOT NULL DEFAULT 0)")
    con.commit()
    return con

def pw_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 240000).hex()
    return f"{salt}${digest}"

def pw_ok(password, stored):
    try:
        salt, digest = stored.split('$', 1)
        return secrets.compare_digest(pw_hash(password, salt).split('$',1)[1], digest)
    except Exception:
        return False

def seed_demo_users():
    con = auth_db()
    if con.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        # Einmalige DEMO-Zugangsdaten, nach Möglichkeit vor echtem Einsatz ändern.
        rows = [
            ('admin','Ad Mina','Admin','de','', 'KiBurg-Demo-Admin-26!',0),
            ('hirschen','Brauhaus zum Hirschen','Gastronom','de','Brauhaus zum Hirschen','Hirschen-Demo-26!',1),
            ('bella','Ristorante Bella Italia','Gastronom','de','Ristorante Bella Italia','Bella-Demo-26!',1),
            ('sarajevo','Restaurant Sarajevo','Gastronom','sr','Restaurant Sarajevo','Sarajevo-Demo-26!',1),
            ('petruta','Petruta Guta','Kommissionär','ro','','Petruta-Demo-26!',0),
            ('friedrich','Friedrich Merz','Rampen-Kontrolleur','de','','Friedrich-Demo-26!',0),
            ('milan','Milan Petrovic','Kommissionär','sr','','Milan-Demo-26!',0),
            ('guenther','Zoka Gredeljevic','Fahrer','de','','Guenther-Demo-26!',0),
            ('nicolae','Nicolae Guta','Fahrer','ro','','Nicolae-Demo-26!',0),
            ('zoka','Zoka Gredeljevic','Fahrer','sr','','Zoka-Demo-26!',0),
            ('dominik-au','Dominique Kieburg (Außendienst)','Außendienst','de','','Aussendienst-Demo-26!',0),
            ('dominik-in','Dominique Kieburg (Innendienst)','Innendienst','de','','Innendienst-Demo-26!',0),
        ]
        for username,name,role,lang,restaurant,password,is_owner in rows:
            con.execute('INSERT OR IGNORE INTO users(username,display_name,role,lang,restaurant,password_hash,active,is_owner) VALUES(?,?,?,?,?,?,1,?)',
                        (username,name,role,lang,restaurant,pw_hash(password),is_owner))
    con.commit(); con.close()

seed_demo_users()

# Schlanke Präsentationsauswahl: eine Identität pro Fachrolle. Die Sprache wird
# separat in der Sidebar gewählt; weitere Konten bleiben in der Demo-Datenbank erhalten.
PRESENTATION_ACCOUNT_ORDER = [
    "admin", "hirschen", "bella", "sarajevo",
    "kunde-tour1-2", "kunde-tour1-3", "kunde-tour2-2",
    "petruta", "zoka", "nicolae",
    "friedrich", "dominik-in", "dispo-demo", "dominik-au",
]

def ensure_presentation_accounts():
    """Ergänzt fehlende Demo-Zugänge idempotent, ohne bestehende Konten zu löschen."""
    con = auth_db()
    rows = [
        ("rampen-demo", "Friedrich Merz", "Rampen-Kontrolleur", "de", "", "Rampen-Demo-26!", 0),
        ("dispo-demo", "Paco Rabanne", "Disposition", "de", "", "Disposition-Demo-26!", 0),
        ("bella", "Ristorante Bella Italia", "Gastronom", "de", "Ristorante Bella Italia", "Bella-Demo-26!", 1),
        ("sarajevo", "Restaurant Sarajevo", "Gastronom", "sr", "Restaurant Sarajevo", "Sarajevo-Demo-26!", 1),
        ("kunde-tour1-2", "Trattoria am Markt", "Gastronom", "de", "Trattoria am Markt", "Trattoria-Demo-26!", 0),
        ("kunde-tour1-3", "Hotel Rheinblick", "Gastronom", "de", "Hotel Rheinblick", "Rheinblick-Demo-26!", 0),
        ("kunde-tour2-2", "Restoran Dunav", "Gastronom", "sr", "Restoran Dunav", "Dunav-Demo-26!", 0),
        ("nicolae", "Nicolae Guta", "Fahrer", "ro", "", "Nicolae-Demo-26!", 0),
    ]
    for username, name, role, lang, restaurant, password, is_owner in rows:
        con.execute(
            "INSERT OR IGNORE INTO users(username,display_name,role,lang,restaurant,password_hash,active,is_owner) VALUES(?,?,?,?,?,?,1,?)",
            (username, name, role, lang, restaurant, pw_hash(password), is_owner),
        )
    # Nur die für die Präsentation ausgewählten Demo-Konten aktualisieren.
    # Bestehende Bestellungen und andere Konten bleiben unberührt.
    con.execute("UPDATE users SET display_name='Ad Mina', role='Admin' WHERE username='admin'")
    con.execute("UPDATE users SET display_name='Petruta Guta', role='Kommissionär' WHERE username='petruta'")
    con.execute("UPDATE users SET display_name='Friedrich Merz', role='Rampen-Kontrolleur' WHERE username='friedrich'")
    con.execute("UPDATE users SET display_name='Zoka Gredeljevic', role='Fahrer' WHERE username='zoka'")
    con.execute("UPDATE users SET display_name='Anna Nass', role='Innendienst' WHERE username='dominik-in'")
    con.execute("UPDATE users SET display_name='Paco Rabanne', role='Disposition' WHERE username='dispo-demo'")
    con.commit()
    con.close()

ensure_presentation_accounts()

def render_login():
    # Präsentationsmodus: vorbereitete Demo-Konten ohne Passwort auswählbar.
    st.title('🏰 GastroLingua – Präsentationsmodus')
    st.caption('Demo-Konto auswählen und direkt starten. Kein Passwort erforderlich.')
    con = auth_db()
    all_rows = con.execute("SELECT username,display_name,role,lang,restaurant,is_owner FROM users WHERE active=1").fetchall()
    con.close()
    row_by_username = {r[0]: r for r in all_rows}
    rows = [row_by_username[u] for u in PRESENTATION_ACCOUNT_ORDER if u in row_by_username]
    if not rows:
        st.error('Keine aktiven Demo-Konten gefunden.')
        st.stop()
    labels = {r[0]: f"{r[1]} — {r[2]}" + (f" · {r[4]}" if r[4] else "") for r in rows}
    chosen = st.selectbox('Mit welchem vorbereiteten Konto möchtest du präsentieren?', [r[0] for r in rows], format_func=lambda x: labels[x], key='demo_start_account')
    if st.button('🚀 Demo starten', type='primary', use_container_width=True):
        row = next(r for r in rows if r[0] == chosen)
        st.session_state.auth_user = {'username':row[0], 'name':row[1], 'role':row[2], 'lang':row[3], 'restaurant':row[4], 'is_owner':bool(row[5])}
        st.session_state.demo_mode = True
        st.rerun()
    st.info('Dieser vereinfachte Zugang ist nur für die lokale Präsentation gedacht. Für einen echten Produktivbetrieb muss die Anmeldung wieder abgesichert werden.')
    st.stop()

if 'auth_user' not in st.session_state:
    render_login()

_LOCAL_SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "secrets.toml")
_HOME_SECRETS_FILE = os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml")

def _is_valid_token_format(tok: str) -> bool:
    t = str(tok or "").strip()
    if not t or len(t) < 35:
        return False
    upper = t.upper()
    if "DEIN-ECHTER-TOKEN" in upper or "HIER-TOKEN" in upper or "PLACEHOLDER" in upper:
        return False
    return True

# Clean up any leftover placeholder secrets.toml in home or project dir automatically
for _sfile in (_HOME_SECRETS_FILE, _LOCAL_SECRETS_FILE):
    try:
        if os.path.exists(_sfile):
            with open(_sfile, "r", encoding="utf-8") as _sf:
                _scontent = _sf.read()
            if "DEIN-ECHTER-TOKEN" in _scontent.upper() or "HIER-TOKEN" in _scontent.upper():
                os.remove(_sfile)
    except Exception:
        pass

def save_local_hubspot_token(token_val: str):
    """Persist token locally in SQLite and .streamlit/secrets.toml so the user never has to use Terminal."""
    clean_tok = str(token_val or "").strip()
    conn = sqlite3.connect(OFFLINE_DB)
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS app_settings (k TEXT PRIMARY KEY, v TEXT)")
        if clean_tok:
            conn.execute("INSERT OR REPLACE INTO app_settings (k, v) VALUES ('hubspot_token', ?)", (clean_tok,))
        else:
            conn.execute("DELETE FROM app_settings WHERE k='hubspot_token'")
        conn.commit()
    finally:
        conn.close()
    for _target_secret in (_LOCAL_SECRETS_FILE, _HOME_SECRETS_FILE):
        try:
            if clean_tok:
                os.makedirs(os.path.dirname(_target_secret), exist_ok=True)
                with open(_target_secret, "w", encoding="utf-8") as sf:
                    sf.write(f'HUBSPOT_ACCESS_TOKEN = "{clean_tok}"\n')
            elif os.path.exists(_target_secret):
                os.remove(_target_secret)
        except Exception:
            pass

def load_saved_db_token() -> str:
    try:
        conn = sqlite3.connect(OFFLINE_DB)
        conn.execute("CREATE TABLE IF NOT EXISTS app_settings (k TEXT PRIMARY KEY, v TEXT)")
        row = conn.execute("SELECT v FROM app_settings WHERE k='hubspot_token'").fetchone()
        conn.close()
        val = str(row[0] or "").strip() if row else ""
        return val if _is_valid_token_format(val) else ""
    except Exception:
        return ""

def load_hubspot_token():
    """Load valid credentials from local DB, Streamlit secrets, or environment."""
    db_tok = load_saved_db_token()
    if db_tok:
        return db_tok
    token = ""
    try:
        token = st.secrets.get("HUBSPOT_ACCESS_TOKEN", "")
    except Exception:
        token = ""
    if not token:
        token = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
    token = str(token or "").strip()
    return token if _is_valid_token_format(token) else ""

_cloud_secret_token = ""
try:
    _cloud_secret_token = str(st.secrets.get("HUBSPOT_ACCESS_TOKEN", "") or "").strip()
except Exception:
    _cloud_secret_token = ""
if not _cloud_secret_token:
    _cloud_secret_token = str(os.getenv("HUBSPOT_ACCESS_TOKEN", "") or "").strip()
if not _is_valid_token_format(_cloud_secret_token):
    _cloud_secret_token = ""

_server_hubspot_token = load_hubspot_token()
if _server_hubspot_token:
    st.session_state.hubspot_token = _server_hubspot_token
elif "hubspot_token" not in st.session_state or not _is_valid_token_format(st.session_state.hubspot_token):
    st.session_state.hubspot_token = "" 

if "cart" not in st.session_state:
    st.session_state.cart = []

if "active_orders" not in st.session_state:
    st.session_state.active_orders = {}
if "gps_demo_step" not in st.session_state:
    st.session_state.gps_demo_step = 0
if "replacement_cases" not in st.session_state:
    st.session_state.replacement_cases = {}

# HubSpot-Connector wird nach der lokalen Token-Eingabe initialisiert.

# ==============================================================================
# 5. SIDEBAR
# ==============================================================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.markdown("🏰")
    st.title("KI-BURG Control")
    st.caption("Version 30.9 | Stabilisierung Retouren & Außendienst")
    
    auth_user = st.session_state.auth_user
    # In der Demo kann die präsentierende Person Konto und Sprache jederzeit ohne erneute Anmeldung wechseln.
    if st.session_state.get('demo_mode', True):
        con_demo = auth_db()
        all_demo_rows = con_demo.execute('SELECT username,display_name,role,lang,restaurant,is_owner FROM users WHERE active=1').fetchall()
        con_demo.close()
        demo_by_username = {r[0]: r for r in all_demo_rows}
        demo_rows = [demo_by_username[u] for u in PRESENTATION_ACCOUNT_ORDER if u in demo_by_username]
        demo_labels = {r[0]: f"{r[1]} — {r[2]}" + (f" · {r[4]}" if r[4] else "") for r in demo_rows}
        current_user_key = auth_user['username'] if any(r[0] == auth_user['username'] for r in demo_rows) else demo_rows[0][0]
        st.markdown('### 🎬 Präsentationssteuerung')
        demo_c1, demo_c2 = st.columns([3, 2])
        with demo_c1:
            picked_user = st.selectbox('Demo-Konto', [r[0] for r in demo_rows], index=[r[0] for r in demo_rows].index(current_user_key), format_func=lambda x: demo_labels[x], key='demo_account_switch')
        with demo_c2:
            lang_options = ['de', 'ro', 'sr']
            current_lang = auth_user.get('lang', 'de') if auth_user.get('lang') in lang_options else 'de'
            picked_lang = st.selectbox('Sprache / Limbă / Jezik', lang_options, index=lang_options.index(current_lang), format_func=lambda x: {'de':'🇩🇪 Deutsch','ro':'🇷🇴 Română','sr':'🇷🇸 Srpski'}[x], key='demo_language_switch')
        picked_row = next(r for r in demo_rows if r[0] == picked_user)
        if picked_user != auth_user['username'] or picked_lang != auth_user.get('lang'):
            st.session_state.auth_user = {'username':picked_row[0], 'name':picked_row[1], 'role':picked_row[2], 'lang':picked_lang, 'restaurant':picked_row[4], 'is_owner':bool(picked_row[5])}
            # Keep the selected language even when switching accounts during the presentation.
            st.rerun()
        auth_user = st.session_state.auth_user
    selected_role_key = ROLE_MAP.get(auth_user['role'], "1. Gastronomie-Kunde")
    active_lang = auth_user['lang'] if auth_user['lang'] in LANG_PACK else 'de'
    if active_lang not in LANG_PACK:
        active_lang = 'de'
    user = {"name": auth_user['name'], "lang": active_lang, "flag": {"de":"🇩🇪","ro":"🇷🇴","sr":"🇷🇸","it":"🇮🇹"}.get(auth_user['lang'],"🌐"), "restaurant": auth_user.get('restaurant','')}
    L = LANG_PACK[active_lang]
    if st.button('Zur Kontoauswahl'):
        st.session_state.pop('auth_user', None)
        st.rerun()
    if auth_user['role'] in ('Gastronom','Admin'):
        with st.expander('👥 Mitarbeiter verwalten', expanded=False):
            st.caption('Restaurantmitarbeiter werden dem Restaurant zugeordnet; ihre Sprache ist unabhängig von der Sprache des Inhabers.')
            con = auth_db()
            if auth_user['role'] == 'Admin':
                restaurant_options = ['Brauhaus zum Hirschen','Ristorante Bella Italia','Restaurant Sarajevo']
            else:
                restaurant_options = [auth_user.get('restaurant') or auth_user['name']]
            chosen_restaurant = st.selectbox('Restaurant', restaurant_options, key='manage_restaurant')
            if auth_user['role'] == 'Admin' or chosen_restaurant == auth_user.get('restaurant'):
                with st.form('add_restaurant_employee'):
                    emp_name = st.text_input('Name des Mitarbeiters')
                    emp_username = st.text_input('Neuer Benutzername').strip().lower()
                    emp_role = st.selectbox('Rolle', ['Gastronom','Küchenchef','Servicekraft'])
                    emp_lang = st.selectbox('Sprache', ['de','ro','sr'], format_func=lambda x: {'de':'Deutsch','ro':'Rumänisch','sr':'Serbisch'}[x])
                    emp_password = st.text_input('Startpasswort (mindestens 10 Zeichen)', type='password')
                    create_emp = st.form_submit_button('Mitarbeiterkonto anlegen')
                if create_emp:
                    if not emp_name.strip() or not emp_username or len(emp_password) < 10:
                        st.error('Bitte Name, Benutzername und ein Passwort mit mindestens 10 Zeichen eingeben.')
                    else:
                        try:
                            con.execute('INSERT INTO users(username,display_name,role,lang,restaurant,password_hash,active,is_owner) VALUES(?,?,?,?,?,?,1,0)',
                                        (emp_username,emp_name.strip(), 'Gastronom' if emp_role=='Gastronom' else emp_role, emp_lang, chosen_restaurant, pw_hash(emp_password)))
                            con.commit(); st.success('Mitarbeiterkonto angelegt.'); st.rerun()
                        except sqlite3.IntegrityError:
                            st.error('Dieser Benutzername ist bereits vergeben.')
                people = con.execute('SELECT username,display_name,role,lang,active FROM users WHERE restaurant=? ORDER BY display_name',(chosen_restaurant,)).fetchall()
                if people:
                    st.write('**Konten dieses Restaurants**')
                    for person in people:
                        c1,c2=st.columns([4,1]); c1.write(f"{person[1]} · {person[0]} · {person[2]} · {person[3].upper()} · {'aktiv' if person[4] else 'gesperrt'}")
                        if person[0] != auth_user['username'] and c2.button('Sperren' if person[4] else 'Aktivieren', key='toggle_'+person[0]):
                            con.execute('UPDATE users SET active=? WHERE username=?',(0 if person[4] else 1,person[0])); con.commit(); st.rerun()
            con.close()
    
    st.divider()
    st.write(f"**{L['logged_in']}** {user['name']}")
    st.write(f"**{L['sys_lang']}** `{active_lang.upper()}`")
    
    st.divider()
    if st.button("🧹 Demo-Pool / Speicher leeren"):
        if st.session_state.hubspot_token:
            _cleanup_hs = HubSpotAPIConnector(st.session_state.hubspot_token)
            _cleanup_hs.cleanup_demo_crm_data()
        reset_conn = sqlite3.connect(OFFLINE_DB)
        try:
            with reset_conn:
                archive_demo_tasks(reset_conn)
                reset_conn.execute("DELETE FROM hubspot_demo_tasks")
                reset_conn.execute("DELETE FROM hubspot_pending_completion")
                reset_conn.execute("DELETE FROM demand_reports")
                reset_conn.execute("CREATE TABLE IF NOT EXISTS created_demo_deals (deal_id TEXT PRIMARY KEY, deal_name TEXT)")
                reset_conn.execute("DELETE FROM created_demo_deals")
        finally:
            reset_conn.close()
        try:
            tour_reset_conn = auth_db()
            with tour_reset_conn:
                tour_reset_conn.execute("CREATE TABLE IF NOT EXISTS order_tour_assignments (order_id TEXT PRIMARY KEY, customer TEXT NOT NULL, tour_id TEXT NOT NULL, vehicle TEXT NOT NULL, driver TEXT NOT NULL, stop_order INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'Geplant', updated_at TEXT NOT NULL)")
                tour_reset_conn.execute("DELETE FROM order_tour_assignments")
            tour_reset_conn.close()
        except Exception:
            pass
        st.session_state.active_orders = {}
        st.session_state.cart = []
        st.session_state.replacement_cases = {}
        st.session_state.demo_tours = {}
        st.session_state.demo_vehicle_status = {"LKW 01": "Bereit", "LKW 02": "Bereit", "LKW 03": "Bereit"}
        st.toast("🧹 Demo-Speicher & HubSpot-Testaufträge bereinigt!", icon="🧹")
        st.rerun()

    st.divider()
    _is_cloud_hosted = bool(_cloud_secret_token) and not os.path.exists(_LOCAL_SECRETS_FILE) and not os.path.exists(_HOME_SECRETS_FILE) and not load_saved_db_token()
    if _is_cloud_hosted:
        # Running in Streamlit Cloud with Secrets configured -> completely hide token UI for examiners
        st.success("🟢 HubSpot Live-Verbindung aktiv (Token sicher hinterlegt)")
    else:
        with st.expander("🔑 HubSpot-Token & Verbindung", expanded=not bool(st.session_state.hubspot_token)):
            token_input = st.text_input(
                "HubSpot Private-App-Token",
                value=st.session_state.hubspot_token,
                type="password",
                placeholder="pat-eu1-...",
                help="Token einmalig einfügen und auf Speichern klicken. Bleibt auch nach Neustart gespeichert."
            )
            tc1, tc2 = st.columns(2)
            if tc1.button("💾 Dauerhaft speichern", use_container_width=True):
                clean_tok = (token_input or "").strip()
                save_local_hubspot_token(clean_tok)
                st.session_state.hubspot_token = clean_tok
                if clean_tok:
                    try:
                        test_r = requests.get(
                            "https://api.hubapi.com/crm/v3/pipelines/deals",
                            headers={"Authorization": f"Bearer {clean_tok}", "Content-Type": "application/json"},
                            timeout=8,
                        )
                        if test_r.status_code == 200:
                            st.session_state["hs_token_check_msg"] = ("ok", "✅ Token gespeichert & von HubSpot bestätigt!")
                        else:
                            st.session_state["hs_token_check_msg"] = ("err", f"❌ Token gespeichert, aber HubSpot meldet HTTP {test_r.status_code}. Bitte prüfen, ob der Token mit 'pat-eu1-' beginnt.")
                    except Exception as _te:
                        st.session_state["hs_token_check_msg"] = ("err", f"⚠️ Gespeichert, Verbindungstest fehlgeschlagen: {_te}")
                else:
                    st.session_state["hs_token_check_msg"] = ("err", "Token wurde gelöscht.")
                st.rerun()
            if tc2.button("🗑️ Token löschen", use_container_width=True):
                save_local_hubspot_token("")
                st.session_state.hubspot_token = ""
                st.session_state.pop("hs_token_check_msg", None)
                st.rerun()
            _chk = st.session_state.get("hs_token_check_msg")
            if _chk:
                if _chk[0] == "ok":
                    st.success(_chk[1])
                else:
                    st.error(_chk[1])
        if st.session_state.hubspot_token:
            st.success("🟢 HubSpot-Token dauerhaft gespeichert")
        else:
            st.warning("Demo-Modus: Kein HubSpot-Token gespeichert.")

    hubspot = HubSpotAPIConnector(st.session_state.hubspot_token)
with sqlite3.connect(OFFLINE_DB) as _completion_conn:
    _has_pending_completion = _completion_conn.execute(
        "SELECT 1 FROM hubspot_pending_completion LIMIT 1"
    ).fetchone()
_completion_conn.close()
if _has_pending_completion and st.sidebar.button("HubSpot-Abschluss erneut senden"):
    sync_task_completion(hubspot)
    st.rerun()


_pending_office_stages = [
    deal for deal in st.session_state.active_orders.values()
    if deal.get("hubspot_office_stage_pending")
]
if _pending_office_stages and st.sidebar.button("HubSpot-Phase erneut senden"):
    for _pending_deal in _pending_office_stages:
        sync_office_stage(hubspot, _pending_deal)
    st.rerun()

# BANNER
st.markdown(f"""
<div class="main-header">
    <h2 style="margin:0;">🏰 KI-BURG GastroLingua Platform</h2>
    <p style="margin:0;">Rolle: <b>{selected_role_key}</b> | {L['logged_in']} {user['flag']} {user['name']} | Restaurant: <b>{user.get('restaurant','') or 'KI-BURG intern'}</b> | {L['active_orders_cnt']} <b>{len(st.session_state.active_orders)}</b></p>
</div>
""", unsafe_allow_html=True)

# LIVE HUBSPOT CRM-MONITOR (für Prüfer & Dozenten ohne eigenen HubSpot-Login)
with st.expander("🔗 Live HubSpot CRM-Monitor (Echtzeit-Dealphasen & Aufgaben für Prüfer)", expanded=False):
    st.caption(
        "Echtzeit-Einblick in das verknüpfte HubSpot-Demoportal über die REST-API. "
        "Jeder in GastroLingua ausgelöste Prozessschritt aktualisiert sofort die Dealphase bzw. Aufgabe in HubSpot und wird hier ohne eigenen HubSpot-Login live angezeigt."
    )
    if not hubspot.token:
        st.warning("Kein HubSpot-Token konfiguriert. Bitte HUBSPOT_ACCESS_TOKEN in den Secrets hinterlegen.")
    else:
        mon_c1, mon_c2 = st.columns([1, 4])
        with mon_c1:
            st.button("🔄 Live-Status aktualisieren", key="hs_monitor_refresh", use_container_width=True)
        with mon_c2:
            st.caption("Tipp: Nach einer Bestellung, Kommissionierung, Auslieferung oder Rampenprüfung hier aktualisieren, um den Phasenwechsel in HubSpot live zu sehen.")
        tab_hs_deals, tab_hs_tasks = st.tabs(["📊 Live-Deals & Dealphasen in HubSpot", "✅ Live-Aufgaben in HubSpot"])
        with tab_hs_deals:
            live_deals_res = hubspot.fetch_live_deals(limit=15)
            if live_deals_res.get("status") == "SUCCESS":
                if live_deals_res["deals"]:
                    st.dataframe(live_deals_res["deals"], use_container_width=True, hide_index=True)
                else:
                    st.info("Aktuell sind noch keine Deals im HubSpot-Demoportal vorhanden. Erstelle im Kundenportal eine Bestellung, um den ersten Deal live anzulegen.")
            else:
                st.warning(f"HubSpot-Deals konnten gerade nicht geladen werden: {live_deals_res.get('msg', '')}")
        with tab_hs_tasks:
            live_tasks_res = hubspot.fetch_live_tasks(limit=15)
            if live_tasks_res.get("status") == "SUCCESS":
                if live_tasks_res["tasks"]:
                    st.dataframe(live_tasks_res["tasks"], use_container_width=True, hide_index=True)
                else:
                    st.info("Aktuell sind noch keine Aufgaben im HubSpot-Demoportal vorhanden.")
            else:
                st.warning(f"HubSpot-Aufgaben konnten gerade nicht geladen werden: {live_tasks_res.get('msg', '')}")


# ==============================================================================
# 6. OPERATIVE MODULE
# ==============================================================================

# ROLLE 1: KUNDE (BESTELLUNG ERZEUGEN)
if "1. Gastro" in selected_role_key:
    st.subheader(L["kundenportal_title"])
    st.info(L["countdown"])
    
    catalog_col, cart_col = st.columns([2.35, 1], gap="large")
    with catalog_col:
        tab_voice, tab_cat, tab_pfand, tab_orders = st.tabs([L["tab_voice"], L["tab_cat"], L["tab_pfand"], {"de":"🧾 Meine Bestellungen", "ro":"🧾 Comenzile mele", "sr":"🧾 Moje porudžbine"}[active_lang]])
    
        with tab_voice:
            st.write(f"### {L['voice_header']}")
            voice_ui = {
                "de": {
                    "caption": "Bestellung aufnehmen oder als Text eingeben. Die Erkennung läuft lokal auf diesem Mac.",
                    "record": "🎙️ Bestellung aufnehmen",
                    "transcribe": "🎧 Aufnahme in Text umwandeln",
                    "spinner": "Lokale Spracherkennung läuft (der erste Start kann länger dauern) …",
                    "success": "Aufnahme verarbeitet. Bitte den erkannten Text prüfen, bevor Produkte übernommen werden.",
                    "language": "Erkannte Sprache durch Whisper",
                    "missing": "Die lokale Spracherkennung fehlt. Installiere im Terminal: python3 -m pip install faster-whisper",
                },
                "ro": {
                    "caption": "Înregistrează comanda sau introdu textul. Recunoașterea vocală rulează local pe acest Mac.",
                    "record": "🎙️ Înregistrează comanda",
                    "transcribe": "🎧 Transformă înregistrarea în text",
                    "spinner": "Se procesează înregistrarea vocală (prima pornire poate dura mai mult) …",
                    "success": "Înregistrarea a fost procesată. Verifică textul recunoscut înainte de a adăuga produsele.",
                    "language": "Limba detectată de Whisper",
                    "missing": "Recunoașterea vocală locală lipsește. Rulează în Terminal: python3 -m pip install faster-whisper",
                },
                "sr": {
                    "caption": "Snimite porudžbinu ili unesite tekst. Prepoznavanje govora radi lokalno na ovom Mac računaru.",
                    "record": "🎙️ Snimi porudžbinu",
                    "transcribe": "🎧 Pretvori snimak u tekst",
                    "spinner": "Obrada govornog snimka je u toku …",
                    "success": "Snimak je obrađen. Proverite tekst pre dodavanja proizvoda.",
                    "language": "Jezik koji je prepoznao Whisper",
                    "missing": "Nedostaje lokalno prepoznavanje govora. Pokrenite u Terminalu: python3 -m pip install faster-whisper",
                },
            }.get(active_lang, {
                "caption": "Bestellung aufnehmen oder als Text eingeben.",
                "record": "🎙️ Bestellung aufnehmen",
                "transcribe": "🎧 Aufnahme in Text umwandeln",
                "spinner": "Lokale Spracherkennung läuft …",
                "success": "Aufnahme verarbeitet. Bitte Text prüfen.",
                "language": "Erkannte Sprache",
                "missing": "faster-whisper fehlt. Installiere es im Terminal.",
            })
            st.caption(voice_ui["caption"])
            recording = st.audio_input(voice_ui["record"], key="voice_recording")
            if recording is not None and st.button(voice_ui["transcribe"], key="transcribe_recording"):
                try:
                    from faster_whisper import WhisperModel
                    import tempfile
                    with st.spinner(voice_ui["spinner"]):
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                            temp_audio.write(recording.getvalue())
                            audio_path = temp_audio.name
                        try:
                            # Force the signed-in user's selected language; do not let Whisper guess another language.
                            whisper_lang = {"de": "de", "ro": "ro", "sr": "sr"}.get(active_lang, "ro")
                            model = get_whisper_model("base")
                            segments, info = model.transcribe(
                                audio_path,
                                beam_size=5,
                                language=whisper_lang,
                                task="transcribe",
                                vad_filter=True,
                                condition_on_previous_text=False,
                            )
                            # faster-whisper yields segments lazily; consume them before deleting the audio file.
                            transcript_parts = [seg.text.strip() for seg in segments]
                            transcript = " ".join(part for part in transcript_parts if part).strip()
                            st.session_state["voice_transcript"] = transcript
                            st.session_state["voice_detected_language"] = getattr(info, "language", "unknown")
                            st.session_state["voice_language_probability"] = getattr(info, "language_probability", None)
                        finally:
                            os.unlink(audio_path)
                    if transcript:
                        st.success(voice_ui["success"])
                    else:
                        empty_msg = {
                            "de": "Es wurde kein Text erkannt. Bitte näher am Mikrofon und etwas langsamer sprechen.",
                            "ro": "Nu a fost recunoscut niciun text. Vorbește puțin mai rar și mai aproape de microfon.",
                            "sr": "Nije prepoznat tekst. Govorite malo sporije i bliže mikrofonu.",
                        }.get(active_lang, "Es wurde kein Text erkannt.")
                        st.warning(empty_msg)
                    detected = st.session_state.get("voice_detected_language", "unknown")
                    prob = st.session_state.get("voice_language_probability")
                    lang_name = {"de": "Germană / German", "ro": "Română / Romanian", "sr": "Srpski / Serbian"}.get(detected, detected)
                    st.caption(f"{voice_ui['language']}: {lang_name}" + (f" · {prob:.0%}" if isinstance(prob, (int, float)) else ""))
                except ImportError:
                    st.error(voice_ui["missing"])
                except Exception as exc:
                    err_prefix = {"de": "Spracherkennung fehlgeschlagen", "ro": "Recunoașterea vocală a eșuat", "sr": "Prepoznavanje govora nije uspelo"}.get(active_lang, "Spracherkennung fehlgeschlagen")
                    st.error(f"{err_prefix}: {exc}")
            voice_input = st.text_area(L["voice_placeholder"], key="voice_transcript", placeholder="z. B. 5 kg Fitness-Salat und 1 Sack Mehl")
            if st.button(L["voice_btn"], key="extract_voice_order"):
                import re
                import unicodedata
                def normalized(value):
                    return ''.join(ch for ch in unicodedata.normalize('NFKD', value.lower()) if not unicodedata.combining(ch))

                raw = normalized(voice_input)
                # Produktbegriffe aus dem Demo-Katalog plus alltagssprachliche Synonyme.
                # Bei mehreren Treffern oder unklaren Mengen wird nicht stillschweigend bestellt.
                aliases = {
                    "NAV-30210": [r"strauchtomaten?", r"tomaten?", r"rosii", r"paradajz"],
                    "NAV-10204": [r"fitness[- ]?salat", r"salatmischung fitness", r"salat fitness"],
                    "NAV-10205": [r"gourmet[- ]?salat", r"salatmischung gourmet"],
                    "NAV-10206": [r"toscana[- ]?salat", r"salatmischung toscana"],
                    "NAV-90950": [r"weizenmehl type 00", r"mehl type 00", r"pizzamehl", r"mehl", r"fain[ae]", r"faina de grau", r"faina grau", r"brasno", r"flour"],
                    "NAV-90951": [r"pizzamehl tipo 00", r"mehl tipo 00", r"faina pizza", r"brasno za picu"],
                    "NAV-20101": [r"mozzarella", r"mocarela"],
                    "NAV-40201": [r"rinderfilet", r"filet vom rind", r"goveđi file", r"muschi de vita"],
                    "PFAND-E2": [r"e2[- ]?kiste", r"fleischerkiste", r"naveta e2", r"e2 gajba"],
                    "NAV-30211": [r"apfel", r"apfelkiste", r"mere", r"jabuke"],
                    "NAV-30212": [r"bananen?", r"banane"],
                    "NAV-30213": [r"kartoffeln?", r"krompir", r"cartofi"],
                    "NAV-30214": [r"rote paprika", r"paprika", r"ardei rosu", r"crvena paprika"],
                    "NAV-30215": [r"salatgurken?", r"gurken?", r"castraveti", r"krastavci"],
                    "NAV-20102": [r"gouda", r"gouda kase", r"branza gouda", r"gouda sir"],
                    "NAV-40202": [r"lachsfilet", r"lachs", r"somon", r"losos"],
                    "NAV-60101": [r"passierte tomaten", r"passata", r"tomatenpassata", r"rosii pasate", r"pasirani paradajz"],
                    "NAV-50101": [r"pommes frites", r"pommes", r"pomfrit"],
                    "NAV-70101": [r"chianti", r"chianti classico"],
                    "NAV-80105": [r"barolo"]
                }
                found = []
                for product in AZ_PRODUCT_CATALOG:
                    sku = product["sku"]
                    pats = aliases.get(sku, [])
                    hits = [(m.start(), m.end(), pat) for pat in pats for m in re.finditer(pat, raw)]
                    if hits:
                        found.append((product, sorted(hits, key=lambda x: x[0])[0]))

                matches = []
                used_skus = set()
                for product, hit in sorted(found, key=lambda item: item[1][0]):
                    sku = product["sku"]
                    if sku in used_skus:
                        continue
                    used_skus.add(sku)
                    pos = hit[0]
                    prefix = raw[max(0, pos-70):pos]
                    # Explizite Packungsanzahl hat Vorrang vor Gewichtsangabe:
                    # "ein Sack Mehl, 25 Kilo" bedeutet einen Sack, nicht 25 Säcke.
                    pack_words = r"(?:ein|eine|einen|einem|1|zwei|zwo|2|drei|3|vier|4|fuenf|funf|5|un|o|jedan|jednu|dva|dve|tri|cetiri|pet)"
                    pack_pattern = pack_words + r"\s+(?:sack|sacke|sac|saci|beutel|kiste|kisten|karton|kartons|flasche|flaschen|dose|dosen|stück|stuck|bucata|gajba|lada)"
                    # Search the whole utterance before the product too: Romanian phrases
                    # such as "un sac de făină de 25 kg" place the package before the product
                    # and the weight after it.
                    pack_match = re.search(pack_pattern, raw)
                    number_words = {"ein":1,"eine":1,"einen":1,"einem":1,"1":1,"zwei":2,"zwo":2,"2":2,"drei":3,"3":3,"vier":4,"4":4,"fuenf":5,"funf":5,"5":5,"un":1,"o":1,"jedan":1,"jednu":1,"dva":2,"dve":2,"tri":3,"cetiri":4,"pet":5}
                    qty = None
                    if pack_match:
                        token = pack_match.group(0).split()[0]
                        qty = number_words.get(token)
                    if qty is None:
                        # If a pack size is spoken, convert the weight to package count.
                        weight_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:kg|kilo|kilogram(?:m)?|kilograme)\b", raw)
                        if weight_match:
                            amount = float(weight_match.group(1).replace(",", "."))
                            if sku == "NAV-90950" and amount >= 10:
                                qty = amount / 25
                            elif sku == "NAV-90951" and amount >= 10:
                                qty = amount / 10
                        if qty is None:
                            nums = re.findall(r"(\d+(?:[.,]\d+)?)\s*(?:kg|kilo|kilogram(?:m)?|kilograme)?", prefix)
                            if nums:
                                amount = float(nums[-1].replace(",", "."))
                                if sku == "NAV-90950" and amount >= 10:
                                    qty = amount / 25
                                elif sku == "NAV-90951" and amount >= 10:
                                    qty = amount / 10
                                else:
                                    qty = amount
                    if qty is None:
                        st.warning({
                            "de": f"Ich habe „{product.get(active_lang, product['de'])}“ erkannt, aber die Menge nicht sicher verstanden. Bitte Menge ergänzen.",
                            "ro": f"Am recunoscut „{product.get(active_lang, product['de'])}”, dar nu am înțeles sigur cantitatea. Vă rugăm să o completați.",
                            "sr": f"Prepoznao sam „{product.get(active_lang, product['de'])}”, ali količina nije jasna. Unesite količinu."
                        }.get(active_lang, "Please specify the quantity."))
                        continue
                    if qty < 1 or int(qty) != qty:
                        st.warning({
                            "de": f"Die Menge für „{product.get(active_lang, product['de'])}“ ist nicht eindeutig. Bitte Packungsanzahl im Katalog prüfen.",
                            "ro": f"Cantitatea pentru „{product.get(active_lang, product['de'])}” nu este clară. Verificați numărul de ambalaje în catalog.",
                            "sr": f"Količina pentru „{product.get(active_lang, product['de'])}” nije jasna. Verificați numărul de ambalaje în catalog."
                        }.get(active_lang, "Please verify the package quantity in the catalog."))
                        continue
                    if not product.get("in_stock", True):
                        st.warning({
                            "de": f"„{product.get(active_lang, product['de'])}“ ist derzeit als nicht verfügbar markiert. Bitte Alternative im Katalog auswählen.",
                            "ro": f"„{product.get(active_lang, product['de'])}” nu este disponibil momentan. Selectați o alternativă din catalog.",
                            "sr": f"„{product.get(active_lang, product['de'])}” trenutno nije dostupan. Izaberite alternativu iz kataloga."
                        }.get(active_lang, "Product unavailable; choose an alternative in the catalog."))
                        continue
                    qty = int(qty)
                    unit = product.get("unit", "Einheit")
                    matches.append({"sku": sku, "name": product.get(active_lang, product["de"]), "price": product["price"], "qty": qty, "details": f"{qty} × {unit}"})

                if matches:
                    st.session_state.cart.extend(matches)
                    st.success(f"{len(matches)} erkannte Artikel in den Warenkorb übernommen. Bitte Produkte und Mengen vor Freigabe prüfen.")
                    st.rerun()
                else:
                    st.warning({
                        "de": "Ich konnte noch keinen Artikel sicher zuordnen. Bitte Produkt und Menge nennen oder den Artikel im Katalog auswählen.",
                        "ro": "Nu am putut identifica sigur un produs. Spuneți produsul și cantitatea sau selectați articolul din catalog.",
                        "sr": "Nisam mogao pouzdano da prepoznam proizvod. Navedite proizvod i količinu ili izaberite artikl iz kataloga."
                    }.get(active_lang, "Could not identify product. Please choose it from the catalog."))

        # KATALOG: mobile-first, categories + search + clear product cards
        with tab_cat:
            st.write(f"### {L['cat_header']}")
            st.caption("Demo-Katalog für den Prototyp: Produktbilder sind illustrative Beispielbilder (nicht immer Original-Packshots); Artikelnummern, Preise und Bestände sind Beispieldaten und nicht als Rüther-Originaldaten bestätigt. Rüthers öffentliches Sortiment dient als Warengruppen-Orientierung.")
            st.caption({"de": "Finde Produkte über Warengruppe oder Suche. Ready-Cut und Rohware findest du beim jeweiligen Salat.", "ro": "Găsește produsele după categorie sau prin căutare. Opțiunile Ready-Cut și materie primă sunt disponibile la fiecare salată.", "sr": "Pronađite proizvode po kategoriji ili pretragom. Ready-Cut i sirova roba dostupni su kod odgovarajuće salate."}.get(active_lang, ""))

            search_q = st.text_input(L["search_label"], value="", placeholder={"de": "z. B. Tomaten, Mozzarella, Artikelnummer", "ro": "ex. roșii, mozzarella, cod articol", "sr": "npr. paradajz, mocarela, šifra artikla"}.get(active_lang, ""))
            categories = ["ALLE"] + list(CATEGORIES_TRANS.keys())
            cat_labels = ["Alle Produkte"] + [
                CATEGORIES_TRANS.get(cat, {}).get(active_lang, cat) for cat in CATEGORIES_TRANS.keys()
            ]
            selected_cat_label = st.radio(
                "Warengruppe",
                options=cat_labels,
                horizontal=True,
                label_visibility="collapsed",
                key="catalog_category",
            )
            cat_q = categories[cat_labels.index(selected_cat_label)]

            filtered_products = AZ_PRODUCT_CATALOG
            if cat_q != "ALLE":
                filtered_products = [p for p in filtered_products if p["category"] == cat_q]

            search_clean = search_q.strip().lower()
            if search_clean:
                filtered_products = [
                    p for p in filtered_products
                    if search_clean in p["de"].lower()
                    or search_clean in p["ro"].lower()
                    or search_clean in p["sr"].lower()
                    or search_clean in p["sku"].lower()
                ]

            st.caption({"de": f"{len(filtered_products)} Artikel gefunden", "ro": f"{len(filtered_products)} produse găsite", "sr": f"Pronađeno proizvoda: {len(filtered_products)}"}.get(active_lang, f"{len(filtered_products)}"))
            if not filtered_products:
                st.warning({"de": f"Keine Produkte für '{search_q}' gefunden.", "ro": f"Nu s-au găsit produse pentru '{search_q}'.", "sr": f"Nema proizvoda za '{search_q}'."}.get(active_lang, "Keine Produkte gefunden."))
            else:
                for row_start in range(0, len(filtered_products), 2):
                    card_cols = st.columns(2, gap="medium")
                    for local_idx, p in enumerate(filtered_products[row_start:row_start + 2]):
                        p_idx = row_start + local_idx
                        with card_cols[local_idx]:
                            prod_name = p.get(active_lang, p["de"])
                            # Produktbezogenes Bild statt eines einheitlichen Kategorie-Bilds.
                            # Illustrationen für den Prototyp; keine bestätigten Originalfotos des Lieferanten.
                            image_url = PRODUCT_IMAGE_URLS.get(p["sku"])
                            if image_url:
                                st.image(image_url, use_container_width=True)
                            cat_name = CATEGORIES_TRANS.get(p['category'], {}).get(active_lang, p['category'])
                            unit_name = UNITS_TRANS.get(p['unit'], {}).get(active_lang, p['unit'])
                            in_cart_qty = get_cart_qty(p['sku'])
                            card_class = "product-card-added" if in_cart_qty > 0 else "product-card-idle"

                            st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)
                            st.markdown(f"**{prod_name}**")
                            st.caption({"de": f"{cat_name} · Artikelnummer {p['sku']}", "ro": f"{cat_name} · Cod articol {p['sku']}", "sr": f"{cat_name} · Šifra artikla {p['sku']}"}.get(active_lang, f"{cat_name} · {p['sku']}"))
                            price_col, stock_col = st.columns([1, 1])
                            price_col.markdown(f"### {p['price']:.2f} €")
                            price_col.caption({"de": f"pro {unit_name}", "ro": f"per {unit_name}", "sr": f"po {unit_name}"}.get(active_lang, unit_name))
                            if p["in_stock"]:
                                stock_col.success({"de": "Verfügbar", "ro": "Disponibil", "sr": "Dostupno"}.get(active_lang, "Verfügbar"))
                            else:
                                stock_col.error(L["out_of_stock"])

                            if in_cart_qty > 0:
                                st.markdown(
                                    f"<span class='cart-badge'>{L['in_cart_badge']} ({in_cart_qty:.1f} {unit_name})</span>",
                                    unsafe_allow_html=True
                                )

                            if p["in_stock"]:
                                qty_col, add_col = st.columns([1, 1.5])
                                manual_qty = qty_col.number_input(
                                    {"de": "Menge", "ro": "Cantitate", "sr": "Količina"}.get(active_lang, "Menge"), value=1, min_value=1, step=1,
                                    key=f"num_{p['sku']}_{p_idx}"
                                )
                                if add_col.button(L["add_cart"], key=f"btn_add_{p['sku']}_{p_idx}", use_container_width=True):
                                    st.session_state.cart.append({
                                        "sku": p['sku'],
                                        "name": prod_name,
                                        "price": p['price'] * manual_qty,
                                        "qty": manual_qty,
                                        "details": f"{manual_qty}x {p['unit']}"
                                    })
                                    st.toast(f"✅ {manual_qty}x {prod_name} {L['toast_added']}", icon="🛒")
                                    st.rerun()

                            # Salad-specific choices stay attached to the product card.
                            if p.get("is_salad"):
                                salad_ui = {
                                    "de": {"expander": "🥗 Ready-Cut oder Rohware auswählen", "qty": "Gewünschte Netto-Salatmenge (kg)", "raw_caption": "Rohware: {eisb:.2f} kg Eisberg, {rad:.2f} kg Radicchio, {kar:.2f} kg Karotten (Demo-Aufteilung; Rezeptur und Preise bitte fachlich bestätigen).", "ready": "Ready-Cut hinzufügen", "raw": "Rohware hinzufügen", "ready_toast": "Ready-Cut wurde zum Warenkorb hinzugefügt", "raw_toast": "Rohware wurde zum Warenkorb hinzugefügt", "net": "kg netto", "gross": "kg brutto", "iceberg": "Eisbergsalat", "carrot": "Karotten"},
                                    "ro": {"expander": "🥗 Selectați salată Ready-Cut sau legume întregi", "qty": "Cantitatea netă dorită de salată (kg)", "raw_caption": "Legume întregi: {eisb:.2f} kg salată iceberg, {rad:.2f} kg radicchio, {kar:.2f} kg morcovi (repartizare demonstrativă; confirmați rețeta și prețurile).", "ready": "Adăugați salata Ready-Cut", "raw": "Adăugați legumele întregi", "ready_toast": "Salata Ready-Cut a fost adăugată în coș", "raw_toast": "Legumele întregi au fost adăugate în coș", "net": "kg net", "gross": "kg brut", "iceberg": "salată iceberg", "carrot": "morcovi"},
                                    "sr": {"expander": "🥗 Izaberite Ready-Cut salatu ili celo povrće", "qty": "Željena neto količina salate (kg)", "raw_caption": "Celo povrće: {eisb:.2f} kg iceberg salate, {rad:.2f} kg radiča, {kar:.2f} kg šargarepe (demo raspodela; proveriti recepturu i cene).", "ready": "Dodaj Ready-Cut salatu", "raw": "Dodaj celo povrće", "ready_toast": "Ready-Cut salata je dodata u korpu", "raw_toast": "Celo povrće je dodato u korpu", "net": "kg neto", "gross": "kg bruto", "iceberg": "iceberg salata", "carrot": "šargarepa"}
                                }.get(active_lang, {})
                                with st.expander(salad_ui.get("expander", "🥗 Ready-Cut oder Rohware auswählen"), expanded=False):
                                    s_kg = st.number_input(
                                        salad_ui.get("qty", "Gewünschte Netto-Salatmenge (kg)"), value=2.0, min_value=0.5,
                                        step=0.5, key=f"kg_s_{p['sku']}_{p_idx}"
                                    )
                                    b_raw = s_kg * 1.25
                                    eisb, rad, kar = b_raw * 0.5, b_raw * 0.3, b_raw * 0.2
                                    rc_col, raw_col = st.columns(2)
                                    ready_label = {"de": "Ready-Cut", "ro": "Salată Ready-Cut", "sr": "Ready-Cut salata"}.get(active_lang, "Ready-Cut")
                                    raw_label = {"de": "Rohware", "ro": "Legume întregi", "sr": "Celo povrće"}.get(active_lang, "Rohware")
                                    rc_col.markdown(f"**{ready_label}**  \n{s_kg:.1f} {salad_ui.get('net', 'kg netto')}  \n**{p['price']*s_kg:.2f} €**")
                                    raw_price = p['price'] * 0.85 * b_raw
                                    raw_col.markdown(f"**{raw_label}**  \n{b_raw:.2f} {salad_ui.get('gross', 'kg brutto')}  \n**{raw_price:.2f} €**")
                                    st.caption(salad_ui.get("raw_caption", "Rohware: {eisb:.2f} kg Eisberg, {rad:.2f} kg Radicchio, {kar:.2f} kg Karotten").format(eisb=eisb, rad=rad, kar=kar))
                                    rc_btn, raw_btn = st.columns(2)
                                    if rc_btn.button(salad_ui.get("ready", "Ready-Cut hinzufügen"), key=f"rc_btn_{p['sku']}_{p_idx}", use_container_width=True):
                                        st.session_state.cart.append({
                                            "sku": f"{p['sku']}-CUT", "name": f"{prod_name} ({ready_label})",
                                            "price": p['price'] * s_kg, "qty": s_kg,
                                            "details": f"{s_kg:.1f} kg netto geschnitten"
                                        })
                                        st.toast(salad_ui.get("ready_toast", "Ready-Cut wurde zum Warenkorb hinzugefügt"), icon="✂️")
                                        st.rerun()
                                    if raw_btn.button(salad_ui.get("raw", "Rohware hinzufügen"), key=f"rw_btn_{p['sku']}_{p_idx}", use_container_width=True):
                                        raw_desc = f"{eisb:.2f} kg Eisberg, {rad:.2f} kg Radicchio, {kar:.2f} kg Karotten"
                                        st.session_state.cart.append({
                                            "sku": f"{p['sku']}-RAW", "name": f"{prod_name} (Rohware)",
                                            "price": raw_price, "qty": b_raw, "details": raw_desc
                                        })
                                        st.toast("Rohware zum Warenkorb hinzugefügt", icon="🥦")
                                        st.rerun()

                            if not p["in_stock"]:
                                st.markdown(
                                    f"<div class='out-of-stock-card'><b>{L['alt_label']}</b> {p['alternative_name']}</div>",
                                    unsafe_allow_html=True
                                )
                                alt_c1, alt_c2 = st.columns(2)
                                if alt_c1.button(L["alt_btn"], key=f"btn_alt_{p['sku']}_{p_idx}", use_container_width=True):
                                    st.session_state.cart.append({
                                        "sku": p['alternative_sku'],
                                        "name": p['alternative_name'],
                                        "price": 18.20,
                                        "qty": 1,
                                        "details": "Alternative (Demo-Preis)"
                                    })
                                    st.toast(f"{p['alternative_name']} {L['toast_added']}", icon="✅")
                                    st.rerun()
                                if alt_c2.button(L["demand_btn"], key=f"btn_dem_{p['sku']}_{p_idx}", use_container_width=True):
                                    conn = sqlite3.connect(OFFLINE_DB)
                                    c = conn.cursor()
                                    c.execute(
                                        "INSERT INTO demand_reports (customer_name, sku, product_name, timestamp) VALUES (?,?,?,?)",
                                        (user['name'], p["sku"], p["de"], datetime.now().strftime("%Y-%m-%d %H:%M"))
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.toast("Bedarfsmeldung gespeichert", icon="📩")

                            st.markdown("</div>", unsafe_allow_html=True)

        with tab_pfand:
            st.write(f"### {L['pfand_header']}")
            gps_titles = {
                "de": ("Simulierte Fahrzeugposition", "Lieferroute", "Zielkunde", "Position aktualisieren", "Demo-Simulation – keine echte GPS-Ortung"),
                "ro": ("Poziția simulată a vehiculului", "Traseu de livrare", "Client destinatar", "Actualizează poziția", "Simulare demo – nu este localizare GPS reală"),
                "sr": ("Simulirana pozicija vozila", "Ruta isporuke", "Krajnji kupac", "Ažuriraj poziciju", "Demo simulacija – ovo nije stvarno GPS praćenje")
            }
            gps = gps_titles.get(active_lang, gps_titles["de"])
            col_p1, col_p2 = st.columns(2)
            col_p1.metric(L["e2_balance"], "34")
            eta_minutes = max(8, 38 - int(st.session_state.gps_demo_step) * 5)
            col_p2.metric(L["eta"], f"ca. {eta_minutes} Min.", delta="simuliert")
            st.metric(L["temp"], "3.2 °C 🟢")
            st.markdown(f"#### 🗺️ {gps[0]}")
            progress = min(78, 12 + int(st.session_state.gps_demo_step) * 11)
            map_html = f"""<div style='background:#eef3f5;border:1px solid #cbd5e1;border-radius:12px;padding:18px;color:#1f2937;'>
              <div style='display:flex;justify-content:space-between;font-weight:600;margin-bottom:12px;'><span>🚚 LKW 01</span><span>📍 {gps[2]}</span></div>
              <div style='height:150px;position:relative;background:linear-gradient(135deg,#e2e8f0,#f8fafc);border-radius:8px;overflow:hidden;'>
                <div style='position:absolute;left:8%;top:66%;width:78%;height:5px;background:#cbd5e1;transform:rotate(-22deg);transform-origin:left center;'></div>
                <div style='position:absolute;left:8%;top:66%;width:{progress}%;height:5px;background:#0f766e;transform:rotate(-22deg);transform-origin:left center;'></div>
                <div style='position:absolute;left:{progress}%;top:{max(15,66-progress*0.45)}%;font-size:24px;'>🚚</div>
                <div style='position:absolute;right:7%;top:12%;font-size:24px;'>🏁</div>
                <div style='position:absolute;left:12px;bottom:8px;font-size:12px;'>{gps[1]} · Stopp 1</div>
              </div>
              <div style='margin-top:10px;font-size:12px;color:#92400e;font-weight:600;'>ⓘ {gps[4]}</div>
            </div>"""
            st.markdown(map_html, unsafe_allow_html=True)
            if st.button(f"🔄 {gps[3]}", key="customer_gps_update", use_container_width=True):
                st.session_state.gps_demo_step = min(6, int(st.session_state.gps_demo_step) + 1)
                st.rerun()

        with tab_orders:
            orders_text = {
                "de": {"title":"Meine Bestellungen", "intro":"Bestellungen und zugehörige Ersatzangebote im Überblick.", "empty":"Für dieses Kundenkonto liegen aktuell keine Ersatzangebote vor.", "open":"Offenes Ersatzangebot", "original":"Nicht verfügbarer Originalartikel", "alternative":"Vorgeschlagener Ersatzartikel", "accept":"Ersatz annehmen", "reject":"Ersatz ablehnen – Original für später vormerken", "other":"Ablehnen und anderen Ersatz anfragen", "accepted":"Kunde hat Ersatz angenommen", "rejected":"Kunde lehnt Ersatz ab – Original für spätere Lieferung vorgemerkt", "other_saved":"Kunde lehnt Ersatz ab und wünscht eine andere Alternative", "done":"Deine Entscheidung wurde gespeichert.", "status":"Status", "history":"Entscheidung"},
                "ro": {"title":"Comenzile mele", "intro":"Comenzi și oferte de înlocuire asociate.", "empty":"Momentan nu există oferte de înlocuire pentru acest cont.", "open":"Ofertă de înlocuire deschisă", "original":"Articol original indisponibil", "alternative":"Articol înlocuitor propus", "accept":"Acceptă înlocuitorul", "reject":"Respinge – păstrează articolul original pentru mai târziu", "other":"Respinge și solicită alt înlocuitor", "accepted":"Clientul a acceptat înlocuitorul", "rejected":"Clientul respinge înlocuitorul – articolul original este rezervat pentru o livrare viitoare", "other_saved":"Clientul respinge înlocuitorul și solicită o alternativă diferită", "done":"Decizia ta a fost salvată.", "status":"Status", "history":"Decizie"},
                "sr": {"title":"Moje porudžbine", "intro":"Pregled porudžbina i povezanih ponuda zamene.", "empty":"Trenutno nema ponuda zamene za ovaj korisnički nalog.", "open":"Otvorena ponuda zamene", "original":"Nedostupni originalni artikal", "alternative":"Predloženi zamenski artikal", "accept":"Prihvati zamenu", "reject":"Odbij – sačuvaj original za kasniju isporuku", "other":"Odbij i zatraži drugu zamenu", "accepted":"Kupac je prihvatio zamenu", "rejected":"Kupac odbija zamenu – original je označen za buduću isporuku", "other_saved":"Kupac odbija zamenu i traži drugu alternativu", "done":"Tvoja odluka je sačuvana.", "status":"Status", "history":"Odluka"}
            }[active_lang]
            st.write(f"### 📋 {orders_text['title']}")
            st.caption(orders_text["intro"])
            # Bestellübersicht: normale Bestellungen immer anzeigen, auch ohne Ersatzfall.
            customer_names = {str(user.get("name", "")).strip(), str(user.get("restaurant", "")).strip()}
            customer_names.discard("")
            customer_orders = [
                _order for _order in st.session_state.active_orders.values()
                if str(_order.get("customer", "")).strip() in customer_names
                or str(_order.get("restaurant", "")).strip() in customer_names
            ]
            if customer_orders:
                st.markdown("#### 🧾 " + {"de":"Deine Bestellübersicht","ro":"Prezentarea comenzilor tale","sr":"Pregled tvojih porudžbina"}[active_lang])
                for _order in sorted(customer_orders, key=lambda x: str(x.get("time_created", "")), reverse=True):
                    _order_items = _order.get("items", [])
                    _order_lines = []
                    for _item in _order_items:
                        _item_name = catalog_product_display(
                            str(_item.get("name", _item.get("item", "Artikel"))), active_lang,
                            _item.get("sku")
                        )
                        _qty = _item.get("qty", _item.get("quantity", 1))
                        _unit = _item.get("unit", "")
                        _order_lines.append(f"• {_item_name} — {_qty} {_unit}".strip())
                    _items_fallback = str(_order.get("items_summary", "")).strip()
                    _stage_labels = {
                        "de": {"1_auftragseingang":"Eingegangen","2_in_kommissionierung":"In Kommissionierung","3_gepackt":"Kommissioniert","4_verladen":"Verladen","5_belieferung":"Unterwegs","6_geliefert":"Geliefert","7_abgeschlossen":"Abgeschlossen"},
                        "ro": {"1_auftragseingang":"Primită","2_in_kommissionierung":"În pregătire","3_gepackt":"Pregătită","4_verladen":"Încărcată","5_belieferung":"În livrare","6_geliefert":"Livrată","7_abgeschlossen":"Finalizată"},
                        "sr": {"1_auftragseingang":"Primljena","2_in_kommissionierung":"U pripremi","3_gepackt":"Spakovana","4_verladen":"Utovarena","5_belieferung":"Na isporuci","6_geliefert":"Isporučena","7_abgeschlossen":"Završena"}
                    }
                    _stage = _stage_labels[active_lang].get(str(_order.get("current_stage", "")), str(_order.get("current_stage", "—")))
                    with st.container(border=True):
                        st.markdown(f"**#{_order.get('deal_id', '—')} · { {'de':'Bestellt um','ro':'Comandată la','sr':'Poručeno u'}[active_lang] } {_order.get('time_created', '—')}**")
                        st.caption(f"{ {'de':'Status','ro':'Status','sr':'Status'}[active_lang] }: {_stage}")
                        if _order_lines:
                            st.markdown("\\n".join(_order_lines))
                        elif _items_fallback:
                            st.write(_items_fallback)
                        st.markdown(f"**{ {'de':'Gesamt','ro':'Total','sr':'Ukupno'}[active_lang] }: {float(_order.get('total', 0) or 0):.2f} €**")
            else:
                st.info({"de":"Für dieses Kundenkonto sind noch keine Bestellungen vorhanden.","ro":"Nu există încă comenzi pentru acest cont.","sr":"Za ovaj nalog još nema porudžbina."}[active_lang])

            # Ersatzangebote werden zusätzlich angezeigt, wenn es welche gibt.
            customer_cases = [c for c in st.session_state.replacement_cases.values() if str(c.get("customer", "")).strip() in customer_names]
            if customer_cases:
                st.markdown("#### 🔄 " + {"de":"Ersatzangebote und Entscheidungen","ro":"Oferte de înlocuire și decizii","sr":"Ponude zamene i odluke"}[active_lang])
            for _case in customer_cases:
                st.markdown(f"#### 📦 Auftrag #{_case.get('order_id','?')} · Ersatzfall {_case.get('case_id','')}")
                # Customer-facing product names use the customer's selected language,
                # not the language selected by the picker. Preserve unknown/custom names.
                _original_display = catalog_product_display(_case.get('original', '—'), active_lang, _case.get('original_sku'))
                _alternative_display = replacement_label_display(_case.get('alternative', '—'), active_lang)
                _status_display = str(_case.get('status', '—'))
                _status_translations = {
                    "Vom Kunden angenommen – Disposition muss vor Tourfreigabe dokumentieren": {"de":"Vom Kunden angenommen – Disposition muss vor Tourfreigabe dokumentieren", "ro":"Acceptat de client – dispeceratul trebuie să documenteze înainte de plecarea în cursă", "sr":"Kupac je prihvatio – dispečer mora da evidentira odluku pre polaska ture"},
                    "Kunde lehnt Ersatz ab – Disposition muss vor Tourfreigabe bearbeiten": {"de":"Kunde lehnt Ersatz ab – Disposition muss vor Tourfreigabe bearbeiten", "ro":"Clientul a refuzat înlocuitorul – dispeceratul trebuie să soluționeze cazul înainte de plecare", "sr":"Kupac je odbio zamenu – dispečer mora da obradi slučaj pre polaska ture"},
                    "Kunde wünscht anderen Ersatz – Disposition muss vor Tourfreigabe bearbeiten": {"de":"Kunde wünscht anderen Ersatz – Disposition muss vor Tourfreigabe bearbeiten", "ro":"Clientul solicită un alt înlocuitor – dispeceratul trebuie să soluționeze cazul înainte de plecare", "sr":"Kupac traži drugu zamenu – dispečer mora da obradi slučaj pre polaska ture"}
                }
                _status_display = _status_translations.get(_status_display, {}).get(active_lang, _status_display)
                st.write(f"**{orders_text['original']}:** {_original_display}")
                st.write(f"**{orders_text['alternative']}:** {_alternative_display}")
                st.write(f"**{orders_text['status']}:** {_status_display}")
                if _case.get("customer_decision", "Offen") == "Offen" and _case.get("dispo_decision") == "Ausstehend":
                    st.warning(orders_text["open"])
                    _choice = st.radio(orders_text["history"], [orders_text["accept"], orders_text["reject"], orders_text["other"]], key=f"customer_replacement_choice_{_case['case_id']}")
                    if st.button(orders_text["accept"], key=f"customer_replacement_accept_{_case['case_id']}"):
                        _case["customer_decision"] = "Angenommen"
                        _case["status"] = "Vom Kunden angenommen – Disposition muss vor Tourfreigabe dokumentieren"
                        _case["customer_decision_at"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                        st.success(orders_text["done"])
                        st.rerun()
                    if st.button(orders_text["reject"], key=f"customer_replacement_reject_{_case['case_id']}"):
                        _case["customer_decision"] = "Abgelehnt – Original für spätere Lieferung vormerken"
                        _case["status"] = "Kunde lehnt Ersatz ab – Disposition muss vor Tourfreigabe bearbeiten"
                        _case["future_preorder"] = True
                        _case["customer_decision_at"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                        st.success(orders_text["done"])
                        st.rerun()
                    if st.button(orders_text["other"], key=f"customer_replacement_other_{_case['case_id']}"):
                        _case["customer_decision"] = "Abgelehnt – anderer Ersatz gewünscht"
                        _case["status"] = "Kunde wünscht anderen Ersatz – Disposition muss vor Tourfreigabe bearbeiten"
                        _case["customer_decision_at"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                        st.success(orders_text["done"])
                        st.rerun()
                else:
                    st.info(f"{orders_text['history']}: {_case.get('customer_decision','Offen')}")
                st.divider()

    with cart_col:
        st.markdown("<div class='sticky-cart-anchor'></div>", unsafe_allow_html=True)
        st.subheader(L["cart_title"])
        if not st.session_state.cart:
            st.info(L["cart_empty"])
        else:
            summary_items = []
            total = 0.0
            for idx, item in enumerate(st.session_state.cart):
                item_total = float(item["price"]) * float(item.get("qty", 1))
                total += item_total
                det = f" ({item['details']})" if item.get("details") else ""
                cart_ui = {
                    "de": {"price": "Einzelpreis", "qty": "Menge", "remove": "Artikel entfernen", "history_title": "📅 Letzte 6 Demo-Bestellungen dieses Restaurants ansehen", "history_note": "Simulierte Bestellhistorie für die Präsentation; keine echten Kundendaten und keine tatsächlichen HubSpot-Aufträge.", "history_heading": "🧠 Aus der Demo-Bestellhistorie", "history_help": "Demo-Vorschläge anhand einer simulierten Bestellhistorie dieses Restaurants. Nichts wird automatisch hinzugefügt.", "add": "Hinzufügen", "more": "Du kannst weitere Produkte über den Tab „A–Z Produktkatalog“ suchen und hinzufügen. Erst der folgende Freigabeklick übergibt den Auftrag an HubSpot.", "submit": "🚀 Verbindlich bestellen und an HubSpot übergeben"},
                    "ro": {"price": "Preț unitar", "qty": "Cantitate", "remove": "Eliminați articolul", "history_title": "📅 Vezi ultimele 6 comenzi demonstrative ale acestui restaurant", "history_note": "Istoric de comenzi simulat pentru prezentare; nu conține date reale ale clienților și nu reprezintă comenzi reale HubSpot.", "history_heading": "🧠 Din istoricul demonstrativ al comenzilor", "history_help": "Sugestii bazate pe un istoric simulat al acestui restaurant. Nimic nu este adăugat automat.", "add": "Adăugați", "more": "Puteți căuta și adăuga alte produse în fila „Catalog produse A–Z”. Comanda este trimisă către HubSpot numai după confirmarea de mai jos.", "submit": "🚀 Trimiteți comanda și transmiteți-o către HubSpot"},
                    "sr": {"price": "Cena po jedinici", "qty": "Količina", "remove": "Ukloni artikal", "history_title": "📅 Pogledajte poslednjih 6 demo-porudžbina ovog restorana", "history_note": "Simulirana istorija porudžbina za prezentaciju; nema stvarnih podataka kupaca niti stvarnih HubSpot porudžbina.", "history_heading": "🧠 Iz demo-istorije porudžbina", "history_help": "Demo-predlozi na osnovu simulirane istorije ovog restorana. Ništa se ne dodaje automatski.", "add": "Dodaj", "more": "Dodatne proizvode možete pronaći i dodati u kartici „A–Z Katalog proizvoda“. Porudžbina se šalje HubSpot-u tek nakon potvrde ispod.", "submit": "🚀 Potvrdi porudžbinu i pošalji je u HubSpot"}
                }.get(active_lang, {})
                # Re-translate stored cart item names by stable SKU when the customer profile language changes.
                base_sku = item.get("sku", "").removesuffix("-CUT").removesuffix("-RAW")
                catalog_item = next((p for p in AZ_PRODUCT_CATALOG if p["sku"] == base_sku), None)
                display_name = catalog_item.get(active_lang, catalog_item["de"]) if catalog_item else item.get("name", item.get("sku", "Artikel"))
                if item.get("sku", "").endswith("-CUT"):
                    display_name += {"de": " (Ready-Cut)", "ro": " (salată Ready-Cut)", "sr": " (Ready-Cut salata)"}.get(active_lang, " (Ready-Cut)")
                elif item.get("sku", "").endswith("-RAW"):
                    display_name += {"de": " (Rohware)", "ro": " (legume întregi)", "sr": " (celo povrće)"}.get(active_lang, " (Rohware)")
                item_col, qty_col, del_col = st.columns([4.5, 1.5, 0.8])
                item_col.markdown(f"**{display_name}**")
                item_col.caption(f"{cart_ui.get('price', 'Einzelpreis')}: {float(item['price']):.2f} €{det}")
                new_qty = qty_col.number_input(cart_ui.get("qty", "Menge"), min_value=1, max_value=999, value=int(item.get("qty", 1)), step=1, key=f"cart_qty_{idx}", label_visibility="collapsed")
                if int(new_qty) != int(item.get("qty", 1)):
                    st.session_state.cart[idx]["qty"] = int(new_qty)
                    st.rerun()
                if del_col.button("🗑️", key=f"del_cart_{idx}", help=cart_ui.get("remove", "Artikel entfernen")):
                    st.session_state.cart.pop(idx)
                    st.rerun()
                summary_items.append({"sku": item["sku"], "name": display_name, "details": item.get("details", ""), "qty": item.get("qty", 1), "price": item["price"]})
            st.divider()
            st.markdown(f"### {L['cart_total']} **{total:.2f} €**")

            # Demo-Historie: getrennt je Restaurant, ausdrücklich Beispieldaten.
            # Die Empfehlungen sind Vorschläge und werden nie automatisch bestellt.
            restaurant = user.get("restaurant", "")
            history_recs = {
                "Brauhaus zum Hirschen": [("NAV-30213", 2, "Kartoffeln wurden in der Demo-Historie regelmäßig bestellt."), ("NAV-30214", 1, "Paprika taucht in den letzten Demo-Bestellungen häufig auf.")],
                "Ristorante Bella Italia": [("NAV-20101", 1, "Mozzarella wurde in der Demo-Historie regelmäßig nachbestellt."), ("NAV-90951", 1, "Pizzamehl wurde in der Demo-Historie häufig bestellt.")],
                "Restaurant Sarajevo": [("NAV-30214", 1, "Paprika wurde in der Demo-Historie regelmäßig bestellt."), ("NAV-40201", 1, "Rinderfilet taucht in den letzten Demo-Bestellungen häufig auf.")],
            }
            demo_history = {
                "Brauhaus zum Hirschen": [
                    ("Vor 2 Tagen", "Weizenmehl Type 00 × 2; Kartoffeln × 2; Rote Paprika × 1"),
                    ("Vor 4 Tagen", "Weizenmehl Type 00 × 2; Kartoffeln × 2; Gouda × 1"),
                    ("Vor 6 Tagen", "Weizenmehl Type 00 × 3; Rote Paprika × 1; Salatgurken × 10"),
                    ("Vor 8 Tagen", "Kartoffeln × 3; Gouda × 1; Strauchtomaten × 2"),
                    ("Vor 10 Tagen", "Weizenmehl Type 00 × 2; Kartoffeln × 2; Rote Paprika × 1"),
                    ("Vor 12 Tagen", "Weizenmehl Type 00 × 2; Salatgurken × 10; Gouda × 1"),
                ],
                "Ristorante Bella Italia": [
                    ("Vor 1 Tag", "Mozzarella × 2; Pizzamehl Tipo 00 × 2; Passierte Tomaten × 3"),
                    ("Vor 3 Tagen", "Mozzarella × 2; Pizzamehl Tipo 00 × 2; Strauchtomaten × 2"),
                    ("Vor 5 Tagen", "Mozzarella × 1; Pizzamehl Tipo 00 × 3; Passierte Tomaten × 3"),
                    ("Vor 7 Tagen", "Mozzarella × 2; Gouda × 1; Pizzamehl Tipo 00 × 2"),
                    ("Vor 9 Tagen", "Mozzarella × 2; Passierte Tomaten × 2; Strauchtomaten × 2"),
                    ("Vor 11 Tagen", "Mozzarella × 1; Pizzamehl Tipo 00 × 2; Passierte Tomaten × 3"),
                ],
                "Restaurant Sarajevo": [
                    ("Vor 2 Tagen", "Rinderfilet × 2; Rote Paprika × 2; Kartoffeln × 2"),
                    ("Vor 4 Tagen", "Rinderfilet × 2; Kartoffeln × 2; Salatgurken × 8"),
                    ("Vor 6 Tagen", "Rote Paprika × 2; Gouda × 1; Kartoffeln × 3"),
                    ("Vor 8 Tagen", "Rinderfilet × 1; Rote Paprika × 2; Strauchtomaten × 1"),
                    ("Vor 10 Tagen", "Rinderfilet × 2; Kartoffeln × 2; Gouda × 1"),
                    ("Vor 12 Tagen", "Rote Paprika × 2; Kartoffeln × 3; Salatgurken × 8"),
                ],
            }
            history_ui = {"de": {"title": "📅 Letzte 6 Demo-Bestellungen dieses Restaurants ansehen", "note": "Simulierte Bestellhistorie für die Präsentation; keine echten Kundendaten und keine tatsächlichen HubSpot-Aufträge."}, "ro": {"title": "📅 Vezi ultimele 6 comenzi demonstrative ale acestui restaurant", "note": "Istoric simulat pentru prezentare; nu conține date reale ale clienților și nu reprezintă comenzi reale HubSpot."}, "sr": {"title": "📅 Pogledajte poslednjih 6 demo-porudžbina ovog restorana", "note": "Simulirana istorija za prezentaciju; nema stvarnih podataka kupaca niti stvarnih HubSpot porudžbina."}}.get(active_lang, {})
            with st.expander(history_ui.get("title", "📅 Letzte 6 Demo-Bestellungen dieses Restaurants ansehen"), expanded=False):
                st.caption(history_ui.get("note", "Simulierte Bestellhistorie für die Präsentation; keine echten Kundendaten und keine tatsächlichen HubSpot-Aufträge."))
                for history_date, history_items in demo_history.get(restaurant, []):
                    st.write(f"**{history_date}:** {history_items}")
            current_skus = {x.get("sku") for x in st.session_state.cart}
            suggested = [(sku, qty, reason) for sku, qty, reason in history_recs.get(restaurant, []) if sku not in current_skus]
            if suggested:
                history_ui = {"de": {"heading": "🧠 Aus der Demo-Bestellhistorie", "help": "Demo-Vorschläge anhand einer simulierten Bestellhistorie dieses Restaurants. Nichts wird automatisch hinzugefügt."}, "ro": {"heading": "🧠 Din istoricul demonstrativ al comenzilor", "help": "Sugestii bazate pe un istoric simulat al acestui restaurant. Nimic nu este adăugat automat."}, "sr": {"heading": "🧠 Iz demo-istorije porudžbina", "help": "Demo-predlozi na osnovu simulirane istorije ovog restorana. Ništa se ne dodaje automatski."}}.get(active_lang, {})
                st.markdown(f"#### {history_ui.get('heading', '🧠 Aus der Demo-Bestellhistorie')}")
                st.caption(history_ui.get("help", "Demo-Vorschläge anhand einer simulierten Bestellhistorie dieses Restaurants. Nichts wird automatisch hinzugefügt."))
                catalog_by_sku = {p["sku"]: p for p in AZ_PRODUCT_CATALOG}
                for sku, suggested_qty, reason in suggested:
                    p = catalog_by_sku.get(sku)
                    if not p:
                        continue
                    rec_col, rec_btn = st.columns([4, 1.4])
                    rec_col.write(f"**{p.get(active_lang, p['de'])}** · {suggested_qty} × {p['unit']} · {p['price']:.2f} €")
                    rec_col.caption(reason)
                    if rec_btn.button(cart_ui.get("add", "Hinzufügen"), key=f"history_add_{sku}"):
                        st.session_state.cart.append({"sku": sku, "name": p.get(active_lang, p['de']), "price": p["price"], "qty": suggested_qty, "details": f"{suggested_qty} × {p['unit']}"})
                        st.rerun()
            st.info(cart_ui.get("more", "Du kannst weitere Produkte über den Tab „A–Z Produktkatalog“ suchen und hinzufügen. Erst der folgende Freigabeklick übergibt den Auftrag an HubSpot."))
            summary_heading = {"de":"🧾 Automatisch erkannte Bestellzusammenfassung – bitte prüfen", "ro":"🧾 Rezumatul comenzii recunoscut automat – verificați", "sr":"🧾 Automatski prepoznat sažetak porudžbine – proverite"}.get(active_lang, "🧾 Automatisch erkannte Bestellzusammenfassung – bitte prüfen")
            summary_help = {"de":"Prüfe Artikel, Mengen und Gesamtbetrag. Bei Unklarheiten bitte vor dem Absenden korrigieren.", "ro":"Verificați produsele, cantitățile și totalul. Corectați orice neclaritate înainte de trimitere.", "sr":"Proverite artikle, količine i ukupan iznos. Ispravite nejasnoće pre slanja."}.get(active_lang, "Prüfe Artikel, Mengen und Gesamtbetrag.")
            st.markdown(f"#### {summary_heading}")
            st.caption(summary_help)
            for review_item in summary_items:
                st.write(f"• **{review_item['name']}** — {review_item['qty']} × {float(review_item['price']):.2f} €")
            total_label = {"de":"Bestellsumme", "ro":"Total comandă", "sr":"Ukupan iznos"}.get(active_lang, "Bestellsumme")
            st.write(f"**{total_label}: {total:.2f} €**")
            confirm_label = {"de":"Ich habe Artikel, Mengen und Summe geprüft und bestätige diese Bestellung.", "ro":"Am verificat produsele, cantitățile și totalul și confirm comanda.", "sr":"Proverio/la sam artikle, količine i iznos i potvrđujem porudžbinu."}.get(active_lang, "Ich habe die Bestellung geprüft.")
            order_review_confirmed = st.checkbox(confirm_label, key="order_review_confirmed")
            if st.button(cart_ui.get("submit", "🚀 Verbindlich bestellen und an HubSpot übergeben"), type="primary", use_container_width=True, disabled=not order_review_confirmed):
                items_summary_str = ", ".join([f"{i['qty']}x {i['name']}" + (f" ({i['details']})" if i.get('details') else "") for i in summary_items])
                hs_res = hubspot.create_deal(f"GastroLingua Auftrag – {user['name']}", total, items_summary_str)
                if hs_res.get("status") == "SUCCESS" and hs_res.get("deal_id"):
                    real_hs_id = str(hs_res["deal_id"])
                    st.session_state.active_orders[real_hs_id] = {
                        "deal_id": real_hs_id, "customer": user["name"], "restaurant": user.get("restaurant", ""), "items": summary_items,
                        "items_summary": items_summary_str, "total": total, "current_stage": "1_auftragseingang",
                        "stage_label": hs_res.get("stage") or L["stage_1"], "time_created": datetime.now().strftime("%H:%M:%S"),
                        "created_by": user["name"], "picker_name": "", "driver_name": "",
                        "stage_history": [{"stage":"1_auftragseingang","by":user["name"],"at":datetime.now().strftime("%d.%m.%Y %H:%M:%S")}],
                        "outgoing_units": {"e2": 0, "rolli": 0, "pal": 0}, "leergut_driver": {"e2": 0, "rolli": 0, "palette": 0},
                        "retouren_driver": [], "is_loaded": False, "is_driving": False, "is_delivered": False,
                        "rampe_locked": False, "gutschrift_gebucht": False, "hs_id": real_hs_id, "sync_status": "SUCCESS"
                    }
                    msg = f"HubSpot-Auftrag erstellt. ID: {real_hs_id} · Pipeline: {hs_res.get('pipeline','')} · Phase: {hs_res.get('stage','')}"
                    st.success(msg)
                    if hs_res.get("warning"):
                        st.warning(hs_res["warning"])
                    st.session_state.cart = []
                    st.rerun()
                else:
                    st.error(f"HubSpot hat den Auftrag nicht bestätigt. Es wurde kein lokaler Schein-Erfolg angelegt. Details: {hs_res.get('msg', hs_res.get('status','Unbekannter Fehler'))}")

# ROLLE 2: KOMMISSIONIERER (POOLED ORDERS)
elif "2. Kommissionierer" in selected_role_key:
    st.subheader(L["picking_header"])
    pool_orders = [o for o in st.session_state.active_orders.values() if o["current_stage"] in ["1_auftragseingang", "2_kommissionierung", "3_gepackt"]]
    _pick_active = sum(1 for o in pool_orders if o.get("current_stage") == "2_kommissionierung")
    _pick_waiting = sum(1 for o in pool_orders if o.get("current_stage") == "1_auftragseingang")
    _pick_done = sum(1 for o in pool_orders if o.get("current_stage") == "3_gepackt")
    st.markdown(f"""<div class="picking-hero"><h3>📦 Kommissionierstation</h3><p><b>{user['name']}</b> · {L['picking_info']}</p></div>""", unsafe_allow_html=True)
    _m1, _m2, _m3 = st.columns(3)
    _m1.metric({"de":"Warten auf Start","ro":"În așteptare","sr":"Čeka početak"}[active_lang], _pick_waiting)
    _m2.metric({"de":"In Bearbeitung","ro":"În pregătire","sr":"U obradi"}[active_lang], _pick_active)
    _m3.metric({"de":"Gepackt / Tor","ro":"Pregătite","sr":"Spakovano"}[active_lang], _pick_done)
    _pick_flow_label = {"de":"Arbeitsablauf", "ro":"Flux de lucru", "sr":"Tok rada"}[active_lang]
    st.markdown(f"""<div class="picking-tip">🧭 <b>{_pick_flow_label}:</b> 1. Auftrag starten → 2. Positionen prüfen → 3. Ladeeinheiten erfassen → 4. Packen abschließen und an das Tor übergeben.</div>""", unsafe_allow_html=True)

    if not pool_orders:
        st.info(L["no_orders_pool"])
    else:
        st.write(f"### {L['pool_orders_title']} ({len(pool_orders)}):")
        for deal in pool_orders:
            _pick_state = deal.get("current_stage", "")
            _pick_card_class = "active" if _pick_state == "2_kommissionierung" else ("done" if _pick_state == "3_gepackt" else "")
            _pick_state_label = {
                "de":{"1_auftragseingang":"1 · WARTET","2_kommissionierung":"2 · IN BEARBEITUNG","3_gepackt":"3 · FERTIG AM TOR"},
                "ro":{"1_auftragseingang":"1 · ÎN AȘTEPTARE","2_kommissionierung":"2 · ÎN LUCRU","3_gepackt":"3 · GATA LA RAMPA"},
                "sr":{"1_auftragseingang":"1 · ČEKA","2_kommissionierung":"2 · U OBRADI","3_gepackt":"3 · SPREMNO NA RAMPI"}
            }[active_lang].get(_pick_state, _pick_state)
            st.markdown(f'<div class="pick-order {_pick_card_class}"><span class="pick-step {_pick_card_class}">{_pick_state_label}</span><br><b>#{deal.get("deal_id","—")} · {deal.get("customer","Kunde")}</b></div>', unsafe_allow_html=True)
            if deal["current_stage"] == "2_kommissionierung":
                st.markdown(f"""
                <div class="order-card-active">
                    <div class="active-badge">⚡ { {'de':'IN BEARBEITUNG DURCH','ro':'ÎN LUCRU DE CĂTRE','sr':'U OBRADI KOD'}[active_lang] } {user['name'].upper()}</div>
                    <h3 style="margin:0; color: #92400E;">📦 { {'de':'Auftrag','ro':'Comanda','sr':'Porudžbina'}[active_lang] } #{deal['deal_id']} — {deal['customer']}</h3>
                    <p style="margin:0;"><b>{ {'de':'Eingegangen','ro':'Primită','sr':'Primljena'}[active_lang] }:</b> {deal['time_created']} | <b>{ {'de':'Status','ro':'Stare','sr':'Status'}[active_lang] }:</b> <span style="color:#D97706; font-weight:bold;">{ {'de':'2. In Kommissionierung (Aktiv)','ro':'2. În pregătire (activă)','sr':'2. U pakovanju (aktivno)'}[active_lang] }</span></p>
                </div>
                """, unsafe_allow_html=True)
                
                st.write({"de":"#### 📋 Aktiver Packzettel (Positionen abhaken):","ro":"#### 📋 Lista activă de ambalare (bifați pozițiile):","sr":"#### 📋 Aktivna lista za pakovanje (označite stavke):"}[active_lang])
                if "items" in deal and isinstance(deal["items"], list):
                    for idx, itm in enumerate(deal["items"]):
                        c_chk, c_txt = st.columns([1, 10])
                        c_chk.checkbox("", key=f"chk_{deal['deal_id']}_{idx}", value=False)
                        details_str = f" — *{itm.get('details','') }*" if itm.get('details') else ""
                        c_txt.write(f"**{catalog_product_display(itm.get('name', ''), active_lang, itm.get('sku'))}**{details_str} (`{itm['sku']}`)")
                else:
                    st.write(f"**{ {'de':'Inhalt','ro':'Conținut','sr':'Sadržaj'}[active_lang] }:** {translate_items_summary(deal.get('items_summary', ''), active_lang)}")
                
                # Ersatzartikel-Demo: Ersatz wird zunächst provisorisch gepackt und bleibt bis zur Entscheidung gesperrt.
                st.divider()
                st.write({"de":"#### 🔁 Ersatzartikel bei Fehlbestand","ro":"#### 🔁 Înlocuitor pentru stoc epuizat","sr":"#### 🔁 Zamenski artikal za nedostatak zaliha"}[active_lang])
                rep_item_names = [str(itm.get("name", "Artikel")) for itm in deal.get("items", []) if isinstance(itm, dict)]
                rep_orig = st.selectbox({"de":"Nicht verfügbaren Originalartikel wählen","ro":"Alegeți articolul indisponibil","sr":"Izaberite nedostupan originalni artikal"}[active_lang], rep_item_names or [deal.get("items_summary", "Artikel")], format_func=lambda n: catalog_product_display(n, active_lang), key=f"rep_orig_{deal['deal_id']}")
                rep_alternative = st.selectbox({"de":"Vorgeschlagener Ersatzartikel","ro":"Înlocuitor propus","sr":"Predloženi zamenski artikal"}[active_lang], ["Alternative A – vergleichbarer Artikel", "Alternative B – andere Marke", "Alternative C – ähnliche Größe"], format_func=lambda n: replacement_label_display(n, active_lang), key=f"rep_alt_{deal['deal_id']}")
                if st.button({"de":"Ersatz provisorisch packen & Kundenanfrage anlegen","ro":"Ambalați provizoriu și creați solicitarea","sr":"Privremeno spakujte i kreirajte zahtev"}[active_lang], key=f"rep_create_{deal['deal_id']}"):
                    case_id = f"{deal['deal_id']}:{len(st.session_state.replacement_cases)+1}"
                    _rep_sku = next((str(p.get("sku")) for p in AZ_PRODUCT_CATALOG if rep_orig in {str(p.get("de", "")), str(p.get("ro", "")), str(p.get("sr", ""))}), "")
                    st.session_state.replacement_cases[case_id] = {"case_id":case_id,"order_id":str(deal.get("deal_id")),"customer":deal.get("customer","Kunde"),"original":rep_orig,"original_sku":_rep_sku,"alternative":rep_alternative,"status":"Wartet auf Kundenentscheidung","customer_decision":"Offen","dispo_decision":"Ausstehend","created_by":user.get("name","Kommissionierung"),"future_preorder":False}
                    st.success(rep_text("packed", active_lang))
                for _cid, _case in st.session_state.replacement_cases.items():
                    if _case["order_id"] == str(deal.get("deal_id")):
                        _alt_local = replacement_label_display(_case.get("alternative", "—"), active_lang)
                        _status_local = {"de":"Wartet auf Kundenentscheidung","ro":"Așteaptă decizia clientului","sr":"Čeka se odluka kupca"}.get(active_lang, _case.get("status", "—"))
                        st.info(f"{rep_text('case', active_lang)} {_cid}: {_alt_local} · {rep_text('status', active_lang)}: {_status_local}")

                st.divider()
                st.write({"de":"#### 📦 Ausgehende Ladeeinheiten erfassen (Kapitel 4.6):","ro":"#### 📦 Înregistrați unitățile de încărcare expediate (capitolul 4.6):","sr":"#### 📦 Evidentirajte izlazne jedinice za utovar (poglavlje 4.6):"}[active_lang])
                col_l1, col_l2, col_l3 = st.columns(3)
                e2_out = col_l1.number_input({"de":"Gepackte E2-Kisten:","ro":"Lăzi E2 ambalate:","sr":"Spakovane E2 gajbe:"}[active_lang], value=5, key=f"e2_out_{deal['deal_id']}")
                roll_out = col_l2.number_input({"de":"Rollcontainer:","ro":"Containere rulante:","sr":"Roll kontejneri:"}[active_lang], value=1, key=f"roll_out_{deal['deal_id']}")
                pal_out = col_l3.number_input({"de":"Europaletten:","ro":"Europaleți:","sr":"Euro palete:"}[active_lang], value=0, key=f"pal_out_{deal['deal_id']}")
                
                if st.button(f"{L['finish_packing']} #{deal['deal_id']}", key=f"finish_{deal['deal_id']}"):
                    deal["current_stage"] = "3_gepackt"
                    deal["stage_label"] = L["stage_3"]
                    deal["outgoing_units"] = {"e2": e2_out, "rolli": roll_out, "pal": pal_out}
                    sync_res = hubspot.sync_stage(deal.get("hs_id", deal["deal_id"]), "3_gepackt", "Gepackt am Tor")
                    if sync_res.get("status") != "SUCCESS":
                        st.error(f"Lokaler Status geändert, HubSpot-Phase NICHT bestätigt: {sync_res.get('msg', sync_res.get('status'))}")
                    else:
                        st.success(sync_res.get("msg", "HubSpot-Phase aktualisiert."))
                    st.toast("✅ Auftrag fertig gepackt & an Tor übergeben!", icon="✅")
                    st.rerun()

            elif deal["current_stage"] == "3_gepackt":
                st.markdown(f"""
                <div class="order-card-idle">
                    <h4>📦 { {'de':'Auftrag','ro':'Comanda','sr':'Porudžbina'}[active_lang] } #{deal['deal_id']} — {deal['customer']}</h4>
                    <div class="done-badge">✅ { {'de':'3. GEPACKT AM TOR — Bereit zur LKW-Verladung','ro':'3. PREGĂTITĂ LA RAMPA — Gata pentru încărcare','sr':'3. SPAKOVANO NA RAMPI — Spremno za utovar'}[active_lang] }</div>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.markdown(f"""
                <div class="order-card-idle">
                    <h4 style="margin:0;">📦 { {'de':'Auftrag','ro':'Comanda','sr':'Porudžbina'}[active_lang] } #{deal['deal_id']} — {deal['customer']}</h4>
                    <p style="margin:0;"><b>{ {'de':'Eingegangen um','ro':'Primită la ora','sr':'Primljena u'}[active_lang] }:</b> {deal['time_created']} | <b>{ {'de':'Status','ro':'Stare','sr':'Status'}[active_lang] }:</b> ⏳ { {'de':'Wartet auf Start','ro':'În așteptarea începerii','sr':'Čeka početak'}[active_lang] }</p>
                    <p style="margin-top:0.5rem;"><b>{ {'de':'Positionen','ro':'Produse','sr':'Stavke'}[active_lang] }:</b> {translate_items_summary(deal.get('items_summary', ''), active_lang)}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"{L['start_picking']} #{deal['deal_id']}", key=f"start_{deal['deal_id']}"):
                    deal["current_stage"] = "2_kommissionierung"
                    deal["stage_label"] = L["stage_2"]
                    deal["picker_name"] = user["name"]
                    deal.setdefault("stage_history", []).append({"stage":"2_kommissionierung","by":user["name"],"at":datetime.now().strftime("%d.%m.%Y %H:%M:%S")})
                    sync_res = hubspot.sync_stage(deal.get("hs_id", deal["deal_id"]), "2_kommissionierung", "In Kommissionierung")
                    if sync_res.get("status") != "SUCCESS":
                        st.error(f"Lokaler Status geändert, HubSpot-Phase NICHT bestätigt: {sync_res.get('msg', sync_res.get('status'))}")
                    else:
                        st.success(sync_res.get("msg", "HubSpot-Phase aktualisiert."))
                    st.toast("⚡ Kommissionierung gestartet!", icon="📦")
                    st.rerun()

# ROLLE 3: FAHRER
elif "3. Auslieferungs-Fahrer" in selected_role_key:
    st.subheader(L["driver_header"])
    st.write(f"**{L['logged_in']}** {user['name']} 🇩🇪")
    
    driver_orders = [o for o in st.session_state.active_orders.values() if o["current_stage"] in ["3_gepackt", "4_verladen", "5_belieferung", "6_geliefert"]]
    _all_demo_tours = st.session_state.get("demo_tours", {})
    # Wenn Aufträge Touren zugewiesen sind, sieht ein Fahrer nur seine eigenen
    # Aufträge in der Arbeitsmaske. Nicht zugewiesene Altaufträge bleiben sichtbar,
    # solange noch überhaupt keine Tourzuordnungen existieren.
    _assigned_ids_for_user = {
        str(t.get("order_id")) for t in _all_demo_tours.values()
        if t.get("driver") == user.get("name")
    }
    if _all_demo_tours:
        driver_orders = [
            o for o in driver_orders
            if str(o.get("deal_id")) in _assigned_ids_for_user
        ]
    _driver_tour_by_order = {
        str(t.get("order_id")): t for t in _all_demo_tours.values()
        if t.get("driver") == user.get("name")
    }

    # Vorabinformation: Fahrer sehen bereits geplante Touren auch vor Abschluss der Kommissionierung.
    planned_tours = [
        t for t in st.session_state.get("demo_tours", {}).values()
        if t.get("driver") == user.get("name")
    ]
    if planned_tours:
        st.markdown(f"### {L['planned_tours_title']}")
        st.info(L["planned_tours_info"])
        st.dataframe([
            {
                L["tour_order"]: t.get("label", f"#{t.get('order_id', '?')}"),
                L["tour_vehicle"]: t.get("vehicle", L["not_set"]),
                L["tour_stop"]: t.get("stop", L["not_set"]),
                L["tour_status"]: t.get("status", "Geplant" if active_lang == "de" else ("Planificat" if active_lang == "ro" else "Planirano")),
            }
            for t in planned_tours
        ], use_container_width=True, hide_index=True)
        # Schlüsselhinweis schon direkt nach Tourzuordnung zeigen, unabhängig vom Kommissionierstatus.
        for _pt in planned_tours:
            _poid = str(_pt.get("order_id", ""))
            _pdeal = st.session_state.active_orders.get(_poid)
            if not _pdeal:
                continue
            _pname = str(_pdeal.get("customer", "")).lower()
            _pneeds_key = ("hirschen" in _pname) or bool(_pdeal.get("requires_access_key", False))
            if _pneeds_key:
                _pkeyno = _pdeal.get("key_number", "12")
                _pcol1, _pcol2 = st.columns([3, 2])
                with _pcol1:
                    st.warning({"de":f"🔑 Kundenschlüssel Nr. {_pkeyno} · {_pdeal.get('customer', 'Kunde')} · erforderlich","ro":f"🔑 Cheia clientului nr. {_pkeyno} · {_pdeal.get('customer', 'Client')} · necesară","sr":f"🔑 Ključ klijenta br. {_pkeyno} · {_pdeal.get('customer', 'Kupac')} · obavezan"}[active_lang])
                with _pcol2:
                    _pkey_label = {"de":f"Schlüssel Nr. {_pkeyno} eingesteckt","ro":f"Cheia nr. {_pkeyno} luată","sr":f"Ključ br. {_pkeyno} preuzet"}[active_lang]
                    _pkey_state = st.checkbox(_pkey_label, value=bool(_pdeal.get("key_taken", False)), key=f"key_taken_{_poid}")
                    _pdeal["key_taken"] = _pkey_state
    
    # Eine zentrale Tour-Steuerung statt eines Start-Buttons in jedem einzelnen Auftrag.
    _driver_tours = [t for t in planned_tours if t.get("driver") == user.get("name")]
    _tour_vehicles = sorted({str(t.get("vehicle")) for t in _driver_tours if t.get("vehicle")})
    if _driver_tours:
        st.markdown("---")
        st.markdown(f"### 🚚 { {'de':'Gesamte Tour','ro':'Întreaga cursă','sr':'Cela tura'}[active_lang] }")
        st.caption({
            "de":"Jeden Auftrag einzeln verladen und das Leergut pro Kunde erfassen. Die Tour wird nur einmal gestartet – erst wenn alle zugehörigen Aufträge verladen und alle benötigten Schlüssel bestätigt sind.",
            "ro":"Încărcați fiecare comandă separat și înregistrați ambalajele returnabile pentru fiecare client. Cursa se pornește o singură dată, numai după încărcarea tuturor comenzilor și confirmarea tuturor cheilor necesare.",
            "sr":"Svaku porudžbinu utovarite posebno i evidentirajte povratnu ambalažu za svakog kupca. Tura se pokreće samo jednom, tek kada su sve povezane porudžbine utovarene i svi potrebni ključevi potvrđeni."
        }[active_lang])
        _tour_vehicle = _tour_vehicles[0] if len(_tour_vehicles) == 1 else None
        if _tour_vehicle:
            _tour_order_ids = {str(t.get("order_id")) for t in _driver_tours if str(t.get("vehicle")) == _tour_vehicle}
            _tour_deals = [o for o in st.session_state.active_orders.values() if str(o.get("deal_id")) in _tour_order_ids and not o.get("is_delivered")]
            _all_tour_loaded = bool(_tour_deals) and all(o.get("is_loaded", False) for o in _tour_deals)
            _all_required_keys_taken = all((not (bool(o.get("requires_access_key", False)) or "hirschen" in str(o.get("customer", "")).lower())) or bool(o.get("key_taken", False)) for o in _tour_deals)
            _already_tour_driving = any(o.get("is_driving", False) for o in _tour_deals)
            _loaded_count = sum(bool(o.get("is_loaded", False)) for o in _tour_deals)
            st.info({"de":f"Fahrzeug { _tour_vehicle } · { _loaded_count } von {len(_tour_deals)} Aufträgen verladen", "ro":f"Vehicul { _tour_vehicle } · { _loaded_count } din {len(_tour_deals)} comenzi încărcate", "sr":f"Vozilo { _tour_vehicle } · { _loaded_count } od {len(_tour_deals)} porudžbina utovareno"}[active_lang])
            if _already_tour_driving:
                st.success({"de":"Diese Tour wurde bereits gestartet.","ro":"Această cursă a fost deja pornită.","sr":"Ova tura je već pokrenuta."}[active_lang])
            else:
                if not _all_tour_loaded:
                    st.warning({"de":"Tourstart gesperrt: Bitte zuerst alle Aufträge dieser Tour einzeln verladen.","ro":"Pornirea este blocată: încărcați mai întâi fiecare comandă din această cursă.","sr":"Polazak je blokiran: prvo utovarite svaku porudžbinu ove ture."}[active_lang])
                if _all_tour_loaded and not _all_required_keys_taken:
                    st.warning({"de":"Tourstart gesperrt: Bitte die Schlüsselmitnahme für alle betroffenen Aufträge bestätigen.","ro":"Pornirea este blocată: confirmați preluarea cheilor pentru toate comenzile relevante.","sr":"Polazak je blokiran: potvrdite preuzimanje ključeva za sve relevantne porudžbine."}[active_lang])
                _start_label = {"de":"🚦 GESAMTE TOUR STARTEN", "ro":"🚦 PORNIȚI ÎNTREAGA CURSĂ", "sr":"🚦 POKRENI CELU TURU"}[active_lang]
                if st.button(_start_label, key=f"drive_tour_overview_{_tour_vehicle}", type="primary", use_container_width=True, disabled=(not _all_tour_loaded or not _all_required_keys_taken or not _tour_deals)):
                    for _tour_deal in _tour_deals:
                        if not _tour_deal.get("is_driving"):
                            _tour_deal["is_driving"] = True
                            _tour_deal["current_stage"] = "5_belieferung"
                            _tour_deal["driver_name"] = user["name"]
                            _tour_deal.setdefault("stage_history", []).append({"stage":"5_belieferung","by":user["name"],"at":datetime.now().strftime("%d.%m.%Y %H:%M:%S")})
                            _tour_deal["stage_label"] = L["stage_5"]
                            sync_res = hubspot.sync_stage(_tour_deal.get("hs_id", _tour_deal["deal_id"]), "5_belieferung", "In Belieferung")
                            if sync_res.get("status") != "SUCCESS":
                                st.warning(f"Auftrag #{_tour_deal['deal_id']}: HubSpot-Phase nicht bestätigt: {sync_res.get('msg', sync_res.get('status'))}")
                    for _tour in _all_demo_tours.values():
                        if _tour.get("driver") == user.get("name") and str(_tour.get("vehicle")) == _tour_vehicle:
                            _tour["status"] = "Unterwegs"
                    st.toast("✅ Tour gestartet!" if active_lang == "de" else ("✅ Cursa a pornit!" if active_lang == "ro" else "✅ Tura je pokrenuta!"), icon="🚦")
                    st.rerun()
        else:
            st.warning({"de":"Bitte nur ein Fahrzeug pro Tourübersicht verwenden; die Touren sind aktuell mehreren Fahrzeugen zugeordnet.","ro":"Folosiți un singur vehicul pentru această prezentare a cursei; momentan sunt asociate mai multe vehicule.","sr":"Za ovaj pregled koristite jedno vozilo; trenutno je povezano više vozila."}[active_lang])
        st.markdown("---")

    if not driver_orders:
        st.info(L["no_driver_orders"])
    else:
        for deal in driver_orders:
            _translated_summary = translate_items_summary(deal.get("items_summary", ""), active_lang)
            st.markdown(f"""
            <div class="order-card-idle">
                <h4>🚚 Stopp: #{deal['deal_id']} — {deal['customer']}</h4>
                <p><b>{ {'de':'Soll-Ladung','ro':'Încărcătură planificată','sr':'Planirani teret'}[active_lang] }:</b> {_translated_summary}</p>
            </div>
            """, unsafe_allow_html=True)

            # Demo-Lieferhinweise werden nur bei einer dem aktuellen Fahrer zugeordneten Tour gezeigt.
            _assigned_tour = _driver_tour_by_order.get(str(deal.get("deal_id")))
            _customer_name = str(deal.get("customer", "")).lower()
            _needs_key = ("hirschen" in _customer_name) or bool(deal.get("requires_access_key", False))
            if _assigned_tour:
                _delivery_notes = deal.get("delivery_notes") or ({
                    "de": "Hinter dem Eingangstor abstellen.",
                    "ro": "Lăsați marfa în spatele porții de intrare.",
                    "sr": "Ostaviti robu iza ulazne kapije."
                } if "hirschen" in _customer_name else {"de":"Keine besonderen Lieferhinweise hinterlegt.","ro":"Nu sunt instrucțiuni speciale de livrare.","sr":"Nema posebnih uputstava za isporuku."})
                st.info(f"📍 { {'de':'Lieferhinweis','ro':'Instrucțiuni de livrare','sr':'Uputstvo za isporuku'}[active_lang] }: {_delivery_notes.get(active_lang, _delivery_notes.get('de',''))}")
                if _needs_key:
                    _access_code = deal.get("access_code", "1234" if "hirschen" in _customer_name else "")
                    st.warning(f"🔑 { {'de':'Zugangscode','ro':'Cod de acces','sr':'Pristupni kod'}[active_lang] }: **{_access_code}**")
                    _key_label = {"de":"Kundenschlüssel bei der Verladung eingepackt","ro":"Cheia clientului a fost luată la încărcare","sr":"Ključ klijenta je spakovan pri utovaru"}[active_lang]
                    # Checkbox wird bereits oben in der Tour-Vorabinformation angezeigt.
                    deal["key_taken"] = bool(st.session_state.get(f"key_taken_{deal['deal_id']}", deal.get("key_taken", False)))

            c1, c2, c3 = st.columns(3)
            
            # SCHRITT 1: VERLADEN
            with c1:
                if deal.get("is_loaded"):
                    st.markdown(f"<div class='done-badge'>✅ { {'de':'4. VERLADEN','ro':'4. ÎNCĂRCAT','sr':'4. UTOVARENO'}[active_lang] }<br/>({deal['outgoing_units']['e2']}x E2, {deal['outgoing_units']['rolli']}x Rolli)</div>", unsafe_allow_html=True)
                else:
                    st.write({"de":"**4. Verlade-Kontrolle:**","ro":"**4. Verificarea încărcării:**","sr":"**4. Kontrola utovara:**"}[active_lang])
                    v_e2 = st.number_input({"de":"Verladene E2-Kisten:","ro":"Lăzi E2 încărcate:","sr":"Utovarene E2 gajbe:"}[active_lang], value=deal.get("outgoing_units", {}).get("e2", 5), key=f"v_e2_{deal['deal_id']}")
                    v_roll = st.number_input({"de":"Verladene Rollis:","ro":"Containere rulante încărcate:","sr":"Utovareni roll kontejneri:"}[active_lang], value=deal.get("outgoing_units", {}).get("rolli", 1), key=f"v_roll_{deal['deal_id']}")
                    
                    if st.button(f"🚛 { {'de':'4. LKW BELADEN & BESTÄTIGEN','ro':'4. ÎNCĂRCAȚI CAMIONUL ȘI CONFIRMAȚI','sr':'4. UTOVARITE KAMION I POTVRDITE'}[active_lang] } #{deal['deal_id']}", key=f"load_{deal['deal_id']}"):
                        deal["is_loaded"] = True
                        deal["outgoing_units"] = {"e2": v_e2, "rolli": v_roll, "pal": 0}
                        deal["current_stage"] = "4_verladen"
                        deal["driver_name"] = user["name"]
                        deal.setdefault("stage_history", []).append({"stage":"4_verladen","by":user["name"],"at":datetime.now().strftime("%d.%m.%Y %H:%M:%S")})
                        deal["stage_label"] = L["stage_4"]
                        sync_res = hubspot.sync_stage(deal.get("hs_id", deal["deal_id"]), "4_verladen", "Verladen im LKW")
                        if sync_res.get("status") != "SUCCESS":
                            st.error(f"Lokaler Status geändert, HubSpot-Phase NICHT bestätigt: {sync_res.get('msg', sync_res.get('status'))}")
                        else:
                            st.success(sync_res.get("msg", "HubSpot-Phase aktualisiert."))
                        st.toast("✅ Im LKW verladen & Leergut bestätigt!", icon="🚛")
                        st.rerun()
                
            # SCHRITT 2: Tourstart wird zentral oberhalb der Auftragskarten gesteuert.
            with c2:
                if deal.get("is_driving"):
                    st.markdown(f"<div class='done-badge'>✅ { {'de':'Tour läuft','ro':'Cursa este în desfășurare','sr':'Tura je u toku'}[active_lang] }</div>", unsafe_allow_html=True)
                elif deal.get("is_loaded"):
                    st.caption({"de":"Wartet auf den zentralen Tourstart.","ro":"Așteaptă pornirea centralizată a cursei.","sr":"Čeka centralno pokretanje ture."}[active_lang])
                else:
                    st.caption({"de":"Tourstart nach Verladung aller Aufträge.","ro":"Cursa pornește după încărcarea tuturor comenzilor.","sr":"Tura se pokreće nakon utovara svih porudžbina."}[active_lang])

            # SCHRITT 3: ABLADEN
            with c3:
                if deal.get("is_delivered"):
                    st.markdown(f"<div class='done-badge'>✅ { {'de':'6. GELIEFERT (POD OK)','ro':'6. LIVRAT (POD CONFIRMAT)','sr':'6. ISPORUČENO (POD POTVRĐEN)'}[active_lang] }<br/>({ {'de':'Zurück','ro':'Returnate','sr':'Vraćeno'}[active_lang] }: {deal['leergut_driver']['e2']}x E2)</div>", unsafe_allow_html=True)
                else:
                    btn_disabled = not deal.get("is_driving", False)
                    st.write({"de":"**6. Vor-Ort Leergut-Rücknahme:**","ro":"**6. Preluarea ambalajelor returnabile la client:**","sr":"**6. Preuzimanje povratne ambalaže kod kupca:**"}[active_lang])
                    ret_e2 = st.number_input({"de":"Zurückgenommene E2-Kisten:","ro":"Lăzi E2 returnate:","sr":"Vraćene E2 gajbe:"}[active_lang], value=5, key=f"ret_e2_{deal['deal_id']}")
                    ret_roll = st.number_input({"de":"Zurückgenommene Rollis:","ro":"Containere rulante returnate:","sr":"Vraćeni roll kontejneri:"}[active_lang], value=1, key=f"ret_roll_{deal['deal_id']}")
                    
                    if st.button(f"📦 { {'de':'6. ABLADEN & POD','ro':'6. DESCĂRCARE ȘI CONFIRMARE POD','sr':'6. ISTOVAR I POD' }[active_lang] } #{deal['deal_id']}", key=f"pod_{deal['deal_id']}", disabled=btn_disabled):
                        deal["is_delivered"] = True
                        deal["leergut_driver"] = {"e2": ret_e2, "rolli": ret_roll, "palette": 0}
                        deal["current_stage"] = "6_geliefert"
                        deal["driver_name"] = user["name"]
                        deal.setdefault("stage_history", []).append({"stage":"6_geliefert","by":user["name"],"at":datetime.now().strftime("%d.%m.%Y %H:%M:%S")})
                        deal["stage_label"] = L["stage_6"]
                        sync_res = hubspot.sync_stage(deal.get("hs_id", deal["deal_id"]), "6_geliefert", "Geliefert")
                        if sync_res.get("status") != "SUCCESS":
                            st.error(f"Lokaler Status geändert, HubSpot-Phase NICHT bestätigt: {sync_res.get('msg', sync_res.get('status'))}")
                        else:
                            st.success(sync_res.get("msg", "HubSpot-Phase aktualisiert."))
                        st.toast("✅ Geliefert, POD & Leergut-Rücknahme erfasst!", icon="📸")
                        st.rerun()

            # RETOUREN-ERFASSUNG MIT URSPRÜNGLICHEM LIEFERDATUM
            if deal.get("is_driving") or deal.get("is_delivered"):
                st.divider()
                st.write({"de":"#### 📝 Retouren & Reklamationen erfassen (mit ursprünglichem Lieferdatum):", "ro":"#### 📝 Înregistrarea retururilor și reclamațiilor (cu data inițială a livrării):", "sr":"#### 📝 Evidencija povrata i reklamacija (sa prvobitnim datumom isporuke):"}[active_lang])
                c_r1, c_r2, c_r3 = st.columns([2, 3, 1.5])
                ret_labels = {"de":{"date":"Datum der ursprünglichen Lieferung:", "sku":"Artikel aus dem Produktstamm:", "qty":"Menge:", "reason":"Retourengrund:", "save":"Retoure vormerken"}, "ro":{"date":"Data livrării inițiale:", "sku":"Selectați articolul din catalog:", "qty":"Cantitate:", "reason":"Motivul returului:", "save":"Înregistrați returul"}, "sr":{"date":"Datum prvobitne isporuke:", "sku":"Izaberite artikal iz kataloga:", "qty":"Količina:", "reason":"Razlog povrata:", "save":"Evidentirajte povrat"}}[active_lang]
                orig_delivery_date = c_r1.date_input(ret_labels["date"], value=date.today(), key=f"dt_{deal['deal_id']}")
                catalog_names = {p["sku"]: p.get(active_lang, p["de"]) for p in AZ_PRODUCT_CATALOG}
                ret_sku = c_r2.selectbox(ret_labels["sku"], list(catalog_names), format_func=lambda sku: f"{catalog_names[sku]} ({sku})", key=f"ret_sku_{deal['deal_id']}")
                ret_qty = c_r3.number_input(ret_labels["qty"], min_value=1, max_value=999, value=1, key=f"ret_qty_{deal['deal_id']}")
                reasons = {"de":["Qualitätsmangel / welk","Falschlieferung","Transportschaden","MHD zu kurz"], "ro":["Problemă de calitate / ofilit","Livrare greșită","Deteriorare la transport","Termen de valabilitate prea scurt"], "sr":["Nedostatak kvaliteta / uvelo","Pogrešna isporuka","Oštećenje u transportu","Prekratak rok trajanja"]}[active_lang]
                ret_reason = st.selectbox(ret_labels["reason"], reasons, key=f"rsn_{deal['deal_id']}")
                ret_item = catalog_names[ret_sku]
                _ret_signature = (str(ret_sku), str(ret_reason), int(ret_qty), orig_delivery_date.strftime("%d.%m.%Y"))
                _ret_already_exists = any((str(_r.get("sku","")), str(_r.get("reason","")), int(_r.get("qty",1)), str(_r.get("delivery_date",""))) == _ret_signature for _r in deal.get("retouren_driver", []))
                if st.button(f"📝 {ret_labels['save']} · {orig_delivery_date.strftime('%d.%m.%Y')} #{deal['deal_id']}", key=f"btn_ret_{deal['deal_id']}", disabled=_ret_already_exists):
                    deal["retouren_driver"].append({"sku":ret_sku, "item":ret_item, "reason":ret_reason, "qty":int(ret_qty), "delivery_date":orig_delivery_date.strftime("%d.%m.%Y")})
                    st.session_state[f"ret_confirm_{deal['deal_id']}"] = f"Retoure erfasst: {ret_item} · {ret_qty} Stück · {ret_reason} · Lieferung {orig_delivery_date.strftime('%d.%m.%Y')}"
                    st.toast({"de":f"Retoure ({ret_item}) erfasst und sichtbar bestätigt!", "ro":f"Returul ({ret_item}) a fost înregistrat și confirmat!", "sr":f"Povrat ({ret_item}) je evidentiran i potvrđen!"}[active_lang], icon="📝")
                    st.rerun()
                if _ret_already_exists:
                    st.success(f"✅ Bereits erfasst: {ret_item} · {ret_qty} Stück · {ret_reason} · Lieferdatum {orig_delivery_date.strftime('%d.%m.%Y')}. Der Button ist gesperrt, damit dieselbe Retoure nicht versehentlich doppelt erfasst wird.")
                if st.session_state.get(f"ret_confirm_{deal['deal_id']}"):
                    st.success("✅ " + st.session_state[f"ret_confirm_{deal['deal_id']}"])

                if deal.get("retouren_driver"):
                    st.write({"de":"**Bereits erfasste Retouren für diesen Kunden:**", "ro":"**Retururi deja înregistrate pentru acest client:**", "sr":"**Već evidentirani povrati za ovog kupca:**"}[active_lang])
                    for r in deal["retouren_driver"]:
                        st.markdown(f"• **{r['item']}** ({ {'de':'Grund','ro':'Motiv','sr':'Razlog'}[active_lang] }: {r['reason']}) — *{ {'de':'Lieferdatum','ro':'Data livrării','sr':'Datum isporuke'}[active_lang] }: {r['delivery_date']}*")

    # INSTANT FEEDBACK-BRIDGE
    st.divider()
    st.write(f"#### {L['driver_alert_title']}")
    
    # Nur reale, im aktuellen Testbestand angelegte Kunden anbieten: aktive Aufträge
    # plus aktive Gastronom-Konten aus der Kontendatenbank. Keine Platzhalterkunden.
    all_customers = sorted({str(o.get("customer", "")).strip() for o in st.session_state.active_orders.values() if str(o.get("customer", "")).strip()})
    try:
        _accounts_conn = auth_db()
        _account_rows = _accounts_conn.execute("SELECT display_name, restaurant FROM users WHERE active=1 AND lower(role) LIKE '%gastronom%'").fetchall()
        _accounts_conn.close()
        for _display_name, _restaurant_name in _account_rows:
            _customer_label = str(_restaurant_name or _display_name or "").strip()
            if _customer_label:
                all_customers.append(_customer_label)
        all_customers = sorted(set(all_customers))
    except Exception:
        all_customers = sorted(set(all_customers))
    if not all_customers:
        st.warning("Es sind keine aktiven Kundenkonten oder Kundenaufträge vorhanden. Bitte zuerst ein Testkundenkonto anlegen.")
        st.stop()
    alert_labels = {
        "de":{"customer":"Betroffenes Kundenkonto wählen:", "category":"Kategorie:", "note":"Sprachnachricht / Textnotiz an Außendienst:", "record":"🎙️ Sprachnachricht aufnehmen", "transcribe":"🎧 Aufnahme transkribieren", "spinner":"Sprachnachricht wird lokal transkribiert …", "placeholder":"Nachricht eingeben oder einsprechen …"},
        "ro":{"customer":"Selectați clientul vizat:", "category":"Categorie:", "note":"Mesaj vocal / notă text pentru agent:", "record":"🎙️ Înregistrați mesajul vocal", "transcribe":"🎧 Transcrieți înregistrarea", "spinner":"Mesajul vocal este transcris local …", "placeholder":"Introduceți sau dictați mesajul pentru agent …"},
        "sr":{"customer":"Izaberite kupca:", "category":"Kategorija:", "note":"Glasovna poruka / beleška za komercijalistu:", "record":"🎙️ Snimite glasovnu poruku", "transcribe":"🎧 Transkribujte snimak", "spinner":"Snimak se lokalno transkribuje …", "placeholder":"Unesite ili izdiktirajte poruku …"}
    }[active_lang]
    selected_customer_alert = st.selectbox(alert_labels["customer"], all_customers)

    category_codes = ["QUALITÄTSMANGEL", "PREISDRUCK", "UPSELLING_WUNSCH", "SONSTIGES"]
    category_labels = {
        "de": {"QUALITÄTSMANGEL":"Qualitätsmangel", "PREISDRUCK":"Preisvergleich / Preisdruck", "UPSELLING_WUNSCH":"Zusätzlicher Bedarf", "SONSTIGES":"Sonstiges"},
        "ro": {"QUALITÄTSMANGEL":"Problemă de calitate", "PREISDRUCK":"Prețuri mai mici la concurență", "UPSELLING_WUNSCH":"Cerere suplimentară", "SONSTIGES":"Altele"},
        "sr": {"QUALITÄTSMANGEL":"Problem kvaliteta", "PREISDRUCK":"Niže cene kod konkurencije", "UPSELLING_WUNSCH":"Dodatna potražnja", "SONSTIGES":"Ostalo"},
    }
    alert_cat = st.selectbox(alert_labels["category"], category_codes, format_func=lambda code: category_labels[active_lang][code])
    recording_alert = st.audio_input(alert_labels["record"], key="driver_alert_audio")
    if recording_alert is not None and st.button(alert_labels["transcribe"], key="driver_alert_transcribe"):
        _audio_path = None
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as _audio:
                _audio.write(recording_alert.getvalue())
                _audio_path = _audio.name
            with st.spinner(alert_labels["spinner"]):
                _model = get_whisper_model("base")
                _segments, _info = _model.transcribe(_audio_path, beam_size=5, language={"de":"de","ro":"ro","sr":"sr"}.get(active_lang, "ro"), task="transcribe", vad_filter=True, condition_on_previous_text=False)
                _transcript = " ".join(seg.text.strip() for seg in _segments).strip()
            if _transcript:
                # Update the actual keyed widget state; setting only its value= argument
                # does not replace an already-initialized Streamlit text_area value.
                st.session_state["driver_alert_text"] = _transcript
                st.session_state["driver_alert_transcript"] = _transcript
                st.session_state["driver_alert_original"] = _transcript
                st.session_state["driver_alert_translation_de"] = ""
                if _info.language in ("ro", "sr"):
                    try:
                        _tr = requests.get(
                            "https://translate.googleapis.com/translate_a/single",
                            params={"client":"gtx", "sl":_info.language, "tl":"de", "dt":"t", "q":_transcript},
                            timeout=8,
                        )
                        _tr.raise_for_status()
                        _tr_data = _tr.json()
                        _translated = "".join(part[0] for part in (_tr_data[0] or []) if part and part[0])
                        st.session_state["driver_alert_translation_de"] = _translated.strip()
                    except Exception:
                        st.session_state["driver_alert_translation_de"] = ""
                    if not st.session_state.get("driver_alert_translation_de"):
                        try:
                            _fallback_tr = requests.get(
                                "https://api.mymemory.translated.net/get",
                                params={"q": _transcript, "langpair": f"{_info.language}|de"}, timeout=10,
                            )
                            _fallback_tr.raise_for_status()
                            _fallback_json = _fallback_tr.json()
                            _fallback_text = str((_fallback_json.get("responseData") or {}).get("translatedText") or "").strip()
                            if _fallback_text and _fallback_text.casefold() != _transcript.casefold():
                                st.session_state["driver_alert_translation_de"] = _fallback_text
                        except Exception:
                            pass
                st.success(f"Erkannt / detectat: {_info.language} ({_info.language_probability:.0%})")
            else:
                st.warning({"de":"Kein Text erkannt. Bitte erneut aufnehmen.", "ro":"Nu s-a recunoscut text. Încercați din nou.", "sr":"Tekst nije prepoznat. Pokušajte ponovo."}[active_lang])
        except Exception as _err:
            st.error(f"Transkriptionsfehler / Eroare la transcriere: {_err}")
        finally:
            if _audio_path and os.path.exists(_audio_path):
                os.unlink(_audio_path)
    if "driver_alert_text" not in st.session_state:
        st.session_state["driver_alert_text"] = st.session_state.get("driver_alert_transcript", "")
    alert_text = st.text_area(alert_labels["note"], placeholder=alert_labels["placeholder"], key="driver_alert_text")
    _translated_feedback = st.session_state.get("driver_alert_translation_de", "")
    if _translated_feedback:
        st.markdown({"de":"**Deutsche Übersetzung für den Außendienst:**", "ro":"**Traducere în germană pentru agentul de vânzări:**", "sr":"**Nemački prevod za komercijalistu:**"}[active_lang])
        st.info(_translated_feedback)
    elif st.session_state.get("driver_alert_original") and active_lang in ("ro", "sr"):
        st.caption("Deutsche Übersetzung derzeit nicht verfügbar. Der Originaltext bleibt erhalten.")

    if st.button(L["driver_alert_btn"]):
        if not (alert_text or "").strip():
            st.warning({"de":"Bitte zuerst eine Feedback-Nachricht aufnehmen oder eingeben.", "ro":"Înregistrați sau introduceți mai întâi mesajul de feedback.", "sr":"Prvo snimite ili unesite poruku povratnih informacija."}[active_lang])
            st.stop()
        _original_feedback = (alert_text or "").strip()
        # Translate typed or transcribed notes into German for field sales; auto-detect source language.
        _translation_for_task = ""
        try:
            _tr = requests.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client":"gtx", "sl":"auto", "tl":"de", "dt":"t", "q":_original_feedback},
                timeout=8,
            )
            _tr.raise_for_status()
            _tr_data = _tr.json()
            _translation_for_task = "".join(part[0] for part in (_tr_data[0] or []) if part and part[0]).strip()
            if str(_tr_data[2] if len(_tr_data) > 2 else "").lower().startswith("de"):
                _translation_for_task = _original_feedback
        except Exception:
            _translation_for_task = ""
        if not _translation_for_task.strip() and active_lang in ("ro", "sr"):
            try:
                _fallback_tr = requests.get(
                    "https://api.mymemory.translated.net/get",
                    params={"q": _original_feedback, "langpair": f"{active_lang}|de"}, timeout=10,
                )
                _fallback_tr.raise_for_status()
                _fallback_json = _fallback_tr.json()
                _translation_for_task = str((_fallback_json.get("responseData") or {}).get("translatedText") or "").strip()
            except Exception:
                _translation_for_task = ""
        if _translation_for_task.strip() == _original_feedback and active_lang in ("ro", "sr"):
            # Do not pass an unchanged Romanian/Serbian original off as a German translation.
            _translation_for_task = ""

        conn = sqlite3.connect(OFFLINE_DB)
        c = conn.cursor()
        _priority = "HOCH" if alert_cat == "QUALITÄTSMANGEL" else "NORMAL"
        _task_status = "NEU"
        _assigned_sales = "Dominique Kieburg (Außendienst)"
        c.execute("INSERT INTO driver_alerts (driver_name, customer_name, category, alert_text, timestamp, status, translated_text, task_status, priority, appointment, sales_notes, assigned_to) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (user['name'], selected_customer_alert, alert_cat, _original_feedback, datetime.now().strftime("%d.%m.%Y %H:%M:%S"), "UNGELESEN", _translation_for_task, _task_status, _priority, "", "", _assigned_sales))
        _alert_id = c.lastrowid
        conn.commit()
        conn.close()
        _task_body = (
            f"Kundenfeedback / Fahrer-Rückmeldung\n"
            f"Interne GastroLingua-Aufgabe: automatisch erstellt\n"
            f"Zuständiger Außendienst: {_assigned_sales}\n"
            f"Priorität: {_priority}\n"
            f"Kundenkonto: {selected_customer_alert}\n"
            f"Kategorie: {category_labels['de'][alert_cat]} ({alert_cat})\n"
            f"Originalmeldung ({active_lang}): {_original_feedback}"
        )
        if _translation_for_task:
            _task_body += f"\nDeutsche Übersetzung: {_translation_for_task}"
        hs_task_result = hubspot.create_crm_task(f"Kundenfeedback ({selected_customer_alert})", _task_body, alert_cat)
        if hs_task_result.get("status") == "SUCCESS":
            if hs_task_result.get("task_id"):
                _task_conn = sqlite3.connect(OFFLINE_DB)
                try:
                    with _task_conn:
                        _task_conn.execute(
                            "INSERT INTO hubspot_demo_tasks (task_key, task_id) VALUES (?,?)",
                            (f"driver:{_alert_id}", str(hs_task_result["task_id"])),
                        )
                finally:
                    _task_conn.close()
            st.success(f"HubSpot-Aufgabe wurde bestätigt angelegt (Aufgaben-ID: {hs_task_result.get('task_id', 'unbekannt')}). Kundenkonto: {selected_customer_alert}")
        elif hs_task_result.get("status") == "MOCK":
            st.info(f"Demo: Alert lokal gespeichert; keine HubSpot-Aufgabe angelegt. Kundenkonto: {selected_customer_alert}")
        else:
            st.warning(f"Alert lokal gespeichert, HubSpot-Aufgabe konnte nicht bestätigt werden. Ergebnis: {hs_task_result.get('status', 'unbekannt')}")

# ROLLE 4: RAMPEN-KONTROLLEUR (THOMAS MÜLLER)
elif "4. Rampen-Kontrolleur" in selected_role_key:
    st.subheader(L["rampe_header"])
    
    rampe_orders = [o for o in st.session_state.active_orders.values() if o["current_stage"] in ["6_geliefert", "7_abgeschlossen"]]
    
    if not rampe_orders:
        st.info(L["no_rampe_orders"])
    else:
        for deal in rampe_orders:
            if deal["rampe_locked"]:
                if not deal.get("hubspot_office_stage_sent"):
                    if st.button("Auftragsstatus nach der Rampe weiterführen", key=f"ramp_followup_{deal['deal_id']}"):
                        sync_office_stage(hubspot, deal)
                        st.rerun()
                st.markdown(f"<div class='firewall-locked'>✅ #{deal['deal_id']} Physisch geprüft & versiegelt von {user['name']}! (7_abgeschlossen)</div>", unsafe_allow_html=True)
            else:
                st.write(f"### LKW-Rückkehr Prüfung: #{deal['deal_id']} ({deal['customer']})")
                
                st.write("#### 📋 Retourenprüfung je Artikel – Entscheidung an den Innendienst")
                if deal.get("retouren_driver"):
                    _return_conn = sqlite3.connect(OFFLINE_DB)
                    _return_conn.execute("""CREATE TABLE IF NOT EXISTS return_cases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, case_key TEXT UNIQUE, deal_id TEXT,
                        customer_name TEXT, item_name TEXT, sku TEXT, quantity INTEGER DEFAULT 1,
                        delivery_date TEXT, driver_reason TEXT, goods_condition TEXT DEFAULT '',
                        credit_decision TEXT DEFAULT 'KLÄRUNG ERFORDERLICH', status TEXT DEFAULT 'NEU',
                        sales_action TEXT DEFAULT '', sales_notes TEXT DEFAULT '', created_at TEXT, updated_at TEXT)""")
                    for _ri, r in enumerate(deal["retouren_driver"]):
                        _case_key = f"{deal['deal_id']}:{_ri}"
                        _existing_case = _return_conn.execute("SELECT goods_condition, credit_decision, status FROM return_cases WHERE case_key=?", (_case_key,)).fetchone()
                        st.markdown(f"**📦 {catalog_product_display(r.get('item','Artikel'), 'de', r.get('sku'))} · Menge: {r.get('qty',1)} · Kunde: {deal.get('customer','Kunde')}**")
                        st.caption(f"Fahrer-Grund: {return_reason_german(r.get('reason','Nicht angegeben'))} · Ursprüngliches Lieferdatum: {r.get('delivery_date','–')}")
                        _cond_options = ["Einwandfrei / wiederverkaufsfähig", "Verpackung beschädigt", "Ware welk / Qualitätsmangel", "MHD zu kurz / ältere Ware", "Falschlieferung", "Bruch / nicht verkaufsfähig", "Unklar – weitere Prüfung"]
                        _credit_options = ["Gutschrift grundsätzlich möglich", "Klärung erforderlich – noch keine Gutschrift", "Keine Gutschrift empfohlen"]
                        _old_cond = _existing_case[0] if _existing_case and _existing_case[0] in _cond_options else "Unklar – weitere Prüfung"
                        _old_credit = _existing_case[1] if _existing_case and _existing_case[1] in _credit_options else "Klärung erforderlich – noch keine Gutschrift"
                        _cc1, _cc2 = st.columns(2)
                        _goods_condition = _cc1.selectbox("Zustand der Ware", _cond_options, index=_cond_options.index(_old_cond), key=f"ramp_return_cond_{_case_key}")
                        _credit_decision = _cc2.selectbox("Gutschrift / Klärung", _credit_options, index=_credit_options.index(_old_credit), key=f"ramp_return_credit_{_case_key}")
                        if st.button(f"📨 Prüfung an Innendienst übergeben · {r.get('item','Artikel')}", key=f"ramp_return_submit_{_case_key}"):
                            _now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                            _return_conn.execute("""INSERT INTO return_cases
                                (case_key,deal_id,customer_name,item_name,sku,quantity,delivery_date,driver_reason,goods_condition,credit_decision,status,sales_action,sales_notes,created_at,updated_at)
                                VALUES (?,?,?,?,?,?,?,?,?,?, 'OFFEN_INNENDIENST','','',?,?)
                                ON CONFLICT(case_key) DO UPDATE SET goods_condition=excluded.goods_condition,
                                credit_decision=excluded.credit_decision,status='OFFEN_INNENDIENST',archived=0,updated_at=excluded.updated_at""",
                                (_case_key,str(deal['deal_id']),str(deal.get('customer','Kunde')),catalog_product_display(r.get('item','Artikel'), 'de', r.get('sku')),
                                 str(r.get('sku','')),int(r.get('qty',1)),str(r.get('delivery_date','')),return_reason_german(r.get('reason','')),
                                 _goods_condition,_credit_decision,_now,_now))
                            _return_conn.commit()
                            _task_item = catalog_product_display(r.get("item", "Artikel"), "de", r.get("sku"))
                            send_office_task(
                                hubspot, f"return:{_case_key}", deal.get("hs_id") or deal["deal_id"],
                                "RETOURE", f"Retoure prüfen · {deal['customer']} · {_task_item}",
                                f"Auftrag #{deal['deal_id']}. Artikel: {_task_item}. Menge: {r.get('qty', 1)}. "
                                f"Zustand an der Rampe: {_goods_condition}. Einschätzung: {_credit_decision}. "
                                "Bitte die Entscheidung in GastroLingua im Innendienst festhalten.",
                            )
                            st.success("Prüfung gespeichert und an den Innendienst übergeben.")
                            st.rerun()
                        if _existing_case:
                            st.success("✓ An den Innendienst übergeben")
                        st.divider()
                    _return_conn.close()
                else:
                    st.info("Keine Retouren vom Fahrer erfasst.")
                
                drv_lg = deal.get("leergut_driver", {"e2": 0, "rolli": 0, "palette": 0})
                st.write(f"**Vom Fahrer erfasstes Leergut:** `{drv_lg.get('e2', 0)} E2-Kisten`, `{drv_lg.get('rolli', 0)} Rollis`")
                
                col_r1, col_p2, col_p3 = st.columns(3)
                v_e2 = col_r1.number_input("Nachgezählte E2-Kisten an Rampe:", value=drv_lg.get("e2", 5), key=f"r_e2_{deal['deal_id']}")
                v_roll = col_p2.number_input("Nachgezählte Rollis:", value=drv_lg.get("rolli", 1), key=f"r_roll_{deal['deal_id']}")
                v_pal = col_p3.number_input("Nachgezählte Europaletten:", value=drv_lg.get("palette", 0), key=f"r_pal_{deal['deal_id']}")
                
                haccp_status = st.selectbox("HACCP Hygienestatus Wareneingang:", ["A-Ware (Wiederverkaufsfähig)", "B-Ware (Werksverkauf)", "C-Ware (Bruch / Entsorgung)"], key=f"haccp_{deal['deal_id']}")
                
                if st.button(f"🔒 7. RAMPE PRÜFEN & VERSIEGELN #{deal['deal_id']}", key=f"lck_{deal['deal_id']}"):
                    deal["rampe_locked"] = True
                    deal["leergut_verified"] = {"e2": v_e2, "rolli": v_roll, "palette": v_pal}
                    deal["haccp_status"] = haccp_status
                    deal["current_stage"] = "7_abgeschlossen"
                    deal["stage_label"] = L["stage_7"]
                    
                    sync_res = hubspot.sync_stage(deal.get("hs_id", deal["deal_id"]), "7_abgeschlossen", "Rampen-Prüfung Abgeschlossen")
                    if sync_res.get("status") != "SUCCESS":
                        st.error(f"Rampenprüfung lokal gespeichert; HubSpot-Phase NICHT bestätigt: {sync_res.get('msg', sync_res.get('status'))}")
                    else:
                        st.success(sync_res.get("msg", "HubSpot-Phase aktualisiert."))
                    if v_e2 > 0 and not deal.get("gutschrift_gebucht"):
                        send_office_task(
                            hubspot, f"empties:{deal['deal_id']}", deal.get("hs_id") or deal["deal_id"],
                            "LEERGUT", f"Leergutgutschrift buchen · {deal['customer']}",
                            f"Auftrag #{deal['deal_id']}. An der Rampe bestätigt: {v_e2} E2-Kisten. "
                            "Bitte die Leergutgutschrift in GastroLingua im Innendienst bearbeiten.",
                        )
                    st.toast("🎉 Rampen-Firewall versiegelt!", icon="🔒")
                    st.rerun()

# ROLLE 5: INNENDIENST
elif "5. Innendienst" in selected_role_key:
    st.subheader(L["innendienst_header"])

    st.markdown("### 📬 Retouren- und Reklamationsfälle vom Fahrer / von der Rampe")
    _sales_conn = sqlite3.connect(OFFLINE_DB)
    _sales_conn.execute("""CREATE TABLE IF NOT EXISTS return_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT, case_key TEXT UNIQUE, deal_id TEXT,
        customer_name TEXT, item_name TEXT, sku TEXT, quantity INTEGER DEFAULT 1,
        delivery_date TEXT, driver_reason TEXT, goods_condition TEXT DEFAULT '',
        credit_decision TEXT DEFAULT 'KLÄRUNG ERFORDERLICH', status TEXT DEFAULT 'NEU',
        sales_action TEXT DEFAULT '', sales_notes TEXT DEFAULT '', created_at TEXT, updated_at TEXT, archived INTEGER DEFAULT 0)""")
    _sales_conn.commit()
    _sales_cases = _sales_conn.execute("""SELECT id, deal_id, customer_name, item_name, quantity, case_key,
        delivery_date, driver_reason, goods_condition, credit_decision, status, sales_action, sales_notes
        FROM return_cases WHERE COALESCE(archived,0)=0 AND COALESCE(status,'')<>'ERLEDIGT'
        ORDER BY CASE WHEN status='OFFEN_INNENDIENST' THEN 0 WHEN status='IN_BEARBEITUNG' THEN 1 ELSE 2 END, id DESC""").fetchall()
    _sales_conn.close()
    if not _sales_cases:
        st.info("Keine offenen Retourenfälle im Innendienst.")
    for _case in _sales_cases:
        (_cid,_did,_cust,_item,_qty,_case_key,_ddate,_reason,_condition,_decision,_status,_action,_notes)=_case
        with st.container(border=True):
            st.markdown(f"### 🏷️ {_cust}")
            st.markdown(f"**Artikel:** {_item} · **Menge:** {_qty} · **Auftrag:** #{_did}")
            st.write(f"**Ursprüngliches Lieferdatum:** {_ddate or '–'}")
            st.write(f"**Fahrer-Grund:** {return_reason_german(_reason) or '–'}")
            st.write(f"**Zustand Rampe:** {_condition or 'Noch nicht geprüft'}")
            st.write(f"**Rampeneinschätzung:** {_decision or 'Klärung erforderlich'}")
            _action_options = ["Gutschrift freigeben", "Kunden kontaktieren / Rückfrage", "Fall zur weiteren Prüfung öffnen", "Gutschrift ablehnen"]
            _current_action = _action if _action in _action_options else _action_options[2]
            _a1,_a2 = st.columns(2)
            _chosen_action = _a1.selectbox("Entscheidung Innendienst", _action_options, index=_action_options.index(_current_action), key=f"sales_return_action_{_cid}")
            _case_status_options = ["OFFEN_INNENDIENST", "IN_BEARBEITUNG", "WARTET_AUF_KUNDE", "ERLEDIGT"]
            _status_map = {"OFFEN_INNENDIENST":"Offen", "IN_BEARBEITUNG":"In Bearbeitung", "WARTET_AUF_KUNDE":"Wartet auf Kunden", "ERLEDIGT":"Erledigt"}
            _chosen_status = _a2.selectbox("Fallstatus", _case_status_options, index=_case_status_options.index(_status) if _status in _case_status_options else 0, format_func=lambda x:_status_map[x], key=f"sales_return_status_{_cid}")
            _sales_note = st.text_area("Notiz / Kundenkontakt / Begründung", value=_notes or "", key=f"sales_return_note_{_cid}")
            if st.button("💾 Entscheidung speichern", key=f"sales_return_save_{_cid}", type="primary"):
                _save_conn = None
                try:
                    _save_conn = sqlite3.connect(OFFLINE_DB, timeout=10)
                    _save_conn.execute("BEGIN IMMEDIATE")
                    _save_cursor = _save_conn.execute(
                        "UPDATE return_cases SET sales_action=?, status=?, sales_notes=?, updated_at=? WHERE id=? AND COALESCE(archived,0)=0",
                        (_chosen_action, _chosen_status, _sales_note, datetime.now().strftime("%d.%m.%Y %H:%M:%S"), _cid))
                    if _save_cursor.rowcount != 1:
                        _save_conn.rollback()
                        st.error("Nicht gespeichert: Der Fall ist nicht mehr aktiv oder wurde nicht gefunden. Bitte Liste aktualisieren.")
                    else:
                        _save_conn.commit()
                        _verify = _save_conn.execute("SELECT sales_action, status, sales_notes FROM return_cases WHERE id=?", (_cid,)).fetchone()
                        if _verify and _verify[0] == _chosen_action and _verify[1] == _chosen_status and (_verify[2] or "") == _sales_note:
                            if _chosen_status == "ERLEDIGT":
                                sync_task_completion(hubspot, f"return:{_case_key}")
                                _order_for_case = st.session_state.active_orders.get(str(_did))
                                if _order_for_case is not None:
                                    sync_office_stage(hubspot, _order_for_case)
                                st.toast(f"Fall für {_cust} erledigt.", icon="✅")
                                st.rerun()
                            st.success(f"✅ Datenbank bestätigt: {_cust} · {_chosen_action} · {_status_map[_chosen_status]}.")
                        else:
                            st.error("Die Datenbank hat die gespeicherten Werte nicht bestätigt. Bitte nicht mehrfach klicken.")
                except sqlite3.Error as _save_err:
                    if _save_conn:
                        _save_conn.rollback()
                    st.error(f"Speichern fehlgeschlagen: {_save_err}. Deine Eingaben bleiben auf der Seite sichtbar.")
                finally:
                    if _save_conn:
                        _save_conn.close()
    _innendienst_orders = [
        deal for deal in st.session_state.active_orders.values()
        if not deal.get("gutschrift_gebucht")
    ]
    if not _innendienst_orders:
        st.info("ℹ️ Keine aktiven Aufträge zur Bearbeitung vorhanden.")
    else:
        for deal in _innendienst_orders:
            st.write(f"### Auftrag #{deal['deal_id']} ({deal['customer']})")
            if not deal["rampe_locked"]:
                st.error("🛑 SPERRE AKTIV: keine Gutschrift möglich! Rampenfreigabe von Friedrich Merz nach Tourenende fehlt.")
            else:
                st.success("✅ FREIGESCHALTET: Rampen-Prüfung liegt vor.")
                v_e2 = deal.get("leergut_verified", {}).get("e2", 0)
                gutschrift_val = v_e2 * 2.50
                st.write(f"Berechneter Gutschriftenbetrag Leergut (`{v_e2} Kisten` x 2,50 €): `{gutschrift_val:.2f} €`")
                
                if st.button(f"💶 Gutschrift 1-Klick buchen #{deal['deal_id']}", key=f"gut_{deal['deal_id']}"):
                    deal["gutschrift_gebucht"] = True
                    if v_e2 > 0:
                        sync_task_completion(hubspot, f"empties:{deal['deal_id']}")
                    sync_office_stage(hubspot, deal)
                    st.toast("💶 Gutschrift im ERP gebucht!", icon="💶")
                    st.rerun()

# ROLLE 7: AUSSENDIENST
elif "7. Vertrieb" in selected_role_key:
    st.subheader(L["sales_header"])
    _sales_feedback = st.session_state.get("sales_task_save_feedback")
    if _sales_feedback:
        _feedback_ok, _feedback_text = _sales_feedback
        if _feedback_ok:
            st.success(_feedback_text)
        else:
            st.warning(_feedback_text)
        if st.button("Speicherbestätigung schließen"):
            st.session_state.pop("sales_task_save_feedback", None)
            st.rerun()
    st.caption("Automatisch erstellte Aufgaben aus Fahrer-Rückmeldungen. Änderungen werden lokal gespeichert.")
    st.markdown("### 🗓️ Terminkalender")
    _calendar_conn = sqlite3.connect(OFFLINE_DB)
    _calendar_rows = _calendar_conn.execute("SELECT customer_name, appointment, task_status, priority, assigned_to FROM driver_alerts WHERE COALESCE(archived,0)=0 AND appointment IS NOT NULL AND trim(appointment)<>'' ORDER BY appointment").fetchall()
    _calendar_conn.close()
    _calendar_events = []
    for _ccust, _cappointment, _cstatus, _cpriority, _cassigned in _calendar_rows:
        _calendar_events.append({"Termin": _cappointment, "Kunde": _ccust, "Priorität": _cpriority or "NORMAL", "Status": _cstatus or "NEU", "Zuständig": _cassigned or "Außendienst"})
    if _calendar_events:
        import calendar as _calendar_module
        _today = date.today()
        _month_name = {1:"Januar",2:"Februar",3:"März",4:"April",5:"Mai",6:"Juni",7:"Juli",8:"August",9:"September",10:"Oktober",11:"November",12:"Dezember"}[_today.month]
        st.markdown(f"#### {_month_name} {_today.year}")
        _events_by_day = {}
        _unparsed_events = []
        for _ev in _calendar_events:
            _appt_text = str(_ev.get("Termin") or "").strip()
            _parsed_dt = None
            for _fmt in ("%d.%m.%Y, %H:%M Uhr", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d", "%Y/%m/%d, %H:%M Uhr", "%Y/%m/%d %H:%M"):
                try:
                    _parsed_dt = datetime.strptime(_appt_text, _fmt)
                    break
                except (ValueError, TypeError):
                    pass
            if _parsed_dt:
                if _parsed_dt.year == _today.year and _parsed_dt.month == _today.month:
                    _events_by_day.setdefault(_parsed_dt.day, []).append((_ev, _parsed_dt))
                else:
                    _unparsed_events.append(_ev)
            else:
                _unparsed_events.append(_ev)
        _weekday_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        _head_cols = st.columns(7)
        for _idx, _weekday in enumerate(_weekday_labels):
            _head_cols[_idx].markdown(f"**{_weekday}**")
        for _week in _calendar_module.monthcalendar(_today.year, _today.month):
            _day_cols = st.columns(7)
            for _idx, _day in enumerate(_week):
                with _day_cols[_idx]:
                    if not _day:
                        st.caption(" ")
                    else:
                        _day_events = _events_by_day.get(_day, [])
                        if _day_events:
                            st.markdown(f"**📌 {_day}**")
                            for _ev, _dt in _day_events:
                                st.caption(f"{_dt.strftime('%H:%M')} · {str(_ev.get('Kunde','Kunde'))[:18]}")
                        else:
                            st.markdown(f"**{_day}**")
        with st.expander("📋 Alle Termine", expanded=True):
            st.dataframe(_calendar_events, use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Gesprächstermine eingetragen. Lege in einer Aufgabe Datum und Uhrzeit fest; der Termin erscheint anschließend hier.")
    with st.expander("🎙️ Gesprächsnotiz per Sprache erfassen", expanded=False):
        st.caption("Nimm eine kurze Notiz auf. Die Transkription benötigt faster-whisper und wird vor dem Speichern überprüfbar angezeigt.")
        _sales_audio = st.audio_input("Gesprächsnotiz aufnehmen", key="sales_audio_note") if hasattr(st, "audio_input") else None
        if _sales_audio is not None:
            if st.button("🎧 Aufnahme transkribieren", key="sales_transcribe_note"):
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as _sales_tmp:
                        _sales_tmp.write(_sales_audio.getvalue())
                        _sales_audio_path = _sales_tmp.name
                    try:
                        _sales_model = get_whisper_model("base")
                        _sales_segments, _sales_info = _sales_model.transcribe(_sales_audio_path, beam_size=5, language={"de":"de","ro":"ro","sr":"sr"}.get(active_lang), task="transcribe", vad_filter=True)
                        _sales_transcript = " ".join(seg.text.strip() for seg in _sales_segments).strip()
                        if _sales_transcript:
                            st.session_state["sales_voice_transcript"] = _sales_transcript
                            st.success(f"Transkription erkannt ({_sales_info.language}). Bitte unten prüfen und in die gewünschte Aufgabe übernehmen.")
                        else:
                            st.warning("Kein Text erkannt. Bitte erneut aufnehmen.")
                    finally:
                        if os.path.exists(_sales_audio_path): os.unlink(_sales_audio_path)
                except Exception as _sales_err:
                    st.error(f"Sprachtranskription nicht verfügbar: {_sales_err}")
        if st.session_state.get("sales_voice_transcript"):
            st.text_area("Erkannter Text (bearbeitbar)", key="sales_voice_transcript")
            if st.button("📋 Erkannte Notiz anzeigen", key="sales_voice_apply"):
                st.code(st.session_state.get("sales_voice_transcript", ""))
                st.info("Diese allgemeine Aufnahme ist ein Entwurf. Für die direkte Zuordnung bitte die Sprachnotiz innerhalb der konkreten Kundenaufgabe verwenden.")
    conn = sqlite3.connect(OFFLINE_DB)
    c = conn.cursor()
    c.execute("SELECT id, driver_name, customer_name, category, alert_text, timestamp, translated_text, task_status, priority, appointment, sales_notes, assigned_to FROM driver_alerts WHERE COALESCE(archived,0)=0 ORDER BY CASE WHEN priority='HOCH' THEN 0 ELSE 1 END, CASE WHEN appointment IS NOT NULL AND trim(appointment)<>'' THEN 0 ELSE 1 END, id DESC")
    alerts = c.fetchall()
    conn.close()

    if not alerts:
        st.info(L["no_alerts"])
    else:
        _status_names = {"NEU":"Neu", "IN_BEARBEITUNG":"In Bearbeitung", "TERMIN_VEREINBART":"Termin vereinbart", "ERLEDIGT":"Erledigt"}
        _category_names = {"QUALITÄTSMANGEL":"Qualitätsmangel", "PREISDRUCK":"Preisvergleich / Preisdruck", "UPSELLING_WUNSCH":"Zusätzlicher Bedarf", "SONSTIGES":"Sonstiges"}
        _open_alert_count = sum(alert[7] != "ERLEDIGT" for alert in alerts)
        st.write(f"**Offene Außendienst-Aufgaben: {_open_alert_count}**")
        _show_completed_alerts = st.checkbox("Erledigte Außendienst-Aufgaben anzeigen")
        if not _open_alert_count and not _show_completed_alerts:
            st.info("Keine offenen Außendienst-Aufgaben.")
        for a_id, drv, cust, cat, txt, ts, translated_txt, task_status, priority, appointment, sales_notes, assigned_to in alerts:
            if task_status == "ERLEDIGT" and not _show_completed_alerts:
                continue
            import html
            _priority = priority or ("HOCH" if cat == "QUALITÄTSMANGEL" else "NORMAL")
            _task_status = task_status or ("ERLEDIGT" if str(ts) == "ERLEDIGT" else "NEU")
            _original_html = html.escape(str(txt or ''))
            _translated_html = html.escape(str(translated_txt or ''))
            with st.container(border=True):
                if _task_status == "ERLEDIGT":
                    st.success("Erledigt")
                else:
                    st.info(f"Offen · {_status_names.get(_task_status, _task_status)}")
                st.markdown(f"<div class='task-customer'>{'✅' if _task_status == 'ERLEDIGT' else ('🔴' if _priority == 'HOCH' else '📌')} {html.escape(str(cust))}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='task-meta'>Aufgabe #{a_id} · <b>{html.escape(_category_names.get(str(cat), str(cat)))}</b> · Priorität: <b>{_priority}</b> · Status: {_status_names.get(_task_status, _task_status)}</div>", unsafe_allow_html=True)
                st.caption(f"Erstellt: {ts} · Fahrer: {drv} · Zuständig: {assigned_to or 'Außendienst'}")
                st.markdown(f"**Originalmeldung:** { _original_html }", unsafe_allow_html=True)
                if translated_txt and translated_txt.strip() and translated_txt.strip() != (txt or '').strip():
                    st.info(f"Deutsche Übersetzung: {translated_txt}")
                elif str(txt or '').strip():
                    st.warning("Für diese Rückmeldung liegt keine bestätigte deutsche Übersetzung vor. Der Originaltext bleibt erhalten.")
                    if st.button("🌐 Deutsche Übersetzung erneut versuchen", key=f"retry_translation_{a_id}"):
                        try:
                            _retry_translation = ""
                            _translation_errors = []
                            try:
                                _retry = requests.get("https://translate.googleapis.com/translate_a/single", params={"client":"gtx", "sl":"auto", "tl":"de", "dt":"t", "q":str(txt)}, timeout=10)
                                _retry.raise_for_status()
                                _retry_data = _retry.json()
                                _retry_translation = "".join(part[0] for part in (_retry_data[0] or []) if part and part[0]).strip()
                                _detected = str(_retry_data[2] if len(_retry_data) > 2 else "").lower()
                            except Exception as _google_err:
                                _translation_errors.append(str(_google_err))
                                _detected = ""
                            if not _retry_translation:
                                try:
                                    _fallback = requests.get("https://api.mymemory.translated.net/get", params={"q":str(txt), "langpair":"autodetect|de"}, timeout=10)
                                    _fallback.raise_for_status()
                                    _fallback_json = _fallback.json()
                                    _retry_translation = str((_fallback_json.get("responseData") or {}).get("translatedText") or "").strip()
                                except Exception as _fallback_err:
                                    _translation_errors.append(str(_fallback_err))
                            if _retry_translation and _retry_translation.strip().casefold() != str(txt).strip().casefold():
                                _tr_conn = sqlite3.connect(OFFLINE_DB)
                                _tr_conn.execute("UPDATE driver_alerts SET translated_text=? WHERE id=?", (_retry_translation, a_id))
                                _tr_conn.commit(); _tr_conn.close()
                                st.success("Deutsche Übersetzung gespeichert.")
                                st.rerun()
                            elif _detected.startswith("de") or str(txt).strip().casefold() == str(_retry_translation).strip().casefold():
                                st.info("Die Nachricht scheint bereits auf Deutsch zu sein.")
                            else:
                                st.warning("Keine Übersetzung erhalten. Bitte Internetverbindung prüfen oder später erneut versuchen.")
                        except Exception as _translation_outer_err:
                            st.error(f"Übersetzung fehlgeschlagen: {_translation_outer_err}")
                with st.expander("🎙️ Sprachnotiz zu diesem Kunden aufnehmen", expanded=True):
                    _task_audio = st.audio_input("Gesprächsnotiz aufnehmen", key=f"task_audio_{a_id}") if hasattr(st, "audio_input") else None
                    if _task_audio is not None and st.button("🎧 Sprachnotiz transkribieren", key=f"task_transcribe_{a_id}"):
                        try:
                            import tempfile
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as _task_tmp:
                                _task_tmp.write(_task_audio.getvalue())
                                _task_audio_path = _task_tmp.name
                            try:
                                _task_model = get_whisper_model("base")
                                _task_segments, _task_info = _task_model.transcribe(_task_audio_path, beam_size=5, language={"de":"de","ro":"ro","sr":"sr"}.get(active_lang), task="transcribe", vad_filter=True)
                                _task_transcript = " ".join(seg.text.strip() for seg in _task_segments).strip()
                                if _task_transcript:
                                    st.session_state[f"task_voice_transcript_{a_id}"] = _task_transcript
                                    # Populate the actual keyed text area before rerun, not just its default value.
                                    st.session_state[f"task_notes_{a_id}"] = _task_transcript
                                    st.success("Sprachnotiz erkannt und in die Gesprächsnotiz übernommen. Bitte prüfen und speichern.")
                                    st.rerun()
                                else:
                                    st.warning("Kein Text erkannt. Bitte erneut aufnehmen.")
                            finally:
                                if os.path.exists(_task_audio_path):
                                    os.unlink(_task_audio_path)
                        except Exception as _task_voice_err:
                            st.error(f"Spracherkennung nicht verfügbar: {_task_voice_err}. Bitte faster-whisper installieren oder die Notiz eintippen.")
                with st.form(f"sales_task_form_{a_id}"):
                    _status_options = ["NEU", "IN_BEARBEITUNG", "TERMIN_VEREINBART", "ERLEDIGT"]
                    _current_idx = _status_options.index(_task_status) if _task_status in _status_options else 0
                    _new_status = st.selectbox("Bearbeitungsstatus", _status_options, index=_current_idx, format_func=lambda x: _status_names[x], key=f"task_status_{a_id}")
                    # Kalenderfelder für Außendiensttermine; ältere Freitext-Termine bleiben sichtbar.
                    _old_appt = str(appointment or '').strip()
                    _appt_date_default = date.today()
                    _appt_time_default = datetime.now().replace(second=0, microsecond=0).time()
                    try:
                        _appt_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})[, ]+([0-2]\d):([0-5]\d)', _old_appt)
                        if _appt_match:
                            _appt_date_default = date(int(_appt_match.group(3)), int(_appt_match.group(2)), int(_appt_match.group(1)))
                            _appt_time_default = datetime.strptime(_appt_match.group(4)+':'+_appt_match.group(5), '%H:%M').time()
                        elif re.match(r'\d{4}-\d{2}-\d{2}', _old_appt):
                            _appt_date_default = date.fromisoformat(_old_appt[:10])
                    except Exception:
                        pass
                    _ac1, _ac2 = st.columns(2)
                    _appointment_date = _ac1.date_input("Besuchstermin", value=_appt_date_default, key=f"task_appointment_date_{a_id}")
                    _appointment_time = _ac2.time_input("Uhrzeit", value=_appt_time_default, key=f"task_appointment_time_{a_id}")
                    _notes_default = sales_notes or st.session_state.get(f"task_voice_transcript_{a_id}", "")
                    _notes_value = st.text_area("Gesprächsnotiz / Ergebnis (Text aus Sprache kann hier geprüft werden)", value=_notes_default, key=f"task_notes_{a_id}")
                    st.caption("Änderungen speichern übernimmt den gewählten Status. Aufgabe abschließen setzt den Status direkt auf Erledigt und meldet den Abschluss an HubSpot.")
                    _save_task = st.form_submit_button("💾 Änderungen speichern", use_container_width=True)
                    _finish_task = st.form_submit_button("✅ Aufgabe abschließen", type="primary", use_container_width=True)
                if _save_task or _finish_task:
                    if _finish_task:
                        _new_status = "ERLEDIGT"
                    conn = sqlite3.connect(OFFLINE_DB)
                    c = conn.cursor()
                    _appointment_value = f"{_appointment_date.strftime('%d.%m.%Y')}, {_appointment_time.strftime('%H:%M')} Uhr" if _appointment_date else ""
                    c.execute("UPDATE driver_alerts SET task_status=?, status=?, appointment=?, sales_notes=? WHERE id=?", (_new_status, "ERLEDIGT" if _new_status == "ERLEDIGT" else "UNGELESEN", _appointment_value, _notes_value.strip(), a_id))
                    conn.commit()
                    conn.close()
                    st.session_state.pop(f"task_voice_transcript_{a_id}", None)
                    if _new_status == "ERLEDIGT":
                        _sync_ok = sync_task_completion(hubspot, f"driver:{a_id}")
                        _feedback = (
                            (True, f"{cust}: Aufgabe erledigt und in HubSpot abgeschlossen.")
                            if _sync_ok else
                            (False, f"{cust}: Lokal erledigt. Der Abschluss in HubSpot wurde nicht bestätigt.")
                        )
                    else:
                        _body = "<br>".join(html.escape(str(line)) for line in (
                            f"Kundenkonto: {cust}",
                            f"Originalmeldung: {txt}",
                            f"Deutsche Übersetzung: {translated_txt or '–'}",
                            f"Status in GastroLingua: {_status_names[_new_status]}",
                            f"Besuchstermin: {_appointment_value or '–'}",
                            f"Gesprächsnotiz: {_notes_value.strip() or '–'}",
                        ))
                        _due = datetime.combine(_appointment_date, _appointment_time) if _appointment_date else None
                        _sync_error = sync_driver_task_details(hubspot, a_id, _body, _due)
                        _feedback = (
                            (False, f"{cust}: Lokal gespeichert. {_sync_error}")
                            if _sync_error else
                            (True, f"{cust}: Aufgabe und Termin gespeichert. HubSpot wurde aktualisiert.")
                        )
                    st.session_state["sales_task_save_feedback"] = _feedback
                    st.rerun()

# ROLLE 8: ADMIN
elif "8. Admin" in selected_role_key:
    st.subheader(L["admin_header"])
    conn = sqlite3.connect(OFFLINE_DB)
    c = conn.cursor()
    c.execute("SELECT customer_name, sku, product_name, timestamp FROM demand_reports")
    demands = c.fetchall()
    conn.close()
    if demands:
        st.dataframe(demands)
    else:
        st.info(L["no_demands"])

# ROLLE 6: DISPO
else:
    st.subheader(L["dispo_header"])
    st.info("🧪 DEMO-SIMULATION: Touren, Fahrzeugstatus und Kartenpositionen sind Beispieldaten. Es findet keine echte GPS-Ortung statt.")
    orders = list(st.session_state.active_orders.values())
    st.metric("Aktive Aufträge im System", len(orders))

    st.markdown("### " + rep_text("heading", active_lang))
    _all_cases = list(st.session_state.replacement_cases.values())
    _open_cases = [c for c in _all_cases if c.get("dispo_decision") == "Ausstehend"]
    if not _open_cases:
        st.success(rep_text("none", active_lang))
    else:
        for _case in _open_cases:
            _customer_reply = str(_case.get("customer_decision", "Offen"))
            _reply_lower = _customer_reply.lower()
            if "abgelehnt" in _reply_lower:
                st.error(rep_text("rejected", active_lang))
                if "später" in _reply_lower or "vormerken" in _reply_lower:
                    _next_step = rep_text("future", active_lang)
                elif "anderen ersatz" in _reply_lower:
                    _next_step = rep_text("other", active_lang)
                else:
                    _next_step = rep_text("check", active_lang)
            elif "angenommen" in _reply_lower or "akzeptiert" in _reply_lower:
                st.success(rep_text("accepted", active_lang))
                _next_step = rep_text("accept_next", active_lang)
            else:
                st.warning(rep_text("open", active_lang))
                _next_step = rep_text("open_next", active_lang)
            st.markdown(f"**Auftrag #{_case['order_id']} · {_case['customer']}**")
            _dispo_original = catalog_product_display(_case.get("original", "—"), active_lang, _case.get("original_sku"))
            _dispo_alternative = replacement_label_display(_case.get("alternative", "—"), active_lang)
            st.markdown(f"**{rep_text('original', active_lang)}:** {_dispo_original} · **{rep_text('alternative', active_lang)}:** {_dispo_alternative}")
            st.info(f"**{rep_text('next', active_lang)}:** {_next_step}")
            st.caption(f"{rep_text('case', active_lang)} {_case['case_id']} · {rep_text('reply', active_lang)}: {_customer_reply} · {rep_text('pending', active_lang)}")
            _decision_options = ["Ersatz mit Tour ausliefern (Disposition entscheidet)", "Ersatz herausnehmen – Original für spätere Lieferung vormerken", "Ersatz herausnehmen – Kunden soll anderen Ersatz wählen"]
            _decision = st.radio(f"{rep_text('decision', active_lang)} {_case['case_id']}", _decision_options, format_func=lambda x: rep_text("opt"+str(_decision_options.index(x)), active_lang), key=f"dispo_rep_dec_{_case['case_id']}")
            if st.button(f"{rep_text('save', active_lang)} · {rep_text('case', active_lang)} {_case['case_id']}", key=f"dispo_rep_save_{_case['case_id']}"):
                _case["dispo_decision"] = _decision
                _case["status"] = "Von Disposition entschieden"
                _case["decision_by"] = user.get("name", "Disposition")
                _case["decision_at"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                _case["future_preorder"] = "spätere Lieferung vormerken" in _decision
                st.success(rep_text("saved", active_lang))
                st.rerun()
    _all_cases = list(st.session_state.replacement_cases.values())
    _decided_cases = [c for c in _all_cases if c.get("dispo_decision") != "Ausstehend"]
    if _decided_cases:
        with st.expander(rep_text("completed", active_lang)):
            for _case in _decided_cases:
                st.markdown(f"**Auftrag #{_case.get('order_id')} · Ersatzfall {_case.get('case_id')}**")
                st.write(f"Kundenantwort: {_case.get('customer_decision', 'Offen')}")
                st.write(f"Dispositionsentscheidung: {_case.get('dispo_decision')}")
                st.caption(f"Entschieden von {_case.get('decision_by', 'Disposition')} am {_case.get('decision_at', 'Zeitpunkt nicht verfügbar')}")
    _all_cases = list(st.session_state.replacement_cases.values())
    if _all_cases:
        with st.expander(rep_text("all", active_lang)):
            st.dataframe(_all_cases, use_container_width=True, hide_index=True)

    if "demo_tours" not in st.session_state:
        st.session_state.demo_tours = {}
    if "demo_vehicle_status" not in st.session_state:
        st.session_state.demo_vehicle_status = {"LKW 01": "Bereit", "LKW 02": "Bereit", "LKW 03": "Bereit"}

    # Dauerhafte Standardtour je Kundenkonto/Restaurant (SQLite), separat von
    # der tagesaktuellen Zuordnung einzelner Aufträge.
    _tour_con = auth_db()
    _tour_con.execute("CREATE TABLE IF NOT EXISTS customer_tour_defaults (customer_key TEXT PRIMARY KEY, tour_id TEXT NOT NULL)")
    _tour_con.execute("""CREATE TABLE IF NOT EXISTS order_tour_assignments (
        order_id TEXT PRIMARY KEY, customer TEXT NOT NULL, tour_id TEXT NOT NULL,
        vehicle TEXT NOT NULL, driver TEXT NOT NULL, stop_order INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'Geplant', updated_at TEXT NOT NULL
    )""")
    _tour_con.commit()
    _tour_con.close()
    _tour_db_path = AUTH_DB
    _tour_names = {
        "tour1": {"de": "Tour 1", "ro": "Ruta 1", "sr": "Ruta 1"},
        "tour2": {"de": "Tour 2", "ro": "Ruta 2", "sr": "Ruta 2"},
    }
    _tour_drivers = {"tour1": "Zoka Gredeljevic", "tour2": "Nicolae Guta"}
    _tour_vehicles = {"tour1": "LKW 01", "tour2": "LKW 02"}
    _tour_label = lambda tid: f"{_tour_names[tid][active_lang]} · {_tour_vehicles[tid]} · {_tour_drivers[tid]}"
    st.markdown("### 🗺️ Feste Touren & Tagesplanung")
    st.caption({"de":"Stammkunden werden ihrer gespeicherten Standardtour zugeordnet. Paco kann einzelne Aufträge bei Krankheit oder Zeitänderungen jederzeit auf die andere Tour verschieben.", "ro":"Clienții permanenți sunt repartizați pe ruta standard salvată. Paco poate muta oricând comenzile pe cealaltă rută în caz de absență sau schimbări de program.", "sr":"Stalni kupci se dodeljuju sačuvanoj standardnoj ruti. Paco može u bilo kom trenutku da prebaci pojedinačne porudžbine na drugu rutu zbog odsustva vozača ili promene vremena."}[active_lang])

    _con = sqlite3.connect(_tour_db_path)
    _defaults = dict(_con.execute("SELECT customer_key, tour_id FROM customer_tour_defaults").fetchall())
    _saved_assignments = {str(r[0]): {"order_id": str(r[0]), "customer": r[1], "tour_id": r[2], "vehicle": r[3], "driver": r[4], "stop_order": int(r[5] or 1), "status": r[6], "updated_at": r[7]} for r in _con.execute("SELECT order_id, customer, tour_id, vehicle, driver, stop_order, status, updated_at FROM order_tour_assignments").fetchall()}
    _con.close()
    # Restore saved assignment for active orders after a rerun or app restart.
    _active_order_ids = {str(o.get("deal_id", "")) for o in orders}
    for _saved_oid, _saved_tour in _saved_assignments.items():
        if _saved_oid in _active_order_ids and _saved_oid not in st.session_state.demo_tours:
            st.session_state.demo_tours[_saved_oid] = dict(_saved_tour)
    # Die beiden fest eingerichteten Stammkunden werden bei neuen Aufträgen automatisch
    # einer festen Tour zugeordnet. Weitere Kunden bleiben zur manuellen Tagesplanung offen.
    _fixed_defaults = {"Brauhaus zum Hirschen": "tour1", "Ristorante Bella Italia": "tour2"}
    for _auto_order in orders:
        _auto_oid = str(_auto_order.get("deal_id", ""))
        _auto_customer = str(_auto_order.get("restaurant") or _auto_order.get("customer") or "")
        if _auto_oid and _auto_oid not in st.session_state.demo_tours:
            _auto_tid = _defaults.get(_auto_customer) or _fixed_defaults.get(_auto_customer)
            if _auto_tid:
                st.session_state.demo_tours[_auto_oid] = {
                    "order_id": _auto_oid, "label": f"{_auto_customer} · Auftrag #{_auto_oid}",
                    "customer": _auto_customer, "tour_id": _auto_tid,
                    "vehicle": _tour_vehicles[_auto_tid], "driver": _tour_drivers[_auto_tid],
                    "stop": "Stopp 1", "stop_order": 1, "status": "Geplant"
                }
    _customer_keys = sorted({str(o.get("restaurant") or o.get("customer") or "Unbekannter Kunde") for o in orders})
    _customer_keys = list(dict.fromkeys(_customer_keys + ["Brauhaus zum Hirschen", "Ristorante Bella Italia", "Restaurant Sarajevo", "Trattoria am Markt", "Hotel Rheinblick", "Restoran Dunav"]))
    _customer_names = {"de": "Stammkunde", "ro": "Client permanent", "sr": "Stalni kupac"}
    with st.expander({"de":"⚙️ Feste Standardtouren der Kunden verwalten", "ro":"⚙️ Gestionați rutele standard ale clienților", "sr":"⚙️ Podesite standardne rute kupaca"}[active_lang], expanded=False):
        st.caption({"de":"Hier wird die Standardtour dauerhaft gespeichert. Die Tageszuordnung einzelner Aufträge kann darunter weiterhin geändert werden.", "ro":"Ruta standard este salvată permanent aici. Repartizarea zilnică a comenzilor poate fi modificată mai jos.", "sr":"Standardna ruta se ovde trajno čuva. Dnevna raspodela pojedinačnih porudžbina može se menjati ispod."}[active_lang])
        for _idx, _ck in enumerate(_customer_keys):
            _def_key = _defaults.get(_ck, "tour1" if "hirschen" in _ck.lower() else ("tour2" if "bella" in _ck.lower() else "tour1"))
            _c1, _c2 = st.columns([2, 2])
            _c1.write(f"**{_ck}**")
            _chosen_default = _c2.selectbox("Standardtour", ["tour1", "tour2"], index=0 if _def_key == "tour1" else 1, format_func=_tour_label, key=f"cust_default_{_idx}_{re.sub(r'[^a-zA-Z0-9]', '', _ck)[:18]}")
            if _chosen_default != _defaults.get(_ck, _def_key):
                _con = sqlite3.connect(_tour_db_path)
                _con.execute("INSERT INTO customer_tour_defaults(customer_key,tour_id) VALUES(?,?) ON CONFLICT(customer_key) DO UPDATE SET tour_id=excluded.tour_id", (_ck, _chosen_default))
                _con.commit(); _con.close()
                _defaults[_ck] = _chosen_default

    _tour_cols = st.columns(2)
    for _tid, _tc in zip(["tour1", "tour2"], _tour_cols):
        with _tc:
            st.markdown(f"#### 🚚 {_tour_label(_tid)}")
            _assigned = [t for t in st.session_state.demo_tours.values() if t.get("tour_id") == _tid]
            st.metric({"de":"Zugeordnete Aufträge", "ro":"Comenzi repartizate", "sr":"Dodeljene porudžbine"}[active_lang], len(_assigned))
            st.caption({"de":"Fester Fahrer und festes Fahrzeug", "ro":"Șofer și vehicul fixe", "sr":"Fiksni vozač i vozilo"}[active_lang])
            for _t in _assigned:
                st.write(f"• {_t.get('customer','Kunde')} · #{_t.get('order_id')} · {_t.get('status','Geplant')}")
            if not _assigned:
                st.caption({"de":"Noch keine Aufträge zugeordnet", "ro":"Nu sunt încă repartizate comenzi", "sr":"Još nema dodeljenih porudžbina"}[active_lang])

    if not orders:
        st.info({"de":"Noch keine aktiven Aufträge. Neue Kundenaufträge erscheinen hier automatisch zur Planung.", "ro":"Nu există comenzi active. Comenzile noi vor apărea aici automat pentru planificare.", "sr":"Nema aktivnih porudžbina. Nove porudžbine vor apărea ovde za planiranje."}[active_lang])
    else:
        st.markdown(f"#### 📥 { {'de':'Aufträge zuordnen oder verschieben','ro':'Repartizați sau mutați comenzile','sr':'Dodelite ili premestite porudžbine'}[active_lang] }")
        for _oi, _o in enumerate(orders):
            _oid = str(_o.get("deal_id", ""))
            _cust = str(_o.get("restaurant") or _o.get("customer") or "Unbekannter Kunde")
            _existing = st.session_state.demo_tours.get(_oid, {})
            _default_tid = _existing.get("tour_id") or _defaults.get(_cust) or ("tour1" if "hirschen" in _cust.lower() else ("tour2" if "bella" in _cust.lower() else "tour1"))
            _a, _b, _c = st.columns([3, 2, 1.4])
            with _a:
                st.write(f"**{_cust}** · Auftrag #{_oid}")
                if _existing.get("tour_id") in _tour_names:
                    st.success(f"✓ Zugeordnet: {_tour_label(_existing['tour_id'])}", icon="🚚")
                else:
                    st.caption({"de":"Noch keiner Tour zugeordnet","ro":"Încă nerepartizată","sr":"Još nije dodeljena ruti"}[active_lang])
                st.caption(_o.get("stage_label", _o.get("current_stage", "")))
            with _b:
                _new_tid = st.selectbox({"de":"Ziel-Tour", "ro":"Ruta destinație", "sr":"Odredišna ruta"}[active_lang], ["tour1", "tour2"], index=0 if _default_tid == "tour1" else 1, format_func=_tour_label, key=f"order_tour_{_oid}")
            with _c:
                if st.button({"de":"Zuordnen","ro":"Repartizați","sr":"Dodeli"}[active_lang], key=f"assign_order_{_oid}", type="primary", use_container_width=True):
                    _prev = st.session_state.demo_tours.get(_oid, {})
                    _same_tour = [x for x in st.session_state.demo_tours.values() if x.get("tour_id") == _new_tid and str(x.get("order_id")) != _oid]
                    _stop_order = len(_same_tour) + 1
                    st.session_state.demo_tours[_oid] = {
                        **_prev, "order_id": _oid, "label": f"{_cust} · Auftrag #{_oid}", "customer": _cust,
                        "tour_id": _new_tid, "vehicle": _tour_vehicles[_new_tid], "driver": _tour_drivers[_new_tid],
                        "stop_order": _stop_order, "stop": f"Stopp {_stop_order}", "status": _prev.get("status", "Geplant")
                    }
                    _save = st.session_state.demo_tours[_oid]
                    _con = sqlite3.connect(_tour_db_path)
                    _con.execute("""INSERT INTO order_tour_assignments(order_id,customer,tour_id,vehicle,driver,stop_order,status,updated_at)
                        VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET customer=excluded.customer,tour_id=excluded.tour_id,vehicle=excluded.vehicle,driver=excluded.driver,stop_order=excluded.stop_order,status=excluded.status,updated_at=excluded.updated_at""",
                        (_oid, _cust, _new_tid, _tour_vehicles[_new_tid], _tour_drivers[_new_tid], _stop_order, _save.get("status", "Geplant"), datetime.now().isoformat(timespec="seconds")))
                    _con.commit(); _con.close()
                    # Re-sequence remaining stops on both tours after moving an order.
                    for _tour_to_fix in ["tour1", "tour2"]:
                        _fix_items = sorted([x for x in st.session_state.demo_tours.values() if x.get("tour_id") == _tour_to_fix], key=lambda x: (int(x.get("stop_order", 999)), str(x.get("order_id"))))
                        for _pos, _item in enumerate(_fix_items, 1):
                            _item["stop_order"] = _pos
                            _item["stop"] = f"Stopp {_pos}"
                            _con = sqlite3.connect(_tour_db_path)
                            _con.execute("UPDATE order_tour_assignments SET stop_order=?, updated_at=? WHERE order_id=?", (_pos, datetime.now().isoformat(timespec="seconds"), str(_item.get("order_id"))))
                            _con.commit(); _con.close()
                    st.session_state.demo_vehicle_status[_tour_vehicles[_new_tid]] = "Tour geplant"
                    st.success({"de":f"Auftrag #{_oid} ist {_tour_names[_new_tid][active_lang]} zugeordnet.", "ro":f"Comanda #{_oid} a fost repartizată la {_tour_names[_new_tid][active_lang]}.", "sr":f"Porudžbina #{_oid} je dodeljena na {_tour_names[_new_tid][active_lang]}."}[active_lang])
                    st.rerun()

    st.markdown(f"### 🚚 { {'de':'Geplante Touren – Übersicht','ro':'Rute planificate – prezentare','sr':'Planirane rute – pregled'}[active_lang] }")
    if st.session_state.demo_tours:
        for _tid in ["tour1", "tour2"]:
            _items = sorted([t for t in st.session_state.demo_tours.values() if t.get("tour_id") == _tid], key=lambda x: (int(x.get("stop_order", 999)), str(x.get("order_id"))))
            with st.expander(_tour_label(_tid) + f" · {len(_items)}", expanded=True):
                if _items:
                    st.dataframe([{"Reihenfolge":t.get("stop_order", i+1),"Kunde":t.get("customer"),"Auftrag":t.get("order_id"),"Stopp":t.get("stop"),"Status":t.get("status")} for i,t in enumerate(_items)], use_container_width=True, hide_index=True)
                else:
                    st.caption({"de":"Noch keine Aufträge", "ro":"Încă nu există comenzi", "sr":"Još nema porudžbina"}[active_lang])
    else:
        st.caption({"de":"Aufträge werden beim ersten Zuordnen mit der gespeicherten Standardtour verknüpft.", "ro":"Comenzile sunt asociate rutei standard salvate la prima repartizare.", "sr":"Porudžbine se povezuju sa standardnom rutom sačuvanom pri prvom dodeljivanju."}[active_lang])


    # Praxisnahe Routensimulation mit fiktiven Adressen, Zeitfenstern und simuliertem Verkehr.
    # Keine echten GPS-/Verkehrsdaten: alle Adressen, Distanzen und Stauwerte sind Demo-Daten.
    st.markdown(f"### 🧭 { {'de':'Routenoptimierung & Reihenfolge','ro':'Optimizarea rutelor și ordinea opririlor','sr':'Optimizacija ruta i redosled stajanja'}[active_lang] }")
    st.caption({
        "de":"Praxisnahe Simulation: fiktive Lieferadressen, Zeitfenster und wechselnde Verkehrslage. Die automatische Optimierung berücksichtigt Lieferzeiten und geschätzte Fahrzeiten. Paco kann die Reihenfolge anschließend manuell ändern.",
        "ro":"Simulare practică: adrese fictive, intervale de livrare și trafic variabil. Optimizarea ia în calcul orele de livrare și timpii estimați. Paco poate modifica apoi manual ordinea.",
        "sr":"Praktična simulacija: izmišljene adrese, vremenski prozori i promenljiv saobraćaj. Optimizacija uzima u obzir rokove isporuke i procenjeno vreme vožnje. Paco zatim može ručno promeniti redosled."
    }[active_lang])

    _demo_customer_route = {
        "Brauhaus zum Hirschen": ("Venloer Straße 120, Köln (DEMO)", "08:00–10:00", 50.9505, 6.9234),
        "Ristorante Bella Italia": ("Aachener Straße 210, Köln (DEMO)", "10:00–12:00", 50.9382, 6.9257),
        "Restaurant Sarajevo": ("Deutzer Freiheit 65, Köln (DEMO)", "09:00–11:00", 50.9368, 6.9748),
        "Trattoria am Markt": ("Eigelstein 45, Köln (DEMO)", "11:00–13:00", 50.9494, 6.9596),
        "Hotel Rheinblick": ("Rheinuferweg 8, Köln (DEMO)", "07:00–09:00", 50.9257, 6.9679),
        "Restoran Dunav": ("Zülpicher Straße 80, Köln (DEMO)", "12:00–14:00", 50.9272, 6.9378),
    }
    _traffic_factor = {"Ruhig": 1.0, "Normal": 1.2, "Stark": 1.55}
    _traffic_label = {"de": {"Ruhig":"Ruhig", "Normal":"Normal", "Stark":"Stark"}, "ro":{"Ruhig":"Liber", "Normal":"Normal", "Stark":"Intens"}, "sr":{"Ruhig":"Slab", "Normal":"Normalan", "Stark":"Gust"}}[active_lang]
    _traffic_choice = st.select_slider(
        {"de":"Simulierte Verkehrslage", "ro":"Trafic simulat", "sr":"Simulirani saobraćaj"}[active_lang],
        options=["Ruhig", "Normal", "Stark"], value="Normal",
        format_func=lambda x: _traffic_label[x],
        key="route_demo_traffic"
    )
    _traffic_multiplier = _traffic_factor[_traffic_choice]

    def _route_customer_info(customer_name):
        return _demo_customer_route.get(
            str(customer_name),
            ("Demo-Adresse, Köln (DEMO)", "09:00–12:00", 50.9375, 6.9603)
        )

    def _distance_km(a, b):
        # Näherungsweise Luftlinienentfernung in einer fiktiven Stadtkarte, auf Straßenfaktor skaliert.
        import math
        return max(0.6, math.sqrt(((a[0]-b[0])*75.0)**2 + ((a[1]-b[1])*48.0)**2) * 1.35)

    _route_rows_for_ui = []
    for _tid in ["tour1", "tour2"]:
        _route_items = sorted(
            [t for t in st.session_state.demo_tours.values() if t.get("tour_id") == _tid],
            key=lambda x: (int(x.get("stop_order", 999)), str(x.get("order_id")))
        )
        if not _route_items:
            continue
        with st.expander(f"{_tour_label(_tid)} · { {'de':'Route','ro':'Rută','sr':'Ruta'}[active_lang] }", expanded=True):
            _rcols = st.columns([1.1, 1, 1])
            with _rcols[0]:
                st.metric({"de":"Kundenstopps","ro":"Opriri","sr":"Stajanja"}[active_lang], len(_route_items))
            with _rcols[1]:
                _base_km = sum(
                    _distance_km(
                        (_route_customer_info(_route_items[i-1].get("customer"))[2], _route_customer_info(_route_items[i-1].get("customer"))[3]),
                        (_route_customer_info(_route_items[i].get("customer"))[2], _route_customer_info(_route_items[i].get("customer"))[3])
                    ) for i in range(1, len(_route_items))
                )
                st.metric({"de":"Geschätzte Strecke","ro":"Distanță estimată","sr":"Procenjena udaljenost"}[active_lang], f"{_base_km:.1f} km")
            with _rcols[2]:
                _est_minutes = int((_base_km / 28.0 * 60.0) * _traffic_multiplier)
                st.metric({"de":"Fahrzeit (Demo)","ro":"Timp de condus (demo)","sr":"Vreme vožnje (demo)"}[active_lang], f"{_est_minutes} min")
            st.caption({"de":"Alle Adressen und Verkehrswerte sind ausdrücklich simuliert.", "ro":"Toate adresele și valorile de trafic sunt simulate.", "sr":"Sve adrese i podaci o saobraćaju su simulirani."}[active_lang])
            _route_table = []
            for _idx_route, _rt in enumerate(_route_items, 1):
                _addr, _window, _lat, _lon = _route_customer_info(_rt.get("customer"))
                _route_table.append({
                    {"de":"Stopp","ro":"Oprire","sr":"Stajanje"}[active_lang]: _idx_route,
                    {"de":"Kunde","ro":"Client","sr":"Kupac"}[active_lang]: _rt.get("customer"),
                    {"de":"Lieferadresse (Demo)","ro":"Adresă (demo)","sr":"Adresa (demo)"}[active_lang]: _addr,
                    {"de":"Zeitfenster","ro":"Interval","sr":"Vremenski prozor"}[active_lang]: _window,
                    {"de":"Status","ro":"Status","sr":"Status"}[active_lang]: _rt.get("status", "Geplant")
                })
            st.dataframe(_route_table, use_container_width=True, hide_index=True)
            _left, _right = st.columns(2)
            with _left:
                if st.button({"de":"✨ Route automatisch optimieren (Simulation)","ro":"✨ Optimizează automat ruta (simulare)","sr":"✨ Automatski optimizuj rutu (simulacija)"}[active_lang], key=f"opt_route_{_tid}", use_container_width=True):
                    # Sort by delivery time window first, then by proximity from the fictional depot.
                    _depot = (50.9375, 6.9603)
                    _sorted_for_route = sorted(
                        _route_items,
                        key=lambda x: (
                            _route_customer_info(x.get("customer"))[1],
                            _distance_km(_depot, (_route_customer_info(x.get("customer"))[2], _route_customer_info(x.get("customer"))[3]))
                        )
                    )
                    for _pos, _rt in enumerate(_sorted_for_route, 1):
                        _rt["stop_order"] = _pos
                        _rt["stop"] = f"Stopp {_pos}"
                        _rt["vehicle"] = _tour_vehicles[_tid]
                        _rt["driver"] = _tour_drivers[_tid]
                    _con = sqlite3.connect(_tour_db_path)
                    for _rt in _sorted_for_route:
                        _con.execute("""INSERT INTO order_tour_assignments(order_id,customer,tour_id,vehicle,driver,stop_order,status,updated_at)
                            VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET tour_id=excluded.tour_id,vehicle=excluded.vehicle,driver=excluded.driver,stop_order=excluded.stop_order,status=excluded.status,updated_at=excluded.updated_at""",
                            (str(_rt.get("order_id")), str(_rt.get("customer")), _tid, _tour_vehicles[_tid], _tour_drivers[_tid], _rt["stop_order"], _rt.get("status","Geplant"), datetime.now().isoformat(timespec="seconds")))
                    _con.commit()
                    _con.close()
                    st.success({"de":"Reihenfolge nach Zeitfenster und Demo-Fahrzeiten optimiert.", "ro":"Ordinea a fost optimizată după intervale și timpii de deplasare demo.", "sr":"Redosled je optimizovan prema vremenskim prozorima i demo vremenima vožnje."}[active_lang])
                    st.rerun()
            with _right:
                st.write({"de":"Manuelle Reihenfolge","ro":"Ordine manuală","sr":"Ručni redosled"}[active_lang])
            # Reliable manual reorder controls (one position at a time).
            for _pos, _rt in enumerate(_route_items):
                _mc1, _mc2, _mc3, _mc4 = st.columns([4, 1, 1, 1])
                _mc1.write(f"{_pos+1}. {_rt.get('customer')} · #{_rt.get('order_id')}")
                if _mc2.button("↑", key=f"route_up_{_tid}_{_rt.get('order_id')}", disabled=(_pos == 0), help="Nach oben"):
                    _route_items[_pos-1], _route_items[_pos] = _route_items[_pos], _route_items[_pos-1]
                    for _p2, _it2 in enumerate(_route_items, 1):
                        _it2["stop_order"] = _p2
                        _it2["stop"] = f"Stopp {_p2}"
                    _con = sqlite3.connect(_tour_db_path)
                    for _it2 in _route_items:
                        _con.execute("UPDATE order_tour_assignments SET stop_order=?, updated_at=? WHERE order_id=?", (_it2["stop_order"], datetime.now().isoformat(timespec="seconds"), str(_it2.get("order_id"))))
                    _con.commit(); _con.close()
                    st.rerun()
                if _mc3.button("↓", key=f"route_down_{_tid}_{_rt.get('order_id')}", disabled=(_pos == len(_route_items)-1), help="Nach unten"):
                    _route_items[_pos+1], _route_items[_pos] = _route_items[_pos], _route_items[_pos+1]
                    for _p2, _it2 in enumerate(_route_items, 1):
                        _it2["stop_order"] = _p2
                        _it2["stop"] = f"Stopp {_p2}"
                    _con = sqlite3.connect(_tour_db_path)
                    for _it2 in _route_items:
                        _con.execute("UPDATE order_tour_assignments SET stop_order=?, updated_at=? WHERE order_id=?", (_it2["stop_order"], datetime.now().isoformat(timespec="seconds"), str(_it2.get("order_id"))))
                    _con.commit(); _con.close()
                    st.rerun()
                _mc4.caption(f"Stopp {_pos+1}")


    st.markdown("### 📡 Fahrzeugübersicht – simulierte Live-Ansicht")
    st.caption("Die Punkte auf der Karte sind feste Demo-Positionen und ändern sich nicht durch GPS. Statusänderungen werden nur innerhalb dieser Streamlit-Sitzung simuliert.")
    vehicle_rows = [
        {"Fahrzeug": "LKW 01", "Status": st.session_state.demo_vehicle_status.get("LKW 01", "Bereit"), "latitude": 50.9375, "longitude": 6.9603},
        {"Fahrzeug": "LKW 02", "Status": st.session_state.demo_vehicle_status.get("LKW 02", "Bereit"), "latitude": 50.9500, "longitude": 6.9800},
        {"Fahrzeug": "LKW 03", "Status": st.session_state.demo_vehicle_status.get("LKW 03", "Bereit"), "latitude": 50.9200, "longitude": 6.9400},
    ]
    map_col, status_col = st.columns([1.5, 1])
    with map_col:
        st.map([{ "latitude": r["latitude"], "longitude": r["longitude"] } for r in vehicle_rows], latitude="latitude", longitude="longitude", size=120)
    with status_col:
        st.dataframe([{"Fahrzeug": r["Fahrzeug"], "Status (Simulation)": r["Status"]} for r in vehicle_rows], use_container_width=True, hide_index=True)

st.caption("KI-BURG GastroLingua Platform 2026 | Abschlussbausteine | Tourenplanung und Fahrzeugpositionen in der Disposition sind ausdrücklich simuliert; HubSpot-Livebetrieb nur bei bestätigter API-Antwort.")

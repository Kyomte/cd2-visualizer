import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from datetime import date, timedelta

PROJECT  = "cd2-visualizer-data"
DATASET  = "cd2_data"
BQ_PRE   = f"`{PROJECT}.{DATASET}"

# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

BG_PRIMARY    = "#0b0d12"
BG_CARD       = "#151821"
BG_CARD_HOVER = "#1c2030"
BORDER        = "#262a36"
TEXT_PRIMARY  = "#e6e8ee"
TEXT_MUTED    = "#8b91a3"
ACCENT        = "#6366f1"
ACCENT_2      = "#06b6d4"
SUCCESS       = "#22c55e"
WARN          = "#f59e0b"
DANGER        = "#ef4444"
CHART_SEQ     = ["#6366f1", "#06b6d4", "#22c55e", "#f59e0b", "#ec4899", "#8b5cf6"]
CHART_DIVERGING = [[0, DANGER], [0.5, WARN], [1, SUCCESS]]

# Account ID → college/department name
COLLEGE_NAMES = {
    105: "Sandbox / Admin", 107: "Architecture", 109: "Law",
    120: "Basic Education (K–12)", 123: "NSTP", 124: "Nursing",
    126: "Sports Management & PE", 132: "EdTech / Course Playground",
    134: "Theology", 135: "Economics", 136: "Teacher Education",
    137: "Banking & Finance", 139: "Communication & Media",
    141: "Elementary Education", 145: "Literature & Translation",
    149: "Advertising & Fine Arts", 150: "Interior Design",
    152: "Computer Science", 154: "Information Technology",
    157: "Physical Therapy", 161: "Biology & Life Sciences",
    165: "Tourism & Recreation Mgmt", 177: "Creative Writing",
    178: "Communication (Campus B)", 180: "Journalism",
    181: "Library Management", 182: "Chemical Engineering",
    183: "Civil Engineering", 184: "Electrical Engineering",
    185: "Electronics Engineering", 186: "Industrial Engineering",
    187: "Mechanical Engineering", 188: "Medical Technology",
    190: "Biochemistry", 191: "Pharmacy", 199: "SHS — ABM Track",
    203: "Health Sciences / Allied", 204: "SHS — Various Tracks",
    210: "SHS — STEM Track", 212: "Accountancy & Business",
    213: "Information Systems", 214: "Management Accounting",
    325: "Tourism & Hospitality", 327: "Seminary / Religious Education",
    339: "Psychology", 424: "Medicine", 447: "Applied Minor",
    455: "Teacher Certification Program",
}

st.set_page_config(
    page_title="CD2 Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, button, input, select, textarea {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

.stApp {{ background-color: {BG_PRIMARY}; }}

/* Hide Streamlit chrome */
#MainMenu, footer, header [data-testid="stToolbar"] {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* Headings */
h1 {{ font-weight: 700 !important; letter-spacing: -0.02em !important; font-size: 1.7rem !important; }}
h2 {{ font-weight: 600 !important; letter-spacing: -0.01em !important; font-size: 1.25rem !important; }}
h3 {{ font-weight: 600 !important; font-size: 1.05rem !important; }}

/* Dividers */
hr {{ border: none !important; border-top: 1px solid {BORDER} !important; margin: 1.5rem 0 !important; }}

/* Metric cards (default st.metric replacement-friendly) */
[data-testid="stMetric"] {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1rem 1.25rem;
    transition: all 0.2s ease;
}}
[data-testid="stMetric"]:hover {{
    background: {BG_CARD_HOVER};
    border-color: {ACCENT};
    transform: translateY(-1px);
}}
[data-testid="stMetricLabel"] {{
    color: {TEXT_MUTED} !important;
    font-size: 0.68rem !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 500;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}}
[data-testid="stMetricLabel"] > div {{
    white-space: normal !important;
    overflow: visible !important;
}}
[data-testid="stMetricValue"] {{
    color: {TEXT_PRIMARY} !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}}
[data-testid="stMetricDelta"] {{ font-size: 0.78rem !important; font-weight: 500 !important; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: #0a0c11 !important;
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: {TEXT_PRIMARY}; }}

/* Sidebar branded header */
.brand-header {{
    display: flex; align-items: center; gap: 10px;
    padding: 0.5rem 0 1.25rem 0;
    border-bottom: 1px solid {BORDER}; margin-bottom: 1rem;
}}
.brand-mark {{
    width: 32px; height: 32px;
    background: linear-gradient(135deg, {ACCENT} 0%, {ACCENT_2} 100%);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; color: white; font-size: 0.9rem;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
}}
.brand-name {{ font-weight: 700; font-size: 1rem; color: {TEXT_PRIMARY}; line-height: 1; }}
.brand-sub  {{ font-size: 0.7rem; color: {TEXT_MUTED}; letter-spacing: 0.04em; text-transform: uppercase; }}

.sidebar-section-label {{
    font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: {TEXT_MUTED}; font-weight: 600; margin: 0.75rem 0 0.4rem 0;
}}

/* Sidebar radio nav */
[data-testid="stSidebar"] .stRadio > div {{ gap: 2px; }}
[data-testid="stSidebar"] .stRadio label {{
    padding: 0.4rem 0.6rem !important;
    border-radius: 8px !important;
    transition: all 0.15s ease;
    cursor: pointer;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    background: {BG_CARD};
}}
[data-testid="stSidebar"] .stRadio label p,
[data-testid="stSidebar"] .stRadio label span,
[data-testid="stSidebar"] .stRadio label div {{
    color: {TEXT_PRIMARY} !important;
    font-size: 0.88rem !important;
    font-weight: 500;
}}

/* Sidebar select/multiselect labels visible */
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {{
    color: {TEXT_PRIMARY} !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}}

/* Selectbox, multiselect, slider — dark surfaces */
.stSelectbox > div > div, .stMultiSelect > div > div, .stTextInput > div > div {{
    background: {BG_CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {BORDER}; }}
.stTabs [data-baseweb="tab"] {{
    padding: 0.5rem 1rem !important;
    color: {TEXT_MUTED} !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    background: transparent !important;
}}
.stTabs [aria-selected="true"] {{
    color: {TEXT_PRIMARY} !important;
    border-bottom: 2px solid {ACCENT} !important;
}}

/* DataFrames */
[data-testid="stDataFrame"] {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 4px;
}}

/* Buttons */
.stButton > button {{
    background: {BG_CARD} !important;
    border: 1px solid {BORDER} !important;
    color: {TEXT_PRIMARY} !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease;
}}
.stButton > button:hover {{
    background: {BG_CARD_HOVER} !important;
    border-color: {ACCENT} !important;
}}

/* Custom scrollbar */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: {BG_PRIMARY}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {TEXT_MUTED}; }}

/* Section header */
.section-header {{ margin: 0.5rem 0 1.5rem 0; }}
.section-eyebrow {{
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: {ACCENT}; margin-bottom: 0.35rem;
}}
.section-title {{
    font-size: 1.65rem; font-weight: 700; letter-spacing: -0.02em;
    color: {TEXT_PRIMARY}; margin: 0; line-height: 1.2;
}}
.section-subtitle {{
    font-size: 0.92rem; color: {TEXT_MUTED}; margin-top: 0.35rem;
}}

/* Filter chips */
.filter-chips {{
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 1rem;
}}
.chip {{
    display: inline-flex; align-items: center; gap: 6px;
    background: {BG_CARD}; border: 1px solid {BORDER};
    color: {TEXT_PRIMARY}; padding: 4px 12px;
    border-radius: 999px; font-size: 0.78rem; font-weight: 500;
}}
.chip-accent {{ border-color: {ACCENT}; color: {ACCENT}; }}

/* Pill badge for proficiency */
.pill {{
    display: inline-block; padding: 6px 14px; margin: 4px 6px 4px 0;
    background: {BG_CARD}; border-left: 3px solid var(--col, {ACCENT});
    border-radius: 6px; font-weight: 500; font-size: 0.85rem;
    color: {TEXT_PRIMARY};
}}

/* Fade-in animation */
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(4px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
[data-testid="stMetric"], .stPlotlyChart, [data-testid="stDataFrame"] {{
    animation: fadeIn 0.45s ease-out;
}}

/* Sidebar footer */
.sidebar-footer {{
    margin-top: 1rem; padding-top: 0.75rem;
    border-top: 1px solid {BORDER};
    font-size: 0.78rem; color: {TEXT_MUTED};
    display: flex; align-items: center; gap: 6px;
}}
.sidebar-footer-dot {{
    width: 6px; height: 6px; border-radius: 50%; background: {ACCENT};
}}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# BIGQUERY CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_client():
    import json
    from google.oauth2 import service_account
    # Try Streamlit secrets first (deployed); ignore if no secrets file exists locally
    try:
        has_secret = "gcp_credentials_json" in st.secrets
    except Exception:
        has_secret = False
    if has_secret:
        info = json.loads(st.secrets["gcp_credentials_json"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=PROJECT, credentials=creds)
    # Local development — uses Application Default Credentials
    try:
        return bigquery.Client(project=PROJECT)
    except Exception:
        st.error("Add `gcp_credentials_json` to your Streamlit secrets.")
        st.stop()

def bq(sql: str) -> pd.DataFrame:
    return get_client().query(sql).to_dataframe()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS — UI + CHARTS
# ═══════════════════════════════════════════════════════════════════════════════

def section_header(eyebrow: str, title: str, subtitle: str = None):
    sub = f'<div class="section-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
        <div class="section-header">
            <div class="section-eyebrow">{eyebrow}</div>
            <div class="section-title">{title}</div>
            {sub}
        </div>
    """, unsafe_allow_html=True)

def filter_chips(chips: list):
    if not chips:
        return
    html = '<div class="filter-chips">'
    for c in chips:
        html += f'<span class="chip chip-accent">{c}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def apply_chart_theme(fig, height: int = None, show_legend: bool = True):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT_PRIMARY, size=12),
        margin=dict(t=30, b=30, l=10, r=10),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=TEXT_MUTED)),
        hoverlabel=dict(bgcolor=BG_CARD, bordercolor=ACCENT,
                        font=dict(family="Inter", color=TEXT_PRIMARY, size=12)),
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    if height:
        fig.update_layout(height=height)
    if not show_legend:
        fig.update_layout(showlegend=False)
    return fig

def add_time_controls(fig):
    """Add range slider + preset buttons to a time-series chart."""
    fig.update_layout(
        xaxis=dict(
            gridcolor=BORDER, zerolinecolor=BORDER,
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="ALL"),
                ],
                bgcolor=BG_CARD, activecolor=ACCENT,
                font=dict(color=TEXT_PRIMARY, size=11),
                bordercolor=BORDER, borderwidth=1,
                x=0, y=1.15,
            ),
            rangeslider=dict(visible=True, thickness=0.05, bgcolor=BG_CARD),
            type="date",
        ),
        hovermode="x unified",
    )
    return fig

def date_range_clause(column: str = "assessed_at") -> str:
    """Return SQL WHERE clause fragment for active date filter, or empty string."""
    days = st.session_state.get("date_filter_days", 0)
    if days and days > 0:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return f" AND {column} >= '{cutoff}'"
    return ""

DATE_OPTIONS = {
    "All time":      0,
    "Last 30 days":  30,
    "Last 90 days":  90,
    "Last 6 months": 180,
    "Last year":     365,
}


# ═══════════════════════════════════════════════════════════════════════════════
# CACHED QUERIES
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def overview_stats(date_days: int = 0):
    extra = ""
    if date_days > 0:
        cutoff = (date.today() - timedelta(days=date_days)).isoformat()
        extra = f" AND assessed_at >= '{cutoff}'"
    active_courses  = bq(f"SELECT COUNT(*) AS n FROM {BQ_PRE}.courses` WHERE workflow_state='available'")['n'].iloc[0]
    active_users    = bq(f"SELECT COUNT(*) AS n FROM {BQ_PRE}.users` WHERE workflow_state='registered'")['n'].iloc[0]
    active_outcomes = bq(f"SELECT COUNT(*) AS n FROM {BQ_PRE}.learning_outcomes` WHERE workflow_state='active'")['n'].iloc[0]
    mastery_pct     = bq(f"SELECT ROUND(COUNTIF(mastery='t')/COUNT(*)*100,1) AS n FROM {BQ_PRE}.learning_outcomes_results` WHERE workflow_state='active'{extra}")['n'].iloc[0]
    return pd.DataFrame([{
        "active_courses": active_courses,
        "active_users": active_users,
        "active_outcomes": active_outcomes,
        "mastery_pct": mastery_pct,
    }])

@st.cache_data(ttl=3600, show_spinner=False)
def monthly_results(date_days: int = 0):
    extra = ""
    if date_days > 0:
        cutoff = (date.today() - timedelta(days=date_days)).isoformat()
        extra = f" AND assessed_at >= '{cutoff}'"
    return bq(f"""
        SELECT
          DATE_TRUNC(DATE(assessed_at), MONTH) AS month,
          COUNT(*) AS assessments,
          ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_pct
        FROM {BQ_PRE}.learning_outcomes_results`
        WHERE workflow_state = 'active'
          AND assessed_at IS NOT NULL{extra}
        GROUP BY 1
        ORDER BY 1
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def score_distribution():
    return bq(f"""
        SELECT ROUND(percent * 100) AS score_pct
        FROM {BQ_PRE}.learning_outcomes_results`
        WHERE workflow_state = 'active' AND percent IS NOT NULL
        LIMIT 50000
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def ratings_data():
    return bq(f"SELECT * FROM {BQ_PRE}.outcome_proficiencies_ratings`")

@st.cache_data(ttl=3600, show_spinner=False)
def mastery_bands(date_days: int = 0):
    extra = ""
    if date_days > 0:
        cutoff = (date.today() - timedelta(days=date_days)).isoformat()
        extra = f" AND assessed_at >= '{cutoff}'"
    return bq(f"""
        SELECT
          CASE
            WHEN percent >= 0.9 THEN 'Exceeds (90–100%)'
            WHEN percent >= 0.7 THEN 'Meets (70–89%)'
            WHEN percent >= 0.5 THEN 'Approaching (50–69%)'
            ELSE 'Below (<50%)'
          END AS band,
          COUNT(*) AS n
        FROM {BQ_PRE}.learning_outcomes_results`
        WHERE workflow_state = 'active' AND percent IS NOT NULL{extra}
        GROUP BY 1
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def at_risk_outcomes(min_assessments: int = 50):
    return bq(f"""
        SELECT
          lo.display_name AS code,
          lo.short_description AS outcome,
          COUNT(r.id) AS assessments,
          COUNT(DISTINCT r.user_id) AS students,
          ROUND(COUNTIF(r.mastery='t') / COUNT(r.id) * 100, 1) AS mastery_rate,
          ROUND(AVG(r.percent) * 100, 1) AS avg_score
        FROM {BQ_PRE}.learning_outcomes_results` r
        JOIN {BQ_PRE}.learning_outcomes` lo ON r.learning_outcome_id = lo.id
        WHERE r.workflow_state = 'active'
        GROUP BY 1, 2
        HAVING assessments >= {min_assessments} AND mastery_rate < 70
        ORDER BY mastery_rate ASC
        LIMIT 30
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def outcome_volume_vs_mastery():
    return bq(f"""
        SELECT
          lo.display_name AS code,
          lo.short_description AS outcome,
          COUNT(r.id) AS assessments,
          COUNT(DISTINCT r.user_id) AS students,
          ROUND(COUNTIF(r.mastery='t') / COUNT(r.id) * 100, 1) AS mastery_rate
        FROM {BQ_PRE}.learning_outcomes_results` r
        JOIN {BQ_PRE}.learning_outcomes` lo ON r.learning_outcome_id = lo.id
        WHERE r.workflow_state = 'active'
        GROUP BY 1, 2
        HAVING assessments >= 10
        ORDER BY assessments DESC
        LIMIT 200
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def assessment_coverage():
    return bq(f"""
        SELECT
          COUNT(DISTINCT lo.id) AS total_outcomes,
          COUNT(DISTINCT r.learning_outcome_id) AS assessed_outcomes
        FROM {BQ_PRE}.learning_outcomes` lo
        LEFT JOIN {BQ_PRE}.learning_outcomes_results` r
          ON lo.id = r.learning_outcome_id AND r.workflow_state = 'active'
        WHERE lo.workflow_state = 'active'
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def college_benchmark():
    return bq(f"""
        SELECT
          c.account_id,
          COUNT(DISTINCT r.user_id) AS students,
          COUNT(r.id) AS assessments,
          ROUND(COUNTIF(r.mastery='t') / COUNT(r.id) * 100, 1) AS mastery_rate
        FROM {BQ_PRE}.learning_outcomes_results` r
        JOIN {BQ_PRE}.courses` c ON r.context_id = c.id
        WHERE r.workflow_state = 'active'
        GROUP BY 1
        HAVING assessments >= 50
        ORDER BY mastery_rate DESC
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def college_summary():
    return bq(f"""
        SELECT c.account_id,
          COUNT(DISTINCT lo.id)  AS outcomes,
          SUM(stats.assessments) AS assessments,
          ROUND(AVG(stats.mastery_rate), 1) AS mastery_rate,
          ROUND(AVG(stats.avg_score), 1)    AS avg_score
        FROM {BQ_PRE}.learning_outcomes` lo
        JOIN {BQ_PRE}.courses` c
          ON lo.context_id = c.id AND lo.context_type = 'Course'
        LEFT JOIN (
          SELECT learning_outcome_id, COUNT(*) AS assessments,
            ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_rate,
            ROUND(AVG(percent) * 100, 1) AS avg_score
          FROM {BQ_PRE}.learning_outcomes_results`
          WHERE workflow_state = 'active' GROUP BY 1
        ) stats ON lo.id = stats.learning_outcome_id
        WHERE lo.workflow_state = 'active' GROUP BY 1
        UNION ALL
        SELECT lo.context_id AS account_id,
          COUNT(DISTINCT lo.id)  AS outcomes,
          SUM(stats.assessments) AS assessments,
          ROUND(AVG(stats.mastery_rate), 1) AS mastery_rate,
          ROUND(AVG(stats.avg_score), 1)    AS avg_score
        FROM {BQ_PRE}.learning_outcomes` lo
        LEFT JOIN (
          SELECT learning_outcome_id, COUNT(*) AS assessments,
            ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_rate,
            ROUND(AVG(percent) * 100, 1) AS avg_score
          FROM {BQ_PRE}.learning_outcomes_results`
          WHERE workflow_state = 'active' GROUP BY 1
        ) stats ON lo.id = stats.learning_outcome_id
        WHERE lo.workflow_state = 'active' AND lo.context_type = 'Account' GROUP BY 1
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def outcomes_for_college(account_id: int):
    return bq(f"""
        SELECT lo.id, lo.display_name, lo.short_description,
          lo.calculation_method, lo.context_type,
          stats.assessments, stats.mastery_rate, stats.avg_score
        FROM {BQ_PRE}.learning_outcomes` lo
        LEFT JOIN (
          SELECT learning_outcome_id, COUNT(*) AS assessments,
            ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_rate,
            ROUND(AVG(percent) * 100, 1) AS avg_score
          FROM {BQ_PRE}.learning_outcomes_results`
          WHERE workflow_state = 'active' GROUP BY 1
        ) stats ON lo.id = stats.learning_outcome_id
        WHERE lo.workflow_state = 'active'
          AND (
            (lo.context_type = 'Account' AND lo.context_id = {account_id})
            OR (lo.context_type = 'Course' AND lo.context_id IN (
              SELECT id FROM {BQ_PRE}.courses` WHERE account_id = {account_id}
            ))
          )
        ORDER BY stats.assessments DESC NULLS LAST
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def monthly_results_for_college(account_id: int, date_days: int = 0):
    extra = ""
    if date_days > 0:
        cutoff = (date.today() - timedelta(days=date_days)).isoformat()
        extra = f" AND r.assessed_at >= '{cutoff}'"
    return bq(f"""
        SELECT
          DATE_TRUNC(DATE(r.assessed_at), MONTH) AS month,
          COUNT(*) AS assessments,
          ROUND(COUNTIF(r.mastery='t') / COUNT(*) * 100, 1) AS mastery_pct
        FROM {BQ_PRE}.learning_outcomes_results` r
        JOIN {BQ_PRE}.courses` c ON r.context_id = c.id
        WHERE r.workflow_state = 'active'
          AND c.account_id = {account_id}
          AND r.assessed_at IS NOT NULL{extra}
        GROUP BY 1 ORDER BY 1
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def courses_for_college(account_id: int):
    return bq(f"""
        SELECT c.id AS course_id, c.name AS course_name, c.course_code,
          COUNT(DISTINCT r.user_id) AS students, COUNT(r.id) AS assessments,
          ROUND(COUNTIF(r.mastery='t') / NULLIF(COUNT(r.id),0) * 100, 1) AS mastery_rate,
          ROUND(AVG(r.percent) * 100, 1) AS avg_score
        FROM {BQ_PRE}.courses` c
        JOIN {BQ_PRE}.learning_outcomes_results` r ON c.id = r.context_id
        WHERE c.account_id = {account_id} AND r.workflow_state = 'active'
        GROUP BY 1, 2, 3 ORDER BY assessments DESC LIMIT 200
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def outcome_breakdown_for_college(account_id: int):
    return bq(f"""
        SELECT lo.short_description, lo.display_name,
          COUNT(r.id) AS assessments,
          ROUND(COUNTIF(r.mastery='t') / NULLIF(COUNT(r.id),0) * 100, 1) AS mastery_rate
        FROM {BQ_PRE}.learning_outcomes_results` r
        JOIN {BQ_PRE}.courses` c ON r.context_id = c.id
        JOIN {BQ_PRE}.learning_outcomes` lo ON r.learning_outcome_id = lo.id
        WHERE c.account_id = {account_id} AND r.workflow_state = 'active'
        GROUP BY 1, 2 ORDER BY assessments DESC LIMIT 30
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def all_outcomes():
    return bq(f"""
        SELECT lo.id, lo.display_name, lo.short_description, lo.calculation_method,
          lo.workflow_state,
          stats.assessments, stats.mastery_rate, stats.avg_score
        FROM {BQ_PRE}.learning_outcomes` lo
        LEFT JOIN (
          SELECT learning_outcome_id, COUNT(*) AS assessments,
            ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_rate,
            ROUND(AVG(percent) * 100, 1) AS avg_score
          FROM {BQ_PRE}.learning_outcomes_results`
          WHERE workflow_state = 'active' GROUP BY 1
        ) stats ON lo.id = stats.learning_outcome_id
        WHERE lo.workflow_state = 'active'
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def course_performance(min_students: int = 1):
    return bq(f"""
        SELECT c.id, c.name, c.course_code,
          COUNT(DISTINCT r.user_id) AS students, COUNT(r.id) AS assessments,
          ROUND(COUNTIF(r.mastery='t') / NULLIF(COUNT(r.id),0) * 100, 1) AS mastery_rate,
          ROUND(AVG(r.percent) * 100, 1) AS avg_score
        FROM {BQ_PRE}.courses` c
        JOIN {BQ_PRE}.learning_outcomes_results` r ON c.id = r.context_id
        WHERE r.workflow_state = 'active'
        GROUP BY 1, 2, 3 HAVING students >= {min_students}
        ORDER BY assessments DESC LIMIT 500
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def search_users(query: str):
    safe = query.replace("'", "''")
    return bq(f"""
        SELECT id, name, sortable_name, workflow_state
        FROM {BQ_PRE}.users`
        WHERE LOWER(name) LIKE LOWER('%{safe}%')
           OR LOWER(sortable_name) LIKE LOWER('%{safe}%')
        LIMIT 50
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def student_results(user_id: int):
    return bq(f"""
        SELECT r.id, r.score, r.possible, r.percent, r.mastery,
          r.assessed_at, r.context_id,
          lo.display_name, lo.short_description,
          c.name AS course_name
        FROM {BQ_PRE}.learning_outcomes_results` r
        LEFT JOIN {BQ_PRE}.learning_outcomes` lo ON r.learning_outcome_id = lo.id
        LEFT JOIN {BQ_PRE}.courses` c ON r.context_id = c.id
        WHERE r.user_id = {user_id} AND r.workflow_state = 'active'
        ORDER BY r.assessed_at DESC
    """)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown(f"""
<div class="brand-header">
    <div class="brand-mark">CD</div>
    <div>
        <div class="brand-name">CD2 Explorer</div>
        <div class="brand-sub">Canvas Data 2</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Global filters
st.sidebar.markdown('<div class="sidebar-section-label">Filters</div>', unsafe_allow_html=True)

date_label = st.sidebar.selectbox(
    "Date range", list(DATE_OPTIONS.keys()),
    index=0, key="date_filter_label",
    help="Filters time-series queries across pages",
)
st.session_state["date_filter_days"] = DATE_OPTIONS[date_label]

college_options = sorted(COLLEGE_NAMES.values())
selected_colleges = st.sidebar.multiselect(
    "Colleges (default: all)", college_options,
    default=[], key="college_filter",
    help="Filter Colleges page to a subset",
)

# Navigation
st.sidebar.markdown('<div class="sidebar-section-label">Browse</div>', unsafe_allow_html=True)
browse_page = st.sidebar.radio(
    "Browse nav", ["Overview", "Colleges", "Learning Outcomes", "Course Performance", "Student Mastery"],
    label_visibility="collapsed", key="browse_nav",
)

st.sidebar.markdown('<div class="sidebar-section-label">Analyze</div>', unsafe_allow_html=True)
analyze_page = st.sidebar.radio(
    "Analyze nav", ["— none —", "Insights"],
    label_visibility="collapsed", key="analyze_nav",
)

page = analyze_page if analyze_page != "— none —" else browse_page

# Cache refresh
st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("🔄  Clear cache", use_container_width=True):
    st.cache_data.clear()
    st.toast("Cache cleared", icon="✨")
    st.rerun()

# Footer
st.sidebar.markdown(f"""
<div class="sidebar-footer">
    <span class="sidebar-footer-dot"></span>
    Made by Kiel Mingote
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVE FILTER CHIPS
# ═══════════════════════════════════════════════════════════════════════════════

def render_filter_chips():
    chips = []
    if st.session_state.get("date_filter_days", 0) > 0:
        chips.append(f"📅 {date_label}")
    if selected_colleges:
        chips.append(f"🏫 {len(selected_colleges)} colleges")
    filter_chips(chips)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

if page == "Overview":
    section_header("DASHBOARD", "Overview",
                   "High-level snapshot of courses, users, outcomes, and mastery.")
    render_filter_chips()

    days = st.session_state.get("date_filter_days", 0)
    with st.spinner("Loading…"):
        stats    = overview_stats(days).iloc[0]
        monthly  = monthly_results(days)
        scores   = score_distribution()
        ratings  = ratings_data()
        coverage = assessment_coverage()

    total_out    = int(coverage["total_outcomes"].iloc[0])
    assessed_out = int(coverage["assessed_outcomes"].iloc[0])

    trend_sorted = monthly.sort_values("month")
    if len(trend_sorted) >= 2:
        mom_delta = round(trend_sorted["mastery_pct"].iloc[-1] - trend_sorted["mastery_pct"].iloc[-2], 1)
        mom_str   = f"+{mom_delta}%" if mom_delta >= 0 else f"{mom_delta}%"
    else:
        mom_str = None

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active Courses",    f"{int(stats['active_courses']):,}")
    c2.metric("Active Users",      f"{int(stats['active_users']):,}")
    c3.metric("Learning Outcomes", f"{total_out:,}")
    c4.metric("Overall Mastery",   f"{stats['mastery_pct']}%", mom_str)
    c5.metric("Outcomes Assessed", f"{assessed_out:,}",
              f"{round(assessed_out/total_out*100)}% coverage")

    st.divider()

    # ── Results over time ────────────────────────────────────────────────────
    chart_type = st.segmented_control(
        "Chart style", ["Combo", "Line", "Bar"],
        default="Combo", key="overview_chart_type",
    )

    fig = go.Figure()
    if chart_type in ("Combo", "Bar"):
        fig.add_bar(x=monthly["month"], y=monthly["assessments"],
                    name="Assessments", marker_color=ACCENT, opacity=0.65)
    if chart_type in ("Combo", "Line"):
        fig.add_scatter(x=monthly["month"], y=monthly["mastery_pct"],
                        name="Mastery %",
                        yaxis="y2" if chart_type == "Combo" else "y",
                        line=dict(color=ACCENT_2, width=2.5),
                        mode="lines+markers", marker=dict(size=5))
    if chart_type == "Combo":
        fig.update_layout(
            yaxis=dict(title="# Assessments"),
            yaxis2=dict(title="Mastery %", overlaying="y", side="right", range=[0, 105]),
        )
    elif chart_type == "Bar":
        fig.update_layout(yaxis=dict(title="# Assessments"))
    else:
        fig.update_layout(yaxis=dict(title="Mastery %", range=[0, 105]))

    apply_chart_theme(fig, height=380)
    add_time_controls(fig)
    st.markdown("##### Results Over Time")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Score distribution + proficiency scale ────────────────────────────────
    left, right = st.columns([2, 1])
    with left:
        st.markdown("##### Score Distribution")
        fig2 = px.histogram(scores, x="score_pct", nbins=20,
                            color_discrete_sequence=[ACCENT])
        fig2.update_traces(marker_line_width=0)
        fig2.update_layout(xaxis_title="Score %", yaxis_title="Count")
        apply_chart_theme(fig2, height=320, show_legend=False)
        st.plotly_chart(fig2, use_container_width=True)

    with right:
        st.markdown("##### Proficiency Scale")
        if not ratings.empty:
            for _, row in ratings.sort_values("points", ascending=False).iterrows():
                color = f"#{row['color']}" if pd.notna(row.get("color")) else ACCENT
                tag = " ⭐" if row.get("mastery") in [True, "t"] else ""
                st.markdown(
                    f'<div class="pill" style="--col: {color};">'
                    f'<strong>{row["description"]}</strong>{tag} · {row["points"]} pts</div>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Insights":
    section_header("ANALYTICS", "Insights",
                   "Patterns and findings automatically derived from outcomes data.")
    render_filter_chips()

    days = st.session_state.get("date_filter_days", 0)
    with st.spinner("Loading insights…"):
        bands    = mastery_bands(days)
        trend    = monthly_results(days)
        coverage = assessment_coverage()

    total      = int(coverage["total_outcomes"].iloc[0])
    assessed   = int(coverage["assessed_outcomes"].iloc[0])
    unassessed = total - assessed

    trend_sorted = trend.sort_values("month")
    if len(trend_sorted) >= 2:
        latest_pct  = trend_sorted["mastery_pct"].iloc[-1]
        mom_delta   = round(latest_pct - trend_sorted["mastery_pct"].iloc[-2], 1)
        delta_label = f"+{mom_delta}%" if mom_delta >= 0 else f"{mom_delta}%"
    else:
        latest_pct, delta_label = None, "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Outcomes",       f"{total:,}")
    c2.metric("Outcomes Assessed",    f"{assessed:,}", f"{round(assessed/total*100)}% of total")
    c3.metric("Never Assessed",       f"{unassessed:,}",
              f"{round(unassessed/total*100)}% of total", delta_color="inverse")
    c4.metric("Latest Month Mastery", f"{latest_pct}%" if latest_pct else "—", delta_label)

    st.divider()

    # ── Bands + trend ─────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("##### Proficiency Band Distribution")
        band_order  = ["Exceeds (90–100%)", "Meets (70–89%)", "Approaching (50–69%)", "Below (<50%)"]
        band_colors = [SUCCESS, ACCENT_2, WARN, DANGER]
        bands_sorted = bands.set_index("band").reindex(band_order).reset_index().dropna()
        fig = px.pie(bands_sorted, names="band", values="n",
                     color="band",
                     color_discrete_map=dict(zip(band_order, band_colors)), hole=0.5)
        fig.update_traces(textinfo="percent+label", textfont=dict(color=TEXT_PRIMARY))
        apply_chart_theme(fig, height=350, show_legend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("##### Monthly Mastery Trend")
        fig2 = go.Figure()
        fig2.add_scatter(
            x=trend_sorted["month"], y=trend_sorted["mastery_pct"],
            mode="lines+markers", line=dict(color=ACCENT, width=2.5),
            marker=dict(size=6), name="Mastery %",
            fill="tozeroy", fillcolor="rgba(99,102,241,0.15)",
        )
        if not trend_sorted.empty:
            fig2.add_hline(y=trend_sorted["mastery_pct"].mean(),
                           line_dash="dot", line_color=WARN,
                           annotation_text=f"Avg {trend_sorted['mastery_pct'].mean():.1f}%",
                           annotation_font_color=WARN)
        fig2.update_layout(yaxis=dict(title="Mastery %", range=[0, 105]))
        apply_chart_theme(fig2, height=350, show_legend=False)
        add_time_controls(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Outcomes needing attention ────────────────────────────────────────────
    st.markdown("##### 🚨 Outcomes Needing Attention")
    st.caption("Outcomes with ≥ N assessments and mastery rate below 70%.")

    min_n = st.slider("Min assessments threshold", 10, 500, 50, step=10,
                      key="insights_min_n")
    with st.spinner("Loading…"):
        at_risk = at_risk_outcomes(min_n)

    if at_risk.empty:
        st.success("No at-risk outcomes at this threshold.")
    else:
        fig3 = px.bar(
            at_risk.sort_values("mastery_rate"),
            x="mastery_rate", y="outcome", orientation="h",
            color="mastery_rate", color_continuous_scale=CHART_DIVERGING,
            range_color=[0, 100], custom_data=["assessments", "students"],
            labels={"mastery_rate": "Mastery %", "outcome": "Outcome"},
        )
        fig3.update_traces(
            hovertemplate="<b>%{y}</b><br>Mastery: %{x}%<br>"
                          "Assessments: %{customdata[0]}<br>Students: %{customdata[1]}<extra></extra>"
        )
        fig3.add_vline(x=70, line_dash="dash", line_color=WARN,
                       annotation_text="70% threshold", annotation_font_color=WARN)
        apply_chart_theme(fig3, height=max(350, len(at_risk) * 28))
        fig3.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

        show = at_risk.copy()
        show.columns = ["Code", "Outcome", "Assessments", "Students", "Mastery %", "Avg Score %"]
        st.dataframe(show, use_container_width=True, height=300)

    st.divider()

    # ── Volume vs Mastery quadrant ────────────────────────────────────────────
    st.markdown("##### 📊 Volume vs Mastery — Quadrant View")
    st.caption("Top-left quadrant (high volume, low mastery) = highest priority for intervention.")

    with st.spinner("Loading quadrant data…"):
        quad = outcome_volume_vs_mastery()

    if not quad.empty:
        med_vol     = quad["assessments"].median()
        med_mastery = quad["mastery_rate"].median()

        fig4 = px.scatter(
            quad, x="mastery_rate", y="assessments",
            size="students", color="mastery_rate",
            color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
            hover_name="outcome",
            hover_data={"code": True, "assessments": True, "students": True, "mastery_rate": True},
            labels={"mastery_rate": "Mastery %", "assessments": "# Assessments",
                    "students": "# Students"},
        )
        fig4.add_vline(x=med_mastery, line_dash="dot", line_color=TEXT_MUTED,
                       annotation_text=f"Median {med_mastery:.0f}%",
                       annotation_font_color=TEXT_MUTED)
        fig4.add_hline(y=med_vol, line_dash="dot", line_color=TEXT_MUTED,
                       annotation_text=f"Median {int(med_vol)}",
                       annotation_font_color=TEXT_MUTED)
        fig4.add_annotation(x=20, y=quad["assessments"].max()*0.95,
                            text="🚨 High Impact / Low Mastery",
                            showarrow=False, font=dict(color=DANGER, size=11))
        fig4.add_annotation(x=85, y=quad["assessments"].max()*0.95,
                            text="✅ High Impact / High Mastery",
                            showarrow=False, font=dict(color=SUCCESS, size=11))
        apply_chart_theme(fig4, height=480)
        fig4.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    # ── College benchmark ────────────────────────────────────────────────────
    st.markdown("##### 🏫 College Performance Benchmark")

    with st.spinner("Loading college data…"):
        bench = college_benchmark()

    bench["college"] = bench["account_id"].map(COLLEGE_NAMES).fillna(
        "Account " + bench["account_id"].astype(str))
    bench = bench.sort_values("mastery_rate", ascending=False)
    inst_avg = round(bench["mastery_rate"].mean(), 1)

    fig5 = px.bar(
        bench, x="college", y="mastery_rate",
        color="mastery_rate", color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
        labels={"college": "College", "mastery_rate": "Mastery %"},
        text=bench["mastery_rate"].astype(str) + "%",
    )
    fig5.add_hline(y=inst_avg, line_dash="dash", line_color=ACCENT,
                   annotation_text=f"Institution avg {inst_avg}%",
                   annotation_font_color=ACCENT)
    fig5.update_traces(textposition="outside", textfont=dict(size=10, color=TEXT_MUTED))
    apply_chart_theme(fig5, height=420)
    fig5.update_layout(coloraxis_showscale=False, xaxis_tickangle=-35)
    st.plotly_chart(fig5, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: COLLEGES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Colleges":
    section_header("DRILL-DOWN", "Colleges",
                   "Outcomes, performance, and courses grouped by college / department.")
    render_filter_chips()

    with st.spinner("Loading college summary…"):
        col_sum = college_summary()

    col_sum["college"] = col_sum["account_id"].map(COLLEGE_NAMES).fillna(
        "Account " + col_sum["account_id"].astype(str))
    col_agg = (col_sum.groupby(["account_id", "college"])
               .agg(outcomes=("outcomes","sum"),
                    assessments=("assessments","sum"),
                    mastery_rate=("mastery_rate","mean"),
                    avg_score=("avg_score","mean"))
               .reset_index()
               .sort_values("outcomes", ascending=False))

    # Apply sidebar college filter if set
    if selected_colleges:
        col_agg = col_agg[col_agg["college"].isin(selected_colleges)]

    # Compare mode toggle
    compare_mode = st.toggle("Compare two colleges", value=False, key="compare_mode")

    # All-college bar chart
    st.markdown("##### Mastery Rate by College")
    chart_data = col_agg.dropna(subset=["mastery_rate"]).sort_values("mastery_rate")
    if not chart_data.empty:
        fig = px.bar(
            chart_data, x="mastery_rate", y="college", orientation="h",
            color="mastery_rate", color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
            labels={"mastery_rate": "Mastery %", "college": ""},
            text=chart_data["mastery_rate"].round(1).astype(str) + "%",
        )
        fig.update_traces(textposition="outside", textfont=dict(size=10, color=TEXT_MUTED))
        apply_chart_theme(fig, height=max(420, len(chart_data) * 26))
        fig.update_layout(coloraxis_showscale=False, margin=dict(t=10, l=10))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # College selector(s)
    college_options = col_agg[col_agg["assessments"].fillna(0) > 0]["college"].tolist()

    if compare_mode:
        chosen = st.multiselect("Select up to 2 colleges to compare",
                                sorted(college_options),
                                default=sorted(college_options)[:2],
                                max_selections=2)
        if len(chosen) < 2:
            st.info("Pick 2 colleges to see the side-by-side comparison.")
        else:
            cols = st.columns(2)
            for idx, cname in enumerate(chosen):
                sel_row = col_agg[col_agg["college"] == cname].iloc[0]
                aid = int(sel_row["account_id"])
                with cols[idx]:
                    st.markdown(f"### {cname}")
                    m1, m2 = st.columns(2)
                    m1.metric("Outcomes",  f"{int(sel_row['outcomes']):,}")
                    m2.metric("Mastery", f"{sel_row['mastery_rate']:.1f}%"
                              if pd.notna(sel_row['mastery_rate']) else "—")
                    days = st.session_state.get("date_filter_days", 0)
                    m_data = monthly_results_for_college(aid, days)
                    if not m_data.empty:
                        fig_c = go.Figure()
                        fig_c.add_scatter(
                            x=m_data["month"], y=m_data["mastery_pct"],
                            mode="lines+markers", name="Mastery %",
                            line=dict(color=CHART_SEQ[idx], width=2.5),
                            fill="tozeroy",
                            fillcolor=f"rgba({99 if idx==0 else 6},{102 if idx==0 else 182},{241 if idx==0 else 212},0.15)",
                        )
                        fig_c.update_layout(yaxis=dict(range=[0, 105]))
                        apply_chart_theme(fig_c, height=300, show_legend=False)
                        st.plotly_chart(fig_c, use_container_width=True)
    else:
        selected_college = st.selectbox(
            "Select a college to drill down", sorted(college_options),
            key="college_select",
        )
        sel_row = col_agg[col_agg["college"] == selected_college].iloc[0]
        sel_account_id = int(sel_row["account_id"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Outcomes Defined",  f"{int(sel_row['outcomes']):,}")
        c2.metric("Total Assessments", f"{int(sel_row['assessments'] or 0):,}")
        c3.metric("Avg Mastery Rate",  f"{sel_row['mastery_rate']:.1f}%"
                  if pd.notna(sel_row['mastery_rate']) else "—")
        c4.metric("Avg Score",         f"{sel_row['avg_score']:.1f}%"
                  if pd.notna(sel_row['avg_score']) else "—")

        tab1, tab2, tab3 = st.tabs(["Outcomes", "Results Over Time", "Courses"])

        with tab1:
            with st.spinner("Loading outcomes…"):
                outcomes = outcomes_for_college(sel_account_id)

            search_out = st.text_input("Filter outcomes",
                                       placeholder="e.g. Identify or design",
                                       key="college_outcome_search")
            disp = outcomes.copy()
            if search_out:
                mask = (
                    disp["short_description"].str.contains(search_out, case=False, na=False) |
                    disp["display_name"].str.contains(search_out, case=False, na=False)
                )
                disp = disp[mask]

            top_n = st.segmented_control("Show", ["Top 10", "Top 30", "Top 50"],
                                          default="Top 30", key="college_top_n")
            n_map = {"Top 10": 10, "Top 30": 30, "Top 50": 50}
            n = n_map[top_n]

            chart = disp.dropna(subset=["mastery_rate"]).head(n).sort_values("mastery_rate")
            if not chart.empty:
                fig2 = px.bar(
                    chart, x="mastery_rate", y="short_description", orientation="h",
                    color="mastery_rate", color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
                    labels={"mastery_rate": "Mastery %", "short_description": ""},
                    title=f"Top {n} Outcomes — Mastery Rate",
                )
                apply_chart_theme(fig2, height=max(380, len(chart)*26))
                fig2.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig2, use_container_width=True)

            show = disp[["display_name", "short_description", "calculation_method",
                         "context_type", "assessments", "mastery_rate", "avg_score"]].copy()
            show.columns = ["Code", "Outcome", "Method", "Level",
                            "Assessments", "Mastery %", "Avg Score %"]
            st.dataframe(show, use_container_width=True, height=400)

        with tab2:
            days = st.session_state.get("date_filter_days", 0)
            with st.spinner("Loading results…"):
                monthly_c  = monthly_results_for_college(sel_account_id, days)
                outcome_bd = outcome_breakdown_for_college(sel_account_id)

            if monthly_c.empty:
                st.info("No assessment results found for this college.")
            else:
                fig3 = go.Figure()
                fig3.add_bar(x=monthly_c["month"], y=monthly_c["assessments"],
                             name="Assessments", marker_color=ACCENT, opacity=0.65)
                fig3.add_scatter(x=monthly_c["month"], y=monthly_c["mastery_pct"],
                                 name="Mastery %", yaxis="y2",
                                 line=dict(color=ACCENT_2, width=2.5),
                                 mode="lines+markers", marker=dict(size=5))
                fig3.update_layout(
                    yaxis=dict(title="# Assessments"),
                    yaxis2=dict(title="Mastery %", overlaying="y", side="right", range=[0, 105]),
                )
                apply_chart_theme(fig3, height=380)
                add_time_controls(fig3)
                st.plotly_chart(fig3, use_container_width=True)

            if not outcome_bd.empty:
                st.markdown("##### Outcome Breakdown")
                top_ob = outcome_bd.sort_values("mastery_rate")
                fig4 = px.bar(
                    top_ob, x="mastery_rate", y="short_description", orientation="h",
                    color="mastery_rate", color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
                    labels={"mastery_rate": "Mastery %", "short_description": ""},
                )
                apply_chart_theme(fig4, height=max(320, len(top_ob)*28))
                fig4.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig4, use_container_width=True)

        with tab3:
            with st.spinner("Loading courses…"):
                courses_c = courses_for_college(sel_account_id)

            if courses_c.empty:
                st.info("No courses with assessment data found.")
            else:
                fig5 = px.scatter(
                    courses_c, x="students", y="mastery_rate", size="assessments",
                    color="avg_score", color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
                    hover_name="course_name",
                    labels={"students": "# Students", "mastery_rate": "Mastery %",
                            "avg_score": "Avg Score %"},
                    title=f"Courses in {selected_college}",
                )
                apply_chart_theme(fig5, height=420)
                st.plotly_chart(fig5, use_container_width=True)

                show_c = courses_c[["course_name", "course_code", "students",
                                     "assessments", "mastery_rate", "avg_score"]].copy()
                show_c.columns = ["Course", "Code", "Students", "Assessments",
                                   "Mastery %", "Avg Score %"]
                st.dataframe(show_c, use_container_width=True, height=400)

    st.divider()
    st.markdown("##### All Colleges Summary")
    show_all = col_agg[["college", "outcomes", "assessments",
                         "mastery_rate", "avg_score"]].copy()
    show_all.columns = ["College", "Outcomes", "Assessments", "Mastery %", "Avg Score %"]
    show_all["Mastery %"]   = show_all["Mastery %"].round(1)
    show_all["Avg Score %"] = show_all["Avg Score %"].round(1)

    event = st.dataframe(
        show_all, use_container_width=True, height=420,
        on_select="rerun", selection_mode="single-row",
        key="all_colleges_df",
    )
    if event and event.selection and event.selection.rows:
        row_idx = event.selection.rows[0]
        clicked_college = show_all.iloc[row_idx]["College"]
        if not compare_mode and clicked_college != st.session_state.get("college_select"):
            st.session_state["college_select"] = clicked_college
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LEARNING OUTCOMES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Learning Outcomes":
    section_header("CATALOG", "Learning Outcomes",
                   "Browse, search, and analyze all institutional outcomes.")
    render_filter_chips()

    with st.spinner("Loading outcomes…"):
        df = all_outcomes()

    search = st.text_input("Search outcomes",
                           placeholder="e.g. THM5206 or Identify…",
                           key="lo_search")
    if search:
        mask = (
            df["display_name"].str.contains(search, case=False, na=False) |
            df["short_description"].str.contains(search, case=False, na=False)
        )
        df = df[mask]

    st.caption(f"Showing {len(df):,} outcomes")

    col_left, col_right = st.columns([1.6, 1])

    with col_left:
        top_n_label = st.segmented_control("Show", ["Top 10", "Top 20", "Top 30"],
                                            default="Top 20", key="lo_top_n")
        n = int(top_n_label.split()[1])
        top_n = df.dropna(subset=["mastery_rate"]).nlargest(n, "assessments").sort_values("mastery_rate")
        if not top_n.empty:
            fig = px.bar(
                top_n, x="mastery_rate", y="short_description", orientation="h",
                color="mastery_rate", color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
                labels={"mastery_rate": "Mastery %", "short_description": ""},
                title=f"Top {n} Most-Assessed Outcomes — Mastery Rate",
            )
            apply_chart_theme(fig, height=500)
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("##### Calculation Methods")
        method_counts = df["calculation_method"].value_counts().reset_index()
        method_counts.columns = ["method", "count"]
        fig2 = px.pie(method_counts, names="method", values="count",
                      color_discrete_sequence=CHART_SEQ, hole=0.5)
        fig2.update_traces(textinfo="percent", textfont=dict(color=TEXT_PRIMARY))
        apply_chart_theme(fig2, height=320)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    with st.spinner("Loading quadrant…"):
        quad = outcome_volume_vs_mastery()

    if not quad.empty and not search:
        st.markdown("##### Volume vs Mastery Quadrant")
        med_m = quad["mastery_rate"].median()
        med_v = quad["assessments"].median()
        fig_q = px.scatter(
            quad, x="mastery_rate", y="assessments",
            size="students", color="mastery_rate",
            color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
            hover_name="outcome", hover_data={"code": True},
            labels={"mastery_rate": "Mastery %", "assessments": "# Assessments"},
        )
        fig_q.add_vline(x=med_m, line_dash="dot", line_color=TEXT_MUTED)
        fig_q.add_hline(y=med_v, line_dash="dot", line_color=TEXT_MUTED)
        fig_q.add_annotation(x=10, y=quad["assessments"].max()*0.93,
                             text="🚨 Needs Attention", showarrow=False,
                             font=dict(color=DANGER, size=11))
        apply_chart_theme(fig_q, height=400)
        fig_q.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_q, use_container_width=True)

    st.markdown("##### Outcomes Table")
    show = df[["display_name", "short_description", "calculation_method",
               "assessments", "mastery_rate", "avg_score"]].rename(columns={
        "display_name": "Code", "short_description": "Description",
        "calculation_method": "Method", "assessments": "# Assessments",
        "mastery_rate": "Mastery %", "avg_score": "Avg Score %",
    })
    st.dataframe(show, use_container_width=True, height=420)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: COURSE PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Course Performance":
    section_header("PERFORMANCE", "Course Performance",
                   "Mastery rates and enrolment across every course with results.")
    render_filter_chips()

    col1, col2 = st.columns(2)
    min_students = col1.slider("Min students", 1, 100, 5, key="cp_min_students")
    sort_by      = col2.selectbox("Sort by",
                                  ["mastery_rate", "students", "avg_score"],
                                  key="cp_sort_by")

    with st.spinner("Loading courses…"):
        df = course_performance(min_students)

    df = df.sort_values(sort_by, ascending=False)
    st.caption(f"{len(df):,} courses matched")

    fig = px.scatter(
        df.head(200), x="students", y="mastery_rate", size="assessments",
        color="avg_score", color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
        hover_name="name", hover_data={"course_code": True},
        labels={"students": "# Students", "mastery_rate": "Mastery %",
                "avg_score": "Avg Score %"},
        title="Course Mastery vs. Enrolment (top 200)",
    )
    apply_chart_theme(fig, height=460)
    st.plotly_chart(fig, use_container_width=True)

    show = df[["name", "course_code", "students", "assessments",
               "mastery_rate", "avg_score"]].copy()
    show.columns = ["Course", "Code", "Students", "Assessments", "Mastery %", "Avg Score %"]
    st.dataframe(show, use_container_width=True, height=420)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: STUDENT MASTERY
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Student Mastery":
    section_header("LOOKUP", "Student Mastery",
                   "Search a student to see their full outcome assessment history.")

    search = st.text_input("Search student name",
                           placeholder="e.g. Santos or Cruz", key="sm_search")

    if not search or len(search) < 2:
        st.info("Enter at least 2 characters to search for a student.")
    else:
        with st.spinner("Searching…"):
            matched = search_users(search)

        if matched.empty:
            st.warning("No users found.")
        else:
            options = matched.apply(lambda r: f"{r['name']} (ID {r['id']})", axis=1).tolist()
            choice  = st.selectbox("Select student", options, key="sm_select")
            uid     = int(choice.split("ID ")[1].rstrip(")"))

            with st.spinner("Loading results…"):
                sr = student_results(uid)

            total    = len(sr)
            mastered = (sr["mastery"] == "t").sum()
            avg_pct  = sr["percent"].mean() * 100 if total else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Assessments", f"{total:,}")
            c2.metric("Outcomes Mastered", f"{int(mastered):,} / {total:,}")
            c3.metric("Average Score",     f"{avg_pct:.1f}%")

            if not sr.empty:
                sr["mastered"]  = sr["mastery"] == "t"
                sr["score_pct"] = sr["percent"] * 100
                fig = px.scatter(
                    sr.sort_values("assessed_at"),
                    x="assessed_at", y="score_pct",
                    color="mastered",
                    color_discrete_map={True: SUCCESS, False: DANGER},
                    hover_data=["display_name", "course_name"],
                    labels={"assessed_at": "Date", "score_pct": "Score %",
                            "mastered": "Mastered"},
                    title="Assessment History",
                )
                apply_chart_theme(fig, height=380)
                add_time_controls(fig)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("##### Outcome Details")
            show = sr[["display_name", "short_description", "course_name",
                        "score", "possible", "percent", "mastery",
                        "assessed_at"]].copy()
            show["percent"] = (show["percent"] * 100).round(1)
            show["mastery"] = show["mastery"].map({"t": "✅", "f": "❌"})
            show.columns = ["Code", "Outcome", "Course", "Score", "Possible",
                            "Pct %", "Mastered", "Assessed At"]
            st.dataframe(show, use_container_width=True, height=420)

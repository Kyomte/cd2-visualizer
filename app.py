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
# DESIGN SYSTEM — Light Glassmorphism
# ═══════════════════════════════════════════════════════════════════════════════

BG_PAGE        = "#eef2f7"
BG_GRADIENT_A  = "#e8eef5"
BG_GRADIENT_B  = "#f5f8fb"
GLASS_BG       = "rgba(255,255,255,0.65)"
GLASS_BORDER   = "rgba(255,255,255,0.85)"
GLASS_SHADOW   = "0 8px 32px rgba(31,41,55,0.06)"
INK            = "#1a2332"
INK_MUTED      = "#6b7280"
INK_FAINT      = "#9ca3af"
NAVY_BTN       = "#1f2937"
SUCCESS        = "#10b981"
DANGER         = "#ef4444"
WARN           = "#f59e0b"
PASTEL_BLUE    = "#e0eaff"
PASTEL_PEACH   = "#ffe5d9"
PASTEL_YELLOW  = "#fff5cc"
PASTEL_MINT    = "#d6f5e3"
PASTEL_LILAC   = "#eee0ff"
CHART_SEQ      = ["#1f2937", "#6366f1", "#10b981", "#f59e0b", "#ec4899", "#06b6d4"]
CHART_DIVERGING = [[0, "#ef4444"], [0.5, "#f59e0b"], [1, "#10b981"]]
DARK_CONTRAST_BG = "#1f2937"

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
# GLOBAL CSS — Light Glassmorphism
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp, .stMarkdown, button, input, select, textarea {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Page background */
.stApp {
    background: linear-gradient(135deg, #e8eef5 0%, #f5f8fb 50%, #eef2f7 100%) !important;
}

/* Headings */
h1 { font-weight: 700 !important; letter-spacing: -0.02em !important; font-size: 1.7rem !important; color: #1a2332 !important; }
h2 { font-weight: 600 !important; letter-spacing: -0.01em !important; font-size: 1.25rem !important; color: #1a2332 !important; }
h3 { font-weight: 600 !important; font-size: 1.05rem !important; color: #1a2332 !important; }
h4, h5, h6 { color: #1a2332 !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e5e7eb !important;
    box-shadow: 2px 0 16px rgba(31,41,55,0.06) !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #1a2332 !important; }
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label {
    color: #1a2332 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}

/* Sidebar nav pills */
[data-testid="stSidebar"] .stRadio > div { gap: 2px; }
[data-testid="stSidebar"] .stRadio label {
    padding: 0.45rem 0.75rem !important;
    border-radius: 10px !important;
    transition: all 0.18s ease;
    cursor: pointer;
}
[data-testid="stSidebar"] .stRadio label:hover { background: #f3f4f6 !important; }
[data-testid="stSidebar"] .stRadio label p,
[data-testid="stSidebar"] .stRadio label span,
[data-testid="stSidebar"] .stRadio label div {
    color: #4b5563 !important;
    font-size: 0.88rem !important;
    font-weight: 500;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 14px !important;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 4px 16px rgba(31,41,55,0.05) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(31,41,55,0.09) !important;
}
[data-testid="stMetricLabel"] {
    color: #6b7280 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
    white-space: normal !important;
    overflow: visible !important;
}
[data-testid="stMetricLabel"] > div { white-space: normal !important; overflow: visible !important; }
[data-testid="stMetricValue"] {
    color: #1a2332 !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em;
}
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; font-weight: 600 !important; }

/* Buttons */
.stButton > button {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    color: #1a2332 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 4px rgba(31,41,55,0.06) !important;
    transition: all 0.18s ease !important;
}
.stButton > button:hover {
    background: #f8fafc !important;
    box-shadow: 0 4px 12px rgba(31,41,55,0.10) !important;
    transform: translateY(-1px) !important;
    border-color: #1f2937 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid #e5e7eb;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    padding: 0.5rem 1rem !important;
    color: #6b7280 !important;
    font-weight: 500 !important;
    background: transparent !important;
    border-radius: 8px 8px 0 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #1a2332 !important;
    background: #ffffff !important;
    border-bottom: 2px solid #1f2937 !important;
}

/* DataFrame */
[data-testid="stDataFrame"] {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 14px !important;
    padding: 4px !important;
}

/* Form inputs */
.stSelectbox > div > div, .stMultiSelect > div > div, .stTextInput > div > div {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    color: #1a2332 !important;
}

/* Divider */
hr { border: none !important; border-top: 1px solid #e5e7eb !important; margin: 1.25rem 0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(31,41,55,0.18); border-radius: 3px; }

/* Animations */
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
[data-testid="stMetric"], .stPlotlyChart, [data-testid="stDataFrame"] { animation: fadeIn 0.4s ease-out; }

/* Hide Streamlit chrome */
#MainMenu, footer, header [data-testid="stToolbar"] { visibility: hidden; }
.stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# BIGQUERY CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_client():
    import json
    from google.oauth2 import service_account
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
    try:
        return bigquery.Client(project=PROJECT)
    except Exception:
        st.error("Add `gcp_credentials_json` to your Streamlit secrets.")
        st.stop()

def bq(sql: str) -> pd.DataFrame:
    return get_client().query(sql).to_dataframe()


# ═══════════════════════════════════════════════════════════════════════════════
# DATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

DATE_OPTIONS = {
    "All time":      0,
    "Last 30 days":  30,
    "Last 90 days":  90,
    "Last 6 months": 180,
    "Last year":     365,
}

def date_range_clause(column: str = "assessed_at") -> str:
    days = st.session_state.get("date_filter_days", 0)
    if days and days > 0:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return f" AND {column} >= '{cutoff}'"
    return ""


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
# HELPERS — Chart theme
# ═══════════════════════════════════════════════════════════════════════════════

def apply_chart_theme(fig, height: int = None, show_legend: bool = True):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(family="Inter, sans-serif", color=INK, size=12),
        margin=dict(t=30, b=30, l=10, r=10),
        xaxis=dict(gridcolor="rgba(31,41,55,0.06)", zerolinecolor="rgba(31,41,55,0.1)"),
        yaxis=dict(gridcolor="rgba(31,41,55,0.06)", zerolinecolor="rgba(31,41,55,0.1)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(255,255,255,0.7)", font=dict(size=11, color=INK_MUTED)),
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.95)", bordercolor="rgba(31,41,55,0.15)",
                        font=dict(family="Inter", color=INK, size=12)),
        transition=dict(duration=400, easing="cubic-in-out"),
    )
    if height:
        fig.update_layout(height=height)
    if not show_legend:
        fig.update_layout(showlegend=False)
    return fig

def add_time_controls(fig):
    fig.update_layout(
        xaxis=dict(
            gridcolor="rgba(31,41,55,0.06)", zerolinecolor="rgba(31,41,55,0.1)",
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="ALL"),
                ],
                bgcolor="rgba(255,255,255,0.85)", activecolor=DARK_CONTRAST_BG,
                font=dict(color=INK, size=11),
                bordercolor="rgba(31,41,55,0.12)", borderwidth=1,
                x=0, y=1.15,
            ),
            rangeslider=dict(visible=True, thickness=0.05, bgcolor="rgba(255,255,255,0.7)"),
            type="date",
        ),
        hovermode="x unified",
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS — Glassmorphism UI components
# ═══════════════════════════════════════════════════════════════════════════════

def pastel_icon(emoji: str, bg: str) -> str:
    """Returns HTML for a small rounded pastel icon square."""
    return (
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f'width:36px;height:36px;border-radius:10px;background:{bg};'
        f'font-size:1.1rem;flex-shrink:0;">{emoji}</span>'
    )

def metric_glass(label: str, value: str, delta: str = None,
                 status: str = "flat", icon: str = None, icon_bg: str = PASTEL_BLUE):
    """Render a frosted-glass metric card via st.markdown."""
    delta_color = SUCCESS if status == "up" else (DANGER if status == "down" else INK_MUTED)
    delta_arrow = "↑" if status == "up" else ("↓" if status == "down" else "")
    delta_html  = (f'<div style="font-size:0.78rem;color:{delta_color};font-weight:600;margin-top:2px;">'
                   f'{delta_arrow} {delta}</div>') if delta else ""
    icon_html   = f'<div style="margin-bottom:0.6rem;">{pastel_icon(icon, icon_bg)}</div>' if icon else ""
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.65);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.85);border-radius:14px;padding:1.1rem 1.25rem;box-shadow:0 4px 16px rgba(31,41,55,0.05);margin-bottom:0.75rem;">'
        f'{icon_html}'
        f'<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:{INK_MUTED};margin-bottom:0.3rem;">{label}</div>'
        f'<div style="font-size:1.6rem;font-weight:700;color:{INK};letter-spacing:-0.025em;line-height:1.1;">{value}</div>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

def activity_row(icon: str, icon_bg: str, title: str, subtitle: str,
                 value: str, status_label: str, status_color: str):
    """Render a single activity-list row (transaction style)."""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;padding:0.6rem 0;border-bottom:1px solid rgba(31,41,55,0.06);">'
        f'{pastel_icon(icon, icon_bg)}'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="font-size:0.88rem;font-weight:600;color:{INK};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{title}</div>'
        f'<div style="font-size:0.75rem;color:{INK_MUTED};margin-top:1px;">{subtitle}</div>'
        f'</div>'
        f'<div style="text-align:right;flex-shrink:0;">'
        f'<div style="font-size:0.88rem;font-weight:700;color:{INK};">{value}</div>'
        f'<div style="display:inline-block;margin-top:2px;padding:1px 8px;border-radius:999px;font-size:0.68rem;font-weight:600;background:{status_color}22;color:{status_color};">{status_label}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def dark_contrast_card(title: str, subtitle: str = "", live_count: int = None):
    """Renders a styled dark navy header for a section (no rows)."""
    live_html = ""
    if live_count is not None:
        live_html = (
            f'<span style="display:inline-flex;align-items:center;gap:5px;'
            f'font-size:0.68rem;font-weight:700;color:{SUCCESS};text-transform:uppercase;'
            f'letter-spacing:0.08em;">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{SUCCESS};'
            f'animation:pulse 1.5s infinite;"></span>LIVE &middot; {live_count}</span>'
        )
    sub_html = (f'<div style="font-size:0.8rem;color:rgba(255,255,255,0.5);margin-top:3px;">'
                f'{subtitle}</div>') if subtitle else ""
    st.markdown(
        f'<div style="background:{DARK_CONTRAST_BG};border-radius:16px;padding:1.25rem 1.4rem 0.75rem 1.4rem;box-shadow:0 8px 32px rgba(31,41,55,0.18);margin-bottom:0.5rem;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">'
        f'<div>'
        f'<div style="font-size:0.95rem;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">{title}</div>'
        f'{sub_html}'
        f'</div>'
        f'{live_html}'
        f'</div>'
        f'</div>'
        f'<style>@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.4}}}}</style>',
        unsafe_allow_html=True,
    )

def dark_leaderboard_card(title: str, subtitle: str = "", live_count: int = None,
                           rows: list = None):
    """
    Renders a dark navy card with header + leaderboard rows in one block (no gap).
    rows = list of (label, value, color) tuples.
    """
    live_html = ""
    if live_count is not None:
        live_html = (
            f'<span style="display:inline-flex;align-items:center;gap:5px;'
            f'font-size:0.68rem;font-weight:700;color:{SUCCESS};text-transform:uppercase;'
            f'letter-spacing:0.08em;">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{SUCCESS};'
            f'animation:pulse 1.5s infinite;"></span>LIVE &middot; {live_count}</span>'
        )
    sub_html = (f'<div style="font-size:0.8rem;color:rgba(255,255,255,0.5);margin-top:3px;">'
                f'{subtitle}</div>') if subtitle else ""
    rows_html = ""
    if rows:
        for label, value, color in rows:
            rows_html += (
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.07);">'
                f'<span style="color:rgba(255,255,255,0.75);font-size:0.8rem;">{label}</span>'
                f'<span style="color:{color};font-weight:700;font-size:0.88rem;">{value}</span>'
                f'</div>'
            )
    st.markdown(
        f'<div style="background:{DARK_CONTRAST_BG};border-radius:16px;'
        f'padding:1.25rem 1.4rem 1rem 1.4rem;'
        f'box-shadow:0 8px 32px rgba(31,41,55,0.18);margin-bottom:0.5rem;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.85rem;">'
        f'<div>'
        f'<div style="font-size:0.95rem;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">{title}</div>'
        f'{sub_html}'
        f'</div>'
        f'{live_html}'
        f'</div>'
        f'{rows_html}'
        f'</div>'
        f'<style>@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.4}}}}</style>',
        unsafe_allow_html=True,
    )

def hero_card(eyebrow: str, title: str, subtitle: str,
              primary_cta: str = None, secondary_cta: str = None,
              primary_key: str = None, secondary_key: str = None):
    """Render the big hero card with eyebrow + title + subtitle + CTA buttons."""
    st.markdown(
        f'<div style="background:rgba(255,255,255,0.72);backdrop-filter:blur(24px) saturate(180%);border:1px solid rgba(255,255,255,0.9);border-radius:20px;padding:1.75rem 2rem 1.25rem 2rem;box-shadow:0 8px 40px rgba(31,41,55,0.08);margin-bottom:0.5rem;">'
        f'<div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:#6366f1;margin-bottom:0.5rem;">{eyebrow}</div>'
        f'<div style="font-size:1.85rem;font-weight:800;color:{INK};letter-spacing:-0.03em;line-height:1.15;margin-bottom:0.5rem;">{title}</div>'
        f'<div style="font-size:0.93rem;color:{INK_MUTED};line-height:1.55;margin-bottom:1rem;">{subtitle}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if primary_cta or secondary_cta:
        btn_cols = st.columns([1, 1, 3])
        if primary_cta and primary_key:
            with btn_cols[0]:
                st.button(primary_cta, key=primary_key, use_container_width=True)
        if secondary_cta and secondary_key:
            with btn_cols[1]:
                st.button(secondary_cta, key=secondary_key, use_container_width=True)

def action_button_row(actions: list):
    """
    Render a bottom row of action buttons.
    actions = list of dicts: {label, icon, icon_bg, key, callback}
    """
    if not actions:
        return
    st.markdown("<div style='margin-top:0.5rem;'>", unsafe_allow_html=True)
    cols = st.columns(len(actions))
    for col, act in zip(cols, actions):
        with col:
            if st.button(f"{act['icon']} {act['label']}", key=act['key'], use_container_width=True):
                cb = act.get('callback')
                if cb:
                    cb()
    st.markdown("</div>", unsafe_allow_html=True)

def top_header(page_title: str, subtabs: list = None, tab_key: str = None,
               search_placeholder: str = None, search_key: str = None) -> tuple:
    """
    Renders the top header bar: page title · sub-tabs · search · bell · avatar.
    Returns (selected_subtab, search_value).
    """
    bell_count = st.session_state.get("_bell_count", "")
    bell_badge = (
        f'<span style="position:absolute;top:-4px;right:-4px;width:16px;height:16px;'
        f'border-radius:50%;background:{DANGER};font-size:0.6rem;font-weight:700;'
        f'color:white;display:flex;align-items:center;justify-content:center;">{bell_count}</span>'
    ) if bell_count else ""

    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;padding:0.5rem 0;">'
        f'<div style="font-size:1.4rem;font-weight:800;color:{INK};letter-spacing:-0.025em;">{page_title}</div>'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<div style="position:relative;display:inline-flex;">'
        f'<span style="font-size:1.2rem;cursor:pointer;" title="At-risk outcomes">&#x1F514;</span>'
        f'{bell_badge}'
        f'</div>'
        f'<div style="width:34px;height:34px;border-radius:50%;background:{DARK_CONTRAST_BG};display:flex;align-items:center;justify-content:center;font-size:0.78rem;font-weight:700;color:white;">KM</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    selected_subtab = None
    search_value = None

    left_col, right_col = st.columns([2, 1])
    with left_col:
        if subtabs:
            selected_subtab = st.segmented_control("View", subtabs, default=subtabs[0], key=tab_key)
    with right_col:
        if search_placeholder and search_key:
            search_value = st.text_input("", placeholder=f"🔍 {search_placeholder}",
                                         key=search_key, label_visibility="collapsed")

    return selected_subtab, search_value


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;padding:0.5rem 0 1.25rem 0;
            border-bottom:1px solid rgba(31,41,55,0.08);margin-bottom:1rem;">
    <div style="width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#1f2937);
                border-radius:10px;display:flex;align-items:center;justify-content:center;
                font-weight:800;color:white;font-size:0.88rem;
                box-shadow:0 4px 12px rgba(99,102,241,0.3);">CD</div>
    <div>
        <div style="font-weight:700;font-size:1rem;color:{INK};line-height:1;">CD2 Explorer</div>
        <div style="font-size:0.68rem;color:{INK_MUTED};letter-spacing:0.05em;text-transform:uppercase;">Canvas Data 2</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f'<div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{INK_MUTED};margin:0.5rem 0 0.4rem 0;">Filters</div>', unsafe_allow_html=True)

date_label = st.sidebar.selectbox("Date range", list(DATE_OPTIONS.keys()), index=0, key="date_filter_label", help="Filters time-series queries")
st.session_state["date_filter_days"] = DATE_OPTIONS[date_label]

college_options = sorted(COLLEGE_NAMES.values())
selected_colleges = st.sidebar.multiselect("Colleges (default: all)", college_options, default=[], key="college_filter")

st.sidebar.markdown(f'<div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{INK_MUTED};margin:0.75rem 0 0.4rem 0;">Browse</div>', unsafe_allow_html=True)
browse_page = st.sidebar.radio("Browse nav", ["Overview", "Colleges", "Learning Outcomes", "Course Performance", "Student Mastery"], label_visibility="collapsed", key="browse_nav")

st.sidebar.markdown(f'<div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{INK_MUTED};margin:0.75rem 0 0.4rem 0;">Analyze</div>', unsafe_allow_html=True)
analyze_page = st.sidebar.radio("Analyze nav", ["— none —", "Insights"], label_visibility="collapsed", key="analyze_nav")

page = analyze_page if analyze_page != "— none —" else browse_page

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown(f'<div style="font-size:0.72rem;color:{INK_MUTED};margin-bottom:4px;">Cache freshness</div>', unsafe_allow_html=True)
st.sidebar.progress(0.85, text="")
st.sidebar.caption("Auto-refreshes every hour")

st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("🔄 Clear cache & refresh", use_container_width=True):
    st.cache_data.clear()
    st.toast("Cache cleared ✨")
    st.rerun()

st.sidebar.markdown(f"""
<div style="margin-top:1rem;padding-top:0.75rem;border-top:1px solid rgba(31,41,55,0.08);
            font-size:0.78rem;color:{INK_MUTED};display:flex;align-items:center;gap:6px;">
    <span style="width:6px;height:6px;border-radius:50%;background:#6366f1;display:inline-block;"></span>
    Made by Kiel Mingote
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

if page == "Overview":
    subtab, search_val = top_header(
        "Institution Overview",
        subtabs=["Snapshot", "Trend", "Distribution"],
        tab_key="overview_subtab",
        search_placeholder="Search outcomes or courses...",
        search_key="overview_search"
    )

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

    # Row 1: Hero + metrics
    col_hero, col_metrics = st.columns([2.2, 1])
    with col_hero:
        hero_card(
            eyebrow="CANVAS DATA 2",
            title="Institution Outcomes Performance",
            subtitle=f"Tracking {total_out:,} learning outcomes across {int(stats['active_courses']):,} courses — {stats['mastery_pct']}% overall mastery rate.",
            primary_cta="📥 Export Report",
            primary_key="overview_export",
            secondary_cta="🔍 Drill In",
            secondary_key="overview_drill",
        )
    with col_metrics:
        metric_glass("Active Students", f"{int(stats['active_users']):,}", icon="👤", icon_bg=PASTEL_BLUE)
        metric_glass(
            "Overall Mastery", f"{stats['mastery_pct']}%",
            delta=mom_str,
            status="up" if (mom_str and mom_str.startswith("+")) else "down",
            icon="🎯", icon_bg=PASTEL_MINT
        )

    # Row 2: Activity + dark contrast
    col_act, col_dark = st.columns([2.2, 1])
    with col_act:
        st.markdown("##### Results Over Time")
        chart_type = st.segmented_control("Chart style", ["Combo", "Line", "Bar"], default="Combo", key="overview_chart_type")
        fig = go.Figure()
        if chart_type in ("Combo", "Bar"):
            fig.add_bar(x=monthly["month"], y=monthly["assessments"], name="Assessments", marker_color="#6366f1", opacity=0.65)
        if chart_type in ("Combo", "Line"):
            fig.add_scatter(x=monthly["month"], y=monthly["mastery_pct"],
                            name="Mastery %", yaxis="y2" if chart_type == "Combo" else "y",
                            line=dict(color="#10b981", width=2.5), mode="lines+markers", marker=dict(size=5))
        if chart_type == "Combo":
            fig.update_layout(yaxis=dict(title="# Assessments"), yaxis2=dict(title="Mastery %", overlaying="y", side="right", range=[0, 105]))
        elif chart_type == "Bar":
            fig.update_layout(yaxis=dict(title="# Assessments"))
        else:
            fig.update_layout(yaxis=dict(title="Mastery %", range=[0, 105]))
        apply_chart_theme(fig, height=340)
        add_time_controls(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col_dark:
        with st.spinner(""):
            bench = college_benchmark()
        if not bench.empty:
            bench["college"] = bench["account_id"].map(COLLEGE_NAMES).fillna("Acct " + bench["account_id"].astype(str))
            top5 = bench.head(5)
            leaderboard_rows = []
            for _, row in top5.iterrows():
                cname = row["college"][:22] + "…" if len(row["college"]) > 22 else row["college"]
                rate  = row["mastery_rate"]
                color = SUCCESS if rate >= 70 else (WARN if rate >= 50 else DANGER)
                leaderboard_rows.append((cname, f"{rate:.0f}%", color))
            dark_leaderboard_card("Top Colleges", "by mastery rate",
                                  live_count=int(stats['active_courses']),
                                  rows=leaderboard_rows)

    st.divider()

    # Score distribution + proficiency scale
    if subtab in ("Distribution", "Snapshot", None):
        left, right = st.columns([2, 1])
        with left:
            st.markdown("##### Score Distribution")
            fig2 = px.histogram(scores, x="score_pct", nbins=20, color_discrete_sequence=["#6366f1"])
            fig2.update_traces(marker_line_width=0)
            fig2.update_layout(xaxis_title="Score %", yaxis_title="Count")
            apply_chart_theme(fig2, height=300, show_legend=False)
            st.plotly_chart(fig2, use_container_width=True)
        with right:
            st.markdown("##### Proficiency Scale")
            if not ratings.empty:
                for _, row in ratings.sort_values("points", ascending=False).iterrows():
                    color = f"#{row['color']}" if pd.notna(row.get("color")) else "#6366f1"
                    tag = " ⭐" if row.get("mastery") in [True, "t"] else ""
                    st.markdown(
                        f'<div style="background:rgba(255,255,255,0.65);border-left:3px solid {color};'
                        f'border-radius:8px;padding:8px 12px;margin:4px 0;font-size:0.85rem;color:{INK};">'
                        f'<strong>{row["description"]}</strong>{tag} · {row["points"]} pts</div>',
                        unsafe_allow_html=True
                    )

    action_button_row([
        {"label": "Refresh", "icon": "🔄", "icon_bg": PASTEL_BLUE,   "key": "ov_refresh",  "callback": lambda: (st.cache_data.clear(), st.rerun())},
        {"label": "Export",  "icon": "📥", "icon_bg": PASTEL_PEACH,  "key": "ov_export",   "callback": None},
        {"label": "Compare", "icon": "⚖️", "icon_bg": PASTEL_YELLOW, "key": "ov_compare",  "callback": None},
        {"label": "Reset",   "icon": "↺",  "icon_bg": PASTEL_LILAC,  "key": "ov_reset",    "callback": None},
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Insights":
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

    with st.spinner("Loading at-risk…"):
        at_risk_preview = at_risk_outcomes(50)

    subtab, search_val = top_header(
        "Outcomes Insights",
        subtabs=["At-Risk", "Bands", "Quadrant", "Benchmark"],
        tab_key="insights_subtab",
        search_placeholder="Search outcomes...",
        search_key="insights_search"
    )

    # Row 1: Hero + metrics
    col_hero, col_metrics = st.columns([2.2, 1])
    with col_hero:
        hero_card(
            eyebrow="ANALYTICS",
            title="Outcomes Analytics",
            subtitle=f"{len(at_risk_preview):,} outcomes flagged at-risk (mastery < 70%). {round(assessed/total*100) if total else 0}% of outcomes have been assessed.",
            primary_cta="📥 Export Insights",
            primary_key="ins_export",
            secondary_cta="🔍 Filter",
            secondary_key="ins_filter",
        )
    with col_metrics:
        metric_glass("At-Risk Outcomes", f"{len(at_risk_preview):,}", icon="🚨", icon_bg=PASTEL_PEACH, status="down")
        metric_glass("Coverage", f"{round(assessed/total*100) if total else 0}%", icon="📊", icon_bg=PASTEL_MINT)

    # Row 2: Activity list + dark contrast
    col_act, col_dark = st.columns([2.2, 1])
    with col_act:
        st.markdown("##### Top At-Risk Outcomes")
        if not at_risk_preview.empty:
            for _, row in at_risk_preview.head(5).iterrows():
                title_str = (row["outcome"][:40] + "…") if len(str(row["outcome"])) > 40 else str(row["outcome"])
                rate      = row["mastery_rate"]
                color     = DANGER if rate < 50 else WARN
                activity_row(
                    icon="⚠️", icon_bg=PASTEL_PEACH,
                    title=title_str,
                    subtitle=f"{row['assessments']:,} assessments · {row['students']:,} students",
                    value=f"{rate}%",
                    status_label="At-Risk",
                    status_color=color,
                )
        else:
            st.info("No at-risk outcomes at current threshold.")

    with col_dark:
        dark_contrast_card("Proficiency Bands", "distribution snapshot")
        band_order  = ["Exceeds (90–100%)", "Meets (70–89%)", "Approaching (50–69%)", "Below (<50%)"]
        band_colors = [SUCCESS, "#6366f1", WARN, DANGER]
        bands_sorted = bands.set_index("band").reindex(band_order).reset_index().dropna()
        if not bands_sorted.empty:
            fig_donut = px.pie(bands_sorted, names="band", values="n",
                               color="band",
                               color_discrete_map=dict(zip(band_order, band_colors)), hole=0.55)
            fig_donut.update_traces(textinfo="percent", textfont=dict(color="#ffffff", size=10))
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10), height=200,
                showlegend=False,
                font=dict(color="#ffffff"),
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()

    # Subtab-driven detail charts
    if subtab == "At-Risk" or subtab is None:
        st.markdown("##### Outcomes Needing Attention")
        st.caption("Outcomes with >= N assessments and mastery rate below 70%.")
        min_n = st.slider("Min assessments threshold", 10, 500, 50, step=10, key="insights_min_n")
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

    elif subtab == "Bands":
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("##### Proficiency Band Distribution")
            band_order  = ["Exceeds (90–100%)", "Meets (70–89%)", "Approaching (50–69%)", "Below (<50%)"]
            band_colors = [SUCCESS, "#6366f1", WARN, DANGER]
            bands_sorted2 = bands.set_index("band").reindex(band_order).reset_index().dropna()
            fig_b = px.pie(bands_sorted2, names="band", values="n",
                           color="band",
                           color_discrete_map=dict(zip(band_order, band_colors)), hole=0.5)
            fig_b.update_traces(textinfo="percent+label", textfont=dict(color=INK))
            apply_chart_theme(fig_b, height=350, show_legend=False)
            st.plotly_chart(fig_b, use_container_width=True)
        with col_r:
            st.markdown("##### Monthly Mastery Trend")
            fig2 = go.Figure()
            fig2.add_scatter(
                x=trend_sorted["month"], y=trend_sorted["mastery_pct"],
                mode="lines+markers", line=dict(color="#6366f1", width=2.5),
                marker=dict(size=6), name="Mastery %",
                fill="tozeroy", fillcolor="rgba(99,102,241,0.10)",
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

    elif subtab == "Quadrant":
        st.markdown("##### Volume vs Mastery — Quadrant View")
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
                labels={"mastery_rate": "Mastery %", "assessments": "# Assessments", "students": "# Students"},
            )
            fig4.add_vline(x=med_mastery, line_dash="dot", line_color=INK_MUTED,
                           annotation_text=f"Median {med_mastery:.0f}%",
                           annotation_font_color=INK_MUTED)
            fig4.add_hline(y=med_vol, line_dash="dot", line_color=INK_MUTED,
                           annotation_text=f"Median {int(med_vol)}",
                           annotation_font_color=INK_MUTED)
            fig4.add_annotation(x=20, y=quad["assessments"].max()*0.95,
                                text="🚨 High Impact / Low Mastery",
                                showarrow=False, font=dict(color=DANGER, size=11))
            fig4.add_annotation(x=85, y=quad["assessments"].max()*0.95,
                                text="✅ High Impact / High Mastery",
                                showarrow=False, font=dict(color=SUCCESS, size=11))
            apply_chart_theme(fig4, height=480)
            fig4.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig4, use_container_width=True)

    elif subtab == "Benchmark":
        st.markdown("##### College Performance Benchmark")
        with st.spinner("Loading college data…"):
            bench2 = college_benchmark()
        bench2["college"] = bench2["account_id"].map(COLLEGE_NAMES).fillna(
            "Account " + bench2["account_id"].astype(str))
        bench2 = bench2.sort_values("mastery_rate", ascending=False)
        inst_avg = round(bench2["mastery_rate"].mean(), 1)
        fig5 = px.bar(
            bench2, x="college", y="mastery_rate",
            color="mastery_rate", color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
            labels={"college": "College", "mastery_rate": "Mastery %"},
            text=bench2["mastery_rate"].astype(str) + "%",
        )
        fig5.add_hline(y=inst_avg, line_dash="dash", line_color="#6366f1",
                       annotation_text=f"Institution avg {inst_avg}%",
                       annotation_font_color="#6366f1")
        fig5.update_traces(textposition="outside", textfont=dict(size=10, color=INK_MUTED))
        apply_chart_theme(fig5, height=420)
        fig5.update_layout(coloraxis_showscale=False, xaxis_tickangle=-35)
        st.plotly_chart(fig5, use_container_width=True)

    action_button_row([
        {"label": "Refresh", "icon": "🔄", "icon_bg": PASTEL_BLUE,   "key": "ins_refresh",  "callback": lambda: (st.cache_data.clear(), st.rerun())},
        {"label": "Export",  "icon": "📥", "icon_bg": PASTEL_PEACH,  "key": "ins_export2",  "callback": None},
        {"label": "Filter",  "icon": "🔍", "icon_bg": PASTEL_YELLOW, "key": "ins_filter2",  "callback": None},
        {"label": "Reset",   "icon": "↺",  "icon_bg": PASTEL_LILAC,  "key": "ins_reset",    "callback": None},
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: COLLEGES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Colleges":
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

    if selected_colleges:
        col_agg = col_agg[col_agg["college"].isin(selected_colleges)]

    subtab, search_val = top_header(
        "Colleges",
        subtabs=["Overview", "Drill-Down", "Compare"],
        tab_key="colleges_subtab",
        search_placeholder="Search colleges...",
        search_key="colleges_search"
    )

    # Apply search filter
    if search_val:
        col_agg = col_agg[col_agg["college"].str.contains(search_val, case=False, na=False)]

    college_options_list = col_agg[col_agg["assessments"].fillna(0) > 0]["college"].tolist()

    # Hero + metrics
    col_hero, col_metrics = st.columns([2.2, 1])
    with col_hero:
        hero_card(
            eyebrow="DRILL-DOWN",
            title="All Colleges",
            subtitle=f"Outcomes, performance, and courses grouped by college / department. {len(col_agg):,} colleges in view.",
            primary_cta="📥 Export",
            primary_key="col_export",
            secondary_cta="⚖️ Compare",
            secondary_key="col_compare_btn",
        )
    with col_metrics:
        metric_glass("Colleges", f"{len(col_agg):,}", icon="🏫", icon_bg=PASTEL_BLUE)
        avg_mastery = round(col_agg["mastery_rate"].mean(), 1) if not col_agg.empty else 0
        metric_glass("Avg Mastery", f"{avg_mastery}%", icon="🎯", icon_bg=PASTEL_MINT)

    if subtab == "Overview" or subtab is None:
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
            fig.update_traces(textposition="outside", textfont=dict(size=10, color=INK_MUTED))
            apply_chart_theme(fig, height=max(420, len(chart_data) * 26))
            fig.update_layout(coloraxis_showscale=False, margin=dict(t=10, l=10))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown("##### All Colleges Summary")
        show_all = col_agg[["college", "outcomes", "assessments", "mastery_rate", "avg_score"]].copy()
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
            if clicked_college != st.session_state.get("college_select"):
                st.session_state["college_select"] = clicked_college
                st.rerun()

    elif subtab == "Drill-Down":
        st.divider()
        selected_college = st.selectbox(
            "Select a college to drill down", sorted(college_options_list),
            key="college_select",
        )
        if selected_college:
            sel_row        = col_agg[col_agg["college"] == selected_college].iloc[0]
            sel_account_id = int(sel_row["account_id"])

            col_act2, col_dark2 = st.columns([2.2, 1])
            with col_act2:
                st.markdown(f"##### {selected_college} — Top Outcomes")
                with st.spinner("Loading outcomes…"):
                    outcomes = outcomes_for_college(sel_account_id)
                top5_out = outcomes.dropna(subset=["mastery_rate"]).head(5)
                for _, row in top5_out.iterrows():
                    title_str = (row["short_description"][:38] + "…") if len(str(row["short_description"])) > 38 else str(row["short_description"])
                    rate  = row["mastery_rate"] if pd.notna(row["mastery_rate"]) else 0
                    color = SUCCESS if rate >= 70 else (WARN if rate >= 50 else DANGER)
                    activity_row(
                        icon="📚", icon_bg=PASTEL_BLUE,
                        title=title_str,
                        subtitle=f"{row['display_name']} · {int(row['assessments'] or 0):,} assessments",
                        value=f"{rate}%",
                        status_label="Mastery",
                        status_color=color,
                    )

            with col_dark2:
                with st.spinner("Loading courses…"):
                    courses_c = courses_for_college(sel_account_id)
                leaderboard_rows = []
                if not courses_c.empty:
                    for _, row in courses_c.head(5).iterrows():
                        cname = row["course_name"][:20] + "…" if len(str(row["course_name"])) > 20 else str(row["course_name"])
                        rate  = row["mastery_rate"] if pd.notna(row["mastery_rate"]) else 0
                        color = SUCCESS if rate >= 70 else (WARN if rate >= 50 else DANGER)
                        leaderboard_rows.append((cname, f"{rate:.0f}%", color))
                dark_leaderboard_card("Top Courses", "by enrolment", rows=leaderboard_rows)

            st.divider()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Outcomes Defined",  f"{int(sel_row['outcomes']):,}")
            c2.metric("Total Assessments", f"{int(sel_row['assessments'] or 0):,}")
            c3.metric("Avg Mastery Rate",  f"{sel_row['mastery_rate']:.1f}%"
                      if pd.notna(sel_row['mastery_rate']) else "—")
            c4.metric("Avg Score",         f"{sel_row['avg_score']:.1f}%"
                      if pd.notna(sel_row['avg_score']) else "—")

            tab1, tab2, tab3 = st.tabs(["Outcomes", "Results Over Time", "Courses"])
            with tab1:
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
                days2 = st.session_state.get("date_filter_days", 0)
                with st.spinner("Loading results…"):
                    monthly_c  = monthly_results_for_college(sel_account_id, days2)
                    outcome_bd = outcome_breakdown_for_college(sel_account_id)
                if monthly_c.empty:
                    st.info("No assessment results found for this college.")
                else:
                    fig3 = go.Figure()
                    fig3.add_bar(x=monthly_c["month"], y=monthly_c["assessments"],
                                 name="Assessments", marker_color="#6366f1", opacity=0.65)
                    fig3.add_scatter(x=monthly_c["month"], y=monthly_c["mastery_pct"],
                                     name="Mastery %", yaxis="y2",
                                     line=dict(color="#10b981", width=2.5),
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

    elif subtab == "Compare":
        st.divider()
        chosen = st.multiselect("Select up to 2 colleges to compare",
                                sorted(college_options_list),
                                default=sorted(college_options_list)[:2],
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
                    days2 = st.session_state.get("date_filter_days", 0)
                    m_data = monthly_results_for_college(aid, days2)
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

    action_button_row([
        {"label": "Refresh", "icon": "🔄", "icon_bg": PASTEL_BLUE,   "key": "col_refresh",  "callback": lambda: (st.cache_data.clear(), st.rerun())},
        {"label": "Export",  "icon": "📥", "icon_bg": PASTEL_PEACH,  "key": "col_export2",  "callback": None},
        {"label": "Compare", "icon": "⚖️", "icon_bg": PASTEL_YELLOW, "key": "col_compare2", "callback": None},
        {"label": "Reset",   "icon": "↺",  "icon_bg": PASTEL_LILAC,  "key": "col_reset",    "callback": None},
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LEARNING OUTCOMES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Learning Outcomes":
    with st.spinner("Loading outcomes…"):
        df = all_outcomes()

    subtab, search_val = top_header(
        "Learning Outcomes",
        subtabs=["By Volume", "Quadrant", "Table"],
        tab_key="lo_subtab",
        search_placeholder="Search outcomes...",
        search_key="lo_header_search"
    )

    if search_val:
        mask = (
            df["display_name"].str.contains(search_val, case=False, na=False) |
            df["short_description"].str.contains(search_val, case=False, na=False)
        )
        df = df[mask]

    total_out_count = len(df)
    assessed_count  = df["assessments"].notna().sum()

    # Hero + metrics
    col_hero, col_metrics = st.columns([2.2, 1])
    with col_hero:
        hero_card(
            eyebrow="CATALOG",
            title="Outcome Catalog",
            subtitle=f"Browse, search, and analyze {total_out_count:,} institutional learning outcomes. {assessed_count:,} have assessment data.",
            primary_cta="📥 Export",
            primary_key="lo_export",
            secondary_cta="🔍 Filter",
            secondary_key="lo_filter",
        )
    with col_metrics:
        metric_glass("Total Outcomes", f"{total_out_count:,}", icon="📋", icon_bg=PASTEL_BLUE)
        assessed_pct = round(assessed_count / total_out_count * 100) if total_out_count else 0
        metric_glass("Assessed %", f"{assessed_pct}%", icon="✅", icon_bg=PASTEL_MINT)

    # Activity + dark contrast
    col_act, col_dark = st.columns([2.2, 1])
    with col_act:
        st.markdown("##### Top 5 Most-Assessed Outcomes")
        top5_df = df.dropna(subset=["assessments"]).nlargest(5, "assessments")
        for _, row in top5_df.iterrows():
            title_str = (str(row["short_description"])[:38] + "…") if len(str(row["short_description"])) > 38 else str(row["short_description"])
            rate  = row["mastery_rate"] if pd.notna(row.get("mastery_rate")) else 0
            color = SUCCESS if rate >= 70 else (WARN if rate >= 50 else DANGER)
            activity_row(
                icon="📖", icon_bg=PASTEL_BLUE,
                title=title_str,
                subtitle=f"{row['display_name']} · {int(row['assessments']):,} assessments",
                value=f"{rate}%",
                status_label="Mastery",
                status_color=color,
            )

    with col_dark:
        dark_contrast_card("Calculation Methods", "breakdown")
        method_counts = df["calculation_method"].value_counts().reset_index()
        method_counts.columns = ["method", "count"]
        if not method_counts.empty:
            fig_donut2 = px.pie(method_counts, names="method", values="count",
                                color_discrete_sequence=CHART_SEQ, hole=0.55)
            fig_donut2.update_traces(textinfo="percent", textfont=dict(color="#ffffff", size=10))
            fig_donut2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10), height=200,
                showlegend=False, font=dict(color="#ffffff"),
            )
            st.plotly_chart(fig_donut2, use_container_width=True)

    st.divider()

    if subtab == "By Volume" or subtab is None:
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
            fig2 = px.pie(method_counts, names="method", values="count",
                          color_discrete_sequence=CHART_SEQ, hole=0.5)
            fig2.update_traces(textinfo="percent", textfont=dict(color=INK))
            apply_chart_theme(fig2, height=320)
            st.plotly_chart(fig2, use_container_width=True)

    elif subtab == "Quadrant":
        with st.spinner("Loading quadrant…"):
            quad = outcome_volume_vs_mastery()
        if not quad.empty and not search_val:
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
            fig_q.add_vline(x=med_m, line_dash="dot", line_color=INK_MUTED)
            fig_q.add_hline(y=med_v, line_dash="dot", line_color=INK_MUTED)
            fig_q.add_annotation(x=10, y=quad["assessments"].max()*0.93,
                                 text="🚨 Needs Attention", showarrow=False,
                                 font=dict(color=DANGER, size=11))
            apply_chart_theme(fig_q, height=400)
            fig_q.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_q, use_container_width=True)

    elif subtab == "Table":
        st.caption(f"Showing {len(df):,} outcomes")
        show = df[["display_name", "short_description", "calculation_method",
                   "assessments", "mastery_rate", "avg_score"]].rename(columns={
            "display_name": "Code", "short_description": "Description",
            "calculation_method": "Method", "assessments": "# Assessments",
            "mastery_rate": "Mastery %", "avg_score": "Avg Score %",
        })
        st.dataframe(show, use_container_width=True, height=480)

    action_button_row([
        {"label": "Refresh", "icon": "🔄", "icon_bg": PASTEL_BLUE,   "key": "lo_refresh",  "callback": lambda: (st.cache_data.clear(), st.rerun())},
        {"label": "Export",  "icon": "📥", "icon_bg": PASTEL_PEACH,  "key": "lo_export2",  "callback": None},
        {"label": "Filter",  "icon": "🔍", "icon_bg": PASTEL_YELLOW, "key": "lo_filter2",  "callback": None},
        {"label": "Reset",   "icon": "↺",  "icon_bg": PASTEL_LILAC,  "key": "lo_reset",    "callback": None},
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: COURSE PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Course Performance":
    subtab, search_val = top_header(
        "Course Performance",
        subtabs=["Scatter", "Table"],
        tab_key="cp_subtab",
        search_placeholder="Search courses...",
        search_key="cp_header_search"
    )

    col1, col2 = st.columns(2)
    min_students = col1.slider("Min students", 1, 100, 5, key="cp_min_students")
    sort_by      = col2.selectbox("Sort by",
                                  ["mastery_rate", "students", "avg_score"],
                                  key="cp_sort_by")

    with st.spinner("Loading courses…"):
        df_cp = course_performance(min_students)

    if search_val:
        df_cp = df_cp[
            df_cp["name"].str.contains(search_val, case=False, na=False) |
            df_cp["course_code"].str.contains(search_val, case=False, na=False)
        ]

    df_cp = df_cp.sort_values(sort_by, ascending=False)
    n_courses  = len(df_cp)
    med_mastery_cp = round(df_cp["mastery_rate"].median(), 1) if not df_cp.empty else 0

    # Hero + metrics
    col_hero, col_metrics = st.columns([2.2, 1])
    with col_hero:
        hero_card(
            eyebrow="PERFORMANCE",
            title="Course Performance Dashboard",
            subtitle=f"Mastery rates and enrolment across {n_courses:,} courses with results.",
            primary_cta="📥 Export",
            primary_key="cp_export",
            secondary_cta="🔍 Filter",
            secondary_key="cp_filter",
        )
    with col_metrics:
        metric_glass("Courses", f"{n_courses:,}", icon="📚", icon_bg=PASTEL_BLUE)
        metric_glass("Median Mastery", f"{med_mastery_cp}%", icon="🎯", icon_bg=PASTEL_MINT)

    # Activity + dark contrast
    col_act, col_dark = st.columns([2.2, 1])
    with col_act:
        st.markdown("##### Top 5 Courses by Enrolment")
        top5_cp = df_cp.head(5)
        for _, row in top5_cp.iterrows():
            cname = (str(row["name"])[:38] + "…") if len(str(row["name"])) > 38 else str(row["name"])
            rate  = row["mastery_rate"] if pd.notna(row.get("mastery_rate")) else 0
            color = SUCCESS if rate >= 70 else (WARN if rate >= 50 else DANGER)
            activity_row(
                icon="🏫", icon_bg=PASTEL_BLUE,
                title=cname,
                subtitle=f"{row['course_code']} · {int(row['students']):,} students",
                value=f"{rate}%",
                status_label="Mastery",
                status_color=color,
            )

    with col_dark:
        leaderboard_rows = []
        for _, row in df_cp.head(5).iterrows():
            cname = (str(row["name"])[:18] + "…") if len(str(row["name"])) > 18 else str(row["name"])
            rate  = row["mastery_rate"] if pd.notna(row.get("mastery_rate")) else 0
            color = SUCCESS if rate >= 70 else (WARN if rate >= 50 else DANGER)
            leaderboard_rows.append((cname, f"{rate:.0f}%", color))
        dark_leaderboard_card("Top 5 by Enrolment", "courses leaderboard", rows=leaderboard_rows)

    st.divider()

    if subtab == "Scatter" or subtab is None:
        st.caption(f"{n_courses:,} courses matched")
        fig = px.scatter(
            df_cp.head(200), x="students", y="mastery_rate", size="assessments",
            color="avg_score", color_continuous_scale=CHART_DIVERGING, range_color=[0, 100],
            hover_name="name", hover_data={"course_code": True},
            labels={"students": "# Students", "mastery_rate": "Mastery %",
                    "avg_score": "Avg Score %"},
            title="Course Mastery vs. Enrolment (top 200)",
        )
        apply_chart_theme(fig, height=460)
        st.plotly_chart(fig, use_container_width=True)

    elif subtab == "Table":
        st.caption(f"{n_courses:,} courses matched")
        show = df_cp[["name", "course_code", "students", "assessments",
                       "mastery_rate", "avg_score"]].copy()
        show.columns = ["Course", "Code", "Students", "Assessments", "Mastery %", "Avg Score %"]
        st.dataframe(show, use_container_width=True, height=480)

    action_button_row([
        {"label": "Refresh", "icon": "🔄", "icon_bg": PASTEL_BLUE,   "key": "cp_refresh",  "callback": lambda: (st.cache_data.clear(), st.rerun())},
        {"label": "Export",  "icon": "📥", "icon_bg": PASTEL_PEACH,  "key": "cp_export2",  "callback": None},
        {"label": "Filter",  "icon": "🔍", "icon_bg": PASTEL_YELLOW, "key": "cp_filter2",  "callback": None},
        {"label": "Reset",   "icon": "↺",  "icon_bg": PASTEL_LILAC,  "key": "cp_reset",    "callback": None},
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: STUDENT MASTERY
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Student Mastery":
    subtab, search_val = top_header(
        "Student Mastery",
        subtabs=["Lookup", "History"],
        tab_key="sm_subtab",
        search_placeholder="Search student name...",
        search_key="sm_header_search"
    )

    # Hero card
    col_hero, col_metrics = st.columns([2.2, 1])
    with col_hero:
        hero_card(
            eyebrow="LOOKUP",
            title="Student Mastery Lookup",
            subtitle="Search a student to see their full outcome assessment history and mastery timeline.",
            primary_cta="🔍 Search",
            primary_key="sm_search_btn",
        )
    with col_metrics:
        metric_glass("Search Students", "Enter name below", icon="👤", icon_bg=PASTEL_BLUE)

    st.divider()

    # Use header search or inline search
    search = search_val if search_val else st.text_input(
        "Search student name",
        placeholder="e.g. Santos or Cruz", key="sm_search"
    )

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

            # Metrics row
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Assessments", f"{total:,}")
            c2.metric("Outcomes Mastered", f"{int(mastered):,} / {total:,}")
            c3.metric("Average Score",     f"{avg_pct:.1f}%")

            # Activity + dark contrast
            col_act, col_dark = st.columns([2.2, 1])
            with col_act:
                st.markdown("##### Recent 5 Assessments")
                if not sr.empty:
                    recent5 = sr.head(5)
                    for _, row in recent5.iterrows():
                        title_str = (str(row["short_description"])[:36] + "…") if len(str(row.get("short_description", "") or "")) > 36 else str(row.get("short_description", "—"))
                        is_mastered = row["mastery"] == "t"
                        color = SUCCESS if is_mastered else DANGER
                        pct   = round(row["percent"] * 100, 1) if pd.notna(row["percent"]) else 0
                        activity_row(
                            icon="✅" if is_mastered else "❌",
                            icon_bg=PASTEL_MINT if is_mastered else PASTEL_PEACH,
                            title=title_str,
                            subtitle=str(row.get("course_name", "—") or "—"),
                            value=f"{pct}%",
                            status_label="Mastered" if is_mastered else "Not Yet",
                            status_color=color,
                        )

            with col_dark:
                dark_contrast_card("Mastery Timeline", "score over time")
                if not sr.empty:
                    sr2 = sr.copy()
                    sr2["mastered"]  = sr2["mastery"] == "t"
                    sr2["score_pct"] = sr2["percent"] * 100
                    fig_sm = px.scatter(
                        sr2.sort_values("assessed_at"),
                        x="assessed_at", y="score_pct",
                        color="mastered",
                        color_discrete_map={True: SUCCESS, False: DANGER},
                        labels={"assessed_at": "Date", "score_pct": "Score %", "mastered": "Mastered"},
                    )
                    fig_sm.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=10, b=10, l=10, r=10), height=220,
                        showlegend=False,
                        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", color="rgba(255,255,255,0.5)"),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", color="rgba(255,255,255,0.5)", range=[0, 105]),
                        font=dict(color="rgba(255,255,255,0.7)"),
                    )
                    st.plotly_chart(fig_sm, use_container_width=True)

            st.divider()

            if subtab == "Lookup" or subtab is None:
                if not sr.empty:
                    sr3 = sr.copy()
                    sr3["mastered"]  = sr3["mastery"] == "t"
                    sr3["score_pct"] = sr3["percent"] * 100
                    fig_full = px.scatter(
                        sr3.sort_values("assessed_at"),
                        x="assessed_at", y="score_pct",
                        color="mastered",
                        color_discrete_map={True: SUCCESS, False: DANGER},
                        hover_data=["display_name", "course_name"],
                        labels={"assessed_at": "Date", "score_pct": "Score %", "mastered": "Mastered"},
                        title="Assessment History",
                    )
                    apply_chart_theme(fig_full, height=380)
                    add_time_controls(fig_full)
                    st.plotly_chart(fig_full, use_container_width=True)

            elif subtab == "History":
                st.markdown("##### Outcome Details")
                show = sr[["display_name", "short_description", "course_name",
                            "score", "possible", "percent", "mastery",
                            "assessed_at"]].copy()
                show["percent"] = (show["percent"] * 100).round(1)
                show["mastery"] = show["mastery"].map({"t": "✅", "f": "❌"})
                show.columns = ["Code", "Outcome", "Course", "Score", "Possible",
                                "Pct %", "Mastered", "Assessed At"]
                st.dataframe(show, use_container_width=True, height=420)

            if subtab == "Lookup" or subtab is None:
                st.markdown("##### Outcome Details")
                show2 = sr[["display_name", "short_description", "course_name",
                             "score", "possible", "percent", "mastery",
                             "assessed_at"]].copy()
                show2["percent"] = (show2["percent"] * 100).round(1)
                show2["mastery"] = show2["mastery"].map({"t": "✅", "f": "❌"})
                show2.columns = ["Code", "Outcome", "Course", "Score", "Possible",
                                 "Pct %", "Mastered", "Assessed At"]
                st.dataframe(show2, use_container_width=True, height=420)

    action_button_row([
        {"label": "Refresh", "icon": "🔄", "icon_bg": PASTEL_BLUE,   "key": "sm_refresh",  "callback": lambda: (st.cache_data.clear(), st.rerun())},
        {"label": "Export",  "icon": "📥", "icon_bg": PASTEL_PEACH,  "key": "sm_export",   "callback": None},
        {"label": "History", "icon": "📅", "icon_bg": PASTEL_YELLOW, "key": "sm_history",  "callback": None},
        {"label": "Reset",   "icon": "↺",  "icon_bg": PASTEL_LILAC,  "key": "sm_reset",    "callback": None},
    ])

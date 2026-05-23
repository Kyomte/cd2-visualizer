import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery

PROJECT  = "cd2-visualizer-data"
DATASET  = "cd2_data"
BQ_PRE   = f"`{PROJECT}.{DATASET}"

# Account ID → college/department name (derived from course subject patterns)
COLLEGE_NAMES = {
    105: "Sandbox / Admin",
    107: "Architecture",
    109: "Law",
    120: "Basic Education (K–12)",
    123: "NSTP",
    124: "Nursing",
    126: "Sports Management & PE",
    132: "EdTech / Course Playground",
    134: "Theology",
    135: "Economics",
    136: "Teacher Education",
    137: "Banking & Finance",
    139: "Communication & Media",
    141: "Elementary Education",
    145: "Literature & Translation",
    149: "Advertising & Fine Arts",
    150: "Interior Design",
    152: "Computer Science",
    154: "Information Technology",
    157: "Physical Therapy",
    161: "Biology & Life Sciences",
    165: "Tourism & Recreation Mgmt",
    177: "Creative Writing",
    178: "Communication (Campus B)",
    180: "Journalism",
    181: "Library Management",
    182: "Chemical Engineering",
    183: "Civil Engineering",
    184: "Electrical Engineering",
    185: "Electronics Engineering",
    186: "Industrial Engineering",
    187: "Mechanical Engineering",
    188: "Medical Technology",
    190: "Biochemistry",
    191: "Pharmacy",
    199: "SHS — ABM Track",
    203: "Health Sciences / Allied",
    204: "SHS — Various Tracks",
    210: "SHS — STEM Track",
    212: "Accountancy & Business",
    213: "Information Systems",
    214: "Management Accounting",
    325: "Tourism & Hospitality",
    327: "Seminary / Religious Education",
    339: "Psychology",
    424: "Medicine",
    447: "Applied Minor",
    455: "Teacher Certification Program",
}

st.set_page_config(
    page_title="CD2 Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stTabs [data-baseweb="tab"] { font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)


# ── BigQuery client ───────────────────────────────────────────────────────────

@st.cache_resource
def get_client():
    import json
    from google.oauth2 import service_account
    if "gcp_credentials_json" in st.secrets:
        info = json.loads(st.secrets["gcp_credentials_json"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
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


# ── Cached queries ────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def overview_stats():
    active_courses  = bq(f"SELECT COUNT(*) AS n FROM {BQ_PRE}.courses` WHERE workflow_state='available'")['n'].iloc[0]
    active_users    = bq(f"SELECT COUNT(*) AS n FROM {BQ_PRE}.users` WHERE workflow_state='registered'")['n'].iloc[0]
    active_outcomes = bq(f"SELECT COUNT(*) AS n FROM {BQ_PRE}.learning_outcomes` WHERE workflow_state='active'")['n'].iloc[0]
    mastery_pct     = bq(f"SELECT ROUND(COUNTIF(mastery='t')/COUNT(*)*100,1) AS n FROM {BQ_PRE}.learning_outcomes_results` WHERE workflow_state='active'")['n'].iloc[0]
    return pd.DataFrame([{
        "active_courses": active_courses,
        "active_users": active_users,
        "active_outcomes": active_outcomes,
        "mastery_pct": mastery_pct,
    }])

@st.cache_data(ttl=3600, show_spinner=False)
def monthly_results():
    return bq(f"""
        SELECT
          DATE_TRUNC(DATE(assessed_at), MONTH) AS month,
          COUNT(*) AS assessments,
          ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_pct
        FROM {BQ_PRE}.learning_outcomes_results`
        WHERE workflow_state = 'active'
          AND assessed_at IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def score_distribution():
    return bq(f"""
        SELECT ROUND(percent * 100) AS score_pct
        FROM {BQ_PRE}.learning_outcomes_results`
        WHERE workflow_state = 'active'
          AND percent IS NOT NULL
        LIMIT 50000
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def ratings_data():
    return bq(f"SELECT * FROM {BQ_PRE}.outcome_proficiencies_ratings`")

@st.cache_data(ttl=3600, show_spinner=False)
def college_summary():
    return bq(f"""
        SELECT
          c.account_id,
          COUNT(DISTINCT lo.id)  AS outcomes,
          SUM(stats.assessments) AS assessments,
          ROUND(AVG(stats.mastery_rate), 1) AS mastery_rate,
          ROUND(AVG(stats.avg_score), 1)    AS avg_score
        FROM {BQ_PRE}.learning_outcomes` lo
        JOIN {BQ_PRE}.courses` c
          ON lo.context_id = c.id AND lo.context_type = 'Course'
        LEFT JOIN (
          SELECT
            learning_outcome_id,
            COUNT(*) AS assessments,
            ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_rate,
            ROUND(AVG(percent) * 100, 1) AS avg_score
          FROM {BQ_PRE}.learning_outcomes_results`
          WHERE workflow_state = 'active'
          GROUP BY 1
        ) stats ON lo.id = stats.learning_outcome_id
        WHERE lo.workflow_state = 'active'
        GROUP BY 1

        UNION ALL

        SELECT
          lo.context_id AS account_id,
          COUNT(DISTINCT lo.id)  AS outcomes,
          SUM(stats.assessments) AS assessments,
          ROUND(AVG(stats.mastery_rate), 1) AS mastery_rate,
          ROUND(AVG(stats.avg_score), 1)    AS avg_score
        FROM {BQ_PRE}.learning_outcomes` lo
        LEFT JOIN (
          SELECT
            learning_outcome_id,
            COUNT(*) AS assessments,
            ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_rate,
            ROUND(AVG(percent) * 100, 1) AS avg_score
          FROM {BQ_PRE}.learning_outcomes_results`
          WHERE workflow_state = 'active'
          GROUP BY 1
        ) stats ON lo.id = stats.learning_outcome_id
        WHERE lo.workflow_state = 'active'
          AND lo.context_type = 'Account'
        GROUP BY 1
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def outcomes_for_college(account_id: int):
    return bq(f"""
        SELECT
          lo.id, lo.display_name, lo.short_description,
          lo.calculation_method, lo.context_type,
          stats.assessments,
          stats.mastery_rate,
          stats.avg_score
        FROM {BQ_PRE}.learning_outcomes` lo
        LEFT JOIN (
          SELECT
            learning_outcome_id,
            COUNT(*) AS assessments,
            ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_rate,
            ROUND(AVG(percent) * 100, 1) AS avg_score
          FROM {BQ_PRE}.learning_outcomes_results`
          WHERE workflow_state = 'active'
          GROUP BY 1
        ) stats ON lo.id = stats.learning_outcome_id
        WHERE lo.workflow_state = 'active'
          AND (
            (lo.context_type = 'Account' AND lo.context_id = {account_id})
            OR
            (lo.context_type = 'Course'  AND lo.context_id IN (
              SELECT id FROM {BQ_PRE}.courses` WHERE account_id = {account_id}
            ))
          )
        ORDER BY stats.assessments DESC NULLS LAST
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def monthly_results_for_college(account_id: int):
    return bq(f"""
        SELECT
          DATE_TRUNC(DATE(r.assessed_at), MONTH) AS month,
          COUNT(*) AS assessments,
          ROUND(COUNTIF(r.mastery='t') / COUNT(*) * 100, 1) AS mastery_pct
        FROM {BQ_PRE}.learning_outcomes_results` r
        JOIN {BQ_PRE}.courses` c ON r.context_id = c.id
        WHERE r.workflow_state = 'active'
          AND c.account_id = {account_id}
          AND r.assessed_at IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def courses_for_college(account_id: int):
    return bq(f"""
        SELECT
          c.id AS course_id, c.name AS course_name, c.course_code,
          COUNT(DISTINCT r.user_id)  AS students,
          COUNT(r.id)                AS assessments,
          ROUND(COUNTIF(r.mastery='t') / NULLIF(COUNT(r.id),0) * 100, 1) AS mastery_rate,
          ROUND(AVG(r.percent) * 100, 1) AS avg_score
        FROM {BQ_PRE}.courses` c
        JOIN {BQ_PRE}.learning_outcomes_results` r ON c.id = r.context_id
        WHERE c.account_id = {account_id}
          AND r.workflow_state = 'active'
        GROUP BY 1, 2, 3
        ORDER BY assessments DESC
        LIMIT 200
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def outcome_breakdown_for_college(account_id: int):
    return bq(f"""
        SELECT
          lo.short_description, lo.display_name,
          COUNT(r.id) AS assessments,
          ROUND(COUNTIF(r.mastery='t') / NULLIF(COUNT(r.id),0) * 100, 1) AS mastery_rate
        FROM {BQ_PRE}.learning_outcomes_results` r
        JOIN {BQ_PRE}.courses` c ON r.context_id = c.id
        JOIN {BQ_PRE}.learning_outcomes` lo ON r.learning_outcome_id = lo.id
        WHERE c.account_id = {account_id}
          AND r.workflow_state = 'active'
        GROUP BY 1, 2
        ORDER BY assessments DESC
        LIMIT 30
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def all_outcomes():
    return bq(f"""
        SELECT
          lo.id, lo.display_name, lo.short_description, lo.calculation_method,
          lo.workflow_state,
          stats.assessments, stats.mastery_rate, stats.avg_score
        FROM {BQ_PRE}.learning_outcomes` lo
        LEFT JOIN (
          SELECT
            learning_outcome_id,
            COUNT(*) AS assessments,
            ROUND(COUNTIF(mastery='t') / COUNT(*) * 100, 1) AS mastery_rate,
            ROUND(AVG(percent) * 100, 1) AS avg_score
          FROM {BQ_PRE}.learning_outcomes_results`
          WHERE workflow_state = 'active'
          GROUP BY 1
        ) stats ON lo.id = stats.learning_outcome_id
        WHERE lo.workflow_state = 'active'
    """)

@st.cache_data(ttl=3600, show_spinner=False)
def course_performance(min_students: int = 1):
    return bq(f"""
        SELECT
          c.id, c.name, c.course_code,
          COUNT(DISTINCT r.user_id) AS students,
          COUNT(r.id) AS assessments,
          ROUND(COUNTIF(r.mastery='t') / NULLIF(COUNT(r.id),0) * 100, 1) AS mastery_rate,
          ROUND(AVG(r.percent) * 100, 1) AS avg_score
        FROM {BQ_PRE}.courses` c
        JOIN {BQ_PRE}.learning_outcomes_results` r ON c.id = r.context_id
        WHERE r.workflow_state = 'active'
        GROUP BY 1, 2, 3
        HAVING students >= {min_students}
        ORDER BY assessments DESC
        LIMIT 500
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
        SELECT
          r.id, r.score, r.possible, r.percent, r.mastery,
          r.assessed_at, r.context_id,
          lo.display_name, lo.short_description,
          c.name AS course_name
        FROM {BQ_PRE}.learning_outcomes_results` r
        LEFT JOIN {BQ_PRE}.learning_outcomes` lo ON r.learning_outcome_id = lo.id
        LEFT JOIN {BQ_PRE}.courses` c ON r.context_id = c.id
        WHERE r.user_id = {user_id}
          AND r.workflow_state = 'active'
        ORDER BY r.assessed_at DESC
    """)


# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("CD2 Data Explorer")
st.sidebar.caption("Canvas Data 2 — BigQuery")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Colleges", "Learning Outcomes", "Course Performance", "Student Mastery"],
    index=0,
)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

if page == "Overview":
    st.title("📊 Overview Dashboard")

    with st.spinner("Loading…"):
        stats   = overview_stats().iloc[0]
        monthly = monthly_results()
        scores  = score_distribution()
        ratings = ratings_data()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Courses",    f"{int(stats['active_courses']):,}")
    c2.metric("Active Users",      f"{int(stats['active_users']):,}")
    c3.metric("Learning Outcomes", f"{int(stats['active_outcomes']):,}")
    c4.metric("Overall Mastery",   f"{stats['mastery_pct']}%")

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Results over Time")
        fig = go.Figure()
        fig.add_bar(x=monthly["month"], y=monthly["assessments"],
                    name="Assessments", marker_color="#667eea", opacity=0.7)
        fig.add_scatter(x=monthly["month"], y=monthly["mastery_pct"],
                        name="Mastery %", yaxis="y2",
                        line=dict(color="#f6a623", width=2))
        fig.update_layout(
            yaxis=dict(title="# Assessments"),
            yaxis2=dict(title="Mastery %", overlaying="y", side="right", range=[0, 105]),
            legend=dict(orientation="h", y=1.1),
            height=320, margin=dict(t=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Score Distribution")
        fig2 = px.histogram(scores, x="score_pct", nbins=20,
                            color_discrete_sequence=["#764ba2"],
                            labels={"score_pct": "Score %"})
        fig2.update_layout(showlegend=False, height=320, margin=dict(t=20),
                           xaxis_title="Score %", yaxis_title="Count")
        st.plotly_chart(fig2, use_container_width=True)

    if not ratings.empty:
        st.subheader("Proficiency Scale")
        for _, row in ratings.sort_values("points", ascending=False).iterrows():
            color = f"#{row['color']}" if pd.notna(row.get("color")) else "#ccc"
            tag   = " ⭐ Mastery" if row.get("mastery") in [True, "t"] else ""
            st.markdown(
                f'<div style="background:{color};color:white;padding:6px 14px;'
                f'border-radius:8px;margin:4px 0;display:inline-block;font-weight:600;">'
                f'{row["description"]}{tag} — {row["points"]} pts</div>',
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: COLLEGES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Colleges":
    st.title("🏫 Colleges — Outcomes View")

    with st.spinner("Loading college summary…"):
        col_sum = college_summary()

    col_sum["college"] = col_sum["account_id"].map(COLLEGE_NAMES).fillna(
        "Account " + col_sum["account_id"].astype(str)
    )
    # Aggregate in case account appears in both union branches
    col_agg = (col_sum.groupby(["account_id", "college"])
               .agg(outcomes=("outcomes","sum"),
                    assessments=("assessments","sum"),
                    mastery_rate=("mastery_rate","mean"),
                    avg_score=("avg_score","mean"))
               .reset_index()
               .sort_values("outcomes", ascending=False))

    # All-college bar chart
    st.subheader("Mastery Rate by College")
    chart_data = col_agg.dropna(subset=["mastery_rate"]).sort_values("mastery_rate")
    if not chart_data.empty:
        fig = px.bar(
            chart_data, x="mastery_rate", y="college", orientation="h",
            color="mastery_rate", color_continuous_scale="RdYlGn", range_color=[0, 100],
            labels={"mastery_rate": "Mastery %", "college": "College / Department"},
            text=chart_data["mastery_rate"].round(1).astype(str) + "%",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=max(400, len(chart_data) * 26),
            margin=dict(t=10, l=10),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # College selector
    college_options = col_agg[col_agg["assessments"].fillna(0) > 0]["college"].tolist()
    selected_college = st.selectbox("Select a college to drill down", sorted(college_options))
    sel_row = col_agg[col_agg["college"] == selected_college].iloc[0]
    sel_account_id = int(sel_row["account_id"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Outcomes Defined",  f"{int(sel_row['outcomes']):,}")
    c2.metric("Total Assessments", f"{int(sel_row['assessments'] or 0):,}")
    c3.metric("Avg Mastery Rate",  f"{sel_row['mastery_rate']:.1f}%" if pd.notna(sel_row['mastery_rate']) else "—")
    c4.metric("Avg Score",         f"{sel_row['avg_score']:.1f}%"    if pd.notna(sel_row['avg_score'])    else "—")

    tab1, tab2, tab3 = st.tabs(["Outcomes", "Results Over Time", "Courses"])

    with tab1:
        with st.spinner("Loading outcomes…"):
            outcomes = outcomes_for_college(sel_account_id)

        search_out = st.text_input("Filter outcomes", placeholder="e.g. Identify or design")
        disp = outcomes.copy()
        if search_out:
            mask = (
                disp["short_description"].str.contains(search_out, case=False, na=False) |
                disp["display_name"].str.contains(search_out, case=False, na=False)
            )
            disp = disp[mask]

        chart = disp.dropna(subset=["mastery_rate"]).head(30).sort_values("mastery_rate")
        if not chart.empty:
            fig2 = px.bar(
                chart, x="mastery_rate", y="short_description", orientation="h",
                color="mastery_rate", color_continuous_scale="RdYlGn", range_color=[0, 100],
                labels={"mastery_rate": "Mastery %", "short_description": "Outcome"},
                title="Top 30 Outcomes — Mastery Rate",
            )
            fig2.update_layout(height=max(350, len(chart)*26),
                               margin=dict(t=40), coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

        show = disp[["display_name", "short_description", "calculation_method",
                     "context_type", "assessments", "mastery_rate", "avg_score"]].copy()
        show.columns = ["Code", "Outcome", "Method", "Level",
                        "Assessments", "Mastery %", "Avg Score %"]
        st.dataframe(show, use_container_width=True, height=400)

    with tab2:
        with st.spinner("Loading results…"):
            monthly_c  = monthly_results_for_college(sel_account_id)
            outcome_bd = outcome_breakdown_for_college(sel_account_id)

        if monthly_c.empty:
            st.info("No assessment results found for this college.")
        else:
            fig3 = go.Figure()
            fig3.add_bar(x=monthly_c["month"], y=monthly_c["assessments"],
                         name="Assessments", marker_color="#667eea", opacity=0.7)
            fig3.add_scatter(x=monthly_c["month"], y=monthly_c["mastery_pct"],
                             name="Mastery %", yaxis="y2",
                             line=dict(color="#f6a623", width=2))
            fig3.update_layout(
                yaxis=dict(title="# Assessments"),
                yaxis2=dict(title="Mastery %", overlaying="y", side="right", range=[0, 105]),
                legend=dict(orientation="h", y=1.1),
                height=350, margin=dict(t=20),
            )
            st.plotly_chart(fig3, use_container_width=True)

        if not outcome_bd.empty:
            st.subheader("Outcome Breakdown")
            top_ob = outcome_bd.sort_values("mastery_rate")
            fig4 = px.bar(
                top_ob, x="mastery_rate", y="short_description", orientation="h",
                color="mastery_rate", color_continuous_scale="RdYlGn", range_color=[0, 100],
                labels={"mastery_rate": "Mastery %", "short_description": "Outcome"},
            )
            fig4.update_layout(height=max(300, len(top_ob)*28),
                               margin=dict(t=10), coloraxis_showscale=False)
            st.plotly_chart(fig4, use_container_width=True)

    with tab3:
        with st.spinner("Loading courses…"):
            courses_c = courses_for_college(sel_account_id)

        if courses_c.empty:
            st.info("No courses with assessment data found.")
        else:
            fig5 = px.scatter(
                courses_c, x="students", y="mastery_rate", size="assessments",
                color="avg_score", color_continuous_scale="RdYlGn",
                hover_name="course_name",
                labels={"students": "# Students", "mastery_rate": "Mastery %",
                        "avg_score": "Avg Score %"},
                title=f"Courses in {selected_college}",
            )
            fig5.update_layout(height=380, margin=dict(t=40))
            st.plotly_chart(fig5, use_container_width=True)

            show_c = courses_c[["course_name", "course_code", "students",
                                 "assessments", "mastery_rate", "avg_score"]].copy()
            show_c.columns = ["Course", "Code", "Students", "Assessments",
                               "Mastery %", "Avg Score %"]
            st.dataframe(show_c, use_container_width=True, height=400)

    st.divider()
    st.subheader("All Colleges Summary")
    show_all = col_agg[["college", "outcomes", "assessments",
                         "mastery_rate", "avg_score"]].copy()
    show_all.columns = ["College", "Outcomes", "Assessments", "Mastery %", "Avg Score %"]
    show_all["Mastery %"]   = show_all["Mastery %"].round(1)
    show_all["Avg Score %"] = show_all["Avg Score %"].round(1)
    st.dataframe(show_all, use_container_width=True, height=400)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LEARNING OUTCOMES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Learning Outcomes":
    st.title("🎯 Learning Outcomes")

    with st.spinner("Loading outcomes…"):
        df = all_outcomes()

    search = st.text_input("Search outcomes", placeholder="e.g. THM5206 or Identify…")
    if search:
        mask = (
            df["display_name"].str.contains(search, case=False, na=False) |
            df["short_description"].str.contains(search, case=False, na=False)
        )
        df = df[mask]

    st.caption(f"Showing {len(df):,} outcomes")

    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        top_n = df.dropna(subset=["mastery_rate"]).nlargest(20, "assessments").sort_values("mastery_rate")
        if not top_n.empty:
            fig = px.bar(
                top_n, x="mastery_rate", y="short_description", orientation="h",
                color="mastery_rate", color_continuous_scale="RdYlGn", range_color=[0, 100],
                labels={"mastery_rate": "Mastery %", "short_description": "Outcome"},
                title="Top 20 Most-Assessed Outcomes — Mastery Rate",
            )
            fig.update_layout(height=500, margin=dict(t=40), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Calculation Methods")
        method_counts = df["calculation_method"].value_counts().reset_index()
        method_counts.columns = ["method", "count"]
        fig2 = px.pie(method_counts, names="method", values="count",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(height=300, margin=dict(t=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Outcomes Table")
    show = df[["display_name", "short_description", "calculation_method",
               "assessments", "mastery_rate", "avg_score"]].rename(columns={
        "display_name": "Code", "short_description": "Description",
        "calculation_method": "Method", "assessments": "# Assessments",
        "mastery_rate": "Mastery %", "avg_score": "Avg Score %",
    })
    st.dataframe(show, use_container_width=True, height=400)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: COURSE PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Course Performance":
    st.title("📚 Course Performance")

    col1, col2 = st.columns(2)
    min_students = col1.slider("Min students", 1, 100, 5)
    sort_by      = col2.selectbox("Sort by", ["mastery_rate", "students", "avg_score"])

    with st.spinner("Loading courses…"):
        df = course_performance(min_students)

    df = df.sort_values(sort_by, ascending=False)
    st.caption(f"{len(df):,} courses matched")

    fig = px.scatter(
        df.head(200),
        x="students", y="mastery_rate", size="assessments",
        color="avg_score", color_continuous_scale="RdYlGn",
        hover_name="name", hover_data={"course_code": True},
        labels={"students": "# Students", "mastery_rate": "Mastery %",
                "avg_score": "Avg Score %"},
        title="Course Mastery vs. Enrolment (top 200)",
    )
    fig.update_layout(height=420, margin=dict(t=40))
    st.plotly_chart(fig, use_container_width=True)

    show = df[["name", "course_code", "students", "assessments",
               "mastery_rate", "avg_score"]].copy()
    show.columns = ["Course", "Code", "Students", "Assessments", "Mastery %", "Avg Score %"]
    st.dataframe(show, use_container_width=True, height=400)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: STUDENT MASTERY
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Student Mastery":
    st.title("👤 Student Mastery")

    search = st.text_input("Search student name", placeholder="e.g. Santos or Cruz")

    if not search or len(search) < 2:
        st.info("Enter at least 2 characters to search for a student.")
    else:
        with st.spinner("Searching…"):
            matched = search_users(search)

        if matched.empty:
            st.warning("No users found.")
        else:
            options = matched.apply(lambda r: f"{r['name']} (ID {r['id']})", axis=1).tolist()
            choice  = st.selectbox("Select student", options)
            uid     = int(choice.split("ID ")[1].rstrip(")"))

            with st.spinner("Loading results…"):
                sr = student_results(uid)

            total    = len(sr)
            mastered = (sr["mastery"] == "t").sum()
            avg_pct  = sr["percent"].mean() * 100 if total else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Assessments", f"{total:,}")
            c2.metric("Outcomes Mastered",  f"{int(mastered):,} / {total:,}")
            c3.metric("Average Score",      f"{avg_pct:.1f}%")

            if not sr.empty:
                sr["mastered"] = sr["mastery"] == "t"
                sr["score_pct"] = sr["percent"] * 100
                fig = px.scatter(
                    sr.sort_values("assessed_at"),
                    x="assessed_at", y="score_pct",
                    color="mastered",
                    color_discrete_map={True: "#2ecc71", False: "#e74c3c"},
                    hover_data=["display_name", "course_name"],
                    labels={"assessed_at": "Date", "score_pct": "Score %",
                            "mastered": "Mastered"},
                    title="Assessment History",
                )
                fig.update_layout(height=350, margin=dict(t=40))
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Outcome Details")
            show = sr[["display_name", "short_description", "course_name",
                        "score", "possible", "percent", "mastery",
                        "assessed_at"]].copy()
            show["percent"] = (show["percent"] * 100).round(1)
            show["mastery"] = show["mastery"].map({"t": "✅", "f": "❌"})
            show.columns = ["Code", "Outcome", "Course", "Score", "Possible",
                            "Pct %", "Mastered", "Assessed At"]
            st.dataframe(show, use_container_width=True, height=400)

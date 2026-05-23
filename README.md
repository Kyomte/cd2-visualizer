# CD2 Data Explorer

A data visualization tool for Canvas Data 2 (CD2) learning outcomes, built with Streamlit and Google BigQuery.

## Features

- **Overview Dashboard** — Key stats, monthly assessment trends, score distribution, and proficiency scale
- **Colleges** — Browse learning outcomes and mastery rates by college/department, with course and timeline breakdowns
- **Learning Outcomes** — Search and explore all outcomes with mastery rate charts
- **Course Performance** — Compare courses by enrollment, mastery rate, and average score
- **Student Mastery** — Look up individual students and view their full assessment history

## Tech Stack

- [Streamlit](https://streamlit.io) — UI framework
- [Google BigQuery](https://cloud.google.com/bigquery) — Data warehouse
- [Plotly](https://plotly.com/python/) — Charts and visualizations
- [Pandas](https://pandas.pydata.org) — Data manipulation

## Data

Sourced from Canvas Data 2 (CD2) exports. The following tables are loaded into BigQuery:

| Table | Description |
|-------|-------------|
| `courses` | Course catalog |
| `users` | Student and staff accounts |
| `learning_outcomes` | Outcome definitions |
| `learning_outcomes_results` | Per-student outcome assessments |
| `learning_outcomes_question_groups` | Outcome question groupings |
| `learning_outcomes_question_results` | Per-question results |
| `outcome_proficiencies` | Proficiency scale config |
| `outcome_proficiencies_ratings` | Rating levels (e.g. Mastery, Exceeds) |

## Running Locally

### Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`) with a project and BigQuery enabled
- Application Default Credentials set up via `gcloud auth application-default login`

### Setup

```bash
git clone https://github.com/Kyomte/cd2-visualizer.git
cd cd2-visualizer

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
./run.sh
```

Then open [http://localhost:8501](http://localhost:8501).

## Deploying to Streamlit Community Cloud

1. Fork or push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Under **Settings → Secrets**, add your Google service account credentials:

```toml
gcp_credentials_json = '{ "type": "service_account", "project_id": "...", ... }'
```

The service account needs the following IAM roles on your GCP project:
- `roles/bigquery.dataViewer`
- `roles/bigquery.jobUser`

---

Made by Kiel Mingote

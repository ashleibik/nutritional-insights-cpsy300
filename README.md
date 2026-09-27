# Cloud Native Nutritional Insights Application

CPSY-300-A Cloud Computing, Fall 2026, Project 1

Processes the `All_Diets.csv` dataset to get nutritional insights (protein, carbs, fat) per diet type and cuisine, using Docker, a simulated serverless function with Azurite, and a CI/CD pipeline with GitHub Actions.

## Team and task split

| Member | Tasks |
|---|---|
| Ahmed | Task 1 (data analysis), Task 3 (Azurite + serverless function), Task 5 data processing enhancement, PDF report |
| Teammate | Task 2 (Docker + Docker Compose), Task 4 (GitHub Actions CI/CD), Task 5 multi stage Docker enhancement |
| Both | Video presentation, contribution report |

## Project structure

```
.
├── All_Diets.csv              # dataset
├── data_analysis.py           # Task 1
├── lambda_function.py         # Task 3 (coming)
├── Dockerfile                 # Task 2 (coming)
├── docker-compose.yml         # Task 2 (coming)
├── .github/workflows/deploy.yml  # Task 4 (coming)
├── requirements.txt
├── simulated_nosql/           # Task 3 results (JSON)
├── docs/screenshots/          # screenshots for the report
└── CONTRIBUTION_LOG.md        # meetings, hours, who did what
```

## Run Task 1

```bash
pip install -r requirements.txt
python3 data_analysis.py
```

Results and charts are saved in `outputs/`.

## How we work

1. Never push straight to `main`. Make a branch for each task (`task1-analysis`, `task2-docker`, ...).
2. Open a pull request and have the other person review and approve it before merging.
3. Log meetings and hours in `CONTRIBUTION_LOG.md`.
4. Every screenshot needs the date and time visible.

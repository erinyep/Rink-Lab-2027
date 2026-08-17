# Rink Lab Agent Instructions

## Project Purpose

Rink Lab is a hockey analytics research project focused on understanding
player talent, repeatability, predictive value, and NCAA-to-NHL translation.

The project uses both R and Python. Do not default to one language for every
task. Choose the language that best fits the analysis and preserve opportunities
for the project owner to learn both.

## Research Principles

- Treat this as a research project, not a player-ranking app.
- Start with a hockey question before choosing a statistical method.
- Distinguish descriptive, explanatory, and predictive analyses.
- Do not assume correlation implies player skill or predictive value.
- Distinguish repeatable skill from outcome variance and luck.
- Validate datasets before modeling.
- Document assumptions and important methodological decisions.
- Prefer interpretable baselines before complex models.

## Data Rules

- Never manually modify files in `data/raw/`.
- Raw data should be reproducible from source whenever possible.
- Store cleaned or transformed datasets in `data/processed/`.
- Preserve NHL `player_id` as the primary player identifier where available.
- Keep season identifiers explicit. Example:
  - Human: 2025-26
  - NHL API: 20252026
- Do not silently remove players because of games-played or TOI thresholds.
  Document and justify analytical filters.
- Treat skaters and goalies as separate analytical populations unless an
  analysis explicitly requires both.

## Data Sources

Prefer authoritative or well-documented sources.

For NHL data, prefer:
1. NHL public APIs
2. fastRhockey / SportsDataverse
3. NHL EDGE where appropriate

Document the source and retrieval method for new datasets.

## R

Use R primarily for:
- exploratory data analysis
- descriptive statistics
- statistical inference
- visualization
- hockey-specific exploration

Prefer tidyverse conventions where practical.

Reusable R functions belong under `R/`.

## Python

Use Python primarily for:
- data pipelines
- larger-scale transformations
- feature engineering
- predictive modeling
- machine learning

Reusable Python code belongs under `src/`.

Do not commit the Python virtual environment.

## Analysis Workflow

Prefer:

Research question
→ acquire data
→ inspect
→ validate
→ clean
→ describe
→ visualize
→ establish baseline
→ model
→ evaluate
→ interpret hockey meaning

Do not jump directly from raw data to machine learning.

## Reproducibility

- Avoid hard-coded absolute local paths.
- Use repository-relative paths.
- Record important package dependencies.
- Do not commit credentials, API keys, virtual environments, or large
  generated datasets.
- Code should be capable of recreating processed datasets from raw sources.

## Validation

Before accepting a new dataset:

- Check row and column counts.
- Check unique player identifiers.
- Check missingness.
- Check duplicates.
- Inspect extreme values.
- Verify season and game type.
- Verify pagination completed.
- Confirm the population represents what the analysis claims it represents.

## Project Roadmap

Read `NEXT_STEPS.md` before beginning substantial new analysis.

Update `NEXT_STEPS.md` when completing a research milestone or identifying a
significant new research question.

## Working Style

- Explain important statistical or hockey-analysis decisions in comments.
- Prefer readable research code over clever code.
- Do not introduce unnecessary dependencies.
- Do not refactor unrelated code without a reason.
- Preserve useful exploratory work rather than replacing it unnecessarily.
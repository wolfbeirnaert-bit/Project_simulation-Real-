# Agentic SMA Radiology Pipeline

This repository now contains a clean reproducible pipeline alongside the legacy report and old simulation scripts.

## Run Commands

Recommended environment:

```bash
conda run -n SMWA2026 python -m sma_agents.run_pipeline --mode quick
```

Full confirmatory run:

```bash
conda run -n SMWA2026 python -m sma_agents.run_pipeline --mode full --workers 4
```

The plain command also works when your active Python is 3.11+ with the dependencies installed:

```bash
python -m sma_agents.run_pipeline --mode quick
python -m sma_agents.run_pipeline --mode full --workers 4
```

## Workers

`--workers` controls how many designs are evaluated in parallel.

- `--workers 1`: slowest, most robust, easiest to debug.
- `--workers 4`: recommended default on an 8-core laptop; usually the best balance.
- `--workers 8`: uses all visible CPU cores; can be faster, but may make the machine less responsive and may not scale perfectly.

In restricted sandbox environments, process-based workers may be blocked. The pipeline then falls back to threads so the command remains runnable, but a normal local terminal is preferred for the fastest full run.

## Workflow

Each run creates `outputs/YYYYMMDD_HHMMSS/` with:

- `config_used.yaml`
- `design_matrix.csv`
- `weekly_results.csv`
- `raw_results.csv`
- `batch_results.csv`
- `summary_results.csv`
- `tables/`
- `figures/`
- `report_assets/`
- `run_log.txt`

The pipeline also mirrors current report-ready files into top-level `report_assets/`.

## Conceptual Agents

The `agents/` folder contains markdown responsibilities for:

- AssignmentInterpreterAgent
- SimulationArchitectAgent
- ScheduleGeneratorAgent
- ExperimentalDesignAgent
- OutputAnalysisAgent
- StatisticalComparisonAgent
- OptimisationAndParetoAgent
- ReportWriterAgent
- QAReviewerAgent

These are implemented as a structured workflow rather than live LLM agents.

Live LLM agents can be added later as an optional review/reporting layer after deterministic simulation outputs exist, for example:

```bash
python -m sma_agents.run_llm_agents --output outputs/latest --agents qa report
```

The simulation and statistics should remain deterministic Python code for reproducibility.

## Important Notes

- Full mode evaluates all 132 required configurations: strategies 1-3, urgent slots 10-20, rules 1-4.
- Quick mode is only a smoke test and must not be used for final conclusions.
- High urgent counts 18-20 are tested. They may be marked unstable only from generated output evidence.
- Existing root scripts and old `smaproject2026` code are preserved as legacy/reference material.

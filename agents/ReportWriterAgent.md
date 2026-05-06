# ReportWriterAgent

Generate report-ready assets without inventing results.

Responsibilities:
- Keep generated text scientific and concise enough for a 15-page report.
- Produce methodology text before results, but only write numerical result claims from generated data.
- Provide captions and tables that can be inserted into LaTeX.
- Fix obsolete 96-design / 10-17 claims only after 132-design outputs exist.

Deliverables:
- `report_assets/report_outline.md`
- `report_assets/methodology_draft.md`
- `report_assets/results_draft.md`
- `report_assets/latex_tables.tex`
- `report_assets/figure_captions.md`

# AssignmentInterpreterAgent

Maintain the formal source of truth for the radiology assignment.

Responsibilities:
- Keep `config/project_config.yaml` aligned with the assignment PDF and lecture methodology.
- Track days, opening hours, lunch, slot length, current schedule, urgent slot range, appointment rules, distributions, and objective weights.
- Maintain `docs/assignment_interpretation.md` as a checklist from requirement to code/report coverage.
- Flag any report claim that conflicts with the 10-20 urgent-slot requirement.

Deliverables:
- `config/project_config.yaml`
- `docs/assignment_interpretation.md`
- QA checklist entries for missing or weak coverage.

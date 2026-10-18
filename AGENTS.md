# Repository instructions

## Code Review Rules

Review pull requests for actionable defects introduced by the change, regressions, missed requirements, and violations of this repository's conventions. Treat review as an additional signal; do not report preferences or speculative concerns as findings.

### Select applicable guidance

- Read the pull request description, complete diff, and relevant surrounding code before deciding which rules apply. Do not classify from a directory name alone.
- For Kotlin and Spring changes, read `plugins/kopring/skills/guide/SKILL.md` and the relevant skill and convention documents under `plugins/kopring/`.
- For Next.js and TypeScript changes, read `plugins/nextts/skills/guide/SKILL.md` and the relevant TypeScript, components, Tailwind, or UI skill under `plugins/nextts/skills/`.
- For Django changes, read `plugins/django/skills/guide/SKILL.md` and the relevant server, templates, or HTMX skill under `plugins/django/skills/`.
- For design documents or UI changes, read `plugins/design/skills/design/SKILL.md`, `plugins/design/docs/design-doc.md`, and the project's approved design references. Compare against approved IA, flows, wireframes, tokens, and component sources where available.
- For planning documents, read `plugins/planning/skills/rules/SKILL.md` and the relevant planning skill. Follow the repository's configured backlog and issue-tracking mode.
- Apply multiple sets of guidance when a pull request spans areas. The detailed source map is in `plugins/pr-review/docs/adapters/README.md`; the review workflow is in `plugins/pr-review/docs/review-workflow.md`.
- Project-local `AGENTS.md`, `CLAUDE.md`, and explicit approved requirements are also relevant. Resolve conflicts using the most specific applicable project guidance and identify unresolved ambiguity instead of inventing policy.

### Findings

- Report only actionable issues supported by the diff and repository evidence. Prioritize correctness, security, data integrity, compatibility, and user-visible behavior.
- For each finding, state severity, the failing condition, evidence, impact, and a concise remediation direction.
- Attach findings to changed lines that cause the issue. Do not comment on unchanged lines or submit duplicate findings for one root cause.
- For design changes, check relevant states, accessibility, and responsive behavior. Do not claim visual or interaction verification unless the rendered UI was inspected; state when review is source-only.
- Do not claim tests, builds, or browser checks passed unless they were actually run. Distinguish executed checks from checks not run.
- If no actionable issue is found, summarize the reviewed scope and verification limits without claiming exhaustive correctness.

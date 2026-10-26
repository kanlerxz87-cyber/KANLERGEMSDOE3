"""Operational guard for immutable, budget-exhausted research journals.

Low-level functions remain readable/importable for synthetic tests and future
explicitly authorized orchestration. This does not alter a metric, model, writer
or the upstream shared-template source. It prevents old CLI commands overwriting
cards/artifacts after their frozen sessions. Read-only audits remain available.
"""


def stop_archived_cli() -> None:
    raise SystemExit(
        "Archived session: its experiments and negative cards are frozen. "
        "This CLI cannot rerun training, rewrite a research TIFF or repin a run card. "
        "Use read-only audits. A new experiment needs an explicitly assigned lane, "
        "canonical shared cache/evaluator, resolved registry and a new authorized ledger."
    )

#!/usr/bin/env python3
"""Build the static portfolio from the audited, immutable historical manifest."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def portfolio_rows(audit: dict) -> str:
    output = []
    for row in sorted(audit["rows"], key=lambda x: x["site"]):
        site, repo, ref, path = (row[k] for k in ("site", "repo", "ref", "path"))
        filename = Path(path).name
        file_url = f"https://github.com/buffedlizard55-lab/{repo}/raw/{ref}/{path}"
        site_url = f"https://buffedlizard55-lab.github.io/{site}/"
        overlap = f"{row['max_within_3px'] * 100:.2f}%"
        alias = " · same mask" if row["exact_mask_alias_sites"] else ""
        verdict = "YES" if row["passes_nine_site_final_dot_threshold"] else "NO"
        output.append(
            f'          <tr><td><a href="{esc(site_url)}">{esc(site)}</a></td>'
            f'<td><a class="file-link" href="{esc(file_url)}">{esc(filename)}</a>'
            f'<small class="cell-secondary">SHA-256 {esc(row["sha256"][:16])}… · research only</small></td>'
            f'<td><span class="claim">{esc(row["owner_reported_claim"])}</span>'
            '<small class="cell-secondary">USER-REPORTED<br>not a receipt</small></td>'
            '<td>Not estimable<small class="cell-secondary">No calibrated forecast</small></td>'
            f'<td><span class="badge-no">{verdict}</span><small class="cell-secondary">{overlap} near {esc(row["max_within_3px_site"])}{esc(alias)}</small></td>'
            '<td><span class="badge-no">NO</span><small class="cell-secondary">Historical file</small></td></tr>'
        )
    return "\n".join(output)


def generated_files() -> dict[Path, str]:
    audit_path = ROOT / "evidence/portfolio-audit.json"
    card_path = ROOT / "evidence/run-card.json"
    audit = json.loads(audit_path.read_text())
    template = (ROOT / "site/index.template.html").read_text()
    values = {"{{PORTFOLIO_ROWS}}": portfolio_rows(audit), "{{SITE_COUNT}}": str(len(audit["rows"])),
              "{{AUDIT_DATE}}": audit["generated_utc"][:10]}
    for key, value in values.items():
        if template.count(key) != 1:
            raise ValueError(f"expected exactly one {key} placeholder")
        template = template.replace(key, value)
    return {ROOT / "docs/index.html": template, ROOT / "docs/data/portfolio-audit.json": audit_path.read_text(),
            ROOT / "docs/data/run-card.json": card_path.read_text()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if committed site differs from its sources")
    args = parser.parse_args()
    stale = []
    for path, contents in generated_files().items():
        if args.check:
            if not path.exists() or path.read_text() != contents:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
    if stale:
        raise SystemExit("Stale generated site files: " + ", ".join(stale))
    print("Static site " + ("is current" if args.check else "built"))


if __name__ == "__main__":
    main()

"""Shared-template bugfix wrappers & diagnostics (preserving byte-pinned `vendor/gems57/*` intact).

Documented defects addressed:
- `IR-TEMPLATE-CODELOAD-01`: Zero-REST-quota blobless git / codeload fetch fallback (`fetch_raw`).
- `IR-TEMPLATE-MKSTEMP-CHMOD-04`: `0644` world-readable temporary file creation (`world_readable_temp_path`).
- `IR-TEMPLATE-RHO-SIGN-05` & `IR-TEMPLATE-LATTICE-HALO-06`: Two-sided `|Spearman| > 0.90` check and
  `>= 95%` 3-px halo-saturated synthetic lattice classification (`representation_class`, `two_phase_summary`).
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import tarfile
import tempfile
import urllib.request
from math import isnan
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
JACCARD_LIMIT = 0.50
DENSE_SUPPORT_FRACTION = 0.20
HALO_SATURATION_FRACTION = 0.95


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def world_readable_temp_path(parent: Path, stem: str, suffix: str) -> Path:
    fd, name = tempfile.mkstemp(prefix=f".{stem}.", suffix=suffix, dir=parent)
    os.fchmod(fd, 0o644)
    os.close(fd)
    return Path(name)


def fetch_raw(repo: str, ref: str, remote_path: str, dst: Path) -> None:
    """Fetch a single file from GitHub via blobless git (`--filter=blob:none`), codeload, or `gh api`."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".part")

    git_cache = ROOT / ".cache" / "git_blobs" / repo.replace("/", "__")
    git_cache.mkdir(parents=True, exist_ok=True)
    if not (git_cache / "HEAD").exists():
        subprocess.run(["git", "init", "--bare", "-q", str(git_cache)], check=True)
    if subprocess.run(["git", "-C", str(git_cache), "cat-file", "-e", f"{ref}^{{commit}}"], capture_output=True).returncode != 0:
        subprocess.run(
            ["git", "-C", str(git_cache), "fetch", "-q", "--filter=blob:none", "--no-tags", f"https://github.com/{repo}.git", ref],
            check=False,
        )
    with tmp.open("wb") as out:
        r = subprocess.run(["git", "-C", str(git_cache), "show", f"{ref}:{remote_path}"], stdout=out, stderr=subprocess.DEVNULL)
    if r.returncode == 0 and tmp.stat().st_size > 0:
        tmp.replace(dst)
        return
    tmp.unlink(missing_ok=True)

    url = f"https://codeload.github.com/{repo}/tar.gz/{ref}"
    req = urllib.request.Request(url, headers={"User-Agent": "kanler-gems/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            with tarfile.open(fileobj=resp, mode="r|gz") as tf:
                for member in tf:
                    parts = member.name.split("/", 1)
                    if len(parts) == 2 and parts[1] == remote_path and member.isfile():
                        src_f = tf.extractfile(member)
                        if src_f is not None:
                            with tmp.open("wb") as out:
                                while True:
                                    buf = src_f.read(1 << 20)
                                    if not buf:
                                        break
                                    out.write(buf)
                            tmp.replace(dst)
                            return
    except Exception:
        tmp.unlink(missing_ok=True)

    with tmp.open("wb") as out:
        subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{remote_path}?ref={ref}", "-H", "Accept: application/vnd.github.raw"],
            check=True,
            stdout=out,
        )
    tmp.replace(dst)


def representation_class(
    their_dots: int,
    footprint_cells: int,
    limit: float = DENSE_SUPPORT_FRACTION,
    halo_fraction: float | None = None,
    halo_limit: float = HALO_SATURATION_FRACTION,
) -> dict:
    if footprint_cells <= 0:
        raise ValueError("footprint_cells must be positive")
    fraction = float(their_dots) / float(footprint_cells)
    if fraction > limit:
        kind = "continuous_surface"
    elif halo_fraction is not None and float(halo_fraction) >= halo_limit:
        kind = "halo_saturated_probe"
    else:
        kind = "dot_field"
    return dict(
        kind=kind,
        support_fraction=fraction,
        limit=float(limit),
        halo_fraction=halo_fraction,
        halo_limit=float(halo_limit),
    )


def two_phase_summary(
    rows,
    footprint_cells: int,
    *,
    rho_limit: float = RHO_LIMIT,
    overlap_limit: float = OVERLAP_LIMIT,
    jaccard_limit: float = JACCARD_LIMIT,
    expected_rasters: int | None = None,
) -> dict:
    checked = [dict(r) for r in rows if "error" not in r]
    if not checked:
        raise ValueError("no checked registry rows to summarise")
    for r in checked:
        r.setdefault(
            "representation",
            representation_class(
                int(r.get("their_dots", 0)),
                footprint_cells,
                halo_fraction=r.get("their_3px_halo_fraction"),
            )["kind"],
        )

    def _worst(subset, key):
        vals = [r[key] for r in subset if r.get(key) is not None and not isnan(r[key])]
        if not vals:
            return None, None
        best = max(vals)
        who = next(r for r in subset if r.get(key) == best)
        return float(best), who

    def _worst_abs_rho(subset):
        valid = [r for r in subset if r.get("spearman_full_footprint") is not None and not isnan(r["spearman_full_footprint"])]
        if not valid:
            return None, None
        who = max(valid, key=lambda r: abs(r["spearman_full_footprint"]))
        return float(abs(who["spearman_full_footprint"])), who

    rho_lit, rho_who = _worst_abs_rho(checked)
    ov_lit, ov_who = _worst(checked, "my_dots_within_3px_of_theirs")
    dot_rows = [r for r in checked if r["representation"] == "dot_field"]
    surf_rows = [r for r in checked if r["representation"] == "continuous_surface"]
    probe_rows = [r for r in checked if r["representation"] == "halo_saturated_probe"]
    ov_dot, ov_dot_who = _worst(dot_rows, "my_dots_within_3px_of_theirs")
    ov_rev, ov_rev_who = _worst(checked, "their_dots_within_3px_of_mine")
    jac, jac_who = _worst(checked, "jaccard_dot_sets")
    literal_firings = [
        dict(
            submission=r.get("submission"),
            repo=r.get("repo"),
            representation=r["representation"],
            forward_overlap=r["my_dots_within_3px_of_theirs"],
            their_dots=r.get("their_dots"),
            their_3px_halo_fraction=r.get("their_3px_halo_fraction"),
        )
        for r in checked
        if r["my_dots_within_3px_of_theirs"] > overlap_limit
    ]
    like_firings = [f for f in literal_firings if f["representation"] == "dot_field"]
    literal_rho_firings = [
        r.get("submission")
        for r in checked
        if r.get("spearman_full_footprint") is not None and abs(r["spearman_full_footprint"]) > rho_limit
    ]
    return dict(
        evidence_class="REGISTRY-MEASUREMENT",
        rasters_checked=len(checked),
        rasters_expected=expected_rasters,
        footprint_cells=int(footprint_cells),
        dense_support_fraction=DENSE_SUPPORT_FRACTION,
        halo_saturation_fraction=HALO_SATURATION_FRACTION,
        thresholds=dict(rho=rho_limit, forward_overlap=overlap_limit, jaccard=jaccard_limit),
        literal_reading=dict(
            worst_spearman_full_footprint=rho_lit,
            worst_spearman_submission=(rho_who or {}).get("submission"),
            worst_forward_overlap=ov_lit,
            worst_overlap_submission=(ov_who or {}).get("submission"),
            forward_overlap_firings=len(literal_firings),
            rho_firings=len(literal_rho_firings),
            duplicate=bool(literal_firings or literal_rho_firings),
        ),
        like_for_like_reading=dict(
            dot_field_rasters=len(dot_rows),
            continuous_surface_rasters=len(surf_rows),
            halo_saturated_probe_rasters=len(probe_rows),
            worst_forward_overlap_dot_fields=ov_dot,
            worst_forward_overlap_dot_field_submission=(ov_dot_who or {}).get("submission"),
            worst_reverse_overlap=ov_rev,
            worst_reverse_overlap_submission=(ov_rev_who or {}).get("submission"),
            worst_jaccard=jac,
            worst_jaccard_submission=(jac_who or {}).get("submission"),
            forward_overlap_firings=len(like_firings),
            duplicate=bool(like_firings or literal_rho_firings),
        ),
        literal_firings=literal_firings,
    )

#!/usr/bin/env python3
"""Inspect saved GeoTIFF bytes with the unchanged shared local format gates.

PASS means only the shared all-finite local policy passed; it does not imply
uniqueness, organizer acceptance, holdout success, or slot approval. This tool
never normalizes, clips, changes nodata, or writes a TIFF.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import rasterio
from restore_workspace import DEFAULT_CACHE, restore


def run(candidate: Path, sample: Path, cache: Path) -> dict:
    restore(cache, fetch=False, features=False, anchors=False)
    sys.path.insert(0, str(cache / 'template/src'))
    from gems57.gates import format_report
    from gems57.validate import validate
    from validate_submission import validate as validate_reference_mask
    with rasterio.open(sample) as ref:
        values = ref.read(1)
        footprint = np.isfinite(values) & (ref.read_masks(1) > 0)
        grid = (ref.shape, ref.crs, ref.transform)
    with rasterio.open(cache / 'data/existing_faults.tif') as labels:
        if (labels.shape, labels.crs, labels.transform) != grid:
            raise ValueError('reference and mirrored catalogue grids differ')
        catalogue = (labels.read(1) > 0) & footprint
    fmt = format_report(candidate, sample, footprint=footprint)
    try:
        # Known-fault pixels are masked by the organizer, not forbidden by the
        # format. The shared validator's optional catalogue-zero check is a
        # stricter placement policy, so do not mislabel it as a format rule.
        detailed = validate(candidate, footprint, catalogue=None)
        with rasterio.open(candidate) as src:
            pixels = src.read(1)
            candidate_mask = src.read_masks(1)
        known_positive = int(((pixels > 0) & catalogue).sum())
        masked_inside = int((candidate_mask[footprint] == 0).sum())
    except ValueError as exc:
        # Preserve the shared format report, including shape errors, rather
        # than losing the useful diagnosis when its optional mask check fails.
        detailed = {'all_checks_passed': False, 'error': str(exc)}
        known_positive = None
        masked_inside = None
    # A nodata tag such as 0 can mask valid cells while the raw pixel values
    # remain in [0,1]. Reject missing cells inside the footprint independently.
    allfinite_ok = bool(fmt['ok'] and detailed['all_checks_passed'] and masked_inside == 0)
    reference_mask = validate_reference_mask(sample, candidate)
    reference_mask_ok = bool(reference_mask['ok'])
    # The shared policy requires a finite zero exterior, while the independent
    # reference-mask policy requires a null exterior. Do not silently select a
    # winner when they disagree; upstream/organizer clarification is required.
    local_ok = allfinite_ok and reference_mask_ok
    return {'schema': 'gems-format-inspection-v2', 'local_format_ok': local_ok,
            'shared_all_finite_policy_ok': allfinite_ok,
            'reference_footprint_null_policy_ok': reference_mask_ok,
            'policies_disagree': allfinite_ok != reference_mask_ok,
            'reference_mask_report': reference_mask,
            'report': fmt, 'detailed': detailed, 'masked_inside_footprint': masked_inside,
            'positive_known_fault_pixels_informational': known_positive,
            'submit_approved': False,
            'reference_origin': ('public mirror; not independently organizer-authenticated' if sample.resolve() == (cache / 'data/sample_submission.tif').resolve() else 'caller-supplied; not authenticated by this tool'),
            'note': 'Official text says outside the bounds is null or NaN. Whether that means the sample footprint inside its rectangular bounds requires clarification. The shared all-finite and reference-mask policies can disagree; neither is an organizer receipt or slot/uniqueness decision.'}


def json_safe(value):
    """Preserve a JSON diagnosis even when a TIFF declares NaN/inf nodata."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return str(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--cache', type=Path, default=DEFAULT_CACHE)
    parser.add_argument('--sample', type=Path, help='Reference sample; defaults to unverified public mirror')
    parser.add_argument('--output', type=Path)
    a = parser.parse_args()
    try:
        report = run(a.candidate, a.sample or a.cache / 'data/sample_submission.tif', a.cache)
        text = json.dumps(json_safe(report), indent=2, allow_nan=False) + '\n'
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(text, encoding='utf-8')
        print(text, end='')
        return 0 if report['local_format_ok'] else 2
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        print(f'FORMAT INSPECTION FAILED CLOSED: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())

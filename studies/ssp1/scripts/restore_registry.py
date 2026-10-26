#!/usr/bin/env python3
"""Restore immutable registry bytes, without changing pins, reports, or predictions.

Uses the exact commit/path + git-blob + SHA-256 recorded in the frozen manifest.
A restore receipt is scratch evidence, not a new experiment or a registry refresh.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
from pathlib import Path
from cache_all_registry import fetch_one
from cache_registry import ROOT


def validate_manifest(manifest: dict, pins: dict) -> dict:
    if manifest.get('n_failed') != 0:
        raise ValueError('Frozen manifest has missing files; cannot certify an incomplete restore')
    unique = {}
    for row in manifest['rasters']:
        if row.get('status') != 'ok' or row.get('commit') != pins[row['site']]['commit']:
            raise ValueError('Snapshot row does not match the frozen commit pins')
        if not row.get('sha256') or not row.get('git_blob_sha'):
            raise ValueError('Missing recorded byte identity')
        key = row['git_blob_sha']
        if key in unique and unique[key]['sha256'] != row['sha256']:
            raise ValueError('One git blob has inconsistent SHA-256 records')
        unique[key] = row
    if len(manifest['rasters']) != manifest['n_files'] or len(unique) != manifest['n_unique_blobs']:
        raise ValueError('Frozen manifest counts are inconsistent')
    return unique


def main():
    source = ROOT/'registry/all_rasters.json'
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest = json.loads(source.read_text())
    pins = json.loads((ROOT/'registry/all_listed_site_pins.json').read_text())
    unique = validate_manifest(manifest, pins)
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i, (blob, receipt) in enumerate(pool.map(fetch_one, unique.values()), 1):
            row = unique[blob]
            if receipt.get('status') != 'ok' or receipt.get('sha256') != row['sha256']:
                failures.append({'blob': blob, 'receipt': receipt})
            if i % 100 == 0:
                print(f'{i}/{len(unique)} frozen blobs checked', flush=True)
    if hashlib.sha256(source.read_bytes()).hexdigest() != original_hash:
        raise RuntimeError('Restore must not modify the frozen manifest')
    out = {'n_unique_blobs': len(unique), 'n_failures': len(failures), 'failures': failures,
           'manifest_sha256': original_hash, 'does_not_change_predictions_or_submit': True}
    dest = ROOT/'.cache/audit/registry_restore_receipt.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k != 'failures'}, indent=2))
    if failures:
        raise SystemExit('Registry restore incomplete; no universal certification')


if __name__ == '__main__':
    main()

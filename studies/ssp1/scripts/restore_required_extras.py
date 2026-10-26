#!/usr/bin/env python3
"""Restore only the three small pinned external derivatives used by SSP1/evaluation."""
import json
from restore_data import ROOT,restore_entry,data_dir
if __name__=='__main__':
    ids={'ext_lidar_scarp_features_u8','ext_geodawn_rad_u8','ext_derived_sgmc_faults_100m_u8'}
    manifest=json.loads((ROOT/'registry/data_manifest.json').read_text())
    receipts=[restore_entry(e,data_dir())for e in manifest['files']if e['id']in ids]
    if len(receipts)!=len(ids):raise SystemExit('Missing required pinned source')
    out=ROOT/'evidence/extra_data_restore.json'
    out.write_text(json.dumps(receipts,indent=2)+'\n')
    print(out)

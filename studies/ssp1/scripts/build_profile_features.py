#!/usr/bin/env python3
"""Build SSP1 derived channels once, reusing the canonical shared cache."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from kanler.science import build_profile_features
from gems32.paths import data_dir,work_dir
if __name__=='__main__':
    receipt=build_profile_features(work_dir()/'feature_stack.npy',data_dir(),work_dir()/'ssp1_features.npy',ROOT/'evidence/ssp1_feature_receipt.json')
    print(receipt,flush=True)

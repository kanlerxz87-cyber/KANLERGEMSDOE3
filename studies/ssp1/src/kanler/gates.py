"""Fail-closed promotion policy; format validity is necessary, never sufficient."""
from __future__ import annotations
from numbers import Integral

REQUIRED = (
    'declared_lane','leakage_canaries','surface_unique','final_dots_unique',
    'registry_snapshot_complete','saved_bytes_valid','current_best_reproduced',
    'paired_holdout_improvement','weekly_selector_approved'
)


def promotion(gates: dict) -> dict:
    failed=[key for key in REQUIRED if gates.get(key) is not True]
    return {'verdict':'promote' if not failed else 'negative','ok_to_download':True,
            'ok_to_submit':not failed,'failed_or_unknown_gates':failed,
            'gates':{key:gates.get(key) for key in REQUIRED},'slot_used':False,
            'policy':'All gates must be literally true. A missing receipt, unknown slot capacity, or a format-only PASS never authorizes submission.'}


def score_record(result: dict) -> dict:
    required=('evaluator_version','n_withheld_positives','pooled_dti','ci95_cluster_bootstrap')
    if any(k not in result for k in required):
        raise ValueError('A HOLDOUT-DTI record requires evaluator, positive count, value and 95% CI')
    if not isinstance(result['evaluator_version'],str)or not result['evaluator_version'].strip():
        raise ValueError('Missing evaluator version')
    count=result['n_withheld_positives']
    if isinstance(count,bool)or not isinstance(count,Integral)or count<=0:
        raise ValueError('Withheld positives must be a positive integer count')
    if isinstance(result['pooled_dti'],bool):
        raise ValueError('A boolean is not a DTI value')
    value=float(result['pooled_dti']);lo,hi=map(float,result['ci95_cluster_bootstrap'])
    if not (0<=lo<=hi<=1 and 0<=value<=1) or int(result['n_withheld_positives'])<=0:
        raise ValueError('Invalid HOLDOUT-DTI record')
    return {'label':'HOLDOUT-DTI',**{k:result[k] for k in required},'leaderboard_estimate':None,
            'caveat':'Local hide-and-recover estimate, not the hidden public/private leaderboard score.'}

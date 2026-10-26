"""Decision-only gate. Does not replace shared geological evaluator/writer.

Evidence must be produced by trusted, pinned runners, not hand-entered claims.
This schema check alone neither authenticates evidence nor allocates a slot.
"""
import json
import math
import re
import sys


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def assess(card):
    failures = []
    if not isinstance(card, dict):
        return {'verdict': 'negative', 'schema_status': 'incomplete', 'failures': ['run card must be an object'], 'promotion_evaluated': False, 'slot_authorized': False}
    required_true = [
        'lane_recorded', 'shared_template_pinned', 'whole_segment_buffered_holdout',
        'visible_only_features', 'pixel_exact_visible_mask', 'all_features_canary_tested',
        'same_evaluator_incumbent', 'registry_complete', 'surface_checked_before_placement',
        'final_dots_checked', 'saved_bytes_validated', 'template_provenance_verified',
    ]
    for field in required_true:
        if card.get(field) is not True:
            failures.append(field)
    # The stated stop is rho > .90, not abs(rho) > .90. A strong negative
    # correlation is not the same-direction duplicate specified by the user.
    for field in ('surface_max_rank_correlation', 'final_max_rank_correlation'):
        v=card.get(field)
        if not finite(v) or not -1 <= v <= .90:
            failures.append(field)
    for field in ('surface_dot_overlap_3px', 'final_dot_overlap_3px'):
        v=card.get(field)
        if not finite(v) or not 0 <= v <= .70:
            failures.append(field)
    auc=card.get('max_feature_auc')
    if not finite(auc) or not 0 <= auc <= .90:
        failures.append('leakage_canary')
    ci=card.get('paired_improvement_ci95')
    if not isinstance(ci,list) or len(ci)!=2 or not all(finite(x) for x in ci) or not 0 < ci[0] <= ci[1] <= 1:
        failures.append('paired_holdout_improvement')
    metric=card.get('holdout',{})
    if not isinstance(metric,dict):metric={}
    version = metric.get('evaluator_version')
    if metric.get('class')!='HOLDOUT-DTI' or not isinstance(version, str) or not version.strip():
        failures.append('holdout_identity')
    n=metric.get('withheld_positives')
    if type(n) is not int or n <= 0:failures.append('withheld_positives')
    score=metric.get('value'); ci=metric.get('ci95')
    if not finite(score) or not 0 <= score <= 1:failures.append('holdout_value')
    if not isinstance(ci,list) or len(ci)!=2 or not all(finite(x) for x in ci) or not 0<=ci[0]<=ci[1]<=1 or (finite(score) and not ci[0]<=score<=ci[1]):failures.append('holdout_ci95')
    if (metric.get('alpha'),metric.get('beta'),metric.get('kernel_m')) != (.2,.8,300) or metric.get('kernel')!='triangular' or metric.get('aggregation')!='pooled':
        failures.append('metric_definition')
    v=card.get('validator',{})
    if not isinstance(v,dict):v={}
    for field in ('single_band','no_nan_inside_footprint','values_0_1_inside_footprint',
                  'crs_match','shape_match','transform_match'):
        if v.get(field) is not True:failures.append('validator.'+field)
    sha=card.get('raster_sha256')
    if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):failures.append('raster_sha256')
    for field in ('hypothesis','mechanism','non_fault_mimic','submission_name'):
        if not isinstance(card.get(field),str) or not card[field].strip():failures.append(field)
    note=card.get('submission_note')
    if not isinstance(note,str) or not 0<len(note)<=140:failures.append('submission_note')
    # Booleans in a card are not authenticated evidence. Even a complete schema
    # can never issue a research promotion or authorize a weekly slot by itself.
    return {'verdict':'negative',
            'schema_status':'incomplete' if failures else 'complete',
            'failures':failures,
            'promotion_evaluated':False,
            'slot_authorized':False}

if __name__=='__main__':
    result=assess(json.load(open(sys.argv[1])))
    print(json.dumps(result,indent=2))
    sys.exit(bool(result['failures']))

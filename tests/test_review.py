import copy
import json
import unittest
from pathlib import Path
from scripts.promotion_gate import assess
from scripts.review import build


def fixture():
    from scripts.promotion_gate import REQUIRED_TRUE, VALIDATOR_CHECKS
    card={k:True for k in REQUIRED_TRUE}
    card.update(surface_max_rank_correlation=.9,final_max_rank_correlation=.9,surface_dot_overlap_3px=.7,final_dot_overlap_3px=.7,max_feature_auc=.9,paired_improvement_ci95=[.001,.01],holdout={'class':'HOLDOUT-DTI','evaluator_version':'TEST ONLY','withheld_positives':10,'value':.2,'ci95':[.1,.3],'alpha':.2,'beta':.8,'kernel_m':300,'kernel':'triangular','aggregation':'pooled'},validator={k:True for k in VALIDATOR_CHECKS},raster_sha256='a'*64,hypothesis='synthetic',mechanism='test',non_fault_mimic='test',submission_name='test',submission_note='test')
    return card

class ReviewTests(unittest.TestCase):
    def test_missing_blocks(self):
        self.assertEqual(assess({})['verdict'],'negative')
    def test_boundaries_and_selector(self):
        self.assertEqual(assess(fixture())['verdict'],'promote')
        self.assertFalse(assess(fixture())['slot_authorized'])
    def test_malformed(self):
        for x in [None,[],42]:self.assertEqual(assess(x)['verdict'],'negative')
        for key in ['holdout','validator']:
            c=fixture();c[key]=None;self.assertEqual(assess(c)['verdict'],'negative')
    def test_every_gate_required(self):
        for key in fixture():
            c=fixture();del c[key];self.assertEqual(assess(c)['verdict'],'negative',key)
    def test_nonfinite_and_threshold(self):
        for key in ['surface_max_rank_correlation','final_max_rank_correlation','surface_dot_overlap_3px','final_dot_overlap_3px','max_feature_auc']:
            for bad in [float('nan'),float('inf'),True,1.01,-1.01]:
                c=fixture();c[key]=bad;self.assertEqual(assess(c)['verdict'],'negative')
    def test_no_improvement(self):
        for ci in ([0,.1],[-.1,.2],[.01,1.01],[.5,.1]):
            c=fixture();c['paired_improvement_ci95']=ci;self.assertEqual(assess(c)['verdict'],'negative')
    def test_signed_correlation_and_literal_boundaries(self):
        c=fixture();c['surface_max_rank_correlation']=-.95;c['final_max_rank_correlation']=-.99
        self.assertEqual(assess(c)['verdict'],'promote')
        for key,value in [('surface_max_rank_correlation',.90001),('final_dot_overlap_3px',.70001),('max_feature_auc',.90001)]:
            c=fixture();c[key]=value;self.assertEqual(assess(c)['verdict'],'negative')
    def test_identity_and_note_controls(self):
        for field,value in [('submission_name','../bad'),('submission_note','  '),('submission_note','hello\nworld')]:
            c=fixture();c[field]=value;self.assertEqual(assess(c)['verdict'],'negative')
        c=fixture();c['holdout']['evaluator_version']=True
        self.assertEqual(assess(c)['verdict'],'negative')
    def test_note(self):
        c=fixture();c['submission_note']='x'*141;self.assertEqual(assess(c)['verdict'],'negative')
    def test_rebuild(self):
        build();rows=json.loads(Path('docs/data/sites.json').read_text())
        self.assertEqual(len(rows),9)
        self.assertTrue(all(not x['submit'] and x['estimate'] is None for x in rows))
    def test_evidence_hashes(self):
        import hashlib
        for row in json.loads(Path('evidence/snapshot_hashes.json').read_text()):
            self.assertEqual(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest(),row['sha256'])

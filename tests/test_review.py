import copy
import json
import unittest
from pathlib import Path
from scripts.promotion_gate import assess
from scripts.review import build


def fixture():
    from scripts.promotion_gate import assess
    card={k:True for k in ['lane_recorded','shared_template_pinned','whole_segment_buffered_holdout','visible_only_features','pixel_exact_visible_mask','all_features_canary_tested','same_evaluator_incumbent','registry_complete','surface_checked_before_placement','final_dots_checked','saved_bytes_validated','template_provenance_verified']}
    card.update(surface_max_rank_correlation=.9,final_max_rank_correlation=.9,surface_dot_overlap_3px=.7,final_dot_overlap_3px=.7,max_feature_auc=.9,paired_improvement_ci95=[.001,.01],holdout={'class':'HOLDOUT-DTI','evaluator_version':'TEST ONLY','withheld_positives':10,'value':.2,'ci95':[.1,.3],'alpha':.2,'beta':.8,'kernel_m':300,'kernel':'triangular','aggregation':'pooled'},validator={k:True for k in ['single_band','all_finite','range_0_1','crs_match','shape_match','transform_match']},raster_sha256='a'*64,hypothesis='synthetic',mechanism='test',non_fault_mimic='test',submission_name='test',submission_note='test')
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
            for bad in [float('nan'),float('inf'),True,1.01,-.91]:
                c=fixture();c[key]=bad;self.assertEqual(assess(c)['verdict'],'negative')
    def test_no_improvement(self):
        c=fixture();c['paired_improvement_ci95']=[0,.1];self.assertEqual(assess(c)['verdict'],'negative')
    def test_note(self):
        c=fixture();c['submission_note']='x'*141;self.assertEqual(assess(c)['verdict'],'negative')
    def test_rebuild(self):
        build();rows=json.loads(Path('docs/data/sites.json').read_text())
        self.assertEqual(len(rows),9)
        self.assertTrue(all(not x['submit'] and x['estimate'] is None for x in rows))
        page=Path('docs/archived-research.html').read_text()
        self.assertIn('<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">',page)
        self.assertNotIn('<a href="<a href=',page)
    def test_evidence_hashes(self):
        import hashlib
        for row in json.loads(Path('evidence/snapshot_hashes.json').read_text()):
            self.assertNotIn('__pycache__', Path(row['path']).parts)
            self.assertNotEqual(Path(row['path']).suffix, '.pyc')
            self.assertEqual(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest(),row['sha256'])

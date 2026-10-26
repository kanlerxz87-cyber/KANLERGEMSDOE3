import copy
import json
import unittest
from pathlib import Path
from scripts.promotion_gate import assess
from scripts.review import build


def fixture():
    """Synthetic structurally complete card; not a real evidence receipt."""
    sha='a'*64; surface='b'*64; manifest='c'*64; folds='d'*64
    def registry(phase, artifact):
        return {'phase':phase, 'complete_applicable_registry':True, 'complete_accessible_scan':True,
                'registry_rasters_expected':2, 'registry_rasters_checked':2, 'missing_or_invalid':0,
                'source_errors':[], 'duplicate_count':0, 'candidate_positive_pixels':1,
                'worst_spearman_full_footprint':.9, 'worst_dot_overlap':.7,
                'registry_manifest_sha256':manifest, 'artifact_sha256':artifact}
    return {'method_lane':'synthetic', 'shared_template_manifest_sha256':'e'*64, 'template_provenance_verified':True,
            'raster_sha256':sha, 'surface_sha256':surface, 'candidate_positive_pixels':1,
            'validator_output':{'sha256':sha, 'all_checks_passed':True},
            'features_used':['synthetic'], 'feature_canary':{'synthetic':.9},
            'surface_registry':registry('surface',surface), 'final_registry':registry('final',sha),
            'holdout':{'evidence_class':'HOLDOUT-DTI','evaluator_version':'TEST ONLY','withheld_positive_pixels':10,
                       'whole_segment_buffered':True,'catalogue_features_visible_only':True,
                       'visible_faults_masked_pixel_exact':True,'alpha':.2,'beta':.8,'kernel_m':300,
                       'kernel':'triangular','aggregation':'pooled','folds_sha256':folds,
                       'dti':.3,'ci95':[.25,.35], 'paired_delta_ci95':[.01,.15],
                       'baseline':{'evidence_class':'HOLDOUT-DTI','evaluator_version':'TEST ONLY',
                                   'withheld_positive_pixels':10,'folds_sha256':folds,
                                   'verified_current_best':True,'dti':.2,'ci95':[.15,.25]}},
            'experiment_count':1,'elapsed_minutes':10,'submission_name':'synthetic','submission_note':'test'}


class ReviewTests(unittest.TestCase):
    def test_missing_blocks(self):
        for value in [{},None,[],42]:
            self.assertEqual(assess(value)['verdict'],'negative')
    def test_boundaries_and_selector(self):
        result=assess(fixture())
        self.assertEqual(result['verdict'],'promote',result)
        self.assertFalse(result['slot_authorized'])
        self.assertFalse(result['ok_to_submit'])
    def test_every_top_level_gate_required(self):
        for key in fixture():
            c=fixture();del c[key]
            self.assertEqual(assess(c)['verdict'],'negative',key)
    def test_nonfinite_and_threshold(self):
        for phase in ['surface_registry','final_registry']:
            for key, bads in [('worst_spearman_full_footprint',[float('nan'),float('inf'),True,.90001]),
                              ('worst_dot_overlap',[float('nan'),float('inf'),True,.70001,-.1])]:
                for bad in bads:
                    c=fixture();c[phase][key]=bad
                    self.assertEqual(assess(c)['verdict'],'negative',(phase,key,bad))
        for bad in [float('nan'),float('inf'),True,.9001,.49]:
            c=fixture();c['feature_canary']['synthetic']=bad
            self.assertEqual(assess(c)['verdict'],'negative',bad)
    def test_no_improvement_and_matched_folds(self):
        for field,bad in [('paired_delta_ci95',[0,.1]),('folds_sha256','f'*64),
                          ('verified_current_best',False),('withheld_positive_pixels',11)]:
            c=fixture()
            if field=='paired_delta_ci95':c['holdout'][field]=bad
            else:c['holdout']['baseline'][field]=bad
            self.assertEqual(assess(c)['verdict'],'negative',field)
    def test_holdout_protocol_and_metric(self):
        for field in ['whole_segment_buffered','catalogue_features_visible_only','visible_faults_masked_pixel_exact']:
            c=fixture();c['holdout'][field]=False
            self.assertEqual(assess(c)['verdict'],'negative',field)
        c=fixture();c['holdout']['kernel_m']=301
        self.assertEqual(assess(c)['verdict'],'negative')
    def test_registry_identity_hashes_empty_and_budget(self):
        c=fixture();c['final_registry']['registry_manifest_sha256']='f'*64
        self.assertEqual(assess(c)['verdict'],'negative')
        c=fixture();c['validator_output']['sha256']='f'*64
        self.assertEqual(assess(c)['verdict'],'negative')
        c=fixture();c['candidate_positive_pixels']=0
        self.assertEqual(assess(c)['verdict'],'negative')
        for field in ['missing_or_invalid','duplicate_count']:
            c=fixture();c['final_registry'][field]=False
            self.assertEqual(assess(c)['verdict'],'negative',field)
        c=fixture();c['final_registry']['candidate_positive_pixels']=2
        self.assertEqual(assess(c)['verdict'],'negative')
        for field,value in [('experiment_count',4),('elapsed_minutes',121)]:
            c=fixture();c[field]=value
            self.assertEqual(assess(c)['verdict'],'negative',field)
    def test_note_and_canary_coverage(self):
        c=fixture();c['submission_note']='x'*141;self.assertEqual(assess(c)['verdict'],'negative')
        c=fixture();c['features_used'].append('untested');self.assertEqual(assess(c)['verdict'],'negative')
    def test_rebuild(self):
        build();rows=json.loads(Path('docs/data/sites.json').read_text())
        self.assertEqual(len(rows),9)
        self.assertTrue(all(not x['submit'] and x['estimate'] is None for x in rows))
        page=Path('docs/research.html').read_text()
        self.assertIn('<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">',page)
        self.assertNotIn('<a href="<a href=',page)
    def test_evidence_hashes(self):
        import hashlib
        for row in json.loads(Path('evidence/snapshot_hashes.json').read_text()):
            self.assertEqual(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest(),row['sha256'])

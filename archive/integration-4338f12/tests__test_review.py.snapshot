import json
import unittest
from pathlib import Path
from scripts.promotion_gate import assess
from scripts.review import build, verify_snapshots


def fixture():
    card = {k: True for k in [
        'lane_recorded', 'shared_template_pinned', 'whole_segment_buffered_holdout',
        'visible_only_features', 'pixel_exact_visible_mask', 'all_features_canary_tested',
        'same_evaluator_incumbent', 'registry_complete', 'surface_checked_before_placement',
        'final_dots_checked', 'saved_bytes_validated', 'template_provenance_verified']}
    card.update(
        surface_max_rank_correlation=.9, final_max_rank_correlation=.9,
        surface_dot_overlap_3px=.7, final_dot_overlap_3px=.7, max_feature_auc=.9,
        paired_improvement_ci95=[.001, .01],
        holdout={'class': 'HOLDOUT-DTI', 'evaluator_version': 'SYNTHETIC TEST ONLY',
                 'withheld_positives': 10, 'value': .2, 'ci95': [.1, .3],
                 'alpha': .2, 'beta': .8, 'kernel_m': 300,
                 'kernel': 'triangular', 'aggregation': 'pooled'},
        validator={k: True for k in ['single_band', 'no_nan_inside_footprint',
                   'values_0_1_inside_footprint', 'crs_match', 'shape_match', 'transform_match']},
        raster_sha256='a'*64, hypothesis='synthetic', mechanism='test',
        non_fault_mimic='test', submission_name='test', submission_note='test')
    return card


class ReviewTests(unittest.TestCase):
    def test_missing_blocks(self):
        self.assertEqual(assess({})['schema_status'], 'incomplete')

    def test_complete_schema_is_not_a_promotion_or_selector(self):
        r = assess(fixture())
        self.assertEqual(r['schema_status'], 'complete')
        self.assertEqual(r['verdict'], 'negative')
        self.assertFalse(r['promotion_evaluated'])
        self.assertFalse(r['slot_authorized'])

    def test_malformed(self):
        for value in [None, [], 42]:
            self.assertEqual(assess(value)['schema_status'], 'incomplete')
        for key in ['holdout', 'validator']:
            card = fixture(); card[key] = None
            self.assertEqual(assess(card)['schema_status'], 'incomplete')

    def test_every_gate_required(self):
        for key in fixture():
            card = fixture(); del card[key]
            self.assertEqual(assess(card)['schema_status'], 'incomplete', key)

    def test_nonfinite_and_threshold(self):
        fields = ['surface_max_rank_correlation', 'final_max_rank_correlation',
                  'surface_dot_overlap_3px', 'final_dot_overlap_3px', 'max_feature_auc']
        for key in fields:
            for bad in [float('nan'), float('inf'), True, 1.01, -1.01]:
                card = fixture(); card[key] = bad
                self.assertEqual(assess(card)['schema_status'], 'incomplete', (key, bad))
        for key in fields:
            card = fixture(); card[key] = .70001 if 'overlap' in key else .90001
            self.assertEqual(assess(card)['schema_status'], 'incomplete', key)

    def test_negative_correlation_is_not_the_positive_duplicate_stop(self):
        card = fixture()
        card['surface_max_rank_correlation'] = -.95
        card['final_max_rank_correlation'] = -1.0
        self.assertEqual(assess(card)['schema_status'], 'complete')
        self.assertEqual(assess(card)['verdict'], 'negative')  # schema is not evidence

    def test_no_improvement(self):
        for ci in ([0, .1], [.01, 1.01], [True, .1]):
            card = fixture(); card['paired_improvement_ci95'] = ci
            self.assertEqual(assess(card)['schema_status'], 'incomplete')

    def test_note_and_evaluator_identity(self):
        card = fixture(); card['submission_note'] = 'x'*141
        self.assertEqual(assess(card)['schema_status'], 'incomplete')
        for bad in [True, 7, ' ', None]:
            card = fixture(); card['holdout']['evaluator_version'] = bad
            self.assertEqual(assess(card)['schema_status'], 'incomplete')

    def test_rebuild(self):
        build()
        rows = json.loads(Path('docs/data/sites.json').read_text())
        self.assertEqual(len(rows), 9)
        self.assertTrue(all(not x['submit'] and x['estimate'] is None for x in rows))
        page = Path('docs/archived-research.html').read_text()
        self.assertIn('<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">', page)
        self.assertNotIn('<a href="<a href=', page)

    def test_evidence_hashes(self):
        verify_snapshots()

    def test_snapshot_is_not_rewritten_by_build(self):
        path = Path('evidence/snapshot_hashes.json')
        before = path.read_bytes()
        build()
        self.assertEqual(before, path.read_bytes())


if __name__ == '__main__':
    unittest.main()

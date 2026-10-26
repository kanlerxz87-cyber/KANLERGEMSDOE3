import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

import numpy as np
from scipy.stats import spearmanr

from scripts.audit_evidence import binary_spearman
from scripts.audit_rasters import overlap
from scripts.build_site import build
from scripts.check_submission import json_safe, inspect
from scripts.restore_assets import fetch
from gems_audit.assets import verify, load_template

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.ids=set(); self.language=None; self.has_main=False
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='html': self.language=attrs.get('lang')
        if tag=='main': self.has_main=True
        if 'id' in attrs: self.ids.add(attrs['id'])
        if tag in ('a','link') and attrs.get('href'): self.links.append(attrs['href'])


class RegistryAuditTests(unittest.TestCase):
    def test_exact_binary_spearman_with_ties(self):
        a=np.array([0,0,1,1,0,1,0,0],bool)
        b=np.array([0,1,1,0,0,1,0,0],bool)
        self.assertAlmostEqual(binary_spearman(a,b,a.size),float(spearmanr(a,b).statistic),places=14)
        self.assertEqual(binary_spearman(a,a,a.size),1.)
        self.assertIsNone(binary_spearman(a,np.zeros_like(a),a.size))
        self.assertIsNone(binary_spearman(a,np.ones_like(a),a.size))
    def test_bad_binary_counts_rejected(self):
        a=np.ones((3,3),bool)
        with self.assertRaisesRegex(ValueError,'counts exceed'):binary_spearman(a,a,8)
        with self.assertRaisesRegex(ValueError,'share a grid'):binary_spearman(a,a[:2],6)

    def test_full_witness_rejects_every_nonempty_dotset(self):
        witness=np.ones((17,19),bool)
        for cells in [[(0,0)],[(16,18)],[(1,1),(10,14),(9,1)]]:
            candidate=np.zeros_like(witness)
            for x,y in cells:candidate[x,y]=True
            self.assertEqual(overlap(candidate,witness),1.)
        with self.assertRaises(ValueError):overlap(np.zeros_like(witness),witness)
    def test_published_certificate_and_histories_are_internally_consistent(self):
        a=json.loads((ROOT/'evidence/audit.json').read_text()); old=json.loads((ROOT/'docs/audit.json').read_text())
        w=a['saturation_witness']; l=a['lattice']; grid=a['grid']
        self.assertTrue(w['universal_overlap_blocker']); self.assertEqual(w['positive_inside_footprint'],grid['footprint_pixels'])
        self.assertEqual(w['uncovered_allowed_pixels'],0)
        self.assertEqual(w['allowed_pixels'],grid['footprint_pixels']-grid['known_pixels'])
        self.assertEqual(l['footprint_within_3_pixels']+l['uncovered_footprint_pixels'],grid['footprint_pixels'])
        self.assertEqual(l['maximum_dots_to_allow_at_most_70_percent_overlap'],math.floor(l['uncovered_footprint_pixels']/.3))
        self.assertEqual(len(a['historical_files']),9);self.assertEqual(len(a['historic_pairwise_comparisons']),72)
        self.assertTrue(all(x['directed_overlap_within_3px']>.7 for x in a['historic_pairwise_comparisons']))
        for row in a['historical_files']:
            other=next(x for x in old['rows'] if x['repo']==row['site'])
            self.assertEqual(row['sha256'],other['sha256']);self.assertEqual(row['positive_pixels'],other['dots'])
        card=json.loads((ROOT/'evidence/run-card.json').read_text())
        self.assertIsNone(card['holdout_dti']);self.assertIsNone(card['raster_sha256']);self.assertIsNone(card['validator_output'])
        self.assertFalse(card['ok_to_submit']);self.assertEqual(card['verdict'],'negative')
        self.assertLessEqual(len(card['submission_note']),140)
    def test_manifest_pins_shared_code_and_inputs(self):
        pins=json.loads((ROOT/'registry/template_pins.json').read_text())
        for path in ['vendor/gems57/evaluate_holdout.py','vendor/gems57/submission_writer.py',
                     'vendor/gems57/uniqueness.py','vendor/gems57/validate.py']:
            self.assertRegex(pins['files'][path],r'^[0-9a-f]{64}$')
        data=json.loads((ROOT/'registry/data_pins.json').read_text())['files']
        self.assertTrue({'training_features','existing_faults','sample_submission','ext_geodawn_rad_u8'} <= {x['id'] for x in data})
        self.assertTrue(all(len(x['sha256'])==64 for x in data))
    def test_corrupt_asset_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'asset';p.write_bytes(b'correct')
            verify(p,hashlib.sha256(b'correct').hexdigest())
            p.write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):verify(p,hashlib.sha256(b'correct').hexdigest())
    def test_atomic_restore_preserves_old_file_on_hash_mismatch(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            destination=Path(d)/'asset';destination.write_bytes(b'old')
            def fake_run(*args,**kwargs):
                kwargs['stdout'].write(b'bad download')
            with patch('scripts.restore_assets.subprocess.run',side_effect=fake_run):
                with self.assertRaisesRegex(ValueError,'hash mismatch'):
                    fetch('owner/repo','ref','thing',destination,hashlib.sha256(b'expected').hexdigest())
            self.assertEqual(destination.read_bytes(),b'old')
            self.assertEqual(sorted(x.name for x in Path(d).iterdir()),['asset'])
    def test_json_nonfinite_is_strict_and_visible(self):
        value=json_safe({'n':float('nan'),'p':float('inf'),'m':float('-inf'),'n2':np.float32('nan')})
        self.assertEqual(value,{'n':'NaN','p':'Infinity','m':'-Infinity','n2':'NaN'})
        json.dumps(value,allow_nan=False)
    def test_pages_have_valid_local_links_and_accessible_landmarks(self):
        build()
        for path in [ROOT/'docs/index.html',ROOT/'docs/executive-summary.html',
                     ROOT/'docs/hypotheses.html',ROOT/'docs/review.html']:
            parser=Links();parser.feed(path.read_text())
            self.assertEqual(parser.language,'en');self.assertTrue(parser.has_main)
            for href in parser.links:
                parsed=urlsplit(href)
                if parsed.scheme or parsed.netloc:continue
                dest=(path.parent/unquote(parsed.path)).resolve() if parsed.path else path
                self.assertTrue(dest.is_file(),f'{path}: {href}')
                if parsed.fragment and dest.suffix=='.html':
                    other=Links();other.feed(dest.read_text())
                    self.assertIn(parsed.fragment,other.ids,f'{path}: {href}')
        self.assertIn('DO NOT SUBMIT',(ROOT/'docs/index.html').read_text())
        self.assertIn((ROOT/'PROJECT_REQUEST.md').read_text(),(ROOT/'README.md').read_text())

    @unittest.skipUnless((ROOT/'.cache/template/vendor/gems57/__init__.py').is_file(),
                         'optional integration: restore_assets.py first')
    def test_rejects_foreign_preloaded_template_submodule(self):
        fake=types.ModuleType('gems57.uniqueness');fake.__file__='/tmp/foreign/uniqueness.py'
        with patch.dict('sys.modules',{'gems57.uniqueness':fake}):
            with self.assertRaisesRegex(RuntimeError,'refusing private fork'):load_template()

    @unittest.skipUnless((ROOT/'.cache/template/vendor/gems57/metric.py').is_file(),
                         'optional integration: restore_assets.py first')
    def test_shared_metric_counterexample_is_documentation_only(self):
        load_template()
        from gems57.metric import dti_binary
        truth=np.zeros((7,7),bool);truth[3,3:5]=True
        empty=np.zeros_like(truth);dot=empty.copy();dot[3,3]=True
        delta=dti_binary(dot,truth)['tp']-dti_binary(empty,truth)['tp']
        self.assertAlmostEqual(delta,5/3)
        self.assertGreater(delta,1.)  # dot self-credit k=1; dT can exceed k

    @unittest.skipUnless((ROOT/'.cache/registry/focus/GEMSDOE32.tif').is_file(),
                         'optional integration: restore_assets.py --focus first')
    def test_real_b2_rejected_and_nan_file_returns_receipt(self):
        result=inspect(ROOT/'.cache/registry/focus/GEMSDOE32.tif')
        self.assertTrue(result['local_validator']['all_checks_passed'])
        self.assertEqual(result['final_check']['overlap_vs_witness'],1.)
        self.assertTrue(result['final_check']['duplicate']);self.assertFalse(result['ok_to_submit'])
        bad=inspect(ROOT/'.cache/registry/focus/GEMSDOE30.tif')
        self.assertFalse(bad['local_validator']['all_checks_passed'])
        self.assertEqual(json_safe(bad)['local_validator']['meta']['nodata'],'NaN')
        json.dumps(json_safe(bad),allow_nan=False)


if __name__=='__main__': unittest.main()

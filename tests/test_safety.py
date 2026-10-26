import hashlib
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from restore_shared_template import extract_pinned, verify_template
from validate_submission import validate


def archive(entries):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w:gz') as tar:
        for name, content in entries:
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    out.seek(0)
    return out


class RestoreTests(unittest.TestCase):
    def test_pinned_extraction_and_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'file'
            content = b'actual'
            spec = {'a/file': {'destination': target, 'sha256': hashlib.sha256(content).hexdigest()}}
            extract_pinned(archive([('repo-hash/a/file', content)]), spec)
            self.assertEqual(target.read_bytes(), content)
            target.write_bytes(b'original')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                extract_pinned(archive([('repo-hash/a/file', b'wrong')]), spec)
            self.assertEqual(target.read_bytes(), b'original')
            with self.assertRaisesRegex(ValueError, 'missing pinned'):
                extract_pinned(archive([('repo-hash/../a/file', content)]), spec)
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                extract_pinned(archive([('repo-hash/a/file', content), ('repo-hash/a/file', content)]), spec)
            with self.assertRaisesRegex(ValueError, 'size mismatch'):
                extract_pinned(archive([('repo-hash/a/file', content)]),
                               {'a/file': {**spec['a/file'], 'size': 99}})

    def test_pin_manifest_and_recorded_measurement(self):
        pins = json.loads((ROOT / 'registry/shared_template_pins.json').read_text())
        self.assertEqual(len(pins['expected_band_sha256']), 19)
        self.assertIn('src/gems57/evaluate_holdout.py', pins['files'])
        self.assertIn('src/gems57/submission_writer.py', pins['files'])
        self.assertTrue(all(len(v['sha256']) == 64 for v in pins['files'].values()))
        evidence = json.loads((ROOT / 'evidence/registry_saturation_20261026.json').read_text())
        self.assertTrue(evidence['measurement']['universal_overlap_blocker'])
        self.assertEqual(evidence['measurement']['uncovered_allowed_pixels'], 0)
        self.assertFalse(evidence['candidate_generated'])
        self.assertIn('continuous', evidence['scope_caveat'])

    def test_shared_metric_synthetic_counterexample_when_available(self):
        pins = json.loads((ROOT / 'registry/shared_template_pins.json').read_text())
        if not verify_template(pins):
            self.skipTest('shared template absent; restore with scripts/restore_shared_template.py')
        sys.path.insert(0, str(ROOT / '.cache/template57/src'))
        from gems57 import metric
        p = np.zeros((7, 7), np.float32); p[3, 3] = 1
        truth = np.zeros((7, 7), bool)
        truth[3, 2] = truth[3, 4] = truth[2, 3] = True
        result = metric.dti_exact(p, truth)
        brute = metric.dti_bruteforce(p, truth)
        for key in ('tp', 'fp', 'fn', 'dti'):
            self.assertAlmostEqual(result[key], brute[key], places=10)
        cover, near, _ = metric.max_cover(p, truth)
        # TP is a sum over truth cells; it can exceed one dot's maximum credit.
        self.assertGreater(float(cover.sum()), float(near[3, 3]))
        naive_denominator = .2 * float(p.sum()) + .8 * int(truth.sum())
        actual_denominator = result['tp'] + .2 * result['fp'] + .8 * result['fn']
        self.assertNotAlmostEqual(naive_denominator, actual_denominator)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ref = self.root / 'sample.tif'
        self.pred = self.root / 'candidate.tif'
        self.profile = dict(driver='GTiff', width=4, height=4, count=1, dtype='float32',
                            crs='EPSG:32611', transform=from_origin(0, 400, 100, 100))

    def write(self, path, data, **kw):
        with rasterio.open(path, 'w', **{**self.profile, **kw}) as ds:
            ds.write(data.astype('float32'), 1)

    def test_empty_template_is_not_a_format_pass(self):
        self.write(self.ref, np.full((4, 4), -9999), nodata=-9999)
        self.write(self.pred, np.zeros((4, 4)))
        r = validate(self.ref, self.pred)
        self.assertFalse(r['ok'])
        self.assertTrue(any('empty' in e for e in r['errors']))

    def test_infinity_outside_is_not_null(self):
        template = np.zeros((4, 4)); template[0, 0] = -9999
        self.write(self.ref, template, nodata=-9999)
        pred = np.zeros((4, 4)); pred[0, 0] = np.inf
        self.write(self.pred, pred)
        r = validate(self.ref, self.pred)
        self.assertFalse(r['ok'])
        self.assertEqual(r['infinite_pixels_whole_grid'], 1)

    def test_ambiguous_unmasked_nan_in_template_blocks(self):
        a = np.zeros((4, 4)); a[0, 0] = np.nan
        self.write(self.ref, a)
        self.write(self.pred, np.zeros((4, 4)))
        self.assertFalse(validate(self.ref, self.pred)['ok'])

    def test_internal_mask_can_make_a_finite_standalone_tiff(self):
        template = np.zeros((4, 4)); template[0, 0] = -9999
        self.write(self.ref, template, nodata=-9999)
        mask = np.full((4, 4), 255, dtype='uint8'); mask[0, 0] = 0
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
            with rasterio.open(self.pred, 'w', **self.profile) as ds:
                ds.write(np.zeros((4, 4), 'float32'), 1)
                ds.write_mask(mask)
        r = validate(self.ref, self.pred)
        self.assertTrue(r['ok'], r['errors'])
        self.assertTrue(r['raw_whole_grid_finite_in_range'])
        self.assertEqual(r['valid_outside_footprint'], 0)

    def test_external_mask_is_not_a_standalone_tiff(self):
        template = np.zeros((4, 4)); template[0, 0] = -9999
        self.write(self.ref, template, nodata=-9999)
        mask = np.full((4, 4), 255, dtype='uint8'); mask[0, 0] = 0
        with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
            with rasterio.open(self.pred, 'w', **self.profile) as ds:
                ds.write(np.zeros((4, 4), 'float32'), 1)
                ds.write_mask(mask)
        r = validate(self.ref, self.pred)
        self.assertFalse(r['ok'])
        self.assertTrue(any('sidecar' in e for e in r['errors']))


if __name__ == '__main__':
    unittest.main()

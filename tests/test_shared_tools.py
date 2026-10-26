import json
from pathlib import Path
import shutil
import tempfile
import unittest

import numpy as np

from scripts.audit_shared_tools import audit, synthetic_context
from scripts.shared_tools import TEMPLATE, load_tool, verify_template

ROOT = Path(__file__).resolve().parents[1]


class SharedToolTests(unittest.TestCase):
    def test_every_upstream_file_is_unmodified(self):
        result = verify_template()
        self.assertTrue(result["ok"])
        self.assertEqual(result["files_checked"], 13)

    def test_modified_or_missing_upstream_file_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "template"
            shutil.copytree(TEMPLATE, target)
            path = target / "src/gems32/metric.py"
            path.write_text(path.read_text() + "\n# private edit\n")
            self.assertFalse(verify_template(target)["ok"])
            path.unlink()
            self.assertFalse(verify_template(target)["ok"])

    def test_recomputed_plain_digest_cannot_whitelist_http_error_body(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'template'
            shutil.copytree(TEMPLATE, target)
            path = target / 'scripts/restore_data.py'
            path.write_text('{"message": "rate limit exceeded", "status": "403"}\n')
            lock_path = target / 'PROVENANCE.json'
            lock = json.loads(lock_path.read_text())
            for row in lock['files']:
                if row['path'] == 'scripts/restore_data.py':
                    row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            lock_path.write_text(json.dumps(lock))
            self.assertFalse(verify_template(target)['ok'])

    def test_all_shared_entry_points_are_real_importable_tools(self):
        for name in ('prepare_data', 'restore_data', 'evaluate_holdout', 'submission_writer'):
            self.assertTrue(callable(load_tool(name).main), name)
        self.assertTrue(callable(load_tool('restore_data').restore_entry))

    def test_absent_or_empty_lock_is_negative(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertFalse(verify_template(root)['ok'])
            (root / 'PROVENANCE.json').write_text('{"files": []}')
            self.assertFalse(verify_template(root)['ok'])

    def test_known_central_defect_blocks_not_promotes(self):
        result = audit()
        self.assertFalse(result["ok"])
        self.assertFalse(result["checks"]["empty_truth_cell_fp_preserved_in_pooled_totals"])
        self.assertTrue(result["checks"]["soft_fields_are_silently_binarized"])
        self.assertIsNone(result["numerical_model_scores"])
        self.assertIn("NOT HOLDOUT-DTI", result["kind"])
        self.assertEqual(result["blocking_findings"][0]["upstream_issue"], "https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41")

    def test_nonempty_truth_fixture_conserves_components(self):
        holdout, context, prediction = synthetic_context(empty_last=False)
        result = holdout.evaluate_hide_and_recover(prediction, context, grid_n=2, n_boot=32)
        for key, blocks in zip(("tp", "fp", "fn"), result["_block_totals"][:3]):
            self.assertAlmostEqual(sum(row[key] for row in result["folds"].values()), float(blocks.sum()))

    def test_shared_binary_metric_and_literal_shared_reference_agree(self):
        # A synthetic operator consistency check, never a geological score.
        module = load_tool("evaluate_holdout")
        from gems32 import metric
        rng = np.random.default_rng(7)
        for _ in range(8):
            prediction = rng.random((8, 8)) > 0.8
            truth = rng.random((8, 8)) > 0.9
            exact = metric.dti_exact(prediction, truth)
            fast = metric.dti_binary(prediction, truth)
            literal = metric.dti_bruteforce(prediction, truth)
            for key in ("tp", "fp", "fn", "dti"):
                self.assertAlmostEqual(exact[key], literal[key], places=10)
                self.assertAlmostEqual(fast[key], literal[key], places=10)
        self.assertEqual(float(module.holdout.kernel(3.0)), 0.0)
        self.assertEqual(float(module.holdout.kernel(0.0)), 1.0)

    def test_only_expected_shared_entry_points(self):
        for bad in ("../metric", "bo_surrogate", "unregistered"):
            with self.assertRaises(ValueError):
                load_tool(bad)

    def test_full_request_is_in_readme(self):
        request = (ROOT / "PROJECT_PROMPT.md").read_text()
        self.assertIn(request, (ROOT / "README.md").read_text())
        for text in ("PARALLEL-RUN PROTOCOL", "MUST GENERATE A UNIQUE TIF", "Pass 3:", "merge the pull request"):
            self.assertIn(text, request)

    def test_single_active_run_card(self):
        self.assertEqual(json.loads((ROOT / "run-card.json").read_text()), json.loads((ROOT / "docs/run-card.json").read_text()))
        card = json.loads((ROOT / "docs/run-card.json").read_text())
        self.assertEqual(card["verdict"], "negative")
        self.assertIsNone(card["holdout"]["value"])
        self.assertIsNone(card["raster_sha256"])
        self.assertEqual(card["experiments_run"], 0)
        self.assertLessEqual(len(card["submission_note"]), 140)


if __name__ == "__main__":
    unittest.main()

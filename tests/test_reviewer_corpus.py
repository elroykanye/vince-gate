"""Structural tests for the planted-defect reviewer corpus.

The corpus itself scores a real review, so it cannot run in CI — that lives in
`live_reviewer_corpus.py`. What runs here is everything about the corpus that can be checked
without a model: that it covers all seven contract criteria, that every case is scoreable by
machine rather than by opinion, and that every regex actually compiles and is discriminating.

A corpus with an unrunnable case or a regex that matches everything would give a reassuring score
and measure nothing, which is the failure mode this file exists to prevent.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "fixtures" / "reviewer_corpus.json"

CRITERIA = {
    "stop after the first CRITICAL",
    "omit untouched ACs or DoD claims",
    "trust narrative counts without mapping raw cases to assertions",
    "skip cross-artifact consistency checks",
    "declare fails closed without attacking every promised path",
    "complete a later pass by checking only prior findings",
    "issue PASS with incomplete manifest coverage",
}


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        cls.cases = cls.corpus["cases"]

    def test_every_contract_criterion_has_a_case(self):
        self.assertEqual(CRITERIA, {case["criterion"] for case in self.cases})

    def test_no_criterion_is_covered_twice(self):
        criteria = [case["criterion"] for case in self.cases]
        self.assertEqual(len(criteria), len(set(criteria)))

    def test_case_ids_are_unique(self):
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_case_is_scoreable_by_machine(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertEqual("PASS", case["forbidden_outcome"])
                self.assertGreaterEqual(len(case["required_signals"]), 2,
                                        "one signal is too easy to hit by accident")
                self.assertTrue(case["planted"], "a case with nothing planted scores nothing")
                self.assertIn("decoy", case)

    def test_every_case_names_the_real_defect_it_came_from(self):
        # Synthetic defects are easier to catch than real ones. If a case loses its provenance it
        # has probably drifted into being synthetic.
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertGreaterEqual(len(case["source"].split()), 12)

    def test_every_signal_compiles(self):
        for case in self.cases:
            for pattern in case["required_signals"]:
                with self.subTest(case=case["id"], pattern=pattern):
                    re.compile(pattern)

    def test_no_signal_matches_an_empty_or_generic_verdict(self):
        # A pattern that fires on boilerplate would score a reviewer that found nothing.
        boilerplate = (
            "# Review verdict: PASS\nReviewed repo@branch at abc1234. "
            "Baseline suite 10/10/0. Suite now 10/10/0.\n"
            "## Per-AC verdict\n## Findings\nnone\n## What is genuinely good\nthe code\n"
        )
        for case in self.cases:
            for pattern in case["required_signals"]:
                with self.subTest(case=case["id"], pattern=pattern):
                    self.assertIsNone(re.search(pattern, ""), "matches an empty verdict")
                    self.assertIsNone(re.search(pattern, boilerplate), "matches a boilerplate verdict")

    def test_a_decoy_only_review_does_not_score(self):
        # Every case must have at least one signal the decoy alone cannot satisfy, or "found the
        # obvious thing and stopped" would pass.
        for case in self.cases:
            with self.subTest(case=case["id"]):
                decoy_text = case["decoy"] + " " + case["planted"][0]
                unmatched = [p for p in case["required_signals"] if not re.search(p, decoy_text)]
                self.assertTrue(unmatched,
                                "every signal is satisfiable from the decoy alone; this case "
                                "cannot distinguish an exhaustive review from an early exit")

    def test_the_scoring_rule_is_stated(self):
        self.assertIn("FAIL", self.corpus["scoring"])
        self.assertIn("validate", self.corpus["scoring"])
        self.assertIn("decoy", self.corpus["scoring"])


if __name__ == "__main__":
    unittest.main()

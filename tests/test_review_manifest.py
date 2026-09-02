"""Tests for the exhaustive-review manifest validator.

`review_manifest.py` is what turns the v0.12.0 review contract from prose into something
mechanical. Until now it had no tests of its own, which is the trap the toolkit's own profile
records: an instrument nobody mutated is an instrument nobody has measured.

The seven behavioural criteria the contract names — the reviewer must not stop after the first
CRITICAL, must not omit untouched criteria, must not trust narrative counts, and so on — cannot be
unit-tested against a language model directly. What CAN be tested is the manifest shape each
failure produces, because a reviewer that commits one of those sins cannot write a manifest that
validates. Every test below is named for the criterion it enforces.
"""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "review_manifest.py"


def _load():
    spec = importlib.util.spec_from_file_location("review_manifest", SCRIPT)
    assert spec is not None and spec.loader is not None, f"cannot load {SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


review_manifest = _load()


def _command(procedure, argv, observed):
    return {
        "method": "command",
        "procedure": procedure,
        "argv": argv,
        "outcome": "PASS",
        "observed": observed,
        "exit_code": 0,
    }


def _inspection(procedure, subject, observed):
    return {
        "method": "inspection",
        "procedure": procedure,
        "subject": subject,
        "outcome": "PASS",
        "observed": observed,
    }


def _attack_passes():
    """A0-A7, each planned, terminal and evidenced — the shape a complete pass produces."""
    planned = {
        "A0": "re-derive the acceptance criteria from the tracker, not the ledger",
        "A1": "re-run every proof command in the ledger and diff origin/dev",
        "A2": "mutate each changed line and confirm a test fails",
        "A3": "empty, boundary, huge and duplicate inputs against the new entry point",
        "A4": "second-account token against the new entry point",
        "A5": "sweep every lessons.md trap touching this change",
        "A6": "find references to each changed public symbol and run their suites",
        "A7": "compare completion-documentation.md against the deployed revision",
    }
    return {
        name: {
            "plan": [plan],
            "status": "PROVEN",
            "evidence": [
                _command(plan, ["python", "-m", "unittest", "-v"], f"{name} ran, 144 tests, 0 failures")
            ],
        }
        for name, plan in planned.items()
    }


def _manifest():
    """A complete, valid pass-1 manifest. Every test mutates exactly one thing about it."""
    data = {
        "task": "SD-0001",
        "review_id": "SD-0001-review-1",
        "review_cycle_id": "SD-0001-cycle-a",
        "review_history": [],
        "pass_number": 1,
        "new_findings": 0,
        "frozen_before_ledger": True,
        "discovery_complete": True,
        "early_exit": False,
        "inventory": None,
        "items": [
            {
                "id": "AC-1",
                "kind": "acceptance",
                "claim": "the endpoint returns one labelled entry per date in the range",
                "source": "tracker SD-0001 acceptance criteria",
                "proof_plan": ["run the read-path suite and read the returned day count"],
                "attack_plan": ["request an inverted range and a range of 400 days"],
                "status": "PROVEN",
                "evidence": [
                    _command(
                        "run the read-path suite and read the returned day count",
                        ["python", "-m", "unittest", "tests.read_path"],
                        "11 entries returned for an 11-day range",
                    )
                ],
                "attacks": [
                    _command(
                        "request an inverted range and a range of 400 days",
                        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:1/x"],
                        "inverted range gave 0 rows, 400-day range gave HTTP 400",
                    )
                ],
            },
            {
                "id": "MC-1",
                "kind": "material-claim",
                "claim": "the ledger states the suite is 144 tests with 0 skips",
                "source": "verification-ledger.md line 812",
                "proof_plan": ["re-run the full suite and count skips"],
                "attack_plan": ["grep the diff for newly added skip markers"],
                "status": "PROVEN",
                "evidence": [
                    _inspection(
                        "re-run the full suite and count skips",
                        "dotnet test output",
                        "Passed 144, Skipped 0, matching the ledger",
                    )
                ],
                "attacks": [
                    _command(
                        "grep the diff for newly added skip markers",
                        ["git", "diff", "origin/dev...HEAD"],
                        "0 new Skip.IfNot or [Ignore] markers in the diff",
                    )
                ],
            },
        ],
        "attack_passes": _attack_passes(),
        "previous_findings": [],
        "adjacent_variants": ["the same range logic reached through the import path"],
        "untouched_surfaces": ["the three sibling endpoints on the same controller"],
    }
    data["inventory"] = review_manifest.frozen_plan(data)
    return data


def _refreeze(data):
    """Re-seal after changing something the seal covers, so the test isolates one failure."""
    data["inventory"] = review_manifest.frozen_plan(data)
    return data


class BaselineTests(unittest.TestCase):
    def test_a_complete_manifest_validates(self):
        # If this ever fails, every negative test below is passing for the wrong reason.
        self.assertEqual([], review_manifest.validate(_manifest()))

    def test_the_cli_agrees_with_the_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review-coverage.json"
            path.write_text(json.dumps(_manifest()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("exhaustive review manifest is complete", result.stdout)


class CannotStopAfterTheFirstCritical(unittest.TestCase):
    """Criterion 1. Discovery does not end because FAIL is already certain."""

    def test_an_item_left_unreviewed_is_still_rejected_when_another_item_already_failed(self):
        data = _manifest()
        data["items"][0]["status"] = "FINDING"
        data["items"][0]["finding_origin"] = "NEW"
        data["new_findings"] = 1
        data["items"][1]["status"] = "NOT-REVIEWED"
        _refreeze(data)
        self.assertIn("items[1].status must be terminal", review_manifest.validate(data))

    def test_declaring_an_early_exit_is_rejected(self):
        data = _manifest()
        data["early_exit"] = True
        _refreeze(data)
        self.assertIn("early_exit must be false", review_manifest.validate(data))

    def test_discovery_must_be_declared_complete(self):
        data = _manifest()
        data["discovery_complete"] = False
        _refreeze(data)
        self.assertIn("discovery_complete must be true", review_manifest.validate(data))

    def test_a_finding_row_still_needs_its_attacks_run(self):
        # The cheapest way to stop early is to record the defect and skip the attack plan.
        data = _manifest()
        data["items"][0]["status"] = "FINDING"
        data["items"][0]["finding_origin"] = "NEW"
        data["items"][0]["attacks"] = []
        data["new_findings"] = 1
        _refreeze(data)
        self.assertIn(
            "items[0].attacks must contain reproducible procedure/outcome/observation records",
            review_manifest.validate(data),
        )


class CannotOmitCriteria(unittest.TestCase):
    """Criterion 2. Untouched acceptance criteria and DoD claims cannot be dropped."""

    def test_an_inventory_with_no_acceptance_item_is_rejected(self):
        data = _manifest()
        data["items"] = [item for item in data["items"] if item["kind"] != "acceptance"]
        _refreeze(data)
        self.assertIn("inventory must include at least one acceptance item", review_manifest.validate(data))

    def test_an_inventory_with_no_material_claim_is_rejected(self):
        data = _manifest()
        data["items"] = [item for item in data["items"] if item["kind"] != "material-claim"]
        _refreeze(data)
        self.assertIn("inventory must include at least one material-claim item", review_manifest.validate(data))

    def test_deleting_an_item_after_freeze_breaks_the_seal(self):
        # Quietly dropping the criterion you could not prove is the failure mode here.
        data = _manifest()
        del data["items"][1]
        self.assertIn("inventory must match the frozen review plan and SHA-256", review_manifest.validate(data))

    def test_adding_an_item_after_freeze_breaks_the_seal(self):
        data = _manifest()
        data["items"].append(copy.deepcopy(data["items"][0]))
        data["items"][-1]["id"] = "AC-2"
        self.assertIn("inventory must match the frozen review plan and SHA-256", review_manifest.validate(data))

    def test_rewriting_a_claim_after_freeze_breaks_the_seal(self):
        # Softening an AC to match what was actually built is the SD-5433-era failure.
        data = _manifest()
        data["items"][0]["claim"] = "the endpoint returns something for most dates"
        self.assertIn("inventory must match the frozen review plan and SHA-256", review_manifest.validate(data))


class CannotTrustNarrativeCounts(unittest.TestCase):
    """Criterion 3. Counts are derived from rows, never copied from prose."""

    def test_a_fabricated_new_finding_count_is_rejected(self):
        data = _manifest()
        data["items"][0]["status"] = "FINDING"
        data["items"][0]["finding_origin"] = "NEW"
        data["new_findings"] = 0  # the row says one; the summary says none
        _refreeze(data)
        self.assertIn(
            "new_findings must equal the number of FINDING rows classified NEW",
            review_manifest.validate(data),
        )

    def test_a_finding_must_declare_whether_it_is_new_or_reproduced(self):
        data = _manifest()
        data["items"][0]["status"] = "FINDING"
        data["new_findings"] = 0
        _refreeze(data)
        self.assertIn("items[0].finding_origin must be NEW or REPRODUCED", review_manifest.validate(data))

    def test_evidence_must_trace_to_a_procedure_planned_before_the_ledger_was_read(self):
        data = _manifest()
        data["items"][0]["evidence"][0]["procedure"] = "looked at it and it seemed fine"
        _refreeze(data)
        self.assertIn(
            "items[0].evidence must contain reproducible procedure/outcome/observation records",
            review_manifest.validate(data),
        )

    def test_a_placeholder_observation_is_not_evidence(self):
        data = _manifest()
        data["items"][0]["evidence"][0]["observed"] = "TBD"
        _refreeze(data)
        self.assertIn(
            "items[0].evidence must contain reproducible procedure/outcome/observation records",
            review_manifest.validate(data),
        )

    def test_a_passing_outcome_cannot_carry_a_failing_exit_code(self):
        data = _manifest()
        data["items"][0]["evidence"][0]["exit_code"] = 1
        _refreeze(data)
        self.assertIn(
            "items[0].evidence must contain reproducible procedure/outcome/observation records",
            review_manifest.validate(data),
        )


class CannotSkipCrossArtifactChecks(unittest.TestCase):
    """Criterion 4. A7 compares documentation and delivery claims with reality."""

    def test_every_attack_pass_must_be_terminal(self):
        for name in (f"A{i}" for i in range(8)):
            with self.subTest(attack=name):
                data = _manifest()
                data["attack_passes"][name]["status"] = "NOT-REVIEWED"
                _refreeze(data)
                self.assertIn(
                    f"attack_passes.{name} must have a terminal status",
                    review_manifest.validate(data),
                )

    def test_a_missing_attack_pass_is_rejected(self):
        data = _manifest()
        del data["attack_passes"]["A7"]
        _refreeze(data)
        self.assertIn("attack_passes.A7 must be an object", review_manifest.validate(data))

    def test_an_attack_pass_with_no_evidence_is_rejected(self):
        data = _manifest()
        data["attack_passes"]["A7"]["evidence"] = []
        _refreeze(data)
        self.assertIn(
            "attack_passes.A7.evidence must contain reproducible outcome records",
            review_manifest.validate(data),
        )


class CannotClaimFailsClosedWithoutAttackingEveryPath(unittest.TestCase):
    """Criterion 5. A proven claim carries attacks tracing to its frozen attack plan."""

    def test_a_proven_item_with_no_attacks_is_rejected(self):
        data = _manifest()
        data["items"][0]["attacks"] = []
        _refreeze(data)
        self.assertIn(
            "items[0].attacks must contain reproducible procedure/outcome/observation records",
            review_manifest.validate(data),
        )

    def test_an_attack_that_was_not_planned_before_freeze_does_not_count(self):
        # Retro-fitting an easy attack in place of the hard one you planned.
        data = _manifest()
        data["items"][0]["attacks"][0]["procedure"] = "tried a normal request, looked fine"
        _refreeze(data)
        self.assertIn(
            "items[0].attacks must contain reproducible procedure/outcome/observation records",
            review_manifest.validate(data),
        )

    def test_an_item_cannot_be_frozen_without_an_attack_plan(self):
        data = _manifest()
        data["items"][0]["attack_plan"] = []
        _refreeze(data)
        self.assertIn("items[0].attack_plan must be planned before freeze", review_manifest.validate(data))


class CannotCompleteALaterPassByCheckingOnlyPriorFindings(unittest.TestCase):
    """Criterion 6. A later pass covers prior findings, adjacent variants and untouched surfaces."""

    def test_untouched_surfaces_cannot_be_empty(self):
        data = _manifest()
        data["untouched_surfaces"] = []
        _refreeze(data)
        self.assertIn(
            "untouched_surfaces must be a planned list of non-blank strings",
            review_manifest.validate(data),
        )

    def test_adjacent_variants_must_be_a_list_of_real_strings(self):
        data = _manifest()
        data["adjacent_variants"] = ["", "  "]
        _refreeze(data)
        self.assertIn(
            "adjacent_variants must be a planned list of non-blank strings",
            review_manifest.validate(data),
        )

    def test_pass_number_must_follow_the_recorded_history(self):
        data = _manifest()
        data["review_history"] = [{"pass": 1, "new_findings": 4}]
        data["pass_number"] = 1  # claims to be pass 1 while history already holds one
        _refreeze(data)
        self.assertIn("pass_number must immediately follow review_history", review_manifest.validate(data))

    def test_history_passes_must_be_contiguous(self):
        data = _manifest()
        data["review_history"] = [{"pass": 1, "new_findings": 4}, {"pass": 3, "new_findings": 2}]
        data["pass_number"] = 3
        _refreeze(data)
        self.assertIn(
            "review_history passes must be contiguous with non-negative new_findings",
            review_manifest.validate(data),
        )

    def test_a_new_review_id_is_required_for_each_pass(self):
        data = _manifest()
        data["review_id"] = ""
        _refreeze(data)
        self.assertIn("review_id must be a non-empty identifying string", review_manifest.validate(data))


class CannotPassWithIncompleteCoverage(unittest.TestCase):
    """Criterion 7. Every surface ends terminal, and the plan must have been sealed first."""

    def test_an_unfrozen_manifest_is_rejected(self):
        data = _manifest()
        data["frozen_before_ledger"] = False
        _refreeze(data)
        self.assertIn("frozen_before_ledger must be true", review_manifest.validate(data))

    def test_freeze_refuses_to_reseal_an_already_frozen_plan(self):
        # Re-freezing after seeing the ledger is how a manifest gets retro-fitted to the answer.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review-coverage.json"
            path.write_text(json.dumps(_manifest()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "freeze", str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("already frozen", result.stderr)

    def test_freeze_refuses_an_empty_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review-coverage.json"
            path.write_text(json.dumps({"task": "SD-0001", "items": []}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "freeze", str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("add review items before freezing", result.stderr)

    def test_duplicate_item_ids_are_rejected(self):
        data = _manifest()
        data["items"][1]["id"] = "AC-1"
        _refreeze(data)
        self.assertIn("items[1].id must be non-empty and unique", review_manifest.validate(data))


class ConvergenceRule(unittest.TestCase):
    """Pass 4+ must show a continuous >=50% decline, or the cycle is declared failed."""

    def _at_pass(self, history, current):
        data = _manifest()
        data["review_history"] = [
            {"pass": index, "new_findings": count} for index, count in enumerate(history, start=1)
        ]
        data["pass_number"] = len(history) + 1
        data["new_findings"] = current
        for item in data["items"]:
            item["status"] = "PROVEN"
            item.pop("finding_origin", None)
        if current:
            data["items"][0]["status"] = "FINDING"
            data["items"][0]["finding_origin"] = "NEW"
        return _refreeze(data)

    def test_passes_one_to_three_are_never_process_failures(self):
        for history in ([], [8], [8, 8]):
            with self.subTest(history=history):
                data = self._at_pass(history, 1)
                self.assertNotIn(
                    "review process failed",
                    " ".join(review_manifest.validate(data)),
                )

    def test_pass_four_without_a_halving_is_a_process_failure(self):
        data = self._at_pass([4, 3, 3], 1)
        self.assertIn(
            "review process failed: pass 4+ lacks a continuous >=50% decline; "
            "stop and redesign or replace the reviewer",
            review_manifest.validate(data),
        )

    def test_pass_four_with_a_continuous_halving_is_accepted(self):
        data = self._at_pass([8, 4, 2], 1)
        self.assertEqual([], review_manifest.validate(data))

    def test_a_single_flat_transition_is_enough_to_fail(self):
        # 8 -> 4 -> 4 -> 1: two of three transitions halve, one does not.
        data = self._at_pass([8, 4, 4], 1)
        self.assertIn("review process failed", " ".join(review_manifest.validate(data)))

    def test_once_at_zero_the_count_must_stay_at_zero(self):
        data = self._at_pass([4, 2, 0], 1)
        self.assertIn("review process failed", " ".join(review_manifest.validate(data)))
        clean = self._at_pass([4, 2, 0], 0)
        self.assertEqual([], review_manifest.validate(clean))


if __name__ == "__main__":
    unittest.main()

import json
import hashlib
import re
import subprocess
import sys
import tempfile
import io
import tarfile
import unittest
from pathlib import Path
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]

# Last release whose gemini binding rendered TOML commands under .gemini/commands/vince.
LEGACY_GEMINI_LAYOUT_TAG = "v0.11.2"
SKILLS = ROOT / "skills"


def skill_parts(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2)
    description = next(
        line.split(":", 1)[1].strip()
        for line in frontmatter.splitlines()
        if line.startswith("description:")
    )
    return description, body


class TokenEfficientSkillTests(unittest.TestCase):
    def complete_manifest(self):
        data = {
            "task": "Task-001",
            "review_id": "review-001",
            "review_cycle_id": "cycle-001",
            "review_history": [],
            "pass_number": 1,
            "new_findings": 0,
            "frozen_before_ledger": True,
            "discovery_complete": True,
            "early_exit": False,
            "items": [
                {
                    "id": "AC-1",
                    "kind": "acceptance",
                    "claim": "observable result",
                    "source": "original contract",
                    "proof_plan": ["run acceptance proof"],
                    "attack_plan": ["mutate acceptance behavior"],
                    "status": "PROVEN",
                    "evidence": [{"method": "command", "procedure": "run acceptance proof", "argv": ["python", "proof.py"], "outcome": "PASS", "observed": "proof.py exited with 0", "exit_code": 0}],
                    "attacks": [{"method": "command", "procedure": "mutate acceptance behavior", "argv": ["python", "mutate.py"], "outcome": "FAIL", "observed": "mutate.py exited with 1", "exit_code": 1}],
                },
                {
                    "id": "CLAIM-1",
                    "kind": "material-claim",
                    "claim": "documented result",
                    "source": "completion documentation",
                    "proof_plan": ["compare document with branch"],
                    "attack_plan": ["reverse documented claim"],
                    "status": "PROVEN",
                    "evidence": [{"method": "inspection", "procedure": "compare document with branch", "subject": "completion documentation", "outcome": "PASS", "observed": "completion-documentation.md matches branch"}],
                    "attacks": [{"method": "inspection", "procedure": "reverse documented claim", "subject": "completion documentation", "outcome": "PASS", "observed": "completion-documentation.md mismatch detected"}],
                },
            ],
            "attack_passes": {
                f"A{i}": {
                    "plan": [f"execute attack pass A{i}"],
                    "status": "PROVEN",
                    "evidence": [{"method": "command", "procedure": f"execute attack pass A{i}", "argv": ["python", "attack.py", f"A{i}"], "outcome": "PASS", "observed": f"attack.py A{i} exited 0", "exit_code": 0}],
                }
                for i in range(8)
            },
            "previous_findings": [],
            "adjacent_variants": ["semantic reversal"],
            "untouched_surfaces": ["none — all manifest items terminal"],
        }
        normalized = [
            {field: item[field] for field in ("id", "kind", "claim", "source", "proof_plan", "attack_plan")}
            for item in data["items"]
        ]
        sealed = {
            "task": data["task"],
            "review_id": data["review_id"],
            "items": normalized,
            "attack_passes": {name: value["plan"] for name, value in sorted(data["attack_passes"].items())},
            "previous_findings": data["previous_findings"],
            "adjacent_variants": data["adjacent_variants"],
            "untouched_surfaces": data["untouched_surfaces"],
            "review_cycle_id": data["review_cycle_id"],
            "review_history": data["review_history"],
            "pass_number": data["pass_number"],
        }
        payload = json.dumps(sealed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        kinds = ("acceptance", "definition-of-done", "dependent", "entry-point", "material-claim")
        data["inventory"] = {
            "item_count": len(data["items"]),
            "kind_counts": {kind: sum(item["kind"] == kind for item in data["items"]) for kind in kinds},
            "plan_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        }
        return data

    def test_discovery_descriptions_are_compact(self):
        descriptions = {}
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            description, _ = skill_parts(path)
            descriptions[path.parent.name] = description
            with self.subTest(skill=path.parent.name):
                self.assertLessEqual(len(description), 320)

        self.assertEqual(len(descriptions), len(set(descriptions.values())))
        trigger_matrix = {
            "vince-cleanup": ("cleanup", "worktree", "stray processes"),
            "vince-doctor": ("broken bindings", "profiles", "health check"),
            "vince-document": ("completion documentation", "publish", "handoffs"),
            "vince-implement": ("features", "fixes", "refactors", "changes code"),
            "vince-intake": ("vague", "unsafe", "actionable contract", "refusal"),
            "vince-learn": ("review findings", "lessons", "known traps", "PASS"),
            "vince-review": ("Adversarially review", "PASS", "FAIL", "done"),
            "vince-route": ("model", "agent role", "planning", "review"),
            "vince-setup": ("profile", "onboarding", "missing profiles", "drift"),
            "vince-update": ("upgrade", "roll back", "version", "outdated"),
        }
        self.assertEqual(set(descriptions), set(trigger_matrix))
        for skill, triggers in trigger_matrix.items():
            with self.subTest(skill=skill):
                lowered = descriptions[skill].lower()
                for trigger in triggers:
                    self.assertIn(trigger.lower(), lowered)

        words = {
            skill: set(re.findall(r"[a-z0-9]+", description.lower()))
            for skill, description in descriptions.items()
        }
        for left, left_words in words.items():
            for right, right_words in words.items():
                if left >= right:
                    continue
                overlap = len(left_words & right_words) / len(left_words | right_words)
                self.assertLessEqual(overlap, 0.35, f"routing descriptions overlap: {left}/{right}")

        frequencies = {
            skill: Counter(re.findall(r"[a-z0-9]+", description.lower()))
            for skill, description in descriptions.items()
        }
        for left, left_counts in frequencies.items():
            for right, right_counts in frequencies.items():
                if left >= right:
                    continue
                terms = set(left_counts) | set(right_counts)
                weighted = sum(min(left_counts[t], right_counts[t]) for t in terms) / sum(
                    max(left_counts[t], right_counts[t]) for t in terms
                )
                self.assertLessEqual(weighted, 0.35, f"frequency overlap: {left}/{right}")

        repeated = {
            skill: Counter(re.findall(r"[a-z0-9]+", (("review " * 15) + " ".join(triggers)).lower()))
            for skill, triggers in trigger_matrix.items()
        }
        synthetic_overlaps = []
        for left, left_counts in repeated.items():
            for right, right_counts in repeated.items():
                if left >= right:
                    continue
                terms = set(left_counts) | set(right_counts)
                synthetic_overlaps.append(
                    sum(min(left_counts[t], right_counts[t]) for t in terms)
                    / sum(max(left_counts[t], right_counts[t]) for t in terms)
                )
        self.assertGreater(max(synthetic_overlaps), 0.35)

    def test_primary_workflows_fit_activation_budget(self):
        for name in ("vince-implement", "vince-review"):
            _, body = skill_parts(SKILLS / name / "SKILL.md")
            with self.subTest(skill=name):
                self.assertLessEqual(
                    len(body),
                    20_000,
                    "activation body exceeds the conservative ~5k-token budget",
                )

    def test_detailed_shared_guidance_is_conditional(self):
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            _, body = skill_parts(path)
            with self.subTest(skill=path.parent.name):
                self.assertNotIn("Read `reference/voice.md`", body)
                self.assertNotIn("Also read `reference/token-discipline.md`", body)
                self.assertIsNone(
                    re.search(r"(?i)always load.{0,80}reference/(?:voice|token-discipline)\.md", body)
                )

        implement = (SKILLS / "vince-implement" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Load `reference/token-discipline.md` only", implement)
        self.assertIn("Load `reference/voice.md` only", implement)

    def test_every_skill_reports_concisely(self):
        rule = (
            "End user-facing updates with three short lines: `Result:`, `Problem:` (omit when "
            "none), and `Next:`. Keep detailed evidence in task artifacts, not chat."
        )
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            _, body = skill_parts(path)
            with self.subTest(skill=path.parent.name):
                self.assertIn(rule, body)

    def test_locked_instruction_and_support_content_is_unchanged(self):
        lock = json.loads((ROOT / "policies" / "content-lock.json").read_text(encoding="utf-8"))
        expected = {
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in SKILLS.rglob("*")
            if path.is_file() and path.suffix in {".md", ".py"}
        }
        expected.update(("README.md", "USER-GUIDE.md", "docs/harnesses.md"))
        self.assertEqual(expected, set(lock))
        for relative, digest in lock.items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            with self.subTest(path=relative):
                self.assertEqual(digest, actual)

    def test_progressive_references_preserve_the_gate(self):
        expected = {
            "vince-implement": (
                "reference/contract-and-recon.md",
                "reference/tdd-and-wire-proof.md",
                "reference/completion-and-review.md",
            ),
            "vince-review": (
                "reference/review-method.md",
                "reference/verdict-and-rereview.md",
            ),
        }
        required = {
            "vince-implement": ("RED", "GREEN", "TAMPER", "E2E-WIRE", "vince-review"),
            "vince-review": ("Pass 0", "mutation", "data boundaries", "PASS", "FAIL"),
        }
        for skill, references in expected.items():
            skill_dir = SKILLS / skill
            combined = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            for reference in references:
                self.assertIn(reference, combined)
                ref_path = skill_dir / reference
                self.assertTrue(ref_path.is_file(), reference)
                combined += ref_path.read_text(encoding="utf-8")
            for term in required[skill]:
                self.assertIn(term, combined)

    def test_implement_activation_preserves_non_negotiable_behavior(self):
        _, body = skill_parts(SKILLS / "vince-implement" / "SKILL.md")
        required_clauses = (
            "No implementation before a test fails for the expected reason.",
            "No completion claim before `vince-review` writes a PASS verdict.",
            "No claim such as “verified” or “tests pass” without the command and observed result.",
            "Never weaken RED, GREEN, TAMPER, regression, wire proof, or independent review to save tokens.",
            "The diff contains only the intended change.",
            "The suite is no worse than baseline.",
            "Nothing user-observable changed.",
            "No secret, debug artifact, or stray file is present.",
            "The commit message and version change follow the profile.",
        )
        for clause in required_clauses:
            self.assertIn(clause, body)
        self.assertIn("Name the three likeliest production failures and test them.", body)
        self.assertIsNone(re.search(r"(?i)(?:skip|omit|do not perform).{0,60}self-attack", body))
        self.assertIsNone(
            re.search(r"(?i)(?:permit|allow).{0,80}shared.{0,40}write.{0,40}(?:without|bypass)", body)
        )

    def test_review_verdict_contract_supports_learning_and_closure(self):
        text = (SKILLS / "vince-review" / "reference" / "verdict-and-rereview.md").read_text(
            encoding="utf-8"
        )
        self.assertGreaterEqual(text.count("[caught: <attack>]"), 2)
        self.assertIn("Reviewer verdict", text)
        self.assertIn("review-verdict.md", text)
        self.assertIn("verification ledger", text.lower())
        self.assertIn("Every finding must carry one `[caught: <attack>]` tag", text)
        self.assertIn("update the verification ledger's `Reviewer verdict` field", text)

    def test_review_requires_exhaustive_manifest_before_any_verdict(self):
        core = (SKILLS / "vince-review" / "SKILL.md").read_text(encoding="utf-8")
        method = (SKILLS / "vince-review" / "reference" / "review-method.md").read_text(
            encoding="utf-8"
        )
        combined = core + method
        required = (
            "Create and freeze `review-coverage.json` before opening the ledger",
            "Finding enough evidence for FAIL never ends discovery early.",
            "Every acceptance criterion, definition-of-done item, material claim, changed entry point, and applicable attack pass",
            "PROVEN, FINDING, BLOCKED, or UNREVIEWED",
            "A later pass must cover previous findings, adjacent variants, and previously untouched surfaces.",
            "At pass 4 or later, every one of",
            "the last three transitions must cut new findings by at least 50%.",
            "declare reviewer-process",
            "failure, stop the cycle",
            "python <toolkit>/scripts/review_manifest.py validate",
        )
        for clause in required:
            self.assertIn(clause, combined)
        self.assertIsNone(
            re.search(r"(?i)(?:stop|end|terminate).{0,80}(?:first|decisive).{0,40}(?:finding|defect)", combined)
        )
        self.assertIsNone(
            re.search(r"(?i)(?:permit|allow).{0,80}shared.{0,40}write.{0,40}(?:without|bypass)", combined)
        )
        self.assertTrue((ROOT / "templates" / "review-coverage.template.json").is_file())
        self.assertTrue((ROOT / "scripts" / "review_manifest.py").is_file())

    def test_review_manifest_validator_rejects_incomplete_coverage(self):
        validator = ROOT / "scripts" / "review_manifest.py"
        incomplete = {
            "task": "T",
            "frozen_before_ledger": True,
            "discovery_complete": True,
            "early_exit": False,
            "items": [{"id": "AC-1", "kind": "acceptance", "status": "PROVEN"}],
            "attack_passes": {},
        }
        complete = self.complete_manifest()
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.json"
            good = Path(directory) / "good.json"
            missing_a7 = Path(directory) / "missing-a7.json"
            bad.write_text(json.dumps(incomplete), encoding="utf-8")
            good.write_text(json.dumps(complete), encoding="utf-8")
            without_a7 = json.loads(json.dumps(complete))
            del without_a7["attack_passes"]["A7"]
            missing_a7.write_text(json.dumps(without_a7), encoding="utf-8")
            rejected = subprocess.run([sys.executable, str(validator), "validate", str(bad)])
            accepted = subprocess.run([sys.executable, str(validator), "validate", str(good)])
            rejected_a7 = subprocess.run(
                [sys.executable, str(validator), "validate", str(missing_a7)]
            )
        self.assertNotEqual(0, rejected.returncode)
        self.assertNotEqual(0, rejected_a7.returncode)
        self.assertEqual(0, accepted.returncode)

    def test_review_manifest_rejects_each_broken_rule_independently(self):
        validator = ROOT / "scripts" / "review_manifest.py"
        mutations = {}
        base = self.complete_manifest()

        def add(name, change):
            mutant = json.loads(json.dumps(base))
            change(mutant)
            mutations[name] = mutant

        add("missing-task", lambda value: value.pop("task"))
        add("blank-task", lambda value: value.update(task=" "))
        add("not-frozen", lambda value: value.update(frozen_before_ledger=False))
        add("discovery-incomplete", lambda value: value.update(discovery_complete=False))
        add("early-exit", lambda value: value.update(early_exit=True))
        add("empty-items", lambda value: value.update(items=[]))
        add("duplicate-id", lambda value: value["items"].append(dict(value["items"][0])))
        add("bad-kind", lambda value: value["items"][0].update(kind="other"))
        add("blank-claim", lambda value: value["items"][0].update(claim=""))
        add("blank-source", lambda value: value["items"][0].update(source=" "))
        add("nonterminal-item", lambda value: value["items"][0].update(status="NOT-REVIEWED"))
        add("blank-evidence", lambda value: value["items"][0].update(evidence=[" "]))
        add("null-evidence", lambda value: value["items"][0].update(evidence=[None]))
        add("blank-attack", lambda value: value["items"][0].update(attacks=[""]))
        add("missing-pass", lambda value: value["attack_passes"].pop("A4"))
        add("nonterminal-pass", lambda value: value["attack_passes"]["A2"].update(status="NOT-REVIEWED"))
        add("blank-pass-evidence", lambda value: value["attack_passes"]["A6"].update(evidence=[" "]))
        add("null-pass-evidence", lambda value: value["attack_passes"]["A7"].update(evidence=[None]))
        add("missing-rereview-list", lambda value: value.pop("adjacent_variants"))
        add("blank-untouched-surface", lambda value: value.update(untouched_surfaces=[" "]))
        add("deleted-item-after-freeze", lambda value: value["items"].pop())
        add("changed-claim-after-freeze", lambda value: value["items"][0].update(claim="changed claim"))
        add("deleted-attack-plan-after-freeze", lambda value: value["items"][0].pop("attack_plan"))
        add("deleted-adjacent-variant-after-freeze", lambda value: value.update(adjacent_variants=[]))
        add("wrong-id-type", lambda value: value["items"][0].update(id=[]))
        add("vacuous-evidence", lambda value: value["items"][0].update(evidence=["x"]))

        with tempfile.TemporaryDirectory() as directory:
            for name, mutant in mutations.items():
                path = Path(directory) / f"{name}.json"
                path.write_text(json.dumps(mutant), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(validator), "validate", str(path)],
                    capture_output=True,
                    text=True,
                )
                with self.subTest(rule=name):
                    self.assertNotEqual(0, result.returncode, result.stdout)

        template = json.loads(
            (ROOT / "templates" / "review-coverage.template.json").read_text(encoding="utf-8")
        )
        self.assertEqual({f"A{i}" for i in range(8)}, set(template["attack_passes"]))

    def test_review_manifest_freeze_records_tamper_evident_inventory(self):
        validator = ROOT / "scripts" / "review_manifest.py"
        manifest = self.complete_manifest()
        manifest.pop("inventory")
        manifest["frozen_before_ledger"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            frozen = subprocess.run(
                [sys.executable, str(validator), "freeze", str(path)], capture_output=True, text=True
            )
            refrozen = subprocess.run(
                [sys.executable, str(validator), "freeze", str(path)], capture_output=True, text=True
            )
            valid = subprocess.run(
                [sys.executable, str(validator), "validate", str(path)], capture_output=True, text=True
            )
            changed = json.loads(path.read_text(encoding="utf-8"))
            changed["items"].pop()
            path.write_text(json.dumps(changed), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(validator), "validate", str(path)], capture_output=True, text=True
            )
        self.assertEqual(0, frozen.returncode, frozen.stderr)
        self.assertNotEqual(0, refrozen.returncode)
        self.assertEqual(0, valid.returncode, valid.stderr)
        self.assertNotEqual(0, rejected.returncode)

    def test_review_manifest_freeze_rejects_non_object_json_without_traceback(self):
        validator = ROOT / "scripts" / "review_manifest.py"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.json"
            path.write_text("[]", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(validator), "freeze", str(path)], capture_output=True, text=True
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("manifest must be a JSON object", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_review_manifest_rejects_vacuous_structured_evidence(self):
        validator = ROOT / "scripts" / "review_manifest.py"
        manifest = self.complete_manifest()
        empty = {"method": "command", "procedure": "xxx", "outcome": "PASS", "observed": "xxx", "exit_code": 0}
        for item in manifest["items"]:
            item["evidence"] = [dict(empty)]
            item["attacks"] = [dict(empty)]
        for attack in manifest["attack_passes"].values():
            attack["evidence"] = [dict(empty)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(validator), "validate", str(path)], capture_output=True, text=True
            )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("reproducible", result.stderr)

        plausible = self.complete_manifest()
        filler = {"method": "command", "procedure": "run the complete verification command", "outcome": "PASS", "observed": "all verification checks completed successfully", "exit_code": 1}
        for item in plausible["items"]:
            item["evidence"] = [dict(filler)]
            item["attacks"] = [dict(filler)]
        for attack in plausible["attack_passes"].values():
            attack["evidence"] = [dict(filler)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plausible.json"
            path.write_text(json.dumps(plausible), encoding="utf-8")
            plausible_result = subprocess.run(
                [sys.executable, str(validator), "validate", str(path)], capture_output=True, text=True
            )
        self.assertNotEqual(0, plausible_result.returncode)

    def test_review_manifest_enforces_pass_four_convergence_boundary(self):
        validator = ROOT / "scripts" / "review_manifest.py"

        def run(history):
            manifest = self.complete_manifest()
            manifest["review_history"] = history[:-1]
            manifest["pass_number"] = history[-1]["pass"]
            manifest["new_findings"] = history[-1]["new_findings"]
            for item in manifest["items"][:manifest["new_findings"]]:
                item["status"] = "FINDING"
                item["finding_origin"] = "NEW"
            normalized = {
                "task": manifest["task"], "review_id": manifest["review_id"],
                "items": [{field: item[field] for field in ("id", "kind", "claim", "source", "proof_plan", "attack_plan")} for item in manifest["items"]],
                "attack_passes": {name: value["plan"] for name, value in sorted(manifest["attack_passes"].items())},
                "previous_findings": manifest["previous_findings"],
                "adjacent_variants": manifest["adjacent_variants"],
                "untouched_surfaces": manifest["untouched_surfaces"],
                "review_cycle_id": manifest["review_cycle_id"],
                "review_history": manifest["review_history"],
                "pass_number": manifest["pass_number"],
            }
            manifest["inventory"]["plan_sha256"] = hashlib.sha256(
                json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "coverage.json"
                path.write_text(json.dumps(manifest), encoding="utf-8")
                return subprocess.run(
                    [sys.executable, str(validator), "validate", str(path)], capture_output=True, text=True
                )

        pass_three = run([{"pass": 1, "new_findings": 8}, {"pass": 2, "new_findings": 4}, {"pass": 3, "new_findings": 2}])
        declining_four = run([{"pass": 1, "new_findings": 8}, {"pass": 2, "new_findings": 4}, {"pass": 3, "new_findings": 2}, {"pass": 4, "new_findings": 1}])
        flat_four = run([{"pass": 1, "new_findings": 8}, {"pass": 2, "new_findings": 4}, {"pass": 3, "new_findings": 3}, {"pass": 4, "new_findings": 2}])
        self.assertEqual(0, pass_three.returncode, pass_three.stderr)
        self.assertEqual(0, declining_four.returncode, declining_four.stderr)
        self.assertNotEqual(0, flat_four.returncode)
        self.assertIn("review process failed", flat_four.stderr)

    def test_current_finding_count_is_recorded_after_freeze_without_resealing(self):
        validator = ROOT / "scripts" / "review_manifest.py"
        manifest = self.complete_manifest()
        manifest.pop("inventory")
        manifest["new_findings"] = None
        manifest["frozen_before_ledger"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            frozen = subprocess.run([sys.executable, str(validator), "freeze", str(path)])
            updated = json.loads(path.read_text(encoding="utf-8"))
            updated["items"][0]["status"] = "FINDING"
            updated["items"][0]["finding_origin"] = "NEW"
            updated["new_findings"] = 1
            path.write_text(json.dumps(updated), encoding="utf-8")
            validated = subprocess.run(
                [sys.executable, str(validator), "validate", str(path)], capture_output=True, text=True
            )
        self.assertEqual(0, frozen.returncode)
        self.assertEqual(0, validated.returncode, validated.stderr)

        updated["new_findings"] = 999
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "arbitrary-count.json"
            path.write_text(json.dumps(updated), encoding="utf-8")
            arbitrary = subprocess.run(
                [sys.executable, str(validator), "validate", str(path)], capture_output=True, text=True
            )
        self.assertNotEqual(0, arbitrary.returncode)
        self.assertIn("classified NEW", arbitrary.stderr)

    def test_gemini_uses_native_agent_skills(self):
        binding = json.loads((ROOT / "bindings" / "gemini.json").read_text(encoding="utf-8"))
        self.assertEqual("dir", binding["layout"])
        self.assertEqual("yaml", binding["frontmatter"])
        self.assertEqual(".gemini/skills", binding["project_dir"])
        self.assertEqual("~/.gemini/skills", binding["user_dir"])
        self.assertEqual("SKILL.md", binding["entry"])
        self.assertIsNone(binding["index"])
        self.assertNotIn("command", binding["invocation"].lower())
        self.assertEqual("unverified", binding["status"])

    def test_copilot_has_a_non_colliding_native_binding(self):
        binding = json.loads((ROOT / "bindings" / "copilot.json").read_text(encoding="utf-8"))
        self.assertEqual("dir", binding["layout"])
        self.assertEqual("yaml", binding["frontmatter"])
        self.assertEqual(".github/skills", binding["project_dir"])
        self.assertEqual("~/.copilot/skills", binding["user_dir"])
        codex = json.loads((ROOT / "bindings" / "codex.json").read_text(encoding="utf-8"))
        self.assertNotEqual(codex["project_dir"], binding["project_dir"])
        self.assertNotEqual(codex["user_dir"], binding["user_dir"])
        self.assertEqual("unverified", binding["status"])

    def test_every_binding_renders_native_skill_entries(self):
        with tempfile.TemporaryDirectory() as target:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "install.py"),
                    "install",
                    "--target",
                    target,
                    "--scope",
                    "project",
                    "--binding",
                    "all",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("[gemini]", result.stdout)
        self.assertIn("[copilot]", result.stdout)
        self.assertGreaterEqual(result.stdout.count("vince-implement/SKILL.md"), 4)

    def test_gemini_upgrade_removes_legacy_managed_layout(self):
        # Pinned to the last release that actually ships the legacy layout. This used to archive
        # origin/main, which made the test self-invalidating: main became 0.12.0, 0.12.0 is the
        # release that REMOVES the legacy layout, so the "old" toolkit stopped being old and the
        # first assertion started failing the moment the change under test merged.
        archive = subprocess.run(
            ["git", "archive", "--format=tar", LEGACY_GEMINI_LAYOUT_TAG],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            old_toolkit = base / "old"
            target = base / "target"
            old_toolkit.mkdir()
            with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
                bundle.extractall(old_toolkit, filter="data")
            old = subprocess.run(
                [sys.executable, str(old_toolkit / "scripts" / "install.py"), "install", "--target", str(target), "--scope", "project", "--binding", "gemini"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, old.returncode, old.stderr)
            self.assertTrue((target / ".gemini" / "commands" / "vince").is_dir())
            upgraded = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "install.py"), "install", "--target", str(target), "--scope", "project", "--binding", "gemini"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, upgraded.returncode, upgraded.stderr)
            self.assertFalse((target / ".gemini" / "commands" / "vince").exists())
            index = target / "GEMINI.md"
            self.assertFalse(index.exists() and "BEGIN VINCE GATE" in index.read_text(encoding="utf-8"))
            status = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "install.py"), "status", "--target", str(target), "--scope", "project"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, status.returncode, status.stdout + status.stderr)
            self.assertIn("healthy", status.stdout)

    def test_docs_describe_progressive_native_bindings_truthfully(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        guide = (ROOT / "USER-GUIDE.md").read_text(encoding="utf-8")
        harnesses = (ROOT / "docs" / "harnesses.md").read_text(encoding="utf-8")
        combined = "\n".join((readme, guide, harnesses))
        self.assertIn("GitHub Copilot", combined)
        self.assertIn(".github/skills", combined)
        self.assertIn(".gemini/skills", combined)
        self.assertIn("progressive disclosure", combined.lower())
        self.assertIn("review-coverage.json", readme)
        self.assertIn("does not stop discovery after finding enough evidence to FAIL", guide)
        self.assertIn("exhaustive review manifest", harnesses.lower())
        self.assertNotIn("TOML commands for Gemini CLI", combined)
        self.assertNotIn("Gemini CLI | TOML custom commands", combined)
        self.assertIn(
            "Gemini CLI and GitHub Copilot follow their\n"
            "documented native skill paths but remain `unverified`",
            readme,
        )
        self.assertIn(
            "Both bindings follow current vendor documentation and are render-tested, but\n"
            "remain `unverified`",
            guide,
        )
        self.assertIn(
            "| `gemini` | Gemini CLI | `.gemini/skills/<skill>/SKILL.md` (user: `~/.gemini/skills/`) | native Agent Skill, YAML frontmatter | unverified |",
            harnesses,
        )
        for name, document in (("README", readme), ("USER-GUIDE", guide), ("harnesses", harnesses)):
            affirmative = re.findall(
                r"(?im)^.*(?:Gemini|Copilot).*(?:(?:are|is|status:?)\s+`?(?:live-verified|verified)`?|"
                r"production runtime.{0,30}(?:succeed|exercis)|proven live|"
                r"runtime support.{0,30}(?:proven|confirmed)|exercised successfully).*$",
                document,
            )
            self.assertEqual([], affirmative, f"false live-verification claim in {name}")
        self.assertIn(
            "| `copilot` | GitHub Copilot | `.github/skills/<skill>/SKILL.md` (user: `~/.copilot/skills/`) | native Agent Skill, YAML frontmatter | unverified |",
            harnesses,
        )


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Create and maintain a private, resumable dev-review ledger."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 3
MODE_NAMES = {
    "audit": "Mode: Audit",
    "audit-and-improve": "Mode: Audit and improve",
    "re-verify": "Mode: Re-verify",
}
PHASES = {
    "preflight",
    "audit",
    "specialist-challenge",
    "council",
    "awaiting-selection",
    "implementation",
    "verification",
    "report",
    "complete",
    "blocked",
}
RUN_STATUSES = {"in_progress", "awaiting_selection", "complete", "blocked"}
VERDICTS = {None, "Ready", "Ready with follow-ups", "Hold", "Blocked"}
CONFIDENCES = {None, "High", "Medium", "Low"}
REVIEW_EVIDENCE = {"Static only", "Runtime exercised"}
CLASSIFICATIONS = {"Fix candidate", "Research", "Preserve / justified", "Deferred"}
SEVERITIES = {"P0 Blocker", "P1 Major", "P2 Polish", "P3 Opportunity"}
OUTCOME_EVIDENCE = {"Verified", "Source-proven", "Untested risk"}
CAUSE_CONFIDENCE = {"Confirmed cause", "Supported cause", "Cause hypothesis"}
RECOMMENDATION_STRENGTH = {"Strong", "Worth exploring", "Speculative"}
FINDING_STATUSES = {
    "Open",
    "Selected",
    "Resolved",
    "Partially resolved",
    "Remaining",
    "Research",
    "Blocked",
    "Deferred",
    "Preserve / justified",
}
CHECK_RESULTS = {"PASS", "FAIL", "NOT RUN", "BLOCKED"}
COUNCIL_RESULTS = {"APPROVE", "APPROVE_WITH_NITS"}
IMPLEMENTATION_RECEIPT_RESULTS = {
    "worker": {"PASS"},
    "seniorFirst": {"PASS"},
    "peer": {"APPROVE", "APPROVE_WITH_NITS"},
    "seniorFinal": {"PASS"},
}
LIST_FIELDS = (
    "findings",
    "decisions",
    "checks",
    "research",
    "nextActions",
    "blockers",
)
RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{8}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def nonempty_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    for index, item in enumerate(value):
        nonempty_string(item, f"{label}[{index}]")
    return value


def run_git(repo: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    value = completed.stdout.strip()
    return value or None


def private_directory(path: Path) -> Path:
    if path.is_symlink():
        raise ValueError(f"refusing symlinked state directory: {path}")
    if path.exists() and not path.is_dir():
        raise ValueError(f"state path is not a directory: {path}")
    existed = path.exists()
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if existed and os.name != "nt" and stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError(f"state directory permissions are too broad: {path}")
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path


def require_private_file(path: Path) -> None:
    if os.name != "nt" and stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError(f"state file permissions are too broad: {path}")


def user_state_base() -> Path:
    override = os.environ.get("DEV_REVIEW_STATE_DIR")
    if override:
        return Path(override).expanduser().absolute()
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local).expanduser().absolute() / "dev-review" / "state"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "dev-review" / "state"
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return Path(xdg_state).expanduser().absolute() / "dev-review"
    return Path.home() / ".local" / "state" / "dev-review"


def repository_context(repo: Path) -> dict[str, str | None]:
    requested = repo.expanduser().resolve()
    root_raw = run_git(requested, "rev-parse", "--show-toplevel")
    if root_raw:
        root = Path(root_raw).resolve()
        common_raw = run_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
        if common_raw:
            common = Path(common_raw).expanduser()
            if not common.is_absolute():
                common = root / common
            common = common.resolve()
            storage = common / "dev-review"
        else:
            common = (root / ".git").resolve()
            storage = common / "dev-review"
        kind = "git-common-dir"
        identity = "git-common-dir:" + hashlib.sha256(str(common).encode()).hexdigest()
        revision = run_git(root, "rev-parse", "HEAD")
    else:
        root = requested
        repo_key = hashlib.sha256(str(root).encode()).hexdigest()[:20]
        storage = user_state_base() / repo_key
        kind = "user-state"
        identity = f"user-state:{repo_key}"
        revision = None

    return {
        "root": str(root),
        "identity": identity,
        "storage": str(storage),
        "storageKind": kind,
        "revision": revision,
    }


def resolve_base_revision(context: dict[str, str | None], requested: str | None) -> str | None:
    if requested is None:
        return context["revision"]
    if context["storageKind"] != "git-common-dir":
        raise ValueError("--base-revision requires a Git repository")
    resolved = run_git(Path(str(context["root"])), "rev-parse", "--verify", f"{requested}^{{commit}}")
    if resolved is None:
        raise ValueError(f"base revision does not resolve to a commit: {requested}")
    return resolved


def storage_paths(repo: Path, ensure: bool = False) -> tuple[dict[str, str | None], Path, Path]:
    context = repository_context(repo)
    storage = Path(str(context["storage"]))
    runs = storage / "runs"
    if ensure:
        private_directory(storage)
        private_directory(runs)
    else:
        if storage.exists():
            private_directory(storage)
        if runs.exists():
            private_directory(runs)
    return context, storage, runs


def acquire_advisory_lock(descriptor: int, lock_path: Path, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            if os.name == "nt":
                import msvcrt

                if os.fstat(descriptor).st_size == 0:
                    os.write(descriptor, b"\0")
                    os.fsync(descriptor)
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise ValueError(f"state is locked by another writer; inspect: {lock_path}")
            time.sleep(0.05)


def release_advisory_lock(descriptor: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(descriptor, fcntl.LOCK_UN)


@contextlib.contextmanager
def write_lock(storage: Path, timeout_seconds: float = 10.0) -> Iterator[None]:
    private_directory(storage)
    lock_path = storage / "write.lock"
    if lock_path.is_symlink():
        raise ValueError(f"refusing symlinked state lock: {lock_path}")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    acquired = False
    try:
        if os.name != "nt" and stat.S_IMODE(os.fstat(descriptor).st_mode) & 0o077:
            raise ValueError(f"state lock permissions are too broad: {lock_path}")
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        acquire_advisory_lock(descriptor, lock_path, timeout_seconds)
        acquired = True
        if lock_path.is_symlink():
            raise ValueError(f"refusing symlinked state lock: {lock_path}")
        opened = os.fstat(descriptor)
        current = os.stat(lock_path, follow_symlinks=False)
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("state lock path changed while acquiring the advisory lock")
        os.ftruncate(descriptor, 0)
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.write(descriptor, f"pid={os.getpid()} created={now_utc()}\n".encode())
        os.fsync(descriptor)
        yield
    finally:
        if acquired:
            release_advisory_lock(descriptor)
        os.close(descriptor)


def atomic_write(path: Path, payload: bytes) -> None:
    private_directory(path.parent)
    if path.is_symlink():
        raise ValueError(f"refusing symlinked state file: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temporary = Path(temporary_name)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
        if hasattr(os, "O_DIRECTORY"):
            try:
                parent_descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            except OSError:
                parent_descriptor = None
            if parent_descriptor is not None:
                try:
                    os.fsync(parent_descriptor)
                finally:
                    os.close(parent_descriptor)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise


def write_json(path: Path, value: dict[str, Any]) -> None:
    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    atomic_write(path, encoded)


def validate_run_id(run_id: str) -> None:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("invalid run ID")


def latest_run_id(storage: Path) -> str | None:
    marker = storage / "latest-run.txt"
    if marker.is_symlink():
        raise ValueError("refusing symlinked latest-run marker")
    if not marker.is_file():
        return None
    require_private_file(marker)
    run_id = marker.read_text(encoding="utf-8").strip()
    validate_run_id(run_id)
    return run_id


def resolve_run(storage: Path, run: str) -> str | None:
    run_id = latest_run_id(storage) if run == "latest" else run
    if run_id is not None:
        validate_run_id(run_id)
    return run_id


def load_run(runs: Path, run_id: str) -> dict[str, Any]:
    validate_run_id(run_id)
    path = runs / f"{run_id}.json"
    if path.is_symlink():
        raise ValueError(f"refusing symlinked review run: {run_id}")
    if not path.is_file():
        raise FileNotFoundError(f"review run not found: {run_id}")
    require_private_file(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("review ledger must be a JSON object")
    return value


def validate_selection_receipt(
    receipt: object,
    run_id: str,
    finding_id: str,
    evidence_revision: str,
    index: int,
) -> None:
    if not isinstance(receipt, dict) or set(receipt) != {
        "selectionKey",
        "authority",
        "approvedAt",
    }:
        raise TypeError(f"findings[{index}].selectionReceipt is invalid")
    expected = f"{run_id}:{finding_id}@{evidence_revision}"
    if receipt.get("selectionKey") != expected:
        raise ValueError(f"findings[{index}].selectionReceipt is stale or mismatched")
    if receipt.get("authority") != "User":
        raise ValueError(f"findings[{index}].selectionReceipt authority must be User")
    nonempty_string(receipt.get("approvedAt"), f"findings[{index}].selectionReceipt.approvedAt")


def validate_implementation_receipts(
    receipts: object,
    owner: str,
    peer_reviewer: str,
    index: int,
    require_complete: bool,
) -> str | None:
    if not isinstance(receipts, dict) or set(receipts) != set(IMPLEMENTATION_RECEIPT_RESULTS):
        raise TypeError(f"findings[{index}].implementationReceipts is invalid")
    digests: set[str] = set()
    actors: dict[str, str] = {}
    missing: list[str] = []
    for role, allowed_results in IMPLEMENTATION_RECEIPT_RESULTS.items():
        receipt = receipts.get(role)
        if receipt is None:
            missing.append(role)
            continue
        if not isinstance(receipt, dict) or set(receipt) != {"actor", "result", "treeSha256"}:
            raise TypeError(f"findings[{index}].implementationReceipts.{role} is invalid")
        actor = nonempty_string(
            receipt.get("actor"),
            f"findings[{index}].implementationReceipts.{role}.actor",
        )
        if receipt.get("result") not in allowed_results:
            raise ValueError(
                f"findings[{index}].implementationReceipts.{role}.result is invalid"
            )
        tree_digest = receipt.get("treeSha256")
        if not isinstance(tree_digest, str) or not SHA256_PATTERN.fullmatch(tree_digest):
            raise ValueError(
                f"findings[{index}].implementationReceipts.{role}.treeSha256 is invalid"
            )
        actors[role] = actor
        digests.add(tree_digest)
    if require_complete and missing:
        raise ValueError(f"findings[{index}] Resolved status requires all review receipts")
    if len(digests) > 1:
        raise ValueError(f"findings[{index}] review receipts must bind one accepted tree digest")
    if actors.get("worker") not in {None, owner}:
        raise ValueError(f"findings[{index}] worker receipt must match owner")
    if actors.get("peer") not in {None, peer_reviewer}:
        raise ValueError(f"findings[{index}] peer receipt must match peerReviewer")
    if (
        actors.get("seniorFirst") is not None
        and actors.get("seniorFinal") is not None
        and actors["seniorFirst"] != actors["seniorFinal"]
    ):
        raise ValueError(f"findings[{index}] senior receipts must name one senior owner")
    senior = actors.get("seniorFinal") or actors.get("seniorFirst")
    if senior is not None and senior in {owner, peer_reviewer}:
        raise ValueError(f"findings[{index}] senior, owner, and peer must be distinct")
    return next(iter(digests), None)


def validate_finding(finding: object, run_id: str, index: int) -> str:
    if not isinstance(finding, dict):
        raise TypeError(f"findings[{index}] must be an object")
    run_suffix = run_id.rsplit("-", 1)[1]
    finding_id = nonempty_string(finding.get("id"), f"findings[{index}].id")
    if not re.fullmatch(rf"DR-{run_suffix}-\d{{3}}", finding_id):
        raise ValueError(f"findings[{index}].id must bind to run suffix {run_suffix}")
    if finding.get("runId") != run_id:
        raise ValueError(f"findings[{index}].runId must match the ledger run")
    for field in (
        "title",
        "scope",
        "evidenceRevision",
        "affectedOutcome",
        "causalBasis",
        "preservationConstraint",
        "boundedDirection",
        "effort",
        "regressionRisk",
    ):
        nonempty_string(finding.get(field), f"findings[{index}].{field}")
    enum_fields = (
        ("classification", CLASSIFICATIONS),
        ("severity", SEVERITIES),
        ("outcomeEvidence", OUTCOME_EVIDENCE),
        ("causalConfidence", CAUSE_CONFIDENCE),
        ("recommendationStrength", RECOMMENDATION_STRENGTH),
        ("status", FINDING_STATUSES),
    )
    for field, allowed in enum_fields:
        if finding.get(field) not in allowed:
            raise ValueError(f"findings[{index}].{field} has an invalid value")
    if not isinstance(finding.get("selected"), bool):
        raise TypeError(f"findings[{index}].selected must be boolean")
    for field in ("evidenceTrace", "relevantFiles", "acceptanceChecks"):
        nonempty_string_list(finding.get(field), f"findings[{index}].{field}")
    classification = finding["classification"]
    status = finding["status"]
    selected = finding["selected"]
    if classification == "Fix candidate":
        if finding["outcomeEvidence"] not in {"Verified", "Source-proven"}:
            raise ValueError(f"findings[{index}] Fix candidate requires verified or source-proven outcome")
        if finding["causalConfidence"] not in {"Confirmed cause", "Supported cause"}:
            raise ValueError(f"findings[{index}] Fix candidate requires confirmed or supported cause")
        if finding["recommendationStrength"] != "Strong":
            raise ValueError(f"findings[{index}] Fix candidate requires a Strong recommendation")
        if status not in {
            "Open",
            "Selected",
            "Resolved",
            "Partially resolved",
            "Remaining",
            "Blocked",
        }:
            raise ValueError(f"findings[{index}] Fix candidate has inconsistent status")
    elif classification == "Research" and status not in {"Research", "Blocked"}:
        raise ValueError(f"findings[{index}] Research classification has inconsistent status")
    elif classification == "Deferred" and status != "Deferred":
        raise ValueError(f"findings[{index}] Deferred classification requires Deferred status")
    elif classification == "Preserve / justified" and status != "Preserve / justified":
        raise ValueError(
            f"findings[{index}] Preserve / justified classification requires matching status"
        )
    for field in ("owner", "peerReviewer", "selectionReceipt", "implementationReceipts"):
        if field not in finding:
            raise ValueError(f"findings[{index}].{field} is required")
    owner = finding.get("owner")
    peer_reviewer = finding.get("peerReviewer")
    if selected and classification != "Fix candidate":
        raise ValueError(f"findings[{index}] only a Fix candidate can be selected")
    if selected:
        if status not in {
            "Selected",
            "Resolved",
            "Partially resolved",
            "Remaining",
            "Blocked",
        }:
            raise ValueError(f"findings[{index}] selected finding has inconsistent status")
        owner = nonempty_string(owner, f"findings[{index}].owner")
        peer_reviewer = nonempty_string(peer_reviewer, f"findings[{index}].peerReviewer")
        if owner == peer_reviewer:
            raise ValueError(f"findings[{index}] owner and peerReviewer must be distinct")
        validate_selection_receipt(
            finding["selectionReceipt"],
            run_id,
            finding_id,
            finding["evidenceRevision"],
            index,
        )
        validate_implementation_receipts(
            finding["implementationReceipts"],
            owner,
            peer_reviewer,
            index,
            require_complete=status == "Resolved",
        )
    else:
        if classification == "Fix candidate" and status != "Open":
            raise ValueError(f"findings[{index}] unselected Fix candidate must remain Open")
        if any(
            value is not None
            for value in (
                owner,
                peer_reviewer,
                finding["selectionReceipt"],
                finding["implementationReceipts"],
            )
        ):
            raise ValueError(f"findings[{index}] unselected finding cannot have implementation state")
    return finding_id


def validate_council_approval(approval: object, report_digest: str) -> None:
    expected_keys = {
        "reportSha256",
        "candidateDigest",
        "evidenceRevision",
        "approvedAt",
        "roundOne",
        "roundTwo",
    }
    if not isinstance(approval, dict) or set(approval) != expected_keys:
        raise TypeError("reportCouncilApproval is invalid")
    if approval.get("reportSha256") != report_digest:
        raise ValueError("reportCouncilApproval must bind the current report digest")
    candidate_digest = approval.get("candidateDigest")
    if not isinstance(candidate_digest, str) or not SHA256_PATTERN.fullmatch(candidate_digest):
        raise ValueError("reportCouncilApproval.candidateDigest is invalid")
    for field in ("evidenceRevision", "approvedAt"):
        nonempty_string(approval.get(field), f"reportCouncilApproval.{field}")
    for round_name in ("roundOne", "roundTwo"):
        results = approval.get(round_name)
        if not isinstance(results, list) or len(results) != 4:
            raise ValueError(f"reportCouncilApproval.{round_name} requires four verdicts")
        if any(result not in COUNCIL_RESULTS for result in results):
            raise ValueError(f"reportCouncilApproval.{round_name} contains a blocking verdict")


def validate_state(value: dict[str, Any], run_id: str, repository_identity: str) -> None:
    if value.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError(f"schemaVersion must be {SCHEMA_VERSION}")
    if value.get("runId") != run_id:
        raise ValueError("runId does not match the selected run")
    validate_run_id(run_id)
    repository = value.get("repository")
    if not isinstance(repository, dict) or repository.get("identity") != repository_identity:
        raise ValueError("repository.identity does not match the selected repository")
    if repository.get("storageKind") not in {"git-common-dir", "user-state"}:
        raise ValueError("repository.storageKind is invalid")
    for field in ("initialRoot", "activeRoot"):
        nonempty_string(repository.get(field), f"repository.{field}")
    for field in ("baseRevision", "currentRevision"):
        revision = repository.get(field)
        if revision is not None:
            nonempty_string(revision, f"repository.{field}")
    mode = value.get("mode")
    phase = value.get("phase")
    status = value.get("status")
    if mode not in set(MODE_NAMES.values()):
        raise ValueError("mode is invalid")
    if phase not in PHASES:
        raise ValueError("phase is invalid")
    if status not in RUN_STATUSES:
        raise ValueError("status is invalid")
    required_status = {
        "awaiting-selection": "awaiting_selection",
        "complete": "complete",
        "blocked": "blocked",
    }.get(phase, "in_progress")
    if status != required_status:
        raise ValueError(f"phase {phase} requires status {required_status}")
    if phase == "awaiting-selection" and mode != "Mode: Audit":
        raise ValueError("awaiting-selection phase requires Mode: Audit")
    if phase == "implementation" and mode != "Mode: Audit and improve":
        raise ValueError("implementation phase requires Mode: Audit and improve")
    if phase == "verification" and mode not in {"Mode: Audit and improve", "Mode: Re-verify"}:
        raise ValueError("verification phase requires an implementation or re-verification mode")
    for field in ("scope", "createdAt", "updatedAt"):
        nonempty_string(value.get(field), field)
    previous = value.get("previousRunId")
    if previous is not None:
        validate_run_id(nonempty_string(previous, "previousRunId"))
        if previous == run_id:
            raise ValueError("previousRunId cannot equal runId")
    for field in LIST_FIELDS:
        if not isinstance(value.get(field), list):
            raise TypeError(f"{field} must be a list")
    finding_ids = [validate_finding(item, run_id, index) for index, item in enumerate(value["findings"])]
    if len(finding_ids) != len(set(finding_ids)):
        raise ValueError("finding IDs must be unique")
    selected_findings = [finding for finding in value["findings"] if finding["selected"]]
    if selected_findings and mode != "Mode: Audit and improve":
        raise ValueError("selected findings require Mode: Audit and improve")
    for index, check in enumerate(value["checks"]):
        if not isinstance(check, dict):
            raise TypeError(f"checks[{index}] must be an object")
        if set(check) != {"name", "evidenceRevision", "result", "required", "findingId", "treeSha256"}:
            raise ValueError(f"checks[{index}] has an invalid shape")
        nonempty_string(check.get("name"), f"checks[{index}].name")
        nonempty_string(check.get("evidenceRevision"), f"checks[{index}].evidenceRevision")
        if check.get("result") not in CHECK_RESULTS:
            raise ValueError(f"checks[{index}].result is invalid")
        if not isinstance(check.get("required"), bool):
            raise TypeError(f"checks[{index}].required must be boolean")
        finding_id = check.get("findingId")
        if finding_id is not None and finding_id not in finding_ids:
            raise ValueError(f"checks[{index}].findingId is unknown")
        tree_digest = check.get("treeSha256")
        if not isinstance(tree_digest, str) or not SHA256_PATTERN.fullmatch(tree_digest):
            raise ValueError(f"checks[{index}].treeSha256 is invalid")
        if finding_id is not None:
            finding = next(item for item in value["findings"] if item["id"] == finding_id)
            if check["evidenceRevision"] != finding["evidenceRevision"]:
                raise ValueError(f"checks[{index}] evidence revision is stale for its finding")
    for finding in selected_findings:
        if finding["status"] != "Resolved":
            continue
        accepted_tree = finding["implementationReceipts"]["seniorFinal"]["treeSha256"]
        for acceptance_check in finding["acceptanceChecks"]:
            matching = [
                check
                for check in value["checks"]
                if check["required"]
                and check["result"] == "PASS"
                and check["findingId"] == finding["id"]
                and check["name"] == acceptance_check
                and check["evidenceRevision"] == finding["evidenceRevision"]
                and check["treeSha256"] == accepted_tree
            ]
            if not matching:
                raise ValueError(
                    "Resolved status requires a passing tree-bound check for every acceptance"
                )
    for index, research in enumerate(value["research"]):
        if not isinstance(research, dict):
            raise TypeError(f"research[{index}] must be an object")
        for field in (
            "id",
            "question",
            "missingEvidence",
            "nextExperiment",
            "costRisk",
            "stopCondition",
        ):
            nonempty_string(research.get(field), f"research[{index}].{field}")
    score = value.get("score")
    if score is not None and (
        isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 10
    ):
        raise ValueError("score must be null or a number from 0 to 10")
    if value.get("coverageConfidence") not in CONFIDENCES:
        raise ValueError("coverageConfidence is invalid")
    if value.get("reviewEvidence") not in REVIEW_EVIDENCE:
        raise ValueError("reviewEvidence is invalid")
    if value.get("productionVerdict") not in VERDICTS:
        raise ValueError("productionVerdict is invalid")
    scored_fields_present = (
        score is not None,
        value.get("coverageConfidence") is not None,
        value.get("productionVerdict") is not None,
    )
    if len(set(scored_fields_present)) != 1:
        raise ValueError("score, coverageConfidence, and productionVerdict must be recorded together")
    unresolved_p0 = any(
        finding["severity"] == "P0 Blocker" and finding["status"] != "Resolved"
        for finding in value["findings"]
    )
    unresolved_p1 = any(
        finding["severity"] == "P1 Major" and finding["status"] != "Resolved"
        for finding in value["findings"]
    )
    verdict = value.get("productionVerdict")
    if unresolved_p0:
        if score is not None and score > 3.9:
            raise ValueError("unresolved P0 Blocker caps score at 3.9")
        if verdict is not None and verdict != "Blocked":
            raise ValueError("unresolved P0 Blocker requires verdict Blocked")
    elif unresolved_p1:
        if score is not None and score > 6.4:
            raise ValueError("unresolved P1 Major caps score at 6.4")
        if verdict is not None and verdict not in {"Hold", "Blocked"}:
            raise ValueError("unresolved P1 Major requires verdict Hold or Blocked")
    if verdict in {"Ready", "Ready with follow-ups"}:
        if value["reviewEvidence"] != "Runtime exercised":
            raise ValueError("ready verdict requires runtime evidence")
        if value["coverageConfidence"] not in {"High", "Medium"}:
            raise ValueError("ready verdict requires High or Medium coverage confidence")
        required_checks = [check for check in value["checks"] if check["required"]]
        if not required_checks:
            raise ValueError("ready verdict requires at least one required verification check")
        failed_required = [
            check for check in required_checks if check["result"] != "PASS"
        ]
        if failed_required:
            raise ValueError("ready verdict requires every required check to pass")
        unresolved_selected = [
            finding
            for finding in value["findings"]
            if finding["selected"] and finding["status"] != "Resolved"
        ]
        if unresolved_selected:
            raise ValueError("ready verdict requires every selected finding to be resolved")
        for finding in selected_findings:
            accepted_tree = finding["implementationReceipts"]["seniorFinal"]["treeSha256"]
            for acceptance_check in finding["acceptanceChecks"]:
                matching = [
                    check
                    for check in required_checks
                    if check["findingId"] == finding["id"]
                    and check["name"] == acceptance_check
                    and check["evidenceRevision"] == finding["evidenceRevision"]
                    and check["treeSha256"] == accepted_tree
                    and check["result"] == "PASS"
                ]
                if not matching:
                    raise ValueError(
                        "ready verdict requires a passing tree-bound check for every selected acceptance"
                    )
    report_path = value.get("reportPath")
    report_digest = value.get("reportSha256")
    council_approval = value.get("reportCouncilApproval")
    if report_path is None:
        if report_digest is not None or council_approval is not None:
            raise ValueError("report digest or council approval requires reportPath")
    else:
        nonempty_string(report_path, "reportPath")
        if not isinstance(report_digest, str) or not SHA256_PATTERN.fullmatch(report_digest):
            raise ValueError("reportSha256 must be a lowercase SHA-256 when reportPath is set")
        if council_approval is not None:
            validate_council_approval(council_approval, report_digest)
    if phase in {"awaiting-selection", "complete"} and (
        score is None or report_path is None or council_approval is None
    ):
        raise ValueError(f"phase {phase} requires score, report, and council approval")


def report_artifact_status(value: dict[str, Any]) -> str:
    report_path = value.get("reportPath")
    if not isinstance(report_path, str):
        return "not-recorded"
    candidate = Path(report_path)
    if candidate.is_symlink():
        return "unsafe-symlink"
    if not candidate.is_file():
        return "missing"
    if os.name != "nt" and stat.S_IMODE(candidate.stat().st_mode) & 0o077:
        return "unsafe-permissions"
    if hashlib.sha256(candidate.read_bytes()).hexdigest() != value.get("reportSha256"):
        return "digest-mismatch"
    return "verified"


def command_init(args: argparse.Namespace) -> int:
    context, storage, runs = storage_paths(Path(args.repo), ensure=True)
    base_revision = resolve_base_revision(context, args.base_revision)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}-{uuid.uuid4().hex[:8]}"
    created = now_utc()
    state: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "runId": run_id,
        "previousRunId": args.previous_run,
        "repository": {
            "identity": context["identity"],
            "initialRoot": context["root"],
            "activeRoot": context["root"],
            "storageKind": context["storageKind"],
            "baseRevision": base_revision,
            "currentRevision": context["revision"],
        },
        "createdAt": created,
        "updatedAt": created,
        "mode": MODE_NAMES[args.mode],
        "scope": args.scope,
        "phase": "preflight",
        "status": "in_progress",
        "reportPath": None,
        "reportSha256": None,
        "reportCouncilApproval": None,
        "score": None,
        "coverageConfidence": None,
        "reviewEvidence": "Static only",
        "productionVerdict": None,
        "findings": [],
        "decisions": [],
        "checks": [],
        "research": [],
        "nextActions": [],
        "blockers": [],
    }
    validate_state(state, run_id, str(context["identity"]))
    with write_lock(storage):
        write_json(runs / f"{run_id}.json", state)
        atomic_write(storage / "latest-run.txt", f"{run_id}\n".encode())
    print(json.dumps({"runId": run_id, "ledgerPath": str(runs / f"{run_id}.json"), "state": state}, indent=2))
    return 0


def command_show(args: argparse.Namespace) -> int:
    context, storage, runs = storage_paths(Path(args.repo), ensure=False)
    if not storage.exists():
        print(json.dumps({"found": False, "repository": context["root"]}, indent=2))
        return 0
    run_id = resolve_run(storage, args.run)
    if run_id is None:
        print(json.dumps({"found": False, "repository": context["root"]}, indent=2))
        return 0
    value = load_run(runs, run_id)
    validate_state(value, run_id, str(context["identity"]))
    report_status = report_artifact_status(value)
    print(
        json.dumps(
            {
                "found": True,
                "activeRepositoryRoot": context["root"],
                "ledgerPath": str(runs / f"{run_id}.json"),
                "reportArtifact": report_status,
                "state": value,
            },
            indent=2,
        )
    )
    return 0


def command_list(args: argparse.Namespace) -> int:
    context, _, runs = storage_paths(Path(args.repo), ensure=False)
    summaries: list[dict[str, Any]] = []
    if runs.is_dir():
        for path in sorted(runs.glob("*.json"), reverse=True):
            try:
                value = load_run(runs, path.stem)
                validate_state(value, path.stem, str(context["identity"]))
            except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
                summaries.append({"runId": path.stem, "error": str(error)})
                continue
            summaries.append(
                {
                    "runId": value["runId"],
                    "updatedAt": value["updatedAt"],
                    "mode": value["mode"],
                    "scope": value["scope"],
                    "phase": value["phase"],
                    "status": value["status"],
                    "productionVerdict": value["productionVerdict"],
                }
            )
    print(json.dumps({"repository": context["root"], "runs": summaries}, indent=2))
    return 0


def command_save(args: argparse.Namespace) -> int:
    context, storage, runs = storage_paths(Path(args.repo), ensure=True)
    run_id = resolve_run(storage, args.run)
    if run_id is None:
        raise FileNotFoundError("no review run exists; initialize one first")
    if args.input == "-":
        raw = sys.stdin.read()
    else:
        input_path = Path(args.input)
        if input_path.is_symlink():
            raise ValueError("refusing symlinked ledger input")
        raw = input_path.read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("input must be a JSON object")
    with write_lock(storage):
        existing = load_run(runs, run_id)
        validate_state(existing, run_id, str(context["identity"]))
        if existing["updatedAt"] != args.expected_updated_at:
            raise ValueError("stale ledger update; reload the run before saving")
        value["createdAt"] = existing["createdAt"]
        value["updatedAt"] = now_utc()
        value["scope"] = existing["scope"]
        value["previousRunId"] = existing.get("previousRunId")
        repository = value.get("repository")
        if isinstance(repository, dict):
            repository["identity"] = existing["repository"]["identity"]
            repository["initialRoot"] = existing["repository"]["initialRoot"]
            repository["activeRoot"] = context["root"]
            repository["storageKind"] = existing["repository"]["storageKind"]
            repository["baseRevision"] = existing["repository"]["baseRevision"]
            repository["currentRevision"] = context["revision"]
        validate_state(value, run_id, str(context["identity"]))
        if value.get("reportPath") is not None:
            report_status = report_artifact_status(value)
            if report_status != "verified":
                raise ValueError(f"report artifact is not safe to persist: {report_status}")
        write_json(runs / f"{run_id}.json", value)
        atomic_write(storage / "latest-run.txt", f"{run_id}\n".encode())
    print(
        json.dumps(
            {
                "saved": True,
                "runId": run_id,
                "updatedAt": value["updatedAt"],
                "ledgerPath": str(runs / f"{run_id}.json"),
            },
            indent=2,
        )
    )
    return 0


def expect_invalid(value: dict[str, Any], run_id: str, identity: str, label: str) -> None:
    try:
        validate_state(value, run_id, identity)
    except (TypeError, ValueError):
        return
    raise AssertionError(f"malformed ledger accepted: {label}")


def append_event(path: Path, value: str) -> None:
    descriptor = os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, f"{value}\n".encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def command_lock_probe(args: argparse.Namespace) -> int:
    storage = Path(args.storage)
    event_log = Path(args.event_log)
    release_file = Path(args.release_file)
    with write_lock(storage, timeout_seconds=10.0):
        append_event(event_log, f"enter {os.getpid()}")
        deadline = time.monotonic() + 10.0
        while not release_file.exists():
            if time.monotonic() >= deadline:
                raise ValueError("lock probe timed out waiting for release")
            time.sleep(0.02)
        append_event(event_log, f"exit {os.getpid()}")
    return 0


def command_self_test(_: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="dev-review-ledger-test-") as temporary:
        root = Path(temporary)
        repo = root / "sample"
        repo.mkdir()
        previous = os.environ.get("DEV_REVIEW_STATE_DIR")
        os.environ["DEV_REVIEW_STATE_DIR"] = str(root / "state")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                command_init(
                    argparse.Namespace(
                        repo=str(repo),
                        mode="audit",
                        scope="self-test",
                        previous_run=None,
                        base_revision=None,
                    )
                )
            context, storage, runs = storage_paths(repo, ensure=False)
            run_id = latest_run_id(storage)
            if run_id is None:
                raise AssertionError("latest run was not recorded")
            value = load_run(runs, run_id)
            original_updated_at = value["updatedAt"]
            suffix = run_id.rsplit("-", 1)[1]
            value["phase"] = "report"
            value["score"] = 8.5
            value["coverageConfidence"] = "Medium"
            value["productionVerdict"] = "Hold"
            report = root / "report.html"
            report.write_text("<!doctype html><title>Self test</title>", encoding="utf-8")
            if os.name != "nt":
                report.chmod(0o600)
            value["reportPath"] = str(report)
            value["reportSha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
            value["findings"] = [
                {
                    "id": f"DR-{suffix}-001",
                    "runId": run_id,
                    "title": "Self-test finding",
                    "scope": "fixture",
                    "evidenceRevision": "fixture-v1",
                    "affectedOutcome": "The fixture remains resumable",
                    "evidenceTrace": ["Source inspection at fixture-v1"],
                    "relevantFiles": ["fixture/example.py"],
                    "causalBasis": "The fixture records the validated source state",
                    "preservationConstraint": "Keep the stable fixture behavior",
                    "boundedDirection": "Change only the fixture boundary",
                    "effort": "Small",
                    "regressionRisk": "Low if the acceptance check passes",
                    "classification": "Fix candidate",
                    "severity": "P2 Polish",
                    "outcomeEvidence": "Source-proven",
                    "causalConfidence": "Supported cause",
                    "recommendationStrength": "Strong",
                    "status": "Open",
                    "selected": False,
                    "acceptanceChecks": ["The fixture remains valid"],
                    "owner": None,
                    "peerReviewer": None,
                    "selectionReceipt": None,
                    "implementationReceipts": None,
                }
            ]
            value["research"] = [
                {
                    "id": "research-001",
                    "question": "Does the alternate runtime preserve the fixture?",
                    "missingEvidence": "No alternate-runtime execution receipt exists",
                    "nextExperiment": "Run the fixture in the alternate disposable runtime",
                    "costRisk": "Low cost; no production data or network access",
                    "stopCondition": "Stop after one deterministic pass or reproducible failure",
                }
            ]
            input_path = root / "updated.json"
            input_path.write_text(json.dumps(value), encoding="utf-8")
            save_args = argparse.Namespace(
                repo=str(repo),
                run=run_id,
                input=str(input_path),
                expected_updated_at=original_updated_at,
            )
            with contextlib.redirect_stdout(io.StringIO()):
                command_save(save_args)
            saved = load_run(runs, run_id)
            validate_state(saved, run_id, str(context["identity"]))
            if saved["score"] != 8.5 or saved["phase"] != "report":
                raise AssertionError("saved ledger did not preserve updates")
            unsafe_input = root / "unsafe-report-save.json"
            unsafe_input.write_text(json.dumps(saved), encoding="utf-8")
            if os.name != "nt":
                report.chmod(0o644)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        command_save(
                            argparse.Namespace(
                                repo=str(repo),
                                run=run_id,
                                input=str(unsafe_input),
                                expected_updated_at=saved["updatedAt"],
                            )
                        )
                except ValueError as error:
                    if "unsafe-permissions" not in str(error):
                        raise
                else:
                    raise AssertionError("broadly readable report was persisted")
                finally:
                    report.chmod(0o600)
            original_report = report.read_bytes()
            report.write_bytes(original_report + b"\n<!-- tampered -->\n")
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    command_save(
                        argparse.Namespace(
                            repo=str(repo),
                            run=run_id,
                            input=str(unsafe_input),
                            expected_updated_at=saved["updatedAt"],
                        )
                    )
            except ValueError as error:
                if "digest-mismatch" not in str(error):
                    raise
            else:
                raise AssertionError("report digest mismatch was persisted")
            finally:
                report.write_bytes(original_report)
                if os.name != "nt":
                    report.chmod(0o600)
            report.unlink()
            show_output = io.StringIO()
            with contextlib.redirect_stdout(show_output):
                command_show(argparse.Namespace(repo=str(repo), run=run_id))
            resumed = json.loads(show_output.getvalue())
            if resumed["reportArtifact"] != "missing":
                raise AssertionError("missing report was not detected on resume")
            resumed_finding = resumed["state"]["findings"][0]
            if not resumed_finding.get("causalBasis") or not resumed_finding.get("evidenceTrace"):
                raise AssertionError("resume-critical finding evidence was not preserved")
            if os.name != "nt":
                run_path = runs / f"{run_id}.json"
                run_path.chmod(0o644)
                try:
                    command_show(argparse.Namespace(repo=str(repo), run=run_id))
                except ValueError as error:
                    if "permissions are too broad" not in str(error):
                        raise
                else:
                    raise AssertionError("broadly readable state file was accepted")
                finally:
                    run_path.chmod(0o600)
                runs.chmod(0o755)
                try:
                    command_list(argparse.Namespace(repo=str(repo)))
                except ValueError as error:
                    if "permissions are too broad" not in str(error):
                        raise
                else:
                    raise AssertionError("broadly readable state directory was accepted")
                finally:
                    runs.chmod(0o700)

            council_state = json.loads(json.dumps(saved))
            council_state["phase"] = "awaiting-selection"
            council_state["status"] = "awaiting_selection"
            council_state["reportCouncilApproval"] = {
                "reportSha256": council_state["reportSha256"],
                "candidateDigest": "c" * 64,
                "evidenceRevision": "fixture-v1",
                "approvedAt": now_utc(),
                "roundOne": ["APPROVE", "APPROVE_WITH_NITS", "APPROVE", "APPROVE"],
                "roundTwo": ["APPROVE", "APPROVE", "APPROVE", "APPROVE"],
            }
            validate_state(council_state, run_id, str(context["identity"]))
            malformed = json.loads(json.dumps(council_state))
            malformed["reportCouncilApproval"] = None
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "awaiting-selection without council approval",
            )

            def selected_state(status: str = "Selected") -> dict[str, Any]:
                selected_value = json.loads(json.dumps(saved))
                selected_value["mode"] = "Mode: Audit and improve"
                finding = selected_value["findings"][0]
                finding["selected"] = True
                finding["status"] = status
                finding["owner"] = "worker-1"
                finding["peerReviewer"] = "peer-1"
                finding["selectionReceipt"] = {
                    "selectionKey": f"{run_id}:{finding['id']}@{finding['evidenceRevision']}",
                    "authority": "User",
                    "approvedAt": now_utc(),
                }
                finding["implementationReceipts"] = {
                    "worker": None,
                    "seniorFirst": None,
                    "peer": None,
                    "seniorFinal": None,
                }
                return selected_value

            malformed = json.loads(json.dumps(saved))
            malformed["productionVerdict"] = "Ship it"
            expect_invalid(malformed, run_id, str(context["identity"]), "invalid verdict")
            malformed = json.loads(json.dumps(saved))
            malformed["findings"].append(dict(malformed["findings"][0]))
            expect_invalid(malformed, run_id, str(context["identity"]), "duplicate finding ID")
            malformed = json.loads(json.dumps(saved))
            malformed["findings"][0]["evidenceRevision"] = ""
            expect_invalid(malformed, run_id, str(context["identity"]), "missing evidence revision")
            malformed = json.loads(json.dumps(saved))
            malformed["findings"][0]["outcomeEvidence"] = "Untested risk"
            malformed["findings"][0]["causalConfidence"] = "Cause hypothesis"
            malformed["findings"][0]["recommendationStrength"] = "Speculative"
            malformed["findings"][0]["selected"] = True
            malformed["findings"][0]["status"] = "Selected"
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "low-confidence selected Fix candidate",
            )
            malformed = json.loads(json.dumps(saved))
            malformed["findings"][0]["classification"] = "Research"
            malformed["findings"][0]["status"] = "Research"
            malformed["findings"][0]["selected"] = True
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "selected Research finding",
            )
            malformed = json.loads(json.dumps(saved))
            malformed["findings"][0]["status"] = "Resolved"
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "unselected resolved finding",
            )
            malformed = selected_state()
            malformed["findings"][0]["selectionReceipt"] = None
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "selected finding without approval receipt",
            )
            malformed = selected_state()
            malformed["findings"][0]["selectionReceipt"]["selectionKey"] += "-stale"
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "selected finding with stale approval receipt",
            )
            malformed = selected_state()
            malformed["findings"][0]["peerReviewer"] = "worker-1"
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "selected finding with same owner and peer",
            )
            malformed = selected_state("Resolved")
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "resolved finding without review receipts",
            )
            intermediate = selected_state()
            intermediate["findings"][0]["implementationReceipts"] = {
                "worker": {"actor": "worker-1", "result": "PASS", "treeSha256": "b" * 64},
                "seniorFirst": {
                    "actor": "senior-1",
                    "result": "PASS",
                    "treeSha256": "b" * 64,
                },
                "peer": None,
                "seniorFinal": None,
            }
            validate_state(intermediate, run_id, str(context["identity"]))
            malformed = selected_state("Resolved")
            malformed["findings"][0]["implementationReceipts"] = {
                "worker": {"actor": "worker-1", "result": "PASS", "treeSha256": "b" * 64},
                "seniorFirst": {
                    "actor": "worker-1",
                    "result": "PASS",
                    "treeSha256": "b" * 64,
                },
                "peer": {"actor": "peer-1", "result": "APPROVE", "treeSha256": "b" * 64},
                "seniorFinal": {
                    "actor": "worker-1",
                    "result": "PASS",
                    "treeSha256": "b" * 64,
                },
            }
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "review receipts without an independent senior",
            )
            malformed = selected_state("Resolved")
            accepted_tree = "b" * 64
            malformed["findings"][0]["implementationReceipts"] = {
                "worker": {"actor": "worker-1", "result": "PASS", "treeSha256": accepted_tree},
                "seniorFirst": {
                    "actor": "senior-1",
                    "result": "PASS",
                    "treeSha256": accepted_tree,
                },
                "peer": {
                    "actor": "peer-1",
                    "result": "APPROVE",
                    "treeSha256": accepted_tree,
                },
                "seniorFinal": {
                    "actor": "senior-1",
                    "result": "PASS",
                    "treeSha256": accepted_tree,
                },
            }
            malformed["score"] = 10.0
            malformed["coverageConfidence"] = "High"
            malformed["productionVerdict"] = "Ready"
            malformed["reviewEvidence"] = "Runtime exercised"
            malformed["checks"] = [
                {
                    "name": "unrelated global check",
                    "evidenceRevision": "fixture-v1",
                    "result": "PASS",
                    "required": True,
                    "findingId": None,
                    "treeSha256": accepted_tree,
                }
            ]
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "ready verdict with unrelated passing check",
            )
            malformed = json.loads(json.dumps(saved))
            malformed["phase"] = "implementation"
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "audit-mode implementation phase",
            )
            malformed = json.loads(json.dumps(saved))
            malformed["phase"] = "complete"
            malformed["status"] = "in_progress"
            malformed["score"] = None
            malformed["coverageConfidence"] = None
            malformed["productionVerdict"] = "Ready"
            malformed["reportPath"] = None
            malformed["reportSha256"] = None
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "fabricated incomplete Ready state",
            )
            malformed = json.loads(json.dumps(council_state))
            malformed["reportCouncilApproval"]["reportSha256"] = "d" * 64
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "council approval for a different report",
            )
            malformed = json.loads(json.dumps(saved))
            malformed["findings"][0]["severity"] = "P0 Blocker"
            malformed["findings"][0]["classification"] = "Deferred"
            malformed["findings"][0]["status"] = "Deferred"
            malformed["score"] = 10.0
            malformed["productionVerdict"] = "Ready"
            malformed["reviewEvidence"] = "Runtime exercised"
            malformed["coverageConfidence"] = "High"
            malformed["checks"] = [
                {
                    "name": "required runtime check",
                    "evidenceRevision": "fixture-v1",
                    "result": "PASS",
                    "required": True,
                    "findingId": None,
                    "treeSha256": "a" * 64,
                }
            ]
            expect_invalid(malformed, run_id, str(context["identity"]), "deferred P0 ready verdict")
            malformed = json.loads(json.dumps(saved))
            malformed["productionVerdict"] = "Ready"
            malformed["score"] = 10.0
            malformed["coverageConfidence"] = "Low"
            malformed["checks"] = []
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "static low-coverage ready verdict",
            )
            malformed = json.loads(json.dumps(saved))
            malformed["productionVerdict"] = "Ready"
            malformed["reviewEvidence"] = "Runtime exercised"
            malformed["coverageConfidence"] = "High"
            malformed["checks"] = [
                {
                    "name": "required check",
                    "evidenceRevision": "fixture-v1",
                    "result": "FAIL",
                    "required": True,
                    "findingId": None,
                    "treeSha256": "a" * 64,
                }
            ]
            expect_invalid(
                malformed,
                run_id,
                str(context["identity"]),
                "ready with failed required check",
            )

            stale_args = argparse.Namespace(
                repo=str(repo),
                run=run_id,
                input=str(input_path),
                expected_updated_at=original_updated_at,
            )
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    command_save(stale_args)
            except ValueError as error:
                if "stale ledger update" not in str(error):
                    raise
            else:
                raise AssertionError("stale ledger update was accepted")

            stale_lock = storage / "write.lock"
            stale_lock.write_text(
                "pid=2147483647 created=2000-01-01T00:00:00.000000Z\n",
                encoding="utf-8",
            )
            with write_lock(storage):
                pass
            if not stale_lock.is_file() or f"pid={os.getpid()}" not in stale_lock.read_text(
                encoding="utf-8"
            ):
                raise AssertionError("dead-writer advisory lock was not safely reused")
            stale_lock.write_text("malformed prior owner metadata\n", encoding="utf-8")
            with write_lock(storage):
                pass
            with write_lock(storage):
                try:
                    with write_lock(storage, timeout_seconds=0.1):
                        raise AssertionError("overlapping writer entered the critical section")
                except ValueError as error:
                    if "locked by another writer" not in str(error):
                        raise
            if os.name != "nt":
                stale_lock.unlink()
                symlink_target = root / "lock-target"
                symlink_target.write_text("preserve\n", encoding="utf-8")
                stale_lock.symlink_to(symlink_target)
                try:
                    with write_lock(storage, timeout_seconds=0.1):
                        raise AssertionError("symlinked lock entered the critical section")
                except ValueError as error:
                    if "symlinked state lock" not in str(error):
                        raise
                stale_lock.unlink()
                if symlink_target.read_text(encoding="utf-8") != "preserve\n":
                    raise AssertionError("symlink lock target was modified")

            event_log = root / "lock-events.log"
            release_file = root / "release-lock-probes"
            probe_command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "lock-probe",
                "--storage",
                str(storage),
                "--event-log",
                str(event_log),
                "--release-file",
                str(release_file),
            ]
            first_probe = subprocess.Popen(
                probe_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            deadline = time.monotonic() + 5.0
            while not event_log.is_file() or not event_log.read_text(encoding="utf-8").strip():
                if time.monotonic() >= deadline:
                    first_probe.kill()
                    raise AssertionError("first lock probe did not enter")
                time.sleep(0.02)
            second_probe = subprocess.Popen(
                probe_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            time.sleep(0.2)
            if len(event_log.read_text(encoding="utf-8").splitlines()) != 1:
                first_probe.kill()
                second_probe.kill()
                raise AssertionError("advisory lock allowed overlapping critical sections")
            release_file.touch()
            first_output = first_probe.communicate(timeout=10)
            second_output = second_probe.communicate(timeout=10)
            if first_probe.returncode != 0 or second_probe.returncode != 0:
                raise AssertionError(
                    "lock probe failed: " + " ".join((*first_output, *second_output))
                )
            events = event_log.read_text(encoding="utf-8").splitlines()
            if [event.split()[0] for event in events] != ["enter", "exit", "enter", "exit"]:
                raise AssertionError(f"advisory lock event order is invalid: {events}")

            git = shutil.which("git")
            if git:
                primary = root / "git-primary"
                linked = root / "git-linked"
                subprocess.run([git, "init", str(primary)], check=True, capture_output=True, text=True)
                subprocess.run(
                    [git, "-C", str(primary), "config", "user.name", "Dev Review Self Test"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    [
                        git,
                        "-C",
                        str(primary),
                        "config",
                        "user.email",
                        "dev-review@example.invalid",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    [git, "-C", str(primary), "commit", "--allow-empty", "-m", "fixture"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                base_commit = run_git(primary, "rev-parse", "HEAD")
                if base_commit is None:
                    raise AssertionError("Git self-test could not resolve its base commit")
                subprocess.run(
                    [git, "-C", str(primary), "commit", "--allow-empty", "-m", "feature"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    [
                        git,
                        "-C",
                        str(primary),
                        "worktree",
                        "add",
                        "-b",
                        "dev-review-linked",
                        str(linked),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    command_init(
                        argparse.Namespace(
                            repo=str(primary),
                            mode="audit",
                            scope="linked-worktree-self-test",
                            previous_run=None,
                            base_revision=base_commit,
                        )
                    )
                linked_context, linked_storage, linked_runs = storage_paths(linked, ensure=False)
                linked_run_id = latest_run_id(linked_storage)
                if linked_run_id is None:
                    raise AssertionError("linked worktree could not discover the review run")
                list_output = io.StringIO()
                with contextlib.redirect_stdout(list_output):
                    command_list(argparse.Namespace(repo=str(linked)))
                listed = json.loads(list_output.getvalue())
                if not listed["runs"] or "error" in listed["runs"][0]:
                    raise AssertionError("linked worktree list did not validate the shared run")
                linked_value = load_run(linked_runs, linked_run_id)
                if (
                    linked_value["repository"]["baseRevision"] != base_commit
                    or linked_value["repository"]["currentRevision"] == base_commit
                ):
                    raise AssertionError("diff review did not preserve a distinct exact base revision")
                linked_input = root / "linked-update.json"
                linked_input.write_text(json.dumps(linked_value), encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    command_save(
                        argparse.Namespace(
                            repo=str(linked),
                            run=linked_run_id,
                            input=str(linked_input),
                            expected_updated_at=linked_value["updatedAt"],
                        )
                    )
                linked_saved = load_run(linked_runs, linked_run_id)
                validate_state(
                    linked_saved,
                    linked_run_id,
                    str(linked_context["identity"]),
                )
                if linked_saved["repository"]["activeRoot"] != str(linked.resolve()):
                    raise AssertionError("linked worktree save did not update the active root")
                with contextlib.redirect_stdout(io.StringIO()):
                    command_show(argparse.Namespace(repo=str(linked), run=linked_run_id))
        finally:
            if previous is None:
                os.environ.pop("DEV_REVIEW_STATE_DIR", None)
            else:
                os.environ["DEV_REVIEW_STATE_DIR"] = previous
    print("review_ledger self-test passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize a new review run")
    init_parser.add_argument("--repo", default=".", help="repository or project path")
    init_parser.add_argument("--mode", choices=sorted(MODE_NAMES), default="audit")
    init_parser.add_argument("--scope", required=True, help="bounded review scope")
    init_parser.add_argument("--previous-run", help="prior run ID for continuity")
    init_parser.add_argument(
        "--base-revision",
        help="exact Git base or merge-base commit for a diff review (defaults to HEAD)",
    )
    init_parser.set_defaults(handler=command_init)

    show_parser = subparsers.add_parser("show", help="show and validate one review run")
    show_parser.add_argument("--repo", default=".", help="repository or project path")
    show_parser.add_argument("--run", default="latest", help="run ID or latest")
    show_parser.set_defaults(handler=command_show)

    list_parser = subparsers.add_parser("list", help="list validated review run summaries")
    list_parser.add_argument("--repo", default=".", help="repository or project path")
    list_parser.set_defaults(handler=command_list)

    save_parser = subparsers.add_parser("save", help="validate and atomically save a full ledger JSON object")
    save_parser.add_argument("--repo", default=".", help="repository or project path")
    save_parser.add_argument("--run", required=True, help="explicit run ID")
    save_parser.add_argument("--expected-updated-at", required=True, help="updatedAt from the last validated read")
    save_parser.add_argument("--input", required=True, help="JSON file path or - for stdin")
    save_parser.set_defaults(handler=command_save)

    test_parser = subparsers.add_parser("self-test", help="run an isolated ledger lifecycle and adversarial validation test")
    test_parser.set_defaults(handler=command_self_test)

    probe_parser = subparsers.add_parser("lock-probe", help=argparse.SUPPRESS)
    probe_parser.add_argument("--storage", required=True)
    probe_parser.add_argument("--event-log", required=True)
    probe_parser.add_argument("--release-file", required=True)
    probe_parser.set_defaults(handler=command_lock_probe)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

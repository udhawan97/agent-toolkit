#!/usr/bin/env python3
"""Validate the dev-review package and its personal client installations."""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL_NAME = "dev-review"
DECLARED_FILES = {
    "SKILL.md",
    "agents/openai.yaml",
    "references/HTML-REPORT.md",
    "references/ORCHESTRATION.md",
    "references/REVIEW-LENSES.md",
    "scripts/review_ledger.py",
    "scripts/validate_skill.py",
}
DECLARED_DIRS = {"agents", "references", "scripts"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_entries(root: Path) -> tuple[set[str], set[str], set[str]]:
    files: set[str] = set()
    directories: set[str] = set()
    symlinks: set[str] = set()
    for path in root.rglob("*"):
        relative_path = path.relative_to(root)
        relative = relative_path.as_posix()
        if path.is_symlink():
            symlinks.add(relative)
        elif (
            "__pycache__" in relative_path.parts
            and path.is_file()
            and path.suffix == ".pyc"
        ):
            continue
        elif path.is_file():
            files.add(relative)
        elif path.is_dir() and "__pycache__" not in relative_path.parts:
            directories.add(relative)
    return files, directories, symlinks


def frontmatter(text: str) -> str:
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md frontmatter is missing or not closed")
    return match.group(1)


def simple_frontmatter_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(frontmatter(text).splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            raise ValueError(f"SKILL.md:{number}: frontmatter must be a flat mapping")
        key, value = line.split(":", 1)
        if key in values:
            raise ValueError(f"SKILL.md:{number}: duplicate frontmatter key: {key}")
        values[key] = value.strip().strip("\"'")
    return values


def parse_scalar(raw: str) -> object:
    value = raw.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.startswith(("\"", "'")):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as error:
            raise ValueError(f"invalid quoted YAML scalar: {value}") from error
    return value


def parse_limited_yaml(text: str, label: str) -> dict[str, object]:
    result: dict[str, object] = {}
    current: dict[str, object] | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  "):
            if line.startswith("   ") or current is None or ":" not in line:
                raise ValueError(f"{label}:{number}: unsupported YAML structure")
            key, raw = line.strip().split(":", 1)
            if not key or key in current:
                raise ValueError(f"{label}:{number}: duplicate or empty key")
            current[key] = parse_scalar(raw)
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            raise ValueError(f"{label}:{number}: unsupported YAML structure")
        key, raw = line.split(":", 1)
        if not key or key in result:
            raise ValueError(f"{label}:{number}: duplicate or empty key")
        if raw.strip():
            result[key] = parse_scalar(raw)
            current = None
        else:
            nested: dict[str, object] = {}
            result[key] = nested
            current = nested
    return result


def load_yaml_mapping(text: str, label: str) -> dict[str, object]:
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        return parse_limited_yaml(text, label)
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise ValueError(f"{label}: invalid YAML: {error}") from error
    if not isinstance(value, dict):
        raise TypeError(f"{label}: expected a YAML mapping")
    return value


def markdown_links(root: Path) -> list[str]:
    errors: list[str] = []
    for markdown_path in root.rglob("*.md"):
        text = markdown_path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            relative_target = target.split("#", 1)[0]
            candidate = (markdown_path.parent / relative_target).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                errors.append(f"link leaves package: {markdown_path.relative_to(root)} -> {target}")
                continue
            if not candidate.exists():
                errors.append(f"broken link: {markdown_path.relative_to(root)} -> {target}")
    return errors


def require_phrases(path: Path, phrases: tuple[str, ...], errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for phrase in phrases:
        if phrase not in text:
            errors.append(f"{path.name} missing required contract phrase: {phrase}")


def validate_package(root: Path) -> list[str]:
    errors: list[str] = []
    files, directories, symlinks = package_entries(root)
    for relative in sorted(DECLARED_FILES - files):
        errors.append(f"missing declared file: {relative}")
    for relative in sorted(files - DECLARED_FILES):
        errors.append(f"unexpected file: {relative}")
    for relative in sorted(DECLARED_DIRS - directories):
        errors.append(f"missing declared directory: {relative}")
    for relative in sorted(directories - DECLARED_DIRS):
        errors.append(f"unexpected directory: {relative}")
    for relative in sorted(symlinks):
        errors.append(f"unexpected package symlink: {relative}")

    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        return errors
    text = skill_path.read_text(encoding="utf-8")
    try:
        values = simple_frontmatter_values(text)
    except ValueError as error:
        errors.append(str(error))
        return errors
    portable_keys = {"name", "description", "license"}
    claude_keys = portable_keys | {"disable-model-invocation"}
    if set(values) not in {frozenset(portable_keys), frozenset(claude_keys)}:
        errors.append("SKILL.md frontmatter contains unsupported keys")
    if values.get("name") != SKILL_NAME:
        errors.append(f"SKILL.md name must be {SKILL_NAME}")
    description = values.get("description", "")
    if not description or "three specialist" not in description or "selected" not in description:
        errors.append("SKILL.md description must identify the three-specialist and selection boundary")
    if values.get("license") != "MIT":
        errors.append("SKILL.md license must be MIT")
    if "disable-model-invocation" in values and values["disable-model-invocation"] != "true":
        errors.append("disable-model-invocation must be true when present")

    require_phrases(
        skill_path,
        (
            "Mode: Audit",
            "Mode: Audit and improve",
            "Mode: Re-verify",
            "exactly three",
            "Which findings would you like me to improve?",
            "Confirmed cause",
            "Supported cause",
            "Cause hypothesis",
            "Merge-ready",
            "two failed correction loops",
            "council-review",
            "credentialed or live egress",
            "Deny external-network access",
            "never repurpose `HOME`",
            "exact private report content and digest",
            "Only a `Fix candidate` with `Verified` or `Source-proven`",
            "--base-revision <exact-base-or-merge-base>",
            "reportCouncilApproval",
            "<skill-root>/scripts/review_ledger.py",
        ),
        errors,
    )
    require_phrases(
        root / "references" / "ORCHESTRATION.md",
        (
            "exactly three real subagents",
            "Worker → senior → peer → senior",
            "one mistake wearing three hats",
            "Allow at most two correction loops",
            "Ready with follow-ups",
            "Durable ledger",
            "stable repository identity",
            "persistent OS advisory lock",
        ),
        errors,
    )
    require_phrases(
        root / "references" / "REVIEW-LENSES.md",
        (
            "Product promise and user journeys",
            "Domain and architecture",
            "Correctness and data integrity",
            "Security, privacy, and supply chain",
            "Zero material findings is valid",
        ),
        errors,
    )
    require_phrases(
        root / "references" / "HTML-REPORT.md",
        (
            "zero external requests",
            "script-src 'none'",
            "x.x / 10",
            "Coverage confidence",
            "Friendly roast",
            "same-document `#fragment` anchors",
            "320, 375, 414, and 768",
        ),
        errors,
    )

    openai_path = root / "agents" / "openai.yaml"
    if openai_path.is_file():
        try:
            openai = load_yaml_mapping(openai_path.read_text(encoding="utf-8"), "agents/openai.yaml")
        except (TypeError, ValueError) as error:
            errors.append(str(error))
        else:
            if set(openai) != {"interface", "policy"}:
                errors.append("agents/openai.yaml must contain only interface and policy")
            interface = openai.get("interface")
            policy = openai.get("policy")
            if not isinstance(interface, dict) or set(interface) != {
                "display_name",
                "short_description",
                "default_prompt",
            }:
                errors.append("agents/openai.yaml interface keys are invalid")
            else:
                if interface.get("display_name") != "Dev Review":
                    errors.append("agents/openai.yaml display_name is stale")
                short = interface.get("short_description")
                prompt = interface.get("default_prompt")
                if not isinstance(short, str) or not 25 <= len(short) <= 64:
                    errors.append("agents/openai.yaml short_description must be 25-64 characters")
                if not isinstance(prompt, str) or not prompt.startswith("Use $dev-review"):
                    errors.append("agents/openai.yaml default_prompt must invoke $dev-review")
            if policy != {"allow_implicit_invocation": False}:
                errors.append("agents/openai.yaml must keep invocation explicit")

    for script_name in ("scripts/review_ledger.py", "scripts/validate_skill.py"):
        script_path = root / script_name
        if script_path.is_file():
            try:
                compile(script_path.read_text(encoding="utf-8"), str(script_path), "exec")
            except SyntaxError as error:
                errors.append(f"{script_name} syntax error: {error}")

    errors.extend(markdown_links(root))
    return errors


def skill_body(text: str) -> str:
    match = re.match(r"^---\n.*?\n---(?:\n|$)(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md frontmatter is missing or not closed")
    return match.group(1)


def validate_install(root: Path, install: Path, label: str) -> list[str]:
    if install.is_symlink():
        try:
            resolved = install.resolve(strict=True)
        except (FileNotFoundError, OSError, RuntimeError) as error:
            return [f"{label} installation symlink cannot be resolved: {error}"]
        return [] if resolved == root.resolve() else [f"{label} symlink does not resolve to canonical package"]
    if not install.exists():
        return [f"{label} installation missing: {install}"]
    if not install.is_dir():
        return [f"{label} installation is not a directory: {install}"]

    errors: list[str] = []
    files, directories, symlinks = package_entries(install)
    for relative in sorted(DECLARED_FILES - files):
        errors.append(f"{label} copy missing: {relative}")
    for relative in sorted(files - DECLARED_FILES):
        errors.append(f"{label} copy has unexpected file: {relative}")
    for relative in sorted(DECLARED_DIRS - directories):
        errors.append(f"{label} copy missing directory: {relative}")
    for relative in sorted(directories - DECLARED_DIRS):
        errors.append(f"{label} copy has unexpected directory: {relative}")
    for relative in sorted(symlinks):
        errors.append(f"{label} copy has unexpected symlink: {relative}")
    for relative in sorted(DECLARED_FILES & files):
        if relative == "SKILL.md" and label == "Claude":
            installed_text = (install / relative).read_text(encoding="utf-8")
            canonical_text = (root / relative).read_text(encoding="utf-8")
            try:
                installed_values = simple_frontmatter_values(installed_text)
            except ValueError as error:
                errors.append(f"Claude SKILL.md: {error}")
                continue
            if installed_values != {
                "name": SKILL_NAME,
                "description": simple_frontmatter_values(canonical_text)["description"],
                "license": "MIT",
                "disable-model-invocation": "true",
            }:
                errors.append("Claude SKILL.md frontmatter is not the explicit-only adapter")
            if skill_body(installed_text) != skill_body(canonical_text):
                errors.append("Claude SKILL.md body differs from canonical")
        elif digest(install / relative) != digest(root / relative):
            errors.append(f"{label} copy differs from canonical: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-install", action="store_true")
    parser.add_argument("--skip-ledger-test", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    errors = validate_package(root)
    checked = [f"package: {root}"]

    if not args.skip_ledger_test and not errors:
        completed = subprocess.run(
            [sys.executable, str(root / "scripts" / "review_ledger.py"), "self-test"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0:
            errors.append("review_ledger.py self-test failed: " + completed.stderr.strip())
        else:
            checked.append("ledger self-test")

    if args.check_install:
        home = Path.home()
        codex_root = Path(os.environ.get("CODEX_HOME", str(home / ".codex"))).expanduser()
        claude_root = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(home / ".claude"))).expanduser()
        codex_install = codex_root / "skills" / SKILL_NAME
        claude_install = claude_root / "skills" / SKILL_NAME
        try:
            loaded_values = simple_frontmatter_values((root / "SKILL.md").read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError) as error:
            errors.append(f"cannot identify loaded package variant: {error}")
            canonical_root = root
        else:
            if loaded_values.get("disable-model-invocation") == "true":
                if codex_install.is_symlink():
                    try:
                        canonical_root = codex_install.resolve(strict=True)
                    except (FileNotFoundError, OSError, RuntimeError) as error:
                        errors.append(f"Codex installation cannot identify canonical package: {error}")
                        canonical_root = root
                elif codex_install.is_dir():
                    canonical_root = codex_install.resolve()
                else:
                    errors.append("Claude adapter cannot find the canonical Codex package")
                    canonical_root = root
            else:
                canonical_root = root
        if canonical_root.resolve() != root.resolve():
            canonical_errors = validate_package(canonical_root)
            errors.extend(f"canonical package: {error}" for error in canonical_errors)
            checked.append(f"canonical package: {canonical_root}")
        for install, label in (
            (codex_install, "Codex"),
            (claude_install, "Claude"),
        ):
            errors.extend(validate_install(canonical_root, install, label))
            checked.append(f"{label}: {install}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Skill validation passed")
    for item in checked:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

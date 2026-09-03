from __future__ import annotations

import io
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import uuid
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, env: dict[str, str], check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, env=env, check=False, text=True, capture_output=True)
    if check and completed.returncode != 0:
        raise AssertionError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def load_agent_kit():
    name = f"agent_kit_test_{uuid.uuid4().hex}"
    loader = SourceFileLoader(name, str(ROOT / "bin" / "agent-kit"))
    spec = spec_from_loader(name, loader)
    if spec is None:
        raise RuntimeError("Unable to load bin/agent-kit for testing")
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


def load_agent_upstreams():
    name = f"agent_upstreams_test_{uuid.uuid4().hex}"
    loader = SourceFileLoader(name, str(ROOT / "bin" / "agent-upstreams"))
    spec = spec_from_loader(name, loader)
    if spec is None:
        raise RuntimeError("Unable to load bin/agent-upstreams for testing")
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


class LauncherRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="agent-toolkit-launcher-test-")
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.seed = self.root / "seed"
        self.source = self.root / "managed-source"
        self.home = self.root / "home"
        self.fake_bin = self.root / "fake-bin"
        self.home.mkdir()
        self.fake_bin.mkdir()

        base_env = os.environ.copy()
        run(["git", "init", "--bare", str(self.remote)], env=base_env)
        run(["git", "init", "-b", "stable", str(self.seed)], env=base_env)
        run(["git", "-C", str(self.seed), "config", "user.name", "Agent Toolkit Tests"], env=base_env)
        run(["git", "-C", str(self.seed), "config", "user.email", "tests@users.noreply.github.com"], env=base_env)
        (self.seed / "version.txt").write_text("one\n", encoding="utf-8")
        run(["git", "-C", str(self.seed), "add", "version.txt"], env=base_env)
        run(["git", "-C", str(self.seed), "commit", "-m", "version one"], env=base_env)
        run(["git", "-C", str(self.seed), "remote", "add", "origin", str(self.remote)], env=base_env)
        run(["git", "-C", str(self.seed), "push", "-u", "origin", "stable"], env=base_env)

        self.env = os.environ.copy()
        self.env.update(
            {
                "HOME": str(self.home),
                "AGENT_KIT_REPO": "agent-toolkit-tests/agent-toolkit",
                "AGENT_KIT_REPO_URL": self.remote.as_uri(),
                "AGENT_KIT_CHANNEL": "stable",
                "AGENT_KIT_SOURCE_DIR": str(self.source),
                "PATH": str(self.fake_bin) + os.pathsep + self.env["PATH"],
            }
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def advance_remote(self) -> str:
        with (self.seed / "version.txt").open("a", encoding="utf-8") as handle:
            handle.write("two\n")
        run(["git", "-C", str(self.seed), "add", "version.txt"], env=self.env)
        run(["git", "-C", str(self.seed), "commit", "-m", "version two"], env=self.env)
        run(["git", "-C", str(self.seed), "push", "origin", "stable"], env=self.env)
        return run(["git", "-C", str(self.seed), "rev-parse", "HEAD"], env=self.env).stdout.strip()

    def assert_update_and_ahead_refusal(self, command: list[str]) -> None:
        run([*command, "install"], env=self.env)
        shallow = run(
            ["git", "-C", str(self.source), "rev-parse", "--is-shallow-repository"], env=self.env
        ).stdout.strip()
        self.assertEqual(shallow, "true")

        upstream_head = self.advance_remote()
        run([*command, "update"], env=self.env)
        managed_head = run(["git", "-C", str(self.source), "rev-parse", "HEAD"], env=self.env).stdout.strip()
        self.assertEqual(managed_head, upstream_head)

        (self.source / "local-only.txt").write_text("do not execute me\n", encoding="utf-8")
        run(["git", "-C", str(self.source), "config", "user.name", "Agent Toolkit Tests"], env=self.env)
        run(
            ["git", "-C", str(self.source), "config", "user.email", "tests@users.noreply.github.com"],
            env=self.env,
        )
        run(["git", "-C", str(self.source), "add", "local-only.txt"], env=self.env)
        run(["git", "-C", str(self.source), "commit", "-m", "local ahead"], env=self.env)
        refused = run([*command, "update"], env=self.env, check=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("does not exactly match", refused.stdout + refused.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX launcher runs on Linux and macOS")
    def test_posix_launcher_updates_shallow_clone_and_refuses_ahead_head(self) -> None:
        fake_python = self.fake_bin / "python3"
        fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        fake_python.chmod(0o755)
        self.assert_update_and_ahead_refusal(["sh", str(ROOT / "bin" / "setup")])

    @unittest.skipIf(os.name == "nt", "POSIX launcher runs on Linux and macOS")
    def test_posix_launcher_can_disable_automatic_prerequisite_install(self) -> None:
        env = self.env | {
            "AGENT_KIT_AUTO_PREREQS": "0",
            "PATH": str(self.fake_bin),
        }
        refused = run(["/bin/sh", str(ROOT / "bin" / "setup")], env=env, check=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("automatic prerequisite setup is disabled", refused.stdout + refused.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX launcher runs on Linux and macOS")
    def test_posix_one_line_command_refreshes_active_installation(self) -> None:
        log = self.root / "python-arguments.log"
        fake_python = self.fake_bin / "python3"
        fake_python.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$AGENT_KIT_PYTHON_LOG\"\nexit 0\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        state = self.home / ".agent-toolkit" / "state.json"
        state.parent.mkdir()
        state.write_text(
            json.dumps({"clients": {"codex": {"status": "active"}}}) + "\n",
            encoding="utf-8",
        )
        env = self.env | {"AGENT_KIT_PYTHON_LOG": str(log)}
        result = run(["sh", str(ROOT / "bin" / "setup")], env=env)
        self.assertIn("existing installation found; refreshing it", result.stdout)
        calls = log.read_text(encoding="utf-8").splitlines()
        self.assertTrue(any("bin/agent-kit update" in call for call in calls))
        self.assertIn("bin/agent-kit doctor", calls[-1])

    @unittest.skipIf(os.name == "nt", "POSIX launcher runs on Linux and macOS")
    def test_posix_launcher_delegates_auto_update_without_running_doctor(self) -> None:
        log = self.root / "python-arguments.log"
        fake_python = self.fake_bin / "python3"
        fake_python.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$AGENT_KIT_PYTHON_LOG\"\nexit 0\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        env = self.env | {"AGENT_KIT_PYTHON_LOG": str(log)}
        run(
            ["sh", str(ROOT / "bin" / "setup"), "auto-update", "status"],
            env=env,
        )
        calls = log.read_text(encoding="utf-8").splitlines()
        delegated = [call for call in calls if "bin/agent-kit" in call]
        self.assertEqual(len(delegated), 1)
        self.assertIn("bin/agent-kit auto-update status", delegated[0])

    @unittest.skipIf(os.name == "nt", "POSIX launcher runs on Linux and macOS")
    def test_posix_launcher_requires_python_venv_capability(self) -> None:
        fake_python = self.fake_bin / "python3"
        fake_python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        fake_python.chmod(0o755)
        fake_git = self.fake_bin / "git"
        fake_git.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        fake_git.chmod(0o755)
        env = self.env | {
            "AGENT_KIT_AUTO_PREREQS": "0",
            "PATH": str(self.fake_bin),
        }
        refused = run(["/bin/sh", str(ROOT / "bin" / "setup")], env=env, check=False)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("venv support", refused.stdout + refused.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX launcher runs on Linux and macOS")
    def test_posix_launcher_preserves_legacy_checkout_across_sanitized_root(self) -> None:
        fake_python = self.fake_bin / "python3"
        fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        fake_python.chmod(0o755)
        command = ["sh", str(ROOT / "bin" / "setup")]
        run([*command, "install"], env=self.env)
        legacy_head = run(["git", "-C", str(self.source), "rev-parse", "HEAD"], env=self.env).stdout.strip()

        replacement = self.root / "replacement"
        run(["git", "init", "-b", "stable", str(replacement)], env=self.env)
        run(["git", "-C", str(replacement), "config", "user.name", "Agent Toolkit Tests"], env=self.env)
        run(["git", "-C", str(replacement), "config", "user.email", "tests@users.noreply.github.com"], env=self.env)
        (replacement / "version.txt").write_text("privacy-scrubbed root\n", encoding="utf-8")
        run(["git", "-C", str(replacement), "add", "version.txt"], env=self.env)
        run(["git", "-C", str(replacement), "commit", "-m", "sanitized root"], env=self.env)
        run(["git", "-C", str(replacement), "remote", "add", "origin", str(self.remote)], env=self.env)
        run(["git", "-C", str(replacement), "push", "--force", "origin", "stable"], env=self.env)

        migration_env = self.env | {"AGENT_KIT_LEGACY_ROOT": legacy_head}
        run([*command, "update"], env=migration_env)
        self.assertEqual((self.source / "version.txt").read_text(encoding="utf-8"), "privacy-scrubbed root\n")
        backups = list(self.root.glob("managed-source.legacy-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "version.txt").read_text(encoding="utf-8"), "one\n")

    @unittest.skipUnless(os.name == "nt", "PowerShell launcher runs on Windows")
    def test_powershell_launcher_updates_shallow_clone_and_refuses_ahead_head(self) -> None:
        if not shutil.which("pwsh"):
            self.skipTest("pwsh is not available")
        self.source.mkdir()
        (self.fake_bin / "py.cmd").write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
        self.assert_update_and_ahead_refusal(
            ["pwsh", "-NoProfile", "-File", str(ROOT / "bin" / "setup.ps1")]
        )


class ReceiptSafetyTests(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "Symlink behavior is verified on POSIX hosts")
    def test_doctor_refuses_symlinked_receipt_parent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-state-test-") as temp:
            root = Path(temp)
            home = root / "home"
            real_state = root / "real-state"
            home.mkdir()
            real_state.mkdir()
            (real_state / "state.json").write_text(
                json.dumps({"schemaVersion": 2, "clients": {}}) + "\n", encoding="utf-8"
            )
            (home / ".agent-toolkit").symlink_to(real_state, target_is_directory=True)
            env = os.environ.copy()
            env["HOME"] = str(home)
            result = run([sys.executable, str(ROOT / "bin" / "agent-kit"), "doctor"], env=env, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to access toolkit state through a symlink", result.stdout + result.stderr)


class AutomaticUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_agent_kit()

    def test_auto_update_requires_a_github_sourced_install(self) -> None:
        with (
            patch.object(
                self.module,
                "load_state",
                return_value={"source": {"kind": "local", "path": "/reviewed/source"}},
            ),
            self.assertRaisesRegex(self.module.ToolkitError, "GitHub source"),
        ):
            self.module.auto_update_source()

    def test_auto_update_enable_writes_private_permissioned_configuration(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-auto-update-") as temporary:
            root = Path(temporary)
            state = root / "state"
            automatic = state / "auto-update"
            config = automatic / "config.json"
            log = automatic / "update.log"
            source = {
                "repo": "example/agent-toolkit",
                "channel": "stable",
                "root": str(root / "managed-source"),
            }
            with (
                patch.object(self.module, "STATE_DIR", state),
                patch.object(self.module, "AUTO_UPDATE_DIR", automatic),
                patch.object(self.module, "AUTO_UPDATE_CONFIG", config),
                patch.object(self.module, "AUTO_UPDATE_LOG", log),
                patch.object(self.module, "auto_update_source", return_value=source),
                patch.object(self.module, "auto_update_platform", return_value="macos"),
                patch.object(self.module, "auto_update_config", return_value=None),
                patch.object(
                    self.module,
                    "schedule_auto_update",
                    return_value=[str(root / "scheduled.plist")],
                ),
            ):
                self.module.command_auto_update(
                    SimpleNamespace(auto_action="enable", frequency="weekly")
                )
            payload = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(payload["frequency"], "weekly")
            self.assertEqual(payload["source"], source)
            wrapper = Path(payload["wrapper"])
            self.assertTrue(wrapper.is_file())
            wrapper_text = wrapper.read_text(encoding="utf-8")
            self.assertIn("AGENT_KIT_AUTO_PREREQS=0", wrapper_text)
            self.assertIn("export PATH=", wrapper_text)
            if os.name != "nt":
                self.assertEqual(wrapper.stat().st_mode & 0o777, 0o700)
                self.assertEqual(config.stat().st_mode & 0o777, 0o600)
                self.assertEqual(log.stat().st_mode & 0o777, 0o600)

    def test_auto_update_parser_supports_enable_disable_status_and_run(self) -> None:
        parser = self.module.build_parser()
        enabled = parser.parse_args(["auto-update", "enable", "--frequency", "daily"])
        self.assertEqual((enabled.auto_action, enabled.frequency), ("enable", "daily"))
        for action in ("disable", "status", "run"):
            parsed = parser.parse_args(["auto-update", action])
            self.assertEqual(parsed.auto_action, action)

    def test_macos_schedule_generation_is_current_user_and_weekly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-launchd-") as temporary:
            root = Path(temporary)
            home = root / "home"
            home.mkdir()
            wrapper = root / "run-update.sh"
            wrapper.write_text("#!/bin/sh\n", encoding="utf-8")
            log = root / "update.log"
            source = {"repo": "example/toolkit", "channel": "stable", "root": str(root)}
            with (
                patch.object(self.module.Path, "home", return_value=home),
                patch.object(self.module, "AUTO_UPDATE_LOG", log),
                patch.object(self.module.subprocess, "run") as raw_run,
                patch.object(self.module, "run") as checked_run,
                patch.object(self.module.os, "getuid", return_value=501, create=True),
            ):
                paths = self.module.schedule_auto_update(
                    source, "weekly", "macos", wrapper
                )
            plist_path = home / "Library" / "LaunchAgents" / "com.agent-toolkit.update.plist"
            self.assertEqual(paths, [str(plist_path)])
            payload = plistlib.loads(plist_path.read_bytes())
            self.assertEqual(payload["ProgramArguments"], ["/bin/sh", str(wrapper)])
            self.assertEqual(
                payload["StartCalendarInterval"],
                {"Hour": 9, "Minute": 0, "Weekday": 2},
            )
            self.assertEqual(payload["StandardOutPath"], str(log))
            self.assertEqual(plist_path.stat().st_mode & 0o777, 0o600)
            self.assertIn("bootout", raw_run.call_args.args[0])
            self.assertIn("bootstrap", checked_run.call_args.args[0])

    def test_linux_schedule_generation_uses_a_persistent_user_timer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-systemd-") as temporary:
            root = Path(temporary)
            home = root / "home"
            home.mkdir()
            wrapper = root / "run update.sh"
            wrapper.write_text("#!/bin/sh\n", encoding="utf-8")
            source = {"repo": "example/toolkit", "channel": "stable", "root": str(root)}
            with (
                patch.object(self.module.Path, "home", return_value=home),
                patch.object(self.module.shutil, "which", return_value="/usr/bin/systemctl"),
                patch.object(self.module, "run") as checked_run,
            ):
                paths = self.module.schedule_auto_update(
                    source, "daily", "linux", wrapper
                )
            unit_root = home / ".config" / "systemd" / "user"
            service = unit_root / "agent-toolkit-update.service"
            timer = unit_root / "agent-toolkit-update.timer"
            self.assertEqual(paths, [str(service), str(timer)])
            self.assertIn(
                f"ExecStart=/bin/sh {self.module.systemd_quote(str(wrapper))}",
                service.read_text(encoding="utf-8"),
            )
            timer_text = timer.read_text(encoding="utf-8")
            self.assertIn("OnCalendar=*-*-* 09:00:00", timer_text)
            self.assertIn("Persistent=true", timer_text)
            self.assertIn("RandomizedDelaySec=1h", timer_text)
            self.assertEqual(checked_run.call_count, 2)

    def test_windows_schedule_generation_uses_current_user_task(self) -> None:
        source = {"repo": "example/toolkit", "channel": "stable", "root": "C:/Toolkit"}
        wrapper = Path("C:/Toolkit/run-update.ps1")

        def executable(name: str) -> str | None:
            return {
                "schtasks.exe": "C:/Windows/System32/schtasks.exe",
                "powershell.exe": "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
            }.get(name)

        with (
            patch.object(self.module.shutil, "which", side_effect=executable),
            patch.object(self.module, "run") as checked_run,
        ):
            paths = self.module.schedule_auto_update(
                source, "weekly", "windows", wrapper
            )
        self.assertEqual(paths, [])
        command = checked_run.call_args.args[0]
        self.assertEqual(command[0], "C:/Windows/System32/schtasks.exe")
        self.assertIn("AgentToolkitUpdate", command)
        self.assertIn("WEEKLY", command)
        self.assertIn("MON", command)
        self.assertNotIn("/RU", command)


class UpstreamSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_agent_upstreams()

    def test_profiles_reference_only_cataloged_upstreams(self) -> None:
        catalog = json.loads((ROOT / "catalog" / "upstreams.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["schemaVersion"], 1)
        bundles = catalog["bundles"]
        for profile in ("recommended", "skills-only", "full"):
            data = json.loads((ROOT / "profiles" / f"{profile}.json").read_text(encoding="utf-8"))
            self.assertTrue(data["guidance"])
            self.assertFalse(set(data["upstreams"]) - set(bundles))
        self.assertEqual(bundles["openai-essentials"]["kind"], "codex-official")

    def test_frontend_skill_sources_are_allowlisted_without_claiming_ownership(self) -> None:
        catalog = json.loads((ROOT / "catalog" / "upstreams.json").read_text(encoding="utf-8"))
        bundles = catalog["bundles"]
        self.assertEqual(
            bundles["hallmark"]["skills"],
            {"hallmark": "skills/hallmark"},
        )
        self.assertEqual(bundles["hallmark"]["repository"], "nutlope/hallmark")
        self.assertEqual(
            bundles["vercel-frontend-skills"]["skills"],
            {
                "composition-patterns": "skills/composition-patterns",
                "react-best-practices": "skills/react-best-practices",
                "web-design-guidelines": "skills/web-design-guidelines",
            },
        )
        for profile in ("recommended", "skills-only", "full"):
            data = json.loads((ROOT / "profiles" / f"{profile}.json").read_text(encoding="utf-8"))
            self.assertTrue({"hallmark", "vercel-frontend-skills"}.issubset(data["upstreams"]))

    def test_selected_skills_package_discovers_only_allowlisted_trees(self) -> None:
        bundle = {
            "displayName": "Frontend Test",
            "skillRoot": "skills",
            "skills": {"selected": "skills/selected"},
        }
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-selected-skills-") as temporary:
            checkout = Path(temporary)
            for name in ("selected", "not-selected"):
                skill = checkout / "skills" / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
            self.assertEqual(
                self.module.discover_skill_package(
                    checkout, bundle, bundle_name="frontend-test"
                ),
                {"selected": "skills/selected"},
            )

    def test_selected_skills_package_receipts_its_own_bundle_identity(self) -> None:
        bundle = {
            "displayName": "Frontend Test",
            "repository": "example/frontend-test",
            "ref": "main",
            "skillRoot": "skills",
            "skills": {"selected": "skills/selected"},
            "clients": ["codex"],
        }
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-selected-receipt-") as temporary:
            root = Path(temporary)
            home = root / "home"
            checkout = root / "checkout"
            skill = checkout / "skills" / "selected"
            skill.mkdir(parents=True)
            home.mkdir()
            (skill / "SKILL.md").write_text("---\nname: selected\n---\n", encoding="utf-8")
            state = home / ".agent-toolkit"
            with (
                patch.object(self.module.Path, "home", return_value=home),
                patch.object(self.module, "STATE_DIR", state),
                patch.object(self.module, "STATE_FILE", state / "upstreams.json"),
                patch.object(self.module, "ensure_tracked_skills_checkout", return_value=checkout),
                patch.object(self.module, "git_value", return_value="a" * 40),
            ):
                resolved = self.module.install_skills_package(
                    bundle,
                    ["codex"],
                    False,
                    None,
                    adopt_existing=False,
                    profile="recommended",
                    bundle_name="frontend-test",
                )
            receipt = json.loads((state / "upstreams.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["bundles"], ["frontend-test"])
            self.assertEqual(receipt["resolved"]["frontend-test"]["skills"], resolved["skills"])

    def test_public_personal_skill_manifest_matches_plugin_payload(self) -> None:
        catalog = json.loads(
            (ROOT / "catalog" / "personal-skills.json").read_text(encoding="utf-8")
        )
        plugin = ROOT / "plugins" / catalog["plugin"] / "skills"
        packaged = {path.parent.name for path in plugin.glob("*/SKILL.md")}
        self.assertEqual(set(catalog["skills"]), packaged)
        claude = ROOT / "plugins" / catalog["plugin"] / "claude" / "skills"
        self.assertEqual(set(catalog["skills"]), {path.parent.name for path in claude.glob("*/SKILL.md")})
        self.assertEqual(
            {metadata["scope"] for metadata in catalog["skills"].values()},
            {"general", "public-product-guardrail"},
        )
        self.assertNotIn("hallmark", catalog["skills"])
        self.assertIn("main-cleanup", catalog["skills"])

    def test_action_bearing_skills_are_explicit_only_in_both_clients(self) -> None:
        plugin = ROOT / "plugins" / "evidence-workflows" / "skills"
        claude = ROOT / "plugins" / "evidence-workflows" / "claude" / "skills"
        for name in (
            "dev-review",
            "improve-userflow-design",
            "loop-refine-release",
            "main-cleanup",
            "releasegit",
            "tech-debt",
        ):
            skill = (claude / name / "SKILL.md").read_text(encoding="utf-8")
            codex = (plugin / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertIn("disable-model-invocation: true", skill)
            self.assertIn("allow_implicit_invocation: false", codex)

    def test_dev_review_packaged_validators_and_ledger_self_tests_pass(self) -> None:
        plugin = ROOT / "plugins" / "evidence-workflows"
        for skill_root in (
            plugin / "skills" / "dev-review",
            plugin / "claude" / "skills" / "dev-review",
        ):
            imported = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        f"import sys; sys.path.insert(0, "
                        f"{str(skill_root / 'scripts')!r}); import review_ledger"
                    ),
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(imported.returncode, 0, imported.stdout + imported.stderr)
            completed = subprocess.run(
                [sys.executable, str(skill_root / "scripts" / "validate_skill.py")],
                check=False,
                text=True,
                capture_output=True,
                timeout=90,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("ledger self-test", completed.stdout)
            authored_cache_file = skill_root / "scripts" / "__pycache__" / "authored.txt"
            authored_cache_file.write_text("must not be hidden\n", encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(skill_root / "scripts" / "validate_skill.py")],
                check=False,
                text=True,
                capture_output=True,
                timeout=90,
            )
            authored_cache_file.unlink()
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("unexpected file", rejected.stdout + rejected.stderr)
        canonical_cache_file = (
            plugin / "skills" / "dev-review" / "scripts" / "__pycache__" / "authored.txt"
        )
        canonical_cache_file.write_text("must not be hidden\n", encoding="utf-8")
        rejected_repository = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "agent-kit"), "validate"],
            check=False,
            text=True,
            capture_output=True,
            timeout=90,
        )
        canonical_cache_file.unlink()
        self.assertNotEqual(rejected_repository.returncode, 0)
        self.assertIn("supporting files differ", rejected_repository.stdout + rejected_repository.stderr)
        repository_validation = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "agent-kit"), "validate"],
            check=False,
            text=True,
            capture_output=True,
            timeout=90,
        )
        self.assertEqual(
            repository_validation.returncode,
            0,
            repository_validation.stdout + repository_validation.stderr,
        )

    def test_claude_adapter_only_allows_invocation_control_frontmatter_difference(self) -> None:
        module = load_agent_kit()
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-adapter-frontmatter-") as temporary:
            root = Path(temporary)
            canonical = root / "canonical" / "sample"
            adapted = root / "adapted" / "sample"
            canonical.mkdir(parents=True)
            adapted.mkdir(parents=True)
            (canonical / "SKILL.md").write_text(
                "---\nname: sample\ndescription: Canonical description.\nlicense: MIT\n---\n\n# Sample\n",
                encoding="utf-8",
            )
            (adapted / "SKILL.md").write_text(
                "---\nname: sample\ndescription: Drifted description.\nlicense: MIT\n---\n\n# Sample\n",
                encoding="utf-8",
            )
            errors: list[str] = []
            with patch.object(module, "ROOT", root):
                module.validate_claude_adapter(root / "canonical", root / "adapted", errors)
            self.assertIn(
                "Codex and Claude skill frontmatter differs beyond invocation control: sample",
                errors,
            )

    def test_skill_validation_checks_links_in_nested_reference_docs(self) -> None:
        module = load_agent_kit()
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-skill-links-") as temporary:
            root = Path(temporary)
            skill = root / "plugins" / "example" / "skills" / "sample" / "SKILL.md"
            reference = skill.parent / "references" / "guide.md"
            reference.parent.mkdir(parents=True)
            skill.write_text(
                "---\nname: sample\ndescription: Example skill.\nlicense: MIT\n---\n\n# Sample\n",
                encoding="utf-8",
            )
            reference.write_text("[Missing](missing.md)\n", encoding="utf-8")
            errors: list[str] = []
            with patch.object(module, "ROOT", root):
                module.validate_frontmatter(skill, errors)
            relative_reference = (
                Path("plugins")
                / "example"
                / "skills"
                / "sample"
                / "references"
                / "guide.md"
            )
            self.assertEqual(
                errors,
                [f"broken relative link in {relative_reference}: missing.md"],
            )

    def test_privacy_scan_catches_cross_platform_homes_and_url_credentials(self) -> None:
        module = load_agent_kit()
        self.assertEqual(module.privacy_markers("safe public text"), [])
        self.assertEqual(
            module.privacy_markers("/" + "Users" + "/alex/private.txt"), ["macOS home path"]
        )
        self.assertEqual(
            module.privacy_markers("/" + "home" + "/alex/private.txt"), ["Linux home path"]
        )
        self.assertEqual(
            module.privacy_markers("/" + "root" + "/private.txt"), ["root home path"]
        )
        self.assertEqual(
            module.privacy_markers("C:" + "\\" + "Users" + "\\alex\\private.txt"),
            ["Windows home path"],
        )
        self.assertEqual(
            module.privacy_markers(
                "\\\\" + "fileserver" + "\\Users\\alex\\private.txt"
            ),
            ["UNC home path"],
        )
        self.assertEqual(
            module.privacy_markers("https://" + "name:secret@example.com/path"),
            ["credential-bearing URL"],
        )
        self.assertEqual(
            module.privacy_markers("https://" + "ghp_token@github.com/repository"),
            ["credential-bearing URL"],
        )

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("zsh"), "macOS app cleanup")
    def test_localtesting_cleanup_refuses_same_id_app_outside_approved_roots(self) -> None:
        script = (
            ROOT
            / "plugins"
            / "evidence-workflows"
            / "skills"
            / "localtesting"
            / "scripts"
            / "cleanup-old-app-copies.sh"
        )
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-app-cleanup-") as temporary:
            root = Path(temporary)
            home = root / "home"
            canonical = root / "canonical" / "Example.app"
            outside = root / "unapproved" / "Example.app"
            fake_bin = root / "bin"
            home.mkdir()
            fake_bin.mkdir()
            payload = plistlib.dumps(
                {"CFBundleIdentifier": "example.toolkit.cleanup", "CFBundleExecutable": "Example"}
            )
            for app in (canonical, outside):
                (app / "Contents" / "MacOS").mkdir(parents=True)
                (app / "Contents" / "Info.plist").write_bytes(payload)
                executable = app / "Contents" / "MacOS" / "Example"
                executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                executable.chmod(0o755)
            mdfind = fake_bin / "mdfind"
            mdfind.write_text(f"#!/bin/sh\nprintf '%s\\n' '{outside}'\n", encoding="utf-8")
            mdfind.chmod(0o755)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["PATH"] = str(fake_bin) + os.pathsep + env["PATH"]
            command = [
                "zsh",
                str(script),
                "--canonical-app",
                str(canonical),
                "--bundle-id",
                "example.toolkit.cleanup",
                "--receipt",
                str(root / "preview.receipt"),
            ]
            preview = subprocess.run(
                command,
                check=False,
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(preview.returncode, 0, preview.stderr)
            result = subprocess.run(
                [*command, "--apply"],
                check=False,
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(outside.is_dir())
            self.assertIn("outside approved cleanup roots", result.stdout)

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("zsh"), "macOS app cleanup")
    def test_localtesting_cleanup_refuses_candidates_added_after_preview(self) -> None:
        script = (
            ROOT
            / "plugins"
            / "evidence-workflows"
            / "skills"
            / "localtesting"
            / "scripts"
            / "cleanup-old-app-copies.sh"
        )
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-app-receipt-") as temporary:
            root = Path(temporary)
            home = root / "home"
            canonical = root / "canonical" / "Example.app"
            scan_root = root / "build"
            first = scan_root / "First.app"
            second = scan_root / "Second.app"
            fake_bin = root / "bin"
            home.mkdir()
            fake_bin.mkdir()

            def write_app(app: Path) -> None:
                payload = plistlib.dumps(
                    {
                        "CFBundleIdentifier": "example.toolkit.cleanup",
                        "CFBundleExecutable": "Example",
                    }
                )
                (app / "Contents" / "MacOS").mkdir(parents=True)
                (app / "Contents" / "Info.plist").write_bytes(payload)
                executable = app / "Contents" / "MacOS" / "Example"
                executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                executable.chmod(0o755)

            write_app(canonical)
            write_app(first)
            mdfind = fake_bin / "mdfind"
            mdfind.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            mdfind.chmod(0o755)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["PATH"] = str(fake_bin) + os.pathsep + env["PATH"]
            command = [
                "zsh",
                str(script),
                "--canonical-app",
                str(canonical),
                "--bundle-id",
                "example.toolkit.cleanup",
                "--scan-root",
                str(scan_root),
                "--receipt",
                str(root / "preview.receipt"),
            ]
            preview = subprocess.run(
                command,
                check=False,
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(preview.returncode, 0, preview.stderr)
            write_app(second)
            result = subprocess.run(
                [*command, "--apply"],
                check=False,
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(first.is_dir())
            self.assertTrue(second.is_dir())
            self.assertIn("changed after preview", result.stderr)

    def test_obscura_allowlist_has_strong_digests(self) -> None:
        catalog = json.loads((ROOT / "catalog" / "upstreams.json").read_text(encoding="utf-8"))
        assets = catalog["bundles"]["obscura"]["assets"]
        self.assertEqual(
            set(assets),
            {"linux-aarch64", "linux-x86_64", "macos-aarch64", "macos-x86_64", "windows-x86_64"},
        )
        for asset in assets.values():
            self.assertRegex(asset["sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(asset["binarySha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(asset["workerSha256"], r"^[0-9a-f]{64}$")

    @unittest.skipIf(os.name == "nt", "POSIX symlink behavior is verified here")
    def test_upstream_receipt_ignores_fixed_symlink_temporary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-upstream-receipt-") as temporary:
            root = Path(temporary)
            state = root / "state"
            target = root / "do-not-overwrite.txt"
            state.mkdir()
            target.write_text("preserve me\n", encoding="utf-8")
            (state / "upstreams.tmp").symlink_to(target)
            with (
                patch.object(self.module, "STATE_DIR", state),
                patch.object(self.module, "STATE_FILE", state / "upstreams.json"),
                patch.object(
                    self.module,
                    "ensure_private_directory",
                    side_effect=lambda path: path.mkdir(parents=True, exist_ok=True),
                ),
            ):
                self.module.save_receipt(
                    "recommended",
                    ["codex"],
                    ["graphify"],
                    {"graphify": {"version": "0.9.50"}},
                )
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve me\n")
            receipt = json.loads((state / "upstreams.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["bundles"], ["graphify"])
            self.assertEqual(receipt["schemaVersion"], 2)
            self.assertEqual(receipt["resolved"]["graphify"]["version"], "0.9.50")

    @unittest.skipIf(os.name == "nt", "POSIX symlink behavior is verified here")
    def test_upstream_receipt_refuses_symlinked_destination(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-upstream-receipt-") as temporary:
            root = Path(temporary)
            state = root / "state"
            target = root / "do-not-overwrite.txt"
            state.mkdir()
            target.write_text("preserve me\n", encoding="utf-8")
            (state / "upstreams.json").symlink_to(target)
            with (
                patch.object(self.module, "STATE_DIR", state),
                patch.object(self.module, "STATE_FILE", state / "upstreams.json"),
                patch.object(
                    self.module,
                    "ensure_private_directory",
                    side_effect=lambda path: path.mkdir(parents=True, exist_ok=True),
                ),
                self.assertRaisesRegex(self.module.UpstreamError, "Refusing symlinked upstream receipt"),
            ):
                self.module.save_receipt(
                    "recommended",
                    ["codex"],
                    ["graphify"],
                    {"graphify": {"version": "0.9.50"}},
                )
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve me\n")

    def test_upstream_receipt_preserves_other_managed_client_targets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-upstream-merge-") as temporary:
            state = Path(temporary)
            receipt_file = state / "upstreams.json"
            receipt_file.write_text(
                json.dumps(
                    {
                        "schemaVersion": 2,
                        "profile": "recommended",
                        "clients": ["claude"],
                        "bundles": ["matt-pocock-skills"],
                        "resolved": {
                            "matt-pocock-skills": {
                                "commit": "a" * 40,
                                "skills": {"one": "skills/one"},
                                "targets": ["/managed/claude/skills"],
                            }
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with (
                patch.object(self.module, "STATE_DIR", state),
                patch.object(self.module, "STATE_FILE", receipt_file),
                patch.object(self.module, "ensure_private_directory"),
            ):
                self.module.save_receipt(
                    "recommended",
                    ["codex"],
                    ["graphify"],
                    {"graphify": {"version": "0.9.50"}},
                )
            merged = json.loads(receipt_file.read_text(encoding="utf-8"))
            self.assertEqual(merged["clients"], ["claude", "codex"])
            self.assertEqual(
                set(merged["resolved"]), {"matt-pocock-skills", "graphify"}
            )

    def test_graphify_command_refuses_unmanaged_path_fallback(self) -> None:
        bundle = {"package": "graphifyy", "version": "0.9.50", "clients": ["codex"]}

        def fake_which(name: str) -> str | None:
            return "/tmp/unverified-graphify" if name == "graphify" else None

        with (
            tempfile.TemporaryDirectory(prefix="agent-toolkit-graphify-managed-") as temporary,
            patch.object(self.module, "STATE_DIR", Path(temporary)),
            patch.object(self.module.shutil, "which", side_effect=fake_which),
            self.assertRaisesRegex(self.module.UpstreamError, "toolkit-managed environment"),
        ):
            self.module.graphify_command(bundle)

    def test_graphify_dry_run_uses_managed_venv_without_uv(self) -> None:
        bundle = {"package": "graphifyy", "version": "0.9.50", "clients": ["codex"]}
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-graphify-managed-") as temporary:
            root = Path(temporary)
            home = root / "home"
            home.mkdir()
            with (
                patch.object(self.module, "STATE_DIR", root / "state"),
                patch.object(self.module.Path, "home", return_value=home),
                patch.dict(os.environ, {"CODEX_HOME": str(root / "codex")}),
                patch.object(self.module, "run") as execute,
            ):
                self.module.install_graphify(
                    bundle,
                    ["codex"],
                    True,
                    None,
                    adopt_existing=False,
                    profile="recommended",
                )
        commands = [call.args[0] for call in execute.call_args_list]
        self.assertEqual(commands[0][:3], [sys.executable, "-m", "venv"])
        self.assertIn("graphifyy==0.9.50", commands[1])
        self.assertFalse(any(command[0] in {"uv", "pipx", "npx"} for command in commands))

    def test_graphify_discovery_pins_invokable_managed_command(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-graphify-pin-") as temporary:
            root = Path(temporary)
            skill = root / "skills" / "graphify"
            executable = root / "managed" / "bin" / "graphify"
            skill.mkdir(parents=True)
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                "---\nname: graphify\n---\n\n# Graphify\n\nRun `graphify query`.\n",
                encoding="utf-8",
            )
            self.module.pin_graphify_discovery(skill, executable, root)
            self.assertIsNone(self.module.graphify_discovery_problem(skill, executable))
            contents = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(str(executable.resolve()), contents)
            self.assertIn("substitute this absolute command", contents)

    def test_graphify_preflight_refuses_unmanaged_discovery_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-graphify-ownership-") as temporary:
            root = Path(temporary)
            destination = root / "client" / "skills" / "graphify"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("# Existing\n", encoding="utf-8")
            with self.assertRaisesRegex(self.module.UpstreamError, "unmanaged Graphify skill"):
                self.module.preflight_graphify_destinations(
                    [(destination, root / "client")],
                    set(),
                    adopt_existing=False,
                    dry_run=False,
                )
            self.assertEqual(
                (destination / "SKILL.md").read_text(encoding="utf-8"), "# Existing\n"
            )

    def test_upstream_client_root_rejects_relative_and_filesystem_root(self) -> None:
        for value in ("", ".", os.path.abspath(os.sep)):
            with (
                self.subTest(value=value),
                patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": value}),
                self.assertRaisesRegex(self.module.UpstreamError, "must not|absolute"),
            ):
                self.module.client_config_root("claude")

    def test_matt_install_discovers_every_current_source_skill(self) -> None:
        bundle = {
            "repository": "mattpocock/skills",
            "ref": "main",
            "skillRoot": "skills",
            "clients": ["codex", "claude"],
        }
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-matt-current-") as temporary:
            root = Path(temporary)
            checkout = root / "checkout"
            for group, name in (("engineering", "first-skill"), ("new-category", "brand-new-skill")):
                skill = checkout / "skills" / group / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
            home = root / "home"
            home.mkdir()
            with (
                patch.dict(os.environ, {"HOME": str(home), "CLAUDE_CONFIG_DIR": str(home / ".claude")}),
                patch.object(self.module.Path, "home", return_value=home),
                patch.object(self.module, "STATE_DIR", home / ".agent-toolkit"),
                patch.object(
                    self.module,
                    "STATE_FILE",
                    home / ".agent-toolkit" / "upstreams.json",
                ),
                patch.object(self.module, "ensure_tracked_skills_checkout", return_value=checkout),
                patch.object(self.module, "git_value", return_value="a" * 40),
            ):
                resolved = self.module.install_skills_package(
                    bundle,
                    ["codex", "claude"],
                    False,
                    None,
                    adopt_existing=False,
                    profile="recommended",
                )
            self.assertEqual(set(resolved["skills"]), {"first-skill", "brand-new-skill"})
            for name in resolved["skills"]:
                self.assertTrue((home / ".agents" / "skills" / name / "SKILL.md").is_file())
                self.assertTrue((home / ".claude" / "skills" / name / "SKILL.md").is_file())

    @unittest.skipIf(os.name == "nt", "POSIX symlink behavior is verified here")
    def test_matt_install_refuses_symlinked_destination_parent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-matt-destination-") as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "home" / ".agents" / "skills" / "example"
            outside = root / "outside"
            source.mkdir()
            outside.mkdir()
            (source / "SKILL.md").write_text("# Example\n", encoding="utf-8")
            destination.parent.parent.mkdir(parents=True)
            destination.parent.symlink_to(outside, target_is_directory=True)
            with (
                patch.object(self.module.Path, "home", return_value=root / "home"),
                self.assertRaisesRegex(self.module.UpstreamError, "symlinked skill destination path"),
            ):
                self.module.backup_and_copy_skill(
                    source,
                    destination,
                    root / "backups",
                    destination.parent.parent,
                    managed=False,
                    adopt_existing=False,
                )
            self.assertFalse((outside / "example").exists())

    def test_matt_install_refuses_unmanaged_existing_skill_without_adoption(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-matt-ownership-") as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "home" / ".agents" / "skills" / "example"
            source.mkdir(parents=True)
            destination.mkdir(parents=True)
            (source / "SKILL.md").write_text("# Current\n", encoding="utf-8")
            (destination / "SKILL.md").write_text("# Existing\n", encoding="utf-8")
            with self.assertRaisesRegex(self.module.UpstreamError, "Refusing unmanaged skill"):
                self.module.backup_and_copy_skill(
                    source,
                    destination,
                    root / "backups",
                    root / "home" / ".agents",
                    managed=False,
                    adopt_existing=False,
                )
            self.assertEqual(
                (destination / "SKILL.md").read_text(encoding="utf-8"), "# Existing\n"
            )

    def test_matt_install_archives_skills_removed_upstream(self) -> None:
        bundle = {
            "repository": "mattpocock/skills",
            "ref": "main",
            "skillRoot": "skills",
            "clients": ["codex"],
        }
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-matt-stale-") as temporary:
            root = Path(temporary)
            home = root / "home"
            checkout = root / "checkout"
            current = checkout / "skills" / "engineering" / "current"
            installed_root = home / ".agents" / "skills"
            current.mkdir(parents=True)
            (current / "SKILL.md").write_text("# Current\n", encoding="utf-8")
            for name in ("current", "retired"):
                destination = installed_root / name
                destination.mkdir(parents=True)
                (destination / "SKILL.md").write_text(f"# {name.title()}\n", encoding="utf-8")
            receipt = {
                "schemaVersion": 2,
                "bundles": ["matt-pocock-skills"],
                "resolved": {
                    "matt-pocock-skills": {
                        "skills": {"current": "old/current", "retired": "old/retired"},
                        "targets": [str(installed_root)],
                    }
                },
            }
            with (
                patch.object(self.module.Path, "home", return_value=home),
                patch.object(self.module, "STATE_DIR", home / ".agent-toolkit"),
                patch.object(
                    self.module,
                    "STATE_FILE",
                    home / ".agent-toolkit" / "upstreams.json",
                ),
                patch.object(self.module, "ensure_tracked_skills_checkout", return_value=checkout),
                patch.object(self.module, "git_value", return_value="a" * 40),
            ):
                resolved = self.module.install_skills_package(
                    bundle,
                    ["codex"],
                    False,
                    receipt,
                    adopt_existing=False,
                    profile="recommended",
                )
            self.assertEqual(set(resolved["skills"]), {"current"})
            self.assertFalse((installed_root / "retired").exists())
            archived = list(
                (home / ".agent-toolkit" / "backups").rglob("retired/SKILL.md")
            )
            self.assertEqual(len(archived), 1)

    def test_matt_install_accepts_external_claude_config_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-matt-external-") as temporary:
            root = Path(temporary)
            source = root / "source"
            external = root / "external-claude"
            destination = external / "skills" / "example"
            source.mkdir()
            (source / "SKILL.md").write_text("# Example\n", encoding="utf-8")
            self.module.backup_and_copy_skill(
                source,
                destination,
                root / "backups",
                external,
                managed=False,
                adopt_existing=False,
            )
            self.assertTrue((destination / "SKILL.md").is_file())

    def test_matt_partial_client_update_refreshes_all_receipted_targets(self) -> None:
        bundle = {
            "repository": "mattpocock/skills",
            "ref": "main",
            "skillRoot": "skills",
            "clients": ["codex", "claude"],
        }
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-matt-targets-") as temporary:
            root = Path(temporary)
            home = root / "home"
            state = home / ".agent-toolkit"
            checkout = state / "sources" / "matt-pocock-skills"
            source = checkout / "skills" / "engineering" / "example"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("# Current\n", encoding="utf-8")
            targets = [home / ".agents" / "skills", home / ".claude" / "skills"]
            for target in targets:
                installed = target / "example"
                installed.mkdir(parents=True)
                (installed / "SKILL.md").write_text("# Previous\n", encoding="utf-8")
            receipt = {
                "schemaVersion": 2,
                "profile": "recommended",
                "clients": ["codex", "claude"],
                "bundles": ["matt-pocock-skills"],
                "resolved": {
                    "matt-pocock-skills": {
                        "repository": "mattpocock/skills",
                        "ref": "main",
                        "commit": "b" * 40,
                        "skills": {"example": "skills/engineering/example"},
                        "targets": [str(target) for target in targets],
                        "status": "active",
                    }
                },
            }
            with (
                patch.object(self.module.Path, "home", return_value=home),
                patch.object(self.module, "STATE_DIR", state),
                patch.object(self.module, "STATE_FILE", state / "upstreams.json"),
                patch.object(self.module, "ensure_tracked_skills_checkout", return_value=checkout),
                patch.object(self.module, "git_value", return_value="a" * 40),
            ):
                resolved = self.module.install_skills_package(
                    bundle,
                    ["codex"],
                    False,
                    receipt,
                    adopt_existing=False,
                    profile="recommended",
                )
            self.assertEqual(set(resolved["targets"]), {str(target) for target in targets})
            for target in targets:
                self.assertEqual(
                    (target / "example" / "SKILL.md").read_text(encoding="utf-8"),
                    "# Current\n",
                )

    def test_matt_interrupted_copy_recovers_from_pending_receipt(self) -> None:
        bundle = {
            "repository": "mattpocock/skills",
            "ref": "main",
            "skillRoot": "skills",
            "clients": ["codex"],
        }
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-matt-recovery-") as temporary:
            root = Path(temporary)
            home = root / "home"
            state = home / ".agent-toolkit"
            checkout = state / "sources" / "matt-pocock-skills"
            for name in ("first", "second"):
                source = checkout / "skills" / "engineering" / name
                source.mkdir(parents=True)
                (source / "SKILL.md").write_text(f"# {name.title()}\n", encoding="utf-8")
            receipt_file = state / "upstreams.json"
            original_copy = self.module.backup_and_copy_skill
            calls = {"count": 0}

            def interrupt_second(*args, **kwargs):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise self.module.UpstreamError("simulated interruption")
                return original_copy(*args, **kwargs)

            common = (
                patch.object(self.module.Path, "home", return_value=home),
                patch.object(self.module, "STATE_DIR", state),
                patch.object(self.module, "STATE_FILE", receipt_file),
                patch.object(self.module, "ensure_tracked_skills_checkout", return_value=checkout),
                patch.object(self.module, "git_value", return_value="a" * 40),
            )
            with (
                common[0],
                common[1],
                common[2],
                common[3],
                common[4],
                patch.object(self.module, "backup_and_copy_skill", side_effect=interrupt_second),
                self.assertRaisesRegex(self.module.UpstreamError, "simulated interruption"),
            ):
                self.module.install_skills_package(
                    bundle,
                    ["codex"],
                    False,
                    None,
                    adopt_existing=False,
                    profile="recommended",
                )
            pending = json.loads(receipt_file.read_text(encoding="utf-8"))
            self.assertEqual(
                pending["resolved"]["matt-pocock-skills"]["status"], "pending"
            )
            with (
                common[0],
                common[1],
                common[2],
                common[3],
                common[4],
                patch.object(self.module, "checkout_problem", return_value=None),
            ):
                resolved = self.module.install_skills_package(
                    bundle,
                    ["codex"],
                    False,
                    self.module.load_receipt(),
                    adopt_existing=False,
                    profile="recommended",
                )
                self.module.save_receipt(
                    "recommended",
                    ["codex"],
                    ["matt-pocock-skills"],
                    {"matt-pocock-skills": resolved},
                )
                self.assertEqual(
                    self.module.doctor_skills_package(
                        bundle, ["codex"], self.module.load_receipt()
                    ),
                    0,
                )
            active = json.loads(receipt_file.read_text(encoding="utf-8"))
            self.assertEqual(active["resolved"]["matt-pocock-skills"]["status"], "active")
            for name in ("first", "second"):
                self.assertTrue((home / ".agents" / "skills" / name / "SKILL.md").is_file())

    def test_matt_doctor_requires_complete_receipted_inventory(self) -> None:
        bundle = {
            "repository": "mattpocock/skills",
            "ref": "main",
            "skillRoot": "skills",
            "clients": ["codex"],
        }
        receipt = {
            "resolved": {
                "matt-pocock-skills": {
                    "repository": "mattpocock/skills",
                    "ref": "main",
                    "commit": "a" * 40,
                    "skills": {"first": "skills/engineering/first"},
                }
            }
        }
        with (
            patch.object(self.module, "checkout_problem", return_value=None),
            patch.object(
                self.module,
                "discover_skill_package",
                return_value={
                    "first": "skills/engineering/first",
                    "new": "skills/engineering/new",
                },
            ),
        ):
            self.assertEqual(self.module.doctor_skills_package(bundle, ["codex"], receipt), 1)

    def test_matt_skill_tree_detects_auxiliary_tampering_and_extras(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-matt-tree-") as temporary:
            root = Path(temporary)
            source = root / "source"
            installed = root / "installed"
            for path in (source, installed):
                (path / "scripts").mkdir(parents=True)
                (path / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
                (path / "scripts" / "check.sh").write_text("exit 0\n", encoding="utf-8")
            self.assertIsNone(self.module.skill_tree_problem(source, installed))
            (installed / "scripts" / "check.sh").write_text("exit 1\n", encoding="utf-8")
            self.assertIn("changed scripts/check.sh", self.module.skill_tree_problem(source, installed) or "")
            (installed / "scripts" / "check.sh").write_text("exit 0\n", encoding="utf-8")
            (installed / "extra.txt").write_text("unexpected\n", encoding="utf-8")
            self.assertIn("extra extra.txt", self.module.skill_tree_problem(source, installed) or "")
            if os.name != "nt":
                (installed / "extra.txt").unlink()
                (installed / "scripts" / "check.sh").unlink()
                (installed / "scripts" / "check.sh").symlink_to(source / "scripts" / "check.sh")
                self.assertIn(
                    "unsafe file",
                    self.module.skill_tree_problem(source, installed) or "",
                )

    def test_marketplace_identity_conflict_is_refused_even_for_preinstalled_catalog(self) -> None:
        bundle = {
            "marketplace": "claude-plugins-official",
            "repository": "anthropics/claude-plugins-official",
        }
        with (
            patch.object(
                self.module,
                "marketplace_entry",
                return_value={"name": "claude-plugins-official", "repo": "lookalike/plugins"},
            ),
            self.assertRaisesRegex(self.module.UpstreamError, "Refusing conflicting"),
        ):
            self.module.ensure_marketplace(bundle, "claude", False)

    def test_openai_checkout_rejects_clean_local_commit_ahead_of_tracking_ref(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-openai-checkout-") as temporary:
            root = Path(temporary)
            remote = root / "remote.git"
            checkout = root / "checkout"
            env = os.environ.copy()
            run(["git", "init", "--bare", str(remote)], env=env)
            run(["git", "clone", str(remote), str(checkout)], env=env)
            run(["git", "-C", str(checkout), "config", "user.name", "Agent Toolkit Tests"], env=env)
            run(["git", "-C", str(checkout), "config", "user.email", "tests@users.noreply.github.com"], env=env)
            (checkout / "one.txt").write_text("one\n", encoding="utf-8")
            run(["git", "-C", str(checkout), "add", "one.txt"], env=env)
            run(["git", "-C", str(checkout), "commit", "-m", "one"], env=env)
            run(["git", "-C", str(checkout), "push", "-u", "origin", "HEAD:main"], env=env)
            run(
                ["git", "-C", str(checkout), "remote", "set-url", "origin", "https://github.com/openai/plugins.git"],
                env=env,
            )
            (checkout / "two.txt").write_text("two\n", encoding="utf-8")
            run(["git", "-C", str(checkout), "add", "two.txt"], env=env)
            run(["git", "-C", str(checkout), "commit", "-m", "local ahead"], env=env)
            problem = self.module.checkout_problem(checkout, "openai/plugins", tracking_ref="main")
            self.assertIn("does not exactly match", problem or "")

    def test_mcp_registration_requires_exact_managed_command_and_argument(self) -> None:
        expected = Path("/managed/obscura")
        self.assertTrue(self.module.mcp_spec_matches((str(expected), ["mcp"]), expected))
        self.assertFalse(self.module.mcp_spec_matches(("/other/obscura", ["mcp"]), expected))
        self.assertFalse(self.module.mcp_spec_matches((str(expected), ["serve"]), expected))

    def test_obscura_install_refuses_conflicting_registration(self) -> None:
        bundle = {"version": "0.2.1", "clients": ["codex"]}
        expected = Path("/managed/obscura")
        with (
            patch.object(self.module, "obscura_binary", return_value=expected),
            patch.object(self.module, "mcp_registration_spec", return_value=("/other/obscura", ["mcp"])),
            patch.object(self.module, "STATE_DIR", Path("/managed/state")),
            self.assertRaisesRegex(self.module.UpstreamError, "Refusing conflicting"),
        ):
            self.module.install_obscura(bundle, ["codex"], False, update=False)

    def test_repository_normalization_rejects_lookalikes(self) -> None:
        normalize = self.module.normalize_repo
        self.assertEqual(normalize("https://github.com/openai/plugins.git"), "openai/plugins")
        self.assertEqual(normalize("git@github.com:openai/plugins.git"), "openai/plugins")
        self.assertIsNone(normalize("https://example.com/openai/plugins"))
        self.assertIsNone(normalize("https://github.com/evil/openai/plugins"))

    def test_tar_extraction_rejects_parent_traversal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-archive-test-") as temporary:
            root = Path(temporary)
            archive = root / "bad.tar.gz"
            payload = b"do not extract\n"
            with tarfile.open(archive, "w:gz") as handle:
                member = tarfile.TarInfo("../escape")
                member.size = len(payload)
                handle.addfile(member, io.BytesIO(payload))
            destination = root / "destination"
            destination.mkdir()
            with self.assertRaisesRegex(self.module.UpstreamError, "Unsafe path"):
                self.module.safe_extract_tar(archive, destination)
            self.assertFalse((root / "escape").exists())

    def test_obscura_doctor_does_not_download_missing_binary(self) -> None:
        bundle = {
            "version": "1.2.3",
            "clients": ["codex"],
        }
        with (
            tempfile.TemporaryDirectory(prefix="agent-toolkit-obscura-doctor-") as temporary,
            patch.object(self.module, "STATE_DIR", Path(temporary)),
            patch.object(self.module, "obscura_binary") as download,
        ):
            self.assertEqual(self.module.doctor_obscura(bundle, ["codex"]), 1)
            download.assert_not_called()

    def test_openai_fallback_adapter_contains_only_allowlisted_plugins(self) -> None:
        catalog = json.loads((ROOT / "catalog" / "upstreams.json").read_text(encoding="utf-8"))
        bundle = catalog["bundles"]["openai-essentials"]
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-openai-adapter-") as temporary:
            adapter = Path(temporary)
            expected = []
            for name in bundle["plugins"]:
                if name == "build-macos-apps" and sys.platform != "darwin":
                    continue
                manifest = adapter / "upstream" / "plugins" / name / ".codex-plugin" / "plugin.json"
                manifest.parent.mkdir(parents=True)
                manifest.write_text("{}\n", encoding="utf-8")
                expected.append(name)
            with patch.object(
                self.module,
                "ensure_private_directory",
                side_effect=lambda path: path.mkdir(parents=True, exist_ok=True),
            ):
                self.module.write_openai_adapter(bundle, adapter)
            generated = json.loads(
                (adapter / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
            )
            self.assertEqual(generated["name"], bundle["fallbackMarketplace"])
            self.assertEqual([entry["name"] for entry in generated["plugins"]], expected)

    def test_graphify_discovery_mirrors_into_custom_codex_home(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agent-toolkit-graphify-home-") as temporary:
            root = Path(temporary)
            source = root / "home" / ".codex" / "skills" / "graphify"
            target = root / "codex" / "skills" / "graphify"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("# Graphify\n", encoding="utf-8")
            (source / ".graphify_version").write_text("0.9.50\n", encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "HOME": str(root / "home"),
                    "USERPROFILE": str(root / "home"),
                    "CODEX_HOME": str(root / "codex"),
                },
                clear=False,
            ):
                self.module.sync_graphify_discovery("codex")
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "# Graphify\n")


class LifecycleRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="agent-toolkit-recovery-test-")
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.original_home = os.environ.get("HOME")
        os.environ["HOME"] = str(self.home)
        self.module = load_agent_kit()
        self.module.STATE_DIR = self.home / ".agent-toolkit"
        self.module.STATE_FILE = self.module.STATE_DIR / "state.json"

    def tearDown(self) -> None:
        if self.original_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self.original_home
        self.temp.cleanup()

    def install_args(self) -> SimpleNamespace:
        return SimpleNamespace(
            clients="codex",
            profile="recommended",
            source="local",
            repo="udhawan97/agent-toolkit",
            channel="stable",
            dry_run=False,
            adopt_existing=False,
            include_guidance=False,
            no_guidance=True,
            core_only=True,
        )

    def uninstall_args(self) -> SimpleNamespace:
        return SimpleNamespace(
            clients=None,
            profile=None,
            dry_run=False,
            remove_guidance=False,
            purge_data=False,
            core_only=True,
        )

    def test_install_persists_pending_marketplace_ownership_before_creation(self) -> None:
        module = self.module
        with (
            patch.object(module, "validate_repo"),
            patch.object(module, "choose_clients", return_value=["codex"]),
            patch.object(module, "profile_plugins", return_value=["evidence-workflows"]),
            patch.object(module, "marketplace_source", return_value=(str(ROOT), str(ROOT), True)),
            patch.object(module, "marketplace_entry", return_value=None),
            patch.object(module, "register_marketplace", side_effect=RuntimeError("interrupted after native add")),
            self.assertRaisesRegex(RuntimeError, "interrupted"),
        ):
            module.command_install(self.install_args())

        state = json.loads(module.STATE_FILE.read_text(encoding="utf-8"))
        pending = state["clients"]["codex"]
        self.assertEqual(pending["status"], "installing")
        self.assertTrue(pending["marketplaceCreated"])
        self.assertEqual(pending["plannedPlugins"], ["evidence-workflows"])
        self.assertFalse(pending["upstreamsEnabled"])
        self.assertFalse(pending["guidanceEnabled"])

    def test_receipt_preferences_drive_later_upstream_lifecycle(self) -> None:
        module = self.module
        plan = {
            "codex": {"profile": "recommended", "plugins": []},
            "claude": {"profile": "skills-only", "plugins": []},
        }
        state = {
            "clients": {
                "codex": {"upstreamsEnabled": False},
                "claude": {"upstreamsEnabled": True},
            }
        }
        self.assertEqual(
            module.upstream_plan_groups(plan, state, core_only=False),
            {"skills-only": ["claude"]},
        )
        self.assertEqual(module.upstream_plan_groups(plan, state, core_only=True), {})

    def test_update_reconciles_a_newly_detected_second_client(self) -> None:
        module = self.module
        state = {
            "schemaVersion": 2,
            "source": {
                "kind": "github",
                "path": None,
                "repo": "udhawan97/agent-toolkit",
                "channel": "stable",
            },
            "clients": {
                "codex": {
                    "profile": "recommended",
                    "status": "active",
                    "upstreamsEnabled": True,
                    "guidanceEnabled": True,
                }
            },
        }
        refreshed = json.loads(json.dumps(state))
        refreshed["clients"]["claude"] = dict(refreshed["clients"]["codex"])
        args = SimpleNamespace(clients=None, dry_run=False, adopt_existing=False)
        with (
            patch.object(module, "detected_clients", return_value=["codex", "claude"]),
            patch.object(module, "command_install") as install,
            patch.object(module, "load_state", return_value=refreshed),
        ):
            result = module.reconcile_detected_clients(args, state)
        self.assertIs(result, refreshed)
        install_args = install.call_args.args[0]
        self.assertEqual(install_args.clients, "claude")
        self.assertEqual(install_args.profile, "recommended")
        self.assertTrue(install_args.include_guidance)
        self.assertFalse(install_args.core_only)

    def test_claude_update_reinstalls_receipted_personal_skills_with_data_retained(self) -> None:
        module = self.module
        state = {
            "schemaVersion": 2,
            "source": {"kind": "local", "path": str(ROOT.resolve()), "repo": None, "channel": None},
            "clients": {
                "claude": {
                    "profile": "recommended",
                    "plugins": ["evidence-workflows"],
                    "pluginOwnership": {"evidence-workflows": "created"},
                    "marketplaceCreated": True,
                    "status": "active",
                    "upstreamsEnabled": False,
                    "guidanceEnabled": False,
                }
            },
            "guidance": [],
        }
        args = SimpleNamespace(
            clients=None,
            profile=None,
            dry_run=False,
            adopt_existing=False,
            core_only=True,
        )
        plan = {"claude": {"profile": "recommended", "plugins": ["evidence-workflows"]}}
        with (
            patch.object(module, "validate_repo"),
            patch.object(module, "load_state", return_value=state),
            patch.object(module, "reconcile_detected_clients", return_value=state),
            patch.object(module, "lifecycle_plan", return_value=plan),
            patch.object(module, "require_matching_marketplace"),
            patch.object(module, "plugin_is_installed", return_value=True),
            patch.object(module, "uninstall_plugin") as uninstall,
            patch.object(module, "install_plugin") as install,
            patch.object(module, "save_state"),
        ):
            module.command_update(args)
        uninstall.assert_called_once_with("claude", "evidence-workflows", False)
        install.assert_called_once_with("claude", "evidence-workflows", False)

    def test_guidance_honors_configured_client_homes(self) -> None:
        module = self.module
        codex_home = self.root / "custom-codex"
        claude_home = self.root / "custom-claude"
        with patch.dict(
            os.environ,
            {"CODEX_HOME": str(codex_home), "CLAUDE_CONFIG_DIR": str(claude_home)},
            clear=False,
        ):
            module.merge_guidance("codex", False)
            module.merge_guidance("claude", False)
        self.assertIn(module.BEGIN_MARKER, (codex_home / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn(module.BEGIN_MARKER, (claude_home / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_core_client_root_rejects_empty_relative_and_filesystem_root(self) -> None:
        module = self.module
        for value in ("", ".", os.path.abspath(os.sep)):
            with (
                self.subTest(value=value),
                patch.dict(os.environ, {"CODEX_HOME": value}),
                self.assertRaisesRegex(module.ToolkitError, "must not|absolute"),
            ):
                module.client_config_root("codex")

    def test_uninstall_persists_completed_client_and_recovers_after_failure(self) -> None:
        module = self.module
        state = {
            "schemaVersion": 2,
            "source": {"kind": "local", "path": str(ROOT.resolve()), "repo": None, "channel": None},
            "clients": {
                client: {
                    "profile": "recommended",
                    "plugins": ["evidence-workflows"],
                    "pluginOwnership": {"evidence-workflows": "created"},
                    "marketplaceCreated": True,
                    "status": "active",
                }
                for client in ("codex", "claude")
            },
            "guidance": [],
        }
        module.save_state(state)
        marketplaces = {"codex": True, "claude": True}
        fail_codex_once = {"value": True}

        def marketplace_entry(client: str):
            return {"name": module.MARKETPLACE} if marketplaces[client] else None

        def uninstall_plugin(client: str, plugin: str, dry_run: bool, purge_data: bool = False) -> None:
            del plugin, dry_run, purge_data
            if client == "codex" and fail_codex_once["value"]:
                fail_codex_once["value"] = False
                raise module.ToolkitError("simulated Codex failure")

        def native_run(command: list[str], **kwargs):
            del kwargs
            if "marketplace" in command and "remove" in command:
                marketplaces[command[0]] = False
            return subprocess.CompletedProcess(command, 0, "", "")

        common_patches = (
            patch.object(module, "ensure_clients_available"),
            patch.object(module, "marketplace_entry", side_effect=marketplace_entry),
            patch.object(module, "marketplace_matches", return_value=(True, "matching test source")),
            patch.object(module, "plugin_is_installed", return_value=True),
            patch.object(module, "uninstall_plugin", side_effect=uninstall_plugin),
            patch.object(module, "run", side_effect=native_run),
        )
        with (
            common_patches[0],
            common_patches[1],
            common_patches[2],
            common_patches[3],
            common_patches[4],
            common_patches[5],
            self.assertRaisesRegex(module.ToolkitError, "simulated Codex failure"),
        ):
            module.command_uninstall(self.uninstall_args())

        partial = json.loads(module.STATE_FILE.read_text(encoding="utf-8"))
        self.assertEqual(set(partial["clients"]), {"codex"}, json.dumps(partial, indent=2))
        self.assertFalse(marketplaces["claude"])

        with (
            patch.object(module, "ensure_clients_available"),
            patch.object(module, "marketplace_entry", side_effect=marketplace_entry),
            patch.object(module, "marketplace_matches", return_value=(True, "matching test source")),
            patch.object(module, "plugin_is_installed", return_value=True),
            patch.object(module, "uninstall_plugin", side_effect=uninstall_plugin),
            patch.object(module, "run", side_effect=native_run),
        ):
            module.command_uninstall(self.uninstall_args())

        self.assertFalse(module.STATE_FILE.exists())
        self.assertFalse(marketplaces["codex"])

    def test_uninstall_recovers_when_receipt_owned_marketplace_is_already_absent(self) -> None:
        module = self.module
        module.save_state(
            {
                "schemaVersion": 2,
                "source": {"kind": "local", "path": str(ROOT.resolve()), "repo": None, "channel": None},
                "clients": {
                    "codex": {
                        "profile": "recommended",
                        "plugins": ["evidence-workflows"],
                        "pluginOwnership": {"evidence-workflows": "created"},
                        "marketplaceCreated": True,
                        "status": "active",
                    }
                },
                "guidance": [],
            }
        )
        with (
            patch.object(module, "ensure_clients_available"),
            patch.object(module, "marketplace_entry", return_value=None),
            patch.object(module, "plugin_is_installed", return_value=False),
        ):
            module.command_uninstall(self.uninstall_args())
        self.assertFalse(module.STATE_FILE.exists())

    def test_disabled_plugin_is_not_healthy_and_receiptless_doctor_fails(self) -> None:
        module = self.module
        with patch.object(
            module,
            "codex_plugins",
            return_value=[
                {
                    "pluginId": "evidence-workflows@agent-toolkit",
                    "installed": True,
                    "enabled": False,
                }
            ],
        ):
            self.assertFalse(module.plugin_is_installed("codex", "evidence-workflows"))

        args = SimpleNamespace(native=False, clients=None, profile=None, core_only=True)
        version = subprocess.CompletedProcess(["codex", "--version"], 0, "codex-test\n", "")
        with (
            patch.object(module, "validate_repo"),
            patch.object(module, "load_state", return_value=None),
            patch.object(module, "detected_clients", return_value=["codex"]),
            patch.object(module, "run", return_value=version),
            patch.object(module, "marketplace_is_registered", return_value=False),
            self.assertRaisesRegex(module.ToolkitError, "missing or disabled"),
        ):
            module.command_doctor(args)


if __name__ == "__main__":
    unittest.main()

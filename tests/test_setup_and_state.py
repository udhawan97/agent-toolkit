from __future__ import annotations

import io
import json
import os
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
                self.module.save_receipt("recommended", ["codex"], ["graphify"])
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve me\n")
            receipt = json.loads((state / "upstreams.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["bundles"], ["graphify"])

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
                self.module.save_receipt("recommended", ["codex"], ["graphify"])
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve me\n")

    def test_graphify_install_refuses_unmanaged_path_fallback(self) -> None:
        bundle = {"package": "graphifyy", "version": "0.9.50", "clients": ["codex"]}

        def fake_which(name: str) -> str | None:
            return "/tmp/unverified-graphify" if name == "graphify" else None

        with (
            patch.object(self.module.shutil, "which", side_effect=fake_which),
            patch.object(self.module, "run") as execute,
            self.assertRaisesRegex(self.module.UpstreamError, "needs uv or pipx"),
        ):
            self.module.install_graphify(bundle, ["codex"], False)
        execute.assert_not_called()

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
                {"HOME": str(root / "home"), "CODEX_HOME": str(root / "codex")},
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

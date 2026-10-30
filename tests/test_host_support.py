"""Exercise host discovery and the actual catalog/doctor using temporary roots."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("file_drag_host_support", ROOT / "lib/host_support.py")
support = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = support
with patch.object(sys, "dont_write_bytecode", True):
    spec.loader.exec_module(support)

FEATURE = "files.drag-and-drop.v1"


class HostSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.home = self.base / "home"
        self.omarchy = self.base / "omarchy"
        self.home.mkdir()
        self.omarchy.mkdir()

    def make_host(self, directory: Path, *, compatible: bool = True) -> Path:
        manifest = {"schemaVersion": 1, "id": support.HOST_ID, "version": "0.5.3-fixture"}
        if compatible:
            manifest["omalaunch"] = {"hostFeatures": [FEATURE]}
        self.write_manifest(directory, manifest)
        return directory

    @staticmethod
    def write_manifest(directory: Path, manifest: object) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def copy_plugin(self) -> Path:
        directory = self.base / "plugin"
        for name in ("manifest.json", "omalaunch.json", "bin/catalog", "bin/doctor", "lib/host_support.py"):
            target = directory / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        return directory

    def run_tool(self, directory: Path, name: str, *arguments: str, path: str | None = None) -> subprocess.CompletedProcess:
        # A managed fixture always wins before discovery could inspect the real
        # HOME. Keep HOME unchanged, matching how the launcher runs providers.
        environment = {**os.environ, "OMARCHY_PATH": str(self.omarchy)}
        if path is not None:
            environment["PATH"] = path
        return subprocess.run(
            [sys.executable, str(directory / "bin" / name), *arguments],
            cwd=directory, env=environment, stdin=subprocess.DEVNULL,
            text=True, capture_output=True, timeout=5,
        )

    def dependency_directory(self) -> Path:
        directory = self.base / "executables"
        directory.mkdir()
        descriptor = json.loads((ROOT / "omalaunch.json").read_text(encoding="utf-8"))
        for name in descriptor["requires"]:
            executable = directory / name
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
        return directory

    def test_marker_accepts_a_compatible_host(self) -> None:
        host = self.make_host(self.base / "host")
        result = support.require_host(host)
        self.assertEqual(result.path, host.resolve())
        self.assertEqual(result.version, "0.5.3-fixture")

    def test_unpatched_host_reports_required_integration(self) -> None:
        host = self.make_host(self.base / "host", compatible=False)
        with self.assertRaises(support.CompatibilityError) as failure:
            support.require_host(host)
        self.assertIn(FEATURE, str(failure.exception))
        self.assertIn("companion host patch", str(failure.exception))

    def test_malformed_metadata_is_not_accepted_as_a_marker(self) -> None:
        host = self.base / "host"
        for metadata in (None, True, "omalaunch", [], {"hostFeatures": FEATURE},
                         {"hostFeatures": None}, {"hostFeatures": True},
                         {"hostFeatures": {}}, {"hostFeatures": [FEATURE, 7]}):
            with self.subTest(metadata=metadata):
                self.write_manifest(host, {
                    "id": support.HOST_ID, "version": "0.5.3-fixture", "omalaunch": metadata,
                })
                with self.assertRaises(support.CompatibilityError):
                    support.require_host(host)

    def test_missing_host_uses_only_the_supplied_roots(self) -> None:
        with self.assertRaisesRegex(support.CompatibilityError, "not installed"):
            support.require_host(home=self.home, omarchy_path=self.omarchy)

    def test_managed_root_wins_over_user_copy(self) -> None:
        managed = self.make_host(self.omarchy / "shell/plugins/z-managed")
        self.make_host(self.home / ".config/omarchy/plugins/a-user")
        result = support.require_host(home=self.home, omarchy_path=self.omarchy)
        self.assertEqual(result.path, managed)

    def test_lexical_winner_does_not_fall_back_to_shadowed_compatible_copies(self) -> None:
        winner = self.make_host(self.omarchy / "shell/plugins/a-winner", compatible=False)
        self.make_host(self.omarchy / "shell/plugins/z-shadowed")
        self.make_host(self.home / ".config/omarchy/plugins/a-user")
        with self.assertRaises(support.CompatibilityError) as failure:
            support.require_host(home=self.home, omarchy_path=self.omarchy)
        self.assertIn(str(winner), str(failure.exception))

    def test_user_root_is_used_when_managed_root_has_no_matching_host(self) -> None:
        self.write_manifest(self.omarchy / "shell/plugins/unrelated", {"id": "example.other"})
        user = self.make_host(self.home / ".config/omarchy/plugins/a-user")
        result = support.require_host(home=self.home, omarchy_path=self.omarchy)
        self.assertEqual(result.path, user)

    def test_catalog_emits_the_provider_only_for_a_compatible_host(self) -> None:
        self.make_host(self.omarchy / "shell/plugins/host")
        plugin = self.copy_plugin()
        result = self.run_tool(plugin, "catalog")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        descriptor = json.loads(result.stdout)
        self.assertEqual(descriptor["id"], "secretweapon.omalaunch-files-drag-drop")
        self.assertEqual(descriptor["capability"], "files")
        self.assertIs(descriptor["dragAndDrop"], True)
        self.assertEqual(list(plugin.rglob("__pycache__")), [])

    def test_catalog_rejects_unpatched_host_without_publishing_json(self) -> None:
        self.make_host(self.omarchy / "shell/plugins/host", compatible=False)
        plugin = self.copy_plugin()
        result = self.run_tool(plugin, "catalog")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn(FEATURE, result.stderr)
        self.assertIn("companion host patch", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(list(plugin.rglob("__pycache__")), [])

    def test_doctor_explicit_host_returns_structured_success(self) -> None:
        host = self.make_host(self.base / "explicit-host")
        plugin = self.copy_plugin()
        dependencies = self.dependency_directory()
        result = self.run_tool(plugin, "doctor", "--host", str(host), "--json", path=str(dependencies))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {
            "ok": True, "host": str(host), "version": "0.5.3-fixture", "feature": FEATURE,
        })
        self.assertEqual(list(plugin.rglob("__pycache__")), [])

    def test_doctor_returns_structured_missing_dependencies(self) -> None:
        host = self.make_host(self.base / "explicit-host")
        plugin = self.copy_plugin()
        result = self.run_tool(plugin, "doctor", "--host", str(host), "--json", path="")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        value = json.loads(result.stdout)
        self.assertIs(value["ok"], False)
        self.assertEqual(value["requiredFeature"], FEATURE)
        self.assertIn("Missing executables:", value["error"])
        descriptor = json.loads((ROOT / "omalaunch.json").read_text(encoding="utf-8"))
        for name in descriptor["requires"]:
            self.assertIn(name, value["error"])
        self.assertEqual(list(plugin.rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()

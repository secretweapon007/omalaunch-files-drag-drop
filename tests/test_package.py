"""Check provider identity, literal commands, and the actual distributable."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import stat
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("plugin_build", ROOT / "tools/build.py")
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(builder)


class PluginPackageTests(unittest.TestCase):
    def test_provider_is_an_optional_files_replacement(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        provider = json.loads((ROOT / "omalaunch.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["id"], provider["id"])
        self.assertEqual(manifest["version"], "0.1.0")
        self.assertEqual(manifest["kinds"], ["extension"])
        self.assertEqual(manifest["entryPoints"], {})
        self.assertEqual(manifest["omalaunch"], {"extensionProviders": [["./bin/catalog"]]})
        self.assertEqual(provider["capability"], "files")
        self.assertEqual(provider["mode"], "files")
        self.assertIs(provider["dragAndDrop"], True)
        self.assertGreater(provider["priority"], 10)
        self.assertEqual(provider["prefixes"], ["files"])
        self.assertEqual(provider["root"], "~")
        self.assertIn("python", provider["requires"])
        self.assertIn("wl-copy", provider["requires"])

    def test_file_commands_keep_paths_as_literal_arguments(self) -> None:
        provider = json.loads((ROOT / "omalaunch.json").read_text(encoding="utf-8"))
        self.assertEqual(provider["command"], ["xdg-open", "{path}"])
        self.assertEqual(provider["directoryCommand"], ["xdg-open", "{path}"])
        self.assertEqual(provider["terminalCommand"], ["xdg-terminal-exec", "--dir={path}"])
        self.assertEqual(provider["copyCommand"], ["wl-copy", "--", "{path}"])
        copy_file = provider["copyFileCommand"]
        self.assertEqual(copy_file[:2], ["python", "-c"])
        self.assertEqual(copy_file[-1], "{path}")
        compile(copy_file[2], "copyFileCommand", "exec")

    def test_archive_is_reproducible_and_contains_only_runtime_files(self) -> None:
        expected_files = {
            "LICENSE", "README.md", "bin/catalog", "bin/doctor",
            "lib/host_support.py", "manifest.json", "omalaunch.json",
        }
        with tempfile.TemporaryDirectory() as directory:
            first = builder.build(Path(directory) / "first")
            second = builder.build(Path(directory) / "second")
            self.assertEqual(first.name, "secretweapon.omalaunch-files-drag-drop-0.1.0.tar.gz")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with tarfile.open(first, "r:gz") as bundle:
                self.assertEqual(bundle.getnames(), sorted(expected_files))
                self.assertIn("manifest.json", bundle.getnames())
                for entry in bundle.getmembers():
                    self.assertTrue(entry.isfile(), entry.name)
                    self.assertEqual(entry.mode, builder.RUNTIME_FILES[entry.name])
                    self.assertEqual((entry.uid, entry.gid, entry.mtime), (0, 0, 0))
                    payload = bundle.extractfile(entry)
                    assert payload is not None
                    self.assertEqual(payload.read(), (ROOT / entry.name).read_bytes())
                for executable in ("bin/catalog", "bin/doctor"):
                    self.assertEqual(bundle.getmember(executable).mode, 0o755)
                    self.assertTrue((ROOT / executable).stat().st_mode & stat.S_IXUSR)
                self.assertFalse(any(name.startswith(("tests/", "integration/", "tools/", ".git/")) for name in bundle.getnames()))


if __name__ == "__main__":
    unittest.main()

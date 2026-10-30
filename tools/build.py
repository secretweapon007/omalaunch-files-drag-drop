#!/usr/bin/env python3
"""Build the plugin's deterministic runtime archive using the standard library."""
from __future__ import annotations

import argparse
import gzip
import io
import json
from pathlib import Path
import re
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = {
    "LICENSE": 0o644,
    "README.md": 0o644,
    "bin/catalog": 0o755,
    "bin/doctor": 0o755,
    "lib/host_support.py": 0o644,
    "manifest.json": 0o644,
    "omalaunch.json": 0o644,
}


def build(output_dir: Path | None = None) -> Path:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    plugin_id, version = manifest["id"], manifest["version"]
    if not isinstance(plugin_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]+", plugin_id):
        raise ValueError("manifest id is not a safe archive name")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
        raise ValueError("manifest version is not a supported semantic version")
    payloads = {}
    for name in sorted(RUNTIME_FILES):
        source = ROOT / name
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"runtime file must be a regular file: {name}")
        payloads[name] = source.read_bytes()

    destination = output_dir or ROOT / "dist"
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f"{plugin_id}-{version}.tar.gz"
    with tempfile.NamedTemporaryFile(prefix=".plugin-", suffix=".tar.gz", dir=destination, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            with gzip.GzipFile(filename="", mode="wb", fileobj=temporary, mtime=0, compresslevel=9) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as bundle:
                    for name, payload in payloads.items():
                        entry = tarfile.TarInfo(name)
                        entry.size = len(payload)
                        entry.mode = RUNTIME_FILES[name]
                        entry.uid = entry.gid = entry.mtime = 0
                        entry.uname = entry.gname = ""
                        bundle.addfile(entry, io.BytesIO(payload))
            temporary.flush()
            temporary_path.replace(archive)
        finally:
            temporary_path.unlink(missing_ok=True)
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="archive directory (default: dist/)")
    args = parser.parse_args()
    print(build(args.output_dir))


if __name__ == "__main__":
    main()

"""Read-only compatibility discovery for Omalaunch's native file drag API."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat

HOST_ID = "quantumfire.omalaunch"
HOST_FEATURE = "files.drag-and-drop.v1"
MAX_MANIFEST_BYTES = 256 * 1024
MAX_PLUGIN_ENTRIES = 4096


class CompatibilityError(ValueError):
    pass


@dataclass(frozen=True)
class HostSupport:
    path: Path
    version: str


def read_manifest(path: Path) -> dict | None:
    """Ignore missing/malformed manifests without blocking on special files."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_MANIFEST_BYTES:
                return None
            raw = stream.read(MAX_MANIFEST_BYTES + 1)
        if len(raw) > MAX_MANIFEST_BYTES:
            return None
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except (OSError, UnicodeError, ValueError, RecursionError):
        return None


def find_host(*, home: Path | None = None, omarchy_path: Path | None = None) -> tuple[Path, dict]:
    home = home if home is not None else Path.home()
    omarchy_path = omarchy_path if omarchy_path is not None else Path(os.environ.get("OMARCHY_PATH") or "/usr/share/omarchy")
    # Match Omalaunch discovery: managed manifests win; lexical order breaks
    # ties within a root. An incompatible winner must not select a shadowed copy.
    roots = (omarchy_path / "shell/plugins", home / ".config/omarchy/plugins")
    examined = 0
    for root in roots:
        try:
            with os.scandir(root) as entries:
                candidates = []
                for entry in entries:
                    examined += 1
                    if examined > MAX_PLUGIN_ENTRIES:
                        raise CompatibilityError("Omalaunch discovery exceeded the plugin entry limit.")
                    if entry.is_dir(follow_symlinks=True):
                        candidates.append(Path(entry.path))
        except (FileNotFoundError, NotADirectoryError):
            continue
        except OSError as error:
            raise CompatibilityError(f"Cannot inspect Omarchy plugins: {error.strerror}.") from error
        for path in sorted(candidates):
            manifest = read_manifest(path / "manifest.json")
            if manifest is not None and manifest.get("id") == HOST_ID:
                return path, manifest
    raise CompatibilityError("Omalaunch is not installed. Install and enable quantumfire.omalaunch first.")


def require_host(path: Path | None = None, *, home: Path | None = None,
                 omarchy_path: Path | None = None) -> HostSupport:
    if path is None:
        path, manifest = find_host(home=home, omarchy_path=omarchy_path)
    else:
        path = path.expanduser().resolve()
        manifest = read_manifest(path / "manifest.json")
        if manifest is None or manifest.get("id") != HOST_ID:
            raise CompatibilityError(f"No valid Omalaunch manifest at {path}.")
    metadata = manifest.get("omalaunch")
    features = metadata.get("hostFeatures") if isinstance(metadata, dict) else None
    if (not isinstance(features, list)
            or any(not isinstance(feature, str) for feature in features)
            or HOST_FEATURE not in features):
        raise CompatibilityError(
            f"Omalaunch at {path} lacks {HOST_FEATURE}. "
            "Apply the companion host patch in integration/ or use a host that advertises this API; "
            "unmodified Omalaunch 0.5.3 is unsupported."
        )
    return HostSupport(path=path, version=str(manifest.get("version", "unknown")))

# Omalaunch Files Drag & Drop

Your launcher found the file. Let it hand it over.

Drag files and folders from Omalaunch’s **Files** browser or search results into applications that accept file drops. The launcher steps aside while you drag, then closes when you drop or cancel. Drags offer copy operations, so your originals stay put.

This optional extension provides the `files` capability with native dragging enabled. The current package version is **0.1.0**.

> **A compatible Omalaunch host is required.** Stock Omalaunch 0.5.3 cannot provide native dragging through an extension alone. Install the companion host integration before enabling this plugin; building or installing the plugin does not apply it for you.

## Requirements

- Omarchy with Omalaunch (`quantumfire.omalaunch`) installed and enabled.
- A host implementing and advertising `files.drag-and-drop.v1`. The source checkout includes [host integration instructions](integration/README.md) and a patch for the exact Omalaunch 0.5.3 base recorded there.
- Python 3 available as both `python3` and `python`: the plugin scripts use `python3`, while the Files commands require `python`.
- `fd`, `fzf`, `jq`, `xdg-open`, `xdg-terminal-exec`, and `wl-copy` on `PATH`.
- A destination application that accepts native file drops.

The host owns the Files interface and native Qt/Quickshell drag handling. This plugin supplies the provider definition and checks for the host API before publishing it. On an unsupported host, it reports the missing integration instead of advertising a Files replacement with broken dragging.

## Install from a local checkout

From this repository’s root, check the deployed host and build the archive if the check passes:

```bash
./bin/doctor && python3 tools/build.py
```

The doctor is read-only. It checks the discovered host’s manifest and required executables on `PATH`; it does not verify that the host is enabled or test a live drag.

The build creates `dist/secretweapon.omalaunch-files-drag-drop-0.1.0.tar.gz`. Install it into a new plugin directory:

```bash
(
  set -eu
  plugins_dir="$HOME/.config/omarchy/plugins"
  target="$plugins_dir/secretweapon.omalaunch-files-drag-drop"
  mkdir -p "$plugins_dir"
  mkdir "$target"
  tar -xzf dist/secretweapon.omalaunch-files-drag-drop-0.1.0.tar.gz -C "$target"
  omarchy shell shell rescanPlugins
  omarchy plugin enable secretweapon.omalaunch-files-drag-drop
  omarchy restart shell
)
```

The installer stops if the target directory already exists, preserving an existing installation. Building an archive is a local packaging step; it does not publish a release or marketplace listing.

## Your first drag

1. Open Omalaunch with **Super + Space**.
2. Choose **Extensions → Files**, or type `files` and activate the result.
3. Browse from your home directory or search for a file or folder.
4. Hold the **left mouse button** on its result row and drag it onto the destination window.

The launcher gets out of the way so the receiving app can take the drop. Press **Escape** to cancel. A normal click still opens a file or navigates into a folder.

Dragging works on actual file and folder results. Parent-navigation rows, action-menu commands, and workflow pickers keep their usual behavior. Each drag carries one local file or folder as `text/uri-list` with copy semantics.

For a shorter trip next time, select the **Files extension shortcut** and press **Ctrl + S** to star it on the launcher’s starting screen.

## Providers and favorites

This extension advertises the `files` capability at priority **20**, normally replacing bundled Files while enabled. An explicitly selected, available provider in `~/.config/omarchy/omalaunch/config.jsonc` takes precedence over priority.

Preferences belong to their provider. This extension does not inherit the bundled Files shortcut’s star, configuration, or file favorites. Per-file and per-folder favorites are currently supported only by bundled Files; this extension supports starring its **extension shortcut**. The bundled provider’s existing data stays in place for when you switch back.

To disable the extension:

```bash
omarchy plugin disable secretweapon.omalaunch-files-drag-drop
omarchy restart shell
```

After reload, bundled Files normally returns with its existing favorites, unless another provider is selected. To remove the extension entirely, use:

```bash
omarchy plugin remove secretweapon.omalaunch-files-drag-drop
```

## Troubleshooting

Start with `./bin/doctor` from the source checkout or installed plugin directory. It exits with status `0` on success and `1` on a reported compatibility or dependency failure. For machine-readable output:

```bash
./bin/doctor --json
```

| Symptom | What to check |
| --- | --- |
| `lacks files.drag-and-drop.v1` | The host found by the doctor lacks the required API. Follow the source checkout’s [integration guide](integration/README.md), deploy the compatible host, and rerun the doctor. |
| `Missing executables` | Install the named commands and ensure they are on the launcher’s `PATH`. Both `python3` and `python` must resolve to Python 3. |
| A patched checkout passes, but the plugin still rejects the host | `--host` checks only the path you give it. Run the doctor without that option to check the host the catalog actually discovers. |
| The doctor passes, but Files behaves like the bundled provider | Confirm this plugin is enabled, restart the shell, and check for an explicit `files` provider selection in Omalaunch’s configuration. |
| A drop does nothing | Try an application known to accept file drops. The doctor checks declarations and executable availability; native drop acceptance still needs a live check on your desktop. |

**Host discovery order matters.** The catalog and default doctor look for `quantumfire.omalaunch` in `$OMARCHY_PATH/shell/plugins` first (`OMARCHY_PATH` defaults to `/usr/share/omarchy`), then in `~/.config/omarchy/plugins`. The first matching manifest wins, with directory names sorted within each root. An incompatible managed host can therefore shadow a compatible user copy.

To inspect a patched source checkout before deploying it:

```bash
./bin/doctor --host /path/to/patched/omalaunch
```

This override is available only to the doctor. The catalog always uses normal host discovery.

## Development and packaging

Work in a source checkout outside Omarchy’s watched plugin directory. Keep the extension independent from the host: native UI changes belong in the versioned host integration, and plugin startup or installation must never patch host files.

| Path | Purpose |
| --- | --- |
| [`manifest.json`](manifest.json) | Plugin identity and catalog entry point. |
| [`omalaunch.json`](omalaunch.json) | Files provider, priority, drag opt-in, and file action commands. |
| [`bin/catalog`](bin/catalog) | Publishes the provider only when the discovered host advertises the API. |
| [`bin/doctor`](bin/doctor), [`lib/host_support.py`](lib/host_support.py) | Diagnostics, manifest checks, and host discovery. |
| `integration/` | Companion host patch and instructions; source checkout only. |
| `tests/`, `tools/build.py` | Automated checks and archive builder; source checkout only. |

Before distributing a package, run:

```bash
python3 -m unittest discover -s tests -v
python3 tools/build.py
```

The tests cover host discovery, compatibility failures, catalog output, dependency diagnostics, provider commands, and reproducible packaging. Native desktop drag verification is covered separately in the source checkout’s [integration guide](integration/README.md).

The builder uses only Python’s standard library and accepts `--output-dir PATH`. It includes exactly seven runtime files: `LICENSE`, `README.md`, `manifest.json`, `omalaunch.json`, `bin/catalog`, `bin/doctor`, and `lib/host_support.py`. The manifest sits at the archive root. File order, permissions, ownership, and timestamps are normalized for reproducible archives.

The runtime archive excludes `integration/`, `tests/`, and `tools/`. Keep the source checkout for the host patch and development instructions linked above.

## License

[MIT](LICENSE). The Files provider command definitions are adapted from Omalaunch, copyright 2026 Daniel Lemky.

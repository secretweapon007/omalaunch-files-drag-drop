# Omalaunch Files Drag & Drop

An optional Omalaunch extension that lets you drag files and folders from the **Files** browser or its search results into applications that accept file drops. The launcher gets out of the way during the drag and closes when you drop or cancel. The source offers copy operations, so the originals stay in place. Press **Escape** to cancel.

This is version **0.1.0**, prepared as a local plugin source package. It has not been published to a plugin marketplace or remote repository.

## Compatibility

Omalaunch owns its Files interface; ordinary extension definitions cannot inject QML or pointer handlers. This plugin therefore requires the companion Omalaunch host integration advertising `files.drag-and-drop.v1` in its manifest. The integration adds the native drag implementation and the Files-only `dragAndDrop` extension option. Stock Omalaunch **0.5.3** does not provide this API.

Install that host integration before enabling this plugin. Its source patch and instructions are supplied separately under `integration/` in this source checkout; they are not runtime files installed with the plugin. No host files are patched by the plugin itself.

Run the read-only compatibility check from this checkout:

```bash
./bin/doctor
```

The catalog provider also checks compatibility before contributing its Files definition. On a host without the required API, it reports the missing integration instead of presenting a Files replacement with nonfunctional dragging.

The plugin uses the normal Files dependencies: Python 3, `fd`, `fzf`, `jq`, `xdg-open`, `xdg-terminal-exec`, and `wl-copy`. Native dragging requires a Qt/Quickshell host with the companion integration; destination applications must accept file drops.

## Install from this local checkout

After installing the host integration and passing `./bin/doctor`, build the runtime archive:

```bash
python3 tools/build.py
```

Install it into a new plugin directory. This example stops if the target already exists and does not overwrite an existing installation:

```bash
(
  set -eu
  target="$HOME/.config/omarchy/plugins/secretweapon.omalaunch-files-drag-drop"
  mkdir "$target"
  tar -xzf dist/secretweapon.omalaunch-files-drag-drop-0.1.0.tar.gz -C "$target"
  omarchy shell shell rescanPlugins
  omarchy plugin enable secretweapon.omalaunch-files-drag-drop
  omarchy restart shell
)
```

No Git installation URL is needed for a local package. After the source has a published repository, Omarchy can use its normal `omarchy plugin add <git-url> --enable` workflow.

## Use

Open Omalaunch with **Super + Space**, then choose **Extensions → Files**, or type `files` and activate the result. Browse or search for a file, hold the left mouse button on its row, and drag it onto the destination window. A normal click still opens a file or folder.

Press **Ctrl + S** on the **Files extension shortcut** to show it on the launcher's starting screen. This star belongs to this plugin's provider ID; it does not inherit the bundled Files shortcut's star.

This provider replaces the bundled `files` capability while enabled, with priority 20. If you explicitly selected another provider for that capability in Omalaunch's core configuration, that selection continues to take precedence.

Per-file and per-folder favorite storage is currently implemented only for bundled Files. This external provider supports starring its extension shortcut; it does not adopt or rewrite the bundled provider's file favorites or configuration. Those files remain available when the bundled provider is restored.

## Disable

```bash
omarchy plugin disable secretweapon.omalaunch-files-drag-drop
omarchy restart shell
```

After the catalog reloads, Omalaunch restores its bundled Files provider, including that provider's existing favorites. To remove the plugin, use `omarchy plugin remove secretweapon.omalaunch-files-drag-drop`.

## Build and verify

```bash
python3 -m unittest discover -s tests -v
python3 tools/build.py
```

The builder includes only the declared runtime files, puts `manifest.json` at the archive root, and normalizes ordering, permissions, ownership, and timestamps for reproducible archives. Development files and the companion host patch remain outside the runtime archive.

## License

MIT. The Files provider command definitions are adapted from Omalaunch, copyright 2026 Daniel Lemky; see `LICENSE`.

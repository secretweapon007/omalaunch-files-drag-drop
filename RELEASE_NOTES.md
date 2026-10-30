# Omalaunch Files Drag & Drop v0.1.0

*Draft notes for the first release.*

A little less window juggling. Find a file in Omalaunch, grab it, and drop it into the app that needs it. This optional extension brings native file and folder dragging to the **Files** browser and its search results, with a companion host integration handling the handoff.

## What’s included

- **Drag from browsing or search.** Hold the left mouse button on a file or folder result and drag it into an application that accepts file drops.
- **A launcher that steps aside.** Omalaunch hides its interface during the drag so the destination window can receive the drop, then closes when you finish or cancel.
- **Originals stay put.** Drags offer copy operations. Press **Escape** to cancel; ordinary clicks still open files or navigate into folders.
- **An optional Files provider.** Enable the extension to use its drag-capable Files browser. Disable it to return to the normal provider selection, usually bundled Files with its existing favorites.
- **A read-only compatibility doctor.** `./bin/doctor` checks the host API and required executables. Use `--json` for structured output or `--host PATH` to inspect a patched checkout before deployment.
- **Reproducible packaging.** The standard-library Python builder produces a runtime archive with consistent file order, permissions, ownership, and timestamps.

## Before you install

**This extension requires an Omalaunch host implementing and advertising `files.drag-and-drop.v1`. Stock Omalaunch 0.5.3 is unsupported.**

The source includes a companion patch for the exact Omalaunch 0.5.3 base specified in the [host integration guide](https://github.com/secretweapon007/omalaunch-files-drag-drop/blob/main/integration/README.md). Apply and deploy that integration before enabling the extension. The plugin checks for the API and reports an actionable error when it is missing; plugin installation does not patch the host.

You also need Omarchy with Omalaunch enabled, Python 3 available as both `python3` and `python`, and `fd`, `fzf`, `jq`, `xdg-open`, `xdg-terminal-exec`, and `wl-copy` on `PATH`.

Run `./bin/doctor` against the installed host, then follow the [installation instructions](https://github.com/secretweapon007/omalaunch-files-drag-drop/blob/main/README.md#install-from-a-local-checkout). The runtime archive is named `secretweapon.omalaunch-files-drag-drop-0.1.0.tar.gz`; the host patch remains in the source checkout’s `integration/` directory.

## Known limitations

- Each drag carries **one file or folder**. Parent-navigation rows, action-menu commands, and workflow pickers are not drag sources.
- The **Files extension shortcut** can be starred with **Ctrl + S**. Individual file and folder favorites remain a bundled Files feature. This provider keeps its own identity and does not inherit bundled configuration or favorites; existing bundled data stays in place.
- An explicitly selected, available Files provider takes precedence over this extension’s automatic selection.
- Drop acceptance depends on the receiving application and desktop environment. The doctor checks manifest declarations and executable availability; verify an actual drop on your desktop after setup.

## Credits

Licensed under the [MIT license](https://github.com/secretweapon007/omalaunch-files-drag-drop/blob/main/LICENSE). Files provider command definitions are adapted from Omalaunch by Daniel Lemky.

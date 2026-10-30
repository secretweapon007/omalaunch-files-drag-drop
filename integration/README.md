# Omalaunch host integration

This is a proposed host API for the accompanying Files Drag & Drop plugin. It is not part of an upstream release. Stock Omalaunch 0.5.3 ignores the extension's `dragAndDrop` field and cannot add native dragging through JSON extensions alone.

The patch in this directory adds the necessary UI behavior to a clean Omalaunch 0.5.3 checkout at commit `2f464963b7471b54bb917341c07847c1387d3ac8`. It excludes this machine's starting-screen ordering and direct-extension-routing customizations. The runtime plugin archive does not contain or apply this patch.

## Apply to a source checkout

Use a clean development checkout, outside the installed Omarchy plugin directory. Review the patch before applying it. From that checkout, using the actual path to this package:

```bash
git switch -c feat/files-drag-api-v1 2f464963b7471b54bb917341c07847c1387d3ac8
git apply --check /path/to/omalaunch-files-drag-drop/integration/omalaunch-0.5.3-files-drag-api-v1.patch
git apply /path/to/omalaunch-files-drag-drop/integration/omalaunch-0.5.3-files-drag-api-v1.patch

node tests/menu-model-test.js
node tests/menu-layout-test.js
node tests/files-action-panel-test.js
node tests/file-parent-navigation-test.js
bash tests/manifest-test.sh
qmllint -I /usr/lib/qt6/qml FileDragSource.qml
git diff --check
```

The exact base matters: newer versions or a checkout with local UI changes may require a manual merge. Do not force the patch over unrelated work. This preparation does not change the running launcher. Deploy a reviewed host snapshot through your normal Omarchy plugin workflow, then run `omarchy restart shell`.

From this plugin's source directory, the read-only check can inspect the patched source before deployment:

```bash
./bin/doctor --host /path/to/patched/omalaunch
```

After deploying that host, `./bin/doctor` without `--host` must pass before enabling the plugin. The catalog always checks the installed host; the source override is available only to the diagnostic command.

## API contract

The host advertises its implementation in `manifest.json`:

```json
"omalaunch": {
  "hostFeatures": ["files.drag-and-drop.v1"]
}
```

A `mode: "files"` extension opts in with `"dragAndDrop": true`. Omission or `false` preserves ordinary Files behavior. Non-boolean values and use in other extension modes are rejected. Native dragging is implemented by Omalaunch; providers do not load arbitrary QML.

The stable drag source snapshots an encoded local-file URI and offers `text/uri-list` with `Qt.CopyAction`. It survives file-result delegate refreshes. The host keeps its Wayland surface mapped, hides the card and scrim, releases its focus grab, and uses an empty input mask so an underlying window can receive the drop. The launcher closes after the native drag loop returns. Ordinary file clicks, navigation rows, action menus, and workflow pickers keep their existing behavior.

## Verification

The patch includes normalizer and provider-resolution tests covering opt-in, default-off behavior, malformed declarations, external selection, disable fallback, and unavailable-provider fallback. The source component passes `qmllint`.

The exported patch was applied to a fresh checkout of the recorded base and reproduced every reviewed host file. The actual Omalaunch Python loader, dynamic plugin provider, and JavaScript normalizer were exercised together: enabling this plugin selected drag-capable Files; disabling it restored bundled Files with dragging off; an unsupported host rejected the plugin with an actionable diagnostic and retained bundled Files.

The native implementation was also exercised on this machine with a separate Wayland Qt application: file and folder drops crossed processes, names containing spaces, accents, and `#` arrived as correctly encoded URIs, originals stayed in place, Escape delivered no drop, and a normal folder click still navigated. The packaging and host-marker checks have their own automated tests in the plugin source. A deployment using a different compositor should also verify native drop acceptance there.

## Scope

The host patch does not activate drag-and-drop for bundled Files by default and does not migrate any preferences or favorites. Only an active provider that opts in enables dragging. Disabling the external plugin restores the bundled Files capability. Omalaunch's current bundled-only per-file favorite storage is outside this patch; the external Files provider can star its extension shortcut but does not share bundled file favorites.

# Development

- Develop in this source checkout, outside Omarchy's watched installed plugin directory.
- Keep this optional extension independent from the Omalaunch source tree.
- The plugin contributes the `files` capability through its catalog provider. Native drag handling remains a versioned host API; do not patch host files from plugin startup or installation.
- Keep the compatibility check and runtime archive contents aligned. Unsupported hosts must receive an actionable diagnostic rather than a nonfunctional Files replacement.
- Preserve provider-owned configuration and state boundaries; do not migrate or share the bundled provider's data implicitly.
- Validate with `python3 -m unittest discover -s tests -v` and `python3 tools/build.py` before distributing a package.
- Keep marketplace and remote publication separate from local packaging; do not describe an unpublished package as released.

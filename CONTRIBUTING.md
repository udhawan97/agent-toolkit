# Contributing

Open an issue before adding a broad workflow or a connector. Keep pull requests focused, preserve the public/private boundary, and explain the user workflow the change improves.

Before submitting:

1. Run `python bin/agent-kit validate --native` (use `python3` if your system does not provide a `python` command).
2. Run `python -m unittest discover -s tests -v`.
3. On macOS/Linux, run `sh -n bin/setup`. On Windows, run `./bin/setup.ps1 help` in PowerShell.
4. Run the isolated Codex and Claude lifecycle in `docs/TESTING.md`. The sample environment setup uses a POSIX shell; adapt temporary directories and environment variables when validating Windows-native clients.
5. Render-inspect changed SVG and raster assets and confirm README links remain valid.
6. Confirm no personal absolute paths, credentials, or private evidence entered the diff.
7. Update the changelog and compatibility matrix for observable changes.

By contributing, you agree that your contribution is licensed under the repository's MIT License.

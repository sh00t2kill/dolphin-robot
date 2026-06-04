# Contributing

Thanks for helping improve MyDolphin Plus. Contributions are welcome as bug reports, documentation updates, translations, tests, and code changes.

## Before opening a pull request

- Check existing issues and pull requests to avoid duplicate work.
- Keep changes focused on one fix or feature at a time.
- Update `README.md`, `CHANGELOG.md`, or files in `docs/` when behavior or user-facing setup changes.
- For Home Assistant changes, follow the existing integration structure under `custom_components/mydolphin_plus/`.

## Development setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run checks that are relevant to your change before opening a pull request.

This project uses `pyproject.toml` configuration for formatting, import sorting, linting, and tests.

## Pull request guidelines

- Branch new development work from `develop` and open pull requests back into `develop`.
- Use `develop` for pre-release changes before they are promoted to a stable release.
- Explain the user-visible change and why it is needed.
- Include test details, even when the test is manual.
- Keep secrets, tokens, account emails, and robot identifiers out of issues, logs, and pull requests.
- Prefer small, reviewable pull requests over broad refactors.

## Contributors

Thanks to everyone who has contributed to this project:

- [Elad Bar](https://github.com/elad-bar)
- Dan Wheaton
- [sh00t2kill](https://github.com/sh00t2kill)
- [tigers75](https://github.com/tigers75)
- [Loïc](https://github.com/zoic21)
- Gil Peeters
- [devilismyfriend](https://github.com/devilismyfriend)
- [yumlevi](https://github.com/yumlevi)
- [grillp](https://github.com/grillp)
- [lordlala](https://github.com/lordlala)

If you contributed and are missing from this list, please open a pull request to add your name.

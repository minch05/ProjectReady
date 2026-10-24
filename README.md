# ProjectReady

ProjectReady v0.1 diagnoses whether a Python project's declared environment is
ready, without installing packages, changing files, running project code or
external commands, or accessing the network. Requires Python 3.11+ and `packaging`.

```sh
projectready check samples/ready
projectready check samples/missing-env --json
projectready check samples/python-mismatch --format json
```

It checks `requires-python`, dependency declarations and installed distribution
versions, and missing `.env` keys compared with `.env.example`. It inspects the
**Python environment running the command** and does **not automatically discover
or switch to a separate virtual environment**. A PASS does **not guarantee that
the application will run successfully**.

Exit codes: `0` = PASS/SKIP only, `1` = warnings without failures, `2` = failures.
The samples contain only fake values and deliberately empty dependency lists;
they demonstrate diagnostics, not runnable applications or dependency coverage.

See [executed demo examples](DEMO.md) for terminal and JSON output, and
[validation records](VALIDATION.md) for historical results and current demo checks.
Licensed under the [MIT License](LICENSE). Copyright (c) 2026 minch05.

## Installation and usage

Install into your chosen Python 3.11+ environment when you are ready:

```sh
python -m pip install .
projectready check ./your-project
projectready check ./your-project --json
projectready check ./your-project --format json
```

The installed `projectready` command uses the interpreter chosen at installation.
For an explicit interpreter, use `python -m projectready`.

Installation requires setuptools and packaging. The checker itself never installs
anything. For an existing environment containing packaging, run from source:

```sh
PYTHONPATH=src python -m projectready check samples/ready
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Checks

- Parse `pyproject.toml` with `tomllib` and validate `[project].requires-python`
  against the current interpreter using `packaging`.
- Detect `[project].dependencies` and root `requirements.txt`, including explicitly
  empty definitions. Inspect both sources when both exist.
- Evaluate PEP 508 markers and compare installed distribution versions with declared
  specifiers. Missing packages and incompatible versions fail.
- Compare assignment key names in `.env.example` with `.env`. Missing keys warn.
  `export KEY=value`, whitespace, duplicate keys, and UTF-8 BOMs are supported.
  A present but empty key counts as present. Process environment variables do not
  substitute for `.env` keys.

## Status and exit codes

| Status | Meaning |
| --- | --- |
| PASS | A supported check passed |
| WARN | Missing configuration or a declaration that cannot be fully verified |
| FAIL | Invalid/unreadable input, incompatible Python, or missing/incompatible package |
| SKIP | Optional input is absent or a dependency marker does not apply |

Exit code `0` means only PASS/SKIP results, `1` means at least one WARN and no FAIL,
and `2` means at least one FAIL. Argument errors also use argparse's exit code `2`.
An empty directory warns because it has no supported dependency definition.

JSON output contains `schema_version`, a `checks` array of `name`, `status`, and
`message`, a `summary` count for each status, and `exit_code`. Diagnostic JSON is
written to stdout; argparse usage errors are written to stderr.

## Privacy

Environment values are never included in diagnostic output or logs. Only missing
key names are displayed. Raw dependency declarations, URLs, parser exception
details, and invalid installed version metadata are withheld. Arbitrary non-PEP-440 `===` version strings are
withheld: dependencies warn and invalid Python requirements fail. Parsed package
names, version specifiers, and valid installed versions are displayed to make
diagnostics actionable. Dependency checks use ordinal identifiers such as
`dependency_1`, in pyproject dependency order followed by requirements file order. No log files are
created. Environment files are read in memory solely to extract assignment keys.

## v0.1 limitations

The CLI checks its own interpreter and installed metadata, not a project's separate
virtual environment. Run it with the intended interpreter. It does not prove that
imports, native libraries, services, or application execution will work.

Only PEP 621 runtime dependencies and root requirements files are supported.
Optional dependency groups, Poetry/Pipenv declarations, lockfiles, and build-system
requirements are not resolved. Dynamic dependencies warn. Requirements include
files, pip options, hashes, editable installs, multiline declarations, extras, and
direct URLs warn and are not followed or executed. Markers use the current runtime
environment. Continuation lines are not inspected as separate package
requirements. No transitive dependency resolution is performed.

Environment parsing recognizes single-line assignments, including quoted values.
Multiline quoted values, continuations, and unrecognized lines produce WARN and
stop key comparison rather than reporting an unverified PASS. This is not a full
shell/dotenv parser. It does not validate values or expand variables. Missing
`.env.example`
skips the comparison. Filesystem inspection is not an atomic snapshot; symbolic
links are followed. The checker performs no writes to the inspected project, but
normal filesystem read-access metadata may be updated by the operating system.

## Demo files

- `samples/ready`: matching Python requirement and all example keys present; exit `0`.
- `samples/missing-env`: the fake `DEMO_TOKEN` key is absent from `.env`; exit `1`.
- `samples/python-mismatch`: intentionally requires Python `>=99`; exit `2` on
  current Python 3.11+ interpreters below version 99.

Sample `.env` files are intentionally included as public fake fixtures. Real
`.env` files remain ignored. Do not replace the sample values with credentials.
Run these commands from the repository root; no sample setup or copying is needed.
Actual version strings in output depend on the interpreter running the command.

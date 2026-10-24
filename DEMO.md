# Executed demo examples

Captured on 2026-10-25 using Python 3.12.14, packaging 26.3,
and ProjectReady 0.1.0. These are deliberately constructed sample projects,
not real application validation. No packages were installed.

Commands run from the repository root. The selected interpreter executable is
shown as `python` to keep machine-specific paths private. Use Python 3.11+ with
packaging available. Output version strings may differ on another interpreter.

The three checked-in sample `.env` files contain only fake values. Their empty
dependency lists isolate the Python and environment-key checks; they do not
demonstrate installed-package verification.

## ready

Terminal command:

```sh
PYTHONPATH=src python -B -m projectready check samples/ready
```

Captured stdout:

```text
PASS project: Project directory is accessible.
PASS pyproject: pyproject.toml is valid TOML.
PASS python: Python 3.12.14; required >=3.11: compatible.
PASS dependency_definitions: Dependency definitions detected.
PASS environment: All example keys are present in .env.
Exit code: 0
```

Process exit code: `0`.

JSON command:

```sh
PYTHONPATH=src python -B -m projectready check samples/ready --json
```

Captured stdout:

```json
{
  "schema_version": 1,
  "checks": [
    {
      "name": "project",
      "status": "PASS",
      "message": "Project directory is accessible."
    },
    {
      "name": "pyproject",
      "status": "PASS",
      "message": "pyproject.toml is valid TOML."
    },
    {
      "name": "python",
      "status": "PASS",
      "message": "Python 3.12.14; required >=3.11: compatible."
    },
    {
      "name": "dependency_definitions",
      "status": "PASS",
      "message": "Dependency definitions detected."
    },
    {
      "name": "environment",
      "status": "PASS",
      "message": "All example keys are present in .env."
    }
  ],
  "summary": {
    "PASS": 5,
    "WARN": 0,
    "FAIL": 0,
    "SKIP": 0
  },
  "exit_code": 0
}
```

Process exit code: `0`. `--format json` was also executed and produced
the same parsed JSON and process exit code.

## missing-env

Terminal command:

```sh
PYTHONPATH=src python -B -m projectready check samples/missing-env
```

Captured stdout:

```text
PASS project: Project directory is accessible.
PASS pyproject: pyproject.toml is valid TOML.
PASS python: Python 3.12.14; required >=3.11: compatible.
PASS dependency_definitions: Dependency definitions detected.
WARN environment: Missing .env keys: DEMO_TOKEN
Exit code: 1
```

Process exit code: `1`.

JSON command:

```sh
PYTHONPATH=src python -B -m projectready check samples/missing-env --json
```

Captured stdout:

```json
{
  "schema_version": 1,
  "checks": [
    {
      "name": "project",
      "status": "PASS",
      "message": "Project directory is accessible."
    },
    {
      "name": "pyproject",
      "status": "PASS",
      "message": "pyproject.toml is valid TOML."
    },
    {
      "name": "python",
      "status": "PASS",
      "message": "Python 3.12.14; required >=3.11: compatible."
    },
    {
      "name": "dependency_definitions",
      "status": "PASS",
      "message": "Dependency definitions detected."
    },
    {
      "name": "environment",
      "status": "WARN",
      "message": "Missing .env keys: DEMO_TOKEN"
    }
  ],
  "summary": {
    "PASS": 4,
    "WARN": 1,
    "FAIL": 0,
    "SKIP": 0
  },
  "exit_code": 1
}
```

Process exit code: `1`. `--format json` was also executed and produced
the same parsed JSON and process exit code.

## python-mismatch

Terminal command:

```sh
PYTHONPATH=src python -B -m projectready check samples/python-mismatch
```

Captured stdout:

```text
PASS project: Project directory is accessible.
PASS pyproject: pyproject.toml is valid TOML.
FAIL python: Python 3.12.14; required >=99: incompatible.
PASS dependency_definitions: Dependency definitions detected.
PASS environment: All example keys are present in .env.
Exit code: 2
```

Process exit code: `2`.

JSON command:

```sh
PYTHONPATH=src python -B -m projectready check samples/python-mismatch --json
```

Captured stdout:

```json
{
  "schema_version": 1,
  "checks": [
    {
      "name": "project",
      "status": "PASS",
      "message": "Project directory is accessible."
    },
    {
      "name": "pyproject",
      "status": "PASS",
      "message": "pyproject.toml is valid TOML."
    },
    {
      "name": "python",
      "status": "FAIL",
      "message": "Python 3.12.14; required >=99: incompatible."
    },
    {
      "name": "dependency_definitions",
      "status": "PASS",
      "message": "Dependency definitions detected."
    },
    {
      "name": "environment",
      "status": "PASS",
      "message": "All example keys are present in .env."
    }
  ],
  "summary": {
    "PASS": 4,
    "WARN": 0,
    "FAIL": 1,
    "SKIP": 0
  },
  "exit_code": 2
}
```

Process exit code: `2`. `--format json` was also executed and produced
the same parsed JSON and process exit code.

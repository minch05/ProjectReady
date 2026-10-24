# Validation record

This document separates historical validation from the new demo executions.
External project names and all personal filesystem paths are intentionally omitted.
No external project source, configuration, or credentials are included.

## Historical validation: 2026-10-25

The results in this section are from the previous development task and its
completion report. They were not rerun during this demo-preparation task. This is
a summary of recorded results, not a newly captured test log.

### Unit tests and temporary fixtures

The supplied revision's 25 unittest tests passed. After targeted privacy and
false-failure fixes, the full suite contained 29 tests and all passed under
Python 3.12.14. These tests used temporary synthetic projects and mocked package
metadata where appropriate. They do not represent 29 real projects.

Coverage included Python compatibility, dependency declarations and installed
versions, conditional markers, environment key comparison, multiline environment
syntax warnings, invalid metadata redaction, read-only behavior, and terminal/JSON
output with exit codes 0, 1, and 2. The checker did not invoke external commands
in the guarded read-only test. Python source comment tokens were also checked;
none were found.

### Real project checks

Three existing projects were inspected: ProjectReady itself and two external
projects. The external identifiers below are anonymous labels, not project names.
All checks used the same Python 3.12.14 environment running ProjectReady.

| Existing project | PASS | WARN | FAIL | SKIP | Process exit code |
| --- | ---: | ---: | ---: | ---: | ---: |
| ProjectReady itself | 5 | 0 | 0 | 1 | 0 |
| External project A | 2 | 0 | 2 | 3 | 2 |
| External project B | 8 | 0 | 22 | 3 | 2 |

The external FAIL results indicated dependencies missing from the interpreter
running the checker. They did not establish whether those projects' own virtual
environments were prepared. No virtual environment was discovered or activated.
All three projects lacked `.env.example`, so their environment comparisons were
SKIP. Multiline parsing and missing-key behavior were verified with temporary
test fixtures instead, not by these real project checks.

For each existing project, terminal, `--json`, and `--format json` were run.
Per-check results, JSON summaries, and process exit codes agreed across formats;
no stderr output occurred. Existing environment assignment values of at least
four characters were compared with outputs in memory; no matches were found.
This was a targeted check, not proof that every possible secret pattern is absent.

File content hashes, modification times, and permissions were unchanged across
these diagnostic runs. The comparison covered 8 files in ProjectReady, 9 in
external project A, and 2,791 in external project B. It excluded virtual
environments, caches, Git internals, and dependency directories. Filesystem access
times were not part of the comparison.

## New demo executions: 2026-10-25

These checks were actually run during demo preparation, using Python 3.12.14,
packaging 26.3, and ProjectReady 0.1.0. Only the samples below were rerun; the
historical unit suite and external projects above were not rerun in this task.
The runtime and test source files and project metadata were kept unchanged.

All three projects below are purpose-built samples with fake environment values
and empty dependency lists. They are not real applications, and their results do
not demonstrate dependency installation checks or application execution.

| Synthetic sample | PASS | WARN | FAIL | SKIP | Process exit code |
| --- | ---: | ---: | ---: | ---: | ---: |
| `samples/ready` | 5 | 0 | 0 | 0 | 0 |
| `samples/missing-env` | 4 | 1 | 0 | 0 | 1 |
| `samples/python-mismatch` | 4 | 0 | 1 | 0 | 2 |

Each sample was run in terminal mode, with `--json`, and with `--format json`:
nine actual CLI processes in total. Per-check terminal messages matched JSON
records; JSON summary counts, embedded exit codes, and process exit codes agreed.
Both JSON options produced the same parsed report, and stderr was empty.
The sample file content hashes and modification times were unchanged, and no
fake environment values appeared in output. See [DEMO.md](DEMO.md) for captured
stdout and reproducible commands. Only the command's interpreter path is
represented generically as `python`; the diagnostic output is not rewritten.

## Public-file review

The intended public set is `.gitignore`, `pyproject.toml`, `README.md`, `DEMO.md`,
`VALIDATION.md`, `LICENSE`, Python files under `src/` and `tests/`, and the nine files under
`samples/`. No private reports, external project copies, or raw external logs
are included. The sample `.env` files are explicit fake-fixture exceptions to the
normal `.env` ignore rule. No real `.env` file is included.

The public set was reviewed for personal paths and external project names,
credential-like patterns, private keys, unexpected environment files, and cache
or build artifacts. No real credentials, personal paths, external project names,
or cache/build artifacts were found. Test sentinel strings and deliberately fake
sample tokens remain as fixtures. This is a local review of the listed files,
not a certification or a scan of a future Git history or release archive.

During that demo-preparation task, no packages were installed, no runtime features
were added, and no commit, push, release upload, or public deployment was performed.
License selection was pending at that stage. The later publication-preparation
step added the approved MIT LICENSE with Copyright (c) 2026 minch05.


## Publication preparation recheck: 2026-10-25

After publication approval, the existing 29-test unittest suite was rerun under
Python 3.12.14 and all tests passed. The three synthetic samples were also rerun
in terminal mode and both JSON modes (nine CLI processes). Exit codes were 0, 1,
and 2 as documented. Captured outputs matched DEMO.md, both JSON modes agreed,
and stderr was empty. Sample file hashes and modification times were unchanged;
fake environment values were absent from diagnostic output. The historical
external project checks were not rerun.

The final public inventory contains 20 files including the approved MIT LICENSE.
Runtime source, tests, and pyproject.toml match the prior demo-preparation
baseline. Only release documentation and the license were finalized. The staged
file list is checked to include exactly the three fake sample .env fixtures;
real environment files, draft licenses, caches, and private paths are excluded.


## Developer self-installation check: 2026-10-25

This was personally performed by the developer on **macOS with Python 3.12.14**
against the public v0.1.0 GitHub tag. It is not independent external-user
validation. Two separate temporary checkouts and two fresh Python 3.12.14
virtual environments were used. Neither installation
used the development checkout, an editable install, system site-packages, or
PYTHONPATH. The verified public source commit was
`c9a60d82efd4ca5264c6b4c8868b027344a7d9ef`.

### Installation commands

The first checkout used the following commands. `<TEMP>` represents its private
temporary directory, and `<PYTHON_3_12>` represents the already-installed Python
3.12.14 executable. Only those machine-specific paths are anonymized here.

```sh
git clone --branch v0.1.0 --depth 1 https://github.com/minch05/ProjectReady.git <TEMP>/ProjectReady
cd <TEMP>/ProjectReady
<PYTHON_3_12> -B -m venv <TEMP>/venv
unset PYTHONPATH PYTHONHOME
source <TEMP>/venv/bin/activate
python -m pip install .
```

The original public README supplied `python -m pip install .` but omitted the
clone, change-directory, and virtual-environment setup steps. Those prerequisites
were supplied to carry out this requested check; the original README was not a
complete first-user walkthrough. Installation itself succeeded without changing
the published code or adding extra install commands. Pip installed ProjectReady
0.1.0 and packaging 26.3 and obtained isolated build dependencies. Module location
was verified inside the fresh environment's site-packages; pip direct_url.json
identified the temporary public checkout and showed no editable installation.

### Inspection commands and results

After installation, the actual installed `projectready` executable was run from
the temporary public checkout, not through a source import:

```sh
projectready check samples/ready
projectready check samples/ready --json
projectready check samples/ready --format json
projectready check samples/missing-env
projectready check samples/missing-env --json
projectready check samples/missing-env --format json
projectready check samples/python-mismatch
projectready check samples/python-mismatch --json
projectready check samples/python-mismatch --format json
```

| Synthetic sample | PASS | WARN | FAIL | SKIP | Exit code in all three modes |
| --- | ---: | ---: | ---: | ---: | ---: |
| ready | 5 | 0 | 0 | 0 | 0 |
| missing-env | 4 | 1 | 0 | 0 | 1 |
| python-mismatch | 4 | 0 | 1 | 0 | 2 |

Both JSON options produced equal reports, JSON exit_code matched the process
exit code, terminal check messages matched JSON, and stderr was empty. Sample
hashes and modification times were unchanged. Fake environment values did not
appear in diagnostic output. The public checkout's existing unittest suite also
passed all 29 tests against the installed package with PYTHONPATH unset:

```sh
python -B -m unittest discover -s tests -v
```

### Documentation correction and recheck

Only the local development README and this validation record were changed.
The README now documents cloning the release, entering the repository, verifying
Python 3.11+, creating/activating a virtual environment, installing, and then
running the samples. It distinguishes installation downloads from read-only
checks, expected warning/failure exit codes from installation failures, and the
installed workflow from the optional source-development workflow. Detached HEAD
when checking out a tag and POSIX-only activation instructions are explained.

The corrected command sequence was tested using a second new clone of the same
public tag and a second fresh `.venv`. A pre-existing Python 3.12.14 interpreter
was selected on PATH before running `python3 --version`, `python3 -m venv .venv`,
`. .venv/bin/activate`, and `python -m pip install .`. The second installation
succeeded and all nine installed CLI executions above passed again. Pip reused
its normal download cache on this second run; no system packages were inherited.
In total this task completed two installations and 18 sample CLI executions.

The code was not changed. At the end of that installation-validation task, the
README corrections were local; no commit, push, new tag, or additional publication
had been performed. This validates one macOS/Python 3.12.14 setup, not Windows/Linux
or every supported Python version.

The subsequent documentation-only review cross-checked these results against the
recorded executions and clarified the tested platform in both documents. Only
README.md and VALIDATION.md are updated on main; the v0.1.0 tag and release are
unchanged. Functional tests were not rerun for this documentation-only update.

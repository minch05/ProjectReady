from contextlib import redirect_stdout
from importlib import metadata
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from projectready.checks import Check, check_project, exit_code
from projectready.cli import main


class ProjectReadyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name, content):
        (self.root / name).write_text(content, encoding="utf-8")

    def results(self):
        return {check.name: check for check in check_project(self.root)}

    def test_missing_target(self):
        self.assertEqual(exit_code(check_project(self.root / "missing")), 2)

    def test_file_target(self):
        self.write("file", "")
        self.assertEqual(exit_code(check_project(self.root / "file")), 2)

    def test_empty_project(self):
        results = self.results()
        self.assertEqual(results["python"].status, "SKIP")
        self.assertEqual(results["dependency_definitions"].status, "WARN")
        self.assertEqual(results["environment"].status, "SKIP")

    def test_python_version_ranges(self):
        for spec, expected in [(">=3.11,<4", "PASS"), (">=99", "FAIL"), ("broken", "FAIL"), ("", "FAIL")]:
            with self.subTest(spec=spec):
                self.write("pyproject.toml", f'[project]\nrequires-python = "{spec}"\ndependencies = []\n')
                with patch("projectready.checks.platform.python_version", return_value="3.12.0"):
                    self.assertEqual(self.results()["python"].status, expected)

    def test_broken_toml_is_redacted(self):
        self.write("pyproject.toml", 'secret-value = [broken')
        results = check_project(self.root)
        self.assertEqual(exit_code(results), 2)
        self.assertNotIn("secret-value", repr(results))

    def test_invalid_metadata(self):
        for content in ['project = "bad"', '[project]\ndependencies = 5', '[project]\nrequires-python = 3', '[project]\ndynamic = 2']:
            with self.subTest(content=content):
                self.write("pyproject.toml", content)
                self.assertEqual(exit_code(check_project(self.root)), 2)

    def test_explicit_empty_dependencies(self):
        self.write("pyproject.toml", '[project]\ndependencies = []')
        self.assertEqual(self.results()["dependency_definitions"].status, "PASS")

    def test_dependency_sources_and_versions(self):
        self.write("pyproject.toml", '[project]\ndependencies = ["alpha>=2"]')
        self.write("requirements.txt", "beta==1\n")
        with patch("projectready.checks.metadata.version", side_effect=["2.5", "2"]):
            results = self.results()
        self.assertEqual(results["dependency_1"].status, "PASS")
        self.assertEqual(results["dependency_2"].status, "FAIL")

    def test_missing_dependency(self):
        self.write("requirements.txt", "absent-package")
        with patch("projectready.checks.metadata.version", side_effect=metadata.PackageNotFoundError):
            self.assertEqual(self.results()["dependency_1"].status, "FAIL")

    def test_markers(self):
        self.write("requirements.txt", 'anything; python_version < "1"')
        with patch("projectready.checks.metadata.version") as version:
            self.assertEqual(self.results()["dependency_1"].status, "SKIP")
            version.assert_not_called()

    def test_unsupported_requirements_and_secrets(self):
        self.write("requirements.txt", "-r other.txt\n--index-url https://user:secret@example.test\nname @ https://user:secret@example.test/name.whl\nname[extra]\n")
        results = check_project(self.root)
        self.assertEqual(sum(item.status == "WARN" for item in results), 4)
        self.assertNotIn("secret", repr(results))
        self.assertNotIn("example.test", repr(results))

    def test_dynamic_dependencies(self):
        self.write("pyproject.toml", '[project]\ndynamic = ["dependencies"]')
        self.assertEqual(self.results()["dynamic_dependencies"].status, "WARN")

    def test_environment_keys_only(self):
        self.write(".env.example", "export TOKEN=example-secret\nHOST=localhost\n# IGNORE=hidden\nTOKEN=duplicate\n")
        self.write(".env", "TOKEN=real-secret\nEXTRA=extra-secret\n")
        results = self.results()
        self.assertEqual(results["environment"].status, "WARN")
        self.assertIn("HOST", results["environment"].message)
        self.assertNotIn("secret", repr(results))

    def test_multiline_environment_never_passes(self):
        for filename in (".env", ".env.example"):
            for quote in (chr(34), chr(39)):
                with self.subTest(filename=filename, quote=quote):
                    self.write(".env.example", "TOKEN=placeholder")
                    self.write(".env", "TOKEN=present")
                    self.write(filename, "TEXT=" + quote + "hidden-secret\nTOKEN=hidden-secret\n" + quote)
                    results = check_project(self.root)
                    environment = next(item for item in results if item.name == "environment")
                    self.assertEqual(environment.status, "WARN")
                    self.assertNotIn("hidden-secret", repr(results))

    def test_supported_quoted_environment(self):
        self.write(".env.example", "TOKEN=placeholder\nHOST=localhost")
        self.write(".env", "TOKEN=\"value=abc\" # comment\nHOST='localhost'\n")
        self.assertEqual(self.results()["environment"].status, "PASS")

    def test_ambiguous_environment_warns(self):
        self.write(".env.example", "TOKEN=placeholder")
        for value in ('TOKEN="unfinished', 'TOKEN="value"trailing', "TOKEN=value" + chr(92), "source other.env"):
            with self.subTest(value=value):
                self.write(".env", value)
                self.assertEqual(self.results()["environment"].status, "WARN")

    def test_actionable_version_messages(self):
        self.write("pyproject.toml", '[project]\nrequires-python=">=99"\ndependencies=["alpha>=2"]')
        with patch("projectready.checks.platform.python_version", return_value="3.12.0"), patch("projectready.checks.metadata.version", return_value="1.0"):
            results = self.results()
        for text in ("3.12.0", ">=99"):
            self.assertIn(text, results["python"].message)
        for text in ("alpha", ">=2", "1.0"):
            self.assertIn(text, results["dependency_1"].message)

    def test_invalid_installed_version_is_withheld(self):
        self.write("requirements.txt", "alpha>=2")
        with patch("projectready.checks.metadata.version", return_value="secret-invalid-version"):
            results = check_project(self.root)
        self.assertNotIn("secret-invalid-version", repr(results))
        self.assertEqual(next(item.status for item in results if item.name == "dependency_1"), "WARN")

    def test_arbitrary_version_specifiers_are_withheld(self):
        secret = "https://user:credential-sentinel@example.test"
        self.write("requirements.txt", "alpha===" + secret)
        results = self.results()
        self.assertEqual(results["dependency_1"].status, "WARN")
        self.assertNotIn(secret, repr(results))
        self.assertNotIn("credential-sentinel", repr(results))
        self.write("pyproject.toml", '[project]\nrequires-python="===' + secret + '"')
        results = self.results()
        self.assertEqual(results["python"].status, "FAIL")
        self.assertNotIn("credential-sentinel", repr(results))

    def test_non_string_installed_metadata_warns(self):
        self.write("requirements.txt", "alpha>=2")
        for value in (None, 42, ["credential-sentinel"]):
            with self.subTest(value=value):
                with patch("projectready.checks.metadata.version", return_value=value):
                    results = self.results()
                self.assertEqual(results["dependency_1"].status, "WARN")
                self.assertNotIn("credential-sentinel", repr(results))

    def test_requirement_continuation_is_not_a_separate_package(self):
        self.write("requirements.txt", "alpha" + chr(92) + "\nmissing-package\npackaging")
        with patch("projectready.checks.metadata.version", return_value="26.3") as version:
            results = self.results()
        self.assertEqual(results["dependency_1"].status, "WARN")
        self.assertEqual(results["dependency_2"].status, "PASS")
        self.assertNotIn("dependency_3", results)
        version.assert_called_once_with("packaging")

    def test_output_privacy_and_exit_codes_for_all_statuses(self):
        for requirement, expected in (("packaging", 0), ("-r private.txt", 1), ("projectready-absent-package-sentinel", 2)):
            with self.subTest(expected=expected):
                self.write("requirements.txt", requirement)
                self.write(".env.example", "TOKEN=example-credential-sentinel")
                self.write(".env", "TOKEN=actual-credential-sentinel")
                outputs = []
                for flags in ([], ["--json"], ["--format", "json"]):
                    stream = io.StringIO()
                    with redirect_stdout(stream):
                        code = main(["check", str(self.root), *flags])
                    self.assertEqual(code, expected)
                    output = stream.getvalue()
                    self.assertNotIn("credential-sentinel", output)
                    outputs.append(output)
                    if flags:
                        payload = json.loads(output)
                        self.assertEqual(payload["exit_code"], expected)
                        for item in payload["checks"]:
                            self.assertIn(f'{item["status"]:4} {item["name"]}: {item["message"]}', outputs[0])
                    else:
                        self.assertIn(f"Exit code: {expected}", output)

    def test_missing_env(self):
        self.write(".env.example", "TOKEN=secret")
        self.assertEqual(self.results()["environment"].message, "Missing .env keys: TOKEN")

    def test_env_keys_present_even_if_empty(self):
        self.write(".env.example", "TOKEN=secret")
        self.write(".env", "TOKEN=")
        self.assertEqual(self.results()["environment"].status, "PASS")

    def test_invalid_utf8(self):
        for name in ("requirements.txt", ".env.example"):
            with self.subTest(name=name):
                (self.root / name).write_bytes(b"\xff")
                self.assertEqual(exit_code(check_project(self.root)), 2)
                (self.root / name).unlink()

    def test_unreadable_file(self):
        self.write(".env.example", "TOKEN=value")
        with patch("projectready.checks.env_keys", side_effect=PermissionError("secret")):
            results = check_project(self.root)
        self.assertEqual(exit_code(results), 2)
        self.assertNotIn("secret", repr(results))

    def test_exit_code_precedence(self):
        for statuses, expected in [([], 0), (["PASS", "SKIP"], 0), (["WARN"], 1), (["WARN", "FAIL"], 2)]:
            self.assertEqual(exit_code([Check("test", status, "") for status in statuses]), expected)

    def test_json_and_terminal(self):
        self.write("pyproject.toml", '[project]\ndependencies = []')
        for flags in (["--json"], ["--format", "json"], []):
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["check", str(self.root), *flags])
            self.assertEqual(code, 0)
            if flags:
                result = json.loads(output.getvalue())
                self.assertEqual(result["exit_code"], code)
                self.assertEqual(sum(result["summary"].values()), len(result["checks"]))
            else:
                self.assertIn("PASS", output.getvalue())

    def test_no_modification_or_external_execution(self):
        self.write("pyproject.toml", '[project]\ndependencies = []')
        self.write(".env.example", "TOKEN=secret")
        before = {item.name: (item.read_bytes(), item.stat().st_mtime_ns) for item in self.root.iterdir()}
        with patch("subprocess.Popen", side_effect=AssertionError("external execution")), patch("os.system", side_effect=AssertionError("external execution")):
            check_project(self.root)
        after = {item.name: (item.read_bytes(), item.stat().st_mtime_ns) for item in self.root.iterdir()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()

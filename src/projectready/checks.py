from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
import platform
import re
import tomllib

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    message: str


def exit_code(checks: list[Check]) -> int:
    if any(check.status == "FAIL" for check in checks):
        return 2
    return int(any(check.status == "WARN" for check in checks))


def report(checks: list[Check]) -> dict:
    return {"schema_version": 1, "checks": [asdict(check) for check in checks],
            "summary": {status: sum(check.status == status for check in checks)
                        for status in ("PASS", "WARN", "FAIL", "SKIP")},
            "exit_code": exit_code(checks)}


class UnsupportedEnvironmentSyntax(ValueError):
    pass


def env_keys(path: Path) -> set[str]:
    keys = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)", line)
        if not match:
            raise UnsupportedEnvironmentSyntax()
        value = match.group(2).lstrip()
        if value.startswith(("'", '"')):
            quote = value[0]
            escaped = False
            closing = None
            for index, character in enumerate(value[1:], 1):
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    closing = index
                    break
            if closing is None:
                raise UnsupportedEnvironmentSyntax()
            tail = value[closing + 1:]
            if tail.strip() and not (tail[0].isspace() and tail.lstrip().startswith("#")):
                raise UnsupportedEnvironmentSyntax()
        elif value.endswith("\\"):
            raise UnsupportedEnvironmentSyntax()
        keys.add(match.group(1))
    return keys


def validated_specifier(value: str) -> SpecifierSet:
    specification = SpecifierSet(value)
    for item in specification:
        Version(item.version.removesuffix(".*"))
    return specification


def check_project(path: Path) -> list[Check]:
    checks = []
    try:
        if not path.is_dir():
            return [Check("project", "FAIL", "Target is not an accessible directory.")]
        checks.append(Check("project", "PASS", "Project directory is accessible."))
        data = {}
        pyproject = path / "pyproject.toml"
        if pyproject.exists():
            try:
                with pyproject.open("rb") as stream:
                    data = tomllib.load(stream)
                checks.append(Check("pyproject", "PASS", "pyproject.toml is valid TOML."))
            except (OSError, ValueError):
                checks.append(Check("pyproject", "FAIL", "Cannot read or parse pyproject.toml."))
        else:
            checks.append(Check("pyproject", "SKIP", "pyproject.toml is absent."))
        project = data.get("project", {})
        if not isinstance(project, dict):
            checks.append(Check("metadata", "FAIL", "Project metadata must be a table."))
            project = {}
        dynamic = project.get("dynamic", [])
        if not isinstance(dynamic, list) or not all(isinstance(item, str) for item in dynamic):
            checks.append(Check("metadata", "FAIL", "Dynamic metadata must be an array of strings."))
            dynamic = []
        required = project.get("requires-python")
        if required is None:
            checks.append(Check("python", "WARN" if "requires-python" in dynamic else "SKIP",
                                "Python requirement is dynamic or not declared."))
        else:
            try:
                if not isinstance(required, str) or not required.strip():
                    raise InvalidSpecifier()
                current_python = Version(platform.python_version())
                specification = validated_specifier(required)
                compatible = specification.contains(current_python, prereleases=True)
                checks.append(Check("python", "PASS" if compatible else "FAIL",
                                    f"Python {current_python}; required {specification}: "
                                    + ("compatible." if compatible else "incompatible.")))
            except (InvalidSpecifier, InvalidVersion, TypeError):
                checks.append(Check("python", "FAIL", "Invalid requires-python declaration."))
        declarations = []
        defined = "dependencies" in project
        dependencies = project.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
            checks.append(Check("dependencies", "FAIL", "Dependencies must be an array of strings."))
        else:
            declarations.extend(dependencies)
        requirements = path / "requirements.txt"
        if requirements.exists():
            defined = True
            try:
                continuing = False
                for line in requirements.read_text(encoding="utf-8-sig").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    line = re.split(r"\s+#", line, maxsplit=1)[0].strip()
                    if continuing:
                        continuing = line.endswith("\\")
                        continue
                    continuing = line.endswith("\\")
                    declarations.append(line)
            except (OSError, UnicodeError):
                checks.append(Check("requirements", "FAIL", "Cannot read requirements.txt."))
        checks.append(Check("dependency_definitions", "PASS" if defined else "WARN",
                            "Dependency definitions detected." if defined else "No supported dependency definitions detected."))
        if "dependencies" in dynamic:
            checks.append(Check("dynamic_dependencies", "WARN", "Dynamic dependencies cannot be resolved without execution."))
        for index, declaration in enumerate(declarations, 1):
            name = f"dependency_{index}"
            try:
                dependency = Requirement(declaration)
            except InvalidRequirement:
                checks.append(Check(name, "WARN", "Unsupported or invalid dependency declaration; content withheld."))
                continue
            try:
                specification = validated_specifier(str(dependency.specifier))
            except (InvalidSpecifier, InvalidVersion):
                checks.append(Check(name, "WARN", f"{dependency.name}: unsupported version requirement; content withheld."))
                continue
            label = dependency.name + (str(specification) or " (any version)")
            if dependency.marker and not dependency.marker.evaluate():
                checks.append(Check(name, "SKIP", f"{label}: dependency marker does not apply to this environment."))
                continue
            if dependency.url or dependency.extras:
                checks.append(Check(name, "WARN", f"{label}: direct references and extras are not fully verified; URL withheld."))
                continue
            try:
                installed = metadata.version(dependency.name)
                installed_version = Version(installed)
                compatible = dependency.specifier.contains(installed_version, prereleases=True)
                checks.append(Check(name, "PASS" if compatible else "FAIL",
                                    f"{label}: installed {installed_version}; "
                                    + ("compatible." if compatible else "incompatible.")))
            except metadata.PackageNotFoundError:
                checks.append(Check(name, "FAIL", f"{label}: not installed in the current Python environment."))
            except (InvalidVersion, OSError, ValueError, TypeError):
                checks.append(Check(name, "WARN", f"{label}: installed metadata could not be verified."))
        example = path / ".env.example"
        if not example.exists():
            checks.append(Check("environment", "SKIP", ".env.example is absent."))
        else:
            try:
                expected = env_keys(example)
                actual = env_keys(path / ".env") if (path / ".env").exists() else set()
                missing = sorted(expected - actual)
                checks.append(Check("environment", "WARN" if missing else "PASS",
                                    "Missing .env keys: " + ", ".join(missing) if missing else
                                    "All example keys are present in .env."))
            except UnsupportedEnvironmentSyntax:
                checks.append(Check("environment", "WARN", "Unsupported environment syntax; key comparison could not be verified."))
            except (OSError, UnicodeError):
                checks.append(Check("environment", "FAIL", "Cannot read environment key files."))
    except (OSError, ValueError):
        checks.append(Check("filesystem", "FAIL", "Project files could not be inspected."))
    return checks

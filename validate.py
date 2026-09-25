"""Public assignment preflight (Python 3.9+).

Copy validate.py, tests/public_tests.cpp, and .github/workflows/validate.yml into
your assignment repository, preserving these paths. Keep your submission files.
Run: python validate.py (or python3 validate.py). Fix reported issues and rerun.
Requires a GNU-compatible C++17 compiler: g++ by default; CXX may name a different
compiler executable (not a command with flags). Students do not edit settings.
If local tooling is unavailable, push your work and open GitHub Actions >
Assignment Preflight > run > Validate. Linux Actions is the full-check reference.
Exit codes: 0 PASS, 1 FAIL, 2 INCOMPLETE. Both 1 and 2 require attention.
Checks read files beside this script, including unpushed edits. Temporary builds
are cleaned up. No network, AI, accounts, or Python packages are needed locally.
Passing all public checks does not guarantee full credit.
"""

# INSTRUCTOR-ONLY ASSIGNMENT SETTINGS: replace these and the public C++ harness
# when preparing another C++17 assignment. Students use the prepared package.
ASSIGNMENT = {
    "assignment_name": "CIS-277 Assignment 1: Network Packet Buffer Pool",
    "required_files": ["Stack.h", "MemoryPool.h", "MemoryPool.cpp", "main.cpp", "README.md"],
    "readme_title": "# CIS-277 Assignment 1: Network Packet Buffer Pool",
    "readme_headings": ["Student", "Description", "Stack Implementation", "How to Compile", "How to Run", "Analysis Questions"],
    "forbidden_tokens": ["std::stack"],
    "demo_sources": ["main.cpp", "MemoryPool.cpp"],
    "test_sources": ["MemoryPool.cpp"],
    "compiler_flags": ["-std=c++17", "-Wall", "-Wextra", "-pedantic"],
    "manual_review_notes": [
        "Instructor review: six substantive analysis answers, demonstration completeness, code readability, and custom Stack implementation/use.",
        "Source screening does not prove a custom Stack implementation or detect every alias/macro evasion.",
        "Memory checks cover exercised paths, not complete memory safety; binary isolation and ASan may miss overwrites between pool blocks sharing an underlying allocation.",
        "Complexity requires instructor review: allocation is specified O(1); rubric wording also mentions O(1) deallocation and needs clarification. No automatic Big-O verdict is made.",
        "Verify the published GitHub submission requirements manually; this command does not submit work.",
    ],
}

import argparse
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import List, Optional, Tuple


def cpp_tokens(source: str) -> List[Tuple[str, int]]:
    """Screen lexical tokens, excluding comments and ordinary/raw literals.

    Handle line splices before lexing, keeping original line numbers. This is a
    limited lexical screen, not a preprocessor or a full C++ parser.
    """
    characters = []
    lines = []
    line = 1
    position = 0
    while position < len(source):
        splice = re.match(r"\\\r?\n", source[position:position + 3])
        if splice:
            position += len(splice.group())
            line += 1
            continue
        character = source[position]
        characters.append(character)
        lines.append(line)
        line += character == "\n"
        position += 1
    text = "".join(characters)
    token_pattern = re.compile(
        r'(?P<space>\s+)|(?P<comment>//[^\n]*|/\*[\s\S]*?(?:\*/|$))'
        r'|(?P<raw>(?:u8|u|U|L)?R"([^ ()\\\t\r\n]{0,16})\([\s\S]*?\)\4")'
        r'''|(?P<literal>(?:u8|u|U|L)?(?:"(?:\\[\s\S]|[^"\\])*"|'(?:\\[\s\S]|[^'\\])*'))'''
        r"|(?P<token>[A-Za-z_][A-Za-z_0-9]*|[0-9](?:[A-Za-z_0-9.]|'(?=[A-Za-z_0-9]))*|::|[^\s])"
    )
    return [(match.group(), lines[match.start()]) for match in token_pattern.finditer(text) if match.lastgroup == "token"]


def settings_error() -> Optional[str]:
    required = {"assignment_name", "required_files", "readme_title", "readme_headings", "forbidden_tokens", "demo_sources", "test_sources", "compiler_flags", "manual_review_notes"}
    if not isinstance(ASSIGNMENT, dict) or set(ASSIGNMENT) != required:
        return "ASSIGNMENT must contain exactly the documented settings keys."
    for key in ("assignment_name", "readme_title"):
        if not isinstance(ASSIGNMENT[key], str) or not ASSIGNMENT[key].strip() or "\n" in ASSIGNMENT[key]:
            return key + " must be a nonempty single-line string."
    if not ASSIGNMENT["readme_title"].startswith("# "):
        return "readme_title must be a first-level Markdown heading starting with '# '."
    for key in required - {"assignment_name", "readme_title"}:
        value = ASSIGNMENT[key]
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() or "\n" in item or "\x00" in item for item in value):
            return key + " must be a list of nonempty single-line strings."
        if key in {"required_files", "demo_sources", "compiler_flags", "readme_headings"} and not value:
            return key + " must not be empty."
    for key in ("required_files", "demo_sources", "test_sources"):
        for name in ASSIGNMENT[key]:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or name.startswith("-") or name in ("", "."):
                return key + " must contain safe relative file paths."
            if key == "required_files" and len(path.parts) != 1:
                return "required_files must list root filenames."
            if key != "required_files" and name == "tests/public_tests.cpp":
                return "Source lists contain student files only; the runner appends the public harness."
    for entry in ASSIGNMENT["forbidden_tokens"]:
        if not cpp_tokens(entry):
            return "forbidden_tokens must contain literal C++ token sequences."
    return None


def report(results: List[str], status: str, label: str, detail: str = "") -> str:
    results.append(status)
    print(status + ": " + label + (": " + detail if detail else ""))
    return status


def read_text(path: Path, results: List[str], label: str) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        report(results, "INCOMPLETE", label, str(error))
        return None


def check_readme(root: Path, results: List[str]) -> None:
    path = root / "README.md"
    if not path.is_file():
        report(results, "FAIL", "README structure", "Missing README.md")
        return
    source = read_text(path, results, "README structure")
    if source is None:
        return
    headings = {}
    current = None
    fence = None
    title_found = False
    for line in source.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            elif current is not None and line.strip():
                headings[current] = True
            continue
        if marker:
            fence = marker[1]
            continue
        stripped = line.strip()
        title_found = title_found or stripped == ASSIGNMENT["readme_title"]
        heading = re.match(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading and len(heading[1]) <= 2:
            current = heading[2] if len(heading[1]) == 2 else None
            if current is not None:
                headings.setdefault(current, False)
        elif current is not None and stripped and not heading:
            headings[current] = True
    missing = []
    if not title_found:
        missing.append("expected title " + ASSIGNMENT["readme_title"])
    missing.extend("missing or empty ## " + name for name in ASSIGNMENT["readme_headings"] if not headings.get(name))
    report(results, "FAIL" if missing else "PASS", "README structure", "; ".join(missing))


def screen_sources(root: Path, results: List[str]) -> None:
    excluded = {".git", ".github", "build", "out", "dist", "__pycache__", ".venv", "venv"}
    extensions = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".ipp", ".tpp", ".inl"}
    restrictions = [(entry, [token for token, line in cpp_tokens(entry)]) for entry in ASSIGNMENT["forbidden_tokens"]]
    start = len(results)
    def walk_error(error: OSError) -> None:
        report(results, "INCOMPLETE", "Source screening", str(error))
    for directory, folders, files in os.walk(root, onerror=walk_error):
        folders[:] = [name for name in folders if name not in excluded and not name.startswith("cmake-build-")]
        for name in sorted(files):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.suffix.lower() not in extensions or relative == "tests/public_tests.cpp":
                continue
            if not path.resolve().is_relative_to(root):
                report(results, "INCOMPLETE", "Source screening", relative + " points outside the submission")
                continue
            source = read_text(path, results, "Source screening " + relative)
            if source is None:
                continue
            tokens = cpp_tokens(source)
            values = [token for token, line in tokens]
            for entry, forbidden in restrictions:
                for index in range(len(values) - len(forbidden) + 1):
                    if values[index:index + len(forbidden)] == forbidden:
                        report(results, "FAIL", "Source screening", relative + ":" + str(tokens[index][1]) + ": prohibited " + entry)
    if len(results) == start:
        report(results, "PASS", "Source screening")


def execute(command: List[str], root: Path, results: List[str], label: str,
            timeout: int, probe: bool = False, environment: Optional[dict] = None) -> str:
    try:
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                   errors="replace", timeout=timeout, env=environment)
    except subprocess.TimeoutExpired:
        return report(results, "INCOMPLETE" if probe else "FAIL", label,
                      "timeout after " + str(timeout) + "s; likely hang or input prompt" if timeout == 10 else "compilation timeout after " + str(timeout) + "s")
    except OSError as error:
        return report(results, "INCOMPLETE", label, str(error))
    if completed.returncode:
        status = report(results, "INCOMPLETE" if probe else "FAIL", label, "exit " + str(completed.returncode))
        for output in (completed.stdout, completed.stderr):
            if output:
                print(output.rstrip())
        return status
    return report(results, "PASS", label)


def build_and_run(root: Path, temporary: Path, results: List[str], compiler: str,
                  label: str, name: str, sources: List[str], sanitizer: bool = False) -> None:
    executable = temporary / (name + ("-asan" if sanitizer else "") + (".exe" if os.name == "nt" else ""))
    flags = list(ASSIGNMENT["compiler_flags"])
    environment = None
    if sanitizer:
        flags += ["-fsanitize=address", "-fno-omit-frame-pointer", "-g"]
        environment = asan_environment()
    command = [compiler] + flags + ["-I", str(root)] + [str(root / source) for source in sources] + ["-o", str(executable)]
    outcome = execute(command, root, results, label + " build", 60, environment=environment)
    if outcome != "PASS":
        print("UNRUN: " + label + " execution (build did not pass)")
        return
    execute([str(executable)], root, results, label + " execution", 10, environment=environment)


def asan_environment() -> dict:
    environment = os.environ.copy()
    # Do not inherit options that suppress failures, leak checks, or diagnostics.
    environment["ASAN_OPTIONS"] = "detect_leaks=" + ("1" if sys.platform.startswith("linux") else "0") + ":halt_on_error=1:exitcode=1"
    environment["LSAN_OPTIONS"] = "exitcode=1"
    return environment


def compiler_checks(root: Path, temporary: Path, results: List[str]) -> None:
    compiler = os.environ.get("CXX", "g++")
    harness = "tests/public_tests.cpp"
    harness_present = (root / harness).is_file()
    if not harness_present:
        report(results, "INCOMPLETE", "Public harness", "Missing " + harness + "; obtain a corrected package from the instructor")
    build_and_run(root, temporary, results, compiler, "Demo", "demo", ASSIGNMENT["demo_sources"])
    if harness_present:
        build_and_run(root, temporary, results, compiler, "Public tests", "public-tests", ASSIGNMENT["test_sources"] + [harness])
    else:
        print("UNRUN: Public tests build and execution (public harness missing)")
    probe_source = temporary / "asan_probe.cpp"
    probe_source.write_text("int main() { return 0; }\n", encoding="utf-8")
    probe_executable = temporary / ("asan-probe.exe" if os.name == "nt" else "asan-probe")
    command = [compiler, "-std=c++17", "-fsanitize=address", "-fno-omit-frame-pointer", str(probe_source), "-o", str(probe_executable)]
    supported = execute(command, root, results, "AddressSanitizer support build", 60, probe=True, environment=asan_environment()) == "PASS"
    if supported:
        supported = execute([str(probe_executable)], root, results, "AddressSanitizer support execution", 10, probe=True, environment=asan_environment()) == "PASS"
    else:
        print("UNRUN: AddressSanitizer support execution (probe build did not pass)")
    if not supported:
        print("UNRUN: AddressSanitizer demo and public tests (support probe did not pass)")
        return
    build_and_run(root, temporary, results, compiler, "AddressSanitizer demo", "demo", ASSIGNMENT["demo_sources"], True)
    if harness_present:
        build_and_run(root, temporary, results, compiler, "AddressSanitizer public tests", "public-tests", ASSIGNMENT["test_sources"] + [harness], True)
    else:
        print("UNRUN: AddressSanitizer public tests (public harness missing)")


def summarize(results: List[str]) -> int:
    print("\nPassing all public checks does not guarantee full credit.")
    if isinstance(ASSIGNMENT, dict) and isinstance(ASSIGNMENT.get("manual_review_notes"), list):
        for note in ASSIGNMENT["manual_review_notes"]:
            if isinstance(note, str):
                print(note)
    if "INCOMPLETE" in results:
        print("Some mandatory checks could not run. Use GitHub Actions > Assignment Preflight > run > Validate; package configuration issues require the instructor.")
    if "FAIL" in results:
        print("FAIL: Fix the reported issues and rerun python validate.py.")
        return 1
    if "INCOMPLETE" in results:
        print("INCOMPLETE: Resolve the prerequisite or configuration issue and rerun python validate.py.")
        return 2
    print("PASS: All public preflight checks passed.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)
    results = []
    error = settings_error()
    if error:
        report(results, "INCOMPLETE", "Instructor configuration", error + " Ask the instructor for a corrected package.")
        return summarize(results)
    root = Path(__file__).resolve().parent
    print("Assignment Preflight: " + ASSIGNMENT["assignment_name"])
    missing = [name for name in ASSIGNMENT["required_files"] if not (root / name).is_file()]
    report(results, "FAIL" if missing else "PASS", "Required files", "Missing " + ", ".join(missing) if missing else "")
    check_readme(root, results)
    screen_sources(root, results)
    try:
        with tempfile.TemporaryDirectory(prefix="assignment-preflight-") as directory:
            compiler_checks(root, Path(directory), results)
    except OSError as error:
        report(results, "INCOMPLETE", "Temporary build environment", str(error))
        print("UNRUN: Remaining compiler and runtime checks")
    return summarize(results)


if __name__ == "__main__":
    sys.exit(main())

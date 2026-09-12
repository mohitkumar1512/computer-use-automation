"""Project convention: no source file may exceed MAX_LINES, to keep everything readable."""

from pathlib import Path

MAX_LINES = 200
REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKED_DIRS = ["src", "mock_app", "tests"]
CHECKED_SUFFIXES = {".py", ".html", ".css", ".js", ".toml"}


def source_files() -> list[Path]:
    files = []
    for dirname in CHECKED_DIRS:
        directory = REPO_ROOT / dirname
        if directory.exists():
            files += [p for p in directory.rglob("*") if p.suffix in CHECKED_SUFFIXES]
    return files


def test_no_source_file_exceeds_max_lines():
    too_long = {}
    for path in source_files():
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_LINES:
            too_long[str(path.relative_to(REPO_ROOT))] = line_count
    assert not too_long, f"Files over {MAX_LINES} lines: {too_long}"


def test_package_is_importable():
    import cua

    assert cua.__version__

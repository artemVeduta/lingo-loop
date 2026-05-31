from __future__ import annotations

from pathlib import Path

from language_tutor.installer.providers.base import SKILL_FILES

REPO_ROOT = Path(__file__).resolve().parents[2]


def _frontmatter_keys(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", path
    end = lines.index("---", 1)
    keys: set[str] = set()
    for line in lines[1:end]:
        key, _sep, _value = line.partition(":")
        keys.add(key)
    return keys


def test_canonical_skill_tree_contains_exact_files() -> None:
    actual = sorted(
        str(path.relative_to(REPO_ROOT / "skills"))
        for path in (REPO_ROOT / "skills").rglob("*")
        if path.is_file()
    )
    assert actual == sorted(SKILL_FILES)


def test_judge_is_skill_not_agent() -> None:
    assert (REPO_ROOT / "skills" / "tutor-judge" / "SKILL.md").exists()
    assert not (REPO_ROOT / "agents" / "tutor-judge.md").exists()


def test_skill_frontmatter_is_plain_name_description_only() -> None:
    for rel in SKILL_FILES:
        if not rel.endswith("SKILL.md"):
            continue
        assert _frontmatter_keys(REPO_ROOT / "skills" / rel) == {"name", "description"}


def test_skill_markdown_uses_console_tutor_not_source_bin() -> None:
    offenders: list[str] = []
    for rel in SKILL_FILES:
        path = REPO_ROOT / "skills" / rel
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        if "bin" + "/tutor" in text:
            offenders.append(rel)
    assert offenders == []


def test_helper_scripts_resolve_tutor_bin_from_environment() -> None:
    scripts = [
        "tutor-vocab/scripts/run.py",
        "tutor-writing/scripts/run.py",
        "tutor-progress/scripts/run.py",
    ]
    for rel in scripts:
        text = (REPO_ROOT / "skills" / rel).read_text(encoding="utf-8")
        assert 'os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor")' in text
        assert "ROOT = Path(__file__)" not in text
        assert 'ROOT / "bin" / "tutor"' not in text

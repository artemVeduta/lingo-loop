"""Docs correctness gate (§6).

For every install doc (``docs/install/*.md``) and ``README.md``:

1. Every fenced shell block's ``tutor`` invocations must reference real
   subcommands and flags (asserted via ``tutor <leaf> --help``).
2. Every relative markdown link target must resolve to an existing file under
   the repo root.
3. Every documented ``config_root`` path must match the installer's
   ``config_root()`` value on macOS (compared via ``Path.expanduser()``).
4. The string ``language-tutor`` must not appear on a line unless that same
   line also references ``lingo-loop`` (contrast context).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

import pytest
from click.testing import CliRunner

from language_tutor.cli import main as cli_main
from language_tutor.installer.protocol import InstallerContext
from language_tutor.installer.providers.claude import ClaudeInstaller
from language_tutor.installer.providers.codex import CodexInstaller
from language_tutor.installer.providers.hermes import HermesInstaller
from language_tutor.installer.providers.openclaw import OpenClawInstaller
from language_tutor.installer.seams import FakeCommandRunner, FakeFilesystem

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INSTALL = REPO_ROOT / "docs" / "install"
README = REPO_ROOT / "README.md"

DOC_FILES: list[Path] = sorted(DOCS_INSTALL.glob("*.md")) + [README]

# --------------------------------------------------------------------------
# Shared parsing helpers
# --------------------------------------------------------------------------

FENCED_BLOCK_RE = re.compile(
    r"^```(?P<lang>bash|shell|sh)?\s*\n(?P<body>.*?)^```",
    re.MULTILINE | re.DOTALL,
)
TUTOR_LINE_RE = re.compile(r"^\s*(?:\$\s*)?tutor\b(?P<rest>.*)$")
FLAG_RE = re.compile(r"(--[A-Za-z][A-Za-z0-9-]*)")
LINK_RE = re.compile(r"(?<!\!)\[[^\]]+\]\(([^)]+)\)")


def _shell_blocks(text: str) -> Iterable[str]:
    for match in FENCED_BLOCK_RE.finditer(text):
        yield match.group("body")


def _tutor_invocations(block: str) -> Iterable[str]:
    # Strip line continuations + comments
    cleaned = re.sub(r"\\\n", " ", block)
    for line in cleaned.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = TUTOR_LINE_RE.match(stripped)
        if not m:
            continue
        # Drop everything after a pipe / redirection so we only see the tutor
        # invocation flags, not flags belonging to `jq` or other downstream
        # commands.
        rest = re.split(r"[|>;]", m.group("rest"))[0]
        yield rest.strip()


def _leaf_command(invocation: str) -> list[str] | None:
    """Return the leaf click command path for a `tutor ...` invocation.

    Walks token-by-token while each token is a click group/command name.
    Stops at the first token that begins with ``-`` (a flag) or that the
    runner cannot resolve further.
    """
    tokens = [t for t in invocation.split() if t]
    if not tokens:
        return None
    # First non-flag token must be a subcommand (group or command).
    cmd: list[str] = []
    for tok in tokens:
        if tok.startswith("-"):
            break
        # Strip any quoting / argument-looking tokens. We only treat tokens
        # that look like identifiers as command segments.
        if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", tok):
            break
        cmd.append(tok)
        # Heuristic: at most 2 levels of nesting in this CLI.
        if len(cmd) >= 2:
            break
    return cmd or None


def _documented_flags(invocation: str, leaf: list[str]) -> set[str]:
    # Strip the leaf-command prefix from the invocation, so flags belonging
    # to the subcommand args (after positional payload) still count but flag
    # tokens before the leaf (none in practice) do not.
    rest = invocation
    for tok in leaf:
        rest = rest.replace(tok, "", 1)
    return set(FLAG_RE.findall(rest))


# --------------------------------------------------------------------------
# 6.1 CLI examples reference real subcommands + flags
# --------------------------------------------------------------------------


@pytest.mark.parametrize("doc", DOC_FILES, ids=lambda p: p.name)
def test_tutor_examples_parse(doc: Path) -> None:
    runner = CliRunner()
    text = doc.read_text(encoding="utf-8")
    errors: list[str] = []

    for block in _shell_blocks(text):
        for invocation in _tutor_invocations(block):
            leaf = _leaf_command(invocation)
            if not leaf:
                errors.append(f"{doc.name}: cannot parse tutor leaf from `tutor {invocation}`")
                continue
            # Probe the leaf with --help. Click groups also accept --help.
            result = runner.invoke(cli_main, [*leaf, "--help"])
            if result.exit_code != 0:
                errors.append(
                    f"{doc.name}: `tutor {' '.join(leaf)} --help` exited "
                    f"{result.exit_code}: {result.output[:200]}"
                )
                continue
            help_text = result.output
            for flag in _documented_flags(invocation, leaf):
                if flag not in help_text:
                    errors.append(
                        f"{doc.name}: flag `{flag}` not in "
                        f"`tutor {' '.join(leaf)} --help` output"
                    )

    assert not errors, "\n".join(errors)


# --------------------------------------------------------------------------
# 6.2 Relative links resolve against the repo root
# --------------------------------------------------------------------------


SCHEME_RE = re.compile(r"^[a-z][a-z0-9+\-.]*:", re.IGNORECASE)


def _link_targets(text: str) -> Iterable[str]:
    for m in LINK_RE.finditer(text):
        yield m.group(1).strip()


@pytest.mark.parametrize("doc", DOC_FILES, ids=lambda p: p.name)
def test_relative_links_resolve(doc: Path) -> None:
    errors: list[str] = []
    text = doc.read_text(encoding="utf-8")
    for raw in _link_targets(text):
        target = raw.split()[0]  # drop "title" segments
        if target.startswith("#"):
            continue
        if SCHEME_RE.match(target):
            continue
        # Strip anchor from path-with-anchor links.
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        candidate = (doc.parent / path_part).resolve()
        if not candidate.exists():
            errors.append(f"{doc.name}: broken link `{target}` -> {candidate}")
    assert not errors, "\n".join(errors)


# --------------------------------------------------------------------------
# 6.3 Config-root paths match installer.config_root() on macOS
# --------------------------------------------------------------------------


def _installer_config_root(installer_cls: type) -> Path:
    home = Path.home()
    ctx = InstallerContext(
        fs=FakeFilesystem(home=home),
        runner=FakeCommandRunner(available={}),
        bundled_assets_root=REPO_ROOT,
    )
    return installer_cls(ctx).config_root()


HOST_TO_INSTALLER = {
    "claude": ClaudeInstaller,
    "codex": CodexInstaller,
    "hermes": HermesInstaller,
    "openclaw": OpenClawInstaller,
}


@pytest.mark.parametrize("host", sorted(HOST_TO_INSTALLER))
def test_documented_config_root_matches_installer(host: str) -> None:
    doc = DOCS_INSTALL / f"{host}.md"
    text = doc.read_text(encoding="utf-8")
    expected = _installer_config_root(HOST_TO_INSTALLER[host])
    expected_marker = f"~/.{host}/"
    # The doc MUST reference a ~/.{host}/... path (so users see the config root).
    assert expected_marker in text, (
        f"{doc.name}: expected to reference config root prefix `{expected_marker}`"
    )
    # And every such reference must expand to the installer's actual root.
    documented = re.findall(rf"~/\.{host}/[A-Za-z0-9_./-]*", text)
    for path_str in documented:
        # Trim trailing punctuation that markdown may leave attached.
        trimmed = path_str.rstrip(".,);:`")
        expanded = Path(trimmed).expanduser()
        # The documented path must live under the installer's config_root.
        assert str(expanded).startswith(str(expected)), (
            f"{doc.name}: documented `{trimmed}` -> `{expanded}` does not live "
            f"under installer config_root `{expected}`"
        )


# --------------------------------------------------------------------------
# 6.4 `language-tutor` only allowed when contrasted with `lingo-loop`
# --------------------------------------------------------------------------


@pytest.mark.parametrize("doc", DOC_FILES, ids=lambda p: p.name)
def test_language_tutor_only_in_contrast_with_lingo_loop(doc: Path) -> None:
    offenders: list[str] = []
    for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), start=1):
        if "language-tutor" not in line:
            continue
        if "lingo-loop" in line:
            continue
        offenders.append(f"{doc.name}:{lineno}: {line.strip()}")
    assert not offenders, "Found `language-tutor` without lingo-loop contrast:\n" + "\n".join(
        offenders
    )

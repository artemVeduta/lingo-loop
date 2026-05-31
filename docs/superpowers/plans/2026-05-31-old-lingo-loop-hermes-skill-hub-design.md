# Lingo Loop Hermes Skill Hub Install Design

Date: 2026-05-31
Status: Approved design (revised 2026-05-31 after live-container verification)

## Revision Summary

Verified against the running `hermes-language-tutor` container (image
`nousresearch/hermes-agent:v2026.5.29.2`). Findings overturned two earlier path
assumptions. The design now commits to **flat-home mode** and a
**`HERMES_HOME`-derived path resolver**. See "Runtime Verification" and the
revised "Upstream Design".

## Goal

Make the Hermes `language-tutor` agent load the real `lingo-loop` tutor skills from the packaged wheel, install the `tutor-judge` agent, and expose Telegram slash aliases for the tutor flows.

The fix spans two repositories:

- `/Users/artem.veduta/python/language-tutor`: upstream `lingo-loop` owns package assets, Hermes provider install, tests, and the next release.
- `/Users/artem.veduta/proj/homelab`: homelab consumes the fixed artifact, keeps runtime state mounted, runs provider repair at startup, and configures Telegram shortcuts.

## Context

The Hermes `language-tutor` container currently has the `tutor` CLI repair path in the homelab entrypoint, but the image Dockerfile does not install `lingo-loop`. The compose file already passes a `LINGO_LOOP_INSTALL_SPEC` build argument, so the Dockerfile and runtime behavior are out of sync.

The upstream `lingo-loop` package currently installs Hermes profile files only:

- `hermes-profile/distribution.yaml`
- `hermes-profile/config.yaml`
- `hermes-profile/SOUL.md`

It does not install the tutor flow skills into the Hermes skills hub. The profile manifest also contains a `skills: ../skills` pointer that works only as a source-tree idea and resolves to a dead path from a wheel/container install.

The packaged tutor skills still describe source-layout `bin/tutor` calls. That is correct for source plugin development but wrong for Hermes wheel containers, where the console script on `PATH` is the stable command. The OpenClaw plugin already uses the better convention: `LANGUAGE_TUTOR_TUTOR_BIN` with default `tutor`.

## Runtime Verification

Probed live on compute (`docker exec hermes-language-tutor ...`). Facts:

- `hermes` user: `HOME=/opt/data`, `HERMES_HOME=/opt/data`. Both set to the same
  value by `main-wrapper.sh` (`export HOME=/opt/data`) and image `ENV
  HERMES_HOME=/opt/data`.
- `/opt/data` IS the active Hermes home. It is a **flat home**, not a
  profile-switching setup. The gateway reads `/opt/data/SOUL.md` and
  `/opt/data/config.yaml` directly (the homelab-managed files).
- Skills hub is `/opt/data/skills` (Hermes default `$HERMES_HOME/skills`;
  `config.yaml` has `skills.external_dirs: []`).
- `hermes profile list` shows only `◆default`. No `lingo-loop` profile is
  registered or active.
- `hermes skills list` shows only `language-tutor-cli` (category `productivity`,
  state `disabled`). The six tutor flow skills and `tutor-judge` are absent.
- `/opt/data/skills/language-tutor/` exists but contains only `.gitkeep` — the
  empty homelab placeholder. This is the core bug.
- The 0.1.1/0.1.2 `HermesInstaller` wrote its three profile files to
  `/opt/data/home/.hermes/profiles/lingo-loop/`. That directory is **dead**:
  runtime `$HOME=/opt/data`, so Hermes would look under
  `/opt/data/.hermes/profiles/` (which does not exist), and profile mode is not
  in use anyway. Nothing reads those files.

### Root cause

`BaseProviderInstaller.config_root()` resolves `fs.home() / ".hermes"` and
ignores `HERMES_HOME`. At image build time `fs.home()` was `/opt/data/home`, so
managed files landed under a home the runtime never uses. The skills hub was
never a managed area at all, so flow skills were never materialized.

## Decisions

Use the upstream installer as the single source of truth for Hermes skill installation.

**Flat-home mode.** This deploy runs Hermes with `HERMES_HOME=/opt/data` as a
single flat home and does not use Hermes profile switching. The installer
targets the skills hub derived from `HERMES_HOME` and does **not** write a
profile distribution into a `profiles/<name>/` subtree. The packaged
`hermes-profile/` assets (SOUL.md, config.yaml, distribution.yaml) remain in the
wheel as reference/source-of-truth, but provider init for Hermes installs
**skills only**. SOUL.md and config.yaml at the home root stay homelab-owned
(repo-managed), since that is what the gateway actually loads.

Rejected: writing a profile distribution to `$HOME/.hermes/profiles/lingo-loop`.
Verified dead in the target deploy; profile mode is not active and the runtime
home differs from the install-time home.

Rejected options:

- Copy tutor skills from homelab at container startup. This duplicates skill ownership, adds shell drift, and violates the package as source of truth.
- Use `hermes skills install` with local paths. The target Hermes version accepts registry IDs or HTTP(S) URLs, not local paths, so this is fragile for container boot.
- Keep one synthesized bridge skill. The required surface is six separate flow skills plus the judge agent.

The six flow skills will use the Hermes category `language-tutor`. The judge agent will use Hermes category `autonomous-ai-agents`.

## Upstream Design

`HermesInstaller` will own **one** managed area: the Hermes skills hub under
`<hermes-data-root>/skills`.

Path resolution is explicit and `HERMES_HOME`-first. The Hermes data root is
`HERMES_HOME` when set (expanded), otherwise `~/.hermes` (the user's normal
Hermes home). The skills hub is always `<hermes-data-root>/skills`. This is the
fix for the root cause: the resolver must read `HERMES_HOME`, never `fs.home()`
alone.

Resolved targets:

- Container (homelab): `HERMES_HOME=/opt/data` → skills hub `/opt/data/skills`.
- macOS / normal CLI: `HERMES_HOME` unset → skills hub `~/.hermes/skills`.

The installer keeps this as a narrow Hermes-specific path resolver. It does not
hardcode `/opt/data` in shared installer code.

No profile distribution is written. SOUL.md and config.yaml at the Hermes home
root remain homelab/repo-managed (that is what the gateway loads). The packaged
`hermes-profile/` files stay in the wheel as source-of-truth and for
`tutor doctor` payload checks, but `tutor init --provider hermes` does not copy
them into a `profiles/<name>/` directory.

Managed skills hub files:

- `skills/language-tutor/tutor-setup/SKILL.md`
- `skills/language-tutor/tutor-vocab/SKILL.md`
- `skills/language-tutor/tutor-vocab/scripts/run.py`
- `skills/language-tutor/tutor-writing/SKILL.md`
- `skills/language-tutor/tutor-writing/scripts/run.py`
- `skills/language-tutor/tutor-progress/SKILL.md`
- `skills/language-tutor/tutor-progress/scripts/run.py`
- `skills/language-tutor/tutor-reading/SKILL.md`
- `skills/language-tutor/tutor-lesson/SKILL.md`
- `skills/autonomous-ai-agents/tutor-judge/SKILL.md`

The installer copies from package assets into these paths, detects drift per file, and repairs only missing or content-divergent files. It does not touch learner state, secrets, memories, sessions, the home-root SOUL.md/config.yaml, or unrelated Hermes skills. It must overwrite the empty `skills/language-tutor/.gitkeep` placeholder with the real flow skills.

The packaged `hermes-profile/distribution.yaml` keeps its descriptive metadata but no longer contains the dead `skills: ../skills` pointer. It is reference-only; nothing in flat mode installs it.

## Portable Install

The same instruction installs on any host where the `tutor` console script and
Hermes share a `HERMES_HOME` — container or laptop:

```bash
pip install lingo-loop        # or pipx / uv tool install
tutor init --provider hermes --yes
```

`hermes profile install github.com/...` is **not** required and not used. That
command is Hermes-native whole-agent profile distribution (profile mode); this
design ships skills only and lets the host keep its own SOUL/config. The only
per-host difference is the resolved skills hub: `/opt/data/skills` in the
container vs `~/.hermes/skills` on a laptop, both derived from `HERMES_HOME`.

## Skill Command Contract

The Hermes-installed flow skills must use the installed `tutor` command, not source-relative `bin/tutor`.

Skill markdown should describe `tutor ... --json` commands. Helper scripts should resolve:

```python
os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor")
```

This mirrors the OpenClaw plugin convention and supports custom container paths without coupling skills to the source checkout layout.

## Homelab Design

`compute/services/hermes/tutor.Dockerfile` will install the pinned `lingo-loop` artifact into `/opt/hermes/.venv`, link `tutor` onto `PATH`, and run build-time `tutor doctor --json` against a throwaway `LANGUAGE_TUTOR_HOME`.

The default package target is the next fixed release:

```dockerfile
ARG LINGO_LOOP_INSTALL_SPEC=lingo-loop==0.1.3
```

The Git fallback points to the first tag that includes this Hermes skill-hub fix:

```bash
LINGO_LOOP_INSTALL_SPEC='lingo-loop @ git+https://github.com/artemVeduta/lingo-loop@v0.1.3'
```

`compute/services/hermes/docker-compose.yml` keeps:

- `LINGO_LOOP_INSTALL_SPEC: ${LINGO_LOOP_INSTALL_SPEC:-lingo-loop==0.1.3}`
- `LANGUAGE_TUTOR_HOME: /home/hermes/.tutor`
- `/srv/media/config/hermes/language-tutor:/opt/data`
- `/srv/media/config/hermes/language-tutor-state:/home/hermes/.tutor`

`compute/services/hermes/entrypoint.sh` keeps repo-managed config, SOUL, Hindsight config, memories, and `.env` handling. For `AGENT_ID=language-tutor`, it must not copy empty repo skill placeholders over package-managed tutor skills. The empty `compute/services/hermes/config/language-tutor/skills` tree is removed and stays removed.

Startup repair for `language-tutor` runs:

```bash
tutor doctor --json
tutor init --provider hermes --yes
```

If the target Hermes version installs skills disabled, the entrypoint adds the smallest verified enable step after `tutor init`. If skills are enabled by default, no enable step is added.

## Telegram Slash Commands

`compute/services/hermes/config/language-tutor/config.yaml` will add Hermes `quick_commands` only after the exact schema is verified against `nousresearch/hermes-agent:v2026.5.29.2`.

Required aliases:

- `/tutor-setup`
- `/tutor-vocab`
- `/tutor-writing`
- `/tutor-reading`
- `/tutor-lesson`
- `/tutor-progress`

Each alias maps to a natural-language prompt that triggers the corresponding installed skill. The config also uses the Hermes command allowlist shape required by the verified schema so Telegram does not reject these commands as unknown.

No guessed quick-command schema will be deployed.

## Error Handling

Missing package assets fail with exact relative file paths and repair hints.

Missing Hermes CLI or config root blocks provider install with the existing installer status model.

Missing `tutor` binary fails the `hermes-language-tutor` container at startup.

`tutor doctor --json` validates package assets, migrations, writable state, and config schemas without creating a learner session.

Secrets remain outside package assets and provider init flows.

## Testing

Upstream `lingo-loop` tests:

- `HermesInstaller` declares all Hermes skills hub files (six flow skills + `tutor-judge`) and no `profiles/<name>/` files.
- Skills hub root resolves from `HERMES_HOME` when set, else `~/.hermes/skills`. A test sets `HERMES_HOME` and asserts the resolved hub path; another unsets it and asserts the `~/.hermes` fallback. The resolver never uses `fs.home()` when `HERMES_HOME` is present.
- `tutor init --provider hermes --yes` writes six flow skills and `tutor-judge` into the resolved skills hub, and writes no profile distribution.
- Second init is idempotent.
- Single-file drift repairs only the divergent file.
- Missing packaged assets are reported by exact relative path.
- Hermes skill markdown and helper scripts use `tutor` / `LANGUAGE_TUTOR_TUTOR_BIN`, not source-relative `bin/tutor`.
- Full test suite passes before release.

Homelab tests:

- Compose renders with `LINGO_LOOP_INSTALL_SPEC=lingo-loop==0.1.3` and `LANGUAGE_TUTOR_HOME=/home/hermes/.tutor`.
- Dockerfile contains the actual `lingo-loop` install block and build-time doctor.
- Entrypoint does not copy empty `language-tutor/skills` placeholders over package-managed skills.
- README documents package pin, fallback, state roots, and smoke commands.

Compute verification:

- `docker exec hermes-language-tutor tutor doctor --json` returns `status: ok`.
- `docker exec hermes-language-tutor hermes skills list` shows `tutor-setup`, `tutor-vocab`, `tutor-writing`, `tutor-reading`, `tutor-lesson`, `tutor-progress`, and `tutor-judge`.
- Listed tutor skills are enabled.
- A setup request invokes the `tutor-setup` skill instead of raw terminal fallback.
- Telegram `/tutor-setup` is recognized and reaches the tutor agent.

## Post-Deploy Checklist

Run this after the updated `hermes-language-tutor` service is rebuilt and restarted on compute.

1. Confirm the container is running and recent logs have no startup repair failure:

   ```bash
   ssh compute "docker ps --filter name=hermes-language-tutor"
   ssh compute "docker logs hermes-language-tutor --tail 150"
   ```

2. Confirm the package and state contract inside the container:

   ```bash
   ssh compute "docker exec hermes-language-tutor sh -lc 'which tutor && tutor --help >/dev/null && env | grep \"^LANGUAGE_TUTOR_HOME=\"'"
   ssh compute "docker exec hermes-language-tutor tutor doctor --json"
   ```

3. Confirm Hermes skill-hub files exist in the expected categories:

   ```bash
   ssh compute "docker exec hermes-language-tutor sh -lc 'find /opt/data/skills/language-tutor /opt/data/skills/autonomous-ai-agents -maxdepth 3 -type f | sort'"
   ```

4. Confirm Hermes sees the tutor flow skills and judge agent as enabled:

   ```bash
   ssh compute "docker exec hermes-language-tutor hermes skills list"
   ```

   Expected entries include `tutor-setup`, `tutor-vocab`, `tutor-writing`, `tutor-reading`, `tutor-lesson`, `tutor-progress`, and `tutor-judge`.

5. Confirm runtime config contains the verified Telegram slash-command mapping:

   ```bash
   ssh compute "docker exec hermes-language-tutor sh -lc 'grep -n \"quick_commands\\|command_allowlist\\|tutor-setup\" /opt/data/config.yaml'"
   ```

6. Smoke the agent behavior from Telegram:

   - Send `/tutor-setup`.
   - Confirm Hermes does not respond with "Unknown command".
   - Confirm the response follows the `tutor-setup` skill flow rather than issuing raw fallback CLI instructions.

7. Smoke one non-setup flow:

   - Send `/tutor-progress`.
   - Confirm the response uses the installed `tutor-progress` skill and reads persisted tutor state from `/home/hermes/.tutor`.

8. Record deployment evidence:

   - Save the lingo-loop version or git tag used by the image.
   - Save the `tutor doctor --json` status.
   - Save the `hermes skills list` output summary.
   - Update the existing Hermes tutor memory to say skill bodies now come from the `lingo-loop` package, not homelab placeholders.

## Rollout

1. Update and test `/Users/artem.veduta/python/language-tutor`.
2. Release/tag `lingo-loop==0.1.3`.
3. Update `/Users/artem.veduta/proj/homelab` to consume `0.1.3`.
4. Rebuild and restart only `hermes-language-tutor` on compute.
5. Run compute smoke checks.
6. Complete the post-deploy checklist.

## Non-Goals

- No homelab copy of tutor skill bodies.
- No Hermes profile-mode distribution install; flat-home skills-only install only.
- No installer ownership of home-root SOUL.md/config.yaml; those stay homelab-managed.
- No data migration between Hermes and OpenClaw tutor state.
- No public internet exposure changes.
- No speculative new tutor flows beyond the six existing flow skills.
- No changes to the unrelated `hermes-assistant` agent behavior.

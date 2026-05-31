# Lingo Loop Hermes Skill Hub Install Design

Date: 2026-05-31
Status: Approved design

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

## Decisions

Use the upstream installer as the single source of truth for Hermes skill installation.

Rejected options:

- Copy tutor skills from homelab at container startup. This duplicates skill ownership, adds shell drift, and violates the package as source of truth.
- Use `hermes skills install` with local paths. The target Hermes version accepts registry IDs or HTTP(S) URLs, not local paths, so this is fragile for container boot.
- Keep one synthesized bridge skill. The required surface is six separate flow skills plus the judge agent.

The six flow skills will use the Hermes category `language-tutor`. The judge agent will use Hermes category `autonomous-ai-agents`.

## Upstream Design

`HermesInstaller` will own two managed areas:

- Hermes profile files under the existing Hermes profile install directory.
- Hermes skills hub files under `$HERMES_HOME/skills`.

Path resolution is explicit. The Hermes data root is `HERMES_HOME` when set, otherwise the user's normal Hermes data location. The skills hub is always `<hermes-data-root>/skills`; tutor skills are never written under the profile directory. In the homelab target container, this resolves to `/opt/data/skills`.

The Hermes profile root remains separate from the skills hub. In the homelab target container, the profile install path is `/opt/data/home/.hermes/profiles/lingo-loop`. On normal CLI installs, it remains the user's Hermes profile path. Implementation should keep this as a narrow Hermes-specific path resolver instead of hardcoding `/opt/data` in shared installer code.

Managed profile files:

- `profiles/lingo-loop/distribution.yaml`
- `profiles/lingo-loop/config.yaml`
- `profiles/lingo-loop/SOUL.md`

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

The installer copies from package assets into these paths, detects drift per file, and repairs only missing or content-divergent files. It does not touch learner state, secrets, memories, sessions, or unrelated Hermes skills.

The Hermes profile manifest will no longer contain the dead `skills: ../skills` pointer. It will declare the packaged profile accurately and leave actual skill materialization to `tutor init --provider hermes --yes`.

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

- `HermesInstaller` declares profile files and all Hermes skills hub files.
- `tutor init --provider hermes --yes` writes profile files, six flow skills, and `tutor-judge`.
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
- No data migration between Hermes and OpenClaw tutor state.
- No public internet exposure changes.
- No speculative new tutor flows beyond the six existing flow skills.
- No changes to the unrelated `hermes-assistant` agent behavior.

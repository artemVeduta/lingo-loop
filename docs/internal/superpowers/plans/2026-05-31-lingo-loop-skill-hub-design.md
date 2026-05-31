# Lingo Loop Skill Hub Install Design (Hermes + OpenClaw)

Date: 2026-05-31
Status: Approved design

This spec unifies and supersedes:

- `2026-05-31-lingo-loop-hermes-skill-hub-design.md`
- `2026-05-31-lingo-loop-openclaw-skill-hub-design.md`

Both are deleted; this is the single source of truth for the tutor skill-hub work.

## Goal

Make both tutor agents surface the real `lingo-loop` tutor skills as `SKILL.md`
entries in their skill hubs, driven by the installed `tutor` CLI:

- Hermes `language-tutor` loads the six tutor flow skills plus the `tutor-judge`
  agent and exposes Telegram slash aliases for the flows.
- OpenClaw `language-tutor` surfaces the same six flow skills plus `tutor-judge`
  as skill-list entries, invokable as session commands. The existing
  `language-tutor` plugin (contract `language_tutor`, three tools) stays in place
  and keeps providing tool/CLI access.

A single upstream release ships both provider installers and the shared skill
bodies. The fix spans two repositories:

- `/Users/artem.veduta/python/language-tutor`: upstream `lingo-loop` owns the
  Hermes installer, the OpenClaw installer, the canonical skill assets, tests,
  and the next release.
- `/Users/artem.veduta/proj/homelab`: homelab consumes the fixed artifact, keeps
  runtime state mounted, runs provider repair at startup, and (Hermes only)
  configures Telegram shortcuts.

## Release Strategy

One release ships everything: shared canonical skill bodies, `HermesInstaller`,
and `OpenClawInstaller`.

```
lingo-loop==0.1.3
```

Both homelab services pin the same version. The Git fallback is:

```
lingo-loop @ git+https://github.com/artemVeduta/lingo-loop@v0.1.3
```

The release blockers below all gate this single tag.

## Context

### Shared

`tutor init --provider <hermes|openclaw>` today installs only the provider
profile (Hermes) or the plugin (OpenClaw) and never materializes tutor skills.
Neither skill hub contains tutor skills. The canonical instructional body for each
flow lives in the package once and is rendered with provider-appropriate
frontmatter and layout into each hub.

The packaged tutor skills still describe source-layout `bin/tutor` calls. That is
correct for source plugin development but wrong for wheel/container installs,
where the console script on `PATH` is the stable command. The OpenClaw plugin
already uses the better convention: `LANGUAGE_TUTOR_TUTOR_BIN` with default
`tutor`.

### Hermes facts

- The Hermes `language-tutor` container has the `tutor` CLI repair path in the
  homelab entrypoint, but the image Dockerfile did not install `lingo-loop`. The
  compose file already passes a `LINGO_LOOP_INSTALL_SPEC` build argument, so the
  Dockerfile and runtime behavior were out of sync.
- Upstream `lingo-loop` installs Hermes profile files only:
  `hermes-profile/distribution.yaml`, `hermes-profile/config.yaml`,
  `hermes-profile/SOUL.md`. The profile manifest contains a `skills: ../skills`
  pointer that works only as a source-tree idea and resolves to a dead path from a
  wheel/container install.

### OpenClaw facts

Confirmed live on compute (`docker exec openclaw ...`, 2026-05-31):

- `lingo-loop` is installed as one OpenClaw **plugin**: id `language-tutor`,
  version `0.1.0`, enabled, `onStartup`, plugin dir
  `/home/node/.openclaw/plugins/lingo-loop`. Contract `language_tutor` exposes
  three tools: `language_tutor.boot_context`, `language_tutor.text_exercise`
  (required), `language_tutor.run_cli` (optional).
- The OpenClaw skills hub `/home/node/.openclaw/skills/` contains 44 `gws-*`
  skills only; no tutor skills. Each gws skill is a single `SKILL.md` (markdown
  over the `gws` CLI bin) with frontmatter
  `metadata.openclaw.{category,requires.bins,cliHelp}`.
- OpenClaw **auto-discovers** every skill under `~/.openclaw/skills/`. The runtime
  `openclaw.json5` has no `skillsRef`/grouping block; dropping skill dirs into the
  hub is sufficient for discovery. `openclaw skills list`, `openclaw skills check`,
  and `openclaw skills info` enumerate them.

## Decisions

Use the upstream installer as the single source of truth for skill installation
in both providers.

- **One canonical body per flow.** The package owns one instructional body per
  flow; each installer renders provider-appropriate frontmatter and layout around
  it. The instructional text is a single source of truth; layout is
  provider-specific.
- **Skill mechanism: direct `tutor` CLI.** Each `SKILL.md` is thin markdown over
  the `tutor` CLI bin (`tutor <flow> --json`), exactly how the 44 `gws-*` skills
  front the `gws` bin. This lets one body serve both hubs.
- **Scope: upstream installers + homelab pin bump.** `lingo-loop` installs the
  skills; homelab bumps both pins to `0.1.3` and relies on the existing runtime
  `tutor init --provider <p>` step.
- **Judge included.** Install a seventh `tutor-judge` skill alongside the six flow
  skills in both hubs.
- **Hermes categories:** the six flow skills use Hermes category `language-tutor`;
  the judge uses category `autonomous-ai-agents`.

Rejected options:

- Copy/seed tutor skills from homelab at container startup. Duplicates skill
  ownership, adds shell drift, violates package as source of truth.
- Use `hermes skills install` with local paths. The target Hermes version accepts
  registry IDs or HTTP(S) URLs, not local paths; fragile for container boot.
- Keep one synthesized bridge skill. The required surface is six separate flow
  skills plus the judge.
- Plugin-tool skill bodies (`language_tutor.text_exercise`) for OpenClaw.
  Plugin-pure but diverges from the gws convention on the box and forces
  OpenClaw-specific bodies that cannot be shared with Hermes.

## Upstream Design

### Canonical skill bodies

The package owns one instructional body per flow. Both installers consume the
same bodies and render provider-appropriate frontmatter.

Body conventions (both providers):

- Describe `tutor <flow> --json` commands, not source-relative `bin/tutor`.
- Note that the agent calls boot context on the first tutor message.
- State that learner state is read from `LANGUAGE_TUTOR_HOME`.
- Resolve the binary via `os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor")` in
  any helper scripts, matching the OpenClaw plugin convention.

### HermesInstaller

`HermesInstaller` owns two managed areas:

- Hermes profile files under the existing Hermes profile install directory.
- Hermes skills hub files under `$HERMES_HOME/skills`.

Path resolution is explicit. The Hermes data root is `HERMES_HOME` when set,
otherwise the user's normal Hermes data location. The skills hub is always
`<hermes-data-root>/skills`; tutor skills are never written under the profile
directory. In the homelab container this resolves to `/opt/data/skills`. The
profile root remains separate; in the container it is
`/opt/data/home/.hermes/profiles/lingo-loop`. Keep this as a narrow
Hermes-specific path resolver instead of hardcoding `/opt/data` in shared
installer code.

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

The Hermes profile manifest no longer contains the dead `skills: ../skills`
pointer. It declares the packaged profile accurately and leaves skill
materialization to `tutor init --provider hermes --yes`.

### OpenClawInstaller

`OpenClawInstaller` gains a managed area alongside the existing plugin files:

- OpenClaw plugin files (existing, unchanged ownership).
- OpenClaw skills hub files under `<openclaw-home>/skills`.

Path resolution is explicit and OpenClaw-specific. The OpenClaw home is derived
from the provider's existing path resolver (the same root that yields
`/home/node/.openclaw/plugins/lingo-loop` in the container). The skills hub is
always `<openclaw-home>/skills`. Skill dirs are flat, one per skill, matching the
gws layout. Keep this as a narrow OpenClaw-specific resolver, not a hardcoded
`/home/node` path in shared installer code.

Managed skills hub files:

- `skills/tutor-setup/SKILL.md`
- `skills/tutor-vocab/SKILL.md`
- `skills/tutor-writing/SKILL.md`
- `skills/tutor-reading/SKILL.md`
- `skills/tutor-lesson/SKILL.md`
- `skills/tutor-progress/SKILL.md`
- `skills/tutor-judge/SKILL.md`

Optional: `skills/tutor-shared/SKILL.md` for shared auth/state/`--json`
conventions, mirroring `gws-shared`. The six flow skills and judge reference it
via `../tutor-shared/SKILL.md` when present.

OpenClaw frontmatter shape (per the verified gws format):

```yaml
---
name: tutor-vocab
description: "Language tutor: vocabulary practice from persisted learner state."
metadata:
  version: 0.1.3
  openclaw:
    category: "language-tutor"
    requires:
      bins:
        - tutor
    cliHelp: "tutor vocab --help"
---
```

### Installer behavior (both)

Each installer copies from package assets into its managed paths, detects drift
per file, and repairs only missing or content-divergent files. It does not touch
learner state, secrets, memories, sessions, the OpenClaw plugin registry, or
unrelated skills (`gws-*` or other Hermes skills).

## Homelab Design

### Hermes

`compute/services/hermes/tutor.Dockerfile` installs the pinned `lingo-loop`
artifact into `/opt/hermes/.venv`, links `tutor` onto `PATH`, and runs build-time
`tutor doctor --json` against a throwaway `LANGUAGE_TUTOR_HOME`.

```dockerfile
ARG LINGO_LOOP_INSTALL_SPEC=lingo-loop==0.1.3
```

`compute/services/hermes/docker-compose.yml` keeps:

- `LINGO_LOOP_INSTALL_SPEC: ${LINGO_LOOP_INSTALL_SPEC:-lingo-loop==0.1.3}`
- `LANGUAGE_TUTOR_HOME: /home/hermes/.tutor`
- `/srv/media/config/hermes/language-tutor:/opt/data`
- `/srv/media/config/hermes/language-tutor-state:/home/hermes/.tutor`

`compute/services/hermes/entrypoint.sh` keeps repo-managed config, SOUL, Hindsight
config, memories, and `.env` handling. For `AGENT_ID=language-tutor`, it must not
copy empty repo skill placeholders over package-managed tutor skills. The empty
`compute/services/hermes/config/language-tutor/skills` tree is removed and stays
removed.

Startup repair for `language-tutor` runs:

```bash
tutor doctor --json
tutor init --provider hermes --yes
```

If the target Hermes version installs skills disabled, the entrypoint adds the
smallest verified enable step after `tutor init`. If skills are enabled by
default, no enable step is added.

#### Telegram slash commands

`compute/services/hermes/config/language-tutor/config.yaml` adds Hermes
`quick_commands` only after the exact schema is verified against
`nousresearch/hermes-agent:v2026.5.29.2`.

Required aliases:

- `/tutor-setup`
- `/tutor-vocab`
- `/tutor-writing`
- `/tutor-reading`
- `/tutor-lesson`
- `/tutor-progress`

Each alias maps to a natural-language prompt that triggers the corresponding
installed skill. The config also uses the Hermes command allowlist shape required
by the verified schema so Telegram does not reject these commands as unknown. No
guessed quick-command schema is deployed.

### OpenClaw

`compute/services/openclaw/Dockerfile` keeps installing the pinned `lingo-loop`
artifact into `/opt/lingo-loop-venv`, linking `tutor` onto `PATH`, and running
build-time `tutor doctor --json` against a throwaway `LANGUAGE_TUTOR_HOME`.

```dockerfile
ARG LINGO_LOOP_INSTALL_SPEC=lingo-loop==0.1.3
```

`compute/services/openclaw/docker-compose.yml` keeps:

- `LINGO_LOOP_INSTALL_SPEC: ${LINGO_LOOP_INSTALL_SPEC:-lingo-loop==0.1.3}`
- `LANGUAGE_TUTOR_HOME: /home/node/.tutor`
- `/srv/media/config/openclaw:/home/node/.openclaw`
- `/srv/media/config/language-tutor:/home/node/.tutor`

**Runtime install is mandatory.** The compose bind-mount
`/srv/media/config/openclaw:/home/node/.openclaw` shadows any build-time writes to
that path. Skills must be written at runtime, after the volume is mounted, by the
entrypoint's `tutor init --provider openclaw` step — the same reason the plugin is
installed at runtime, not build time.

`compute/services/openclaw/entrypoint.sh` already runs, in
`repair_language_tutor_plugin`, after the persistent volume is mounted:

```bash
tutor doctor --json
tutor init --provider openclaw --yes --json
openclaw plugins install /home/node/.openclaw/plugins/lingo-loop --force
openclaw plugins enable language-tutor
```

Once upstream `0.1.3` installs skills during `tutor init --provider openclaw`, the
seven tutor `SKILL.md` files land in the persisted
`/srv/media/config/openclaw/skills` directory alongside the `gws-*` skills. No new
homelab install logic is required. If the verified OpenClaw release does not
auto-enable discovered skills, the entrypoint adds the smallest verified enable
step after `tutor init`; if discovery is sufficient, no step is added. The
`--json` form is used because the human-readable branch crashes on a cosmetic bug
after `run_init` succeeds.

## Release Blockers

All gate the single `0.1.3` tag:

1. **OpenClaw command-invocation UX.** Confirm OpenClaw exposes auto-discovered
   `SKILL.md` skills as **invokable session commands**, not only model-auto-invoked
   context. The 44 `gws-*` skills prove discovery; verify the command-invocation UX
   on `ghcr.io/openclaw/openclaw:2026.5.20` (via `openclaw skills info` and an
   in-session/Telegram invocation). If commands require an explicit registration
   shape, capture it and add it to the skill frontmatter or runtime config, with
   verified evidence, before homelab consumes `0.1.3`.
2. **Hermes quick-command schema.** Verify the exact `quick_commands` /
   command-allowlist schema against `nousresearch/hermes-agent:v2026.5.29.2` before
   adding aliases. No guessed schema is deployed.
3. **Skills-enabled-by-default.** For each provider, determine whether `tutor init`
   installs skills enabled or disabled, and add the smallest verified enable step
   only if needed.

## Error Handling

Shared:

- Missing package assets fail with exact relative file paths and repair hints.
- `tutor doctor --json` validates package assets, migrations, writable state, and
  config schemas without creating a learner session.
- Missing `tutor` binary fails the container at startup.
- Secrets remain outside package assets and provider init flows.

Hermes:

- Missing Hermes CLI or config root blocks provider install with the existing
  installer status model.

OpenClaw:

- `tutor init --provider openclaw` failure exits the container (`set -e`).
- Skills present on disk but not invocable as session commands are caught by the
  compute smoke checks (`openclaw skills list` / `skills check`).

## Testing

### Upstream `lingo-loop` tests

Shared:

- The same canonical bodies feed both installers; markdown and helper scripts use
  `tutor` / `LANGUAGE_TUTOR_TUTOR_BIN`, not source-relative `bin/tutor`.
- Single-file drift repairs only the divergent file (both installers).
- Missing packaged assets are reported by exact relative path (both installers).
- Full test suite passes before release.

Hermes:

- `HermesInstaller` declares profile files and all Hermes skills hub files.
- `tutor init --provider hermes --yes` writes profile files, six flow skills, and
  `tutor-judge`.
- Second init is idempotent.

OpenClaw:

- `OpenClawInstaller` declares the plugin files and all seven OpenClaw skills hub
  files.
- `tutor init --provider openclaw --yes` writes the plugin, six flow skills, and
  `tutor-judge` into `<openclaw-home>/skills`.
- Second init is idempotent.
- The installer does not delete or modify `gws-*` skills or the plugin registry.

### Homelab tests

Hermes:

- Compose renders with `LINGO_LOOP_INSTALL_SPEC=lingo-loop==0.1.3` and
  `LANGUAGE_TUTOR_HOME=/home/hermes/.tutor`.
- Dockerfile contains the `lingo-loop` install block and build-time doctor.
- Entrypoint does not copy empty `language-tutor/skills` placeholders over
  package-managed skills.
- README documents package pin, fallback, state roots, and smoke commands.

OpenClaw:

- Compose renders with `LINGO_LOOP_INSTALL_SPEC=lingo-loop==0.1.3` and
  `LANGUAGE_TUTOR_HOME=/home/node/.tutor`.
- Dockerfile contains the `lingo-loop` install block and build-time doctor.
- README documents package pin, fallback, state roots, and smoke commands.

### Compute verification

Hermes:

- `docker exec hermes-language-tutor tutor doctor --json` returns `status: ok`.
- `docker exec hermes-language-tutor hermes skills list` shows `tutor-setup`,
  `tutor-vocab`, `tutor-writing`, `tutor-reading`, `tutor-lesson`,
  `tutor-progress`, and `tutor-judge`, all enabled.
- A setup request invokes the `tutor-setup` skill instead of raw terminal
  fallback.
- Telegram `/tutor-setup` is recognized and reaches the tutor agent.

OpenClaw:

- `docker exec openclaw tutor doctor --json` returns `status: ok`.
- `docker exec openclaw openclaw skills list` shows the same seven tutor skills.
- `docker exec openclaw openclaw skills check` reports the tutor skills ready.
- The `gws-*` skills are still present and unaffected; the `language-tutor` plugin
  is still enabled.
- A session/Telegram `/tutor-vocab` (or natural-language vocab request) invokes the
  `tutor-vocab` skill and reads persisted state from `/home/node/.tutor`.

## Post-Deploy Checklist — Hermes

Run after the updated `hermes-language-tutor` service is rebuilt and restarted on
compute.

1. Confirm the container is running and recent logs have no startup repair
   failure:

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

   Expected: `tutor-setup`, `tutor-vocab`, `tutor-writing`, `tutor-reading`,
   `tutor-lesson`, `tutor-progress`, and `tutor-judge`.

5. Confirm runtime config contains the verified Telegram slash-command mapping:

   ```bash
   ssh compute "docker exec hermes-language-tutor sh -lc 'grep -n \"quick_commands\\|command_allowlist\\|tutor-setup\" /opt/data/config.yaml'"
   ```

6. Smoke the agent behavior from Telegram:

   - Send `/tutor-setup`. Confirm Hermes does not respond with "Unknown command"
     and follows the `tutor-setup` skill flow rather than raw fallback CLI
     instructions.

7. Smoke one non-setup flow:

   - Send `/tutor-progress`. Confirm the response uses the installed
     `tutor-progress` skill and reads persisted state from `/home/hermes/.tutor`.

8. Record deployment evidence:

   - Save the lingo-loop version or git tag used by the image.
   - Save the `tutor doctor --json` status.
   - Save the `hermes skills list` output summary.
   - Update the existing Hermes tutor memory to say skill bodies now come from the
     `lingo-loop` package, not homelab placeholders.

## Post-Deploy Checklist — OpenClaw

Run after the updated `openclaw` service is rebuilt and restarted on compute.

1. Confirm the container is running and recent logs have no startup repair
   failure:

   ```bash
   ssh compute "docker ps --filter name=openclaw"
   ssh compute "docker logs openclaw --tail 150"
   ```

2. Confirm the package and state contract inside the container:

   ```bash
   ssh compute "docker exec openclaw sh -lc 'which tutor && tutor --help >/dev/null && env | grep \"^LANGUAGE_TUTOR_HOME=\"'"
   ssh compute "docker exec openclaw tutor doctor --json"
   ```

3. Confirm the seven tutor skill files exist in the skills hub:

   ```bash
   ssh compute "docker exec openclaw sh -lc 'find /home/node/.openclaw/skills -maxdepth 2 -name SKILL.md | grep tutor- | sort'"
   ```

4. Confirm OpenClaw discovers the tutor skills:

   ```bash
   ssh compute "docker exec openclaw openclaw skills list"
   ssh compute "docker exec openclaw openclaw skills check"
   ```

   Expected: `tutor-setup`, `tutor-vocab`, `tutor-writing`, `tutor-reading`,
   `tutor-lesson`, `tutor-progress`, and `tutor-judge`.

5. Confirm `gws-*` skills and the plugin are unaffected:

   ```bash
   ssh compute "docker exec openclaw sh -lc 'ls /home/node/.openclaw/skills | grep -c \"^gws-\"'"
   ssh compute "docker exec openclaw node dist/index.js plugins list 2>&1 | grep -i language-tutor"
   ```

6. Smoke the agent behavior from a session or Telegram:

   - Trigger a vocab request (or `/tutor-vocab` if commands are supported). Confirm
     the response follows the `tutor-vocab` skill flow and reads state from
     `/home/node/.tutor`, rather than raw fallback instructions.

7. Record deployment evidence:

   - Save the `lingo-loop` version or git tag used by the image.
   - Save the `tutor doctor --json` status.
   - Save the `openclaw skills list` output summary.
   - Update the existing OpenClaw/tutor memory to note that OpenClaw now installs
     seven tutor skills from the `lingo-loop` package.

## Rollout

1. Update and test `/Users/artem.veduta/python/language-tutor`: shared canonical
   bodies, `HermesInstaller`, `OpenClawInstaller`, and tests.
2. Clear the release blockers (OpenClaw command-invocation UX on `2026.5.20`,
   Hermes quick-command schema on `hermes-agent:v2026.5.29.2`,
   skills-enabled-by-default per provider).
3. Release/tag `lingo-loop==0.1.3`.
4. Update `/Users/artem.veduta/proj/homelab` to consume `0.1.3` in both services.
5. Rebuild and restart `hermes-language-tutor` and `openclaw` on compute. The
   services are independent; deploy in any order and run each post-deploy checklist
   separately.
6. Complete both post-deploy checklists.

## Non-Goals

- No homelab copy of tutor skill bodies.
- No data migration of tutor learner state between Hermes and OpenClaw.
- No removal or behavior change of the OpenClaw `language-tutor` plugin.
- No public internet exposure changes.
- No speculative new tutor flows beyond the six existing flow skills plus judge.
- No changes to the unrelated `hermes-assistant` or OpenClaw `assistant` agent
  behavior, or to `gws-*` skills.

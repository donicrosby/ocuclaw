# SPEC: Port OcuClaw 2.1.2 → Hermes 0.22.x

**Author:** planner  
**Date:** 2026-11-08  
**Status:** SPEC (no implementation)  
**Branch:** `hermes-0.22-compat`  
**Fork:** `donicrosby/ocuclaw` (of `ocuclaw/ocuclaw`, public)

---

## 1. Summary

This specification defines every change required to make the OcuClaw Hermes
plugin (bundle v2.1.2) load and register on Hermes engine 0.22.x. The plugin
is certified today for `>=0.21.1,<0.22.0` (baseline 0.21.5); the host runs
**Hermes 0.22.5** and the plugin's version gate deliberately refuses startup.

The port is a **compatibility test**, not a recertification. The fork version
will be `2.1.2+hermes022` — an honest local suffix per plugin.yaml norms that
never presents as an official OcuClaw release.

---

## 2. Requirements Table

Each requirement carries an ID, a statement, a confidence label
(VERIFIED/ASSUMED), and the source that supports the label. ASSUMED items
must be validated by the coder against the live 0.22.5 runtime before
committing.

| ID   | Requirement | Confidence | Source |
|------|-------------|------------|--------|
| R1   | The supported Hermes version range SHALL be widened from `>=0.21.1,<0.22.0` to `>=0.21.1,<0.23.0` so the plugin admits Hermes 0.22.x without dropping the 0.21.x floor. | VERIFIED | Task body: host runs 0.22.5, gate must open for 0.22.x; code: `adapter.py:780` `SUPPORTED_HERMES_MAX_EXCLUSIVE` |
| R2   | Every in-code enforcement point for the version gate SHALL move in lockstep — the constants in `adapter.py` and `health.py`, the derived checks in `health_management.py`, and the `HERMES_RELEASE_DATES` table in `health.py`. | VERIFIED | Code audit: `adapter.py` lines 779-780, 2735-2758, 2973, 3062, 4458, 4464; `health.py` lines 44-45, 354; `health_management.py` lines 211-216 |
| R3   | The certified-hermes constants (`CERTIFIED_HERMES_VERSION`, `CERTIFIED_HERMES_TAG`, `CERTIFIED_HERMES_COMMIT`) SHALL be updated to reflect the port baseline: version `0.22.5`, tag `v0.22.5`, and the exact commit hash of the installed 0.22.5 runtime. | VERIFIED | Code: `adapter.py` lines 776-778, `health.py` lines 41-43; task body states the port target |
| R4   | Every bundled skill document that asserts the old range `>=0.21.1,<0.22.0` SHALL be updated to `>=0.21.1,<0.23.0`. | VERIFIED | Grep audit: 12 occurrences across 7 files under `skills/ocuclaw-assist-hermes/` and `README.md` |
| R5   | The plugin version in `plugin.yaml` SHALL become `2.1.2+hermes022`, an honest local suffix that never presents as an official OcuClaw release. | VERIFIED | Task body: "honest-versioning requirement" |
| R6   | The plugin's hook registration surface SHALL remain unchanged — the same seven required hooks (`on_session_end`, `post_approval_response`, `pre_tool_call`, `post_tool_call`, `post_api_request`, `pre_llm_call`, `api_request_error`) and the same optional hooks (`on_interim_message`, `on_stream_*`, `pre_transcription`) — because the Hermes plugin API contract is additive across the 0.21→0.22 boundary and no hook OcuClaw uses was removed or changed. | VERIFIED | Hermes plugin compatibility contract docs: "Documented `PluginContext` methods are not removed or renamed"; hook catalog at https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks confirms all seven required hooks and all optional hooks exist in 0.22.x |
| R7   | The `ctx.register_platform()` call SHALL pass unchanged because its kwargs are additive — new kwargs in 0.22.x are keyword-only with defaults, and the existing kwargs OcuClaw passes (`name`, `label`, `adapter_factory`, `check_fn`, `validate_config`, `setup_fn`, `is_connected`, `allowed_users_env`, `allow_all_env`, `allow_update_command`, `platform_hint`, `env_enablement_fn`) remain valid. | VERIFIED | Hermes docs: "Evolve additively"; `hermes_cli/plugins.py` `register_platform` source shows additive kwarg surface |
| R8   | The `ctx.register_skill()` calls for the two bundled skills (`ocuclaw-assist-hermes`, `glasses-ui`) SHALL pass unchanged — the skill registration API is identical across 0.21→0.22. | VERIFIED | Hermes plugin docs: `register_skill` API unchanged; plugin skill namespace (`plugin:skill`) unchanged |
| R9   | The `ctx.register_system_prompt_section()` calls SHALL pass unchanged — the registered prompt section API is identical across 0.21→0.22. | VERIFIED | Hermes docs: no API change for `register_system_prompt_section` |
| R10  | The `ctx.register_tool()` call for the setup tool SHALL pass unchanged. | VERIFIED | Hermes docs: tool registration API unchanged |
| R11  | The `ctx.register_cli_command()` calls SHALL pass unchanged — the CLI command registration surface is identical across 0.21→0.22. | VERIFIED | Hermes docs: CLI registration API unchanged |
| R12  | The `ctx.register_auxiliary_task()` call for silent-input prediction SHALL pass unchanged. | VERIFIED | Hermes docs: auxiliary task API unchanged |
| R13  | The `register_hook` call signature SHALL be verified against the 0.22.5 runtime — the 0.22.x line added a `hold_stream` keyword-only parameter that defaults to `False` and is backward-compatible, but the coder SHALL confirm that the existing positional calls (`register_hook(name, callback)`) still work without passing `hold_stream`. | ASSUMED | `hermes_cli/plugins.py` source shows `def register_hook(self, hook_name: str, callback: Callable, *, hold_stream: bool = False)` — the `*` separator makes `hold_stream` keyword-only, so positional calls should be unaffected; needs live 0.22.5 confirmation |
| R14  | The `on_session_end` hook payload SHALL be verified for the `platform` field name — the 0.22.x docs show `on_session_end` receives `platform` as a kwarg, matching what OcuClaw expects; the coder SHALL confirm the exact field set broadcast by 0.22.5 at turn end. | ASSUMED | Hermes hook docs show `on_session_end` payload includes `session_id`, `completed`, `interrupted`, `model`, `platform`, `reason`, `profile`; OcuClaw's callback accepts `**kwargs` — this is a defensive verification, not a predicted break |
| R15  | The `post_approval_response` hook payload SHALL be verified for the `choice` field values — the 0.22.x line may emit new `choice` values (`smart_approve`, `smart_deny`) from the smart-approval feature introduced in 0.22.x; OcuClaw's handler already handles unknown choices gracefully, but the coder SHALL confirm. | ASSUMED | Hermes docs show smart-approval `choice` values added in 0.22.x; OcuClaw's `_on_post_approval_response_hook` filters on known choices — defensive verification |
| R16  | The `session_read_state_supported()` probe in `adapter.py` SHALL be re-verified against the 0.22.5 SessionDB schema — the probe reads the sessions schema and checks for required columns; the 0.22.x SessionDB schema may have added columns (e.g., new compaction fields) without removing the ones OcuClaw probes. | ASSUMED | OcuClaw's `session_rpc.py` `session_read_state_supported()` probes for specific schema columns; Hermes session schema evolved in 0.22.x (new compaction columns, session IDs changed to hex format per bug report #142993) — probe must be verified |
| R17  | The `config.yaml` config-key surface (`display.platforms.ocuclaw.*`, `gateway.multiplex_*`, `plugins.stream_reasoning_deltas`) SHALL be verified — no breaking config-key rename or removal is documented for 0.22.x, but `plugins.stream_reasoning_deltas` must remain readable by `hermes config get`. | ASSUMED | Hermes changelog: no config-key renames documented for 0.22.x; `plugins.stream_reasoning_deltas` appears in 0.22.x docs as the gating config for streaming hooks |
| R18  | The `management RPC` surface (`hermes ocuclaw *` subcommands, `hermes plugins *`, `hermes config *`) SHALL be verified — the CLI subcommand dispatch mechanism is unchanged in 0.22.x. | ASSUMED | Hermes docs: CLI extension API unchanged; `register_cli_command` unchanged |
| R19  | The Node runtime bridge (`control_link.py`, `native_compat.py`, `provenance.py`) SHALL pass unchanged — these modules bridge over NDJSON-stdio and do not touch the Hermes plugin API surface. | VERIFIED | Code: these modules import from the plugin's own code and spawn a child process; no Hermes API surface dependency |
| R20  | The gateway state reader (`receipts.py`) SHALL be verified for the 0.22.x `gateway_state.json` format — the task body notes `gatewayPlatformState` was absent from the live agent-turn view, but this may be a status-reporting difference, not a format change. | ASSUMED | Task body: "`gatewayPlatformState` absent from agent-turn view"; `receipts.py` reads `gateway_state.json` — format must be verified against 0.22.5 |
| R21  | The `HERMES_RELEASE_DATES` table in `health.py` SHALL add the 0.22.5 release date entry. | VERIFIED | Code: `health.py` lines 368-374 — the version-identification fallback relies on release dates; without a 0.22.5 entry, the version parser falls through to "unknown" |

---

## 3. Engine Delta Audit: Hermes 0.21 → 0.22

### 3.1 Methodology

The delta was audited by:
1. Reading the 0.22.0 release notes and the 0.22.0→0.23.0 rollup
   (which documents the full 0.22.1–0.22.7 patch window).
2. Reading the published Hermes plugin API documentation
   (hooks reference, plugin registration surface).
3. Reading the `hermes_cli/plugins.py` source for `register_platform`
   and `register_hook` signatures.
4. Comparing the hook catalog in the 0.22.x docs against the hook
   vocabulary OcuClaw's `_valid_hook_names()` probe reads from
   `hermes_cli.plugins.VALID_HOOKS`.

### 3.2 Plugin API: No Breaking Changes

Hermes's published plugin compatibility contract (from the "Build a Hermes
Plugin" docs) states:

> Evolve additively. Documented `PluginContext` methods are not removed or
> renamed. New parameters are optional, have defaults, and should be
> keyword-only. Hook payloads are keyword payloads — new hook data is added
> as keyword fields, never by changing the meaning or position of an
> existing field.

Every surface OcuClaw touches follows this contract:

| Surface | 0.21.5 API | 0.22.5 API | Breaking? |
|---------|-----------|-----------|-----------|
| `ctx.register_platform(**kwargs)` | Accepts kwargs; unknown keys raise TypeError | Accepts same kwargs; new kwargs have defaults | No |
| `ctx.register_hook(name, callback)` | Positional hook_name + callback | Same + keyword-only `hold_stream=False` | No (positional calls unaffected) |
| `ctx.register_skill(name, path, description)` | 3-positional API | Same | No |
| `ctx.register_tool(...)` | Keyword API | Same | No |
| `ctx.register_system_prompt_section(...)` | Keyword API | Same | No |
| `ctx.register_cli_command(...)` | Keyword API | Same | No |
| `ctx.register_auxiliary_task(...)` | Keyword API | Same | No |
| `hermes_cli.plugins.VALID_HOOKS` | frozenset of hook names | frozenset of hook names (superset of 0.21.5) | No (additive) |
| Hook callbacks (e.g. `on_session_end`) | Receive kwargs by name | Receive same kwargs + new additive fields | No (OcuClaw uses `**kwargs`) |

### 3.3 New in 0.22.x (Not Used by OcuClaw)

These features arrived in the 0.22.x window but OcuClaw does not depend on them:

| Addition | Description | OcuClaw Impact |
|----------|-------------|----------------|
| `register_hook(hold_stream=True)` | Block streaming until a rewrite hook finishes | Not used — OcuClaw's `on_stream_*` hooks are observers only |
| `post_compaction` hook | Fires after every committed compaction | Not registered by OcuClaw |
| `on_session_delete` hook | Fires on session deletion | Not registered by OcuClaw |
| `pre_llm_call` block capability | Hook can return `{"action": "block"}` to cancel a turn | Not used — OcuClaw's `pre_llm_call` handler is observer-only |
| `pre_transcription` hook receiver | New hook dispatch seam | OcuClaw already probes for this hook independently |
| Smart approval (`smart_approve`/`smart_deny`) | `post_approval_response` emits new `choice` values | OcuClaw's handler filters on known choices — unknown values are ignored |
| `ctx.post_message()`, `ctx.side_question()` | Plugin message posting | Not used by OcuClaw |
| Plugin LLM access (`ctx.llm.complete(...)`) | Host-owned LLM call | Not used by OcuClaw |
| Kanban hooks (`kanban_task_claimed` etc.) | Board lifecycle hooks | Not registered by OcuClaw |

### 3.4 Removed / Renamed in 0.22.x

| Change | OcuClaw Impact |
|--------|----------------|
| Tool renames (`todo`→`todo_list`, `cronjob`→`cronjob_manage`, `process`→`process_manage`) | Old names still work (#97979); OcuClaw does not call these tools directly |
| Old plugin compatibility import layer removed | OcuClaw imports from `hermes_cli.plugins` (the current layer), not the old one |
| `hermes sync` removed (#132465) | Not used by OcuClaw |
| Built-in browser tools removed in favor of `browser_exec` | OcuClaw does not use browser tools |
| Session ID format changed from `YYYYMMDD_HHMMSS_xxxxxx` to `local-<64 hex>` (reported as bug #142993) | **Potentially affects** `session_rpc.py` which reads session IDs — see R16 |

### 3.5 Live Host Findings (2026-11-08T02:39Z)

The orchestrator recon reported these live status receipt findings on the
0.22.5 host:

| Finding | Severity | Relevance |
|---------|----------|-----------|
| `hermes_unsupported` | Error | **The gate this port removes** |
| `relay_token_missing` | Error | Pre-existing: no Relay Credential was ever generated on this host; setup must run |
| `streaming_not_configured` | Warning | `plugins.stream_reasoning_deltas` not set; the on_stream_* hooks will not register (by design) |
| `continue_here_not_configured` | Warning | Pre-existing; not a port concern |
| `gatewaySupervision: service` | Info | s6 supervision is active; relay child process can be spawned |
| `gatewayPlatformState` absent | Info | May indicate a 0.22.x reporting format change; see R20 |

---

## 4. File-by-File Change List

### 4.1 Version Gate Constants

#### `adapter.py`

| Line(s) | Current | Replacement |
|---------|---------|-------------|
| 776 | `CERTIFIED_HERMES_VERSION = "0.21.5"` | `CERTIFIED_HERMES_VERSION = "0.22.5"` |
| 777 | `CERTIFIED_HERMES_TAG = "v2026.9.24"` | `CERTIFIED_HERMES_TAG = "v0.22.5"` |
| 778 | `CERTIFIED_HERMES_COMMIT = "f97608f178d1ffeca59860195ab7da295f7c8e5f"` | `CERTIFIED_HERMES_COMMIT = "<coder: insert exact 0.22.5 commit hash from live host>"` |
| 780 | `SUPPORTED_HERMES_MAX_EXCLUSIVE = (0, 22, 0)` | `SUPPORTED_HERMES_MAX_EXCLUSIVE = (0, 23, 0)` |

> **Coder note:** The `CERTIFIED_HERMES_COMMIT` value must be read from the
> live 0.22.5 host: `hermes --version` or `pip show hermes-agent`. The
> exact commit hash is not known in this docker sandbox (the Hermes binary
> is present but its venv is broken).

The following enforcement points use these constants and require no further
code changes — their logic is range-driven:

| Line | Function | Behavior after gate change |
|------|----------|---------------------------|
| 2710 | `hermes_version_supported()` | `SUPPORTED_HERMES_MIN <= (0,22,5) < (0,23,0)` → True |
| 2735 | `_host_version_supported()` | Returns True on 0.22.5 |
| 2757 | `check_ocuclaw_requirements()` | Gate passes |
| 2973 | `validate_ocuclaw_config()` | Gate passes |
| 3062 | `setup_ocuclaw_platform()` | Gate passes — setup proceeds |
| 4458 | `_admitted_adapter_factory()` | Returns adapter instead of None |
| 4464 | `_admitted_is_connected()` | Checks host version AND connected state |

#### `health.py`

| Line(s) | Current | Replacement |
|---------|---------|-------------|
| 41 | `CERTIFIED_HERMES_VERSION = "0.21.5"` | `CERTIFIED_HERMES_VERSION = "0.22.5"` |
| 42 | `CERTIFIED_HERMES_TAG = "v2026.9.24"` | `CERTIFIED_HERMES_TAG = "v0.22.5"` |
| 43 | `CERTIFIED_HERMES_COMMIT = "f97608f178d1ffeca59860195ab7da295f7c8e5f"` | `CERTIFIED_HERMES_COMMIT = "<coder: insert exact 0.22.5 commit hash>"` |
| 45 | `SUPPORTED_HERMES_MAX_EXCLUSIVE = (0, 22, 0)` | `SUPPORTED_HERMES_MAX_EXCLUSIVE = (0, 23, 0)` |
| 368-374 | `HERMES_RELEASE_DATES = {...}` | Add `"2026.10.13": "0.22.0"` entry (or exact 0.22.5 release date) |

> **Coder note:** The release date for 0.22.5 must be verified on the live
> host. The 0.22.0 release date is 2026-10-13 from the GitHub release. The
> `HERMES_RELEASE_DATES` table is a fallback for installs with no version
> stamp; the 0.22.x entries should cover the full supported range.

The following enforcement point uses these constants:

| Line | Function | Behavior after gate change |
|------|----------|---------------------------|
| 354 | `hermes_version_supported()` | `(0,21,1) <= (0,22,5) < (0,23,0)` → True |

#### `health_management.py`

No direct constant change needed — imports from `health.py`:

| Line(s) | Reference | Impact |
|---------|-----------|--------|
| 211 | `from .health import SUPPORTED_HERMES_MAX_EXCLUSIVE, SUPPORTED_HERMES_MIN, hermes_version, parse_version` | Imports updated constants automatically |
| 215 | `SUPPORTED_HERMES_MIN <= parsed < SUPPORTED_HERMES_MAX_EXCLUSIVE` | Logic unchanged; range widened by constants |

### 4.2 Bundled Skill Documents

Every file under `skills/ocuclaw-assist-hermes/` that asserts the old range
`>=0.21.1,<0.22.0` must be updated to `>=0.21.1,<0.23.0`. Additionally, the
certified baseline reference should become `0.22.5`.

#### `skills/ocuclaw-assist-hermes/SKILL.md`

| Line | Change |
|------|--------|
| 548 | `- [ ] Hermes version is within \`>=0.21.1,<0.22.0\`` → `\`>=0.21.1,<0.23.0\`` |
| 670 | `- Supported Hermes is exactly \`>=0.21.1,<0.22.0\` (Hermes 0.21.1 and later 0.21.x);` → `\`>=0.21.1,<0.23.0\` (Hermes 0.21.1 and later 0.21.x, plus the 0.22.x port);` |
| 671 | `the certified baseline is \`0.21.5\`.` → `the certified baseline is \`0.22.5\`.` |

#### `skills/ocuclaw-assist-hermes/references/troubleshooting.md`

| Line | Change |
|------|--------|
| 13 | `\`>=0.21.1,<0.22.0\`` → `\`>=0.21.1,<0.23.0\`` |

#### `skills/ocuclaw-assist-hermes/references/install-lifecycle.md`

| Line(s) | Change |
|---------|--------|
| 9 | `(certified baseline \`0.21.5\`, supported \`>=0.21.1,<0.22.0\`)` → `(certified baseline \`0.22.5\`, supported \`>=0.21.1,<0.23.0\`)` |
| 23 | `\`>=0.21.1,<0.22.0\`` → `\`>=0.21.1,<0.23.0\`` |

#### `skills/ocuclaw-assist-hermes/references/fresh-install.md`

| Line | Change |
|------|--------|
| 68 | `\`>=0.21.1,<0.22.0\`` → `\`>=0.21.1,<0.23.0\`` |
| 113 | `\`>=0.21.1,<0.22.0\`` → `\`>=0.21.1,<0.23.0\`` |

#### `skills/ocuclaw-assist-hermes/references/quick-reference.md`

| Line | Change |
|------|--------|
| 16 | `\`>=0.21.1,<0.22.0\` (certified baseline \`0.21.5\`)` → `\`>=0.21.1,<0.23.0\` (certified baseline \`0.22.5\`)` |

#### `skills/ocuclaw-assist-hermes/references/update.md`

| Line | Change |
|------|--------|
| 25 | `\`>=0.21.1,<0.22.0\`` → `\`>=0.21.1,<0.23.0\`` |
| 188 | `\`>=0.21.1,<0.22.0\`` → `\`>=0.21.1,<0.23.0\`` |

#### `skills/ocuclaw-assist-hermes/references/agent-mode.md`

| Line | Change |
|------|--------|
| 39 | `0.21.1 to 0.21.3` reference — this is a factual range describing historical agent-mode availability, not a gate assertion. NO CHANGE — the port does not alter history. |

### 4.3 README.md

| Line | Change |
|------|--------|
| 25 | `\`>=0.21.1,<0.22.0\` (Hermes 0.21.1 and later 0.21.x)` → `\`>=0.21.1,<0.23.0\` (Hermes 0.21.1+ and the 0.22.x compatibility port)` |

### 4.4 Plugin Version

#### `plugin.yaml`

| Line | Change |
|------|--------|
| 4 | `version: 2.1.2` → `version: 2.1.2+hermes022` |

### 4.5 Summary of Files Touched

| File | Changes |
|------|---------|
| `adapter.py` | 4 constant lines |
| `health.py` | 4 constant lines + 1 table entry |
| `plugin.yaml` | 1 version line |
| `README.md` | 1 version line |
| `skills/ocuclaw-assist-hermes/SKILL.md` | 3 version lines |
| `skills/ocuclaw-assist-hermes/references/troubleshooting.md` | 1 version line |
| `skills/ocuclaw-assist-hermes/references/install-lifecycle.md` | 2 version lines |
| `skills/ocuclaw-assist-hermes/references/fresh-install.md` | 2 version lines |
| `skills/ocuclaw-assist-hermes/references/quick-reference.md` | 1 version line |
| `skills/ocuclaw-assist-hermes/references/update.md` | 2 version lines |

**Total: 10 files, ~21 line-level changes.** No code logic changes — this is a
pure gate-widening port.

---

## 5. Out of Scope

The port changes compatibility, not security behavior. The following surfaces
are explicitly NOT changed:

- **Relay security posture:** The relay still listens on `127.0.0.1:47801`
  with the same credential token comparison.
- **`wsBind`:** No change to the WebSocket binding default or configuration.
- **Credential lifecycle:** Relay Credential bootstrap, rotation, and the
  all-device reset flow are unchanged.
- **Pairing flow:** The phone-device pairing protocol, the TUI/Desktop
  pairing presenters, and the pairing-completion receipt are unchanged.
- **Node runtime bridge:** `control_link.py`, `native_compat.py`,
  `provenance.py`, and the `dist-cjs/` bundle are unchanged.
- **Even-AI routing:** The Even-AI endpoint classification and routing modes
  are unchanged.
- **Silent input prediction:** The prediction model routing is unchanged.

---

## 6. Test Plan

### 6.1 Unit Tests (Pre-Deployment)

These tests validate the gate logic without requiring a live Hermes runtime.

| UT-1 | **Version range arithmetic** |
|------|---------------------------|
| Goal | Prove `hermes_version_supported()` returns correct results for the new range |
| Method | Import `health.py` in a standalone Python process; call `hermes_version_supported()` with boundary and representative versions |
| Cases | `"0.21.0"` → False (below min), `"0.21.1"` → True (min inclusive), `"0.21.5"` → True (old baseline), `"0.22.0"` → True (newly admitted), `"0.22.5"` → True (port target), `"0.22.7"` → True (latest patch), `"0.23.0"` → False (max exclusive), `"0.23.0.dev0"` → False (dev cycle), `"0.22.5+12.gabc1234"` → True (git describe), `"0.0.0"` → False (placeholder), `""` → False (empty), `None` → False (unparseable) |
| File | New test file: `tests/test_hermes_version_gate.py` |

| UT-2 | **Same gate for adapter.py constants** |
|------|--------------------------------------|
| Goal | Confirm `adapter.py`'s `hermes_version_supported()` mirrors `health.py`'s |
| Method | Import both modules; call both functions with the same input set |
| Assertion | Both functions return identical results for every test case |
| Note | The functions share the same `SUPPORTED_HERMES_MIN`/`MAX_EXCLUSIVE` constants — this test detects drift between the two copies |

| UT-3 | **CERTIFIED constants match the new range** |
|------|------------------------------------------|
| Goal | Validate that `CERTIFIED_HERMES_VERSION` parses to a triple within the new range |
| Method | `parse_version(CERTIFIED_HERMES_VERSION)`, assert within `SUPPORTED_HERMES_MIN <= parsed < SUPPORTED_HERMES_MAX_EXCLUSIVE` |
| Files | Both `adapter.py` and `health.py` |

### 6.2 Live Smoke Test (On Hermes 0.22.5 Host)

These tests MUST run on the actual 0.22.5 host where the relay will operate.

> **Prerequisites:** Hermes 0.22.5 running, plugin installed from the
> `hermes-0.22-compat` branch, Tailscale connected, relay token generated
> via `/ocuclaw-setup`.

| ST-1 | **Plugin loads and registers without version-gate refusal** |
|------|-----------------------------------------------------------|
| Goal | Prove the plugin passes `register(ctx)` without throwing `RuntimeError` |
| Method | `hermes plugins enable ocuclaw` then check gateway log for the "platform registered" info message |
| Pass | Gateway log contains `[ocuclaw] platform registered (hermes 0.22.5, optional hooks: ...)` |
| Fail | Gateway log contains `RuntimeError` or `hermes_version_outside_supported_range` |

| ST-2 | **`hermes ocuclaw doctor` reports clean host admission** |
|------|--------------------------------------------------------|
| Goal | Prove the doctor lane sees a supported Hermes version |
| Method | `hermes ocuclaw doctor` |
| Pass | `hermes_version` row shows `0.22.5` with no `unsupported` error; `version_check` shows `supported` or similar positive status |
| Fail | `hermes_unsupported` appears as an error |

| ST-3 | **Setup status leaves `unsupported` absent** |
|------|-------------------------------------------|
| Goal | Prove the setup and status surfaces no longer flag the version |
| Method | `hermes ocuclaw status` (or equivalent CLI status command) |
| Pass | No `hermes_unsupported` error in the status output |
| Note | Other errors (`relay_token_missing`) are expected on a pre-setup host — only `hermes_unsupported` must be absent |

| ST-4 | **Relay token bootstrap works** |
|------|------------------------------|
| Goal | Prove the relay credential bootstrap path works on 0.22.5 |
| Method | Run `/ocuclaw-setup` in a Hermes session; follow the guided flow; verify `OCUCLAW_RELAY_TOKEN` exists in `.env` after |
| Pass | `echo $OCUCLAW_RELAY_TOKEN` returns the generated token; `hermes ocuclaw status` shows relay token present |

| ST-5 | **Relay listens on 127.0.0.1:47801** |
|------|-------------------------------------|
| Goal | Prove the Node child spawns, the NDJSON handshake completes, and the relay WebSocket is bound |
| Method | After ST-4, check `ss -tlnp \| grep 47801` or equivalent |
| Pass | Port 47801 bound to 127.0.0.1 by the Node process |

| ST-6 | **Hook registration integrity** |
|------|-------------------------------|
| Goal | Prove the hooks registered by OcuClaw fire on this 0.22.5 host |
| Method | Enable debug logging for the plugin; trigger a full turn (CLI chat); inspect the gateway log for hook firings |
| Pass | Log shows `on_session_end`, `pre_llm_call`, `post_api_request`, `pre_tool_call`, `post_tool_call` events for the turn on the `ocuclaw` platform |

| ST-7 | **Optional hook registry** |
|------|--------------------------|
| Goal | Prove the optional hook probe works correctly on 0.22.5 |
| Method | Check the gateway log for the `optional hooks:` list in the platform-registered message |
| Pass | The list includes `interim_hook` (always, on 0.22.x hosts) and may include `stream_hooks` if `plugins.stream_reasoning_deltas` is set |

### 6.3 Regression Gate

| RG-1 | **0.21.x host still admitted** |
|------|------------------------------|
| Goal | Prove the gate still passes on a 0.21.5 host |
| Method | Run UT-1 on a 0.21.5 Hermes installation |
| Pass | `hermes_version_supported("0.21.5")` → True |

| RG-2 | **0.20.x host still refused** |
|------|-----------------------------|
| Goal | Prove the gate still refuses pre-0.21.1 hosts |
| Method | Run UT-1 with `"0.20.0"`, `"0.20.5"`, `"0.20.99"` |
| Pass | All return False |

| RG-3 | **0.23.0 host still refused** |
|------|-----------------------------|
| Goal | Prove the gate does not silently admit an uncertified future major |
| Method | Run UT-1 with `"0.23.0"`, `"0.23.0.dev0"`, `"0.23.99"` |
| Pass | All return False |

---

## 7. Known Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| SessionDB schema change (R16) | Medium | The session-read-state lane may fail to probe the required columns if 0.22.x renamed or removed them. The probe is fail-soft — missing columns disable the feature token rather than crashing. |
| `gateway_state.json` format change (R20) | Low | The status report document's `gatewayPlatformState` key may have moved or been renamed. The `receipts.py` reader is fail-soft; a missing key produces `None` rather than a crash. |
| Smart-approval `choice` values (R15) | Low | New `choice` values arrive as additive fields in the kwargs dict; OcuClaw's handler checks for known values explicitly and ignores unknown ones. |
| Session ID format change (#142993) | Low | 0.22.x changed session IDs from `YYYYMMDD_HHMMSS_xxxxxx` to `local-<64 hex>`. If `session_rpc.py` parses session IDs expecting the old format, it will break. The coder must verify. |

---

## 8. Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-11-08 | Initial spec: gate-widening port from 0.21.5 to 0.22.5 |
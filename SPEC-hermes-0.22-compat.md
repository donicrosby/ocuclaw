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
| R4   | Every bundled skill document that asserts the old range `>=0.21.1,<0.22.0` SHALL be updated to `>=0.21.1,<0.23.0`, including the gate text in `snapshot.py`. | VERIFIED | Grep audit: 11 occurrences across 7 files under `skills/ocuclaw-assist-hermes/` and `README.md`; 1 additional occurrence in `snapshot.py:563` (literal range string); `snapshot.py:450-458` carries the user-facing `hermes_unsupported` remediation text that also needs the range updated |
| R5   | The plugin version in `plugin.yaml` SHALL become `2.1.2+hermes022`, an honest local suffix that never presents as an official OcuClaw release. | VERIFIED | Task body: "honest-versioning requirement" |
| R6   | The plugin's hook registration surface SHALL remain unchanged — the same seven required hooks (`on_session_end`, `post_approval_response`, `pre_tool_call`, `post_tool_call`, `post_api_request`, `pre_llm_call`, `api_request_error`) and the same optional hooks (`on_interim_message`, `on_stream_*`, `pre_transcription`) — because the Hermes plugin API contract is additive across the 0.21→0.22 boundary and no hook OcuClaw uses was removed or changed. | VERIFIED | Tag diff (0.21.5→0.22.5): adds 5 hooks (`on_human_input_request`, `on_human_input_resolved`, `on_session_delete`, `post_compaction`, `post_gateway_admission`), removes none — all 12 OcuClaw-used hooks present at both tags. Hermes plugin docs: "Evolve additively" (developer-guide/plugins/index.md:239 @ v0.22.5). |
| R7   | The `ctx.register_platform()` call SHALL pass unchanged because its kwargs are additive — new kwargs in 0.22.x ride `**entry_kwargs` with defaults, and the existing kwargs OcuClaw passes (`name`, `label`, `adapter_factory`, `check_fn`, `validate_config`, `setup_fn`, `is_connected`, `allowed_users_env`, `allow_all_env`, `allow_update_command`, `platform_hint`, `env_enablement_fn`) remain valid. | VERIFIED | Signature at both tags: `name, label, adapter_factory, check_fn, validate_config=None, required_env=None, install_hint="", **entry_kwargs` — byte-identical. |
| R8   | The `ctx.register_skill()` calls for the two bundled skills (`ocuclaw-assist-hermes`, `glasses-ui`) SHALL pass unchanged — `register_skill` moved to `plugins_content.py` at 0.22.5 but is re-exported from `plugins` unchanged; the adapter feature-detects via `getattr` anyway. | VERIFIED | Signature identical at both tags; adapter feature-detects via `getattr` — no version-bound branch |
| R9   | The `ctx.register_system_prompt_section()` calls SHALL pass unchanged — the registered prompt section API is identical across 0.21→0.22. | VERIFIED | Signature identical at both tags |
| R10  | The `ctx.register_tool()` call for the setup tool SHALL pass unchanged. | VERIFIED | Signature identical at both tags |
| R11  | The `ctx.register_cli_command()` calls SHALL pass unchanged — the CLI command registration surface is identical across 0.21→0.22. | VERIFIED | Signature identical at both tags |
| R12  | The `ctx.register_auxiliary_task()` call for silent-input prediction SHALL pass unchanged. | VERIFIED | Signature identical at both tags |
| R13  | The `register_hook` call signature SHALL be unchanged across the 0.21→0.22 boundary — `def register_hook(self, hook_name: str, callback: Callable)` is byte-identical at both tags. | VERIFIED | Source at both tags: `hermes_cli/plugins.py` `register_hook(self, hook_name: str, callback: Callable)` — no `hold_stream` parameter exists in any 0.22.x release. The `hold_stream` keyword-only parameter is a **0.23.0** addition (`plugins.py:935`), outside the supported range. |
| R14  | The `on_session_end` hook payload SHALL be verified for the `platform` field name — the 0.22.5 `on_session_end` kwargs are identical to 0.21.5; the coder SHALL confirm presence of `session_id` and `platform` on the live host. | VERIFIED | Source at both tags (`turn_finalizer.py:798`, byte-identical): kwargs are `session_id, task_id, turn_id, completed, failed, interrupted, turn_exit_reason, model, platform`. OcuClaw's callback accepts `**kwargs`. |
| R15  | The `post_approval_response` hook payload SHALL be verified for the `choice` field behavior — `smart_approve`/`smart_deny` were already documented in the 0.21.5 `VALID_HOOKS` comment; the coder SHALL confirm no new `choice` values were added that OcuClaw's handler would mishandle. | VERIFIED | 0.21.5 `plugins.py:144-146` comment already lists `smart_approve`/`smart_deny` as valid `post_approval_response` `choice` values; OcuClaw's handler filters on known choices — unknown values are ignored |
| R16  | The `session_read_state_supported()` probe in `adapter.py` SHALL be re-verified against the 0.22.5 SessionDB schema — the 0.22.5 SessionDB schema carries the same columns OcuClaw probes (`hidden`, `last_read_at`) and the three SessionDB primitives (`set_session_hidden`, `set_session_read`, `session_unread`), with `SCHEMA_VERSION = 32 ≥ MIN_SCHEMA_VERSION = 30`. The probe is fail-soft. | VERIFIED | Verified against v0.22.5 source: `hermes_state_common.py:523-524` (columns), `hermes_state_sessions.py:1058-1068` (primitives), `health_management.py:137,248` (schema check). Fail-soft confirmed: `session_rpc.py:186-232` double exception-wrap → inert + cached. Engine session-ID minting unchanged at 0.22.5 (`hermes_state_ids.py:56` — `YYYYMMDD_HHMMSS_<hex6>`). |
| R17  | The `config.yaml` config-key surface (`display.platforms.ocuclaw.*`, `gateway.multiplex_*`, `plugins.stream_reasoning_deltas`) SHALL be verified — no breaking config-key rename or removal is documented for 0.22.x. | VERIFIED | `plugins.stream_reasoning_deltas` alive at 0.22.5 (`agent/plugin_stream_hooks.py:164`, default False); `gateway.multiplex_profiles` alive (false-value retired, rewritten true at `hermes_cli/gateway_multiplex_mode.py`); plugin detects retirement via code probe (`RETIRED_OPT_OUT_REASON` attr), not a version string. `display.platforms.<p>.streaming` alive at 0.22.5. |
| R18  | The `management RPC` surface (`hermes ocuclaw *` subcommands, `hermes plugins *`, `hermes config *`) SHALL be verified — the CLI subcommand dispatch mechanism is unchanged in 0.22.x. | VERIFIED | Hermes docs: CLI extension API unchanged; `register_cli_command` unchanged |
| R19  | The Node runtime bridge (`control_link.py`, `native_compat.py`, `provenance.py`) SHALL pass unchanged — these modules bridge over NDJSON-stdio and do not touch the Hermes plugin API surface. | VERIFIED | Import chains are stdlib/plugin-local; no Hermes API dependency |
| R20  | The gateway state reader (`receipts.py`) SHALL be verified for the 0.22.x `gateway_state.json` format — `gateway_state.json` is still written and read at 0.22.5; the `gatewayPlatformState`-absent live finding is a reporting difference, not a format change. | VERIFIED | `gateway_state.json` still written/read at 0.22.5 (s6 lifecycle writer; `gateway_windows.py`, `gateway_migrate.py`). Fail-soft confirmed: `receipts.py:715-735` + `_read_json` → `(None, status)` on OSError/Unicode/ValueError; `gateway.status` import exception-wrapped. |
| R21  | The `HERMES_RELEASE_DATES` table in `health.py` SHALL add the 0.22.0 release date entry for identity-accuracy only — the version parser's primary path is `__version__` or install stamp; the date-fallback path cannot identify any 0.22.x host (v0.22.5 ships `__release_date__ = "2026.9.24"` which resolves to "0.21.5", inside the supported range by design). | VERIFIED | Code: `health.py` lines 368-374. GitHub Releases: v0.22.0 published 2026-10-14. Identity-accuracy only — admission rides `__version__`/install stamp, which the spec already covers. |

---

## 3. Engine Delta Audit: Hermes 0.21 → 0.22

### 3.1 Methodology

The delta was audited by:
1. Reading the 0.22.0 release notes and the 0.22.0→0.23.0 rollup
   (which documents the full 0.22.1–0.22.7 patch window).
2. Reading the published Hermes plugin API documentation
   (hooks reference, plugin registration surface).
3. Reading the `hermes_cli/plugins.py` source at the **v0.22.5** tag
   (NOT the v0.23.0 tag — the initial audit relied on a 0.23-era source
   read; every claim below has been re-verified against v0.22.5).
4. Comparing the hook catalog against the hook
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
| `ctx.register_hook(name, callback)` | `(self, hook_name, callback)` | `(self, hook_name, callback)` — identical (no `hold_stream`) | No |
| `ctx.register_skill(name, path, description)` | 3-positional API | Same (moved to `plugins_content.py`, re-exported) | No |
| `ctx.register_tool(...)` | Keyword API | Same | No |
| `ctx.register_system_prompt_section(...)` | Keyword API | Same | No |
| `ctx.register_cli_command(...)` | Keyword API | Same | No |
| `ctx.register_auxiliary_task(...)` | Keyword API | Same | No |
| `hermes_cli.plugins.VALID_HOOKS` | `Set[str]` of hook names | `set[str]` of hook names (superset of 0.21.5) | No (additive) |
| Hook callbacks (e.g. `on_session_end`) | Receive kwargs by name | Receive same kwargs + new additive fields | No (OcuClaw uses `**kwargs`) |

> **Note:** `register_hook` at v0.22.5 is `(self, hook_name: str, callback: Callable)` — byte-identical to 0.21.5. The `hold_stream` keyword-only parameter exists only at **v0.23.0** (`plugins.py:935`), outside the supported range. `VALID_HOOKS` is a plain `set[str]`, not `frozenset`; OcuClaw's `_valid_hook_names()` wraps it in its own `frozenset` — membership semantics identical.

### 3.3 New in 0.22.x (Not Used by OcuClaw)

These features arrived in the 0.22.x window but OcuClaw does not depend on them:

| Addition | Description | OcuClaw Impact |
|----------|-------------|----------------|
| `post_compaction` hook | Fires after every committed compaction | Not registered by OcuClaw |
| `on_session_delete` hook | Fires on session deletion | Not registered by OcuClaw |
| `pre_llm_call` block capability | Hook can return `{"action": "block"}` to cancel a turn | Not used — OcuClaw's `pre_llm_call` handler is observer-only |
| `pre_transcription` hook receiver | New hook dispatch seam | OcuClaw already probes for this hook independently |
| New `post_approval_response` `choice` values | Additional approval choices beyond those already in 0.21.5 | OcuClaw's handler filters on known choices — unknown values are ignored |
| `ctx.post_message()`, `ctx.side_question()` | Plugin message posting | Not used by OcuClaw |
| Plugin LLM access (`ctx.llm.complete(...)`) | Host-owned LLM call | Not used by OcuClaw |
| Kanban hooks (`kanban_task_claimed` etc.) | Board lifecycle hooks | Not registered by OcuClaw |

> **Note:** `smart_approve`/`smart_deny` were already documented as valid
> `post_approval_response` `choice` values in the 0.21.5 `plugins.py:144-146`
> `VALID_HOOKS` comment — they are NOT new in 0.22.x. `register_hook(hold_stream=True)`
> is a **0.23.0** feature only (`plugins.py:935`); it does not exist in any
> 0.22.x release.

### 3.4 Removed / Renamed in 0.22.x

| Change | OcuClaw Impact |
|--------|----------------|
| Tool renames (`todo`→`todo_list`, `cronjob`→`cronjob_manage`, `process`→`process_manage`) | Old names still work (#97979); `todo`→`todo_list` was a 0.21.5 rename, not a 0.22.x change. OcuClaw does not call these tools directly. |
| Old plugin compatibility import layer removed | OcuClaw imports from `hermes_cli.plugins` (the current layer), not the old one |
| `hermes sync` removed (#132465) | Not used by OcuClaw |
| Built-in browser tools removed in favor of `browser_exec` | OcuClaw does not use browser tools |

> **Note:** The session ID format has NOT changed in the engine at 0.22.5 —
> `hermes_state_ids.py:56` still mints `YYYYMMDD_HHMMSS_<hex6>`, identical
> to 0.21.5. Issue #142993 is a v0.22.4 Desktop-layer regression report,
> not an engine format change. No plugin file parses session-ID shapes at all.
> Desktop `local-` IDs are a client-layer concern outside plugin scope.

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
| `gatewayPlatformState` absent | Info | Reporting-format difference (not a data change — `gateway_state.json` still written at 0.22.5); see R20 |

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
| 368-374 | `HERMES_RELEASE_DATES = {...}` | Add `"2026.10.14": "0.22.0"` entry for identity-accuracy only |

> **Coder note:** The v0.22.0 GitHub release date is 2026-10-14
> (published 2026-10-14T03:21:46Z). This entry is for identity-accuracy
> only — the date-fallback path can never identify any 0.22.x host because
> v0.22.5 ships `__release_date__ = "2026.9.24"` (which resolves to "0.21.5",
> inside the supported range). The version parser's primary admission path
> (`__version__` / install stamp) is the one that matters; the date table is
> a fallback for hosts lacking those stamps, and on such a host 0.22.5
> resolves to "0.21.5" (admitted). No 0.22.x-specific date entry can match.

#### Health-tier note (0.22.5)

On 0.22.5, no `NATIVE_BUILDS` hash set matches (the table ends at 0.21.5),
so the health reader drops from **AUDITED** to **COMPATIBLE** tier — a
user-visible status change. The health lane still serves (probe inputs
verified present: `hidden`/`last_read_at` columns, 3 SessionDB primitives,
`SCHEMA_VERSION = 32 ≥ MIN_SCHEMA_VERSION = 30`). The `_probe_diagnostics`
call against 0.22.5's `doctor.py` output shape is unverified on the live
host and should be exercised as part of the smoke test. The COMPATIBLE
tier is the accepted steady state for this port; a `NATIVE_BUILDS` recert
for 0.22.5 would restore AUDITED but is not required for plugin operation.

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

### 4.5 Gate-Output Text (`snapshot.py`)

The `snapshot.py` module carries user-facing gate-text that would instruct
operators to downgrade away from a supported version post-port.

#### `snapshot.py:450-458` — `hermes_unsupported` remediation text

| Current | Replacement |
|---------|-------------|
| `"This Hermes host is outside the supported OcuClaw contract. Use Hermes 0.21.x (recommended release v2026.9.24 / engine 0.21.5), then restart and run hermes ocuclaw doctor --json. Do not force-load this bundle on older or 0.22+ engines."` | `"This Hermes host is outside the supported OcuClaw contract. Use Hermes 0.21.5 or later 0.21.x, or the 0.22.x compatibility port (recommended release v0.22.5), then restart and run hermes ocuclaw doctor --json. Do not force-load this bundle on unsupported engines."` |

> **Coder note:** The old text explicitly told operators to avoid 0.22+
> engines — after porting, that text would instruct users to downgrade away
> from a now-supported version. Replace with a version-neutral message.

#### `snapshot.py:563` — literal range string (comment)

| Line | Change |
|------|--------|
| 563 | The `_RANGE_RE` comment carries the literal `>=0.21.1,<0.22.0` string as an example — update to `>=0.21.1,<0.23.0` |

### 4.6 Summary of Files Touched

| File | Changes |
|------|---------|
| `adapter.py` | 4 constant lines |
| `health.py` | 4 constant lines + 1 table entry |
| `plugin.yaml` | 1 version line |
| `README.md` | 1 version line |
| `snapshot.py` | 2 lines (remediation text + range comment) |
| `skills/ocuclaw-assist-hermes/SKILL.md` | 3 version lines |
| `skills/ocuclaw-assist-hermes/references/troubleshooting.md` | 1 version line |
| `skills/ocuclaw-assist-hermes/references/install-lifecycle.md` | 2 version lines |
| `skills/ocuclaw-assist-hermes/references/fresh-install.md` | 2 version lines |
| `skills/ocuclaw-assist-hermes/references/quick-reference.md` | 1 version line |
| `skills/ocuclaw-assist-hermes/references/update.md` | 2 version lines |

**Total: 11 files, ~23 line-level changes.** No code logic changes — this is a
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
- **0.23.0 features:** The `register_hook(hold_stream=...)` parameter is a
  0.23.0 addition outside the supported range — no port changes are needed
  for it and the plugin must NOT accept 0.23.0+ until a separate
  recertification.

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

| ST-8 | **`post_approval_response` hook fires with a real approval decision** |
|------|---------------------------------------------------------------------|
| Goal | Prove `post_approval_response` actually fires (not just registers) — ST-1…ST-7 never trigger an approval decision |
| Method | On a scratch profile with approval gating enabled for ocuclaw tools, execute a tool that triggers an approval prompt; approve the tool call; inspect the gateway log |
| Pass | Gateway log shows a `post_approval_response` event with a `choice` kwarg on the `ocuclaw` platform |

| ST-9 | **`api_request_error` hook fires on a failed provider call** |
|------|-----------------------------------------------------------|
| Goal | Prove `api_request_error` actually fires — ST-1…ST-7 never trigger a provider error |
| Method | Misconfigure a scratch profile's provider credential (deliberately invalid API key); trigger one turn; inspect the gateway log |
| Pass | Gateway log shows an `api_request_error` event on the `ocuclaw` platform |

| ST-10 | **`on_interim_message` fires under streaming** |
|------|----------------------------------------------|
| Goal | Prove `on_interim_message` fires when streaming is configured — ST-7 checks registration only |
| Method | On a scratch profile with `plugins.stream_reasoning_deltas: true`, trigger a turn; inspect the gateway log |
| Pass | Gateway log shows `on_interim_message` events on the `ocuclaw` platform |

| ST-11 | **Health reads serve on 0.22.5 (COMPATIBLE tier)** |
|------|--------------------------------------------------|
| Goal | Prove the health lane reports a non-error status despite the expected AUDITED→COMPATIBLE tier drop on 0.22.5 |
| Method | `hermes ocuclaw doctor` or the health-read path; inspect the health tier output |
| Pass | Health tier reads `COMPATIBLE` (not ERROR); no probe crashes or unhandled exceptions |

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
| Health-tier drop (AUDITED→COMPATIBLE) | Low | On 0.22.5 no `NATIVE_BUILDS` hash matches; health reads drop to COMPATIBLE. This is user-visible but non-blocking — the health lane still serves. A 0.22.5 `NATIVE_BUILDS` recert (separate follow-up card) would restore AUDITED. |

---

## 8. Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.1 | 2026-11-08 | Revision per adversarial review (round 2): F1 (hold_stream is 0.23-only — R13 rewritten, §3.2/§3.3 fixed); F2 (false session-ID claim deleted — §3.4, §7 risk, R16); F3 (R14 field list corrected — `reason`/`profile` removed, `task_id`/`turn_id`/`failed`/`turn_exit_reason` added); F4 (R21 date corrected to 2026-10-14, re-scoped to identity-accuracy only); F5 (snapshot.py:450-458 + :563 added to §4; R4 count fixed to 11; totals restated); F6 (delta-audit errors: smart_approve/smart_deny already 0.21.5, todo→todo_list 0.21.5, VALID_HOOKS is set not frozenset); F7 (test plan: ST-8/ST-9/ST-10 added for hook-firing coverage; ST-11 for health COMPATIBLE tier); F8 (health-tier drop documented in §4.1 and §7); N1 (R4 arithmetic); N2 (R7 entry_kwargs wording) |
| 1.0 | 2026-11-08 | Initial spec: gate-widening port from 0.21.5 to 0.22.5 |

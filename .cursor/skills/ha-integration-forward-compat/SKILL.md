---
name: ha-integration-forward-compat
description: >-
  Full forward-compat audit of the MyDolphin Plus custom integration against
  Home Assistant developer blog posts and core API contracts—entire
  custom_components tree, not a fixed grep list or HA version. Produces a risk
  register. Use before releases, after new HA versions, or for developer blog,
  deprecations, breaking changes, hassfest, HACS, or integration API risk.
disable-model-invocation: true
---

# Home Assistant integration forward compatibility

Keep **all** of `custom_components/mydolphin_plus/` aligned with current and upcoming Home Assistant core behavior. Do **not** hardcode a target HA version; discover what is current each run.

The audit is **whole-integration**, not a checklist of a few strings. Known grep patterns are shortcuts only—see [reference.md](reference.md) § High-risk patterns.

## 1. Primary source: developer blog

1. Open [Home Assistant Developer Docs](https://developers.home-assistant.io/) and read **Recent Blog Posts** (Blog index if needed).
2. Review posts from the **last 12 months**, or since `docs/ha-compat-last-audit.md` if present.
3. Filter relevance: [reference.md](reference.md) § Blog filter.
4. Build a **change catalog**: API/symbol names, deprecated behavior, replacement, breaks-in/release if stated (cite the post URL—do not invent dates).

Supplement when needed:

- [home-assistant/core releases](https://github.com/home-assistant/core/releases) (latest stable tag)
- `https://www.home-assistant.io/changelogs/core-{major.minor}/` for that tag
- [Developer docs](https://developers.home-assistant.io/docs/creating_integration_manifest/) / platform docs for symbols you rely on

## 2. Repo baseline

Read `manifest.json`, `hacs.json`, `__init__.py` (setup/unload/remove), `config_flow.py`, and [reference.md](reference.md) § MyDolphin Plus invariants.

## 3. Full integration code review (required)

Review **every Python file** under `custom_components/mydolphin_plus/` (including `managers/`, `common/`, `models/`). Do not stop after grep.

### 3a. Import and API inventory

1. List **all** `from homeassistant...` and `import homeassistant...` usages (module, symbol, file).
2. Group by area: `config_entries`, `data_entry_flow`, `helpers.*`, `components.*` platforms in use, `const`, `core`, etc.
3. For each group, cross-check the **change catalog** (blog) and developer docs: is anything we use deprecated, renamed, or scheduled to break?
4. Where uncertain, spot-check `home-assistant/core` `dev` for `deprecated`, `report_usage`, `breaks_in_ha_version` on modules/classes we subclass or call.

### 3b. Surface-by-surface review

| Surface                                                               | What to verify                                                                                      |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Config flow / options / reauth**                                    | Flow steps, abort/reload helpers, storage of credentials, schema, no deprecated flow APIs           |
| **`async_setup_entry` / `async_unload_entry` / `async_remove_entry`** | Lifecycle matches current integration docs; `hass.data`, forward setup, cleanup                     |
| **Each platform module**                                              | Entity base class, features, device_info, unique_id, `async_add_entities`, service handlers         |
| **Coordinator / REST / AWS client**                                   | `DataUpdateCoordinator`, debouncer, dispatcher, aiohttp session helpers, threading/async boundaries |
| **Entity descriptions & translations**                                | Device classes, units, entity categories, translation keys                                          |
| **Diagnostics**                                                       | Redaction, registry APIs                                                                            |
| **Custom services** (if any)                                          | Schema and registration still valid                                                                 |
| **Manifest / HACS**                                                   | `dependencies`, `requirements`, `iot_class`, minimum HA vs APIs actually used                       |

For each file, note: **OK**, **risk**, or **N/A** with one-line evidence (symbol or blog post).

### 3c. High-risk patterns (accelerator only)

Run [reference.md](reference.md) § High-risk patterns as a **fast pass**; any hit must still be understood in full file context. **Absence of hits does not mean pass**—3b is mandatory.

### 3d. Third-party vs HA core

- **`awsiotsdk` / `awscrt`:** note HA runtime Python from latest stable release notes; flag **Watch** if wheel compatibility is unclear.
- Do **not** apply HA **MQTT integration** migration posts unless this repo depends on `homeassistant.components.mqtt`.

## 4. Classify findings

| Status         | Meaning                                                           |
| -------------- | ----------------------------------------------------------------- |
| **Fix now**    | Our code uses a deprecated/removed API for current or next stable |
| **Fix before** | Deprecation with future breaks-in; we still use old pattern       |
| **Watch**      | External/runtime risk; no certain code change                     |
| **N/A**        | Blog/API change does not touch this integration                   |

**Default strictness:** audit **fails** if any **Fix now** remains; warn on **Fix before** and **Watch**.

## 5. Deliverables

1. **Audit header:** date, blog posts count, stable tag (if fetched), manifest version, HACS min HA.
2. **Coverage summary:** file count reviewed, import inventory summary (e.g. “12 modules from homeassistant.helpers…”), platforms list.
3. **Risk register:** ID, file/symbol, source (blog URL or core/doc), status, action.
4. **Recommended changes** (ordered); implement only if user asked **fix** / **implement**.
5. **Changelog** (when shipping fixes): `## {version}` = exact `manifest.json` `version`.
6. **Optional:** update `docs/ha-compat-last-audit.md` after audit.

## 6. Validation

After **any** file changes in the repo (fixes, metadata, changelog, docs):

1. Run from the repository root:

   ```bash
   pre-commit run --all-files
   ```

2. If hooks modify files, stage those changes and re-run until all hooks pass (or fix reported issues).

Also:

- Run **hassfest** if `.github/workflows/hassfest.yaml` exists (CI may do this; run locally when integration structure or manifest changed).
- If the repo has tests touching HA behavior, run them when Python code under `custom_components/` changed.

## When to implement vs report

- **audit / review / check / risks** → report only unless user also says **fix** / **implement**.
- **fix / update / prepare release** → minimal fixes + changelog + metadata alignment, then **§6 Validation** (including `pre-commit run --all-files`).

## Reference

[reference.md](reference.md) — blog filters, surfaces checklist, high-risk patterns, invariants.

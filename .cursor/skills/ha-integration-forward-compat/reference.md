# Reference: HA forward compat (mydolphin_plus)

Confirm **breaks in** dates from the blog post or current core/docs—not from this file.

## MyDolphin Plus invariants

- **Connectivity:** Maytronics via **AWS IoT Device SDK** (`awsiotsdk` in manifest)—not the Home Assistant **MQTT** config entry integration.
- **iot_class:** `cloud_push` in manifest; HACS **Cloud Push** (display).
- **Auth:** Cognito OTP; reauth via `async_update_reload_and_abort` without pairing `add_update_listener` reload.
- **Vacuum:** `StateVacuumEntity` + `VacuumActivity`; battery via **sensor** (`SensorDeviceClass.BATTERY`), not on vacuum.
- **Minimum HA:** `VacuumActivity` implies 2026.1+; `hacs.json` must not understate that.

## Blog filter

**Include:** custom integrations, config/data entry flow, config entries, entity platforms, coordinators, device/entity registry, storage, aiohttp, deprecations, breaking changes, manifest/hassfest.

**Exclude** unless code exists for it: frontend-only, Supervisor, OS, mobile apps, Voice, themes, custom cards, Browse Media, unrelated platforms.

## Full review: file tree

Audit all paths under:

```text
custom_components/mydolphin_plus/
  __init__.py
  config_flow.py
  manifest.json
  strings.json
  translations/
  vacuum.py, sensor.py, binary_sensor.py, light.py, select.py, number.py, remote.py
  diagnostics.py
  common/
  managers/
  models/
```

## Import inventory template

Use when reporting coverage:

| Module imported              | Symbols (representative) | Files | Blog/core risk |
| ---------------------------- | ------------------------ | ----- | -------------- |
| homeassistant.config_entries | ConfigFlow, …            | …     | …              |

Complete one row per distinct `homeassistant.*` top-level import path used.

## Surfaces checklist (every audit)

- [ ] Config flow + options + reauth (`config_flow.py`, `managers/flow_manager.py`)
- [ ] Setup / unload / remove entry (`__init__.py`)
- [ ] Coordinator + API clients (`managers/coordinator.py`, `rest_api.py`, `aws_client.py`, `config_manager.py`)
- [ ] Each entity platform file
- [ ] Entity descriptions + consts tied to HA enums/device classes
- [ ] Diagnostics
- [ ] Manifest + hacs.json vs code reality
- [ ] External requirements (`awsiotsdk`) vs HA Python

## High-risk patterns (accelerator grep only)

Quick scan under `custom_components/mydolphin_plus/`—**not sufficient alone**:

| Pattern                                                            | Why it matters                      |
| ------------------------------------------------------------------ | ----------------------------------- |
| `add_update_listener`                                              | Reload interaction with config flow |
| `async_update_reload_and_abort` / `_abort_if_unique_id_configured` | With listeners → future error class |
| `show_advanced_options`                                            | Deprecated flow UX                  |
| `connection_class` in flow                                         | Use manifest `iot_class`            |
| Vacuum battery on entity                                           | Separate sensor required            |
| Legacy vacuum `STATE_*` imports                                    | `VacuumActivity`                    |
| `homeassistant.components.mqtt`                                    | Usually N/A here                    |
| `self.state` for vacuum control logic                              | Prefer `activity`                   |

Also search our tree for: `deprecated`, `report_usage` (unlikely in custom code), and any override of HA `@property`/`@final` APIs that changed on core `dev`.

## Config flow reload rule

**Anti-pattern:** `add_update_listener` that reloads **and** flow `async_update_reload_and_abort` / unique-id reload for same entry.

**OK here:** reauth reload+abort without listener; options `async_update_entry` + `async_schedule_reload` without listener.

## Platforms in this integration

vacuum, sensor, binary_sensor, light, select, number, remote — verify each against current platform docs when blog mentions that domain.

## Themes often on the developer blog

Verify against **our** code each run; dates come from posts:

- Vacuum battery migration to sensor
- Config entry listener + flow reload
- Data entry flow advanced mode / sections
- HA MQTT protocol (N/A unless we use HA MQTT)

## Incremental audit log

`docs/ha-compat-last-audit.md`: store last audit UTC and last blog title reviewed. Still perform **full** code review every run; use the log only to prioritize **new** blog posts.

## Post-change checks

When the skill run changes files:

```bash
pre-commit run --all-files
```

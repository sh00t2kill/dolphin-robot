# Maytronics Robot Rebrand Plan

This document lists the expected changes for forking the current MyDolphin Plus
integration into a new Home Assistant custom integration named **Maytronics
Robot**, with domain `maytronics_robot`.

The new project should remain clearly credited as a fork of the original
MyDolphin Plus integration and should preserve contributor credits.

## Naming Decision

- New repository/display name: **Maytronics Robot**
- New Home Assistant integration domain: `maytronics_robot`
- New integration package path: `custom_components/maytronics_robot`
- Initial fork version: `v1.0.0`
- Supported mobile apps remain:
  - `MyDolphin Plus`
  - `Maytronics One`

Important: not every `mydolphin_plus` string should be replaced. Some strings
represent the old integration domain and should become `maytronics_robot`.
Other strings represent the MyDolphin Plus mobile app id/name and should remain.

## Required Functional Changes

| File or path                                                    | Required change                                                                                                                                                                            |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `custom_components/mydolphin_plus/`                             | Rename folder to `custom_components/maytronics_robot/`.                                                                                                                                    |
| `custom_components/maytronics_robot/manifest.json`              | Change `"domain"` to `"maytronics_robot"`, `"name"` to `"Maytronics Robot"`, update `documentation` and `issue_tracker` to the new repository, and reset `"version"` to `"v1.0.0"`.        |
| `custom_components/maytronics_robot/common/consts.py`           | Change `DEFAULT_NAME` to `"Maytronics Robot"` and `DOMAIN` to `"maytronics_robot"`. Update `INVALID_TOKEN_SECTION` to the new README URL. Keep `APP_ID_MYDOLPHIN_PLUS = "mydolphin_plus"`. |
| `custom_components/maytronics_robot/common/integration_info.py` | Replace the hard-coded `async_get_integration(hass, "mydolphin_plus")` with `maytronics_robot`, preferably by importing and using `DOMAIN`.                                                |
| `custom_components/maytronics_robot/__init__.py`                | Update docstrings and documentation references from MyDolphin Plus to Maytronics Robot.                                                                                                    |
| `custom_components/maytronics_robot/models/system_details.py`   | Update absolute imports from `custom_components.mydolphin_plus...` to `custom_components.maytronics_robot...`.                                                                             |
| `hacs.json`                                                     | Change `"name"` from `"MyDolphin Plus"` to `"Maytronics Robot"`.                                                                                                                           |

## Translation Changes

Update user-visible integration names in all translation files. Entity names can
usually remain unchanged unless they mention the old integration name directly.

| File                                                      | Required change                                                                                                                                  |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `custom_components/maytronics_robot/strings.json`         | Use "Set up Maytronics Robot", "Re-authenticate Maytronics Robot", and session-expired text mentioning Maytronics Robot.                         |
| `custom_components/maytronics_robot/translations/en.json` | Same English wording as `strings.json`.                                                                                                          |
| `custom_components/maytronics_robot/translations/fr.json` | Use "Configurer Maytronics Robot", "Réauthentifier Maytronics Robot", and "Votre session Maytronics Robot a expiré...".                          |
| `custom_components/maytronics_robot/translations/it.json` | Use "Imposta Maytronics Robot" or "Configura Maytronics Robot", "Riautentica Maytronics Robot", and "La sessione Maytronics Robot è scaduta...". |

Keep app-specific labels unchanged:

- `MyDolphin Plus`
- `Maytronics One`
- `APP_ID_MYDOLPHIN_PLUS = "mydolphin_plus"`
- `APP_ID_MAYTRONICS_ONE = "maytronics_one"`

## Test Changes

After renaming the integration package, tests must import from the new package
path.

| File                                  | Required change                                                                                                       |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `tests/api_test.py`                   | Update imports from `custom_components.mydolphin_plus...` to `custom_components.maytronics_robot...`.                 |
| `tests/genereate_aws_token_test.py`   | Update imports.                                                                                                       |
| `tests/indicators_test.py`            | Update imports.                                                                                                       |
| `tests/test_reauth_flow_semantics.py` | Update imports. If internal class names are rebranded, update `MyDolphinPlusCoordinator` references too.              |
| `tests/test_rest_api_semantics.py`    | Update imports. Keep tests that verify the default mobile app is MyDolphin Plus if that remains the intended default. |
| `tests/test_vacuum_actions.py`        | Update imports.                                                                                                       |
| `tests/translation_compare.py`        | Change `DOMAIN = "mydolphin_plus"` to `DOMAIN = "maytronics_robot"`.                                                  |
| `tests/cognito_test.py`               | Update only integration-level comments. Keep app key names such as `"MyDolphin Plus"`.                                |

## Documentation and Release Files

| File                      | Required change                                                                                                                                                                                                                                                                                                                                       |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `README.md`               | Rewrite title and description for Maytronics Robot. Installation should say "Add Maytronics Robot". Requirements should mention MyDolphin Plus or Maytronics One app/account. Update debug logger examples to `custom_components.maytronics_robot`. Update storage examples to `.storage/maytronics_robot.config.json`. Add credits/fork attribution. |
| `CHANGELOG.md`            | Reset to `v1.0.0`. The first entry should explain that Maytronics Robot is forked from the original MyDolphin Plus integration, rebranded, and supports both MyDolphin Plus and Maytronics One.                                                                                                                                                       |
| `CONTRIBUTING.md`         | Change project name to Maytronics Robot and update the integration path to `custom_components/maytronics_robot/`. Keep all contributor credits.                                                                                                                                                                                                       |
| `info.md`                 | Update like the README, or replace with a shorter HACS-facing summary if the fork still uses it.                                                                                                                                                                                                                                                      |
| `docs/HA_ENTITIES.md`     | Rename title from MyDolphin Plus to Maytronics Robot and update any domain/logger/service examples.                                                                                                                                                                                                                                                   |
| `docs/MQTT_DEBOUNCING.md` | Rename integration text and update debug logger path to `custom_components.maytronics_robot...`.                                                                                                                                                                                                                                                      |
| `docs/WORKFLOWS.md`       | Rename title and references from MyDolphin Plus Integration to Maytronics Robot Integration.                                                                                                                                                                                                                                                          |

## Optional Internal Rebrand

These changes are not strictly required for Home Assistant to load the renamed
integration, but they make the fork cleaner and reduce future confusion.

| Current symbol or file                                                                                                | Suggested change                                                                   |
| --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `MyDolphinPlusCoordinator`                                                                                            | Rename to `MaytronicsRobotCoordinator`.                                            |
| `MyDolphinPlusBaseEntity`                                                                                             | Rename to `MaytronicsRobotBaseEntity`.                                             |
| `MyDolphinPlusEntityDescription` and related entity description classes                                               | Rename to `MaytronicsRobotEntityDescription` and matching platform-specific names. |
| Entity classes in `binary_sensor.py`, `sensor.py`, `select.py`, `number.py`, `light.py`, `remote.py`, and `vacuum.py` | Rename class prefixes from `MyDolphinPlus` to `MaytronicsRobot`.                   |
| `_FLOW_STATE_ATTR = "_mydolphin_state"`                                                                               | Consider renaming to `"_maytronics_robot_state"`.                                  |
| Tests referencing old class names                                                                                     | Update if class names are rebranded.                                               |

## Suggested First Changelog

```md
# Changelog

## v1.0.0

- Fork and rebrand the integration as Maytronics Robot.
- Support authentication for both MyDolphin Plus and Maytronics One mobile apps.
- Reset the integration version for the new forked project.
- Preserve credits for the original MyDolphin Plus integration maintainers and contributors.
```

## Suggested README Credits Section

```md
## Credits

Maytronics Robot is forked from the original MyDolphin Plus Home Assistant
custom integration.

Thanks to the original maintainers and contributors who built and improved the
integration:

- [Elad Bar](https://github.com/elad-bar)
- Dan Wheaton
- [sh00t2kill](https://github.com/sh00t2kill)
- [tigers75](https://github.com/tigers75)
- [Loïc](https://github.com/zoic21)
- Gil Peeters
- [devilismyfriend](https://github.com/devilismyfriend)
- [yumlevi](https://github.com/yumlevi)
- [grillp](https://github.com/grillp)
- [lordlala](https://github.com/lordlala)
```

## Search and Replace Guidance

Safe domain/package replacements:

- `custom_components.mydolphin_plus` -> `custom_components.maytronics_robot`
- `custom_components/mydolphin_plus` -> `custom_components/maytronics_robot`
- `DOMAIN = "mydolphin_plus"` -> `DOMAIN = "maytronics_robot"`
- `"domain": "mydolphin_plus"` -> `"domain": "maytronics_robot"`
- `.storage/mydolphin_plus.config.json` -> `.storage/maytronics_robot.config.json`
- `custom_components.mydolphin_plus` logger names -> `custom_components.maytronics_robot`

Do not blindly replace these app-specific values:

- `APP_ID_MYDOLPHIN_PLUS = "mydolphin_plus"`
- `APP_NAME_MYDOLPHIN_PLUS = "MyDolphin Plus"`
- `APP_KEYS[APP_ID_MYDOLPHIN_PLUS]`
- UI app option label `MyDolphin Plus`
- Any test that intentionally checks MyDolphin Plus as a mobile app option

## Migration Note

Changing the Home Assistant domain from `mydolphin_plus` to `maytronics_robot`
creates a new integration identity. Existing users will not automatically move
from the old integration to the new one unless a migration path is implemented
or documented.

For a clean fork, the simplest approach is to document this as a new integration
that users add manually. If preserving existing entries is important, plan a
separate migration strategy before release.

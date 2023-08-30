# Changelog

## v1.0.5

- Fix error while trying to parse AWS message

## v1.0.4

- Fix dynamic reporting into AWS Client data
- Fix reset data of robot type, is busy, turn on count and timezone reporting when message of pwsState doesn't contain data
- Reconnect when API returns 401 or 403 error code

## v1.0.3

- Improve AWS client connection recovery process (unsubscribe topics and disconnect before trying to connect again)
- Refactor password encryption flow
- Refactor integration loading (will be loaded only after HA is loaded, re-load will be performed immediately)
- Add to integration unload call to unsubscribe AWS client topics
- Integration setup
  - Add support for edit integration details
  - Add title to the form (Add / Edit), will set the integration name

## v1.0.2

- Breaking change: Renamed sensor of `Main Unit Status` to `Power Supply Status`
- Support for defining entities according to robot family (All, M600, M700)
- Add `Temperature` sensor for M700
- Add `Robot Error` and `Power Supply Error` sensors
  - Presents error only when related to latest cycle (if error is available in data and not related to latest, treat as no-error)
  - Fires event `mydolphin_plus_error`
- Add feature to translation tool to complete gaps of missing translations with default values surrounded by asterisks (\*)

## v1.0.1

- Breaking Change: Schedules removed (Sensors and services)
- Add clean mode number component to set cycle time (minutes) per clean mode, defaults:
  - Regular (all): 120
  - Fast mode (fast): 60
  - Floor only (floor): 120
  - Water line (water): 120
  - Ultra clean (ultra): 120
  - Pickup (pickup): 5
- Store clean mode cycle time in configuration file (per integration)
- Starting clean uses clean cycle time configuration
- Turn on / Start actions will start according to fan speed, default if not set: Regular (all)

## v1.0.0

- Fix actions (functionality, translations and attach to relevant services)
  - Turn off
  - Stop
  - Pickup (return to dock / home)
  - Set fan mode (change clean mode)
  - Navigate (integration service)
  - Stop navigation (integration service)
- Improve API test util
- Removed schedule delay / daily services (all functionality of robot available from integration, please use HA automation)

## v0.4.7

- Fix binary sensor loading
- Fix support for entities names
- Set default robot name when empty to "MyDolphin Plus"

## v0.4.6

- Italian translation by [@tigers75](https://github.com/tigers75)
- Asynchronous device loading

## v0.4.5

- Add support to translate names of all components
- Fix parameters for read temperature request

## v0.4.4

**Breaking Change**

This version changes the approach of extracting encryption key,
If the following error message available in log, please follow its instructions:

```log
ERROR (MainThread) [custom_components.mydolphin_plus.managers.config_manager] Invalid encryption key, Please follow instructions in https://github.com/sh00t2kill/dolphin-robot#invalid-token
```

**Changes:**

- Fix unknown error while setting up integration

## v0.4.3

- Jumping version

## v0.4.2

- Fix integration setup process

## v0.4.1

- Fix integration setup process

## v0.4.0

- Refactor code to support HA coordinator
- Improve reconnection when AWS Broker gets disconnected
- Remove integration options (Edit configuration)
- Improve diagnostic data
- New components
  - Sensor: Clean Mode
  - Sensor: Cycle Count
  - Sensor: Main Unit Status
  - Sensor: Robot Status
  - Sensor: Robot Type
  - Sensor: RSSI
  - Sensor: Network Name
  - Sensor: Status (Calculated Status)
  - Number: LED Intensity
- Support translation for
  - Vacuum: Fan Speed
  - Sensor: Filter Status
  - Sensor: Robot Status
  - Sensor: Main Unit Status
  - Sensor: Clean Mode
  - Sensor: Status
  - Select: LED Mode

## v0.3.4

- Fix error upon restart caused by attempt to handle message from AWS MQTT Broker during restart of HA
- Fix Cycle Time sensor to represent minutes of the current program
- Fix Cycle Time Left sensor to represent seconds left for the current program to be completed
- Remove debugging API
- Add diagnostics support (Settings -> Devices & Services -> MyDolphin Plus -> 3 dots menu -> Download diagnostics)
- Fix LED Mode select values

## v0.3.3

- Add AWS Broker disconnection recovery process
- Collect the Motor Unit Serial Number from API instead of try to calculate it

## v0.3.2

- Fix Filter Bag sensor
- Core fix: wrongfully reported logs of entities getting updated when no update perform
- Replaced `store debug data` switch and the feature of storing debug data to `/config/.storage` with debug API

**Endpoints**

| Endpoint Name                      | Method | Description                                                                                         |
| ---------------------------------- | ------ | --------------------------------------------------------------------------------------------------- |
| /api/mydolphin_plus/list           | GET    | List all the endpoints available (supporting multiple integrations), available once for integration |
| /api/mydolphin_plus/{ENTRY_ID}/api | GET    | JSON of all raw data from the MyDolphin Plus API, per integration                                   |
| /api/mydolphin_plus/{ENTRY_ID}/ws  | GET    | JSON of all raw data from the MyDolphin Plus WebSocket, per integration                             |

**Authentication: Requires long-living token from HA**

## v0.3.1

- Core alignment
- Constants cleanup
- Add retry mechanism for AWS token encryption process
- Fix get token API (API changed and new one requires encryption of data) [#76](https://github.com/sh00t2kill/dolphin-robot/issues/76)
- Add generate AWS token test file
- Store encrypted data within config file to avoid re-generating the file on every startup

## v0.3.0

- Fix deleting components when being removed, wrong parameter was sent to be deleted
- Update `core` to latest
- Separate API and WS to different classes
- Separate timers of update entities and data
- Update time remaining value

## v0.2.4

- IOT Class (`iot_class`) changed to `cloud_push`
- Removed time from cleaning mode select HA component (select, translations and services)
- Major refactor of HA Manager, Entity Manager and API (code cleanup)
- AWS IOT Broker works with asynchronous operations
- Publish all messages with QOS=1 (At least once)
- Add AWS Broker status binary sensor
- Override Time Left to 0 when robot is not cleaning
- Send explicit OFF command when toggling robot to off
- Vacuum state is being calculated from both states of head unit and the robot
- Add vacuum entity, replacing:
  - Cleaning mode select
  - Connection binary sensor
  - Power switch
  - All services
- Add locate to vacuum
- Major refactor to `Core`
  - all components are now part of the `Core`
  - Implementation should be done only in API, HA Manager and Configuration Manager
- Added `init` to vacuum state to show something is happening when a cycle is started
- Add {Robot Name} Store Debug Data switch - allows to set whether to store API and WebSocket the latest data for debugging
- Separate API / WS classes
- Separate timers for API / WS and Entities update

## v0.2.3

- Fix core issue while deleting entities

## v0.2.2

- Fix initialization order of API

## v0.2.1

- Fix cycle time left sensor - didn't take new vacuum states into account
- Fix storage API in case file doesn't exist
- Fix initialization order of API
- Removed unused files and code
- Core protect unsupported domains
- IOT Class (`iot_class`) changed to `cloud_push`

## v0.2.0

- Add vacuum start,stop,locate,pause service calls

  - `start` is equivalent to `turn_on` (ie start a cleaning cycle)
  - `stop` and `pause` are equivalent to `turn_off` (ie stop a cleaning cycle)
  - locate turns the LED on for 10 seconds and off again

- Major refactor to `Core`

  - all components are now part of the `Core`
  - Implementation should be done only in API, HA Manager and Configuration Manager

- Remapped vacuum status for each action - turn on, turn off, toggle, start, stop, pause

## v0.1.0

- Major refactor of HA Manager, Entity Manager and API (code cleanup)
- AWS IOT Broker works with asynchronous operations
- Publish all messages with QOS=1 (At least once)
- Add AWS Broker status binary sensor
- Override Time Left to 0 when robot is not cleaning
- Send explicit OFF command when toggling robot to off
- Vacuum state is being calculated from both states of head unit and the robot
- Add vacuum entity, replacing:
  - Cleaning mode select
  - Connection binary sensor
  - Power switch
  - All services

## v0.0.9

- Removed time from cleaning mode select HA component (select, translations and services)
- Moved the off_states of switch to constants

## v0.0.8

- Add a list of relevant states that also determine if a robot is not actively cleaning
- Added MyDolpin Plus to the standard HACS repo

## v0.0.7

- Cycle left time sensor: Add attribute of expected end time
- API: Add logs for server version, time and diff (compared to local time)
- API: change AWS connectivity request parameter of now, from UTC to local time
- API: Add connection validation on each step of the initialization process (for better debugging)

## v0.0.6

- Changed LED `switch` to `light` component

## v0.0.5

- Update the HA when `$aws/things/SERIAL/shadow/update/accepted` event received
- Fix `select` and `switch` state extraction
- Implement and test the following actions:
  - Power on / off
  - Led on / off
  - Lef mode
  - Cleaning mode

## v0.0.4

- HA is working with all components as READONLY (action not tested yet)

## v0.0.3

- Update todo in [README](README.md)
- Update `service.yaml`
- On load call topic `$aws/things/SERIAL/shadow/get` to load all details, this simulates loading the mobile app
- Add `get_accept.jsonc` file example file with all data being collected as part of `api.initialize` or `api.async_update` from MQTT
- Changed sensor `Connection Type` to binary_sensor of `Connection`
- Removed remote entity, instead exposed 2 additional services
  - `mydolphin_plus.drive` - Manually drive the robot
  - `mydolphin_plus.pickup` - Pickup
- Loading correct data for:
  - Binary Sensors: Status, Connection, Filter Bag Status, Delayed Schedule, Daily Schedule (Per day)
  - Select: Cleaning Mode, Led Mode
  - Sensor: Cleaning Time, Cleaning Time Left
  - Switch: Power, Led Enabled

## v0.0.2

- Create stub functions in MyDolphinPlusAPI and its proxy methods in MyDolphinPlusHomeAssistantManager
- Add HA components (More details in [README](README.md))
  - Binary Sensors: Status, Filter Bag Status, Delayed Schedule, Daily Schedule (Per day)
  - Remote
  - Select: Cleaning Mode, Led Mode
  - Sensor: Connection Type, Cleaning Time, Cleaning Time Left
  - Switch: Power, Led Enabled

## v0.0.1

Initial changes - functionality changes, refactor and restructuring of based code to match needs for HA custom component

Functionality:

- Add additional API call to retrieve robot details from `api/serialnumbers/getrobotdetailsbymusn`
- Subscribe to following MQTT topic to get all details from device
  - $aws/things/{}/shadow/get/#
  - $aws/things/{}/shadow/update/#
  - Maytronics/{}/main

Refactor / Restructure:

- Add boilerplate of HA custom component (based on Shinobi Video NVR)
- Add pre-commit
- Switch HTTP requests to async by changing all `requests` to `aiohttp`
- Cleanup string builders to more efficient approach
- Move constants to const file
- Move certificate `AmazonRootCA.pem` to API directory
- Use `logging` component for logging to console instead of `print`
- Update test file to call `MyDolphinPlusAPI` that will be used by HA
- Add testing environment variables

| Environment Variable | Type    | Default | Description                                                                                                               |
| -------------------- | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| TEST_USERNANE        | String  | -       | Username used for MyDolphin Plus                                                                                          |
| TEST_PASSWORD        | String  | -       | Password used for MyDolphin Plus                                                                                          |
| DEBUG                | Boolean | False   | Setting to True will present DEBUG log level message while testing the code, False will set the minimum log level to INFO |

TODO:

- Create sensors and binary sensors based on data retrieved from the MyDolphin Plus app and cloud
- Test the solution within HA
- Add custom component to HACS
- Update [README.md](README.md) (currently available in [info.md](info.md))

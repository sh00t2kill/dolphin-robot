# Changelog

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
|----------------------|---------|---------|---------------------------------------------------------------------------------------------------------------------------|
| TEST_USERNANE        | String  | -       | Username used for MyDolphin Plus                                                                                          |
| TEST_PASSWORD        | String  | -       | Password used for MyDolphin Plus                                                                                          |
| DEBUG                | Boolean | False   | Setting to True will present DEBUG log level message while testing the code, False will set the minimum log level to INFO |

TODO:
- Create sensors and binary sensors based on data retrieved from the MyDolphin Plus app and cloud
- Test the solution within HA
- Add custom component to HACS
- Update [README.md](README.md) (currently available in [info.md](info.md))

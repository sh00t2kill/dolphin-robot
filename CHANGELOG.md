# Changelog

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

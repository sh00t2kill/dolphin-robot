# Changelog

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

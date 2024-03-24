# MyDolphin Plus

## Description

Integration with MyDolphin Plus to monitor and control your robot

[Changelog](https://github.com/sh00t2kill/dolphin-robot/blob/master/CHANGELOG.md)

## How to

#### Requirements

- MyDolphin Plus robot with Always Connected support
- MyDolphin Plus App
- MyDolphin Plus account

#### Installations via HACS

- In HACS, look for "MyDolphin Plus" and install
- In Configuration --> Integrations - Add MyDolphin Plus

#### Integration settings

###### Basic configuration (Configuration -> Integrations -> Add MyDolphin Plus)

| Fields name | Type    | Required | Default | Description                                   |
| ----------- | ------- | -------- | ------- | --------------------------------------------- |
| Username    | Textbox | -        |         | Username of dashboard user for MyDolphin Plus |
| Password    | Textbox | -        |         | Password of dashboard user for MyDolphin Plus |

###### Configuration validations

Upon submitting the form of creating an integration or updating options,

Component will try to log in into the MyDolphin Plus to verify new settings, following errors can appear:

- Integration already configured with the same title
- Invalid server details - Cannot reach the server

###### Encryption key got corrupted

If a persistent notification popped up with the following message:

```
Encryption key got corrupted, please remove the integration and re-add it
```

It means that encryption key was modified from outside the code,
Please remove the integration and re-add it to make it work again.

#### Run as CLI

###### Requirements

- Python 3.10
- Python virtual environment
- Install all dependencies, using `pip install -r requirements.txt` command

###### Environment variables

| Environment Variable | Type    | Default | Description                                                                                                               |
| -------------------- | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| Username             | String  | -       | Username used for MyDolphin Plus                                                                                          |
| Password             | String  | -       | Password used for MyDolphin Plus                                                                                          |
| DEBUG                | Boolean | False   | Setting to True will present DEBUG log level message while testing the code, False will set the minimum log level to INFO |

## HA Components

| Entity Name                          | Type          | Description                                                                 | Additional information                                                                                                              |
| ------------------------------------ | ------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| {Robot Name} AWS Broker              | Binary Sensor | Indicates whether the component synchronized with cloud or not              |                                                                                                                                     |
| {Robot Name} Weekly Schedule         | Binary Sensor | Indicates whether the weekly scheduler is on or off                         |                                                                                                                                     |
| {Robot Name} LED                     | Light         | Turned on or off the led                                                    |                                                                                                                                     |
| {Robot Name} LED Intensity           | Number        | Sets the LED intensity values between 0-100                                 |                                                                                                                                     |
| {Robot Name} Cycle Time {Clean Mode} | Number        | Sets the cycle time of specific clean mode, values between 1 to 600 minutes |                                                                                                                                     |
| {Robot Name} LED Mode                | Select        | Select led mode                                                             | Blinking, Always on, Disco                                                                                                          |
| {Robot Name} Status                  | Sensor        | Presents the calculated status of the device                                |                                                                                                                                     |
| {Robot Name} RSSI                    | Sensor        | Presents the WIFI signal strength in DB                                     |                                                                                                                                     |
| {Robot Name} Network Name            | Sensor        | Presents the name of the network (WIFI SSID)                                |                                                                                                                                     |
| {Robot Name} Clean Mode              | Sensor        | Presents the current clean mode                                             |                                                                                                                                     |
| {Robot Name} Power Supply Status     | Sensor        | Presents the status of the power supply                                     |                                                                                                                                     |
| {Robot Name} Robot Status            | Sensor        | Presents the status of the robot                                            |                                                                                                                                     |
| {Robot Name} Robot Model             | Sensor        | Presents the type of the robot                                              |                                                                                                                                     |
| {Robot Name} Cycle Count             | Sensor        | Presents the number of cycles ran                                           |                                                                                                                                     |
| {Robot Name} Filter Status           | Sensor        | Presents the status of the filter bag                                       |                                                                                                                                     |
| {Robot Name} Cycle Time              | Sensor        | Indicates the time the robot is cleaning                                    | Measurement of duration in minutes                                                                                                  |
| {Robot Name} Cycle Time Left         | Sensor        | Indicates the time left for the robot to complete the cycle                 | Measurement of duration in seconds                                                                                                  |
| {Robot Name}                         | Vacuum        | Provides functionality of vacuum to the robot                               | Features: State, Fan Speed (Cleaning Mode), Return Home (Pickup), Turn On, Turn Off, Send Command (Navigate, Schedule, Delay Clean) |

### Cleaning Modes

| Key   | Name        | Description                                  | Duration (Hours) |
| ----- | ----------- | -------------------------------------------- | ---------------- |
| all   | Regular     | cleans floor, water and waterline            | 2                |
| short | Fast mode   | cleans the floor                             | 1                |
| floor | Floor only  | Cleans the floor only                        | 2                |
| water | Water line  | cleans the walls and water line              | 2                |
| ultra | Ultra clean | deeply cleans the floor, walls and waterline | 2                |

### Led Modes

| Key | Name      |
| --- | --------- |
| 1   | Blinking  |
| 2   | Always on |
| 3   | Disco     |

## Services

### Navigate

Description: Manually navigate the robot

Payload:

```yaml
service: mydolphin_plus.navigate
target:
  entity_id: vacuum.{Robot Name}
data:
  direction: stop / forward / backward / left / right
```

### Exit Navigation

Description: Exit manual navigation mode

Payload:

```yaml
service: mydolphin_plus.exit_navigation
target:
  entity_id: vacuum.{Robot Name}
```

## Events

### mydolphin_plus_error

Description: Notifies about robot or power supply error

```json
{
  "name": "{Robot | Power Supply} Error",
  "Robot Name": "{Robot Name}",
  "state": 1,
  "Description": "details",
  "Instructions": "when relevant"
}
```

#### Available errors

| Error Code | Description                                  | Instructions                                                                                                                                                                                                                                                                                                                     |
| ---------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0          | Ok                                           |                                                                                                                                                                                                                                                                                                                                  |
| 1          | DC in voltage                                |                                                                                                                                                                                                                                                                                                                                  |
| 2          | Out of water                                 |                                                                                                                                                                                                                                                                                                                                  |
| 3          | Impeller overload problem has been detected. | Please follow these steps:<br />1. Unplug the power supply.<br />2. Clean the debris from the impeller opening.<br />3. Dismantle the impeller compartment if the debris is inaccessible.<br />4. Re-assemble the robot, plug in the power supply, and try to operate again.\n5. If the above doesn’t help, contact your dealer. |
| 4          | Impeller 1 underload                         |                                                                                                                                                                                                                                                                                                                                  |
| 5          | Impeller overload problem has been detected. | Please follow these steps:<br />1. Unplug the power supply.<br />2. Clean the debris from the impeller opening.<br />3. Dismantle the impeller compartment if the debris is inaccessible.<br />4. Re-assemble the robot, plug in the power supply, and try to operate again.\n5. If the above doesn’t help, contact your dealer. |
| 6          | Impeller 2 underload                         |                                                                                                                                                                                                                                                                                                                                  |
| 7          | Drive overload problem has been detected     | Please follow these steps:<br />1. Unplug the power supply.<br />2. Remove any object or blockage from the driving system.<br />3. Plug in the power supply and try to operate again.<br />4. If the above doesn’t help, please contact your dealer                                                                              |
| 8          | Drive 1 underload                            |                                                                                                                                                                                                                                                                                                                                  |
| 9          | Drive overload problem has been detected     | Please follow these steps:<br />1. Unplug the power supply.<br />2. Remove any object or blockage from the driving system.<br /> 3. Plug in the power supply and try to operate again.<br />4. If the above doesn’t help, please contact your dealer                                                                             |
| 10         | Drive 2 underload                            |                                                                                                                                                                                                                                                                                                                                  |
| 11         | Wall/floor sensor                            |                                                                                                                                                                                                                                                                                                                                  |
| 12         | DC in voltage 23V                            |                                                                                                                                                                                                                                                                                                                                  |
| 13         | Wall floor sensor 2                          |                                                                                                                                                                                                                                                                                                                                  |
| 14         | Robot stuck                                  |                                                                                                                                                                                                                                                                                                                                  |
| 15         | Power supply overheat                        |                                                                                                                                                                                                                                                                                                                                  |
| 16         | Power supply overload                        |                                                                                                                                                                                                                                                                                                                                  |
| 17         | Impeller 1 Driver failure                    |                                                                                                                                                                                                                                                                                                                                  |
| 18         | Impeller 2 Driver failure                    |                                                                                                                                                                                                                                                                                                                                  |
| 19         | Drive 1 Driver failure                       |                                                                                                                                                                                                                                                                                                                                  |
| 20         | Drive 2 Driver failure                       |                                                                                                                                                                                                                                                                                                                                  |
| 21         | Servo over load                              |                                                                                                                                                                                                                                                                                                                                  |
| 22         | Impeller 1 Motor failure                     |                                                                                                                                                                                                                                                                                                                                  |
| 23         | Impeller 2 Motor failure                     |                                                                                                                                                                                                                                                                                                                                  |
| 24         | Drive 1 Motor failure"                       |                                                                                                                                                                                                                                                                                                                                  |
| 25         | Drive 2 Motor failure"                       |                                                                                                                                                                                                                                                                                                                                  |
| 255        | Ok                                           |                                                                                                                                                                                                                                                                                                                                  |

## Troubleshooting

Before opening an issue, please provide logs related to the issue,
For debug log level, please add the following to your config.yaml

```yaml
logger:
  default: warning
  logs:
    custom_components.mydolphin_plus: debug
```

Please attach also diagnostic details of the integration, available in:
<br />Settings -> Devices & Services -> MyDolphin Plus -> 3 dots menu -> Download diagnostics
<br />See this link for further information:
<br />https://www.home-assistant.io/docs/configuration/troubleshooting/

### Invalid Token

In case you have referenced to that section, something went wrong with the encryption key,
Encryption key should be located in `.storage/mydolphin_plus.config.json` file under `data.key` property,
below are the steps to solve that issue.

#### File not exists or File exists, data.key is not

Please report as issue

#### File exists, data.key is available

Example:

```json
{
  "version": 1,
  "minor_version": 1,
  "key": "mydolphin_plus.config.json",
  "data": {
    "key": "ox-qQsAiHb67Kz3ypxY19uU2_YwVcSjvdbaBVHZJQFY=",
    "b8fa11c50331d2647b8aa7e37935efeb": {
      "locating": false,
      "aws-token-encrypted-key": "AWS_TOKEN"
    }
  }
}
```

OR

```json
{
  "version": 1,
  "minor_version": 1,
  "key": "mydolphin_plus.config.json",
  "data": {
    "key": "ox-qQsAiHb67Kz3ypxY19uU2_YwVcSjvdbaBVHZJQFY="
  }
}
```

1. Remove the integration
2. Delete the file
3. Restart HA
4. Try to re-add the integration
5. If still happens - report as issue

#### File exists, key is available under one of the entry configurations

Example:

```json
{
  "version": 1,
  "minor_version": 1,
  "key": "mydolphin_plus.config.json",
  "data": {
    "b8fa11c50331d2647b8aa7e37935efeb": {
      "key": "ox-qQsAiHb67Kz3ypxY19uU2_YwVcSjvdbaBVHZJQFY=",
      "locating": false,
      "aws-token-encrypted-key": "AWS_TOKEN"
    }
  }
}
```

1. Move the `key` to the root of the JSON
2. Restart HA
3. Try to re-add the integration
4. If still happens - follow instructions of section #1 (_i._)

## Lovelace cards.

We have confirmed the robot works with the custom vacuum card, built by denysdovhan
https://github.com/denysdovhan/vacuum-card

Copy the icons from www on the repository to /config/www. Below is a suggested configuration for the card

```yaml
type: tile
entity: vacuum.robot_name
show_entity_picture: true
features:
  - type: vacuum-commands
    commands:
      - start_pause
      - stop
      - locate
      - return_home
```

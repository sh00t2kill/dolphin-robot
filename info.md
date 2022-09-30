# MyDolphin Plus

## Description

Integration with MyDolphin Plus. Creates the following components:

[Changelog](https://github.com/sh00t2kill/dolphin-robot/blob/master/CHANGELOG.md)

## Status: WIP

Integration is still work in progress, not tested with HA with all its functionality,
to test you can run the CLI mode or within the HA.

### TODO
- ~~On startup trigger the get topic from MQTT as happens when the mobile app is being opened~~
- ~~Implement publish commands to the robot (currently stubs that logs the action only)~~
- ~~Map the select values to the real one from the app (currently available assumed values)~~
- ~~Align consts to the real values of select~~
- ~~Map remote commands~~
- ~~Create services~~
- Test ~~, test and more test~~ actions

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
|-------------|---------|----------|---------|-----------------------------------------------|
| Username    | Textbox | -        |         | Username of dashboard user for MyDolphin Plus |
| Password    | Textbox | -        |         | Password of dashboard user for MyDolphin Plus |

###### Integration options (Configuration -> Integrations -> MyDolphin Plus Integration -> Options)
| Fields name | Type    | Required | Default              | Description                                   |
|-------------|---------|----------|----------------------|-----------------------------------------------|
| Username    | Textbox | -        | Last stored username | Username of dashboard user for MyDolphin Plus |
| Password    | Textbox | -        | Last stored password | Password of dashboard user for MyDolphin Plus |

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
|----------------------|---------|---------|---------------------------------------------------------------------------------------------------------------------------|
| TEST_USERNANE        | String  | -       | Username used for MyDolphin Plus                                                                                          |
| TEST_PASSWORD        | String  | -       | Password used for MyDolphin Plus                                                                                          |
| DEBUG                | Boolean | False   | Setting to True will present DEBUG log level message while testing the code, False will set the minimum log level to INFO |

## HA Components
| Entity Name                      | Type           | Description                                                    | Additional information                                                                                                              |
|----------------------------------|----------------|----------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| {Robot Name} AWS Broker          | Binary Sensors | Indicates whether the component synchronized with cloud or not |                                                                                                                                     |
| {Robot Name} Schedule Delay      | Binary Sensors | Indicates whether the delay cleaning is enabled or not         |                                                                                                                                     |
| {Robot Name} Schedule {Day Name} | Binary Sensors | Indicates whether the schedule cleaning is enabled or not      |                                                                                                                                     |
| {Robot Name} Weekly Schedule     | Binary Sensor  | Indicates whether the weekly scheduler is on or off            |                                                                                                                                     |
| {Robot Name}                     | Light          | Turned on or off the led                                       |                                                                                                                                     |
| {Robot Name} Led Mode            | Select         | Select led mode                                                | Blinking, Always on, Disco                                                                                                          |
| {Robot Name} Filter              | Sensors        | Presents the status of the filter bag                          |                                                                                                                                     |
| {Robot Name} Cycle Time          | Sensor         | Indicates the time the robot is cleaning                       |                                                                                                                                     |
| {Robot Name} Cycle Time Left     | Sensor         | Indicates the time left for the robot to complete the cycle    |                                                                                                                                     |
| {Robot Name}                     | Vacuum         | Provides functionality of vacuum to the robot                  | Features: State, Fan Speed (Cleaning Mode), Return Home (Pickup), Turn On, Turn Off, Send Command (Navigate, Schedule, Delay Clean) |

### Cleaning Modes

| Key   | Name        | Description                                  | Duration (Hours) |
|-------|-------------|----------------------------------------------|------------------|
| all   | Regular     | cleans floor, water and waterline            | 2                |
| short | Fast mode   | cleans the floor                             | 1                |
| floor | Floor only  | Cleans the floor only                        | 2                |
| water | Water line  | cleans the walls and water line              | 2                |
| ultra | Ultra clean | deeply cleans the floor, walls and waterline | 2                |


### Led Modes

| Key | Name      |
|-----|-----------|
| 1   | Blinking  |
| 2   | Always on |
| 3   | Disco     |

## Services
### Navigate

Description: Manually navigate the robot

Payload:
```yaml
service: vacuum.send_command
target:
  entity_id: vacuum.{Robot Name}
data:
  command: navigate
  params:
    direction: stop / forward / backward / left / right
```

### Set Daily Schedule

Description: Set the schedule for a specific day

Payload:
```yaml
service: vacuum.send_command
target:
  entity_id: vacuum.{Robot Name}
data:
    command: daily_schedule
    params:
      day: Sunday
      enabled: true
      time: 00:00
      mode: all
```

### Delayed Cleaning

Description: Set a delayed job for cleaning

Payload:
```yaml
service: vacuum.send_command
target:
  entity_id: vacuum.{Robot Name}
data:
    command: delayed_clean
    params:
      enabled: true
      time: 00:00
      mode: all
```

## Troubleshooting

Before opening an issue, please provide logs related to the issue,
For debug log level, please add the following to your config.yaml
```yaml
logger:
  default: warning
  logs:
    custom_components.mydolphin_plus: debug
```

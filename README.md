# MyDolphin Plus

## Description

Integration with MyDolphin Plus. Creates the following components:

[Changelog](https://github.com/sh00t2kill/dolphin-robot/blob/master/CHANGELOG.md)

## Status: WIP

Integration is still work in progress, not tested with HA with all its functionality,
to test you can run the CLI mode or within the HA.

### TODO
- On startup trigger the get topic from MQTT as happens when the mobile app is being opened
- Implement publish commands to the robot (currently stubs that logs the action only)
- Map the select values to the real one from the app (currently available assumed values)
- Align consts to the real values of select
- Map remote commands
- Create services
- Test, test and more test

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
| Entity Name                      | Type           | Description                                                   | Additional information                                              |
|----------------------------------|----------------|---------------------------------------------------------------|---------------------------------------------------------------------|
| {Robot Name} Status              | Binary Sensors | Indicates whether the robot is turned on or off               |                                                                     |
| {Robot Name} Filter Bag Status   | Binary Sensors | Indicates whether the robot filter bag is full or not         |                                                                     |
| {Robot Name} Schedule Delay      | Binary Sensors | Indicates whether the delay cleaning is enabled or not        | Attributes will hold the mode and delayed time                      |
| {Robot Name} Schedule {Day Name} | Binary Sensors | Indicates whether the schedule cleaning is enabled or not     | Attributes will hold the mode and delayed time                      |
| {Robot Name} Status              | Remote         | Indicates whether the robot is turned on or off               | Allows the following actions:                                       |
|                                  |                |                                                               | - Go backward                                                       |
|                                  |                |                                                               | - Go backward                                                       |
|                                  |                |                                                               | - Go left                                                           |
|                                  |                |                                                               | - Go right                                                          |
|                                  |                |                                                               | - Pick up                                                           |
| {Robot Name} Cleaning Mode       | Select         | Select cleaning mode                                          | Available options                                                   |
|                                  |                |                                                               | **Regular** - cleans floor, water and waterline (2h)                |
|                                  |                |                                                               | **Fast mode** - cleans the floor (1h)                               |  Floor only - cleans the floor only (2h)                     |
|                                  |                |                                                               | **Floor only** - Cleans the floor only (2h)                         |
|                                  |                |                                                               | **Water line** - cleans the walls and water line (2h)               |
|                                  |                |                                                               | **Ultra clean** - deeply cleans the floor, walls and waterline (2h) |
| {Robot Name} Led Mode            | Select         | Select led mode                                               | Available options                                                   |
|                                  |                |                                                               | **Blinking**                                                        |
|                                  |                |                                                               | **Always on**                                                       |
|                                  |                |                                                               | **Disco**                                                           |
| {Robot Name} Connection Type     | Sensor         | Defines which connection is currently available for the robot |                                                                     |
| {Robot Name} Cleaning Time       | Sensor         | Indicates the time the robot is cleaning                      |                                                                     |
| {Robot Name} Cleaning Time Left  | Sensor         | Indicates the time left for the robot to complete the cycle   |                                                                     |
| {Robot Name} Power               | Switch         | Turned on or off the robot                                    |                                                                     |
| {Robot Name} Led Enabled         | Switch         | Turned on or off the led                                      |                                                                     |

## Services (Not implemented yet)

### Set Daily Schedule

Service name: *mydolphin_plus.set_daily_schedule*

Description: Set the schedule for a specific day

Payload:
```yaml
data:
  day: Sunday
  isEnabled: true
  time:
    hours: 255
    minutes: 255
  cleaningMode:
    mode: all
```


### Delayed Cleaning

Service name: *mydolphin_plus.delayed_cleaning*

Description: Set a delayed job for cleaning

Payload:
```yaml
data:
  isEnabled: true
  time:
    hours: 255
    minutes: 255
  cleaningMode:
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

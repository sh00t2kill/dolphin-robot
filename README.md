# MyDolphin Plus

## Description

Integration with MyDolphin Plus to monitor and control your robot

[Changelog](https://github.com/sh00t2kill/dolphin-robot/blob/master/CHANGELOG.md)

## Authentication

Authentication uses the same email-OTP flow as the official MyDolphin Plus mobile app:

1. Enter your account email when adding the integration.
2. Maytronics emails a one-time login code.
3. Enter the code in Home Assistant — the integration exchanges it for a refresh token and connects to the robot.

The refresh token is reused on every Home Assistant restart and silently renewed (~hourly), so you should only need to re-enter an OTP if the refresh token expires (Cognito default ~30 days) or you remove and re-add the integration.

> **Upgrading from a pre-OTP version (≤ 1.0.25b5):** the legacy email/password login endpoint has been retired by Maytronics. After updating, Home Assistant should prompt you to **Reconfigure / Reauthenticate** the existing entry so you can complete OTP login without reinstalling.

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

| Field      | Type    | Required | Description                                                                           |
| ---------- | ------- | -------- | ------------------------------------------------------------------------------------- |
| Title      | Textbox | yes      | Display name for the integration entry                                                |
| Email      | Textbox | yes      | Email of your MyDolphin Plus account — Maytronics emails a login code to this address |
| Login code | Textbox | yes      | The one-time code from the email, entered on the second step of the config flow       |

###### Configuration validations

Upon submitting the form, the integration verifies the credentials by:

1. Triggering Cognito `CUSTOM_AUTH` (sends the OTP email).
2. Exchanging the submitted OTP for an `IdToken` + `RefreshToken`.
3. Calling `apps.maytronics.com/mobapi/user/authenticate-user/` to confirm the account has a paired robot.

The following errors can appear:

- **Invalid account** — the email is empty or rejected by Cognito (no such user)
- **Failed to send login code, check the email and try again** — Cognito refused to send an OTP (rate limit or unknown user)
- **Invalid or expired login code** — the OTP is wrong, expired, or was used already
- **Invalid server details** — could not reach Cognito or `apps.maytronics.com`
- **Integration already configured with the name** — an entry with that title already exists

#### Run as CLI

###### Requirements

- Python 3.10
- Python virtual environment
- Install all dependencies, using `pip install -r requirements.txt` command

###### Environment variables

| Environment Variable | Type    | Default | Description                                                                                                               |
| -------------------- | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| Username             | String  | -       | Email of your MyDolphin Plus account (used to trigger Cognito OTP)                                                        |
| DEBUG                | Boolean | False   | Setting to True will present DEBUG log level message while testing the code, False will set the minimum log level to INFO |

> CLI use requires interactively entering an OTP from the email Maytronics sends — the legacy username/password login is no longer accepted.

## HA Components

| Entity Name                          | Type          | Description                                                                 | Additional information                                                                                                    |
| ------------------------------------ | ------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| {Robot Name} AWS Broker              | Binary Sensor | Indicates whether the component synchronized with cloud or not              |                                                                                                                           |
| {Robot Name} Weekly Schedule         | Binary Sensor | Indicates whether the weekly scheduler is on or off                         |                                                                                                                           |
| {Robot Name} LED                     | Light         | Turned on or off the led                                                    |                                                                                                                           |
| {Robot Name} LED Intensity           | Number        | Sets the LED intensity values between 0-100                                 |                                                                                                                           |
| {Robot Name} Cycle Time {Clean Mode} | Number        | Sets the cycle time of specific clean mode, values between 1 to 600 minutes |                                                                                                                           |
| {Robot Name} LED Mode                | Select        | Select led mode                                                             | Blinking, Always on, Disco                                                                                                |
| {Robot Name} Status                  | Sensor        | Presents the calculated status of the device                                |                                                                                                                           |
| {Robot Name} RSSI                    | Sensor        | Presents the WIFI signal strength in DB                                     |                                                                                                                           |
| {Robot Name} Network Name            | Sensor        | Presents the name of the network (WIFI SSID)                                |                                                                                                                           |
| {Robot Name} Clean Mode              | Sensor        | Presents the current clean mode                                             |                                                                                                                           |
| {Robot Name} Power Supply Status     | Sensor        | Presents the status of the power supply                                     |                                                                                                                           |
| {Robot Name} Robot Status            | Sensor        | Presents the status of the robot                                            |                                                                                                                           |
| {Robot Name} Robot Model             | Sensor        | Presents the type of the robot                                              |                                                                                                                           |
| {Robot Name} Cycle Count             | Sensor        | Presents the number of cycles ran                                           |                                                                                                                           |
| {Robot Name} Filter Status           | Sensor        | Presents the status of the filter bag                                       |                                                                                                                           |
| {Robot Name} Cycle Time              | Sensor        | Indicates the time the robot is cleaning                                    | Measurement of duration in minutes                                                                                        |
| {Robot Name} Cycle Time Left         | Sensor        | Indicates the time left for the robot to complete the cycle                 | Measurement of duration in seconds                                                                                        |
| {Robot Name} Remote                  | Remote        | Provides virtual joystick control for manual robot navigation               | Features: Activity (Stop, Forward, Backward, Left, Right), Turn On, Turn Off                                              |
| {Robot Name}                         | Vacuum        | Provides functionality of vacuum to the robot                               | Features: State, Fan Speed (Cleaning Mode), Return Home (Pickup), Turn On, Turn Off, Send Command (Schedule, Delay Clean) |

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

### Remote Control

The Remote entity provides virtual joystick control for manual robot navigation. Use the Remote entity's activity feature to control the robot:

**Available Activities:**

- `stop` - Stop robot movement
- `forward` - Move robot forward
- `backward` - Move robot backward
- `left` - Turn robot left
- `right` - Turn robot right

**Usage:**

- Turn on the Remote entity to start manual control mode
- Use the activity selector to choose movement direction
- Turn off the Remote entity to exit manual control mode

**Example:**

```yaml
# Start remote control with forward movement
service: remote.turn_on
target:
  entity_id: remote.{Robot Name}_remote
data:
  activity: forward

# Stop robot and exit remote control
service: remote.turn_off
target:
  entity_id: remote.{Robot Name}_remote
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

### Refresh token expired

If the integration logs `EXPIRED_TOKEN` and stops loading, the stored Cognito `RefreshToken` is no longer valid (it has expired or been invalidated server-side). Home Assistant should raise a reauthentication prompt for the existing entry so you can complete the OTP flow again.

If reauthentication does not appear or cannot be completed, remove and re-add the integration as a fallback.

The token state lives in `.storage/mydolphin_plus.config.json`, keyed by the entry id:

```json
{
  "version": 1,
  "minor_version": 1,
  "key": "mydolphin_plus.config.json",
  "data": {
    "b8fa11c50331d2647b8aa7e37935efeb": {
      "id-token": "...",
      "refresh-token": "...",
      "id-token-expires-at": 1746799200.0,
      "serial-number": "...",
      "motor-unit-serial": "..."
    }
  }
}
```

You generally do not need to edit this file by hand — re-running the config flow rewrites it.

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

### OTP login troubleshooting

If you cannot complete the OTP flow:

- **No email arrives** — check spam, then retry. If repeated retries fail, Cognito may be rate-limiting; wait a few minutes.
- **"Invalid or expired login code"** — codes are short-lived. Restart the config flow to receive a fresh one.
- **"Failed to send login code"** — usually means Cognito does not recognise the email. Confirm you can sign in to the official MyDolphin Plus app with the same address; if not, register the account in the app first.
- **Repeated failures with a known-good email** — collect debug logs (see [Troubleshooting](#troubleshooting)) and open an issue.

## Contributors

Thanks to everyone who has contributed to this project:

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

See [Contributing](CONTRIBUTING.md) for contribution guidelines.

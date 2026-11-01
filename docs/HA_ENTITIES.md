# MyDolphin Plus - Home Assistant Entities

This document provides a comprehensive list of all entities created by the MyDolphin Plus integration in Home Assistant, along with their functionality and usage.

## Overview

The MyDolphin Plus integration creates **25 entities** (24 for standard models, 25 for M700 models with temperature sensor) across 7 different platforms. All entities are automatically discovered and created when you add the integration to Home Assistant.

### Devices

The integration creates two devices:

- **{Robot Name} Power Supply** holds the Wi-Fi and cloud connection. It shows the power supply firmware, and has the Power Supply Status, Power Supply Error, RSSI, Network Name and AWS Broker entities.
- **{Robot Name}** is the robot, connected through the power supply. It shows the product name (for example DOLPHIN PREMIUM 2000 AU) as its model, the part number as its model ID, the robot firmware, the robot type (for example S4) as its hardware, and the serial number. It has every other entity.

The product name loads from the Maytronics API at startup; the versions appear once the robot first reports its state.

---

## 🤖 Vacuum Entity (1)

| Entity                                     | Type     | Functionality                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**{Robot Name}**](#vacuum-entity-details) | `vacuum` | Main vacuum control entity with the following features:<br/>• **Start** - Begin cleaning cycle<br/>• **Pause** - Pause current cleaning<br/>• **Return to Base** - Pickup/dock the robot<br/>• **Set Fan Speed** - Select cleaning mode (all, short, floor, water, ultra, pickup)<br/>• **Locate** - Turn on LED to find the robot<br/>• Shows current state: docked, cleaning, paused, error |

---

## 🎮 Remote Control Entity (1)

| Entity                                       | Type     | Functionality                                                                                                                                                                                                                                                                       |
| -------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**Remote**](#remote-control-entity-details) | `remote` | Manual joystick control for the robot:<br/>• **Send Command** - Control direction (forward, backward, left, right, stop)<br/>• **Turn Off** - Exit manual control mode<br/>• **Activity** - Shows current manual control direction<br/>• Allows manual navigation of the pool robot |

---

## 💡 Light Entity (1)

| Entity                           | Type    | Functionality                                                                                                                                         |
| -------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**LED**](#light-entity-details) | `light` | Control the robot's LED light:<br/>• **Turn On/Off** - Enable/disable LED<br/>• Used for locating the robot in the pool<br/>• Category: Configuration |

---

## 🎚️ Select Entity (1)

| Entity                                 | Type     | Functionality                                                                                                                                  |
| -------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [**LED Mode**](#select-entity-details) | `select` | Select LED blinking pattern:<br/>• Various LED modes available (blinking patterns)<br/>• Customizes LED behavior<br/>• Category: Configuration |

---

## 🔢 Number Entities (2)

| Entity                              | Type     | Range     | Functionality                                                                                       |
| ----------------------------------- | -------- | --------- | --------------------------------------------------------------------------------------------------- |
| [**LED Intensity**](#led-intensity) | `number` | 0-100     | Adjust LED brightness level (0-100%)<br/>• Category: Configuration<br/>• Device Class: Power Factor |
| [**Cycle Time**](#cycle-time)       | `number` | 1-600 min | Length of the current clean<br/>• Change it while the robot cleans to set a new time                |

---

## 📊 Sensor Entities (12)

### Status & Diagnostic Sensors

| Entity                                          | Type     | Functionality                                                                                                               |
| ----------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------- |
| [**Status**](#status)                           | `sensor` | Shows calculated overall system state<br/>• Includes attributes with detailed status information<br/>• Category: Diagnostic |
| [**RSSI**](#wifi-signal-strength-rssi)          | `sensor` | WiFi signal strength in dBm<br/>• Device Class: Signal Strength<br/>• Category: Diagnostic                                  |
| [**Network Name**](#network-name)               | `sensor` | WiFi network the robot is connected to<br/>• Category: Diagnostic                                                           |
| [**Clean Mode**](#clean-mode)                   | `sensor` | Current active cleaning mode (all/short/floor/water/ultra/pickup)<br/>• Category: Diagnostic                                |
| [**Power Supply Status**](#power-supply-status) | `sensor` | Power unit state (charging, floating, etc.)<br/>• Category: Diagnostic                                                      |
| [**Robot Status**](#robot-status)               | `sensor` | Robot's current operational status<br/>• Category: Diagnostic                                                               |
| [**Robot Type**](#robot-type)                   | `sensor` | Model type of the robot<br/>• Category: Diagnostic                                                                          |
| [**Cycle Count**](#cycle-count)                 | `sensor` | Total number of cleaning cycles completed<br/>• State Class: Total Increasing<br/>• Category: Diagnostic                    |

### Cleaning Cycle Sensors

| Entity                                  | Type     | Unit  | Functionality                                                                                                                    |
| --------------------------------------- | -------- | ----- | -------------------------------------------------------------------------------------------------------------------------------- |
| [**Cycle Time Left**](#cycle-time-left) | `sensor` | Hours | Remaining time in current cleaning cycle<br/>• Shows start time and expected end time in attributes<br/>• Device Class: Duration |

### Filter & Maintenance Sensors

| Entity                              | Type     | Functionality                                                                                                                                                   |
| ----------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**Filter Status**](#filter-status) | `sensor` | Filter bag status (OK, Warning, Critical)<br/>• Shows numeric filter state value<br/>• Includes reset_fbi flag in attributes<br/>• Dynamic icon based on status |

### Error Sensors

| Entity                          | Type     | Functionality                                                                                           |
| ------------------------------- | -------- | ------------------------------------------------------------------------------------------------------- |
| [**Robot Error**](#robot-error) | `sensor` | Robot error code (0 = no error)<br/>• Icon changes when error present<br/>• Category: Diagnostic        |
| [**PWS Error**](#pws-error)     | `sensor` | Power Supply error code (0 = no error)<br/>• Icon changes when error present<br/>• Category: Diagnostic |

### Battery & Environment Sensors

| Entity                                           | Type     | Unit | Functionality                                                                                                                                |
| ------------------------------------------------ | -------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [**Battery**](#battery)                          | `sensor` | %    | Battery level (always 100% for corded robots)<br/>• Device Class: Battery<br/>• State Class: Measurement                                     |
| [**Temperature**](#temperature-m700-models-only) | `sensor` | °C   | Water temperature (M700 models only)<br/>• Device Class: Temperature<br/>• State Class: Measurement<br/>• Only appears on M700 family robots |

---

## 🔌 Binary Sensor Entity (1)

| Entity                                     | Type            | Functionality                                                                                                                                                                                          |
| ------------------------------------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [**AWS Broker**](#aws-broker-connectivity) | `binary_sensor` | AWS IoT MQTT connection status:<br/>• **On** - Connected to AWS IoT<br/>• **Off** - Disconnected<br/>• Shows detailed status in attributes<br/>• Device Class: Connectivity<br/>• Category: Diagnostic |

---

## Summary by Platform

| Platform          | Count  | Purpose                                         |
| ----------------- | ------ | ----------------------------------------------- |
| **Vacuum**        | 1      | Main robot control                              |
| **Remote**        | 1      | Manual joystick control                         |
| **Light**         | 1      | LED control                                     |
| **Select**        | 1      | LED mode selection                              |
| **Number**        | 2      | LED intensity and cycle time                    |
| **Sensor**        | 12     | Status, diagnostics, cleaning info, errors      |
| **Binary Sensor** | 1      | AWS connectivity status                         |
| **TOTAL**         | **19** | (18 for non-M700, 19 for M700 with temperature) |

---

## Entity Categories

- **Main Control**: Vacuum, Remote, Cycle Time
- **Configuration** (EntityCategory.CONFIG): LED, LED Mode, LED Intensity (3 entities)
- **Diagnostic** (EntityCategory.DIAGNOSTIC): Status, RSSI, Network Name, Clean Mode, Power Supply Status, Robot Status, Robot Type, Cycle Count, AWS Broker, Robot Error, PWS Error (11 entities)
- **Measurement**: Filter Status, Cycle Time Left, Battery, Temperature (4 entities)

---

# Detailed Entity Information

---

## Vacuum Entity Details

### Main Vacuum Control

| Attribute        | Value                                               |
| ---------------- | --------------------------------------------------- |
| **Entity ID**    | `vacuum.{robot_name}`                               |
| **Platform**     | Vacuum                                              |
| **Device Class** | -                                                   |
| **Features**     | Start, Pause, Return to Base, Locate, Set Fan Speed |

#### Functionality

The main vacuum entity provides comprehensive control over the pool cleaning robot:

- **Start Cleaning** (`vacuum.start`) - Begin a cleaning cycle using the current cleaning mode
- **Pause Cleaning** (`vacuum.pause`) - Pause the current cleaning cycle
- **Return to Base** (`vacuum.return_to_base`) - Command the robot to return to dock/pickup
- **Locate** (`vacuum.locate`) - Turn on LED to help find the robot in the pool
- **Set Fan Speed** (`vacuum.set_fan_speed`) - Select cleaning mode:
  - `all` - Regular cleaning (default)
  - `short` - Fast mode
  - `floor` - Floor only
  - `water` - Water line only
  - `ultra` - Ultra clean
  - `pickup` - Quick pickup

#### States

- `docked` - Robot is in power supply/at dock
- `cleaning` - Currently cleaning the pool
- `paused` - Cleaning cycle paused
- `error` - Robot has encountered an error
- `unavailable` - Connection lost

#### Attributes

- `status` - Detailed status information
- `mode` - Current cleaning mode
- Additional diagnostic attributes

---

## Remote Control Entity Details

### Manual Joystick Control

| Attribute        | Value                        |
| ---------------- | ---------------------------- |
| **Entity ID**    | `remote.{robot_name}_remote` |
| **Platform**     | Remote                       |
| **Device Class** | -                            |
| **Features**     | Activity                     |

#### Functionality

Provides manual directional control of the robot using joystick commands:

- **Send Command** (`remote.send_command`) - Control robot direction:
  - `forward` - Move forward
  - `backward` - Move backward
  - `left` - Turn left
  - `right` - Turn right
  - `stop` - Stop movement
- **Turn Off** (`remote.turn_off`) - Exit manual control mode

#### States

- `on` - Manual control mode active
- `off` - Manual control mode inactive

#### Attributes

- `activity` - Current direction command (forward/backward/left/right/stop)

#### Notes

- Manual control is only available when the robot is active and in the water
- Speed is automatically set to 100 for all directional commands
- The robot must be in manual mode before sending directional commands

---

## Light Entity Details

### LED Light Control

| Attribute           | Value                    |
| ------------------- | ------------------------ |
| **Entity ID**       | `light.{robot_name}_led` |
| **Platform**        | Light                    |
| **Device Class**    | -                        |
| **Entity Category** | Configuration            |

#### Functionality

Controls the robot's built-in LED light:

- **Turn On** (`light.turn_on`) - Enable LED
- **Turn Off** (`light.turn_off`) - Disable LED

#### States

- `on` - LED is enabled
- `off` - LED is disabled

#### Usage

The LED is primarily used for:

- Locating the robot in the pool (via `vacuum.locate` service)
- Visibility during night operation
- Customizing robot appearance with LED modes

---

## Select Entity Details

### LED Mode Selection

| Attribute           | Value                          |
| ------------------- | ------------------------------ |
| **Entity ID**       | `select.{robot_name}_led_mode` |
| **Platform**        | Select                         |
| **Device Class**    | -                              |
| **Entity Category** | Configuration                  |

#### Functionality

Select the LED blinking pattern/mode:

- **Select Option** (`select.select_option`) - Choose from available LED modes
- Options include various blinking patterns (specific patterns vary by robot model)

#### States

Current LED mode value (e.g., "blinking", "solid", etc.)

---

## Number Entities Details

### LED Intensity

| Attribute           | Value                               |
| ------------------- | ----------------------------------- |
| **Entity ID**       | `number.{robot_name}_led_intensity` |
| **Platform**        | Number                              |
| **Device Class**    | Power Factor                        |
| **Entity Category** | Configuration                       |
| **Range**           | 0-100                               |
| **Unit**            | % (percentage)                      |

#### Functionality

Adjust the brightness level of the robot's LED:

- **Set Value** (`number.set_value`) - Set intensity from 0% (off) to 100% (full brightness)

---

### Cycle Time

| Attribute        | Value                            |
| ---------------- | -------------------------------- |
| **Entity ID**    | `number.{robot_name}_cycle_time` |
| **Platform**     | Number                           |
| **Device Class** | Duration                         |
| **Range**        | 1-600                            |
| **Unit**         | Minutes                          |

How long the current clean runs, as the robot reports it. When the robot is idle, this is the time of its last clean, which it also uses for the next one unless told otherwise.

#### Functionality

- **Set Value** (`number.set_value`) - Change how long the current clean runs. The robot only accepts this while it cleans or starts up, so setting it while idle fails with an error.
- Starting a clean from Home Assistant sets the robot's own time for that clean mode, as reported by the robot. A clean started from the MyDolphin app or a schedule keeps the time it chose.

**Attributes**:

- `start_time` - When the cycle started

**Icon**: Dynamic clock icon showing hour

#### Unit

Minutes

---

## Sensor Entities Details

### Status & Diagnostic Sensors

#### Status

| Attribute           | Value                        |
| ------------------- | ---------------------------- |
| **Entity ID**       | `sensor.{robot_name}_status` |
| **Device Class**    | -                            |
| **Entity Category** | Diagnostic                   |

Displays the calculated overall system state combining robot status, power supply status, and cleaning state.

**Attributes**: Contains detailed status breakdown including calculated state, vacuum state, power supply state, robot state, and more.

---

#### WiFi Signal Strength (RSSI)

| Attribute           | Value                      |
| ------------------- | -------------------------- |
| **Entity ID**       | `sensor.{robot_name}_rssi` |
| **Device Class**    | Signal Strength            |
| **Entity Category** | Diagnostic                 |
| **Unit**            | dBm                        |

Shows the WiFi signal strength between the robot and your wireless network.

**Range**: Typically -30 dBm (excellent) to -90 dBm (poor)

---

#### Network Name

| Attribute           | Value                              |
| ------------------- | ---------------------------------- |
| **Entity ID**       | `sensor.{robot_name}_network_name` |
| **Device Class**    | -                                  |
| **Entity Category** | Diagnostic                         |

Displays the SSID of the WiFi network the robot is connected to.

---

#### Clean Mode

| Attribute           | Value                            |
| ------------------- | -------------------------------- |
| **Entity ID**       | `sensor.{robot_name}_clean_mode` |
| **Device Class**    | -                                |
| **Entity Category** | Diagnostic                       |

Shows the current active cleaning mode.

**Values**: `all`, `short`, `floor`, `water`, `ultra`, `pickup`

---

#### Power Supply Status

| Attribute           | Value                                     |
| ------------------- | ----------------------------------------- |
| **Entity ID**       | `sensor.{robot_name}_power_supply_status` |
| **Device Class**    | -                                         |
| **Entity Category** | Diagnostic                                |

Displays the current state of the robot's power supply unit.

**Possible Values**: Varies by model (e.g., "charging", "floating", "programming", etc.)

---

#### Robot Status

| Attribute           | Value                              |
| ------------------- | ---------------------------------- |
| **Entity ID**       | `sensor.{robot_name}_robot_status` |
| **Device Class**    | -                                  |
| **Entity Category** | Diagnostic                         |

Shows the robot's current operational status.

---

#### Robot Type

| Attribute           | Value                            |
| ------------------- | -------------------------------- |
| **Entity ID**       | `sensor.{robot_name}_robot_type` |
| **Device Class**    | -                                |
| **Entity Category** | Diagnostic                       |

Displays the model type of your Dolphin robot.

---

#### Cycle Count

| Attribute           | Value                             |
| ------------------- | --------------------------------- |
| **Entity ID**       | `sensor.{robot_name}_cycle_count` |
| **Device Class**    | -                                 |
| **Entity Category** | Diagnostic                        |
| **State Class**     | Total Increasing                  |

Total number of cleaning cycles completed since the robot was first used.

**Usage**: Useful for tracking robot usage and scheduling maintenance.

---

### Cleaning Cycle Sensors

#### Cycle Time Left

| Attribute        | Value                                 |
| ---------------- | ------------------------------------- |
| **Entity ID**    | `sensor.{robot_name}_cycle_time_left` |
| **Device Class** | Duration                              |
| **State Class**  | Measurement                           |
| **Unit**         | Hours                                 |

Remaining time in the current cleaning cycle. The robot reports seconds; Home Assistant shows hours and minutes by default, such as 0h 45m, and you can pick another unit in the entity settings.

**Attributes**:

- `start_time` - When the cycle started
- `expected_end_time` - When the cycle is expected to finish

**Icon**: Dynamic clock icon showing remaining hours

**Note**: Only shows remaining time during active cleaning; shows 0 when not cleaning.

---

### Filter & Maintenance Sensors

#### Filter Status

| Attribute        | Value                               |
| ---------------- | ----------------------------------- |
| **Entity ID**    | `sensor.{robot_name}_filter_status` |
| **Device Class** | -                                   |
| **State Class**  | -                                   |

Status of the robot's filter bag indicating when it needs cleaning or replacement.

**States**:

- `OK` - Filter is clean
- `Warning` - Filter should be cleaned soon
- `Critical` - Filter needs immediate attention

**Attributes**:

- `status` - Numeric filter state value (0-255)
- `reset_fbi` - Filter bag indication reset flag

**Icon**: Dynamic icon based on filter status

---

### Error Sensors

#### Robot Error

| Attribute           | Value                                                            |
| ------------------- | ---------------------------------------------------------------- |
| **Entity ID**       | `sensor.{robot_name}_robot_error`                                |
| **Device Class**    | -                                                                |
| **Entity Category** | Diagnostic                                                       |
| **Icon**            | `mdi:robot-vacuum-variant` (changes to alert when error present) |

Robot error code. A value of `0` indicates no error.

**Usage**: Monitor for hardware or operational errors with the robot itself.

---

#### PWS Error

| Attribute           | Value                                                    |
| ------------------- | -------------------------------------------------------- |
| **Entity ID**       | `sensor.{robot_name}_pws_error`                          |
| **Device Class**    | -                                                        |
| **Entity Category** | Diagnostic                                               |
| **Icon**            | `mdi:water-boiler` (changes to alert when error present) |

Power Supply (PWS) error code. A value of `0` indicates no error.

**Usage**: Monitor for issues with the power supply unit.

---

### Battery & Environment Sensors

#### Battery

| Attribute        | Value                         |
| ---------------- | ----------------------------- |
| **Entity ID**    | `sensor.{robot_name}_battery` |
| **Device Class** | Battery                       |
| **State Class**  | Measurement                   |
| **Unit**         | %                             |

Battery level percentage.

**Note**: Pool cleaning robots are corded devices, so this always shows 100%. This entity exists for Home Assistant compatibility.

---

#### Temperature (M700 Models Only)

| Attribute        | Value                             |
| ---------------- | --------------------------------- |
| **Entity ID**    | `sensor.{robot_name}_temperature` |
| **Device Class** | Temperature                       |
| **State Class**  | Measurement                       |
| **Unit**         | °C                                |
| **Availability** | M700 family robots only           |

Water temperature measured by the robot.

**Note**: This entity only appears on M700 series robots that have temperature sensors.

---

## Binary Sensor Entity Details

### AWS Broker Connectivity

| Attribute           | Value                                   |
| ------------------- | --------------------------------------- |
| **Entity ID**       | `binary_sensor.{robot_name}_aws_broker` |
| **Device Class**    | Connectivity                            |
| **Entity Category** | Diagnostic                              |
| **Icon**            | `mdi:aws`                               |

Indicates whether the integration is connected to AWS IoT MQTT broker.

#### States

- `on` - Connected to AWS IoT (real-time updates active)
- `off` - Disconnected from AWS IoT (no real-time updates)

#### Attributes

- `status` - Detailed connectivity status

#### Importance

This entity is crucial for monitoring the health of the integration:

- When **on**: Real-time updates are working, commands are sent immediately
- When **off**: Integration is attempting to reconnect with exponential backoff

---

## Entity Categories

Home Assistant groups entities into categories for better organization:

### Configuration Entities

Entities used to configure the robot's behavior:

- `light.{robot_name}_led`
- `select.{robot_name}_led_mode`
- `number.{robot_name}_led_intensity`

**Total**: 3 entities

**UI Display**: Typically shown in a separate "Configuration" section

---

### Diagnostic Entities

Entities that provide diagnostic information and monitoring:

- `sensor.{robot_name}_status`
- `sensor.{robot_name}_rssi`
- `sensor.{robot_name}_network_name`
- `sensor.{robot_name}_clean_mode`
- `sensor.{robot_name}_power_supply_status`
- `sensor.{robot_name}_robot_status`
- `sensor.{robot_name}_robot_type`
- `sensor.{robot_name}_cycle_count`
- `sensor.{robot_name}_robot_error`
- `sensor.{robot_name}_pws_error`
- `binary_sensor.{robot_name}_aws_broker`

**Total**: 11 entities

**UI Display**: Typically hidden by default in the UI, accessible via "Show all"

---

### Main Entities

Entities for primary control and monitoring (no specific category):

- `vacuum.{robot_name}`
- `remote.{robot_name}_remote`
- `sensor.{robot_name}_filter_status`
- `number.{robot_name}_cycle_time`
- `sensor.{robot_name}_cycle_time_left`
- `sensor.{robot_name}_battery`
- `sensor.{robot_name}_temperature` (M700 only)

**Total**: 6-7 entities

**UI Display**: Prominently displayed on the device page

---

## Usage Examples

### Starting a Cleaning Cycle

```yaml
# Start cleaning with regular mode
service: vacuum.start
target:
  entity_id: vacuum.my_dolphin

# Start with specific cleaning mode
service: vacuum.set_fan_speed
data:
  fan_speed: floor  # floor only mode
target:
  entity_id: vacuum.my_dolphin

service: vacuum.start
target:
  entity_id: vacuum.my_dolphin
```

### Manual Control

```yaml
# Enter manual mode and move forward
service: remote.send_command
data:
  command: forward
target:
  entity_id: remote.my_dolphin_remote

# Stop movement
service: remote.send_command
data:
  command: stop
target:
  entity_id: remote.my_dolphin_remote

# Exit manual mode
service: remote.turn_off
target:
  entity_id: remote.my_dolphin_remote
```

### LED Control

```yaml
# Turn on LED at full brightness
service: light.turn_on
target:
  entity_id: light.my_dolphin_led

service: number.set_value
data:
  value: 100
target:
  entity_id: number.my_dolphin_led_intensity

# Turn on LED at 50% brightness
service: light.turn_on
target:
  entity_id: light.my_dolphin_led

service: number.set_value
data:
  value: 50
target:
  entity_id: number.my_dolphin_led_intensity
```

### Change the Current Clean's Time

```yaml
# Run the current clean for 90 minutes; the robot must be cleaning
service: number.set_value
data:
  value: 90
target:
  entity_id: number.my_dolphin_cycle_time
```

### Automation Examples

#### Daily Cleaning Schedule

```yaml
automation:
  - alias: "Pool Robot Daily Clean"
    trigger:
      - platform: time
        at: "06:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.my_dolphin_aws_broker
        state: "on" # Ensure connection is active
    action:
      - service: vacuum.set_fan_speed
        data:
          fan_speed: all # Regular mode
        target:
          entity_id: vacuum.my_dolphin
      - service: vacuum.start
        target:
          entity_id: vacuum.my_dolphin
```

#### Filter Maintenance Alert

```yaml
automation:
  - alias: "Pool Robot Filter Warning"
    trigger:
      - platform: state
        entity_id: sensor.my_dolphin_filter_status
        to: "Warning"
    action:
      - service: notify.mobile_app
        data:
          title: "Pool Robot Maintenance"
          message: "The pool robot filter should be cleaned soon."
```

#### Error Notification

```yaml
automation:
  - alias: "Pool Robot Error Alert"
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.my_dolphin_robot_error')|int > 0 or
             states('sensor.my_dolphin_pws_error')|int > 0 }}
    action:
      - service: notify.mobile_app
        data:
          title: "Pool Robot Error"
          message: >
            Robot Error: {{ states('sensor.my_dolphin_robot_error') }}
            PWS Error: {{ states('sensor.my_dolphin_pws_error') }}
```

#### Connection Monitoring

```yaml
automation:
  - alias: "Pool Robot Connection Lost"
    trigger:
      - platform: state
        entity_id: binary_sensor.my_dolphin_aws_broker
        to: "off"
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          title: "Pool Robot Offline"
          message: "Connection to pool robot has been lost."
```

---

## Entity Summary Table

| Platform      | Count    | Category      | Purpose                           |
| ------------- | -------- | ------------- | --------------------------------- |
| Vacuum        | 1        | Main          | Robot control and status          |
| Remote        | 1        | Main          | Manual joystick control           |
| Light         | 1        | Configuration | LED on/off                        |
| Select        | 1        | Configuration | LED mode selection                |
| Number        | 2        | Mixed         | LED intensity and cycle time      |
| Sensor        | 12       | Mixed         | Status, diagnostics, measurements |
| Binary Sensor | 1        | Diagnostic    | AWS connectivity                  |
| **TOTAL**     | **19\*** |               |                                   |

\* 18 entities for standard models, 19 for M700 models (includes temperature sensor)

---

## Additional Resources

- **Integration GitHub**: https://github.com/sh00t2kill/dolphin-robot
- **Workflows Documentation**: See [workflows.md](workflows.md) for technical details on how the integration works
- **Home Assistant Vacuum Documentation**: https://www.home-assistant.io/integrations/vacuum/
- **Maytronics Official Site**: https://www.maytronics.com/

---

## Notes

1. **Entity IDs**: The `{robot_name}` placeholder is replaced with your robot's actual name from the MyDolphin Plus app
2. **Availability**: All entities become unavailable if the integration loses connection to the robot
3. **Real-time Updates**: Most entities update in real-time via MQTT; some update every 30 seconds via polling
4. **M700 Models**: Temperature sensor is only available on M700 family robots
5. **Entity Registry**: You can customize entity IDs, names, and icons through Home Assistant's entity registry

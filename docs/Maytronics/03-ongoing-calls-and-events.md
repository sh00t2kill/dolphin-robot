# 3. Ongoing API Calls & Event Handling

Two communication planes operate in parallel: periodic REST calls for token/profile refresh, and persistent MQTT for real-time robot state.

> **Note**: This document contains Mermaid diagrams. To view them properly:
>
> - On GitHub: Diagrams render automatically
> - In VS Code/Cursor: Install the "Markdown Preview Mermaid Support" extension

---

## Periodic REST Calls

| Call                  | URL                                                          | Interval                           | Trigger                                            |
| --------------------- | ------------------------------------------------------------ | ---------------------------------- | -------------------------------------------------- |
| authenticate-user     | `https://apps.maytronics.com/mobapi/user/authenticate-user/` | 1 hour                             | `UPDATE_API_INTERVAL` timer                        |
| Cognito token refresh | `https://cognito-idp.us-west-2.amazonaws.com/`               | Before expiry (5 min window)       | `ID_TOKEN_REFRESH_WINDOW_SECONDS`                  |
| AWS STS getToken      | `https://apps.maytronics.com/mt-sso/aws/getToken/`           | 1h50m TTL / min 5min between calls | `AWS_CREDENTIALS_TTL` / `MIN_TOKEN_FETCH_INTERVAL` |

---

## MQTT Topics — Subscribe

| Topic Pattern                | Resolves To                    | Purpose                                             |
| ---------------------------- | ------------------------------ | --------------------------------------------------- |
| `$aws/things/{mus}/shadow/#` | `.../shadow/get/accepted`      | Device shadow: full state                           |
|                              | `.../shadow/update/accepted`   | Shadow update confirmations                         |
|                              | `.../shadow/get/rejected`      | Shadow get rejections                               |
|                              | `.../shadow/update/rejected`   | Shadow update rejections                            |
| `Maytronics/{mus}/main`      | `Maytronics/MOTOR_SERIAL/main` | Dynamic messages: joystick, temperature, pwsRequest |

> **Note:** `{mus}` = motor unit serial number, obtained during authentication.

---

## MQTT Topics — Publish

| Topic                             | Payload Example                                      | Purpose                                                       |
| --------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------- |
| `$aws/things/{mus}/shadow/get`    | `{}`                                                 | Request full shadow state (triggers `/get/accepted` response) |
| `$aws/things/{mus}/shadow/update` | `{"state":{"desired":{...}}}`                        | Send commands: cleaning mode, LED, pause, schedule            |
| `Maytronics/{mus}/main`           | `{"type":"pwsRequest","description":"joystick",...}` | Dynamic commands: joystick control, temperature read          |

---

## Sequence Diagram — Periodic REST Refresh

```mermaid
sequenceDiagram
    participant Timer as HA Timer
    participant Coord as Coordinator
    participant API as RestAPI
    participant CM as ConfigManager
    participant Cognito as AWS Cognito
    participant Maytr as Maytronics API

    Timer->>Coord: _async_update_data() fires
    Coord->>Coord: Check api_connected & aws_client_connected

    Coord->>Coord: now - last_update_api >= UPDATE_API_INTERVAL (1h)?

    alt Time for API update
        Coord->>API: update()
        API->>API: Check status == CONNECTED

        alt Device not yet loaded
            API->>API: _ensure_id_token_valid()

            alt Token near expiry
                API->>Cognito: POST InitiateAuth (REFRESH_TOKEN_AUTH)
                Cognito-->>API: New IdToken + ExpiresIn
                API->>CM: update_tokens()
            end

            API->>API: _authenticate_user()
            API->>Maytr: POST /mobapi/user/authenticate-user/
            Maytr-->>API: Sernum, eSERNUM, robot details

            API->>API: _device_loaded = True
            API->>Coord: dispatcher_send(SIGNAL_DEVICE_NEW)
        else Already loaded
            Note over API: Skip — use cached data
        end
    end
```

---

## Sequence Diagram — Periodic MQTT Shadow Poll

```mermaid
sequenceDiagram
    participant Timer as HA Timer
    participant Coord as Coordinator
    participant AWS as AWSClient
    participant Broker as AWS IoT Broker

    Timer->>Coord: _async_update_data() fires
    Coord->>Coord: now - last_update_ws >= UPDATE_WS_INTERVAL (30s)?

    alt Time for MQTT update
        Coord->>AWS: update()
        AWS->>AWS: Check status == CONNECTED
        AWS->>AWS: Record WS_LAST_UPDATE timestamp

        AWS->>Broker: Publish: $aws/things/{mus}/shadow/get → {}
        Note right of Broker: QoS: AT_MOST_ONCE

        Broker-->>AWS: shadow/get/accepted
        AWS->>AWS: _message_callback(topic, payload)

        AWS->>AWS: Extract version, timestamp
        AWS->>AWS: Calculate diff = now - server_timestamp

        loop For each category in state.reported
            AWS->>AWS: Merge category_data into self.data[category]
            Note over AWS: systemState, cycleInfo, led,<br/>wifi, debug, filterBagIndication,<br/>robotError, pwsError
        end

        alt Robot family == M700
            AWS->>AWS: _read_temperature_and_in_water_details()
            AWS->>Broker: Publish dynamic command for temperature
        end

        AWS->>Coord: _on_data_update_callback()
        Coord->>Coord: Update last_update_ws = now
    end

    Coord->>Coord: _set_system_status_details()
```

---

## Sequence Diagram — Real-time MQTT Push Updates

```mermaid
sequenceDiagram
    participant Broker as AWS IoT Broker
    participant AWS as AWSClient
    participant Coord as Coordinator
    participant Entities as HA Entities

    Note over Broker,Entities: Async push updates from device/cloud

    alt Shadow update accepted
        Broker->>AWS: Message on shadow/update/accepted
        AWS->>AWS: _message_callback(topic, payload)
        AWS->>AWS: Parse JSON, extract version + timestamp

        AWS->>AWS: Extract state.reported
        loop For each category in reported
            AWS->>AWS: Merge into self.data[category]
        end

        alt Has state.desired (command echo)
            AWS->>AWS: Extract cleaning_mode from desired
            alt Mode is not None
                AWS->>AWS: sleep(1)
                AWS->>AWS: _set_cycle_time(mode)
                AWS->>Broker: Publish cycle time to shadow/update
            end
        end

        AWS->>Coord: _on_data_update_callback()
    end

    alt Dynamic content message
        Broker->>AWS: Message on Maytronics/{mus}/main
        AWS->>AWS: _message_callback(topic, payload)
        AWS->>AWS: _on_dynamic_content_received(payload)

        AWS->>AWS: message_type = payload.type
        AWS->>AWS: content = payload.content
        AWS->>AWS: Store in data[dynamic][message_type]

        alt type == pwsRequest
            AWS->>AWS: _on_pws_request_message()
            AWS->>AWS: Update direction / remote_control_mode
        end

        AWS->>Coord: _on_data_update_callback()
    end

    alt Rejected message
        Broker->>AWS: Message on shadow/*/rejected
        AWS->>AWS: Log warning with payload details
    end

    Note over Coord,Entities: Debounced coordinator refresh

    Coord->>Coord: _on_mqtt_data_update()

    alt time_since_last >= 5s (max delay)
        Coord->>Coord: Force immediate async_request_refresh()
    else Within cooldown
        Coord->>Coord: _mqtt_debouncer.async_call()
        Note over Coord: 1s cooldown — batches rapid updates
        Coord->>Coord: _debounced_mqtt_refresh()
        Coord->>Coord: async_request_refresh()
    end

    Coord-->>Entities: Updated state available
```

---

## Shadow Message Structure

Shadow `get/accepted` messages follow the AWS IoT Device Shadow format:

```json
{
  "state": {
    "reported": {
      "systemState": {
        "pwsState": 1,
        "robotState": 1,
        "robotType": "...",
        "isBusy": false
      },
      "cycleInfo": { "cleaningMode": { "mode": "all" }, "cycleTime": 120 },
      "led": { "ledMode": "1", "ledIntensity": 80, "ledEnable": false },
      "filterBagIndication": { "state": 0, "resetFBI": false },
      "debug": { "WIFI_RSSI": -45 },
      "wifi": { "netName": "MyNetwork" }
    }
  },
  "version": 1234,
  "timestamp": 1715680000
}
```

---

## Dynamic Message Structure

Messages on `Maytronics/{mus}/main`:

```json
{
  "type": "pwsRequest",
  "description": "joystick",
  "content": {
    "speed": 50,
    "direction": "forward"
  }
}
```

Dynamic message types handled:

- `pwsRequest` — Joystick direction and remote control mode changes
- `iotResponse` — Temperature readings (M700 family)

---

## Publish Commands (desired state)

Commands are sent by publishing to the shadow `update` topic with a `desired` state:

| Command                | Desired Payload                                                    | Function                   |
| ---------------------- | ------------------------------------------------------------------ | -------------------------- |
| Set cleaning mode      | `{"cleaningMode": {"mode": "all"}}`                                | `set_cleaning_mode()`      |
| Set cycle time         | `{"cycleInfo": {"cycleTime": 120}}`                                | `_set_cycle_time()`        |
| Set LED mode           | `{"led": {"ledMode": "2", "ledIntensity": 80, "ledEnable": true}}` | `set_led_mode()`           |
| Pause robot            | `{"systemState": {"pwsState": 0}}`                                 | `pause()`                  |
| Pickup (return home)   | Sets cleaning mode to PICKUP                                       | `pickup()`                 |
| Reset filter indicator | `{"filterBagIndication": {"resetFbi": true}}`                      | `reset_filter_indicator()` |

---

## Update Intervals

| Interval              | Value      | Purpose                                       |
| --------------------- | ---------- | --------------------------------------------- |
| `UPDATE_WS_INTERVAL`  | 30 seconds | Periodic MQTT shadow get poll                 |
| `UPDATE_API_INTERVAL` | 1 hour     | REST profile refresh                          |
| Debounce cooldown     | 1 second   | MQTT callback → coordinator refresh           |
| Max MQTT delay        | 5 seconds  | Safety net: force refresh if debouncer stalls |

---

## Source Code

| Module                    | Responsibility                                                                                           |
| ------------------------- | -------------------------------------------------------------------------------------------------------- |
| `managers/aws_client.py`  | `_message_callback()` — routes messages; `_publish()` — sends commands; `update()` — periodic shadow get |
| `managers/coordinator.py` | `_async_update_data()` — periodic refresh; `_on_mqtt_data_update()` — debounced MQTT callback            |
| `managers/rest_api.py`    | `update()` — periodic authenticate-user; `_ensure_id_token_valid()` — token refresh                      |
| `models/topic_data.py`    | `TopicData` — constructs all topic strings from motor unit serial                                        |

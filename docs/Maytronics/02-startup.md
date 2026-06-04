# 2. Integration Startup

On load, the coordinator initializes the REST API (token refresh + profile), fetches AWS IoT credentials, then connects the MQTT client.

> **Note**: This document contains Mermaid diagrams. To view them properly:
>
> - On GitHub: Diagrams render automatically
> - In VS Code/Cursor: Install the "Markdown Preview Mermaid Support" extension

---

## Endpoints (in order)

| #   | URL                                                          | Purpose                                                     |
| --- | ------------------------------------------------------------ | ----------------------------------------------------------- |
| 1   | `https://cognito-idp.us-west-2.amazonaws.com/`               | Refresh IdToken via `REFRESH_TOKEN_AUTH` flow               |
| 2   | `https://apps.maytronics.com/mobapi/user/authenticate-user/` | Validate token, get serial numbers                          |
| 3   | `https://apps.maytronics.com/mt-sso/aws/getToken/`           | Fetch STS credentials (AccessKeyId, SecretAccessKey, Token) |
| 4   | `wss://a12rqfdx55bdbv-ats.iot.eu-west-1.amazonaws.com:443`   | MQTT over WebSocket (AWS IoT Core)                          |

---

## Sequence Diagram — Full Startup

```mermaid
sequenceDiagram
    participant HA as Home Assistant
    participant Coord as Coordinator
    participant API as RestAPI
    participant CM as ConfigManager
    participant Cognito as AWS Cognito<br/>cognito-idp.us-west-2
    participant Maytr as Maytronics API<br/>apps.maytronics.com
    participant AWS as AWSClient
    participant Broker as AWS IoT Broker<br/>a12rqf...iot.eu-west-1

    HA->>Coord: initialize()
    Coord->>Coord: _build_data_mapping()
    Coord->>HA: async_forward_entry_setups(PLATFORMS)
    Coord->>Coord: async_request_refresh()
    Coord->>API: initialize()

    API->>API: _initialize_session()
    API->>API: _login()

    Note over API,CM: Step 1: Refresh Cognito IdToken

    API->>CM: Get stored refresh_token
    alt No refresh token
        API->>API: _set_status(EXPIRED_TOKEN)
        API->>Coord: Signal → triggers reauth flow
    else Has refresh token
        API->>API: _ensure_id_token_valid()
        API->>API: Check expiry vs ID_TOKEN_REFRESH_WINDOW_SECONDS (5 min)

        alt Token still valid
            Note over API: Skip refresh, use cached IdToken
        else Token near expiry or expired
            API->>Cognito: POST InitiateAuth (REFRESH_TOKEN_AUTH)
            Note right of Cognito: AuthFlow: REFRESH_TOKEN_AUTH<br/>REFRESH_TOKEN: stored token
            Cognito-->>API: New IdToken + ExpiresIn
            API->>CM: update_tokens(IdToken, RefreshToken, ExpiresAt)
        end
    end

    Note over API,Maytr: Step 2: Authenticate user and get serials

    API->>API: _authenticate_user()
    API->>Maytr: POST /mobapi/user/authenticate-user/
    Note right of Maytr: Authorization: Bearer {IdToken}<br/>AppKey: 346BDE92-...-586C

    Maytr-->>API: Data (Sernum, eSERNUM, robot details)

    API->>CM: update_serial_number(Sernum)
    API->>CM: update_motor_unit_serial(eSERNUM)
    API->>API: Store robot details in self.data

    API->>API: _set_status(TEMPORARY_CONNECTED)

    Note over API,Maytr: Step 3: Fetch AWS STS credentials

    API->>API: _refresh_aws_credentials()
    API->>API: _are_cached_credentials_valid()?

    alt Cached credentials still valid
        Note over API: Skip fetch, use cached STS creds
        API->>API: _set_status(CONNECTED)
    else Need fresh credentials
        API->>API: Check rate limit (MIN_TOKEN_FETCH_INTERVAL: 5 min)
        API->>Maytr: GET /mt-sso/aws/getToken/
        Note right of Maytr: Authorization: Bearer {IdToken}
        Maytr-->>API: AccessKeyId, SecretAccessKey, Token

        API->>API: Store STS creds in self.data
        API->>CM: update_last_aws_credentials_fetch(now)
        API->>CM: update_aws_credentials_expiry(now + 1h50m)
        API->>API: _set_status(CONNECTED)
    end

    API->>Coord: dispatcher_send(SIGNAL_API_STATUS, CONNECTED)

    Note over Coord,Broker: Step 4: Initialize MQTT connection

    Coord->>Coord: _on_api_status_changed(CONNECTED)
    Coord->>Coord: _reconnection_attempts = 0
    Coord->>API: update()
    Coord->>AWS: update_api_data(api_data)
    Coord->>AWS: initialize()

    AWS->>AWS: _set_status(CONNECTING)
    AWS->>AWS: Build TopicData from motor_unit_serial
    AWS->>AWS: Load AmazonRootCA.pem certificate

    AWS->>AWS: mqtt_connection_builder.websockets_with_default_aws_signing()
    Note over AWS: endpoint: a12rqf...iot.eu-west-1<br/>port: 443, region: eu-west-1<br/>credentials: STS (AccessKeyId, Secret, Token)<br/>keep_alive: 30s, clean_session: false

    AWS->>Broker: MQTT WebSocket connect
    Broker-->>AWS: Connection established
    AWS->>AWS: _on_connection_success()
    AWS->>AWS: _set_status(CONNECTED)

    Note over AWS,Broker: Step 5: Subscribe and fetch initial state

    AWS->>AWS: _subscribe()
    AWS->>Broker: Subscribe: Maytronics/{mus}/main
    AWS->>Broker: Subscribe: $aws/things/{mus}/shadow/#
    Note right of Broker: QoS: AT_MOST_ONCE

    AWS->>Coord: dispatcher_send(SIGNAL_AWS_CLIENT_STATUS, CONNECTED)
    Coord->>Coord: _on_aws_client_status_changed(CONNECTED)
    Coord->>Coord: _reconnection_attempts = 0
    Coord->>AWS: update()

    AWS->>Broker: Publish: $aws/things/{mus}/shadow/get → {}
    Broker-->>AWS: shadow/get/accepted → full device state
    AWS->>AWS: _message_callback() → parse & store state

    Note over Coord: System fully operational
```

---

## AWS IoT Connection Parameters

| Parameter     | Value                                                 |
| ------------- | ----------------------------------------------------- |
| Endpoint      | `a12rqfdx55bdbv-ats.iot.eu-west-1.amazonaws.com`      |
| Port          | `443`                                                 |
| Region        | `eu-west-1`                                           |
| Protocol      | MQTT over WebSocket (`wss://`)                        |
| Auth          | AWS STS credentials (IAM)                             |
| Keep-alive    | 30 seconds                                            |
| Clean session | `false`                                               |
| CA cert       | `AmazonRootCA.pem` (bundled in `managers/` directory) |

---

## Status Transitions During Startup

```mermaid
stateDiagram-v2
    [*] --> CONNECTING : RestAPI.initialize()
    CONNECTING --> TEMPORARY_CONNECTED : authenticate-user OK
    TEMPORARY_CONNECTED --> CONNECTED : AWS STS creds obtained
    CONNECTED --> AWS_CONNECTING : AWSClient.initialize()
    AWS_CONNECTING --> AWS_CONNECTED : MQTT handshake OK
    AWS_CONNECTED --> [*] : System ready

    CONNECTING --> EXPIRED_TOKEN : No refresh token
    CONNECTING --> FAILED : Network / auth error
    TEMPORARY_CONNECTED --> FAILED : getToken fails
```

---

## Credential Caching

AWS STS credentials are cached to reduce API calls:

| Setting                | Value                   | Constant                          |
| ---------------------- | ----------------------- | --------------------------------- |
| Credential TTL         | 1 hour 50 minutes       | `AWS_CREDENTIALS_TTL`             |
| Min fetch interval     | 5 minutes               | `MIN_TOKEN_FETCH_INTERVAL`        |
| IdToken refresh window | 5 minutes before expiry | `ID_TOKEN_REFRESH_WINDOW_SECONDS` |

On startup, if cached credentials are still valid (checked via `_are_cached_credentials_valid()`), the STS fetch is skipped entirely.

---

## Source Code

| Module                       | Responsibility                                                                                  |
| ---------------------------- | ----------------------------------------------------------------------------------------------- |
| `managers/coordinator.py`    | `initialize()` — sets up platforms, triggers `RestAPI.initialize()`                             |
| `managers/rest_api.py`       | `_login()` → `_ensure_id_token_valid()` → `_authenticate_user()` → `_refresh_aws_credentials()` |
| `managers/aws_client.py`     | `initialize()` — builds MQTT client, connects, subscribes                                       |
| `managers/config_manager.py` | Reads/writes tokens and credentials to HA storage                                               |
| `common/consts.py`           | All endpoint URLs, timing constants, header values                                              |

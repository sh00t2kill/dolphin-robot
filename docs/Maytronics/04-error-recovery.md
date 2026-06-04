# 4. Connection Error Recovery

Recovery operates at two levels: the AWS CRT SDK handles transient MQTT reconnection automatically; the coordinator handles higher-level failures with exponential backoff.

> **Note**: This document contains Mermaid diagrams. To view them properly:
>
> - On GitHub: Diagrams render automatically
> - In VS Code/Cursor: Install the "Markdown Preview Mermaid Support" extension

---

## Status Values

| Status                | Meaning                             | Triggers                                  |
| --------------------- | ----------------------------------- | ----------------------------------------- |
| `CONNECTING`          | Establishing connection             | `initialize()` called                     |
| `TEMPORARY_CONNECTED` | REST login done, awaiting AWS creds | `authenticate-user` succeeded             |
| `CONNECTED`           | Fully operational                   | AWS credentials obtained / MQTT connected |
| `FAILED`              | Error occurred                      | HTTP error, MQTT failure, timeout         |
| `EXPIRED_TOKEN`       | Token rejected/expired              | 401 response, refresh failure             |
| `DISCONNECTED`        | Graceful shutdown                   | `terminate()` or connection closed        |
| `INVALID_CREDENTIALS` | Bad credentials                     | Authentication rejected                   |
| `API_NOT_FOUND`       | Endpoint missing                    | HTTP 404/405 response                     |

---

## State Diagram — Connectivity Status

```mermaid
stateDiagram-v2
    [*] --> CONNECTING : initialize()

    CONNECTING --> TEMPORARY_CONNECTED : authenticate-user OK
    CONNECTING --> FAILED : Network / auth error
    CONNECTING --> EXPIRED_TOKEN : No refresh token

    TEMPORARY_CONNECTED --> CONNECTED : AWS STS creds OK
    TEMPORARY_CONNECTED --> FAILED : getToken fails

    CONNECTED --> FAILED : HTTP error / MQTT failure
    CONNECTED --> EXPIRED_TOKEN : 401 + old token
    CONNECTED --> DISCONNECTED : terminate()

    FAILED --> CONNECTING : Backoff retry → initialize()
    EXPIRED_TOKEN --> CONNECTING : Reauth complete → initialize()
    DISCONNECTED --> CONNECTING : Re-initialize

    note right of FAILED : Triggers exponential backoff
    note right of EXPIRED_TOKEN : Triggers HA reauth flow
    note left of DISCONNECTED : DISCONNECTED → FAILED ignored<br/>(IGNORED_TRANSITIONS)
```

---

## Sequence Diagram — API Disconnection & Recovery

```mermaid
sequenceDiagram
    participant API as RestAPI
    participant Coord as Coordinator
    participant AWS as AWSClient
    participant CM as ConfigManager
    participant Cognito as AWS Cognito
    participant Maytr as Maytronics API
    participant Broker as AWS IoT Broker

    Note over API,CM: API Connection Failure Scenario

    API->>API: HTTP request fails (network/auth/server error)
    API->>API: _handle_client_error() or _handle_server_timeout()

    alt Token expired (401) and token age >= 15min
        API->>CM: reset_login_details()
        CM->>CM: Clear IdToken, RefreshToken
        API->>API: _set_status(EXPIRED_TOKEN)
    else 401 but token age < 15min
        API->>API: Log at DEBUG level
        Note over API: Treat as transient,<br/>await next scheduled refresh
    else HTTP 404/405
        API->>API: _set_status(API_NOT_FOUND)
    else Other failures
        API->>API: _set_status(FAILED)
    end

    alt Status is disconnected
        API->>API: _device_loaded = False
        Note over API: Ensures fresh data fetch on reconnect
    end

    API->>Coord: dispatcher_send(SIGNAL_API_STATUS, status)
    Coord->>Coord: _on_api_status_changed(entry_id, status)

    alt Status == EXPIRED_TOKEN
        Coord->>Coord: _start_reauth_if_needed()
        Note over Coord: Triggers HA reauth UI (OTP flow)
    end

    alt Status in [FAILED, INVALID_CREDENTIALS, EXPIRED_TOKEN]
        Coord->>Coord: _handle_connection_failure()

        Coord->>AWS: terminate()
        AWS->>AWS: disconnect()
        AWS->>AWS: _set_status(DISCONNECTED)

        Coord->>Coord: Calculate backoff = min(2^attempts, 15) minutes
        Coord->>Coord: Increment _reconnection_attempts
        Coord->>Coord: sleep(backoff_interval)

        Note over Coord: After backoff period

        Coord->>API: initialize()
        API->>API: _initialize_session()
        API->>API: _login()

        API->>API: _ensure_id_token_valid()
        API->>Cognito: POST InitiateAuth (REFRESH_TOKEN_AUTH)
        Cognito-->>API: New IdToken

        API->>API: _authenticate_user()
        API->>Maytr: POST /mobapi/user/authenticate-user/
        Maytr-->>API: Sernum, eSERNUM

        API->>API: _refresh_aws_credentials()
        API->>Maytr: GET /mt-sso/aws/getToken/
        Maytr-->>API: AccessKeyId, SecretAccessKey, Token

        alt All steps succeeded
            API->>API: _set_status(CONNECTED)
            API->>Coord: dispatcher_send(SIGNAL_API_STATUS, CONNECTED)

            Coord->>Coord: _on_api_status_changed(CONNECTED)
            Coord->>Coord: _reconnection_attempts = 0
            Note over Coord: Reset backoff counter

            Coord->>API: update()
            Coord->>AWS: update_api_data(api_data)
            Coord->>AWS: initialize()
            AWS->>Broker: MQTT WebSocket connect
            Broker-->>AWS: Connection established
            AWS->>AWS: _on_connection_success()
            AWS->>AWS: Subscribe + shadow/get

            Note over Coord,Broker: System fully recovered
        else Login or token fetch failed
            Note over API: Cycle repeats with next backoff level
        end
    end
```

---

## Sequence Diagram — AWS IoT MQTT Disconnection & Recovery

```mermaid
sequenceDiagram
    participant Broker as AWS IoT Broker
    participant AWS as AWSClient
    participant Coord as Coordinator
    participant API as RestAPI

    Note over Broker,API: AWS IoT Connection Failure Scenario

    alt Connection Interrupted
        Broker->>AWS: on_connection_interrupted(error)
        AWS->>AWS: _set_status(FAILED, error message)
        Note over AWS: CRT SDK will attempt<br/>auto-reconnect internally
    else Connection Closed
        Broker->>AWS: on_connection_closed()
        AWS->>AWS: _set_status(DISCONNECTED)
    else Initial Connection Failure
        Broker--xAWS: on_connection_failure(error)
        AWS->>AWS: _set_status(FAILED, error message)
    end

    AWS->>Coord: dispatcher_send(SIGNAL_AWS_CLIENT_STATUS, status)
    Coord->>Coord: _on_aws_client_status_changed(entry_id, status)

    alt Status in [FAILED, NOT_CONNECTED]
        Coord->>Coord: _handle_connection_failure()
        Coord->>AWS: terminate()
        Coord->>Coord: Calculate exponential backoff
        Coord->>Coord: sleep(backoff_interval)

        Coord->>API: initialize()
        Note over API: Full re-initialization:<br/>token refresh → authenticate → STS creds

        alt Re-initialization successful
            API->>Coord: SIGNAL_API_STATUS → CONNECTED
            Coord->>AWS: initialize()
            AWS->>Broker: Connect with fresh credentials
            Broker-->>AWS: Connection established
            AWS->>AWS: _on_connection_success()
            AWS->>AWS: Subscribe + shadow/get

            AWS->>Coord: SIGNAL_AWS_CLIENT_STATUS → CONNECTED
            Coord->>Coord: _reconnection_attempts = 0

            Note over AWS,Coord: System fully recovered
        else Still failing
            Note over Coord: Retry with next backoff level
        end
    end

    alt CRT SDK Auto-Reconnect (after interruption)
        Broker->>AWS: on_connection_resumed(return_code, session_present)
        AWS->>AWS: _awsiot_client = connection

        alt session_present == false
            AWS->>AWS: resubscribe_existing_topics()
            AWS->>Broker: Re-subscribe to all topics
        end

        AWS->>AWS: _set_status(CONNECTED)
        AWS->>Coord: SIGNAL_AWS_CLIENT_STATUS → CONNECTED
        Coord->>Coord: _reconnection_attempts = 0
        Coord->>AWS: update()

        Note over AWS: Automatic recovery complete
    end
```

---

## Exponential Backoff

| Attempt | Wait Time        | Formula                           |
| ------- | ---------------- | --------------------------------- |
| 1       | 1 minute         | 2^0 = 1                           |
| 2       | 2 minutes        | 2^1 = 2                           |
| 3       | 4 minutes        | 2^2 = 4                           |
| 4       | 8 minutes        | 2^3 = 8                           |
| 5+      | 15 minutes (max) | capped by `RECONNECT_BACKOFF_MAX` |

The counter (`_reconnection_attempts`) resets to 0 on any successful connection (either API or AWS client reaching `CONNECTED` status).

---

## Sequence Diagram — Token Expiry / 401 Handling

```mermaid
sequenceDiagram
    participant API as RestAPI
    participant CM as ConfigManager
    participant Coord as Coordinator
    participant HA as Home Assistant

    API->>API: HTTP 401 response received
    API->>API: _handle_client_error(endpoint, method, crex)

    API->>CM: Check id_token exists?

    alt No IdToken present
        API->>API: Log "No id token present"
        API->>API: _set_status(FAILED)
    else Has IdToken
        API->>CM: Get last_token_fetch timestamp

        alt last_fetch exists and token_age >= RECONNECT_BACKOFF_MAX (15 min)
            API->>CM: reset_login_details()
            Note over CM: Clear IdToken, RefreshToken,<br/>ExpiresAt, serial numbers
            API->>API: _set_status(EXPIRED_TOKEN)
            API->>Coord: SIGNAL_API_STATUS → EXPIRED_TOKEN

            Coord->>Coord: _start_reauth_if_needed()
            Coord->>HA: entry.async_start_reauth(hass)
            Note over HA: User sees reauth UI → OTP flow
        else Token age < 15 min
            API->>API: Log at DEBUG (treat as transient)
            Note over API: _ensure_id_token_valid() will<br/>attempt refresh on next cycle
        else No timestamp recorded
            API->>API: Log "Token exists but no timestamp"
            Note over API: Debug level, let refresh cycle handle it
        end
    end
```

---

## Rate Limiting

AWS credential fetches are rate-limited to prevent hammering the Maytronics API:

| Setting                    | Value             | Purpose                                                       |
| -------------------------- | ----------------- | ------------------------------------------------------------- |
| `MIN_TOKEN_FETCH_INTERVAL` | 5 minutes         | Minimum time between `getToken` calls                         |
| `AWS_CREDENTIALS_TTL`      | 1 hour 50 minutes | Cache validity (AWS tokens valid for 2h, 10min safety margin) |

**Behavior when rate-limited:**

1. If cached credentials are still valid → use them
2. If cached credentials expired and rate-limited → status `FAILED` (wait for cooldown)
3. If no cache at all → attempt fetch despite rate limit (best effort)

---

## Ignored Status Transitions

To prevent status thrashing, certain transitions are suppressed:

```python
IGNORED_TRANSITIONS = {ConnectivityStatus.DISCONNECTED: [ConnectivityStatus.FAILED]}
```

When the system is already `DISCONNECTED`, a transition to `FAILED` is ignored — the system is already shutting down.

---

## Coordinator Signal Handling Summary

### API Status Changes (`SIGNAL_API_STATUS`)

| Status                | Coordinator Action                                                                                  |
| --------------------- | --------------------------------------------------------------------------------------------------- |
| `CONNECTED`           | Reset backoff counter, call `api.update()`, pass data to AWS client, call `aws_client.initialize()` |
| `FAILED`              | Trigger `_handle_connection_failure()` (backoff + retry)                                            |
| `INVALID_CREDENTIALS` | Trigger `_handle_connection_failure()`                                                              |
| `EXPIRED_TOKEN`       | Start HA reauth flow + trigger `_handle_connection_failure()`                                       |

### AWS Client Status Changes (`SIGNAL_AWS_CLIENT_STATUS`)

| Status          | Coordinator Action                                                     |
| --------------- | ---------------------------------------------------------------------- |
| `CONNECTED`     | Reset backoff counter, call `aws_client.update()` (initial shadow get) |
| `FAILED`        | Trigger `_handle_connection_failure()`                                 |
| `NOT_CONNECTED` | Trigger `_handle_connection_failure()`                                 |

---

## Source Code

| Module                          | Responsibility                                                                                                                   |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `managers/coordinator.py`       | `_handle_connection_failure()` — backoff logic; `_on_api_status_changed()` / `_on_aws_client_status_changed()` — signal handlers |
| `managers/rest_api.py`          | `_handle_client_error()` — 401/404 handling; `_set_status()` — dispatches `SIGNAL_API_STATUS`                                    |
| `managers/aws_client.py`        | `_on_connection_*()` callbacks — MQTT lifecycle; `_set_status()` — dispatches `SIGNAL_AWS_CLIENT_STATUS`                         |
| `common/connectivity_status.py` | `ConnectivityStatus` enum, `IGNORED_TRANSITIONS` map                                                                             |

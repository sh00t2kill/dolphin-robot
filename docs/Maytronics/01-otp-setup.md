# 1. Set Up New Integration (OTP Flow)

The integration uses **AWS Cognito Custom Auth** with OTP delivered to the user's email. No password is stored — only tokens are persisted.

> **Note**: This document contains Mermaid diagrams. To view them properly:
>
> - On GitHub: Diagrams render automatically
> - In VS Code/Cursor: Install the "Markdown Preview Mermaid Support" extension

---

## Endpoints

| Step         | URL                                                          | Method | Purpose                              |
| ------------ | ------------------------------------------------------------ | ------ | ------------------------------------ |
| Initiate OTP | `https://cognito-idp.us-west-2.amazonaws.com/`               | POST   | Cognito `InitiateAuth` (CUSTOM_AUTH) |
| Submit OTP   | `https://cognito-idp.us-west-2.amazonaws.com/`               | POST   | Cognito `RespondToAuthChallenge`     |
| Get Profile  | `https://apps.maytronics.com/mobapi/user/authenticate-user/` | POST   | Returns serial numbers for robot     |

---

## Sequence Diagram — New Integration Setup

```mermaid
sequenceDiagram
    participant User as User (HA UI)
    participant CF as ConfigFlow
    participant FM as FlowManager
    participant Cognito as AWS Cognito<br/>cognito-idp.us-west-2
    participant Maytr as Maytronics API<br/>apps.maytronics.com

    User->>CF: Enter email + title
    CF->>FM: async_step_user(user_input)
    FM->>FM: Validate email is not empty

    FM->>Cognito: POST InitiateAuth
    Note right of Cognito: AuthFlow: CUSTOM_AUTH<br/>ClientId: 4ed12eq...2na<br/>USERNAME: user email

    alt Cognito returns CUSTOM_CHALLENGE
        Cognito-->>FM: Session token + ChallengeName
        FM->>FM: Store session + email in flow state
        FM-->>User: Show OTP input form
    else Cognito error
        Cognito--xFM: Error response
        FM-->>User: Show error "otp_send_failed"
    end

    Note over User,Cognito: OTP code delivered to user's email

    User->>CF: Enter OTP code
    CF->>FM: async_step_otp(user_input)

    FM->>Cognito: POST RespondToAuthChallenge
    Note right of Cognito: ChallengeName: CUSTOM_CHALLENGE<br/>ANSWER: OTP code<br/>Session: stored session token

    alt OTP accepted
        Cognito-->>FM: AuthenticationResult (IdToken, RefreshToken, ExpiresIn)

        FM->>Maytr: POST /mobapi/user/authenticate-user/
        Note right of Maytr: Authorization: Bearer {IdToken}<br/>AppKey: 346BDE92-...-586C<br/>app_version: ios_3.1.7_2

        Maytr-->>FM: Data (Sernum, eSERNUM, robot details)

        FM->>FM: Build initial_tokens dict
        Note over FM: IdToken, RefreshToken,<br/>ExpiresAt, Sernum, eSERNUM

        alt New setup
            FM->>CF: async_create_entry(title, data)
            CF-->>User: Integration created
        else Reauthentication
            FM->>CF: async_update_reload_and_abort(entry, data_updates)
            CF-->>User: Integration reloaded
        else Options flow update
            FM->>CF: async_update_entry + async_schedule_reload
            CF-->>User: Integration updated
        end
    else OTP rejected
        Cognito--xFM: Error
        FM-->>User: Show error "invalid_otp"
    end
```

---

## Key Parameters

| Parameter        | Value                                  |
| ---------------- | -------------------------------------- |
| Cognito ClientId | `4ed12eq01o6n0tl5f0sqmkq2na`           |
| Auth Flow        | `CUSTOM_AUTH`                          |
| Challenge Name   | `CUSTOM_CHALLENGE`                     |
| AppKey header    | `346BDE92-53D1-4829-8A2E-B496014B586C` |
| App Version      | `ios_3.1.7_2`                          |

---

## Sequence Diagram — Reauthentication

When the refresh token expires or is rejected, the coordinator triggers HA's reauth flow which re-runs the same OTP sequence.

```mermaid
sequenceDiagram
    participant API as RestAPI
    participant Coord as Coordinator
    participant HA as Home Assistant
    participant User as User (HA UI)
    participant FM as FlowManager
    participant Cognito as AWS Cognito

    API->>API: _ensure_id_token_valid() - refresh fails
    API->>API: reset_login_details()
    API->>API: _set_status(EXPIRED_TOKEN)
    API->>Coord: dispatcher_send(SIGNAL_API_STATUS, EXPIRED_TOKEN)

    Coord->>Coord: _on_api_status_changed(EXPIRED_TOKEN)
    Coord->>Coord: _start_reauth_if_needed()

    alt Reauth not already in progress
        Coord->>HA: entry.async_start_reauth(hass)
        Coord->>Coord: _reauth_in_progress = True

        HA-->>User: Show reauth confirmation form
        User->>HA: Confirm reauth
        HA->>FM: async_step_reauth_confirm(user_input)

        FM->>FM: async_step_user(None)
        FM-->>User: Show email form (pre-filled)

        Note over User,Cognito: Same OTP flow as new setup<br/>(InitiateAuth → OTP → RespondToAuthChallenge)

        FM->>HA: async_update_reload_and_abort(entry, data_updates)
        Note over HA: Integration reloads with new tokens

        HA->>Coord: Re-initialize (new entry data)
        Coord->>Coord: _reauth_in_progress = False
    else Already in progress
        Coord->>Coord: Skip (avoid duplicate reauth)
    end
```

---

## Source Code

| Module                     | Responsibility                                                                                    |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| `managers/flow_manager.py` | `IntegrationFlowManager` — orchestrates `async_step_user` (email) and `async_step_otp` (code)     |
| `managers/rest_api.py`     | `cognito_initiate_auth()`, `cognito_respond_otp()`, `fetch_user_profile()` — standalone functions |
| `config_flow.py`           | HA config flow entry points: `async_step_user`, `async_step_otp`, `async_step_reauth`             |

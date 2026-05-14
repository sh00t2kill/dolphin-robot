# Validates the complete MyDolphin Plus auth + bootstrap chain:
#   1. Cognito CUSTOM_AUTH (email OTP)
#   2. apps.maytronics.com/mobapi/user/authenticate-user/
#   3. apps.maytronics.com/mt-sso/aws/getToken/
#
# Run:  pip install aiohttp  &&  python test_full.py

import asyncio
import json

import aiohttp

CLIENT_ID = "4ed12eq01o6n0tl5f0sqmkq2na"
COGNITO_ENDPOINT = "https://cognito-idp.us-west-2.amazonaws.com/"
APPS_BASE = "https://apps.maytronics.com"
APP_KEYS = {
    "MyDolphin Plus": "346BDE92-53D1-4829-8A2E-B496014B586C",
    "Maytronics One": "39AF9BF2-E906-4205-9368-EB3E16663ACE"
}

APP_VERSION = "ios_3.1.7_2"
USER_AGENT = "HA-MyDolphin-Plus/v1.0.26b3"


async def cognito(session, target, body):
    async with session.post(
        COGNITO_ENDPOINT,
        headers={
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": f"AWSCognitoIdentityProviderService.{target}",
        },
        data=json.dumps(body),
    ) as r:
        text = await r.text()
        if r.status >= 400:
            raise RuntimeError(f"{target} {r.status}: {text}")
        return json.loads(text)


async def read_json_response(response, label):
    text = await response.text()
    content_type = response.headers.get("Content-Type", "")

    if response.status >= 400:
        print(f"\n{label}: HTTP {response.status}")
        print(f"   Content-Type: {content_type}")
        print("   Body preview:")
        print(text[:1000])
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"\n{label}: failed to decode JSON")
        print(f"   Content-Type: {content_type}")
        print("   Body preview:")
        print(text[:1000])
        return None


def select_app_key():
    apps = list(APP_KEYS.items())

    print("Choose app:")
    for index, (name, _) in enumerate(apps, start=1):
        print(f"  {index}. {name}")

    while True:
        choice = input("App: ").strip()
        try:
            index = int(choice)
        except ValueError:
            print("Please enter a number from the list.")
            continue

        if 1 <= index <= len(apps):
            name, app_key = apps[index - 1]
            print(f"Using app: {name}")
            return app_key

        print("Please enter a number from the list.")


async def main():
    app_key = select_app_key()
    email = input("Email: ").strip().lower()

    async with aiohttp.ClientSession() as s:
        # ---- 1. Trigger OTP email ----
        init = await cognito(s, "InitiateAuth", {
            "AuthFlow": "CUSTOM_AUTH",
            "ClientId": CLIENT_ID,
            "AuthParameters": {"USERNAME": email},
            "ClientMetadata": {},
        })
        if init.get("ChallengeName") != "CUSTOM_CHALLENGE":
            print("❌ Unexpected challenge:", json.dumps(init, indent=2))
            return
        print("OTP email sent. Check your inbox.")

        # ---- 2. Submit OTP, exchange for tokens ----
        code = input("OTP: ").strip()
        resp = await cognito(s, "RespondToAuthChallenge", {
            "ChallengeName": "CUSTOM_CHALLENGE",
            "ClientId": CLIENT_ID,
            "Session": init["Session"],
            "ChallengeResponses": {"USERNAME": email, "ANSWER": code},
            "ClientMetadata": {},
        })
        if "AuthenticationResult" not in resp:
            print("❌ OTP rejected:", json.dumps(resp, indent=2))
            return

        r = resp["AuthenticationResult"]
        id_token = r["IdToken"]
        print("\n✅ Cognito login OK")
        print("   ExpiresIn:        ", r["ExpiresIn"], "seconds")
        print("   Has RefreshToken: ", bool(r.get("RefreshToken")))
        print(json.dumps(resp, indent=2))

        bearer_headers = {
            "Authorization": f"Bearer {id_token}",
            "AppKey": app_key,
            "app_version": APP_VERSION,
            "Accept": "*/*",
            "User-Agent": USER_AGENT,
        }

        # ---- 3. authenticate-user (user profile + robot info) ----
        async with s.post(
            f"{APPS_BASE}/mobapi/user/authenticate-user/",
            headers={**bearer_headers,
                     "Content-Type": "application/x-www-form-urlencoded"},
            data="",
        ) as ar:
            auth_data = await read_json_response(ar, "authenticate-user")
            if auth_data is None:
                return
            print("\nauthenticate-user:", ar.status, auth_data.get("Alert"))
            data = auth_data.get("Data", {}) or {}
            print("   Sernum:    ", data.get("Sernum"))
            print("   eSERNUM:   ", data.get("eSERNUM"))
            print("   Robot name:", data.get("MyRobotName"))
            print("   Email:     ", data.get("Email"))
            print("   fmu/fsm:   ", data.get("fmu"), "/", data.get("fsm"))

        # ---- 4. getToken (AWS STS creds for IoT MQTT) ----
        async with s.get(
            f"{APPS_BASE}/mt-sso/aws/getToken/",
            headers=bearer_headers,
        ) as tr:
            tok_data = await read_json_response(tr, "getToken")
            if tok_data is None:
                return
            td = tok_data.get("Data", {}) or {}
            print("\ngetToken:", tr.status, tok_data.get("Alert"))
            print("   AccessKeyId prefix:", str(td.get("AccessKeyId", ""))[:8], "...")
            print("   Has SessionToken:  ", bool(td.get("Token")))
            print("   Expires:            ", td.get("TokenExpiration"))

        # ---- 5. Quick refresh-token sanity check ----
        if r.get("RefreshToken"):
            print("\nTesting refresh-token path...")
            try:
                refreshed = await cognito(s, "InitiateAuth", {
                    "AuthFlow": "REFRESH_TOKEN_AUTH",
                    "ClientId": CLIENT_ID,
                    "AuthParameters": {"REFRESH_TOKEN": r["RefreshToken"]},
                    "ClientMetadata": {},
                })
                rr = refreshed.get("AuthenticationResult", {})
                print("   ✅ Refresh OK; new IdToken expires in",
                      rr.get("ExpiresIn"), "seconds")
            except Exception as e:
                print("   ❌ Refresh failed:", e)


if __name__ == "__main__":
    asyncio.run(main())

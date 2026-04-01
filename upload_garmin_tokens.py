#!/usr/bin/env python3
"""
Run this script LOCALLY to generate Garmin garth tokens and upload them to Railway.
This bypasses the Garmin IP ban on Railway by logging in from your local machine.

Usage:
    pip install garminconnect requests
    python upload_garmin_tokens.py
"""

import os, json, tempfile, getpass
import requests

API_URL = "https://api.healthsync.online"

def login_api(username, password):
    r = requests.post(f"{API_URL}/api/auth/login", json={"username": username, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]

def garmin_login_and_export(email, garmin_password):
    from garminconnect import Garmin
    print(f"[*] Logging into Garmin as {email} from local IP...")
    client = Garmin(email, garmin_password)
    client.login()
    print(f"[*] Logged in! display_name={client.display_name}")

    tmp = tempfile.mkdtemp()
    client.garth.dump(tmp)
    tokens = {}
    for fname in os.listdir(tmp):
        with open(os.path.join(tmp, fname)) as fh:
            tokens[fname] = fh.read()
    print(f"[*] Exported {len(tokens)} token file(s): {list(tokens.keys())}")
    return tokens

def upload_tokens(api_token, tokens):
    r = requests.post(
        f"{API_URL}/api/metrics/garmin/inject-tokens",
        json={"tokens": tokens},
        headers={"Authorization": f"Bearer {api_token}"}
    )
    r.raise_for_status()
    print(f"[*] Uploaded to Railway: {r.json()}")

def main():
    print("=== Garmin Token Uploader ===\n")
    print("Step 1: Login to HealthSync API")
    hs_username = input("HealthSync username (e.g. aminov_kirill): ").strip()
    hs_password = getpass.getpass("HealthSync password: ")
    api_token = login_api(hs_username, hs_password)
    print("[*] HealthSync login OK\n")

    print("Step 2: Login to Garmin (from your local IP)")
    garmin_email = input("Garmin email: ").strip()
    garmin_password = getpass.getpass("Garmin password: ")
    tokens = garmin_login_and_export(garmin_email, garmin_password)

    print("\nStep 3: Upload tokens to Railway DB")
    upload_tokens(api_token, tokens)
    print("\n[OK] Done! Garmin sync should work on Railway now.")
    print("     Try: curl -X POST https://api.healthsync.online/api/metrics/garmin/sync -H 'Authorization: Bearer <token>'")

if __name__ == "__main__":
    main()

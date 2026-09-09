"""
Automated Verification Suite for SquadVault Backend (Phase 2)
Tests REST APIs, Debt Graph solver, Settings, Profile Updates, Itineraries, OCR, FX.
"""

import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_endpoint(name, url, method="GET", payload=None):
    try:
        req = urllib.request.Request(url, method=method)
        if payload:
            data = json.dumps(payload).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        else:
            data = None
            
        with urllib.request.urlopen(req, data=data) as response:
            status = response.status
            body = json.loads(response.read().decode('utf-8'))
            print(f"[PASS] {name} (HTTP {status})")
            return body
    except Exception as e:
        print(f"[FAIL] {name} - Error: {e}")
        sys.exit(1)

def run_all_tests():
    print("--- Starting SquadVault Phase 2 Verification Tests ---")

    # 1. Users & Settings
    users = test_endpoint("Get Users", f"{BASE_URL}/users")
    assert len(users) >= 4, "Expected at least 4 users"
    uid = users[0]["id"]

    settings = test_endpoint("Get User Settings", f"{BASE_URL}/users/{uid}/settings")
    assert "theme" in settings, "Missing theme in settings"

    # Save User Settings
    save_set = test_endpoint("Update User Settings", f"{BASE_URL}/users/{uid}/settings", method="PUT", payload={
        "theme": "cyberpunk",
        "notify_expenses": True,
        "notify_settlements": True,
        "notify_chat": True,
        "notify_likes": False
    })
    assert save_set.get("status") == "settings_saved"

    # Update Profile
    profile_up = test_endpoint("Update Profile", f"{BASE_URL}/users/{uid}", method="PUT", payload={
        "name": "Alex Rivera (Lead)",
        "handle": "@alex_r",
        "avatar": users[0]["avatar"],
        "bio": "Updated bio via API",
        "venmo_handle": "@alex-rivera-venmo",
        "zelle_handle": "alex@rivera.com"
    })
    assert profile_up.get("status") == "updated"

    # 2. Squads & Summary
    squads = test_endpoint("Get Squads", f"{BASE_URL}/squads")
    squad_id = squads[0]["id"]
    summary = test_endpoint("Get Squad Summary & Debt Graph", f"{BASE_URL}/squads/{squad_id}/summary")
    assert "simplified_debts" in summary

    # 3. Itinerary API
    itineraries = test_endpoint("Get Itineraries", f"{BASE_URL}/squads/{squad_id}/itinerary")
    assert isinstance(itineraries, list)

    new_itin = test_endpoint("Create Itinerary Event", f"{BASE_URL}/squads/{squad_id}/itinerary", method="POST", payload={
        "squad_id": squad_id,
        "title": "Evening Hot Springs & Sauna",
        "date": "2026-09-10",
        "time": "08:00 PM",
        "location": "Tahoe Resort Spa",
        "cost": 35.0,
        "created_by": uid
    })
    assert new_itin.get("status") == "created"

    # 4. OCR & FX APIs
    ocr_res = test_endpoint("Scan Receipt (OCR)", f"{BASE_URL}/ocr/scan-receipt", method="POST")
    assert "items" in ocr_res and "total" in ocr_res

    fx_rates = test_endpoint("Get FX Exchange Rates", f"{BASE_URL}/fx/rates")
    assert "EUR" in fx_rates and "JPY" in fx_rates

    voice_res = test_endpoint("Voice Parse Command", f"{BASE_URL}/voice/parse", method="POST", payload={
        "voice_text": "Split $50 pizza between Alex and Maya"
    })
    assert voice_res.get("parsed_amount") == 50.0

    print("\n--- ALL PHASE 2 VERIFICATION TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_all_tests()

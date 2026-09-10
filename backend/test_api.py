"""
Automated Verification Suite for SplitVibe Backend (Auth System Included)
Tests Auth Register, Login, Invalid Password handling, REST APIs, Debt Graph, Settings, OCR, FX.
"""

import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_endpoint(name, url, method="GET", payload=None, expected_status=200):
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
            if status == expected_status:
                print(f"[PASS] {name} (HTTP {status})")
                return body
            else:
                print(f"[FAIL] {name} - Expected {expected_status}, got {status}")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        if e.code == expected_status:
            print(f"[PASS] {name} (Expected HTTP {e.code})")
            return json.loads(e.read().decode('utf-8'))
        else:
            print(f"[FAIL] {name} - HTTP Error {e.code}: {e.reason}")
            sys.exit(1)
    except Exception as e:
        print(f"[FAIL] {name} - Error: {e}")
        sys.exit(1)

def run_all_tests():
    print("--- Starting SplitVibe Auth & Full Stack Verification Tests ---")

    # 1. Auth Register Test
    new_handle = f"@testuser_{hash(BASE_URL) % 10000}"
    reg_res = test_endpoint("Register New Account", f"{BASE_URL}/auth/register", method="POST", payload={
        "name": "Test Runner User",
        "handle": new_handle,
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "bio": "Automated Tester Account",
        "password": "secretpassword123"
    })
    assert reg_res.get("status") == "success"
    assert "token" in reg_res

    # 2. Auth Login Test (Valid Credentials)
    login_res = test_endpoint("Login Account (Valid)", f"{BASE_URL}/auth/login", method="POST", payload={
        "handle": new_handle,
        "password": "secretpassword123"
    })
    assert login_res.get("status") == "success"

    # 3. Auth Login Test (Invalid Password)
    test_endpoint("Login Account (Invalid Password)", f"{BASE_URL}/auth/login", method="POST", payload={
        "handle": new_handle,
        "password": "wrongpassword"
    }, expected_status=401)

    # 4. Users & Settings
    users = test_endpoint("Get Users", f"{BASE_URL}/users")
    assert len(users) >= 4, "Expected users list"
    uid = users[0]["id"]

    settings = test_endpoint("Get User Settings", f"{BASE_URL}/users/{uid}/settings")
    assert "theme" in settings

    save_set = test_endpoint("Update User Settings", f"{BASE_URL}/users/{uid}/settings", method="PUT", payload={
        "theme": "cyberpunk",
        "notify_expenses": True,
        "notify_settlements": True,
        "notify_chat": True,
        "notify_likes": False
    })
    assert save_set.get("status") == "settings_saved"

    # 5. Squads & Debt Summary
    squads = test_endpoint("Get Squads", f"{BASE_URL}/squads")
    squad_id = squads[0]["id"]
    summary = test_endpoint("Get Squad Summary & Debt Graph", f"{BASE_URL}/squads/{squad_id}/summary")
    assert "simplified_debts" in summary

    # 6. OCR & FX APIs
    ocr_res = test_endpoint("Scan Receipt (OCR)", f"{BASE_URL}/ocr/scan-receipt", method="POST")
    assert "items" in ocr_res and "total" in ocr_res

    fx_rates = test_endpoint("Get FX Exchange Rates", f"{BASE_URL}/fx/rates")
    assert "EUR" in fx_rates

    print("\n--- ALL AUTH & FULL STACK TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    run_all_tests()

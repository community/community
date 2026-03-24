"""
Checks if a GitHub user is a member of the 'github' organisation.

Logic:
  1. If ORG_MEMBERS_TOKEN is empty, outputs is_employee=false and exits.
  2. If USERNAME is empty, outputs is_employee=false and exits.
  3. Makes a REST API call to GET /orgs/{org}/members/{username}.
  4. HTTP 204 → member → outputs is_employee=true.
  5. HTTP 404 or any error → not a member → outputs is_employee=false.

Required environment variables:
    ORG_MEMBERS_TOKEN  - Token with org:read scope for the 'github' org
                         (optional: if absent, all authors are treated as
                         not-employee and source_check.py handles bot detection)
    USERNAME           - GitHub login to check
    GITHUB_OUTPUT      - Path to the GitHub Actions output file (set automatically)
"""

import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ORG = "github"


def set_output(name: str, value: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if not github_output:
        print(f"::notice::OUTPUT {name}={value}")
        return
    with open(github_output, "a", encoding="utf-8") as f:
        f.write(f"{name}={value}\n")


def check_org_membership(token: str, username: str) -> bool:
    """Return True if *username* is a member of ORG, False otherwise."""
    url = f"https://api.github.com/orgs/{ORG}/members/{urllib.parse.quote(username)}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "check-employee",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status == 204
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"'{username}' is NOT a member of org '{ORG}'.")
        else:
            print(f"Unexpected HTTP {e.code} checking membership; treating as not-employee.")
        return False
    except urllib.error.URLError as e:
        print(f"Network error checking membership: {e.reason}; treating as not-employee.")
        return False


def main() -> int:
    token = os.environ.get("ORG_MEMBERS_TOKEN", "").strip()
    username = os.environ.get("USERNAME", "").strip()

    if not token:
        print("ORG_MEMBERS_TOKEN is not set; treating all authors as not-employee.")
        set_output("is_employee", "false")
        return 0

    if not username:
        print("No username found; treating as not-employee.")
        set_output("is_employee", "false")
        return 0

    is_member = check_org_membership(token, username)

    if is_member:
        print(f"'{username}' IS a member of org '{ORG}' (treat as employee).")
    else:
        print(f"'{username}' is NOT a member of org '{ORG}'.")

    set_output("is_employee", "true" if is_member else "false")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

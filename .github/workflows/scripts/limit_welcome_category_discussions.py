"""
Prevents a user from creating multiple discussions in the "A Welcome to GitHub" category.

Logic:
  1. If the author is a GitHub employee (IS_EMPLOYEE=true) or github-actions[bot], skip.
  2. Use GitHub GraphQL search to count discussions by this author in the category.
     - count >= 2             → has_prior=true (multiple discussions exist)
     - count == 1, not current → has_prior=true (an older discussion exists)
     - count == 1, is current  → has_prior=false (only their current introduction)
     - count == 0             → fall back to REST search
  3. REST fallback: distinguishes private/unsearchable users (422 → fail-safe false)
     from users with genuinely no prior discussions (success → has_prior=false).

Required environment variables:
    GITHUB_TOKEN              - Token with discussion read permission
    OWNER                     - Repository owner
    REPO                      - Repository name
    CURRENT_DISCUSSION_NUMBER - The numeric number of the newly created/moved discussion
    AUTHOR_LOGIN              - GitHub login of the discussion author
    IS_EMPLOYEE               - 'true' if the author is a GitHub org member, else 'false'
    GITHUB_OUTPUT             - Path to the GitHub Actions output file (set automatically)
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

CATEGORY_NAME = "A Welcome to GitHub"
GRAPHQL_URL = "https://api.github.com/graphql"
REST_SEARCH_URL = "https://api.github.com/search/issues"


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise RuntimeError(f"Missing required env var: {name}")
    return value.strip()


def github_graphql(token: str, query: str, variables: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "limit-welcome-category-discussions",
    }
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(GRAPHQL_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"GraphQL request failed ({e.code}): {raw}") from e


def github_rest_get(token: str, url: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "limit-welcome-category-discussions",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"REST request failed ({e.code}): {raw}") from e


def search_discussions_in_category(
    token: str, owner: str, repo: str, author: str
) -> dict:
    """Search for discussions by the given author in the target category using GraphQL search."""
    query = (
        "query($q: String!) {"
        "  search(query: $q, type: DISCUSSION, first: 2) {"
        "    discussionCount"
        "    nodes { ... on Discussion { number } }"
        "  }"
        "}"
    )
    search_q = f'repo:{owner}/{repo} author:{author} category:"{CATEGORY_NAME}"'
    return github_graphql(token, query, {"q": search_q})


def rest_search_user_discussions(
    token: str, owner: str, repo: str, author: str
) -> dict:
    """REST fallback — used only to distinguish private/unsearchable users from genuine zero results."""
    q = f"repo:{owner}/{repo} type:discussions author:{author}"
    url = REST_SEARCH_URL + "?q=" + urllib.parse.quote(q) + "&per_page=1"
    return github_rest_get(token, url)


def set_output(name: str, value: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if not github_output:
        print(f"::notice::OUTPUT {name}={value}")
        return
    with open(github_output, "a", encoding="utf-8") as f:
        f.write(f"{name}={value}\n")


def main() -> int:
    token = require_env("GITHUB_TOKEN")
    owner = require_env("OWNER")
    repo = require_env("REPO")
    current_number = int(require_env("CURRENT_DISCUSSION_NUMBER"))
    author_login = require_env("AUTHOR_LOGIN")
    is_employee = os.environ.get("IS_EMPLOYEE", "false").strip().lower() == "true"

    print("=== DEBUG (inputs) ===")
    print(f"owner/repo: {owner}/{repo}")
    print(f"author_login: {author_login}")
    print(f"current_discussion_number: {current_number}")
    print(f"is_employee: {is_employee}")
    print("======================")

    # Step 1: Skip enforcement for GitHub employees and the actions bot
    is_bot = author_login == "github-actions[bot]"
    if is_employee or is_bot:
        reason = "GitHub employee" if is_employee else "github-actions[bot]"
        print(f"Author is {reason}; skipping duplicate check.")
        set_output("has_prior", "false")
        return 0

    # Step 2: Search for this author's discussions in the target category
    try:
        gql = search_discussions_in_category(token, owner, repo, author_login)
    except RuntimeError as e:
        print(f"GraphQL search failed: {e}; fail-safe: has_prior=false.")
        set_output("has_prior", "false")
        return 0

    if "errors" in gql and gql["errors"]:
        print(f"GraphQL error response: {json.dumps(gql, indent=2)}")
        set_output("has_prior", "false")
        return 0

    search_data = (gql.get("data") or {}).get("search") or {}
    discussion_count = int(search_data.get("discussionCount") or 0)
    nodes = search_data.get("nodes") or []

    print("=== DEBUG (GraphQL search response) ===")
    print(f"discussionCount: {discussion_count}")
    for i, node in enumerate(nodes, start=1):
        print(f"  hit #{i}: discussion #{node.get('number')}")
    print("=======================================")

    if discussion_count >= 2:
        print(
            f"Found {discussion_count} discussion(s) in '{CATEGORY_NAME}' "
            f"by '{author_login}'; has_prior=true."
        )
        set_output("has_prior", "true")
        return 0

    if discussion_count == 1:
        node_number = nodes[0].get("number") if nodes else None
        if node_number == current_number:
            print("Only the current discussion found in category; has_prior=false.")
            set_output("has_prior", "false")
        else:
            print(
                f"Found prior discussion #{node_number} in '{CATEGORY_NAME}' "
                f"by '{author_login}'; has_prior=true."
            )
            set_output("has_prior", "true")
        return 0

    # discussion_count == 0 — could be a private/unsearchable user or genuinely no prior discussions.
    # Fall back to REST search to distinguish these two cases.
    print(
        "GraphQL returned 0 results; falling back to REST search "
        "to detect private/unsearchable users..."
    )
    try:
        rest = rest_search_user_discussions(token, owner, repo, author_login)
        total_count = int(rest.get("total_count", 0) or 0)
        print(f"REST total_count (repo-wide): {total_count}")
        # REST succeeded — user is searchable. GraphQL returned 0 for the specific category,
        # so no prior introduction exists.
        set_output("has_prior", "false")
        return 0
    except RuntimeError as e:
        error_str = str(e)
        if "REST request failed (422)" in error_str:
            print("User is private/unsearchable (REST 422); fail-safe: has_prior=false.")
        else:
            print(f"REST search error (fail-safe: has_prior=false): {e}")
        set_output("has_prior", "false")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        # Fail-safe: never block on error, surface it in logs
        set_output("has_prior", "false")
        sys.exit(0)

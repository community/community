import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise RuntimeError(f"Missing required env var: {name}")
    return value.strip()


def github_api_request(url: str, token: str, method: str = "GET", body: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "first-time-discussion-author-check",
    }

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            parsed = json.loads(raw) if raw else {}
        except Exception:
            parsed = {"message": raw or str(e)}
        parsed["_http_status"] = e.code
        raise urllib.error.HTTPError(e.url, e.code, e.msg, e.hdrs, None) from RuntimeError(json.dumps(parsed))


def graphql_search_discussions(token: str, owner: str, repo: str, username: str) -> dict:
    url = "https://api.github.com/graphql"
    query = (
        "query($q: String!) {"
        "  search(query: $q, type: DISCUSSION, first: 2) {"
        "    discussionCount"
        "    nodes { ... on Discussion { number url title } }"
        "  }"
        "}"
    )
    search_q = f"repo:{owner}/{repo} author:{username}"
    body = {"query": query, "variables": {"q": search_q}}
    return github_api_request(url, token, method="POST", body=body)


def rest_search_discussions(token: str, owner: str, repo: str, username: str) -> dict:
    # Search issues endpoint covers discussions via type:discussions
    q = f"repo:{owner}/{repo} type:discussions author:{username}"
    url = "https://api.github.com/search/issues?q=" + urllib.parse.quote(q) + "&per_page=1"
    return github_api_request(url, token, method="GET")


def write_output(name: str, value: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        # Local/dev fallback
        print(f"::notice::OUTPUT {name}={value}")
        return
    with open(github_output, "a", encoding="utf-8") as f:
        f.write(f"{name}={value}\n")


def main() -> int:
    token = require_env("GITHUB_TOKEN")

    # This script is intended to run only for discussion.created in the CURRENT repo.
    username = require_env("USERNAME")
    owner = require_env("OWNER")
    repo = require_env("REPO")

    current_discussion_number_raw = require_env("CURRENT_DISCUSSION_NUMBER")
    current_discussion_number = int(current_discussion_number_raw)

    print("=== DEBUG (inputs) ===")
    print("owner/repo:", f"{owner}/{repo}")
    print("username:", username)
    print("current_discussion_number:", current_discussion_number_raw)
    print("======================")

    # Defaults
    should_welcome = "false"
    status = "inconclusive"
    reason = ""

    # 1) GraphQL search once
    try:
        gql = graphql_search_discussions(token, owner, repo, username)
    except urllib.error.HTTPError as e:
        # Unpack the RuntimeError from the cause if present
        print("GraphQL request failed.")
        print("HTTP status:", getattr(e, "code", "unknown"))
        if e.__cause__:
            print("cause:", str(e.__cause__))

        status = "error"
        reason = "graphql_error"
        write_output("should_welcome", should_welcome)
        write_output("status", status)
        write_output("reason", reason)
        return 0

    if "errors" in gql and gql["errors"]:
        print("GraphQL error response:")
        print(json.dumps(gql, indent=2))

        status = "error"
        reason = "graphql_error_response"
        write_output("should_welcome", should_welcome)
        write_output("status", status)
        write_output("reason", reason)
        return 0

    discussion_count = int(gql["data"]["search"].get("discussionCount") or 0)
    nodes = gql["data"]["search"]["nodes"]
    
    print("=== DEBUG (GraphQL response) ===")
    print("discussionCount:", discussion_count)
    for index, node in enumerate(nodes, start=1):
        print(f"GraphQL hit #{index}: #{node['number']} {node['url']}")
    print("===============================")
    
    # Discussion-created logic:
    # - If we see 2+ discussions, they are not first-time.
    # - If we see exactly 1 discussion and it's the current discussion, they are first-time.
    # - If we see 0, fall back to REST.
    
    if discussion_count >= 2:
        write_output("should_welcome", "false")
        print("Prior discussions found")
        return 0
    
    elif discussion_count == 1:
        # assumes nodes[0] exists and has "number"
        if nodes[0]["number"] == current_discussion_number:
            write_output("should_welcome", "true")
            print("Only current discussion found")
            return 0
            
        else:
            write_output("should_welcome", "false")
            print("Single discussion but not current")
            return 0
    
    else:
        # discussion_count == 0 => fall back to REST below
        pass

    # 2) REST fallback for diagnostic/private/unsearchable handling
    print("GraphQL returned 0; falling back to REST search for diagnostic signal...")
    try:
        rest = rest_search_discussions(token, owner, repo, username)
    except urllib.error.HTTPError as e:
        print("=== DEBUG (REST error) ===")
        print("HTTP status:", getattr(e, "code", "unknown"))
        if e.__cause__:
            cause_text = str(e.__cause__)
            print("cause:", cause_text)
            try:
                parsed = json.loads(cause_text)
            except Exception:
                parsed = {}

            # Detect the specific 422 validation failure: "cannot be searched..."
            if parsed.get("_http_status") == 422 and str(parsed.get("message", "")).lower() == "validation failed":
                errors = parsed.get("errors") or []
                first_message = (errors[0].get("message") if errors else "") or ""
                if "cannot be searched" in first_message.lower():
                    print("RESULT: SKIP — user appears unsearchable (private/staff/hidden).")
                    write_output("should_welcome", "false")
                    write_output("status", "skip")
                    return 0

        # Otherwise: inconclusive error
        write_output("should_welcome", "false")
        write_output("status", "inconclusive")
        write_output("reason", "rest_search_error")
        return 0

    total_count = int(rest.get("total_count") or 0)
    print("=== DEBUG (REST response) ===")
    print("total_count:", total_count)
    print("=============================")

    if total_count > 0:
        write_output("should_welcome", "false")
        write_output("status", "conclusive")
        write_output("reason", "prior_discussions_found_rest")
        return 0

    # Still ambiguous
    write_output("should_welcome", "false")
    write_output("status", "inconclusive")
    write_output("reason", "graphql_and_rest_zero")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # Fail-safe: never welcome on crash, but surface error in logs.
        print("ERROR:", str(exc))
        write_output("should_welcome", "false")
        write_output("status", "error")
        write_output("reason", "script_crash")
        sys.exit(0)

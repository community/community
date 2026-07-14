"""
Validates that a newly created GitHub Discussion was submitted through the UI
(i.e., via a discussion template) rather than directly through the API.

Logic:
  1. If the discussion carries the 'source:ui' label (applied automatically by
     every discussion template), set SHOULD_PROCEED to 'true' and return.
  2. Otherwise the discussion lacks 'source:ui', meaning it was created via the
     API/GraphQL rather than the UI template.
     a. If the author is a GitHub employee (IS_EMPLOYEE=true) or any bot account
        (login ending with '[bot]'):
          - Apply the 'source:other' label for tracking purposes.
          - Set SHOULD_PROCEED to 'true' so that labeling still runs.
          - Do NOT close or comment — trusted authors are allowed to submit
            via the API (e.g. automated integration tests, staff tooling).
     b. For all other authors:
          - Apply the 'source:other' label.
          - Post a comment explaining that only UI/template submissions are
            accepted.
          - Close the discussion.
          - Set SHOULD_PROCEED to 'false'.

Required environment variables:
    GITHUB_TOKEN          - Token with discussion read/write permission
    OWNER                 - Repository owner (org or user)
    REPO                  - Repository name
    DISCUSSION_NODE_ID    - The GraphQL node ID of the discussion
    DISCUSSION_LABELS     - JSON array of label name strings currently on the discussion
    AUTHOR_LOGIN          - GitHub login of the discussion author
    IS_EMPLOYEE           - 'true' if the author is a GitHub org member, else 'false'
    GITHUB_OUTPUT         - Path to the GitHub Actions output file (set automatically)
"""

import json
import os
import sys
import urllib.error
import urllib.request

GRAPHQL_URL = "https://api.github.com/graphql"

CLOSE_COMMENT = (
    "Thank you for your interest in contributing to our community! "
    "We currently only accept discussions created through the GitHub UI "
    "using our provided discussion templates. Please re-submit your discussion "
    "by navigating to the appropriate category and using the template provided.\n\n"
    "This discussion has been closed because it was not submitted through the "
    "expected format. If you believe this was a mistake, please reach out to "
    "the maintainers."
)


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise RuntimeError(f"Missing required env var: {name}")
    return value.strip()


def github_graphql(token: str, query: str, variables: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "discussion-source-check",
    }
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(GRAPHQL_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"GraphQL request failed ({e.code}): {raw}") from e
    if result.get("errors"):
        errors = result["errors"]
        if isinstance(errors, list):
            messages = "; ".join(e.get("message", str(e)) if isinstance(e, dict) else str(e) for e in errors)
        else:
            messages = str(errors)
        raise RuntimeError(f"GraphQL errors: {messages}")
    if result.get("data") is None:
        raise RuntimeError("GraphQL response missing 'data' field")
    return result


def fetch_label_id(token: str, owner: str, repo: str, label_name: str) -> str | None:
    """Return the node ID of a label by exact name, or None if not found."""
    query = """
    query($owner: String!, $name: String!, $label: String) {
      repository(owner: $owner, name: $name) {
        labels(first: 5, query: $label) {
          edges {
            node { id name }
          }
        }
      }
    }
    """
    resp = github_graphql(token, query, {"owner": owner, "name": repo, "label": label_name})
    edges = resp["data"]["repository"]["labels"]["edges"]
    for edge in edges:
        node = edge["node"]
        if node["name"] == label_name:
            print(f"Label matched: '{node['name']}' (ID: {node['id']})")
            return node["id"]
    return None


def apply_label(token: str, discussion_id: str, label_id: str) -> None:
    mutation = """
    mutation($labelableId: ID!, $labelIds: [ID!]!) {
      addLabelsToLabelable(input: {labelableId: $labelableId, labelIds: $labelIds}) {
        labelable {
          labels(first: 10) {
            edges { node { id name } }
          }
        }
      }
    }
    """
    resp = github_graphql(
        token,
        mutation,
        {"labelableId": discussion_id, "labelIds": [label_id]},
    )
    applied = [
        e["node"]["name"]
        for e in resp["data"]["addLabelsToLabelable"]["labelable"]["labels"]["edges"]
    ]
    print(f"Labels now applied: {applied}")


def add_comment(token: str, discussion_id: str, body: str) -> None:
    mutation = """
    mutation($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
        comment { id }
      }
    }
    """
    github_graphql(token, mutation, {"discussionId": discussion_id, "body": body})
    print("Comment posted.")


def close_discussion(token: str, discussion_id: str) -> None:
    mutation = """
    mutation($discussionId: ID!) {
      closeDiscussion(input: {discussionId: $discussionId, reason: OUTDATED}) {
        discussion { closed }
      }
    }
    """
    resp = github_graphql(token, mutation, {"discussionId": discussion_id})
    closed = resp["data"]["closeDiscussion"]["discussion"]["closed"]
    print(f"Discussion closed: {closed}")


def set_output(name: str, value: str) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT", "")
    if not output_file:
        raise RuntimeError("GITHUB_OUTPUT environment variable is not set")
    with open(output_file, "a") as f:
        f.write(f"{name}={value}\n")


def main() -> int:
    token = require_env("GITHUB_TOKEN")
    owner = require_env("OWNER")
    repo = require_env("REPO")
    discussion_node_id = require_env("DISCUSSION_NODE_ID")
    author_login = require_env("AUTHOR_LOGIN")
    is_employee = os.environ.get("IS_EMPLOYEE", "false").strip().lower() == "true"
    discussion_labels_raw = os.environ.get("DISCUSSION_LABELS", "[]").strip()

    print(f"Discussion node ID: {discussion_node_id}")
    print(f"Author: {author_login}")
    print(f"Is employee: {is_employee}")

    # Step 1: Check for the source:ui label
    try:
        labels = json.loads(discussion_labels_raw)
    except json.JSONDecodeError:
        print(
            f"Warning: Could not parse DISCUSSION_LABELS as JSON: {discussion_labels_raw!r}. "
            "Failing open to avoid incorrectly closing a legitimate discussion."
        )
        set_output("should_proceed", "true")
        return 0

    has_source_ui = "source:ui" in labels
    print(f"Labels on discussion: {labels}")
    print(f"Has 'source:ui' label: {has_source_ui}")

    if has_source_ui:
        print("Discussion was created via the UI; proceeding with labeling.")
        set_output("should_proceed", "true")
        return 0

    # Step 2: Discussion lacks source:ui — determine how to handle it
    print("Discussion lacks 'source:ui' label; treating as API-created submission.")

    # Bots (any login ending with '[bot]') and verified GitHub employees are
    # trusted authors (e.g. automated integration tests, staff tooling).
    # Apply source:other for tracking but still allow labeling to proceed;
    # do NOT close or comment.
    is_bot = author_login.endswith("[bot]")
    if is_employee or is_bot:
        reason = "GitHub employee" if is_employee else f"bot ({author_login})"
        print(f"Author is {reason}; applying source:other but proceeding without closing.")
        source_other_id = fetch_label_id(token, owner, repo, "source:other")
        if source_other_id:
            apply_label(token, discussion_node_id, source_other_id)
        else:
            print("Warning: 'source:other' label not found in repository; skipping label.")
        set_output("should_proceed", "true")
        return 0

    # Step 3: Unknown author without source:ui — apply source:other, comment, and close
    source_other_id = fetch_label_id(token, owner, repo, "source:other")
    if source_other_id:
        apply_label(token, discussion_node_id, source_other_id)
    else:
        print("Warning: 'source:other' label not found in repository; skipping label.")

    add_comment(token, discussion_node_id, CLOSE_COMMENT)

    close_discussion(token, discussion_node_id)

    set_output("should_proceed", "false")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

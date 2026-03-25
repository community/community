"""
Reads the "Discussion Type" field from a GitHub Discussion body (Markdown),
looks up the matching repository label, and applies it to the discussion.

Required environment variables:
    GITHUB_TOKEN        - Personal access token with discussion write permission
    OWNER               - Repository owner (org or user)
    REPO                - Repository name
    DISCUSSION_BODY     - The Markdown body of the discussion (github.event.discussion.body)
    DISCUSSION_NODE_ID  - The node ID of the discussion (github.event.discussion.node_id)
"""

import json
import os
import sys
import urllib.error
import urllib.request

# Heading aliases recognised as "Discussion Type" headers.
# The emoji-prefixed form ("🏷️ discussion type") is the canonical heading used in all
# current templates; the plain-text aliases are kept for backwards compatibility with
# discussions submitted before the emoji was introduced.
TYPE_HEADINGS = {
    "🏷️ discussion type",
    "discussion type",
    "select topic area",
    "reason for posting",
    "why are you starting this discussion?",
}

# Values that correspond to repository labels
VALID_TOPICS = {"product feedback", "question", "bug"}

GRAPHQL_URL = "https://api.github.com/graphql"


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.strip():
        raise RuntimeError(f"Missing required env var: {name}")
    return value.strip()


def github_graphql(token: str, query: str, variables: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "reason-for-posting-labeler",
    }
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(GRAPHQL_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"GraphQL request failed ({e.code}): {raw}") from e


def extract_discussion_type(body: str) -> str:
    """Parse discussion Markdown body and return the validated 'Discussion Type' value.

    GitHub Discussion form templates render submitted answers as:
        ### Heading
        (blank line)
        Answer
    """
    lines = body.splitlines()
    found_heading = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            heading = stripped[4:].strip().lower()
            found_heading = heading in TYPE_HEADINGS
            continue
        if found_heading and stripped:
            topic = stripped.lower()
            if topic in VALID_TOPICS:
                return topic
            found_heading = False  # non-matching answer; reset and keep searching
    return ""


def fetch_label_id(token: str, owner: str, repo: str, topic: str) -> str | None:
    """Return the node ID of the first label matching *topic*, or None."""
    query = """
    query($owner: String!, $name: String!, $topic: String) {
      repository(owner: $owner, name: $name) {
        labels(first: 1, query: $topic) {
          edges {
            node { id name }
          }
        }
      }
    }
    """
    resp = github_graphql(token, query, {"owner": owner, "name": repo, "topic": topic})
    if "errors" in resp and resp["errors"]:
        raise RuntimeError(f"GraphQL error in fetch_label_id: {json.dumps(resp['errors'])}")
    edges = (
        (resp.get("data") or {})
        .get("repository", {})
        .get("labels", {})
        .get("edges", [])
    )
    if not edges:
        return None
    node = edges[0]["node"]
    print(f"Label matched: '{node['name']}' (ID: {node['id']})")
    return node["id"]


def apply_label(token: str, discussion_id: str, label_id: str) -> None:
    """Add *label_id* to the discussion identified by *discussion_id*."""
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
    if "errors" in resp and resp["errors"]:
        raise RuntimeError(f"GraphQL error in apply_label: {json.dumps(resp['errors'])}")
    applied = [
        e["node"]["name"]
        for e in (resp.get("data") or {})
        .get("addLabelsToLabelable", {})
        .get("labelable", {})
        .get("labels", {})
        .get("edges", [])
    ]
    print(f"Labels now applied: {applied}")


def main() -> int:
    token = require_env("GITHUB_TOKEN")
    owner = require_env("OWNER")
    repo = require_env("REPO")
    discussion_body = require_env("DISCUSSION_BODY")
    discussion_node_id = require_env("DISCUSSION_NODE_ID")

    print(f"Discussion node ID: {discussion_node_id}")

    topic = extract_discussion_type(discussion_body)
    print(f"Selected topic: '{topic}'")

    if not topic:
        print("No valid 'Discussion Type' topic found; skipping labeling.")
        return 0

    label_id = fetch_label_id(token, owner, repo, topic)
    if not label_id:
        print(f"No label found for topic '{topic}'; skipping labeling.")
        return 0

    apply_label(token, discussion_node_id, label_id)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

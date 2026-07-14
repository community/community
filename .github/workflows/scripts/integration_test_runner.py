"""
End-to-end integration test runner for workflow scripts.

Creates real GitHub Discussions in this repository to exercise the automated
workflow scripts, waits for those workflows to run, verifies the expected
outcomes, then closes every test discussion to keep the repository clean.

--- Token choice: primary token (GITHUB_TOKEN / STAFF_DISCUSSIONS_PAT) ---

The workflow uses STAFF_DISCUSSIONS_PAT — a PAT belonging to a GitHub staff
member (or a bot account whose login ends with '[bot]').  This is required
because the built-in github.token (job token) does NOT trigger downstream
workflow runs; only a PAT or App token causes the discussion:created event
to fire label-templated-discussions.yml.

source_check.py handles these trusted authors as follows:
  - Verified GitHub employee (IS_EMPLOYEE=true): applies source:other label
    for tracking and sets should_proceed=true — no close or comment.
  - Bot account (login ending with '[bot]'): same trusted path.
  - source:ui will NOT be present (GraphQL API creation) — this is accepted.

--- Source-rejection path: IT-6 (NON_STAFF_TOKEN) ---

IT-6 exercises source_check.py's rejection path.  It requires NON_STAFF_TOKEN
(populated from NON_STAFF_DISCUSSIONS_PAT) — a PAT whose owner is neither a
GitHub employee nor a bot account.  The discussion is created without a
source:ui label, so source_check.py applies source:other, posts a comment, and
closes the discussion.  IT-6 verifies all three outcomes.  When NON_STAFF_TOKEN
is absent IT-6 is reported as SKIP.

source:ui behaviour (the path where a discussion was submitted through the
GitHub UI template) must be tested manually.

Timing: triggered workflows run asynchronously. WAIT_SECONDS (default 90)
gives the labeler jobs enough time to start, check out code, and apply labels.
Flaky failures due to GitHub Actions queueing can be retried by re-running the
workflow with a larger wait value.

Cleanup: GitHub's API does not allow deleting discussions, only closing them.
All test discussions are created with the "[IT]" title prefix so the cleanup
step (and the standalone cleanup_only mode) can identify and close them.

Required environment variables:
    GITHUB_TOKEN      — Staff member PAT (STAFF_DISCUSSIONS_PAT) or bot App
                        token; must NOT be the built-in github.token as that
                        will not trigger downstream labeler workflows.
                        Used to create IT-1 – IT-5 and to read/clean up
                        all test discussions.
    NON_STAFF_TOKEN   — Optional PAT for a non-staff, non-bot account; enables
                        IT-6 (source-rejection path).  Set from
                        NON_STAFF_DISCUSSIONS_PAT repository secret.
    OWNER             — Repository owner
    REPO              — Repository name
    CATEGORY          — Discussion category to post in (default: Actions)
    WAIT_SECONDS      — Seconds to wait for triggered workflows (default: 90)
    CLEANUP_ONLY      — If 'true', close all open [IT] discussions and exit
    DRY_RUN           — If 'true', print scenario list without creating anything
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

GRAPHQL_URL = "https://api.github.com/graphql"
TEST_TITLE_PREFIX = "[IT]"
DEFAULT_CATEGORY = "Actions"
DEFAULT_WAIT_SECONDS = 90

# ---------------------------------------------------------------------------
# Template helpers — used to build category-aware test scenarios
# ---------------------------------------------------------------------------

def _category_to_template_slug(category: str) -> str:
    """Convert a category display name to its discussion template file slug.

    Example: "Copilot Conversations" → "copilot-conversations"
    """
    return re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")


def _load_feature_topic_option(category: str) -> str | None:
    """Return the first Feature/Topic Area option from the category's template.

    Reads the YAML discussion template for *category* and returns the first
    option listed under the "💬 Feature/Topic Area" dropdown.  Returns None
    when no template is found or the template has no such dropdown.
    """
    slug = _category_to_template_slug(category)
    templates_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "DISCUSSION_TEMPLATE")
    )
    template_path = os.path.join(templates_dir, f"{slug}.yml")
    if not os.path.exists(template_path):
        return None
    try:
        import yaml  # PyYAML — available on ubuntu-latest GitHub-hosted runners
    except ImportError:
        return None
    try:
        with open(template_path, encoding="utf-8") as fh:
            template = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError):
        return None
    for item in template.get("body") or []:
        if item.get("type") != "dropdown":
            continue
        label = str((item.get("attributes") or {}).get("label") or "").lower()
        if "feature/topic area" in label:
            options = (item.get("attributes") or {}).get("options") or []
            return str(options[0]).strip("\"'") if options else None
    return None


# ---------------------------------------------------------------------------
# Test scenarios
#
# IT-1 / IT-2 / IT-3 verify the Discussion Type labeler.
# IT-4 verifies the Feature/Topic Area labeler using an option taken directly
#   from the selected category's discussion template so the label is always
#   relevant to the category under test.
# IT-5 verifies that no type label is applied when the heading is absent.
# IT-6 verifies the source-rejection path: a discussion created without
#   source:ui by a non-staff, non-bot author is closed with source:other and
#   a comment.  Requires NON_STAFF_TOKEN; reported as SKIP when absent.
# ---------------------------------------------------------------------------

def build_test_scenarios(
    category: str,
    non_staff_token: str | None = None,
) -> list[dict]:
    """Return the list of test scenarios tailored to *category*.

    IT-4 is built from the first Feature/Topic Area option in the category's
    discussion template.  If no such option exists the scenario still runs
    but will likely be reported as SKIP (label absent from the repository).

    IT-6 is included when *non_staff_token* is provided; otherwise it is
    pre-marked as SKIP.
    """
    feature_topic_option = _load_feature_topic_option(category)

    scenarios = [
        {
            "id": "IT-1",
            "description": "Bug label applied from ### 🏷️ Discussion Type = Bug",
            "title": f"{TEST_TITLE_PREFIX} Automated test — Bug label",
            "body": (
                "### 🏷️ Discussion Type\n\nBug\n\n"
                "### Discussion Details\n\n"
                "Automated integration test. Safe to close."
            ),
            "expected_labels": ["Bug"],
        },
        {
            "id": "IT-2",
            "description": "Question label applied from ### 🏷️ Discussion Type = Question",
            "title": f"{TEST_TITLE_PREFIX} Automated test — Question label",
            "body": (
                "### 🏷️ Discussion Type\n\nQuestion\n\n"
                "### Discussion Details\n\n"
                "Automated integration test. Safe to close."
            ),
            "expected_labels": ["Question"],
        },
        {
            "id": "IT-3",
            "description": "Product Feedback label applied from ### 🏷️ Discussion Type",
            "title": f"{TEST_TITLE_PREFIX} Automated test — Product Feedback label",
            "body": (
                "### 🏷️ Discussion Type\n\nProduct Feedback\n\n"
                "### Discussion Details\n\n"
                "Automated integration test. Safe to close."
            ),
            "expected_labels": ["Product Feedback"],
        },
    ]

    # Build IT-4 using a Feature/Topic Area option from the category's template.
    if feature_topic_option:
        description = (
            f"Feature/Topic Area label applied alongside Discussion Type "
            f"({feature_topic_option!r} from {category} template)"
        )
        title = f"{TEST_TITLE_PREFIX} Automated test — {feature_topic_option[:40]} label"
        body = (
            "### 🏷️ Discussion Type\n\nQuestion\n\n"
            f"### 💬 Feature/Topic Area\n\n{feature_topic_option}\n\n"
            "### Discussion Details\n\n"
            "Automated integration test. Safe to close."
        )
        expected = ["Question", feature_topic_option]
    else:
        description = (
            "Feature/Topic Area label applied alongside Discussion Type "
            "(no template options found for this category)"
        )
        title = f"{TEST_TITLE_PREFIX} Automated test — feature/topic area label"
        body = (
            "### 🏷️ Discussion Type\n\nQuestion\n\n"
            "### 💬 Feature/Topic Area\n\n_No option available_\n\n"
            "### Discussion Details\n\n"
            "Automated integration test. Safe to close."
        )
        expected = ["Question"]

    scenarios.append({
        "id": "IT-4",
        "description": description,
        "title": title,
        "body": body,
        "expected_labels": expected,
    })

    scenarios.append({
        "id": "IT-5",
        "description": "No Discussion Type heading → no type label applied",
        "title": f"{TEST_TITLE_PREFIX} Automated test — no type label",
        "body": (
            "### Discussion Details\n\n"
            "Automated integration test. Safe to close.\n"
            "This discussion deliberately has no Discussion Type heading."
        ),
        "expected_labels": [],
    })

    # IT-6: source-rejection path.  Requires a non-staff, non-bot token.
    if non_staff_token:
        it6_skip_reason = None
    else:
        it6_skip_reason = "NON_STAFF_TOKEN is not set; configure NON_STAFF_DISCUSSIONS_PAT secret to enable"

    scenarios.append({
        "id": "IT-6",
        "description": (
            "API-submitted discussion (no source:ui, non-staff author) → "
            "closed with source:other label and comment"
        ),
        "title": f"{TEST_TITLE_PREFIX} Automated test — source rejection",
        "body": (
            "### Discussion Details\n\n"
            "Automated integration test. Safe to close.\n"
            "This discussion is intentionally submitted without source:ui "
            "to exercise the rejection path in source_check.py."
        ),
        "expected_labels": ["source:other"],
        "expected_closed": True,
        "expected_comment": True,
        "creation_token": non_staff_token,
        "skip_reason": it6_skip_reason,
    })

    return scenarios


# ---------------------------------------------------------------------------
# GraphQL helpers
# ---------------------------------------------------------------------------

def graphql(token: str, query: str, variables: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "integration-test-runner",
    }
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(GRAPHQL_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"GraphQL HTTP {e.code}: {raw}") from e
    if result.get("errors"):
        raise RuntimeError(f"GraphQL errors: {json.dumps(result['errors'])}")
    if result.get("data") is None:
        raise RuntimeError(f"GraphQL response missing 'data': {json.dumps(result)}")
    return result["data"]


def get_repo_and_category(
    token: str, owner: str, repo: str, category_name: str
) -> tuple[str, str]:
    """Return (repo_node_id, category_node_id) for the given category name."""
    data = graphql(
        token,
        """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            id
            discussionCategories(first: 50) {
              nodes { id name }
            }
          }
        }
        """,
        {"owner": owner, "repo": repo},
    )
    repo_id = data["repository"]["id"]
    categories = data["repository"]["discussionCategories"]["nodes"]
    category = next((c for c in categories if c["name"] == category_name), None)
    if category is None:
        available = [c["name"] for c in categories]
        raise RuntimeError(
            f"Category '{category_name}' not found. "
            f"Available categories: {available}"
        )
    return repo_id, category["id"]


def check_labels_exist(
    token: str, owner: str, repo: str, label_names: list[str]
) -> dict[str, bool]:
    """Return a mapping of label_name → exists for each name in label_names."""
    if not label_names:
        return {}
    # Paginate through all repository labels so that repos with more than 100
    # labels are handled correctly.
    existing: set[str] = set()
    cursor = None
    while True:
        variables: dict = {"owner": owner, "repo": repo, "cursor": cursor}
        data = graphql(
            token,
            """
            query($owner: String!, $repo: String!, $cursor: String) {
              repository(owner: $owner, name: $repo) {
                labels(first: 100, after: $cursor) {
                  nodes { name }
                  pageInfo { hasNextPage endCursor }
                }
              }
            }
            """,
            variables,
        )
        labels_page = data["repository"]["labels"]
        existing.update(n["name"] for n in labels_page["nodes"])
        page_info = labels_page["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
    return {name: name in existing for name in label_names}


def create_discussion(
    token: str,
    repo_id: str,
    category_id: str,
    title: str,
    body: str,
) -> tuple[str, int, str]:
    """Create a discussion and return (node_id, number, url)."""
    data = graphql(
        token,
        """
        mutation($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
          createDiscussion(input: {
            repositoryId: $repoId
            categoryId: $categoryId
            title: $title
            body: $body
          }) {
            discussion { id number url }
          }
        }
        """,
        {
            "repoId": repo_id,
            "categoryId": category_id,
            "title": title,
            "body": body,
        },
    )
    d = data["createDiscussion"]["discussion"]
    return d["id"], d["number"], d["url"]


def fetch_discussion_state(
    token: str, owner: str, repo: str, number: int
) -> dict:
    """Fetch the current label and closed state of a discussion."""
    data = graphql(
        token,
        """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            discussion(number: $number) {
              id
              closed
              labels(first: 20) {
                nodes { name }
              }
              comments(first: 1) {
                totalCount
              }
            }
          }
        }
        """,
        {"owner": owner, "repo": repo, "number": number},
    )
    return data["repository"]["discussion"]


def close_discussion(token: str, node_id: str) -> None:
    """Close a discussion (GitHub does not support deletion via the API)."""
    graphql(
        token,
        """
        mutation($discussionId: ID!) {
          closeDiscussion(input: {discussionId: $discussionId, reason: RESOLVED}) {
            discussion { closed }
          }
        }
        """,
        {"discussionId": node_id},
    )


def find_open_test_discussions(
    token: str, owner: str, repo: str
) -> list[dict]:
    """Return all open discussions whose title starts with TEST_TITLE_PREFIX."""
    data = graphql(
        token,
        """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            discussions(first: 100, states: [OPEN]) {
              nodes { id number title url }
            }
          }
        }
        """,
        {"owner": owner, "repo": repo},
    )
    return [
        d
        for d in data["repository"]["discussions"]["nodes"]
        if d["title"].startswith(TEST_TITLE_PREFIX)
    ]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def run_cleanup(token: str, owner: str, repo: str) -> None:
    """Close all open test discussions (identified by the [IT] prefix)."""
    print(f"Searching for open discussions prefixed '{TEST_TITLE_PREFIX}'...")
    test_discussions = find_open_test_discussions(token, owner, repo)
    if not test_discussions:
        print("No open test discussions found.")
        return
    print(f"Found {len(test_discussions)} open test discussion(s) to close:")
    for d in test_discussions:
        print(f"  #{d['number']}: {d['title']} — {d['url']}")
        close_discussion(token, d["id"])
        print(f"  ✓ Closed #{d['number']}")
    print(f"Cleanup complete: {len(test_discussions)} discussion(s) closed.")


def verify_scenario(
    scenario: dict,
    state: dict,
    repo_labels: dict[str, bool],
) -> tuple[str, list[str]]:
    """
    Return (result, messages) where result is 'pass', 'fail', or 'skip'.

    'skip' is returned when:
    - scenario has a pre-determined skip_reason (e.g. missing token), or
    - an expected label does not exist in the repository (the labeler
      correctly finds nothing to apply, so the test cannot meaningfully pass
      or fail).
    """
    if scenario.get("skip_reason"):
        return "skip", [f"SKIP: {scenario['skip_reason']}"]

    applied = {n["name"] for n in state["labels"]["nodes"]}
    messages = []

    for expected in scenario["expected_labels"]:
        if not repo_labels.get(expected):
            messages.append(
                f"SKIP: label '{expected}' does not exist in this repository "
                f"(labeler correctly skips it)"
            )
            return "skip", messages
        if expected not in applied:
            messages.append(
                f"FAIL: expected label '{expected}' not applied. "
                f"Labels present: {sorted(applied)}"
            )

    if scenario.get("expected_closed") and not state.get("closed"):
        messages.append("FAIL: expected discussion to be closed, but it is still open")

    if scenario.get("expected_comment"):
        comment_count = (state.get("comments") or {}).get("totalCount", 0)
        if comment_count == 0:
            messages.append("FAIL: expected a comment to be posted, but none found")

    if any(m.startswith("FAIL") for m in messages):
        return "fail", messages
    return "pass", messages


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    non_staff_token = os.environ.get("NON_STAFF_TOKEN", "").strip() or None
    owner = os.environ.get("OWNER", "").strip()
    repo = os.environ.get("REPO", "").strip()
    category = os.environ.get("CATEGORY", DEFAULT_CATEGORY).strip()
    wait_seconds = int(os.environ.get("WAIT_SECONDS", DEFAULT_WAIT_SECONDS))
    cleanup_only = os.environ.get("CLEANUP_ONLY", "false").strip().lower() == "true"
    dry_run = os.environ.get("DRY_RUN", "false").strip().lower() == "true"

    if not token:
        print("ERROR: GITHUB_TOKEN is not set")
        return 1
    if not owner or not repo:
        print("ERROR: OWNER and REPO must both be set")
        return 1

    print(f"Repository   : {owner}/{repo}")
    print(f"Category     : {category}")
    print(f"Wait seconds : {wait_seconds}")
    print(f"Cleanup only : {cleanup_only}")
    print(f"Dry run      : {dry_run}")
    print(f"Non-staff PAT: {'yes (IT-6 enabled)' if non_staff_token else 'no (IT-6 will be SKIP)'}")
    print()

    # ── Cleanup-only mode ─────────────────────────────────────────────────
    if cleanup_only:
        run_cleanup(token, owner, repo)
        return 0

    # ── Dry-run mode ──────────────────────────────────────────────────────
    if dry_run:
        print("DRY RUN — would create the following discussions:")
        for s in build_test_scenarios(category, non_staff_token):
            skip_note = f" [SKIP: {s['skip_reason']}]" if s.get("skip_reason") else ""
            print(f"  {s['id']}: {s['title']}{skip_note}")
            print(f"    Expected labels : {s['expected_labels']}")
        return 0

    # ── Resolve repository and category IDs ───────────────────────────────
    print(f"Fetching repository info and '{category}' category ID...")
    try:
        repo_id, category_id = get_repo_and_category(token, owner, repo, category)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return 1
    print(f"  Repo node ID     : {repo_id}")
    print(f"  Category node ID : {category_id}")
    print()

    # ── Build category-specific test scenarios ────────────────────────────
    test_scenarios = build_test_scenarios(category, non_staff_token)

    # ── Check which expected labels exist in the repository ───────────────
    all_expected = list({
        lbl
        for s in test_scenarios
        for lbl in s["expected_labels"]
    })
    repo_labels = check_labels_exist(token, owner, repo, all_expected)
    missing = [lbl for lbl, exists in repo_labels.items() if not exists]
    if missing:
        print(
            f"Note: the following expected labels are not present in this "
            f"repository — related test scenarios will be reported as SKIP:\n"
            f"  {missing}\n"
        )

    # ── Create test discussions ───────────────────────────────────────────
    created: list[dict] = []
    print(f"Creating {len(test_scenarios)} test discussion(s) in '{category}'...")
    for scenario in test_scenarios:
        if scenario.get("skip_reason"):
            created.append({**scenario, "node_id": None, "number": None, "url": None})
            print(f"  ~ {scenario['id']} — SKIP: {scenario['skip_reason']}")
            continue
        creation_token = scenario.get("creation_token") or token
        try:
            node_id, number, url = create_discussion(
                creation_token, repo_id, category_id, scenario["title"], scenario["body"]
            )
            created.append({**scenario, "node_id": node_id, "number": number, "url": url})
            print(f"  ✓ {scenario['id']} — #{number} {url}")
        except RuntimeError as e:
            print(f"  ✗ {scenario['id']} — creation failed: {e}")
            created.append({**scenario, "node_id": None, "number": None, "url": None, "create_error": str(e)})
    print()

    # ── Wait for triggered labeler workflows ─────────────────────────────
    print(
        f"Waiting {wait_seconds}s for label-templated-discussions.yml "
        f"and its downstream labeler workflows to run..."
    )
    time.sleep(wait_seconds)
    print()

    # ── Verify outcomes ───────────────────────────────────────────────────
    results: list[dict] = []
    print("Verifying discussion states...")
    for item in created:
        if item.get("skip_reason"):
            print(f"  ~ SKIP  {item['id']}: {item['skip_reason']}")
            results.append({"id": item["id"], "result": "skip", "messages": [f"SKIP: {item['skip_reason']}"]})
            continue

        if item.get("create_error"):
            print(f"  SKIP  {item['id']}: creation failed — {item['create_error']}")
            results.append({"id": item["id"], "result": "fail", "messages": [f"Creation failed: {item['create_error']}"]})
            continue

        try:
            state = fetch_discussion_state(token, owner, repo, item["number"])
        except RuntimeError as e:
            print(f"  ERROR {item['id']}: could not fetch state — {e}")
            results.append({"id": item["id"], "result": "fail", "messages": [f"State fetch error: {e}"]})
            continue

        result, messages = verify_scenario(item, state, repo_labels)
        icon = {"pass": "✓", "fail": "✗", "skip": "~"}[result]
        print(f"  {icon} {result.upper():4s}  {item['id']}: {item['description']}")
        for msg in messages:
            print(f"         {msg}")
        results.append({"id": item["id"], "result": result, "messages": messages})
    print()

    # ── Cleanup ───────────────────────────────────────────────────────────
    print("Cleaning up — closing test discussions...")
    for item in created:
        if item.get("node_id"):
            try:
                close_discussion(token, item["node_id"])
                print(f"  ✓ Closed #{item['number']} ({item['id']})")
            except RuntimeError as e:
                print(f"  ✗ Could not close #{item['number']}: {e}")
    print()

    # ── Summary ───────────────────────────────────────────────────────────
    passed = sum(1 for r in results if r["result"] == "pass")
    skipped = sum(1 for r in results if r["result"] == "skip")
    failed = sum(1 for r in results if r["result"] == "fail")
    total = len(results)

    print("=" * 55)
    print(f"Integration Test Results  {passed} passed / {skipped} skipped / {failed} failed  (of {total})")
    print("=" * 55)
    for r in results:
        icon = {"pass": "✓", "fail": "✗", "skip": "~"}[r["result"]]
        print(f"  {icon}  {r['id']}")
        for msg in r.get("messages", []):
            print(f"     {msg}")

    if failed > 0:
        print(
            "\nNote: SKIP means a required label was absent from the repository or "
            "a required token was not configured (not a workflow bug). "
            "FAIL means an expected outcome was not observed."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

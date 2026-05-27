#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime, timezone
from urllib import error, request


def load_event_payload(event_path: str) -> dict:
    with open(event_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_target_repository(value: str) -> tuple[str, str]:
    owner, separator, repo = value.partition("/")
    if not separator or not owner or not repo:
        raise ValueError("TARGET_OPS_REPOSITORY must be set as owner/repo")
    return owner, repo


def build_trusted_staff(raw_value: str) -> set[str]:
    return {entry.strip() for entry in raw_value.split(",") if entry.strip()}


def iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_dispatch(owner: str, repo: str, token: str, event_type: str, payload: dict) -> None:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/dispatches"
    body = json.dumps(
        {
            "event_type": event_type,
            "client_payload": payload,
        }
    ).encode("utf-8")
    api_request = request.Request(
        api_url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "community-discussion-feedback-dispatch",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with request.urlopen(api_request) as response:
            if response.status != 204:
                raise RuntimeError(f"Dispatch failed with unexpected status: {response.status}")
    except error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Dispatch failed with status {exc.code}: {message}") from exc


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH is not set")

    token = os.environ.get("DISPATCH_TOKEN", "")
    if not token:
        print("COMM_COMM_OPS_DISPATCH_TOKEN is not configured; skipping ops dispatch.")
        return 0

    payload = load_event_payload(event_path)
    action = payload.get("action")
    discussion = payload.get("discussion") or {}
    label = payload.get("label") or {}
    actor = os.environ.get("GITHUB_ACTOR") or ((payload.get("sender") or {}).get("login")) or ""
    trusted_staff = build_trusted_staff(os.environ.get("PROD_TRUSTED_STAFF", ""))

    discussion_number = discussion.get("number")
    if not discussion_number:
        raise RuntimeError("Missing discussion number in discussion event payload")

    actor_type = "bot" if actor.endswith("[bot]") else "human"
    if actor_type == "bot":
        print(f"Skipping bot-generated event: {actor}")
        return 0

    dispatch_event_type = (
        "discussion-created" if action in {"created", "category_changed"} else "label-feedback"
    )

    label_name = label.get("name")
    if dispatch_event_type == "label-feedback" and not label_name:
        print("Skipping label event with missing label")
        return 0

    owner, repo = parse_target_repository(os.environ.get("TARGET_OPS_REPOSITORY", ""))
    source_repository = os.environ.get("GITHUB_REPOSITORY", "unknown/unknown")
    dispatch_payload = {
        "data": {
            "source_repository": source_repository,
            "origin_repo_role": "prod-truth",
            "discussion_number": discussion_number,
            "discussion_title": discussion.get("title") or "unknown",
            "discussion_url": discussion.get("html_url") or discussion.get("url") or "",
            "category": (discussion.get("category") or {}).get("name") or "unknown",
            "category_slug": (discussion.get("category") or {}).get("slug") or "unknown",
            "event_type": action,
            "label": label_name,
            "actor": actor,
            "actor_type": actor_type,
            "is_trusted_staff": actor in trusted_staff,
            "label_source": "manual" if dispatch_event_type == "label-feedback" else "mirror-observation",
            "createdAt": iso_timestamp(),
        }
    }
    create_dispatch(owner, repo, token, dispatch_event_type, dispatch_payload)
    print(
        f"Forwarded {action} event as {dispatch_event_type} to ops for discussion #{discussion_number}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
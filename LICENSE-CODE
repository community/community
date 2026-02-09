{
  "id": 12344191,
  "name": "danialzivehdar1992@gmail.com.",
  "target": "branch",
  "source_type": "Repository",
  "source": "danialzivehdar1992-hue/app-privacy-policy-generator",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "exclude": [],
      "include": [
        "~ALL"
      ]
    }
  },
  "rules": [
    {
      "type": "non_fast_forward"
    },
    {
      "type": "deletion"
    },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "required_reviewers": [],
        "require_code_owner_review": false,
        "require_last_push_approval": true,
        "required_review_thread_resolution": false,
        "allowed_merge_methods": [
          "merge",
          "squash",
          "rebase"
        ]
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          {
            "context": "d"
          },
          {
            "context": "prebuild",
            "integration_id": 15368
          }
        ]
      }
    },
    {
      "type": "code_scanning",
      "parameters": {
        "code_scanning_tools": [
          {
            "tool": "CodeQL",
            "security_alerts_threshold": "all",
            "alerts_threshold": "all"
          }
        ]
      }
    },
    {
      "type": "code_quality",
      "parameters": {
        "severity": "all"
      }
    },
    {
      "type": "copilot_code_review",
      "parameters": {
        "review_on_push": true,
        "review_draft_pull_requests": true
      }
    },
    {
      "type": "copilot_code_review_analysis_tools",
      "parameters": {
        "tools": [
          {
            "name": "CodeQL"
          },
          {
            "name": "PMD"
          }
        ]
      }
    },
    {
      "type": "creation"
    }
  ],
  "bypass_actors": [
    {
      "actor_id": 2,
      "actor_type": "RepositoryRole",
      "bypass_mode": "always"
    },
    {
      "actor_id": 4,
      "actor_type": "RepositoryRole",
      "bypass_mode": "always"
    },
    {
      "actor_id": 5,
      "actor_type": "RepositoryRole",
      "bypass_mode": "always"
    }
  ]
}

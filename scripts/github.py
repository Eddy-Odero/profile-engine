"""
github.py  (Phase 4)

Fetches live GitHub data for a user:
    - repo count, followers, total stars (REST)
    - top languages across repos (REST)
    - recent public activity (REST)
    - pinned repositories, contribution count (GraphQL - needs a token)

REST alone can't see pinned repos or contribution totals - those only
exist via GitHub's GraphQL API, which requires authentication even for
public data. So this module degrades gracefully in three tiers:

    1. GITHUB_TOKEN set + GraphQL succeeds -> full stats, real pinned
       repos and contribution count.
    2. No token, or GraphQL fails -> REST-only stats, with "pinned"
       repos approximated as the most-starred repos, and contributions
       reported as unavailable.
    3. REST itself fails (offline, rate-limited, bad username) -> the
       whole function raises, and build.py falls back to mock stats
       (same pattern as avatar.py's fallback).

Usage:
    from github import fetch_github_stats
    stats = fetch_github_stats("EddyOdero")
"""

from __future__ import annotations

import requests

from utils import github_headers

REST_BASE = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

_PINNED_FALLBACK_COUNT = 3
_TOP_LANGUAGE_COUNT = 3
_RECENT_ACTIVITY_COUNT = 5

# GitHub event "type" values -> short human-readable verbs for the activity feed.
_EVENT_VERBS = {
    "PushEvent": "pushed to",
    "PullRequestEvent": "opened a PR on",
    "IssuesEvent": "opened an issue on",
    "CreateEvent": "created",
    "ForkEvent": "forked",
    "WatchEvent": "starred",
    "IssueCommentEvent": "commented on",
    "ReleaseEvent": "released on",
}


def fetch_profile(username: str) -> dict:
    """GET /users/{username} - basic counts (repos, followers, following)."""
    resp = requests.get(
        f"{REST_BASE}/users/{username}", headers=github_headers(), timeout=10
    )
    resp.raise_for_status()
    return resp.json()


def fetch_all_repos(username: str) -> list[dict]:
    """
    Paginate /users/{username}/repos to collect every public, non-fork repo.
    Forks are excluded so stars/languages reflect the user's own work.
    """
    repos: list[dict] = []
    page = 1
    while True:
        resp = requests.get(
            f"{REST_BASE}/users/{username}/repos",
            headers=github_headers(),
            params={"per_page": 100, "page": page, "type": "owner"},
            timeout=10,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(r for r in batch if not r.get("fork"))
        if len(batch) < 100:
            break
        page += 1
    return repos


def aggregate_repo_stats(repos: list[dict]) -> dict:
    """Sum stars and rank languages by how many repos use them."""
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    language_counts: dict[str, int] = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1
    top_languages = sorted(language_counts, key=language_counts.get, reverse=True)

    top_starred = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)

    return {
        "stars": total_stars,
        "top_languages": top_languages[:_TOP_LANGUAGE_COUNT],
        "top_starred_names": [r["name"] for r in top_starred[:_PINNED_FALLBACK_COUNT]],
    }


def fetch_recent_activity(username: str, limit: int = _RECENT_ACTIVITY_COUNT) -> list[str]:
    """Turn recent public events into short human-readable lines."""
    resp = requests.get(
        f"{REST_BASE}/users/{username}/events/public",
        headers=github_headers(),
        params={"per_page": limit},
        timeout=10,
    )
    resp.raise_for_status()

    lines = []
    for event in resp.json()[:limit]:
        verb = _EVENT_VERBS.get(event.get("type"), "did something on")
        repo_name = event.get("repo", {}).get("name", "a repo")
        lines.append(f"{verb} {repo_name}")
    return lines


_GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
      }
    }
    pinnedItems(first: 6, types: [REPOSITORY]) {
      nodes {
        ... on Repository {
          name
        }
      }
    }
  }
}
"""


def fetch_graphql_extras(username: str) -> dict | None:
    """
    Fetch contribution count + pinned repos via GraphQL. Returns None
    (instead of raising) if there's no token or the call fails, so
    callers can fall back to REST-derived approximations.
    """
    headers = github_headers()
    if "Authorization" not in headers:
        return None

    try:
        resp = requests.post(
            GRAPHQL_URL,
            headers=headers,
            json={"query": _GRAPHQL_QUERY, "variables": {"login": username}},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()["data"]["user"]
        return {
            "contributions": data["contributionsCollection"]["contributionCalendar"][
                "totalContributions"
            ],
            "pinned": [node["name"] for node in data["pinnedItems"]["nodes"]],
        }
    except Exception:
        # GraphQL is a nice-to-have here, not essential - REST fallback covers us.
        return None


def fetch_github_stats(username: str) -> dict:
    """
    Full Phase 4 pipeline: username -> dict shaped for the render context.

    Keys: repo_count, stars, followers, top_languages, recent_activity,
    pinned_repos, contributions (int or None if unavailable).
    """
    profile = fetch_profile(username)
    repos = fetch_all_repos(username)
    repo_stats = aggregate_repo_stats(repos)
    activity = fetch_recent_activity(username)
    extras = fetch_graphql_extras(username)

    if extras:
        pinned_repos = extras["pinned"] or repo_stats["top_starred_names"]
        contributions = extras["contributions"]
    else:
        pinned_repos = repo_stats["top_starred_names"]
        contributions = None

    return {
        "repo_count": profile.get("public_repos", len(repos)),
        "stars": repo_stats["stars"],
        "followers": profile.get("followers", 0),
        "top_languages": repo_stats["top_languages"],
        "recent_activity": activity,
        "pinned_repos": pinned_repos,
        "contributions": contributions,
    }


if __name__ == "__main__":
    import sys
    import json

    name = sys.argv[1] if len(sys.argv) > 1 else "octocat"
    print(json.dumps(fetch_github_stats(name), indent=2))

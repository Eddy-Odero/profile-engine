"""
leetcode.py  (Phase 5)

Fetches LeetCode stats for a username via LeetCode's (unofficial, but
widely used) GraphQL endpoint:
    - solved problem counts (total / easy / medium / hard)
    - contest rating, ranking, top percentage
    - badges
    - recent accepted submissions

LeetCode has no official public REST API - this endpoint is the same
one leetcode.com's own frontend calls, and is the standard approach
used by most open-source "leetcode stats card" projects. It requires
no auth for public profile data, but does expect a browser-like
Referer header or it will reject the request.

Degrades the same way github.py does: if contest ranking is missing
(the user has never entered a contest) that's a normal, valid response
- not an error - so it's reported as None rather than raising. If the
whole fetch fails (offline, username doesn't exist, endpoint changed),
fetch_leetcode_stats raises and build.py falls back to mock data.

Usage:
    from leetcode import fetch_leetcode_stats
    stats = fetch_leetcode_stats("EddyOdero")
"""

from __future__ import annotations

import requests

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

_HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "profile-engine",
}

_RECENT_SUBMISSIONS_LIMIT = 5

# One combined query - LeetCode's GraphQL endpoint allows multiple root
# fields per request, so this is a single round trip instead of four.
_QUERY = """
query userProfile($username: String!, $limit: Int!) {
  matchedUser(username: $username) {
    submitStats: submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
    badges {
      displayName
    }
  }
  userContestRanking(username: $username) {
    attendedContestsCount
    rating
    globalRanking
    topPercentage
  }
  recentAcSubmissionList(username: $username, limit: $limit) {
    title
  }
}
"""


def _parse_solved_counts(ac_submission_num: list[dict]) -> dict:
    """
    LeetCode returns counts per difficulty as a list of
    {"difficulty": "All"|"Easy"|"Medium"|"Hard", "count": N}.
    Reshape into a flat, predictable dict.
    """
    counts = {row["difficulty"]: row["count"] for row in ac_submission_num}
    return {
        "total": counts.get("All", 0),
        "easy": counts.get("Easy", 0),
        "medium": counts.get("Medium", 0),
        "hard": counts.get("Hard", 0),
    }


def fetch_leetcode_stats(username: str) -> dict:
    """
    Full Phase 5 pipeline: username -> dict shaped for the render context.

    Keys: solved (dict: total/easy/medium/hard), rating, ranking,
    top_percentage, contests_attended, badges (list[str]),
    recent_submissions (list[str]).

    `rating`/`ranking`/`top_percentage`/`contests_attended` are None if
    the user has never entered a rated contest - that's a normal state,
    not a failure.
    """
    resp = requests.post(
        LEETCODE_GRAPHQL_URL,
        headers=_HEADERS,
        json={
            "query": _QUERY,
            "variables": {"username": username, "limit": _RECENT_SUBMISSIONS_LIMIT},
        },
        timeout=10,
    )
    resp.raise_for_status()
    payload = resp.json()

    if payload.get("errors"):
        raise RuntimeError(f"LeetCode GraphQL error: {payload['errors']}")

    data = payload["data"]
    matched_user = data.get("matchedUser")
    if matched_user is None:
        raise ValueError(f"LeetCode user not found: {username!r}")

    solved = _parse_solved_counts(matched_user["submitStats"]["acSubmissionNum"])
    badges = [b["displayName"] for b in matched_user.get("badges", [])]

    contest = data.get("userContestRanking")
    recent = [row["title"] for row in data.get("recentAcSubmissionList", [])]

    return {
        "solved": solved,
        "rating": round(contest["rating"]) if contest else None,
        "ranking": contest["globalRanking"] if contest else None,
        "top_percentage": contest["topPercentage"] if contest else None,
        "contests_attended": contest["attendedContestsCount"] if contest else None,
        "badges": badges,
        "recent_submissions": recent,
    }


if __name__ == "__main__":
    import json
    import sys

    name = sys.argv[1] if len(sys.argv) > 1 else "leetcode"
    print(json.dumps(fetch_leetcode_stats(name), indent=2))

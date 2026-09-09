"""Generate a transparent trophy board from GitHub profile statistics."""

import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    contributionsCollection { contributionCalendar { totalContributions } }
    repositories(first: 100, after: $cursor, privacy: PUBLIC,
                 ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount forkCount }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""

# Each medal has a light and dark accent; all text shares the same palette.
ITEMS = (
    ("stars", "Stars", "public originals", "#b77908", "#f2c14e",
     '<path d="m12 2 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z"/>'),
    ("repos", "Repositories", "public originals", "#2474cf", "#60a5fa",
     '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 3v18M11 8h5M11 12h5"/>'),
    ("followers", "Followers", "community", "#9254c8", "#c084fc",
     '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 5v2"/>'),
    ("forks", "Forks", "of public originals", "#13856b", "#34d399",
     '<circle cx="6" cy="5" r="2"/><circle cx="18" cy="5" r="2"/><circle cx="12" cy="20" r="2"/><path d="M6 7v3c0 4 12 4 12 0V7M12 13v5"/>'),
    ("contributions", "Contributions", "past year", "#d06623", "#fb923c",
     '<path d="M2 13h5l3-9 4 17 3-8h5"/>'),
    ("years", "Years on GitHub", "completed years", "#b54d7b", "#f472b6",
     '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 2v6M17 2v6M3 11h18M8 15h2M14 15h2"/>'),
)


def request_user(login, cursor, token):
    payload = json.dumps({"query": QUERY, "variables": {"login": login, "cursor": cursor}}).encode()
    for attempt in range(3):
        try:
            request = urllib.request.Request(
                "https://api.github.com/graphql", data=payload,
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/json", "User-Agent": "StarHeartY-trophy"},
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.load(response)
            if result.get("errors") or not result.get("data", {}).get("user"):
                raise ValueError("GitHub did not return complete profile data")
            return result["data"]["user"]
        except (urllib.error.URLError, OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def fetch_stats(login, token, now=None):
    now = now or datetime.now(timezone.utc)
    cursor = None
    stars = forks = 0
    while True:
        user = request_user(login, cursor, token)
        if cursor is None:
            created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
            years = now.year - created.year - (
                (now.month, now.day) < (created.month, created.day)
            )
            stats = {
                "followers": user["followers"]["totalCount"],
                "contributions": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
                "repos": user["repositories"]["totalCount"],
                "years": max(0, years),
            }
        repositories = user["repositories"]
        for repo in repositories["nodes"]:
            stars += repo["stargazerCount"]
            forks += repo["forkCount"]
        page = repositories["pageInfo"]
        if not page["hasNextPage"]:
            return dict(stats, stars=stars, forks=forks)
        if not page["endCursor"] or page["endCursor"] == cursor:
            raise ValueError("GitHub returned an invalid repository cursor")
        cursor = page["endCursor"]


def render_svg(stats, dark=False):
    foreground, muted = ("#e6edf3", "#919ba8") if dark else ("#24292f", "#656d76")
    medals = []
    for index, (key, label, detail, light, night, icon) in enumerate(ITEMS):
        value = stats[key]
        if type(value) is not int or value < 0:
            raise ValueError(f"Invalid statistic: {key}")
        color = night if dark else light
        medals.append(f'''<g transform="translate({80 + index * 160},0)">
  <title>{escape(label)}: {value:,} ({escape(detail)})</title>
  <path d="m-19 88-6 28 15-6 10 8 8-8 15 6-6-28" fill="{color}" opacity=".22"/>
  <circle cy="76" r="29" fill="{color}" fill-opacity=".10" stroke="{color}" stroke-width="1.5"/>
  <g transform="translate(-12,64)" fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{icon}</g>
  <text y="153" class="value">{value:,}</text>
  <text y="178" class="label">{escape(label)}</text>
  <text y="196" class="detail">{escape(detail)}</text>
</g>''')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="215" viewBox="0 0 960 215" role="img" aria-labelledby="title description">
<title id="title">Trophy Board</title>
<desc id="description">Public original repositories, their stars and forks, followers, contributions in the past year, and completed years on GitHub.</desc>
<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; text-anchor: middle; }}
.heading {{ fill: {foreground}; font-size: 20px; font-weight: 600; text-anchor: start; }}
.value {{ fill: {foreground}; font-size: 28px; font-weight: 600; }}
.label {{ fill: {foreground}; font-size: 13px; }}
.detail {{ fill: {muted}; font-size: 11px; }}
</style>
<text x="18" y="26" class="heading">Trophy Board</text>
{''.join(medals)}
</svg>'''
    ET.fromstring(svg)
    return svg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="StarHeartY")
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    stats = fetch_stats(args.username, token)
    images = {"trophy.svg": render_svg(stats), "trophy-dark.svg": render_svg(stats, dark=True)}
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, svg in images.items():
        (args.output / filename).write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()

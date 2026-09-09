"""Prepare validated profile cards for publication to the stats branch."""

import argparse
from pathlib import Path
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


CARDS = {
    "languages.svg": (
        "https://github-readme-stats-nine-swart-42.vercel.app/api/top-langs/"
        "?username=StarHeartY&layout=compact&theme=transparent",
        ("Most Used Languages",),
    ),
    "github-stats.svg": (
        "https://github-readme-stats-nine-swart-42.vercel.app/api"
        "?username=StarHeartY&show_icons=true&theme=transparent",
        ("Total Stars", "Total Commits"),
    ),
    "activity.svg": (
        "https://github-readme-activity-graph-flax-nu.vercel.app/graph"
        "?username=StarHeartY&bg_color=none&color=4a9eff&line=4a9eff&point=c0c0c0",
        ("Days", "Contributions"),
    ),
}
STREAK_LABELS = ("Total Contributions", "Current Streak", "Longest Streak")
SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"


def validate_svg(data, required_labels):
    root = ET.fromstring(data)
    if root.tag != SVG_NAMESPACE + "svg":
        raise ValueError("Response is not an SVG image")
    # Services can return HTTP 200 with an SVG error card instead of statistics.
    visible_text = " ".join(
        "".join(node.itertext())
        for node in root.iter(SVG_NAMESPACE + "text")
    )
    for label in required_labels:
        if label.casefold() not in visible_text.casefold():
            raise ValueError(f"Missing statistics label: {label}")


def download_card(url, required_labels):
    for attempt in range(4):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "StarHeartY-profile-stats"}
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                data = response.read()
            validate_svg(data, required_labels)
            return data
        except (urllib.error.URLError, OSError, ValueError, ET.ParseError) as error:
            if attempt == 3:
                raise RuntimeError("Could not retrieve a valid statistics card") from error
            print(f"Attempt {attempt + 1} failed: {error}; retrying", flush=True)
            time.sleep(5 * (attempt + 1))


def prepare_cards(output):
    validate_svg((output / "streak.svg").read_bytes(), STREAK_LABELS)
    cards = {}
    for filename, (url, labels) in CARDS.items():
        print(f"Downloading {filename}", flush=True)
        cards[filename] = download_card(url, labels)
    # Publication only runs after every card passes validation.
    for filename, data in cards.items():
        (output / filename).write_bytes(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    prepare_cards(parser.parse_args().output)

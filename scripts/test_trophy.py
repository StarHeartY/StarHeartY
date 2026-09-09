from datetime import datetime, timezone
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from scripts import trophy


def page(nodes, has_next=False, cursor=None):
    return {
        "createdAt": "2020-09-10T00:00:00Z",
        "followers": {"totalCount": 7},
        "contributionsCollection": {"contributionCalendar": {"totalContributions": 2345}},
        "repositories": {"totalCount": 101, "nodes": nodes,
                         "pageInfo": {"hasNextPage": has_next, "endCursor": cursor}},
    }


class TrophyTests(unittest.TestCase):
    def test_sums_all_repository_pages(self):
        pages = [page([{"stargazerCount": 2, "forkCount": 1}] * 100, True, "next"),
                 page([{"stargazerCount": 10, "forkCount": 4}])]
        with patch.object(trophy, "request_user", side_effect=pages) as request:
            stats = trophy.fetch_stats("StartYR", "test", datetime(2026, 9, 9, tzinfo=timezone.utc))
        self.assertEqual(stats, dict(stars=210, forks=104, repos=101,
                                     followers=7, contributions=2345, years=5))
        self.assertEqual(request.call_args.args[1], "next")

    def test_anniversary_and_zero_repositories(self):
        with patch.object(trophy, "request_user", return_value=page([])):
            stats = trophy.fetch_stats("StartYR", "test", datetime(2026, 9, 10, tzinfo=timezone.utc))
        self.assertEqual(stats["years"], 6)
        self.assertEqual(stats["stars"], 0)

    def test_rejects_broken_pagination(self):
        with patch.object(trophy, "request_user", return_value=page([], True, None)):
            with self.assertRaises(ValueError):
                trophy.fetch_stats("StartYR", "test")

    def test_graphql_partial_errors_are_not_published(self):
        with patch.object(trophy.urllib.request, "urlopen"), patch.object(
            trophy.json, "load", return_value={"data": {"user": page([])}, "errors": [{"message": "failed"}]}
        ), patch.object(trophy.time, "sleep"), self.assertRaises(ValueError):
            trophy.request_user("StartYR", None, "test")

    def test_both_themes_have_six_colored_medals_and_no_background_rect(self):
        stats = dict(stars=1234567, repos=0, followers=123, forks=40, contributions=5000, years=6)
        for dark in (False, True):
            svg = trophy.render_svg(stats, dark)
            root = ET.fromstring(svg)
            namespace = {"s": "http://www.w3.org/2000/svg"}
            self.assertEqual(len(root.findall("s:g", namespace)), 6)
            self.assertEqual(root.findall("s:rect", namespace), [])
            self.assertIn("1,234,567", svg)
            for item in trophy.ITEMS:
                self.assertIn(item[4] if dark else item[3], svg)

    def test_invalid_numbers_fail_generation(self):
        stats = dict(stars=-1, repos=0, followers=0, forks=0, contributions=0, years=0)
        with self.assertRaises(ValueError):
            trophy.render_svg(stats)


if __name__ == "__main__":
    unittest.main()

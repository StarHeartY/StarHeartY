import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import profile_stats as stats


def svg(*labels):
    text = "".join(f"<text>{label}</text>" for label in labels)
    return f'<svg xmlns="http://www.w3.org/2000/svg">{text}</svg>'.encode()


class ProfileStatsTests(unittest.TestCase):
    def test_accepts_statistics(self):
        stats.validate_svg(svg(*stats.STREAK_LABELS), stats.STREAK_LABELS)

    def test_rejects_html_and_error_cards(self):
        for data in (b"<html>Bad gateway</html>", svg("Something went wrong!")):
            with self.subTest(data=data), self.assertRaises(ValueError):
                stats.validate_svg(data, stats.STREAK_LABELS)

    def test_retries_error_card_before_accepting_valid_card(self):
        good = svg("Most Used Languages")
        with patch.object(stats.urllib.request, "urlopen") as request, patch.object(
            stats.time, "sleep"
        ):
            request.return_value.__enter__.return_value.read.side_effect = [
                svg("API rate limit exceeded"), good
            ]
            self.assertEqual(stats.download_card("https://example.com", ("Most Used Languages",)), good)
            self.assertEqual(request.call_count, 2)

    def test_stops_after_repeated_network_failure(self):
        with patch.object(stats.urllib.request, "urlopen", side_effect=TimeoutError) as request, patch.object(
            stats.time, "sleep"
        ), self.assertRaises(RuntimeError):
            stats.download_card("https://example.com", ("Most Used Languages",))
        self.assertEqual(request.call_count, 4)

    def test_failed_batch_preserves_existing_cards(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "streak.svg").write_bytes(svg(*stats.STREAK_LABELS))
            (output / "languages.svg").write_bytes(b"previous card")
            with patch.object(stats, "download_card", side_effect=[svg("Most Used Languages"), RuntimeError]), self.assertRaises(RuntimeError):
                stats.prepare_cards(output)
            self.assertEqual((output / "languages.svg").read_bytes(), b"previous card")
            self.assertFalse((output / "github-stats.svg").exists())

    def test_successful_batch_writes_all_cards(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "streak.svg").write_bytes(svg(*stats.STREAK_LABELS))
            with patch.object(stats, "download_card", side_effect=[svg(*labels) for _, labels in stats.CARDS.values()]):
                stats.prepare_cards(output)
            for filename, (_, labels) in stats.CARDS.items():
                stats.validate_svg((output / filename).read_bytes(), labels)


if __name__ == "__main__":
    unittest.main()

import unittest

from src.ci_demo.__main__ import response_for


class AppTest(unittest.TestCase):
    def test_health(self):
        self.assertEqual(response_for("/health"), (200, {"status": "ok"}))

    def test_convert_temperature(self):
        for celsius, fahrenheit in [(20, 68), (0, 32), (-40, -40), (0.01, 32.02)]:
            with self.subTest(celsius=celsius):
                self.assertEqual(
                    response_for(f"/fahrenheit?celsius={celsius}"),
                    (200, {"fahrenheit": fahrenheit}),
                )

    def test_invalid_temperature(self):
        queries = [
            "",
            "celsius=abc",
            "celsius=NaN",
            "celsius=1e308",
            "celsius=1&celsius=2",
            "celsius=1&celsius=",
        ]
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(response_for(f"/fahrenheit?{query}")[0], 400)

    def test_unknown_path(self):
        self.assertEqual(response_for("/unknown")[0], 404)

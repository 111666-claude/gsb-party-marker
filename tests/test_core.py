import unittest

from markers.core import Markers


def world():
    return Markers(per_player_max=5, ttl_ms=1000)


class BasicTest(unittest.TestCase):
    def test_empty_active(self):
        self.assertEqual(world().active(0), [])

    def test_single_mark(self):
        target = world()
        target.mark("p1", "boss", 0)
        self.assertEqual(target.active(0), ["boss"])

    def test_count_starts_at_zero(self):
        self.assertEqual(world().count(), 0)

    def test_scanned_starts_at_zero(self):
        self.assertEqual(world().scanned_count(), 0)


if __name__ == "__main__":
    unittest.main()

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


class DedupTest(unittest.TestCase):
    def test_same_target_kept_once(self):
        w = world()
        w.mark("p1", "boss", 0)
        w.mark("p1", "boss", 10)
        self.assertEqual(w.active(20), ["boss"])

    def test_remark_refreshes_ttl(self):
        w = world()
        w.mark("p1", "boss", 0)
        w.mark("p1", "boss", 900)
        self.assertEqual(w.active(1000), ["boss"])
        self.assertEqual(w.active(1900), [])

    def test_same_target_across_players_deduped(self):
        w = world()
        w.mark("p1", "boss", 0)
        w.mark("p2", "boss", 1)
        self.assertEqual(w.active(2), ["boss"])


class CapTest(unittest.TestCase):
    def test_cap_drops_oldest(self):
        w = Markers(per_player_max=2, ttl_ms=100000)
        for index in range(3):
            w.mark("p1", "t-%d" % index, index)
        self.assertEqual(w.active(10), ["t-1", "t-2"])

    def test_cap_is_per_player(self):
        w = Markers(per_player_max=1, ttl_ms=100000)
        w.mark("p1", "a", 0)
        w.mark("p2", "b", 0)
        self.assertEqual(w.active(0), ["a", "b"])

    def test_remark_does_not_evict(self):
        w = Markers(per_player_max=2, ttl_ms=100000)
        w.mark("p1", "a", 0)
        w.mark("p1", "b", 1)
        w.mark("p1", "a", 2)
        self.assertEqual(w.active(3), ["a", "b"])


class TtlTest(unittest.TestCase):
    def test_expired_mark_not_active(self):
        w = world()
        w.mark("p1", "boss", 0)
        self.assertEqual(w.active(1000), [])

    def test_mark_alive_before_ttl(self):
        w = world()
        w.mark("p1", "boss", 0)
        self.assertEqual(w.active(999), ["boss"])

    def test_expired_mark_frees_cap_slot(self):
        w = Markers(per_player_max=1, ttl_ms=100)
        w.mark("p1", "old", 0)
        w.mark("p1", "new", 200)
        self.assertEqual(w.active(200), ["new"])


class OrderingTest(unittest.TestCase):
    def test_active_sorted_by_target(self):
        w = world()
        w.mark("p1", "c", 0)
        w.mark("p1", "a", 1)
        w.mark("p1", "b", 2)
        self.assertEqual(w.active(3), ["a", "b", "c"])

    def test_repeated_runs_are_deterministic(self):
        def run():
            w = Markers(per_player_max=3, ttl_ms=50)
            w.mark("p1", "x", 0)
            w.mark("p2", "y", 5)
            w.mark("p1", "z", 10)
            w.mark("p1", "x", 20)
            return w.active(30)

        self.assertEqual(run(), run())

    def test_invariants_hold(self):
        w = Markers(per_player_max=4, ttl_ms=100)
        for index in range(50):
            w.mark("p-%d" % (index % 3), "t-%d" % (index % 7), index)
        result = w.active(60)
        self.assertEqual(len(result), len(set(result)))
        self.assertEqual(result, sorted(result))
        self.assertLessEqual(len(result), 3 * 4)


class ScanCostTest(unittest.TestCase):
    def test_scanned_does_not_grow_with_history(self):
        w = Markers(per_player_max=10000, ttl_ms=100000)
        for index in range(3000):
            w.mark("p-%d" % index, "t-%d" % index, 0)
        for _ in range(3000):
            w.active(0)
        self.assertLessEqual(w.scanned_count(), 6000)

    def test_scanned_only_counts_expired(self):
        w = Markers(per_player_max=10000, ttl_ms=10)
        for index in range(1000):
            w.mark("p-%d" % index, "t-%d" % index, index)
        w.active(2000)
        self.assertLessEqual(w.scanned_count(), 1000)

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


class DedupTest(unittest.TestCase):
    def test_same_target_keeps_latest_only(self):
        w = world()
        w.mark("p1", "boss", 0)
        w.mark("p1", "boss", 10)
        self.assertEqual(w.active(20), ["boss"])
        self.assertEqual(w.count(), 1)

    def test_dedup_across_players(self):
        w = world()
        w.mark("p1", "boss", 0)
        w.mark("p2", "boss", 5)
        self.assertEqual(w.active(10), ["boss"])
        self.assertEqual(w.count(), 1)

    def test_remark_refreshes_expiry(self):
        w = world()
        w.mark("p1", "boss", 0)
        w.mark("p1", "boss", 500)
        self.assertEqual(w.active(1001), ["boss"])
        self.assertEqual(w.active(1500), [])

    def test_takeover_counts_against_new_owner(self):
        w = Markers(per_player_max=1, ttl_ms=1000)
        w.mark("p1", "a", 0)
        w.mark("p2", "a", 1)  # a 转手给 p2，p1 的槽位释放
        w.mark("p1", "c", 2)  # p1 可以再标
        self.assertEqual(w.active(3), ["a", "c"])
        w.mark("p2", "b", 4)  # p2 超上限，丢掉自己最早的 a
        self.assertEqual(w.active(5), ["b", "c"])


class CapTest(unittest.TestCase):
    def test_cap_drops_earliest(self):
        w = Markers(per_player_max=2, ttl_ms=100000)
        w.mark("p1", "t-0", 0)
        w.mark("p1", "t-1", 1)
        w.mark("p1", "t-2", 2)
        self.assertEqual(w.active(10), ["t-1", "t-2"])
        self.assertEqual(w.count(), 2)

    def test_cap_is_per_player(self):
        w = Markers(per_player_max=1, ttl_ms=100000)
        w.mark("p1", "a", 0)
        w.mark("p2", "b", 0)
        self.assertEqual(w.active(1), ["a", "b"])

    def test_remark_moves_marker_to_newest(self):
        w = Markers(per_player_max=2, ttl_ms=100000)
        w.mark("p1", "a", 0)
        w.mark("p1", "b", 1)
        w.mark("p1", "a", 2)
        w.mark("p1", "c", 3)
        self.assertEqual(w.active(10), ["a", "c"])


class TtlTest(unittest.TestCase):
    def test_expired_mark_not_active(self):
        w = world()
        w.mark("p1", "boss", 0)
        self.assertEqual(w.active(999), ["boss"])
        self.assertEqual(w.active(1000), [])

    def test_expiry_is_per_mark(self):
        w = world()
        w.mark("p1", "a", 0)
        w.mark("p1", "b", 500)
        self.assertEqual(w.active(1200), ["b"])

    def test_expired_mark_frees_cap_slot(self):
        w = Markers(per_player_max=1, ttl_ms=1000)
        w.mark("p1", "a", 0)
        w.mark("p1", "b", 1)
        self.assertEqual(w.active(1000), ["b"])
        self.assertEqual(w.active(1001), [])


class OrderInvariantTest(unittest.TestCase):
    def test_results_sorted_by_target_name(self):
        w = world()
        for name in ["delta", "alpha", "charlie", "bravo"]:
            w.mark("p1", name, 0)
        self.assertEqual(w.active(1), ["alpha", "bravo", "charlie", "delta"])

    def test_repeated_queries_are_identical(self):
        w = world()
        w.mark("p1", "b", 0)
        w.mark("p1", "a", 0)
        first = w.active(1)
        self.assertEqual(w.active(1), first)
        self.assertEqual(w.active(1), first)

    def test_replaying_same_sequence_gives_same_result(self):
        def run():
            w = Markers(per_player_max=3, ttl_ms=100)
            w.mark("p1", "x", 0)
            w.mark("p2", "y", 1)
            w.mark("p1", "x", 2)
            w.mark("p1", "z", 3)
            w.mark("p1", "w", 4)
            return w.active(50)

        self.assertEqual(run(), run())

    def test_active_returns_independent_list(self):
        w = world()
        w.mark("p1", "a", 0)
        result = w.active(0)
        result.append("mutated")
        self.assertEqual(w.active(0), ["a"])


class ScanCostTest(unittest.TestCase):
    def test_scanned_not_linear_in_history(self):
        w = Markers(per_player_max=10000, ttl_ms=100000)
        for index in range(3000):
            w.mark("p-%d" % index, "t-%d" % index, 0)
        for _ in range(3000):
            w.active(0)
        self.assertLessEqual(w.scanned_count(), 6000)

    def test_active_scans_only_expired(self):
        w = Markers(per_player_max=100, ttl_ms=1000)
        for index in range(100):
            w.mark("p1", "t-%d" % index, index)
        before = w.scanned_count()
        w.active(50)
        self.assertLessEqual(w.scanned_count() - before, 100)

    def test_large_scale_stays_bounded(self):
        w = Markers(per_player_max=100000, ttl_ms=1000000)
        for index in range(100000):
            w.mark("p-%d" % index, "t-%d" % index, index)
        before = w.scanned_count()
        for _ in range(1000):
            w.active(500)
        self.assertLessEqual(w.scanned_count() - before, 2000)


if __name__ == "__main__":
    unittest.main()

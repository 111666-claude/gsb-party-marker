"""队伍标记：同一目标去重、每人上限、过期清理与排序。

实现：每个玩家一个按插入顺序排列的 目标 -> 时间戳 字典（去重并维持
先后顺序），配合一个按过期时间排序的最小堆做惰性过期清理；`active`
只弹出已到期的堆顶元素，不扫描全部历史标记，单次摊还 O(活跃标记数)。
"""

import heapq


class Markers:
    def __init__(self, per_player_max, ttl_ms):
        self.per_player_max = per_player_max
        self.ttl_ms = ttl_ms
        self._by_player = {}
        self._expiry_heap = []
        self._seq = 0
        self._count = 0
        self.scanned = 0

    def _expire(self, now_ms):
        heap = self._expiry_heap
        while heap and heap[0][0] <= now_ms:
            _, _, player, target, marked_at = heapq.heappop(heap)
            self.scanned += 1
            marks = self._by_player.get(player)
            if marks is None or marks.get(target) != marked_at:
                continue
            del marks[target]
            self._count -= 1
            if not marks:
                del self._by_player[player]

    def mark(self, player, target, now_ms):
        self._expire(now_ms)
        marks = self._by_player.setdefault(player, {})
        if target in marks:
            del marks[target]
            self._count -= 1
        marks[target] = now_ms
        self._count += 1
        self._seq += 1
        heapq.heappush(
            self._expiry_heap,
            (now_ms + self.ttl_ms, self._seq, player, target, now_ms),
        )
        while len(marks) > self.per_player_max:
            oldest = next(iter(marks))
            del marks[oldest]
            self._count -= 1
        return True

    def active(self, now_ms):
        self._expire(now_ms)
        return sorted({target for marks in self._by_player.values() for target in marks})

    def count(self):
        return self._count

    def scanned_count(self):
        return self.scanned

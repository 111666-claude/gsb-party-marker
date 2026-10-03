"""队伍标记：同一目标去重、每人上限、过期清理与排序。

实现口径（见 README）：
- 目标去重：同一目标只保留最新一条标记，不叠加。
- 每人上限：同一玩家同时最多 per_player_max 条标记，超出时丢掉最早的一条。
- 过期：标记存在时间达到 ttl_ms 后失效，active 不再返回。
- 排序：结果按目标名升序，结果缓存，重复查询不重复排序。
- 代价：active 只从过期堆里弹出已到期的标记，摊还 O(1)，
  scanned_count 不随标记数线性增长。
"""

import heapq
from collections import deque


class Markers:
    def __init__(self, per_player_max, ttl_ms):
        self.per_player_max = per_player_max
        self.ttl_ms = ttl_ms
        # target -> (player, marked_at_ms)，同一目标只保留最新一条
        self._by_target = {}
        # player -> deque[(target, marked_at_ms)]，队首是最早的一条
        self._by_player = {}
        # 每个玩家当前持有的标记条数
        self._player_count = {}
        # (过期时刻, target, marked_at_ms) 小根堆，惰性清理
        self._expiry_heap = []
        # 按目标名升序的缓存，数据变化时置 None
        self._sorted_cache = None
        self.scanned = 0

    def mark(self, player, target, now_ms):
        previous = self._by_target.get(target)
        if previous is not None:
            old_player, _ = previous
            self._player_count[old_player] -= 1
        self._by_target[target] = (player, now_ms)
        self._player_count[player] = self._player_count.get(player, 0) + 1
        queue = self._by_player.setdefault(player, deque())
        queue.append((target, now_ms))
        heapq.heappush(self._expiry_heap, (now_ms + self.ttl_ms, target, now_ms))
        while self._player_count[player] > self.per_player_max:
            old_target, old_marked_at = queue.popleft()
            self.scanned += 1
            current = self._by_target.get(old_target)
            if current is None or current[1] != old_marked_at:
                continue
            del self._by_target[old_target]
            self._player_count[player] -= 1
        self._sorted_cache = None
        return True

    def active(self, now_ms):
        heap = self._expiry_heap
        while heap:
            self.scanned += 1
            expires_at, target, marked_at = heap[0]
            if expires_at > now_ms:
                break
            heapq.heappop(heap)
            current = self._by_target.get(target)
            if current is not None and current[1] == marked_at:
                del self._by_target[target]
                self._player_count[current[0]] -= 1
            self._sorted_cache = None
        if self._sorted_cache is None:
            self._sorted_cache = sorted(self._by_target)
        return list(self._sorted_cache)

    def count(self):
        return len(self._by_target)

    def scanned_count(self):
        return self.scanned

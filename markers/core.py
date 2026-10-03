"""队伍标记：同一目标去重、每人上限、过期清理与排序。

缺陷：同一目标重复标记、每人上限不生效、过期不清理、结果不排序、
每次查询扫描全部标记。
"""


class Markers:
    def __init__(self, per_player_max, ttl_ms):
        self.per_player_max = per_player_max
        self.ttl_ms = ttl_ms
        self.items = []
        self.scanned = 0

    def mark(self, player, target, now_ms):
        self.scanned += len(self.items)
        self.items.append((player, target, now_ms))
        return True

    def active(self, now_ms):
        self.scanned += len(self.items)
        return sorted({target for _, target, _ in self.items})

    def count(self):
        return len(self.items)

    def scanned_count(self):
        return self.scanned

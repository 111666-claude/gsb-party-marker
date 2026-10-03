# party-marker

队伍标记：同一目标去重、每人上限、过期清理与排序，只用 Python 标准库。

```
python3 -m markers.cli --sample dedup
python3 -m markers.cli --sample cap
python3 -m markers.cli --sample ttl
python3 -m markers.cli --sample scan
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **目标去重**：同一个目标只保留最新一条标记，不叠加。
- **每人上限**：同一玩家同时最多 `per_player_max` 条标记，超出时丢掉最早的一条。
- **过期**：标记存在时间达到 `ttl_ms` 后失效，`active` 不再返回。
- **排序**：结果按目标名升序。
- **不变量**：结果里目标不重复；条数不超过上限；同一串标记序列重复执行结果相同。
- **代价**：`active` 不许扫描全部历史标记，`scanned_count` 不随标记数线性增长。
- **规模**：10 万标记、每秒 10 万次查询，单次摊还 O(活跃标记数)。

## 输出契约（不改格式）

```
active=..
scanned=..
```

## 目录

```
markers/core.py   去重、上限、过期与排序
markers/cli.py    命令行入口
tests/            unittest 用例
```

"""命令行入口：跑队伍标记样例。"""

import argparse

from .core import Markers


def main(argv=None):
    parser = argparse.ArgumentParser(prog="party-marker", description="队伍标记")
    parser.add_argument("--sample", default="dedup", help="dedup / cap / ttl / scan")
    args = parser.parse_args(argv)
    if args.sample == "dedup":
        world = Markers(per_player_max=5, ttl_ms=100000)
        world.mark("p1", "boss", 0)
        world.mark("p1", "boss", 10)
        print("active=%d" % len(world.active(20)))
    elif args.sample == "cap":
        world = Markers(per_player_max=2, ttl_ms=100000)
        for index in range(3):
            world.mark("p1", "t-%d" % index, index)
        print("active=%d" % len(world.active(10)))
    elif args.sample == "ttl":
        world = Markers(per_player_max=5, ttl_ms=1000)
        world.mark("p1", "boss", 0)
        print("active=%d" % len(world.active(1001)))
    elif args.sample == "scan":
        world = Markers(per_player_max=10000, ttl_ms=100000)
        for index in range(3000):
            world.mark("p-%d" % index, "t-%d" % index, 0)
        for index in range(3000):
            world.active(0)
        print("scanned=%d" % world.scanned_count())
    else:
        raise SystemExit("需要 --sample dedup|cap|ttl|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

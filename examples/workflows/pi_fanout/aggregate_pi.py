"""Fan-in aggregator. Its Input Directory is the run root, so every
parent task's archive is a subdirectory of the current working dir."""

import glob
import json

shards = [
    json.load(open(p)) for p in sorted(glob.glob("*/inputDirectory/pi_shard.json"))
]
assert shards, "no shard results found"
n = sum(s["n"] for s in shards)
inside = sum(s["inside"] for s in shards)
pi = 4.0 * inside / n
report = {
    "shards": len(shards),
    "total_samples": n,
    "pi_estimate": pi,
    "abs_error": abs(pi - 3.141592653589793),
}
json.dump(report, open("pi_estimate.json", "w"), indent=2)
print(json.dumps(report, indent=2))

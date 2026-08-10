"""One Monte-Carlo pi shard. SEED and N_SAMPLES arrive as job env vars."""

import json
import os
import random

seed = int(os.environ["SEED"])
n = int(os.environ["N_SAMPLES"])
rng = random.Random(seed)
inside = sum(1 for _ in range(n) if rng.random() ** 2 + rng.random() ** 2 <= 1.0)
json.dump({"seed": seed, "n": n, "inside": inside}, open("pi_shard.json", "w"))
print(f"shard seed={seed}: {inside}/{n}")

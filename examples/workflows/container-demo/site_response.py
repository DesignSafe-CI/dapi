"""Linear-elastic site response of a damped soil layer on rigid rock.

Computes the surface/bedrock amplification spectrum
    |F(f)| = 1 / sqrt(cos^2(k H) + (xi * k H)^2),  k = 2 pi f / Vs
and self-checks that the peak sits at the fundamental site frequency
f0 = Vs / (4 H). Runs anywhere Python + numpy exist; this copy is baked
into a container built on the TACC ubuntu22 base image.
"""

import json
import os

import numpy as np

profile = {"Vs": 200.0, "H": 25.0, "damping": 0.05}  # m/s, m, ratio
if os.path.exists("profile.json"):
    profile.update(json.load(open("profile.json")))

Vs, H, xi = profile["Vs"], profile["H"], profile["damping"]
f = np.linspace(0.05, 20.0, 4000)
kH = 2.0 * np.pi * f * H / Vs
amp = 1.0 / np.sqrt(np.cos(kH) ** 2 + (xi * kH) ** 2)

f_peak = float(f[int(np.argmax(amp))])
f0 = Vs / (4.0 * H)
result = {
    "profile": profile,
    "f0_theory_hz": f0,
    "f_peak_hz": f_peak,
    "peak_amplification": float(np.max(amp)),
    "peak_matches_theory": bool(abs(f_peak - f0) < 0.05),
}
json.dump(result, open("site_response.json", "w"), indent=2)
np.savetxt(
    "transfer_function.csv",
    np.column_stack([f, amp]),
    delimiter=",",
    header="frequency_hz,amplification",
    comments="",
)
print(json.dumps(result, indent=2))
assert result["peak_matches_theory"], "resonance check failed"
print(f"OK: peak at {f_peak:.2f} Hz matches f0 = Vs/4H = {f0:.2f} Hz")

"""Cantilever pushover (one PyLauncher task).

Inputs (CLI):  --NodalMass --LCol --E --outDir
Output:        <outDir>/metrics.json
"""

import argparse
import json
import math
import os

if os.path.exists("opensees.so"):
    import opensees as ops  # TACC-compiled OpenSeesPy
else:
    import openseespy.opensees as ops

p = argparse.ArgumentParser()
p.add_argument("--NodalMass", type=float, required=True)  # kip*s^2/in
p.add_argument("--LCol", type=float, required=True)  # in
p.add_argument("--E", type=float, required=True)  # ksi
p.add_argument("--outDir", type=str, required=True)
args = p.parse_args()

os.makedirs(args.outDir, exist_ok=True)

# Fixed section properties
A = 3600.0  # in^2
Iz = 1.08e6  # in^4

ops.wipe()
ops.model("basic", "-ndm", 2, "-ndf", 3)
ops.node(1, 0.0, 0.0)
ops.node(2, 0.0, args.LCol)
ops.fix(1, 1, 1, 1)
ops.mass(2, args.NodalMass, 0.0, 0.0)
ops.geomTransf("Linear", 1)
ops.element("elasticBeamColumn", 1, 1, 2, A, args.E, Iz, 1)

# Modal: fundamental period
omega2 = ops.eigen("-fullGenLapack", 1)[0]
period = 2.0 * math.pi / math.sqrt(omega2)

# Static pushover under 100-kip lateral load
ops.timeSeries("Linear", 1)
ops.pattern("Plain", 1, 1)
ops.load(2, 100.0, 0.0, 0.0)
ops.constraints("Plain")
ops.numberer("Plain")
ops.system("BandGeneral")
ops.test("NormDispIncr", 1.0e-8, 6)
ops.algorithm("Newton")
ops.integrator("LoadControl", 0.1)
ops.analysis("Static")
ops.analyze(10)
top_disp = ops.nodeDisp(2, 1)

k_theory = 3.0 * args.E * Iz / (args.LCol**3)

metrics = {
    "NodalMass": args.NodalMass,
    "LCol": args.LCol,
    "E": args.E,
    "A": A,
    "Iz": Iz,
    "period": period,
    "k_theory": k_theory,
    "top_disp_at_100kip": top_disp,
}
with open(os.path.join(args.outDir, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)

print(f"OK NodalMass={args.NodalMass} LCol={args.LCol} E={args.E} period={period:.4f}")

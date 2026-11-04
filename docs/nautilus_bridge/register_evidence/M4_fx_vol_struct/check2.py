import math, sys
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
from core.ficc import equity_deriv as ED
from core.ficc.swaps import black76
F, r, T = 1126.0, 0.032, 20/365
df = math.exp(-r*T)
k1, k2 = 1125.0, 1127.5
B = 2.5*df
for dB in (0.01, 0.025, 0.05):
    print("box price err", dB, "rate err pct-pts", ((-math.log((B+dB)/2.5)/T) - r)*100)
# ATM premium size (tick regime)
print("ATM call premium at 20% vol", black76(F, 1125.0, T, 0.20, df, True).price)
# wider box 1075/1175
B2 = 100*df
print("100pt box, 0.05 err ->", ((-math.log((B2+0.05)/100)/T) - r)*100)

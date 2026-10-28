import math, sys
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
from core.ficc import equity_deriv as ED
from core.ficc.swaps import black76
for vol, days in ((0.20, 20), (0.40, 15), (0.20, 79)):
    F, r, T = 1126.0, 0.032, days/365
    df = math.exp(-r*T)
    ks = np.arange(round(F*0.9/2.5)*2.5, F*1.10, 2.5)
    q = [ED.Quote(strike=float(k), call_mid=black76(F, k, T, vol, df, True).price, put_mid=black76(F, k, T, vol, df, False).price, call_bid=0.01, put_bid=0.01) for k in ks]
    mv = ED.mfiv(q, F, T, r)
    print(f"vol {vol} days {days}: mfiv over +-10% = {mv['vol']:.4f} (n {mv['n_strikes']})")

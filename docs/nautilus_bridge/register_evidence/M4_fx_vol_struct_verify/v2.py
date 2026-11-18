import sys, math
sys.path.insert(0, "/home/user/quantgen")
import numpy as np
from core.ficc import equity_deriv as ED
from ui import derivatives_page as DP
# closed market: drop bid/ask from the synthetic board
q = DP.synthetic_board(1126.0, 20/365, 0.032)
closed = [ED.Quote(strike=x.strike, call_mid=x.call_mid, put_mid=x.put_mid, call_iv_exchange=x.call_iv_exchange, put_iv_exchange=x.put_iv_exchange) for x in q]
arb = ED.static_arbitrage(closed, quoted_only=True, F=1126.0, max_moneyness=0.15)
print("closed board static_arbitrage:", arb)
par = ED.parity_residuals(closed, 1126.0, 20/365, 0.032)
pw = [x["within"] for x in par if x["within"] is not None]
within = (sum(pw)/len(pw)) if pw else float("nan")
print("parity within text:", f"{within:.0%}")
# mfiv on closed board: bids None -> mids used
print("mfiv closed:", ED.mfiv(closed, 1126.0, 20/365, 0.032)["vol"])

# Replicates the check in tests/expansion_acceptance.py:294-306 against two synthetic weight rules
# (pure numpy; imports no repository code): one causal, one that peeks one bar ahead.
import numpy as np
rng = np.random.default_rng(8)
P = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, (900, 3)), axis=0))
P2 = P.copy()
P2[600:] *= np.exp(np.cumsum(rng.normal(0.01, 0.02, (300, 3)), axis=0))
def causal(P):            # weight at t from P[t] and P[t-20]
    W = np.zeros_like(P); W[20:] = (P[20:] > P[:-20]).astype(float); return W
def peek1(P):             # weight at t from P[t+1] (a one-bar look-ahead)
    W = np.zeros_like(P); W[:-1] = (P[1:] > P[:-1]).astype(float); return W
def peek2(P):             # weight at t from P[t+2]
    W = np.zeros_like(P); W[:-2] = (P[2:] > P[:-2]).astype(float); return W
for fn in (causal, peek1, peek2):
    W1, W2 = fn(P), fn(P2)
    print(fn.__name__, "test slice [:599] equal:", bool(np.allclose(W1[:599], W2[:599])),
          "| full prefix [:600] equal:", bool(np.allclose(W1[:600], W2[:600])))

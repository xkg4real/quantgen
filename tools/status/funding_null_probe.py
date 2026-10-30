"""Independent synthetic null, no market data/cards/ledger; not a gate study.

Compares the retired IID sign frequency with the exploratory phase diagnostic.
The AR(1) simulation is a stress probe, not proof of the circular-phase null.
"""
import argparse
import json
import numpy as np
from core.crypto.funding_diagnostic import phase_diagnostic


def probe(repetitions=300):
    p_old=[];p_new=[];group_sizes=[]
    for seed in range(repetitions):
        rng=np.random.default_rng(60000+seed);n=730;burn=1000
        f=np.zeros(n+burn);noise=rng.normal(size=len(f))
        for i in range(1,len(f)):f[i]=.98*f[i-1]+noise[i]
        f=f[burn:];r=rng.normal(0,.02,n-1)
        signal=np.convolve(f,np.ones(7)/7,'valid')[:-30]
        forward=np.convolve(r,np.ones(30),'valid')[6:]
        lo,hi=np.quantile(signal,[.1,.9]);top=forward[signal>=hi];bottom=forward[signal<=lo]
        # Independently reconstruct the OLD algorithm (IID draws within groups).
        oldrng=np.random.default_rng(3)
        draws=np.array([oldrng.choice(top,len(top)).mean()-oldrng.choice(bottom,len(bottom)).mean() for _ in range(2000)])
        p_old.append(float(np.mean(draws>=0)))
        p_new.append(phase_diagnostic(signal,forward,30)['p_lower'])
        group_sizes.append([len(top),len(bottom)])
    return dict(scenario='Independent Gaussian BTC log increments and stationary-burn-in AR1 funding phi=.98',
        days=730,horizon=30,window=7,repetitions=repetitions,simulation_seed_start=60000,
        legacy_bootstrap_seed=3,legacy_draws=2000,
        old_fraction_below_005=float(np.mean(np.array(p_old)<.05)),
        phase_fraction_below_005=float(np.mean(np.array(p_new)<.05)),
        phase_assumptions='Uniform relative cyclic phase; not verified for real data',
        min_group_counts=np.min(group_sizes,axis=0).tolist(),
        historical_card_revalidated=False,old_p=p_old,phase_p=p_new)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repetitions',type=int,default=300)
    args=parser.parse_args()
    if not 1<=args.repetitions<=1000:parser.error('repetitions must be 1..1000')
    print(json.dumps(probe(args.repetitions),indent=2))

#!/usr/bin/env python3
"""Continue only numerically unconverged completed cases; never waive mesh/wall gates."""
import argparse,concurrent.futures,json
from auswerten import H,measure,main
from rechnen import one
NUMERICAL={'at_least_200_iterations','force_std_below_3_percent','force_drift_below_2_percent','power_std_below_3_percent','power_drift_below_2_percent','velocity_residual_below_1e4','pressure_residual_below_1e4','mass_imbalance_below_1_percent'}
def continue_one(rank,max_iteration):
    case=H/'cases'/f'K{rank:02d}_coarse'
    for _ in range(4):
        r=measure(case)
        if r['accepted']:print('ACCEPTED',rank,flush=True);return
        failed={k for k,v in r.get('checks',{}).items() if not v}
        if not failed or not failed<=NUMERICAL:print('NOT NUMERICAL-ONLY',rank,sorted(failed),flush=True);return
        last=r.get('lastIteration',0)
        if last>=max_iteration:print('LIMIT REACHED',rank,last,flush=True);return
        target=min(max_iteration,int(last)+250)
        if one(rank,'coarse','auto',target):return
    print('CONTINUATION LIMIT',rank,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ranks',default=','.join(map(str,range(1,11))));p.add_argument('--max-iteration',type=int,default=1250);p.add_argument('--jobs',type=int,default=2);a=p.parse_args();assert 1<=a.jobs<=2
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:list(ex.map(lambda i:continue_one(i,a.max_iteration),map(int,a.ranks.split(','))))
    main()

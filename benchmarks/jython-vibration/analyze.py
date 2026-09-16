"""Descriptive saturation assessment; no hard-coded input-count decisions."""
import json, math, statistics
from pathlib import Path

def slope(points):
    if len(points)<3:return None
    tx=statistics.mean(x for x,y in points);ty=statistics.mean(y for x,y in points)
    d=sum((x-tx)**2 for x,y in points)
    return sum((x-tx)*(y-ty) for x,y in points)/d if d else None

def assess(run):
    c=run['config'];s=run['summary'];duration=c['records']*c['interval_ms']/1000
    end=min(duration-2,run['input_duration_s']-.2)
    points=[]
    for row in run['samples']:
        if row['missed_flags']:break
        if 10<=row['seconds']<=end:
            points.append((row['seconds'],row['published']-row['worker_entries']))
    blocks=[]
    for start in range(10,int(end),10):
        # Require a full block: partial final windows distort means.
        ys=[y for x,y in points if start<=x<start+10]
        if start+10<=end and len(ys)>=7:blocks.append(dict(start=start,mean=statistics.mean(ys)))
    overall=slope(points);tail=slope([p for p in points if p[0]>=end-20])
    # A descriptive deadband, not a statistical confidence bound or proof of zero drift.
    tolerance=max(.1,c['channels']*1000/c['interval_ms']*.005)
    rising=len(blocks)>=3 and all(b['mean']>a['mean'] for a,b in zip(blocks,blocks[1:]))
    integrity=any(s.get(k,0) for k in ['wrong','duplicates','unknown','write_failures']) or run.get('observer_error')
    if c['preflight']:state='Correctness passed' if run['numerical_pass'] else 'Correctness failed'
    elif integrity:state='Invalid: measurement or result error'
    elif not run['generator_valid']:state='Invalid: publisher missed schedule'
    elif s['missed_flags']:state='Overloaded: missed events'
    elif run.get('error'):state='Stopped: '+run['error']
    elif overall is not None and tail is not None and overall>tolerance and tail>tolerance and rising:state='Overloaded: sustained backlog growth'
    elif rising and overall is not None and tail is not None and overall>0 and tail>0:state='Inconclusive: small persistent growth; run longer'
    elif len(points)>=35 and run['numerical_pass'] and overall<=tolerance and tail<=tolerance:state='Held during observation'
    else:state='Inconclusive: extend or repeat'
    return dict(run_id=run['run_id'],inputs=c['channels'],interval_ms=c['interval_ms'],state=state,preflight=c['preflight'],queue_slope=overall,tail_slope=tail,blocks=blocks,tolerance_jobs_s=tolerance,published=s['published'],verified=s['verified'],missed_flags=s['missed_flags'],duration_s=run['input_duration_s'],max_lateness_ms=run['max_generator_lateness_ms'])

def collect(path):
    runs=[]
    for f in sorted(Path(path).glob('Jython-*.json')):
        r=json.loads(f.read_text());runs.append(dict(assessment=assess(r),raw=r))
    return runs
if __name__=='__main__':
    import sys
    rows=[r['assessment'] for r in collect(sys.argv[1] if len(sys.argv)>1 else 'results')]
    print(json.dumps(rows,indent=2))

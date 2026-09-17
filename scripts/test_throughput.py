"""Check that startup and successful draining cannot hide sustained overload."""
import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'benchmarks/jython-vibration/project/ignition/script-python/throughput_summary/code.py'
s=importlib.util.spec_from_file_location('rates',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
r=dict(run_id='test',config=dict(channels=100,interval_ms=1000),input_duration_s=60,generator_valid=True,summary=dict(wrong=0,missed_flags=0),samples=[dict(seconds=t,published=100*min(t,60),verified=min(80*t,6000),worker_entries=min(80*t+3,6000)) for t in range(81)])
p=m.summarize(r)
assert p['offered']==100 and p['completed']==80 and p['queue_growth']==20
r['summary']['missed_flags']=1
assert m.summarize(r)['queue_growth'] is None
r['summary']['missed_flags']=0
r['generator_valid']=False
assert m.summarize(r)['measured'] is None and m.summarize(r)['invalid']==80
r['input_duration_s']=15
assert m.summarize(r) is None
r['config']['preflight']=True
assert m.summarize(r) is None
print('Throughput checks passed: sustained overload, drain exclusion, invalid schedule, short runs, preflight.')
r['config']['preflight']=False
r['input_duration_s']=60
r['generator_valid']=True
r['numerical_pass']=True
assert 'fell behind' in m.scan_stop_reason(r,m.summarize(r))
r['summary']['missed_flags']=1
assert 'missed events' in m.scan_stop_reason(r,m.summarize(r))
r['summary']['missed_flags']=0
r['generator_valid']=False
assert 'publisher' in m.scan_stop_reason(r,m.summarize(r))
r['generator_valid']=True
r['numerical_pass']=False
assert 'incomplete' in m.scan_stop_reason(r,m.summarize(r))
r['numerical_pass']=True
for row in r['samples']:row['verified']=row['published'];row['worker_entries']=row['published']
assert m.scan_stop_reason(r,m.summarize(r)) is None
assert 'enough' in m.scan_stop_reason(r,None)
print('Automatic scan stop criteria passed.')
# End-to-end search trajectories, including a failure below the initial probe.
for limit in [0,1,4,85,130,300,500]:
    scan=dict(low=0,high=None,current=100,index=1)
    seen=[]
    for _ in range(20):
        n=scan['current'];seen.append(n)
        result=dict(config=dict(channels=n),summary={},generator_valid=True,numerical_pass=True)
        point=dict(offered=n,completed=n if n<=limit else n*.8,queue_growth=0 if n<=limit else n*.2+1)
        target,conclusion=m.search_step(scan,result,point)
        if conclusion:break
    else:raise AssertionError('Search did not converge')
    assert len(seen)==len(set(seen)),seen
    if limit==500:assert scan['low']==500 and scan['high'] is None
    else:assert scan['low']<=limit<scan['high'] and scan['high']-scan['low']<5
scan=dict(low=50,high=100,current=75,index=3)
result=dict(config=dict(channels=75),summary={},generator_valid=False,numerical_pass=True)
assert m.search_step(scan,result,None)[0] is None
assert scan['low']==50 and scan['high']==100
result.update(generator_valid=True,numerical_pass=False,error='Jython missedEvents / input overflow',summary={'missed_flags':1})
assert m.search_step(scan,result,None)[0]==62
print('Adaptive search verified across boundaries 0–500; invalid runs preserve bracket; early missed events establish overload.')
rows=[dict(seconds=t,published=100*t,worker_entries=80*t,verified=80*t) for t in range(22)]
assert m.early_overload(rows)
assert not m.early_overload(rows[:15])
for row in rows:row['worker_entries']=row['published']-10;row['verified']=row['published']-12
assert not m.early_overload(rows) # initial backlog that settles
for row in rows:row['worker_entries']=row['published']-max(0,40-row['seconds']);row['verified']=row['worker_entries']
assert not m.early_overload(rows) # backlog drains
scan=dict(low=50,high=None,current=100,index=1)
r2=dict(config=dict(channels=100),summary={},generator_valid=True,numerical_pass=False,early_overload=True)
assert m.search_step(scan,r2,None)[0]==75
print('Early overload checks passed: sustained growth, startup rejection, settled and draining queues, bisection after early stop.')
rows=[dict(seconds=t,published=100*t,worker_entries=80*t,verified=80*t) for t in range(15)]
p=m.live_point(rows,{'channels':100,'interval_ms':1000},'live-test')
assert p['offered']==100 and p['live']==80 and p['measured'] is None
assert m.live_point(rows[:2],{'channels':100},'short') is None
assert m.live_point(rows,{'preflight':True},'preflight') is None
print('Live point verified against actual counter rates; no provisional capacity result.')

rows=[dict(seconds=t,published=100,worker_entries=90,completed=90,missed_flags=1) for t in range(10,17)]
assert m.loss_drain_quiet(rows,10)
assert not m.loss_drain_quiet(rows,13)
rows[-1]['completed']=89
assert not m.loss_drain_quiet(rows,10)
rows[-1]['completed']=90;rows[0]['worker_entries']=89
assert not m.loss_drain_quiet(rows,10)
print('Loss drain checks passed: quiet window, recent input, active callback, changing counters.')

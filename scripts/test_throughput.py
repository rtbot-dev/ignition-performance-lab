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

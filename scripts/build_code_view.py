"""Generate a local read-only source view from the shipped computation itself."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
project=root/'benchmarks/jython-vibration/project'
code=(project/'ignition/script-python/benchmark_full/code.py').read_text()
digest=hashlib.sha256(code.encode()).hexdigest()
source='Each tag event passes one acceleration burst to `calculate(payload)`. This module computes the indicators and contains the independent reference and result ledger.\n\nThis read-only view is generated from the shipped source; editing it does not change the running script.\n\nSHA-256: `'+digest+'`\n\n```python\n'+code+'\n```'
intro = '''# The computation running in this lab

We deliberately simulate a heavy analytics workload to push processing toward saturation and make the limits visible. The computation itself is real: each acceleration burst is processed into vibration condition indicators.

**Capacity varies widely with the specific computation, input cadence and available hardware.** The input count measured here is not a general limit for Ignition. Our goal is to show customers how to find the limits of their own workloads by increasing input and watching for sustained queue growth or missed events.

If you need help with real-time analytics and machine learning for industrial applications, [please reach out to Katenaria](mailto:services@katenaria.com).
'''
button={'type':'ia.input.button','meta':{'name':'Back'},'props':{'text':'Back to experiment'},'position':{'basis':'42px','shrink':0},'events':{'component':{'onActionPerformed':{'type':'script','scope':'G','config':{'script':'\tsystem.perspective.navigate(page="/")'}}}}}
view={'custom':{},'params':{},'props':{'defaultSize':{'width':1200,'height':850}},'root':{'type':'ia.container.flex','meta':{'name':'root'},'props':{'direction':'column','style':{'padding':'24px','gap':'16px','overflow':'auto','backgroundColor':'#f3f7f8'}},'children':[button,{'type':'ia.display.markdown','meta':{'name':'Purpose'},'props':{'source':intro},'position':{'basis':'auto','shrink':0}},{'type':'ia.container.flex','meta':{'name':'SectionSpacing'},'props':{},'position':{'basis':'32px','grow':0,'shrink':0}}, {'type':'ia.display.markdown','meta':{'name':'Code'},'props':{'source':source},'position':{'basis':'auto','shrink':0}}]}}
p=project/'com.inductiveautomation.perspective/views/Computation';p.mkdir(exist_ok=True)
(p/'view.json').write_text(json.dumps(view,indent=2)+'\n')
(p/'resource.json').write_text(json.dumps({'scope':'DG','version':1,'restricted':False,'overridable':True,'files':['view.json'],'attributes':{}})+'\n')

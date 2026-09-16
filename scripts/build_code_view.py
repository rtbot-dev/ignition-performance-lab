"""Generate a local read-only source view from the shipped computation itself."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
project=root/'benchmarks/jython-vibration/project'
code=(project/'ignition/script-python/benchmark_full/code.py').read_text()
digest=hashlib.sha256(code.encode()).hexdigest()
source='# The computation running in this lab\n\nEach tag event passes one acceleration burst to `calculate(payload)`. This module computes the indicators and contains the independent reference and result ledger.\n\nThis read-only view is generated from the shipped source; editing it does not change the running script.\n\nSHA-256: `'+digest+'`\n\n```python\n'+code+'\n```'
button={'type':'ia.input.button','meta':{'name':'Back'},'props':{'text':'Back to experiment'},'position':{'basis':'42px','shrink':0},'events':{'component':{'onActionPerformed':{'type':'script','scope':'G','config':{'script':'\tsystem.perspective.navigate(page="/")'}}}}}
view={'custom':{},'params':{},'props':{'defaultSize':{'width':1200,'height':850}},'root':{'type':'ia.container.flex','meta':{'name':'root'},'props':{'direction':'column','style':{'padding':'24px','gap':'16px','overflow':'auto','backgroundColor':'#f3f7f8'}},'children':[button,{'type':'ia.display.markdown','meta':{'name':'Code'},'props':{'source':source},'position':{'basis':'auto','shrink':0}}]}}
p=project/'com.inductiveautomation.perspective/views/Computation';p.mkdir(exist_ok=True)
(p/'view.json').write_text(json.dumps(view,indent=2)+'\n')
(p/'resource.json').write_text(json.dumps({'scope':'DG','version':1,'restricted':False,'overridable':True,'files':['view.json'],'attributes':{}})+'\n')

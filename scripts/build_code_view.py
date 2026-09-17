"""Generate a local read-only source view from the shipped computation itself."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
project=root/'benchmarks/jython-vibration/project'
code=(project/'ignition/script-python/benchmark_full/code.py').read_text()
digest=hashlib.sha256(code.encode()).hexdigest()
source='Each tag event passes one acceleration burst to `calculate(payload)`. This module computes the indicators and contains the independent reference and result ledger.\n\nThis read-only view is generated from the shipped source; editing it does not change the running script.\n\nSHA-256: `'+digest+'`\n\n```python\n'+code+'\n```'
intro = """# The computation running in this lab

We deliberately use a heavy workload to make saturation visible: each acceleration burst is processed into vibration condition indicators.

Capacity varies widely with the computation, input cadence and hardware. Our goal is to show customers how to find the limits of their own workloads by increasing input and watching for sustained queue growth or missed events.
"""
button={'type':'ia.input.button','meta':{'name':'Back'},'props':{'text':'Back to experiment'},'position':{'basis':'42px','shrink':0},'events':{'component':{'onActionPerformed':{'type':'script','scope':'G','config':{'script':'\tsystem.perspective.navigate(page="/")'}}}}}
def markdown(name, text, style):
    return {'type':'ia.display.markdown','meta':{'name':name},'props':{'source':text,'style':style},'position':{'basis':'auto','shrink':0}}

explanation, code_block = source.split('```python', 1)
body_style = {'fontSize':'16px','lineHeight':'1.65','color':'#244152','maxWidth':'940px','width':'100%','alignSelf':'center'}
contact = 'Need help with real-time analytics or machine learning for industrial applications? [Talk to Katenaria](mailto:services@katenaria.com).'
button['props']['style']={'backgroundColor':'#103641','color':'white','borderRadius':'6px','width':'190px','alignSelf':'flex-start'}
view={'custom':{},'params':{},'props':{'defaultSize':{'width':1200,'height':850}},'root':{'type':'ia.container.flex','meta':{'name':'root'},'props':{'direction':'column','style':{'padding':'28px','gap':'0px','overflow':'auto','backgroundColor':'#f3f7f8'}},'children':[
    button,
    markdown('Purpose',intro,dict(body_style,marginTop='24px',marginBottom='16px')),
    markdown('Explanation',explanation,dict(body_style,fontSize='14px',color='#526875',marginBottom='16px')),
    markdown('Contact',contact,dict(body_style,fontSize='13px',color='#607580',borderTop='1px solid #d6e1e5',paddingTop='12px',paddingBottom='24px')),
    markdown('Code','```python'+code_block,{'fontSize':'13px','lineHeight':'1.5','width':'100%','maxWidth':'1100px','alignSelf':'center','padding':'16px','backgroundColor':'#ffffff','border':'1px solid #dce5e8','borderRadius':'8px','boxSizing':'border-box'})
]}}
p=project/'com.inductiveautomation.perspective/views/Computation';p.mkdir(exist_ok=True)
(p/'view.json').write_text(json.dumps(view,indent=2)+'\n')
(p/'resource.json').write_text(json.dumps({'scope':'DG','version':1,'restricted':False,'overridable':True,'files':['view.json'],'attributes':{}})+'\n')

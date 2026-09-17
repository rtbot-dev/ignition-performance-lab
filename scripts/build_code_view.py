"""Generate a local read-only source view from the shipped computation itself."""
from pathlib import Path
import json,hashlib,copy,html,io,keyword,tokenize
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
contact = 'Real-time analytics and machine learning for industrial applications. Follow us or reach out on LinkedIn.'
main_view=json.loads((project/'com.inductiveautomation.perspective/views/PerformanceLab/view.json').read_text())
def find_component(node,name):
    if node.get('meta',{}).get('name')==name:return node
    for child in node.get('children',[]):
        found=find_component(child,name)
        if found:return found
social=copy.deepcopy(find_component(main_view['root'],'LinkedInFollow'))
social['meta']['name']='LinkedInContact'
social['props']['text']='Follow us on LinkedIn'
social['props']['style'].update(width='218px',fontSize='13px',padding='0 14px')
social['props']['image'].update(width=18,height=18)
social['position']={'basis':'36px','grow':0,'shrink':0}
contact_box={'type':'ia.container.flex','meta':{'name':'Contact'},'props':{'direction':'column','alignItems':'flex-start','style':{'width':'100%','maxWidth':'940px','alignSelf':'center','borderTop':'1px solid #d6e1e5','paddingTop':'12px','paddingBottom':'24px','gap':'10px'}},'position':{'basis':'auto','shrink':0},'children':[markdown('ContactCopy',contact,{'fontSize':'13px','color':'#607580'}),social]}

# Static, escaped HTML: no browser scripts or external syntax-highlighting service.
offsets=[0]
for line in code.splitlines(True):offsets.append(offsets[-1]+len(line))
parts=[];cursor=0
for token in tokenize.generate_tokens(io.StringIO(code).readline):
    start=offsets[min(token.start[0]-1,len(offsets)-1)]+token.start[1]
    end=offsets[min(token.end[0]-1,len(offsets)-1)]+token.end[1]
    if end<=start or start<cursor:continue
    color=None
    if token.type==tokenize.STRING:color='#0a3069'
    elif token.type==tokenize.COMMENT:color='#6e7781'
    elif token.type==tokenize.NUMBER:color='#0550ae'
    elif token.type==tokenize.NAME and keyword.iskeyword(token.string):color='#cf222e'
    elif token.type==tokenize.NAME and token.string in ('self','math','threading'):color='#8250df'
    parts.append(html.escape(code[cursor:start]))
    text=html.escape(code[start:end])
    parts.append('<span style="color:%s">%s</span>'%(color,text) if color else text)
    cursor=end
parts.append(html.escape(code[cursor:]))
highlighted='<pre style="margin:0;white-space:pre;overflow-x:auto;color:#24292f"><code>'+''.join(parts)+'</code></pre>'
code_component=markdown('Code',highlighted,{'fontSize':'13px','lineHeight':'1.6','width':'100%','maxWidth':'1100px','alignSelf':'center','padding':'20px','backgroundColor':'#ffffff','border':'1px solid #dce5e8','borderRadius':'8px','boxSizing':'border-box','overflow':'auto'})
code_component['props']['markdown']={'escapeHtml':False,'skipHtml':False}
button['props']['style']={'backgroundColor':'#103641','color':'white','borderRadius':'6px','width':'190px','alignSelf':'flex-start'}
view={'custom':{},'params':{},'props':{'defaultSize':{'width':1200,'height':850}},'root':{'type':'ia.container.flex','meta':{'name':'root'},'props':{'direction':'column','style':{'padding':'28px','gap':'0px','overflow':'auto','backgroundColor':'#f3f7f8'}},'children':[
    button,
    markdown('Purpose',intro,dict(body_style,marginTop='24px',marginBottom='16px')),
    markdown('Explanation',explanation,dict(body_style,fontSize='14px',color='#526875',marginBottom='16px')),
    contact_box,
    markdown('Language','**Python**',{'fontSize':'12px','color':'#526875','width':'100%','maxWidth':'1100px','alignSelf':'center','marginBottom':'8px'}),
    code_component
]}}
p=project/'com.inductiveautomation.perspective/views/Computation';p.mkdir(exist_ok=True)
(p/'view.json').write_text(json.dumps(view,indent=2)+'\n')
(p/'resource.json').write_text(json.dumps({'scope':'DG','version':1,'restricted':False,'overridable':True,'files':['view.json'],'attributes':{}})+'\n')

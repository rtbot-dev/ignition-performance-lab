"""Local Perspective controls; numerical callback remains unchanged."""
import json, os
import system
import load_benchmark as original
import throughput_summary
from java.lang import System, Runtime
from java.lang.management import ManagementFactory
ROOT='/bench'
BASE='[default]PerformanceLab/'

def save(name,value):
    path=ROOT+'/'+name
    with open(path+'.tmp','w') as f:json.dump(value,f,indent=2)
    os.rename(path+'.tmp',path)

def write(values):
    names=list(values)
    system.tag.writeBlocking([BASE+n for n in names],[values[n] for n in names])

def tick():
    g=system.util.getGlobals()
    try:
        if original.KEY not in g:
            system.tag.configure('[default]',[dict(name='LoadBenchmark',tagType='Folder',tags=[original.spec('Armed','Boolean',True)])],'m')
            g[original.KEY]=original.Harness()
            g[original.KEY].state='Ready. Choose a load, then run.'
            defs=[('Inputs','Int4',40),('Cadence','Int4',1000),('Duration','Int4',60),('Command','String',''),('Busy','Boolean',False),('Status','String','Ready. Choose a load, then run.'),('History','Document',[]),('Published','Int8',0),('Started','Int8',0),('Verified','Int8',0),('Waiting','Int8',0),('Missed','Int8',0),('Wrong','Int8',0),('Heap','Float8',0),('CPU','Float8',0),('Late','Float8',0),('Config','String',''),('LastResult','String','No run yet')]
            system.tag.configure('[default]',[dict(name='PerformanceLab',tagType='Folder',tags=[original.spec(*x) for x in defs])],'o')
            g['lab.trace']=[];g['lab.origin']=System.nanoTime()
            runtime=Runtime.getRuntime()
            env=dict(java=str(System.getProperty('java.version')),os=str(System.getProperty('os.name')),architecture=str(System.getProperty('os.arch')),visible_cpus=runtime.availableProcessors(),max_heap_bytes=runtime.maxMemory(),jvm_arguments=[str(x) for x in ManagementFactory.getRuntimeMXBean().getInputArguments() if not str(x).startswith('-Dwrapper.')],workers=int(System.getProperty('ignition.tags.scriptthreads','3')),queue_per_tag=int(System.getProperty('ignition.tags.scriptqueuemaxsize','5')))
            save('results/environment.json',env)
            write({'Config':'%s visible CPUs | %s Jython workers | %.1f GiB maximum JVM heap | 5 queued events per tag'%(env['visible_cpus'],env['workers'],env['max_heap_bytes']/1073741824.)})
        if 'lab.throughput' not in g:
            try:
                with open(ROOT+'/results/throughput.json') as f:g['lab.throughput']=json.load(f)
            except (IOError, ValueError):g['lab.throughput']=[]
            system.tag.configure(BASE.rstrip('/'),[original.spec('Throughput','Document',g['lab.throughput'])],'m')
        h=g[original.KEY];was=h.active;h.tick();now=System.currentTimeMillis()
        if was and not h.active:
            result=h.history[-1]
            point=throughput_summary.summarize(result)
            if point:
                g['lab.throughput']=(g['lab.throughput']+[point])[-100:]
                save('results/throughput.json',g['lab.throughput'])
                write({'Throughput':g['lab.throughput']})
            save('results/resources-'+result['run_id']+'.json',dict(run_id=result['run_id'],cpu_definition='100 percent = one CPU equivalent',heap_definition='used JVM heap / maximum JVM heap',samples=g.get('lab.trace',[])))
            write({'LastResult':result['run_id']+'.json'})
            if result['summary']['outstanding'] and not result['summary']['missed_flags']:
                g['lab.error']='Unfinished work after drain. Restart the lab before another run.'
            if result['config']['preflight'] and not result['numerical_pass']:
                g['lab.error']='Correctness check failed; inspect results before running.'
            if g.get('lab.pending'):
                g['lab.prepared']=False;g['lab.when']=now+5000
        vals=system.tag.readBlocking([BASE+n for n in ['Command','Inputs','Cadence','Duration']])
        command=str(vals[0].value)
        if command:
            write({'Command':''})
            if command=='stop':
                g.pop('lab.pending',None);h.stop()
            elif command=='run' and not h.active and not g.get('lab.pending') and not g.get('lab.error'):
                inputs=int(vals[1].value);cadence=int(vals[2].value);duration=int(vals[3].value)
                if not (1<=inputs<=500 and 250<=cadence<=10000 and 10<=duration<=180):
                    write({'Status':'Choose 1-500 inputs, 0.25-10 s cadence and 10-180 s duration.'});return
                records=max(1,int(duration*1000./cadence))
                if inputs*records>200000:
                    write({'Status':'Reduce input count or duration: maximum 200,000 bursts per run.'});return
                g['lab.pending']=(inputs,records,cadence)
                g['lab.prepared']=False;g['lab.when']=now+3000
                if 'Jython' not in h.preflight_pass:
                    h.configure(2,'Jython');g['lab.check']=True
        if g.get('lab.pending') and not h.active and not g.get('lab.error') and now>=g.get('lab.when',0):
            if g.pop('lab.check',False):
                h.start('Jython',2,4,2000,True,'staggered')
                g['lab.trace']=[];g['lab.origin']=System.nanoTime()
            elif not g.get('lab.prepared'):
                h.configure(g['lab.pending'][0],'Jython');g['lab.prepared']=True;g['lab.when']=now+3000
            else:
                inputs,records,cadence=g.pop('lab.pending')
                h.start('Jython',inputs,records,cadence,False,'staggered')
                g['lab.trace']=[];g['lab.origin']=System.nanoTime()
        if os.path.exists(ROOT+'/runtime/STOP'):
            g.pop('lab.pending',None);h.stop()
        s=h.ledger.snapshot();runtime=Runtime.getRuntime()
        heap=100.*(runtime.totalMemory()-runtime.freeMemory())/runtime.maxMemory()
        # JVM CPU time / wall time = CPU equivalents (100% = one fully busy CPU).
        cpu_ns=ManagementFactory.getOperatingSystemMXBean().getProcessCpuTime()
        stamp=System.nanoTime();previous=g.get('lab.cpu')
        cpu=max(0.,100.*(cpu_ns-previous[0])/(stamp-previous[1])) if previous and stamp>previous[1] else 0.
        g['lab.cpu']=(cpu_ns,stamp)
        waiting=max(0,s['published']-s['worker_entries'])
        if h.active:
            g['lab.trace'].append(dict(seconds=round((stamp-g['lab.origin'])/1e9,1),waiting=None if s['missed_flags'] else waiting,heap=heap,cpu=cpu))
            g['lab.trace']=g['lab.trace'][-240:]
        status=g.get('lab.error') or ('Checking numerical correctness before your first run...' if h.active and h.config.get('preflight') else ('Preparing input tags...' if g.get('lab.pending') and not h.active else h.state))
        if s['missed_flags']:status='Overload detected: missed events. '+('Draining submitted work...' if h.active else 'Input stopped; trace and raw results preserved.')
        write(dict(Busy=bool(h.active or g.get('lab.pending')),Status=status,History=g['lab.trace'],Published=s['published'],Started=s['worker_entries'],Verified=s['verified'],Waiting=-1 if s['missed_flags'] else waiting,Missed=s['missed_flags'],Wrong=s['wrong'],Heap=heap,CPU=cpu,Late=getattr(h,'max_lateness_ms',0)))
        save('results/status.json',dict(active=h.active,state=status,counts=s,last_result=h.history[-1]['run_id'] if h.history else None))
    except Exception as e:
        save('results/adapter-error.json',dict(error=str(e)))
        system.util.getLogger('DockerBenchmark').error(str(e))
        try:write({'Status':'Lab error: '+str(e)})
        except:pass

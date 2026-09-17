"""Gateway harness. Idle by default; no timed stage starts on import."""
import json
import math
import os
import threading
import system
from java.lang import System, Runtime
from java.util import Date
from com.inductiveautomation.ignition.gateway.tags.managed import ManagedTagProviderConfiguration
from com.inductiveautomation.ignition.common.sqltags.model.types import DataType
from java.util.concurrent import TimeUnit
from com.inductiveautomation.ignition.gateway import IgnitionGateway
from com.inductiveautomation.ignition.common.tags.paths.parser import TagPathParser
from com.inductiveautomation.ignition.common.tags.model.event import TagChangeListener
from com.inductiveautomation.ignition.common.model.values import BasicQualifiedValue, QualityCode
import benchmark_full as benchmark_core
import benchmark_corpus

ROOT='[default]LoadBenchmark'
KEY='katenaria.load.benchmark.v1'
VERSION=16
FIELDS=benchmark_core.FIELDS

def tag(name):return ROOT+'/'+name

def write(names,values):return system.tag.writeBlocking([tag(n) for n in names],values)

def spec(name,typ,value):
    return dict(name=name,tagType='AtomicTag',valueSource='memory',dataType=typ,value=value,deadbandMode='Off')

def private_field(obj,name):
    field=obj.getClass().getDeclaredField(name)
    field.setAccessible(True)
    return field.get(obj)

def native_metrics():
    raise ValueError('This package benchmarks Jython only')

class OutputListener(TagChangeListener):
    def __init__(self,owner):self.owner=owner
    def tagChanged(self,event):
        try:self.owner.output(event)
        except Exception as e:
            self.owner.observer_error=str(e)
            self.owner.cancel.set()

class Harness(object):
    def __init__(self):
        self.version=VERSION
        self.lock=threading.RLock()
        self.cancel=threading.Event()
        self.active=False
        self.state='Idle / correctness checks only until armed'
        self.corpus=json.loads(benchmark_corpus.DATA)
        for item in self.corpus:item["reference"]=benchmark_core.reference(item["payload"])
        self.ledger=benchmark_core.Ledger()
        self.listeners=[]
        self.listener=OutputListener(self)
        self.partial={}
        self.observer_error=''
        self.run_id=''
        self.native={}
        self.samples=[]
        self.last_sample=0
        self.mode=''
        self.history=[]
        self.started=0
        self.config={}
        self.phase='idle'
        self.generator_error=''
        self.input_done=False
        self.max_lateness_ms=0
        self.preflight_pass=set()
        self.configured_counts={"Jython":0,"Coprocessor":0}
        config=ManagedTagProviderConfiguration.builder('LoadBenchmark').allowTagCustomization(True).allowTagDeletion(True).persistTags(False).hasDataTypes(True).build()
        self.provider=IgnitionGateway.get().getTagManager().getOrCreateManagedProvider(config)
        self.configure(2,'Jython')

    def configure(self,channels,only_mode=None):
        if self.active:raise ValueError('Stop and drain before configuring')
        if not 1<=channels<=50000:raise ValueError('Channel limit is 50000')
        script="""if not initialChange:
    import system
    h=system.util.getGlobals().get('katenaria.load.benchmark.v1')
    if h is not None:
        h.on_input(tagPath,currentValue,missedEvents)
"""
        script += '# Refresh benchmark event binding '+str(System.nanoTime())+'\n'
        for mode in ([only_mode] if only_mode else ['Jython','Coprocessor']):
            for channel in range(self.configured_counts.get(mode,0),channels):
                # Preparation is outside the timed workload. Stop before tag creation
                # exhausts the gateway heap, including when no input is running.
                if channel % 50 == 0:
                    rt=Runtime.getRuntime()
                    if (rt.totalMemory()-rt.freeMemory())/float(rt.maxMemory())>.75:
                        System.gc()
                        if (rt.totalMemory()-rt.freeMemory())/float(rt.maxMemory())>.75:
                            raise ValueError('Preparation heap safety limit at %d %s channels'%(channel,mode))
                name='%04d'%channel
                if not system.tag.exists('[LoadBenchmark]'+mode+'/'+name+'/Burst'):
                    self.provider.configureTag(mode+'/'+name+'/Burst',DataType.String)
                if mode=='Jython':
                    result=system.tag.configure('[LoadBenchmark]Jython/'+name,[dict(name='Burst',eventScripts=[dict(eventid='valueChanged',script='\n'.join('\t'+line for line in script.splitlines()),enabled=True)])],'m')
                    if not all(q.isGood() for q in result):raise ValueError('Tag script configuration failed')
                    self.provider.updateValue(mode+'/'+name+'/Burst','',QualityCode.Good,Date(System.currentTimeMillis()))
                    for f in FIELDS:self.provider.configureTag('JythonResults/'+name+'/'+f,DataType.Float8)
                self.configured_counts[mode]=channel+1
        self.channels=channels

    def on_input(self,path,value,missed):
        self.raw_callbacks=getattr(self,'raw_callbacks',0)+1
        if not self.active or self.mode!='Jython':return
        channel=str(path).split('/')[-2]
        source_ms=value.timestamp.getTime()
        seq=int((source_ms-self.base_ms)//2000)
        key=(channel,seq)
        if source_ms!=self.base_ms+seq*2000 or key not in self.ledger.jobs:
            self.rejected_callbacks=getattr(self,'rejected_callbacks',0)+1
            return
        self.ledger.enter(missed)
        if missed:
            system.util.getLogger("LoadBenchmark.MissedEvents").warn("Ignition reported missedEvents: run=%s tag=%s sequence=%s"%(self.run_id,path,seq))
        try:
            values=benchmark_core.calculate(str(value.value))
            stamp=Date(source_ms+1024)
            for f in FIELDS:
                self.provider.updateValue('JythonResults/'+channel+'/'+f,values[f],QualityCode.Good,stamp)
        except Exception as e:
            self.generator_error='Jython calculation: '+str(e);self.cancel.set()

    def subscribe(self):
        self.unsubscribe()
        paths=[]
        for channel in range(self.channels):
            name='%04d'%channel
            base=('[Coprocessor]load-benchmark/'+name if self.mode=='Coprocessor' else '[LoadBenchmark]JythonResults/'+name)
            if not system.tag.exists(base+'/rms_trend/sample_count'):
                raise ValueError('Missing output '+base+'; deploy Coprocessor and warm tags first')
            for folder,fields in benchmark_core.LAYOUT.items():
                qs=system.tag.configure(base+'/'+folder,[dict(name=f,deadbandMode='Off') for f in fields],'m')
                if not all(q.isGood() for q in qs):raise ValueError('Could not disable output deadband')
            paths.extend(TagPathParser.parse(base+'/'+f) for f in FIELDS)
        self.listeners=paths
        IgnitionGateway.get().getTagManager().subscribeAsync(paths,[self.listener]*len(paths)).get(10,TimeUnit.SECONDS)

    def unsubscribe(self):
        if self.listeners:
            IgnitionGateway.get().getTagManager().unsubscribeAsync(self.listeners,[self.listener]*len(self.listeners)).get(10,TimeUnit.SECONDS)
            self.listeners=[]

    def output(self,event):
        if not self.active:return
        q=event.getValue()
        if q is None or not q.quality.isGood():return
        path=str(event.getTagPath().toStringFull())
        pieces=path.split('/')
        field='/'.join(pieces[-2:])
        channel=pieces[-3]
        timestamp=q.timestamp.getTime()
        seq=int((timestamp-self.base_ms)//2000)
        # Disjoint logical 2-second slots carry identity through the numerical engine.
        if seq<0 or seq>=self.config['records']:return
        key=(channel,seq)
        if not self.base_ms+seq*2000<=timestamp<=self.base_ms+seq*2000+1025:
            raise ValueError('Output event timestamp outside its recording slot')
        with self.lock:
            # Completed jobs retain identity and validity, not all 22 values.
            if self.ledger.jobs.get(key,{}).get('done'):
                self.ledger.duplicates+=1
                return
            parts=self.partial.setdefault(key,{})
            if field in parts:
                # Duplicate deliveries cannot silently count as another completed job.
                self.ledger.duplicates+=1
                return
            parts[field]=float(q.value)
            if len(parts)==len(FIELDS):
                self.ledger.complete(key,parts,System.nanoTime())
                del self.partial[key]

    def start(self,mode,channels,records,interval_ms,preflight=True,arrival_pattern="staggered"):
        if arrival_pattern not in ["staggered","synchronized"]:raise ValueError("Unknown arrival pattern")
        if self.active:raise ValueError('A run is already active')
        if mode != 'Jython':raise ValueError('Unknown contender')
        if not preflight:
            armed=bool(system.tag.readBlocking([tag('Armed')])[0].value)
            if not armed or self.preflight_pass!=set(['Jython']):
                raise ValueError('Timed runs require Arm and both correctness checks')
        if preflight and (channels>2 or records>8):raise ValueError('Preflight capped at 16 jobs')
        if records*channels>200000:raise ValueError('Ledger capacity exceeded')
        if interval_ms<250:raise ValueError('Interval below supported pilot range')
        self.configure(channels,mode)
        self.mode=mode
        self.native={}
        self.native_start={}
        if mode=='Coprocessor':
            self.native_start=native_metrics()
            if self.native_start['instances']<channels:raise ValueError('Not enough runtimes; prepare and wait for discovery')
        self.subscribe()
        self.cancel.clear()
        self.partial={}
        self.ledger=benchmark_core.Ledger()
        self.observer_error=self.generator_error=''
        self.config=dict(workload='full-original-22-numeric-outputs',mode=mode,channels=channels,records=records,interval_ms=interval_ms,preflight=preflight,samples_per_burst=20480,arrival_pattern=arrival_pattern,experiment='breadth' if interval_ms>2000 else 'baseline')
        self.run_id=mode+'-'+str(System.currentTimeMillis())
        event_clock=system.util.getGlobals()
        self.base_ms=max((System.currentTimeMillis()//10000+2)*10000,event_clock.get(KEY+'.eventclock',0))
        event_clock[KEY+'.eventclock']=self.base_ms+records*2000+2000
        self.started=System.nanoTime()
        self.samples=[];self.last_sample=0;self.max_lateness_ms=0;self.early_overload=False
        self.heap_high_ticks=0
        self.input_done=False;self.raw_callbacks=0;self.rejected_callbacks=0;self.active=True;self.phase='publishing'
        self.state='Correctness check / '+mode if preflight else 'Measuring / '+mode
        system.util.invokeAsynchronous(self.generate,description='Benchmark open-loop publisher')

    def generate(self):
        try:
            count=self.config['channels'];interval=self.config['interval_ms']
            for seq in range(self.config['records']):
                for c in range(count):
                    if self.cancel.is_set():return
                    offset=c*interval/float(count) if self.config["arrival_pattern"]=="staggered" else 0
                    target=self.started+long((seq*interval+offset)*1e6)
                    while System.nanoTime()<target:
                        if self.cancel.wait(min(.01,(target-System.nanoTime())/1e9)):return
                    now=System.nanoTime()
                    late=max(0,(now-target)/1e6)
                    self.max_lateness_ms=max(self.max_lateness_ms,late)
                    channel='%04d'%c;key=(channel,seq)
                    item=self.corpus[(seq+c)%len(self.corpus)]
                    self.ledger.register(key,item['reference'],now,seq,channel)
                    payload=item['payload'].rsplit(',',1)[0]+','+str(-1000000000-(self.base_ms//2000)%100000000-seq)
                    self.provider.updateValue(self.mode+'/'+channel+'/Burst',payload,QualityCode.Good,Date(self.base_ms+seq*2000))
                    self.ledger.accepted(key,True)
        except Exception as e:
            self.generator_error=str(e);self.cancel.set()
        finally:
            self.input_end=System.nanoTime()
            self.phase='draining'
            # Publish completion last: the timer must not read the prior run's end time.
            self.input_done=True

    def stop(self):
        if not self.active:
            self.state='Idle / input already stopped'
            return
        self.cancel.set()
        self.state='Stopping input / draining accepted jobs'

    def tick(self):
        if not self.active:return
        now=System.nanoTime();snapshot=self.ledger.snapshot()
        if now-self.last_sample>=1000000000:
            self.last_sample=now
            row=dict(seconds=(now-self.started)/1e9,**snapshot)
            if self.mode=='Coprocessor':
                try:
                    self.native=native_metrics();row['native']=self.native
                    if self.native['dropped']>self.native_start['dropped'] or self.native['errors']>self.native_start['errors']:
                        self.generator_error='Native drop or error';self.cancel.set()
                except Exception as e:
                    self.generator_error='Native metrics unavailable: '+str(e);self.cancel.set()
            if self.samples:
                previous=self.samples[-1];dt=row['seconds']-previous['seconds']
                row['offered_bursts_s']=(row['published']-previous['published'])/dt
                row['verified_bursts_s']=(row['verified']-previous['verified'])/dt
            self.samples.append(row)
        if snapshot['wrong'] or snapshot['duplicates'] or snapshot['write_failures'] or self.observer_error:
            self.cancel.set()
        if self.mode=='Jython' and snapshot['missed_flags']:
            self.generator_error='Jython missedEvents / input overflow';self.cancel.set()
        if self.mode=='Jython' and now-self.started>3000000000 and snapshot['published']>0 and snapshot['worker_entries']==0:
            self.generator_error='Jython callback setup failure';self.cancel.set()
        # Bound retained CSV backlog and stop before it can exhaust gateway memory.
        if snapshot['outstanding']>min(4000, max(32,self.channels*8)):
            self.generator_error='Outstanding job safety limit';self.cancel.set()
        runtime=__import__('java.lang',fromlist=['Runtime']).Runtime.getRuntime()
        heap=(runtime.totalMemory()-runtime.freeMemory())/float(runtime.maxMemory())
        from java.lang.management import ManagementFactory
        # Allocation occupancy naturally reaches the GC threshold. Retained heap
        # after a collection distinguishes that cycle from actual memory pressure.
        retained=sum(p.getCollectionUsage().getUsed() for p in ManagementFactory.getMemoryPoolMXBeans()
                     if str(p.getType())=='Heap memory' and p.getCollectionUsage() is not None)/float(runtime.maxMemory())
        if self.samples:
            self.samples[-1]['heap_fraction']=heap
            self.samples[-1]['retained_heap_fraction']=retained
        self.heap_high_ticks=self.heap_high_ticks+1 if retained>.8 or heap>.98 else 0
        if self.heap_high_ticks>=3:
            self.generator_error='Gateway heap safety limit';self.cancel.set()
        quiet_after_loss=False
        if self.input_done and self.mode=='Jython' and snapshot['missed_flags']:
            import throughput_summary
            quiet_after_loss=throughput_summary.loss_drain_quiet(self.samples,(self.input_end-self.started)/1e9)
        if self.input_done and (snapshot['outstanding']==0 or quiet_after_loss or now-self.input_end>30000000000):
            self.finish(now,snapshot)

    def finish(self,now,snapshot):
        self.active=False;self.phase='idle'
        snapshot=self.ledger.snapshot(exact=True)
        expected=self.config['channels']*self.config['records']
        complete=(snapshot['verified']==expected and not snapshot['wrong'] and not snapshot['duplicates']
                  and not snapshot['unknown'] and not snapshot['write_failures'] and not self.observer_error and not self.generator_error)
        # A saturated producer is an invalid schedule, not a contender capacity limit.
        generator_valid=self.max_lateness_ms<=max(50,self.config['interval_ms']*.1)
        if complete and self.config['preflight']:self.preflight_pass.add(self.mode)
        result=dict(run_id=self.run_id,config=self.config,summary=snapshot,
                    early_overload=getattr(self,'early_overload',False),
                    harness_version=self.version,raw_callbacks=getattr(self,'raw_callbacks',0),rejected_callbacks=getattr(self,'rejected_callbacks',0),
                    input_duration_s=(self.input_end-self.started)/1e9,
                    numerical_pass=complete,generator_valid=generator_valid,
                    max_generator_lateness_ms=self.max_lateness_ms,
                    elapsed_s=(now-self.started)/1e9,missing_ids=self.ledger.missing(),
                    observer_error=self.observer_error,error=self.generator_error,samples=self.samples,
                    native_start=self.native_start,native_end=self.native,
                    tag_script_workers=int(System.getProperty('ignition.tags.scriptthreads','3')),
                    tag_script_queue=int(System.getProperty('ignition.tags.scriptqueuemaxsize','5')))
        self.history.append(result);self.history=self.history[-20:]
        if complete:outcome='PASS'
        elif self.generator_error=='Gateway heap safety limit':outcome='SAFETY STOP / heap'
        elif self.cancel.is_set() and not self.generator_error and not self.observer_error:outcome='STOPPED / submitted jobs drained' if snapshot['outstanding']==0 else 'STOPPED / unfinished jobs'
        else:outcome='CHECK FAILED'
        result['outcome']=outcome
        self.state=outcome+' / '+self.mode
        if not generator_valid:self.state+=' / schedule late'
        path=os.path.join(benchmark_corpus.OUTPUT_DIR,self.run_id+'.json')
        with open(path,'w') as f:json.dump(result,f,indent=2)
        self.unsubscribe()
        system.util.getLogger('LoadBenchmark').info(self.state+' '+str(snapshot)+' saved '+path)

    def warm(self):
        # Sixteen total raw jobs is the upper limit of any automatic preflight.
        self.configure(2,'Jython')
        for c in range(2):
            self.provider.updateValue('Coprocessor/%04d/Burst'%c,self.corpus[c]['payload'],QualityCode.Good,Date(System.currentTimeMillis()))
        self.state='Warm inputs sent / deploy or check Coprocessor outputs'

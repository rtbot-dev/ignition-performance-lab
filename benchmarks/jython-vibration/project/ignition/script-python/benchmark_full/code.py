"""Full original numerical workload, with 22 numeric output updates per burst."""
import math
import threading
LAYOUT = {'rms_trend': ['sample_count', 'rms_value'], 'kurtosis_trend': ['sample_count', 'kurtosis_value', 'm4', 'variance_value'], 'crest_clearance_impulse': ['sample_count', 'peak_to_peak', 'impulse_factor', 'shape_factor', 'clearance_factor', 'crest_factor', 'rms_value'], 'statistical_dashboard': ['sample_count', 'kurtosis_value', 'm4', 'skewness_value', 'm3', 'rms_value', 'std_value', 'variance_value', 'mean_value']}
FIELDS = tuple(folder+'/'+field for folder in sorted(LAYOUT) for field in LAYOUT[folder])

def samples_from_payload(payload):
    values = [float(p.strip()) for p in payload.split(',')]
    if not values or not -2000000000 <= values[-1] <= -1000000000:
        raise ValueError('Missing reserved delimiter')
    samples = values[:-1]
    if len(samples)<2 or any(math.isnan(x) or math.isinf(x) or x<=-100000000 for x in samples):
        raise ValueError('Invalid acceleration burst')
    return samples

def flatten(metrics):
    return {folder+'/'+field:metrics[field] for folder in LAYOUT for field in LAYOUT[folder]}

def _mean(values):
    return sum(values) / float(len(values))


def _safe_div(numerator, denominator):
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def _compute_metrics(samples, device_id, channel_id):
    n = len(samples)
    if n == 0:
        return None

    mean_value = _mean(samples)
    centered = [x - mean_value for x in samples]

    m2 = _mean([x * x for x in centered])
    m3 = _mean([x * x * x for x in centered])
    m4 = _mean([x * x * x * x for x in centered])

    variance_value = m2
    std_value = math.sqrt(max(variance_value, 0.0))
    rms_value = math.sqrt(_mean([x * x for x in samples]))
    kurtosis_value = _safe_div(m4, variance_value * variance_value)
    skewness_value = _safe_div(m3, std_value * std_value * std_value)

    abs_values = [abs(x) for x in samples]
    peak_value = max(abs_values)
    min_value = min(samples)
    max_value = max(samples)
    peak_to_peak = max_value - min_value
    mean_abs = _mean(abs_values)
    mean_sqrt_abs = _mean([math.sqrt(a) for a in abs_values])

    crest_factor = _safe_div(peak_value, rms_value)
    clearance_factor = _safe_div(peak_value, mean_sqrt_abs * mean_sqrt_abs)
    impulse_factor = _safe_div(peak_value, mean_abs)
    shape_factor = _safe_div(rms_value, mean_abs)

    return {
        "sample_count":     n,
        "device_id":        device_id,
        "channel_id":       channel_id,
        "mean_value":       mean_value,
        "variance_value":   variance_value,
        "std_value":        std_value,
        "rms_value":        rms_value,
        "m3":               m3,
        "m4":               m4,
        "skewness_value":   skewness_value,
        "kurtosis_value":   kurtosis_value,
        "peak_to_peak":     peak_to_peak,
        "crest_factor":     crest_factor,
        "clearance_factor": clearance_factor,
        "impulse_factor":   impulse_factor,
        "shape_factor":     shape_factor,
    }



def calculate(payload):
    return flatten(_compute_metrics(samples_from_payload(payload),0,0))

def reference(payload):
    x=samples_from_payload(payload);n=len(x)
    avg=lambda values: math.fsum(values)/n
    mean=avg(x);delta=[v-mean for v in x]
    v=avg(t*t for t in delta);m3=avg(t**3 for t in delta);m4=avg(t**4 for t in delta)
    rms=math.sqrt(avg(t*t for t in x));std=math.sqrt(v)
    peak=max(abs(t) for t in x);ma=avg(abs(t) for t in x);msa=avg(math.sqrt(abs(t)) for t in x)
    div=lambda a,b:a/b if b else 0.
    return flatten(dict(sample_count=n,mean_value=mean,variance_value=v,std_value=std,rms_value=rms,m3=m3,m4=m4,
        kurtosis_value=div(m4,v*v),skewness_value=div(m3,std**3),peak_to_peak=max(x)-min(x),
        crest_factor=div(peak,rms),clearance_factor=div(peak,msa*msa),impulse_factor=div(peak,ma),shape_factor=div(rms,ma)))

class Ledger(object):
    def __init__(self):
        self.lock = threading.RLock()
        self.jobs = {}
        self.published = self.completed = self.verified = self.outstanding = 0
        self.latency_histogram = {}
        self.latencies = []
        self.duplicates = self.unknown = self.wrong = self.write_failures = 0
        self.missed_flags = self.worker_entries = 0
        self.max_sequence = {}
        self.out_of_order = 0

    def register(self, key, reference, start, sequence, channel):
        with self.lock:
            if key in self.jobs:
                raise ValueError('Duplicate scheduled identity')
            self.jobs[key] = dict(reference=reference, start=start, sequence=sequence,
                                  channel=channel, done=False, accepted=None)

    def accepted(self, key, ok):
        with self.lock:
            job = self.jobs[key]
            old = job['accepted']
            if old is True:
                self.published -= 1
                if not job['done']:self.outstanding -= 1
            job['accepted'] = bool(ok)
            if ok:
                self.published += 1
                if not job['done']:self.outstanding += 1
            if not ok:
                self.write_failures += 1

    def enter(self, missed=False):
        with self.lock:
            self.worker_entries += 1
            self.missed_flags += int(bool(missed))

    def complete(self, key, values, end):
        with self.lock:
            job = self.jobs.get(key)
            if job is None:
                self.unknown += 1
                return
            if job['done']:
                self.duplicates += 1
                return
            valid = True
            for field in FIELDS:
                actual, expected = values.get(field), job['reference'][field]
                if actual is None or math.isnan(float(actual)) or math.isinf(float(actual)):
                    valid = False
                elif field.endswith('/sample_count'):
                    valid = valid and actual == expected
                else:
                    valid = valid and abs(actual-expected) <= 1e-8+1e-6*abs(expected)
            channel, sequence = job['channel'], job['sequence']
            if sequence < self.max_sequence.get(channel, -1):
                self.out_of_order += 1
            self.max_sequence[channel] = max(sequence, self.max_sequence.get(channel, -1))
            job.update(done=True, valid=valid, latency_ms=(end-job['start'])/1e6)
            self.completed += 1
            self.verified += int(valid)
            if job['accepted'] is True:self.outstanding -= 1
            latency = job['latency_ms']
            self.latencies.append(latency)
            bucket = int(math.ceil(latency))
            self.latency_histogram[bucket] = self.latency_histogram.get(bucket, 0)+1
            if not valid:
                self.wrong += 1

    def snapshot(self, exact=False):
        with self.lock:
            # Never scan/sort the growing job ledger in the timed path. Exact
            # quantiles are computed only once, after all input and drain stop.
            if exact:
                latencies = sorted(self.latencies)
                def percentile(p):
                    return latencies[max(0,int(math.ceil(p*len(latencies)))-1)] if latencies else 0
            else:
                bins = sorted(self.latency_histogram.items())
                def percentile(p):
                    target = int(math.ceil(p*self.completed))
                    count = 0
                    for upper,n in bins:
                        count += n
                        if count >= target:return upper
                    return 0
            return dict(planned=len(self.jobs), published=self.published,
                        completed=self.completed, verified=self.verified,
                        outstanding=self.outstanding,
                        wrong=self.wrong, duplicates=self.duplicates, unknown=self.unknown,
                        write_failures=self.write_failures, missed_flags=self.missed_flags,
                        worker_entries=self.worker_entries, out_of_order=self.out_of_order,
                        p50_ms=percentile(.5), p99_ms=percentile(.99))

    def missing(self):
        with self.lock:
            return sorted(k for k,j in self.jobs.items() if j['accepted'] is True and not j['done'])

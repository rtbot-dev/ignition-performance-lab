"""Measured rates during input, never including startup or queue drain."""
def summarize(result):
    if result['config'].get('preflight'):
        return None
    rows = [s for s in result.get('samples', [])
            if 10.0 <= s['seconds'] <= result['input_duration_s']]
    if len(rows) < 2 or rows[-1]['seconds'] - rows[0]['seconds'] < 10.0:
        return None
    first, last = rows[0], rows[-1]
    seconds = last['seconds'] - first['seconds']
    offered = (last['published'] - first['published']) / seconds
    completed = (last['verified'] - first['verified']) / seconds
    valid = result.get('generator_valid', False) and not result.get('observer_error') and not any(result['summary'].get(k, 0) for k in ['wrong', 'duplicates', 'unknown', 'write_failures'])
    return dict(run_id=result['run_id'], inputs=result['config']['channels'],
                cadence_ms=result['config']['interval_ms'], seconds=round(seconds, 1),
                offered=offered, completed=completed,
                measured=completed if valid else None,
                invalid=completed if not valid else None,
                missed=result['summary'].get('missed_flags', 0),
                status=result.get('outcome', ''),
                queue_growth=(last['published']-last['worker_entries']-first['published']+first['worker_entries'])/seconds if not result['summary'].get('missed_flags') else None)


def scan_stop_reason(result, point):
    """Conservative stop for a coarse scan, not a certified capacity threshold."""
    if result['summary'].get('missed_flags'):
        return 'missed events detected; inspect this run and the previous level.'
    if not result.get('generator_valid'):
        return 'publisher could not maintain cadence; this is not a processing limit.'
    if not result.get('numerical_pass'):
        return 'run incomplete or failed a correctness/safety check; inspect raw results.'
    if not point:
        return 'not enough sustained measurement time.'
    if point['completed'] < point['offered'] * 0.98 and (point.get('queue_growth') or 0) > 0.5:
        return 'processing fell behind with growing backlog; repeat nearby loads to refine the boundary.'
    return None


def search_step(scan, result, point):
    """Update a measured pass/fail bracket; invalid runs never establish a bound."""
    summary = result['summary']
    if (not result.get('generator_valid') or result.get('observer_error') or
            any(summary.get(k, 0) for k in ['wrong', 'duplicates', 'unknown', 'write_failures'])):
        return None, 'Search stopped: invalid schedule or correctness check. No new bound recorded.'
    missed = bool(summary.get('missed_flags'))
    if result.get('error') and not missed:
        return None, 'Search stopped at a safety/error condition. No new bound recorded.'
    early = bool(result.get('early_overload'))
    if not missed and not early and (not result.get('numerical_pass') or not point):
        return None, 'Search stopped: incomplete measurement. No new bound recorded.'
    overloaded = missed or early or (point['completed'] < point['offered'] * 0.98 and (point.get('queue_growth') or 0) > 0.5)
    count = result['config']['channels']
    if overloaded:scan['high'] = count
    else:scan['low'] = count
    low, high = scan['low'], scan['high']
    if high is not None and high-low < 5:
        if not low:return None, 'No passing load established; overload observed at %s inputs.' % high
        return None, 'Estimated boundary: %s inputs kept pace; %s overloaded (gap %s). For this workload and these resources.' % (low, high, high-low)
    if high is None:
        if low >= 500:return None, '500 inputs kept pace. The limit is above this search range.'
        target = min(500, count*2)
    else:target = max(1, (low+high)//2)
    scan['current'] = target
    scan['index'] += 1
    return target, None


def early_overload(samples):
    """Require growth in each of three ~5-second windows after startup."""
    if not samples or samples[-1]['seconds'] < 20:
        return False
    end = samples[-1]['seconds']
    rows = [s for s in samples if s['seconds'] >= max(5, end-16)]
    if len(rows) < 10 or rows[-1]['seconds']-rows[0]['seconds'] < 14:
        return False
    if any(s.get('missed_flags') for s in rows):return False
    for i in range(3):
        window = [s for s in rows if end-15+i*5 <= s['seconds'] <= end-10+i*5]
        if len(window)<3:return False
        times=[s['seconds'] for s in window]
        queues=[s['published']-s['worker_entries'] for s in window]
        mt=sum(times)/len(times);mq=sum(queues)/float(len(queues))
        denom=sum((t-mt)**2 for t in times)
        slope=sum((t-mt)*(q-mq) for t,q in zip(times,queues))/denom if denom else 0
        if slope<=0.5:return False
    first,last=rows[0],rows[-1]
    offered=last['published']-first['published']
    completed=last['verified']-first['verified']
    return offered>0 and completed<offered*.98


def live_point(samples, config, run_id):
    """Provisional rate over the latest observations; not a capacity result."""
    if config.get('preflight') or len(samples)<3:return None
    end=samples[-1]['seconds']
    rows=[s for s in samples if s['seconds']>=max(0,end-10)]
    if len(rows)<3:return None
    first,last=rows[0],rows[-1];dt=last['seconds']-first['seconds']
    if dt<2:return None
    offered=(last['published']-first['published'])/dt
    completed=(last['verified']-first['verified'])/dt
    return dict(run_id=run_id,inputs=config['channels'],cadence_ms=config['interval_ms'],seconds=round(dt,1),offered=offered,completed=completed,live=completed,measured=None,invalid=None,missed=last.get('missed_flags',0),status='LIVE / provisional')

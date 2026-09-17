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

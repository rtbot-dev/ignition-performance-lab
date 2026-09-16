import unittest, sys, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'project/ignition/script-python/benchmark_full'))
import code as unused
import importlib.util
spec=importlib.util.spec_from_file_location('kernel',Path(__file__).parent/'project/ignition/script-python/benchmark_full/code.py');kernel=importlib.util.module_from_spec(spec);spec.loader.exec_module(kernel)
from analyze import assess

def fake(queue, missed=0):
    rows=[]
    for t in range(1,61):
        p=t*100;q=queue(t);rows.append(dict(seconds=t,published=p,worker_entries=p-q,missed_flags=missed if t>=55 else 0))
    return dict(run_id='test',config=dict(channels=100,records=60,interval_ms=1000,preflight=False),summary=dict(published=6000,verified=6000,missed_flags=missed),samples=rows,input_duration_s=60,numerical_pass=True,generator_valid=True,max_generator_lateness_ms=1,error='',observer_error='')
class Tests(unittest.TestCase):
    def test_kernel_known_values(self):
        p='-1,0,1,-1000000001';v=kernel.calculate(p)
        self.assertEqual(v['statistical_dashboard/mean_value'],0)
        self.assertAlmostEqual(v['rms_trend/rms_value'],math.sqrt(2/3))
        self.assertEqual(v['crest_clearance_impulse/peak_to_peak'],2)
        self.assertEqual(len(v),22)
    def test_zeros_are_data(self):
        v=kernel.calculate('0,0,0,-1000000001')
        self.assertEqual(v['rms_trend/sample_count'],3)
        self.assertEqual(v['kurtosis_trend/kurtosis_value'],0)
    def test_constant(self):
        a=kernel.calculate('2,2,2,-1000000001');b=kernel.reference('2,2,2,-1000000001')
        for k in a:self.assertAlmostEqual(a[k],b[k])
    def test_startup_is_not_overload(self):
        r=assess(fake(lambda t:max(0,100-t*10)))
        self.assertEqual(r['state'],'Held during observation')
    def test_sustained_growth_is_overload(self):
        self.assertIn('sustained backlog',assess(fake(lambda t:3*t))['state'])
    def test_small_growth_needs_longer_run(self):
        self.assertIn('small persistent growth',assess(fake(lambda t:.1*t))['state'])
    def test_late_publisher_invalid(self):
        r=fake(lambda t:0);r['generator_valid']=False
        self.assertIn('Invalid',assess(r)['state'])
    def test_loss_masks_queue_after_first_flag(self):
        r=fake(lambda t:t,1);a=assess(r)
        self.assertIn('missed events',a['state'])
        self.assertAlmostEqual(a['queue_slope'],1)
if __name__=='__main__':unittest.main()

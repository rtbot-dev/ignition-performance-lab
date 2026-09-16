"""Fast checks; does not start Ignition or imply container execution coverage."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
for bench in sorted((ROOT/'benchmarks').iterdir()):
    if not bench.is_dir():continue
    metadata=json.loads((bench/'benchmark.json').read_text())
    assert metadata['id']==bench.name
    for name in ['README.md','NOTICE.md','compose.yaml','Dockerfile','plan.json','test_benchmark.py']:
        assert (bench/name).is_file(),name
    for file in (bench/'project').rglob('*.json'):json.loads(file.read_text())
    if bench.name=='jython-vibration':
        provenance=json.loads((bench/'provenance.json').read_text())
        kernel=bench/'project/ignition/script-python/benchmark_full/code.py'
        assert hashlib.sha256(kernel.read_bytes()).hexdigest()==provenance['kernel_sha256']
        view=json.loads((bench/'project/com.inductiveautomation.perspective/views/Computation/view.json').read_text())
        assert '```python\n'+kernel.read_text()+'\n```' in view['root']['children'][1]['props']['source'], 'Regenerate the source view'
        assert hashlib.sha256((bench/'corpus.json').read_bytes()).hexdigest()==provenance['corpus_sha256']
    subprocess.run([sys.executable,'test_benchmark.py'],cwd=bench,check=True)
print('Benchmark metadata, project JSON, provenance and numerical tests passed.')

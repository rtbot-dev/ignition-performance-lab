"""Export only tracked source files, with a checksum manifest."""
from pathlib import Path
import hashlib,json,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
files=[name for name in files if name]
assert files,'Stage source files before packaging'
for name in files:
    parts=Path(name).parts
    assert not any(x in ['.env','results','runtime','dist','__pycache__'] for x in parts),name
out=ROOT/'dist';out.mkdir(exist_ok=True)
manifest={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}
with zipfile.ZipFile(out/'ignition-performance-lab.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name in files:archive.write(ROOT/name,'ignition-performance-lab/'+name)
    archive.writestr('ignition-performance-lab/SHA256SUMS.json',json.dumps(manifest,indent=2))
print(out/'ignition-performance-lab.zip')

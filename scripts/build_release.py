"""Build a source ZIP and small launchers pinned to that ZIP's SHA-256."""
from pathlib import Path
import hashlib,subprocess,sys,re
root=Path(__file__).resolve().parents[1]
version=sys.argv[1] if len(sys.argv)>1 else 'v0.1.4'
assert re.fullmatch(r'v\d+\.\d+\.\d+',version)
subprocess.run([sys.executable,str(root/'scripts/package.py')],check=True)
out=root/'dist';digest=hashlib.sha256((out/'ignition-performance-lab.zip').read_bytes()).hexdigest()
for template,names in [('bootstrap.sh.in',['Run-experiment-mac.command','Run-experiment-linux.sh']),('bootstrap.ps1.in',['Run-experiment-windows.ps1'])]:
    text=(root/'scripts/launchers'/template).read_text().replace('@VERSION@',version).replace('@SHA256@',digest)
    for name in names:
        (out/name).write_text(text);(out/name).chmod(0o755)
# The CMD file is a double-clickable Windows entry point, with the same pinned
# bootstrap embedded. Bypass is process-local; no persistent policy is changed.
ps=(out/'Run-experiment-windows.ps1').read_text()
encoded=__import__('base64').b64encode(ps.encode('utf-16-le')).decode()
(out/'Run-experiment-windows.cmd').write_text('@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand '+encoded+'\r\npause\r\n')
files=['ignition-performance-lab.zip','Run-experiment-mac.command','Run-experiment-linux.sh','Run-experiment-windows.ps1','Run-experiment-windows.cmd']
(out/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256((out/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in files))
print('Built '+version+' release launchers; archive SHA256 '+digest)

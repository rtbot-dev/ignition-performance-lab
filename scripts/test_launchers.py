"""Verify shell installer behavior without network, licensing or Docker workloads."""
import hashlib,os,subprocess,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Launchers(unittest.TestCase):
 def test_verified_install_cache_and_corruption(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);bin_=root/'bin';bin_.mkdir();archive=root/'source.zip'
   with zipfile.ZipFile(archive,'w') as z:z.writestr('ignition-performance-lab/scripts/start.sh','#!/bin/sh\necho started >> "$TEST_LOG"\n')
   digest=hashlib.sha256(archive.read_bytes()).hexdigest()
   for name,body in [('docker','exit 0'),('curl','echo download >> "$TEST_DOWNLOADS"\nwhile [ "$1" != "-o" ]; do shift; done\ncp "$TEST_ARCHIVE" "$2"')]:
    f=bin_/name;f.write_text('#!/bin/sh\n'+body+'\n');f.chmod(0o755)
   env=dict(os.environ,PATH=str(bin_)+':'+os.environ['PATH'],XDG_DATA_HOME=str(root/'data'),TEST_ARCHIVE=str(archive),TEST_LOG=str(root/'log'),TEST_DOWNLOADS=str(root/'downloads'))
   template=(ROOT/'scripts/launchers/bootstrap.sh.in').read_text()
   launcher=root/'launch.sh';launcher.write_text(template.replace('@VERSION@','v0.1.1').replace('@SHA256@',digest))
   for _ in range(2):subprocess.run(['sh',str(launcher)],env=env,check=True,capture_output=True)
   self.assertEqual((root/'log').read_text().splitlines(),['started','started'])
   self.assertEqual((root/'downloads').read_text().splitlines(),['download'])
   launcher.write_text(template.replace('@VERSION@','v0.1.2').replace('@SHA256@','0'*64))
   result=subprocess.run(['sh',str(launcher)],env=env,capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0);self.assertIn('checksum failed',result.stdout)
   self.assertFalse((root/'data/katenaria/ignition-performance-lab/v0.1.2').exists())
if __name__=='__main__':unittest.main()

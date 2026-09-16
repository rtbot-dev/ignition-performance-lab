import os,subprocess,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parent/'port.sh'
class Ports(unittest.TestCase):
 def run_case(self,answers,own=False):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'bin').mkdir()
   docker=p/'bin/docker';docker.write_text('''#!/bin/sh
case "$1" in
 ps) case "$*" in *publish=9088*) if [ ! -f "$STATE" ]; then echo "old-gateway ${OWNER:-other-project}"; fi;; esac;;
 stop) echo "$2" >> "$STOPS"; touch "$STATE";;
esac
''');docker.chmod(0o755)
   lsof=p/'bin/lsof';lsof.write_text('#!/bin/sh\nexit 1\n');lsof.chmod(0o755)
   env=dict(os.environ,PATH=str(p/'bin')+':'+os.environ['PATH'],STATE=str(p/'stopped'),STOPS=str(p/'stops'),OWNER='katenaria-lab-jython-vibration' if own else 'other-project');env.pop('LAB_PORT',None)
   r=subprocess.run(['sh','-c','. "$1"; printf "URL=%s" "$lab_url"','sh',str(SCRIPT)],cwd=p,env=env,input=answers,text=True,capture_output=True)
   return r,(p/'stops').read_text() if (p/'stops').exists() else '',(p/'runtime/port').read_text() if (p/'runtime/port').exists() else ''
 def test_alternate(self):
  r,stops,port=self.run_case('2\n9090\n');self.assertEqual(r.returncode,0);self.assertEqual(stops,'');self.assertEqual(port.strip(),'9090');self.assertIn('localhost:9090',r.stdout)
 def test_explicit_stop(self):
  r,stops,port=self.run_case('1\n');self.assertEqual(r.returncode,0);self.assertEqual(stops,'old-gateway\n');self.assertEqual(port.strip(),'9088')
 def test_cancel(self):
  r,stops,port=self.run_case('\n');self.assertNotEqual(r.returncode,0);self.assertEqual(stops,'');self.assertEqual(port,'')
 def test_own_project_reused(self):
  r,stops,port=self.run_case('',True);self.assertEqual(r.returncode,0);self.assertEqual(stops,'')
 def test_invalid_port_then_valid(self):
  r,stops,port=self.run_case('2\nnot-a-port\n9091\n');self.assertEqual(r.returncode,0);self.assertEqual(port.strip(),'9091')
if __name__=='__main__':unittest.main()

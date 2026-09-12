"""Check package integrity and reject unsupported inputs in the real Player."""
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def run(output=None):
 p=output or ROOT/'results/avatar-package-tests'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-%fZ')
 p=p.resolve();p.mkdir(parents=True,exist_ok=False)
 package=ROOT/'builds/lab/avatars/haolan.tcap';exe=ROOT/'builds/lab/TanakaCap.exe'
 with zipfile.ZipFile(package) as z:
  valid=json.loads(z.read('manifest.json'));assert hashlib.sha256(z.read('avatar.bundle')).hexdigest()==valid['bundleSha256']
 results={}
 for name,change in [('version',{'formatVersion':99}),('checksum',{'bundleSha256':'0'*64}),('unity',{'unityVersion':'incompatible'}),('bundle',{'bundleSha256':hashlib.sha256(b'invalid').hexdigest()})]:
  file=p/(name+'.tcap');m=dict(valid,**change)
  with zipfile.ZipFile(file,'w') as z:z.writestr('manifest.json',json.dumps(m));z.writestr('avatar.bundle',b'invalid')
  log=p/(name+'.log');r=subprocess.run([str(exe),'-batchmode','--avatar',str(file),'-logFile',str(log)],timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
  text=log.read_text(encoding='utf-8',errors='replace');assert r.returncode==2 and 'TANAKACAP_PACKAGE_ERROR' in text and 'TANAKACAP_PACKAGE_LOADED' not in text
  results[name]={'rejected':True,'exit_code':r.returncode}
 (p/'report.json').write_text(json.dumps(results,indent=2));print(results)
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args();run(args.output)

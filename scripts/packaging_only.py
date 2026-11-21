"""Verify a trusted previously validated release ZIP before repackaging the installer."""
import argparse,configparser,hashlib,json,pathlib,re,shutil,zipfile,io
from stage import pe_kind, validate_zip, ROOT

def main():
 p=argparse.ArgumentParser();p.add_argument('--zip',required=True);p.add_argument('--sha256',required=True);p.add_argument('--out',required=True);p.add_argument('--env',required=True);a=p.parse_args()
 z=pathlib.Path(a.zip);expected=a.sha256.strip().lower()
 if not re.fullmatch('[a-f0-9]{64}',expected):raise RuntimeError('Exact SHA256 is mandatory for trusted rebuild')
 actual=hashlib.sha256(z.read_bytes()).hexdigest()
 if actual!=expected:raise RuntimeError(f'Original ZIP checksum mismatch; expected {expected}, got {actual}')
 validate_zip(z);out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(z) as archive:
  names=archive.namelist()
  if any(info.external_attr>>16 & 0o120000 == 0o120000 for info in archive.infolist()):raise RuntimeError('Archive symlinks unsupported')
  if any(not n.startswith(ROOT+'/') or '..' in pathlib.PurePosixPath(n).parts for n in names):raise RuntimeError('Unsafe archive paths')
  identity=json.loads(archive.read(ROOT+'/Other/Source/BUILD-IDENTITY.json'))
  config=configparser.ConfigParser();config.read_string(archive.read(ROOT+'/App/AppInfo/appinfo.ini').decode('utf-8'))
  version=config['Version']['PackageVersion']
  if not re.fullmatch(r'\d+\.\d+\.\d+\.\d+',version):raise RuntimeError('Invalid original version')
  sha=identity.get('upstream_commit','')
  if not re.fullmatch('[a-f0-9]{40}',sha):raise RuntimeError('Unverified original source identity')
  # Extract only after zip path validation, preserving the original ZIP unchanged.
  archive.extractall(out)
 (out/'ZIP-SHA256.txt').write_text(f'{actual}  {z.name}\n',encoding='utf-8')
 with pathlib.Path(a.env).open('a',encoding='utf-8') as f:f.write(f'APP_VERSION={version}\nUPSTREAM_SHA={sha}\n')
 print('Original verified; upstream commit',sha,'version',version)
if __name__=='__main__':main()

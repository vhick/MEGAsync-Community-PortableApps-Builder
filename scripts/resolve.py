"""Resolve upstream Windows stable releases with numeric ordering, no master fallback."""
import argparse, json, os, pathlib, re, urllib.request, urllib.error
TAG = re.compile(r'^v(\d+)\.(\d+)\.(\d+)\.(\d+)_Win$')
API='https://api.github.com/repos/meganz/MEGAsync/releases?per_page=100'
def numeric(tag):
    m=TAG.fullmatch(tag);return tuple(map(int,m.groups())) if m else None
def choose(releases, requested=''):
    safe = [r for r in releases if not r.get('draft') and not r.get('prerelease') and numeric(r.get('tag_name',''))]
    if requested:
        hits=[r for r in safe if r['tag_name']==requested]
        if not hits: raise ValueError('Requested tag does not match a published stable Windows release')
        return hits[0]
    if not safe: raise ValueError('No suitable stable Windows release found')
    return max(safe,key=lambda r:numeric(r['tag_name']))
def fetch():
    headers={'Accept':'application/vnd.github+json','User-Agent':'MEGA-Community-Portable-Builder','X-GitHub-Api-Version':'2022-11-28'}
    if os.getenv('GITHUB_TOKEN'):headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
    req=urllib.request.Request(API,headers=headers)
    with urllib.request.urlopen(req,timeout=45) as r:
        body=json.load(r)
        if not isinstance(body,list):raise RuntimeError('Unexpected GitHub response')
        return body
def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',default='');p.add_argument('--env',required=True);args=p.parse_args()
    r=choose(fetch(),args.tag);tag=r['tag_name']; version='.'.join(str(x) for x in numeric(tag))
    path=pathlib.Path(args.env);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as f:f.write(f'UPSTREAM_TAG={tag}\nAPP_VERSION={version}\n')
    print(f'Chosen stable upstream Windows release: {tag}; version {version}; URL {r["html_url"]}')
if __name__=='__main__':main()

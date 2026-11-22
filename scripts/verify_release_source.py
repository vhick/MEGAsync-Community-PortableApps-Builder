"""Verify an official GitHub release asset from THIS builder before launcher-only reuse.

No arbitrary URLs, `latest` shortcuts, non-matching upstream commits, or
unverified external ZIPs. Only a builder release that points to the requested
source-build run (or whose exact tag the caller explicitly selected) qualifies.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

TAG = re.compile(r'^mega-portable-v(?P<version>\d+\.\d+\.\d+\.\d+)-(?P<rev>b1r\d+)-(?P<commit>[0-9a-f]{40})$')
ZIP = re.compile(r'^MEGAsyncPortable_(?P<version>\d+\.\d+\.\d+\.\d+)_(?P<rev>b1r\d+)_x64\.zip$')
HASH = re.compile(r'^[a-f0-9]{64}$')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for buf in iter(lambda: f.read(1024 * 1024), b''):
            h.update(buf)
    return h.hexdigest()


def release_matches_run(body: str, repository: str, run_id: str) -> bool:
    if not run_id:
        return True
    return bool(re.search(r'https://github\.com/' + re.escape(repository) +
                          r'/actions/runs/' + re.escape(run_id) + r'(?!\d)', body, re.I))


def eligible_release(release: dict, repository: str, expected_sha: str,
                     source_run_id: str = '', explicit_tag: str = '') -> dict | None:
    if not isinstance(release, dict) or release.get('draft') or release.get('prerelease'):
        return None
    tag = release.get('tag_name', '')
    if explicit_tag and tag != explicit_tag:
        return None
    m = TAG.fullmatch(tag)
    if m is None:
        return None
    if release.get('html_url') != f'https://github.com/{repository}/releases/tag/{tag}':
        return None
    if not release_matches_run(release.get('body') or '', repository, source_run_id):
        return None
    assets = release.get('assets')
    if not isinstance(assets, list):
        return None
    zips = [a for a in assets if isinstance(a, dict) and
            ZIP.fullmatch(a.get('name','')) and a.get('state') == 'uploaded']
    zips = [a for a in zips if ZIP.fullmatch(a['name']).group('version') == m.group('version') and
            ZIP.fullmatch(a['name']).group('rev') == m.group('rev')]
    sums = [a for a in assets if isinstance(a, dict) and
            a.get('name') == 'SHA256SUMS.txt' and a.get('state') == 'uploaded']
    if len(zips) != 1 or len(sums) != 1:
        return None
    digest = zips[0].get('digest')
    if digest and digest.lower() != 'sha256:' + expected_sha:
        return None
    if zips[0].get('size', 0) < 100000:
        return None
    return {
        'tag': tag,
        'zip_filename': zips[0]['name'],
        'sha256': expected_sha,
        'commit': m.group('commit'),
        'version': m.group('version'),
        'source_run_id': source_run_id,
        'repository': repository,
        'release_id': release.get('id'),
        'release_asset_id': zips[0].get('id'),
        'source_kind': 'verified-published-release',
    }


def choose_release(data: list | dict, repository: str, expected_sha: str,
                   source_run_id: str = '', explicit_tag: str = '') -> dict:
    if not HASH.fullmatch(expected_sha):
        raise ValueError('Expected SHA-256 must contain exactly 64 lowercase hexadecimal characters')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Invalid repository name')
    if source_run_id and not re.fullmatch(r'[1-9]\d{0,18}', source_run_id):
        raise ValueError('Invalid source run ID')
    if not source_run_id and not explicit_tag:
        raise ValueError('An exact source release tag or source run ID is required')
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError('Invalid GitHub release API response')
    choices = [c for r in data if (c := eligible_release(r, repository, expected_sha,source_run_id,explicit_tag))]
    if len(choices) != 1:
        raise ValueError(f'Expected exactly one matching trusted published release; found {len(choices)}. '
                         'Enter an exact release tag or use a different verified source ZIP.')
    return choices[0]


def verify_downloaded(plan: dict, directory: Path) -> None:
    file_name = plan['zip_filename']
    if not ZIP.fullmatch(file_name):
        raise ValueError('Invalid ZIP filename in selected release')
    zip_path = directory / file_name
    sums_path = directory / 'SHA256SUMS.txt'
    if not zip_path.is_file() or not sums_path.is_file():
        raise ValueError('The exact release ZIP and SHA256SUMS.txt must both be downloaded')
    real = sha256(zip_path)
    if real != plan['sha256']:
        raise ValueError('Downloaded release ZIP does not match the user-supplied SHA256')
    entries = []
    for line in sums_path.read_text(encoding='utf-8-sig').splitlines():
        match = re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?(.+?)\s*', line.strip())
        if match and match.group(2).replace('\\','/') == file_name:
            entries.append(match.group(1).lower())
    if entries != [real]:
        raise ValueError('Release SHA256SUMS.txt is missing, duplicated, or mismatched for the exact source ZIP')
    with zipfile.ZipFile(zip_path) as archive:
        identity = json.loads(archive.read('MEGAsyncPortable/Other/Source/BUILD-IDENTITY.json'))
        if identity.get('upstream_commit') != plan['commit']:
            raise ValueError('Release tag upstream commit does not match packaged BUILD-IDENTITY.json')
        if identity.get('kit_revision') != ZIP.fullmatch(file_name).group('rev'):
            raise ValueError('Release ZIP builder revision and embedded identity differ')
        ini = archive.read('MEGAsyncPortable/App/AppInfo/appinfo.ini').decode('utf-8')
        if not re.search(r'(?m)^PackageVersion=' + re.escape(plan['version']) + r'\s*$', ini):
            raise ValueError('Release ZIP application version does not match release tag')
    print('Verified release ZIP, checksum manifest, upstream SHA and package identity:',file_name)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['select','verify'])
    p.add_argument('--metadata-json', type=Path)
    p.add_argument('--repository')
    p.add_argument('--sha256')
    p.add_argument('--source-run-id', default='')
    p.add_argument('--tag', default='')
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--directory', type=Path)
    args = p.parse_args()
    if args.phase == 'select':
        data = json.loads(args.metadata_json.read_text(encoding='utf-8-sig'))
        selected = choose_release(data, args.repository, args.sha256.lower(),
                                  args.source_run_id, args.tag)
        args.plan.write_text(json.dumps(selected, indent=2) + '\n',encoding='utf-8')
        print('Trusted release selected:', selected['tag'], selected['zip_filename'])
    else:
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        verify_downloaded(plan, args.directory)

if __name__ == '__main__':
    main()

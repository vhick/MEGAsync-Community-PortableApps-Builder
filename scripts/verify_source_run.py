"""Fail-closed verification of a GitHub Actions source run and canonical workflow identity.

Called before downloading a prior failed-installer artifact. It validates official
GitHub REST responses, not untrusted user-entered workflow names or tags.
"""
import argparse
import json
import re
from pathlib import Path

EXPECTED_WORKFLOW_PATH = ".github/workflows/build-portableapps.yml"


def source_path(path):
    """Normalize the documented run.path format, with optional @branch/@ref.

    GitHub workflow run API uses '.github/workflows/foo.yml@main', not the
    leading-slash '/.github/...' form assumed by the b1r10 workflow.
    """
    if not isinstance(path, str) or not path:
        raise ValueError("Source run has no workflow path")
    # Never match suffixes: a different workflow or repository must not pass.
    if not re.fullmatch(r"/?\.github/workflows/build-portableapps\.yml(?:@[^\r\n]+)?", path):
        raise ValueError(f"Unexpected source workflow run path: {path!r}")
    return path.split('@', 1)[0].lstrip('/')


def check_source_run(run, workflow, repository, run_id):
    """Validate exact same-repository workflow identity, ID, dispatch and completion."""
    if not re.fullmatch(r"[1-9][0-9]{0,18}", str(run_id)):
        raise ValueError("Invalid numeric source run ID")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid calling repository identity")
    if not isinstance(run, dict) or not isinstance(workflow, dict):
        raise ValueError("Unexpected GitHub API response shape")
    if run.get('id') != int(run_id):
        raise ValueError(f"Source run ID mismatch: requested {run_id}, API returned {run.get('id')!r}")
    repo = run.get('repository')
    actual_repository = repo.get('full_name') if isinstance(repo, dict) else None
    if not isinstance(actual_repository, str) or actual_repository.casefold() != repository.casefold():
        raise ValueError(f"Source run repository mismatch: {actual_repository!r} != {repository!r}")
    if run.get('event') != 'workflow_dispatch':
        raise ValueError(f"Source run was not manually dispatched: {run.get('event')!r}")
    if run.get('status') != 'completed':
        raise ValueError(f"Source run has not completed: {run.get('status')!r}")
    source_path(run.get('path'))
    if workflow.get('path') != EXPECTED_WORKFLOW_PATH:
        raise ValueError(f"Canonical workflow file mismatch: {workflow.get('path')!r}")
    workflow_id = workflow.get('id')
    if not isinstance(workflow_id, int) or workflow_id <= 0 or run.get('workflow_id') != workflow_id:
        raise ValueError(f"Source workflow ID mismatch: run {run.get('workflow_id')!r}; canonical {workflow_id!r}")
    return (f"Trusted completed source-build run {run_id}: repository={actual_repository}, "
            f"workflow_id={workflow_id}, path={run['path']}, event={run['event']}")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-json', type=Path, required=True)
    ap.add_argument('--workflow-json', type=Path, required=True)
    ap.add_argument('--repository', required=True)
    ap.add_argument('--run-id', required=True)
    args=ap.parse_args()
    run=json.loads(args.run_json.read_text(encoding='utf-8-sig'))
    workflow=json.loads(args.workflow_json.read_text(encoding='utf-8-sig'))
    print(check_source_run(run, workflow, args.repository, args.run_id))

if __name__=='__main__':
    main()

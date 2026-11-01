#!/usr/bin/env python3
"""Start one owned external wait; no inference while idle, no recurring daemon."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from oaplib import load_runtime, resolved_root, validate_pane, require, safe_path, lock

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind',choices=['control','response']); p.add_argument('--repo-root',required=True)
    p.add_argument('--runtime',required=True); p.add_argument('--identifier'); p.add_argument('--dry-run',action='store_true')
    a=p.parse_args(); repo=resolved_root(a.repo_root); config=load_runtime(a.runtime,repo,not a.dry_run)
    role='coding' if a.kind=='control' else 'strategic'; validate_pane(config,role)
    operation='wait-control' if a.kind=='control' else 'signal-wait'
    argv=[sys.executable,str(repo/'oap/bin/oap.py'),operation,'--repo-root',str(repo),'--runtime',str(Path(a.runtime).absolute()),'--role',role.upper()]
    if a.kind=='response': require(a.identifier is not None,'Response waiter needs identifier'); argv+=['--identifier',a.identifier]
    if a.dry_run:
        print(json.dumps({'mode':'DRY_RUN','argv':argv,'starts_process':False})); return
    home=Path(config['strategic_home']); state=safe_path(home,'.oap-state')
    with lock(state/(a.kind+'-launcher.lock')):
        # This is a preflight only; the child owns the actual long-lived reader lock.
        with lock(state/(a.kind+'-reader.lock')): pass
        logfile=state/(a.kind+'-waiter.log')
        fd=os.open(logfile,os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW,0o600)
        try:
            process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=fd,stderr=fd,
                                     cwd=str(repo if role=='coding' else home),start_new_session=True,close_fds=True)
        finally: os.close(fd)
    print(json.dumps({'started_pid':process.pid,'kind':a.kind,'log':str(logfile),
                      'note':'Wrapper will refuse duplicate reader; startup does not certify signal delivery.'}))

if __name__=='__main__': main()

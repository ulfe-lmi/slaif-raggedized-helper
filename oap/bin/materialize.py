#!/usr/bin/env python3
"""Non-destructive local installation of a reviewed, inactive OAP package."""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
from oaplib import ProtocolError, atomic_write, digest, read_bytes, require, resolved_root, safe_path, now

MUTABLE = {'CRITICAL.md','STATUS.md'}

def plan_install(package, repo, strategic, refresh=()):
    roots=[package,repo,strategic]
    require(all(a!=b and a not in b.parents and b not in a.parents for i,a in enumerate(roots) for b in roots[i+1:]),'Package, repository and strategic roots must be distinct and non-nested')
    manifest=json.loads(read_bytes(package/'PACKAGE-MANIFEST.json'))
    require(not (repo/'oap/active').exists(),'Existing active installation requires a separately scoped quiescent refresh')
    prior_path=strategic/'.oap-installation.json'
    prior=json.loads(read_bytes(prior_path)) if prior_path.exists() else {'files':{}}
    actions=[]
    for key,expected in manifest['files'].items():
        role,rel=key.split('/',1); destination=repo if role=='repo' else strategic
        source=safe_path(package,key); data=read_bytes(source)
        require(digest(data)==expected,'Package source identity mismatch: '+key)
        target=safe_path(destination,rel)
        if target.exists():
            require(target.is_file(),'File type conflict: '+key)
            actual=digest(read_bytes(target))
            if actual==expected: status='UNCHANGED'
            elif (role=='repo' and rel in MUTABLE) or (role=='strategic' and rel in ('runtime.json','workorders/EXECUTION_TIMINGS.md')):
                status='PRESERVED'
            elif key in refresh:
                require(prior['files'].get(key)==actual,'Scoped refresh requires unchanged previously installed bytes: '+key)
                status='BACKUP_AND_REFRESH'
            elif not prior['files'] and manifest.get('initial_replace',{}).get(key)==actual:
                status='BACKUP_AND_INSTALL'
            else:
                raise ProtocolError('Conflicting existing file; preserve and reconcile: '+key)
        else: status='CREATE'
        actions.append({'key':key,'status':status,'source':str(source),'destination':str(target),'sha256':expected})
    for name,target_rel in manifest['strategic_links'].items():
        destination=strategic/name; expected=str(repo/target_rel)
        # Links are explicit controlled navigation, never traversed for writes.
        if destination.is_symlink():
            require(os.readlink(destination)==expected,'Conflicting strategic navigation link')
            status='UNCHANGED_LINK'
        elif destination.exists(): raise ProtocolError('Refusing to replace existing navigation path: '+name)
        else: status='CREATE_LINK'
        actions.append({'key':'strategic/'+name,'status':status,'destination':str(destination),'target':expected})
    for name in ('control.fifo','response.fifo'):
        target=strategic/name
        if target.exists() or target.is_symlink():
            value=target.lstat(); require(stat.S_ISFIFO(value.st_mode) and value.st_uid==os.getuid() and stat.S_IMODE(value.st_mode)==0o600,'Existing FIFO conflict')
            status='UNCHANGED_FIFO'
        else: status='CREATE_FIFO'
        actions.append({'key':'strategic/'+name,'status':status,'destination':str(target)})
    return manifest,prior,actions

def install(package,repo,strategic,dry_run=True,refresh=()):
    manifest,prior,actions=plan_install(package,repo,strategic,refresh)
    if dry_run: return {'mode':'DRY_RUN','writes':False,'actions':actions}
    # No Git operations, process startup, signal, product service or active pointer.
    for action in actions:
        target=Path(action['destination']); status=action['status']
        if status in ('CREATE','BACKUP_AND_REFRESH','BACKUP_AND_INSTALL'):
            if status.startswith('BACKUP'):
                backup=strategic/'bootstrap-backups'/digest(read_bytes(target))/action['key']
                atomic_write(backup,read_bytes(target),immutable=True,mode=0o600)
            mode=0o600 if action['key']=='strategic/runtime.json' else (0o755 if action['key'].endswith('.sh') or '/bin/' in action['key'] else 0o644)
            atomic_write(target,read_bytes(Path(action['source'])),mode=mode)
        elif status=='CREATE_LINK':
            target.parent.mkdir(parents=True,exist_ok=True); target.symlink_to(action['target'])
        elif status=='CREATE_FIFO': os.mkfifo(target,0o600)
    for rel in ('drafts','critical-drafts','audit','logs','agent-homes/coding','agent-homes/strategic','.oap-state'):
        target=safe_path(strategic,rel)
        if not target.exists(): target.mkdir(parents=True,mode=0o700)
        require(target.is_dir() and not target.is_symlink(),'Private directory type conflict')
    record={'package_sha256':digest(read_bytes(package/'PACKAGE-MANIFEST.json')),
            'files':{a['key']:digest(read_bytes(Path(a['destination']))) for a in actions if a['status'] in ('CREATE','UNCHANGED','BACKUP_AND_REFRESH','BACKUP_AND_INSTALL','PRESERVED')}}
    previous=strategic/'.oap-installation.json'
    serialized=(json.dumps(record,indent=2,sort_keys=True)+'\n').encode()
    if not previous.exists() or read_bytes(previous)!=serialized: atomic_write(previous,serialized,mode=0o600)
    return {'mode':'APPLIED','actions':actions,'active_created':False,'signals_sent':False,'agents_started':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package-root',required=True); p.add_argument('--repo-root',required=True); p.add_argument('--strategic-home',required=True)
    p.add_argument('--apply',action='store_true'); p.add_argument('--refresh',action='append',default=[])
    a=p.parse_args()
    try:
        result=install(resolved_root(a.package_root),resolved_root(a.repo_root),resolved_root(a.strategic_home),not a.apply,a.refresh)
        print(json.dumps(result,indent=2)); return 0
    except (ProtocolError,OSError,ValueError,KeyError) as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc)})); return 2

if __name__=='__main__': raise SystemExit(main())

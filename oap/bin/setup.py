#!/usr/bin/env python3
"""Access setup shells without credentials, activation, model changes or agent launch."""
import argparse
import json
import shlex
from pathlib import Path
from oaplib import resolved_root, load_runtime, command, require

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root',required=True); p.add_argument('--runtime',required=True)
    p.add_argument('--new-session'); p.add_argument('--dry-run',action='store_true')
    a=p.parse_args(); repo=resolved_root(a.repo_root); config=load_runtime(a.runtime,repo)
    actions=[]
    if a.new_session:
        require(a.new_session.replace('-','').replace('_','').isalnum(),'Unsafe tmux session name')
        actions=[['tmux','new-session','-d','-s',a.new_session,'-c',config['strategic_home']],
                 ['tmux','split-window','-h','-t',a.new_session+':0','-c',config['repo_root']]]
    print(json.dumps({'mode':'SETUP_ONLY','activation_enabled':config['activation_enabled'],
                      'existing_panes':{'strategic':config['strategic_pane'],'coding':config['coding_pane']},
                      'actions':actions,'starts_agents':False,'needs_credentials':False},indent=2))
    if not a.dry_run:
        for action in actions: command(action)

if __name__=='__main__': main()

"""Small POSIX OAP harness. Instructions are governance, not OS authentication."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import select
import stat
import subprocess
import sys
import tempfile
import time

ID_RE = re.compile(r'[0-9]{3}-[a-z]{1,2}')
CRIT_RE = re.compile(r'^## (CRIT-[0-9]{4}) — .+$', re.M)
SECTIONS = ('Objective', 'Dependencies and current state', 'Allowed paths and scope',
            'Non-goals', 'Acceptance criteria', 'Verification and negative evidence',
            'Documentation', 'Runtime and protected resources', 'Deferred human adjudication',
            'Publication and report')
CRIT_SECTIONS = ('Dilemma', 'Decision taken', 'Reasoning', 'Alternatives considered',
                 'Strongest argument that this decision is wrong', 'Assumptions',
                 'Failure mode and blast radius', 'Mitigations and evidence',
                 'Reversibility and rollback', 'Safe autonomous continuation',
                 'Exact human gate', 'Exact question for the human adjudicator',
                 'Strategic attestation', 'Human disposition', 'Resolution')

class ProtocolError(RuntimeError):
    pass

def require(condition, message):
    if not condition:
        raise ProtocolError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def command(argv, cwd=None, input=None):
    result = subprocess.run(argv, cwd=cwd, input=input, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    require(result.returncode == 0, f'Command failed ({result.returncode}): {argv[0]} {argv[1] if len(argv)>1 else ""}; inspect locally (output withheld to avoid secret leakage)')
    return result.stdout

def git(repo, *args):
    return command(['git', '-C', str(repo), *args]).decode().strip()

def gh(*args):
    return json.loads(command(['gh', *args]))

def resolved_root(value):
    path = Path(value).absolute()
    require(path.exists() and path.is_dir() and not path.is_symlink(), 'Root must be a real existing directory')
    require(path.resolve() == path, 'Root path must be canonical, without symlink components')
    require(path.stat().st_uid == os.getuid(), 'Root is not owned by current user')
    return path

def safe_path(root, relative):
    part = Path(relative)
    require(not part.is_absolute() and '..' not in part.parts and str(part) not in ('', '.'), 'Unsafe relative path')
    target = root / part
    for candidate in [target, *list(target.parents)[:len(part.parts)-1]]:
        require(not candidate.is_symlink(), f'Symlink refused: {candidate.name}')
    return target

def read_bytes(path):
    require(path.is_file() and not path.is_symlink(), f'Regular file required: {path.name}')
    return path.read_bytes()

def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def atomic_write(path, data, *, immutable=False, mode=0o644):
    require(not path.is_symlink(), 'Refusing symlink write')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.oap-write-', dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'wb') as out:
            out.write(data); out.flush(); os.fsync(out.fileno())
        if immutable:
            try: os.link(temporary, path)
            except FileExistsError:
                require(read_bytes(path) == data, 'Immutable file already exists with different bytes')
        else:
            os.replace(temporary, path)
        fsync_dir(path.parent)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

@contextlib.contextmanager
def lock(path):
    require(not path.is_symlink(), 'Symlink lock refused')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise ProtocolError('Another owner/consumer holds this lock')
        yield
    finally: os.close(fd)

def unfenced(text):
    lines=[]; fence=None
    for line in text.splitlines():
        marker=re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            token=marker.group(1)
            if fence is None: fence=token
            elif token[0] == fence[0] and len(token)>=len(fence): fence=None
            continue
        if fence is None: lines.append(line)
    require(fence is None, 'Unclosed Markdown fence')
    return '\n'.join(lines)

def metadata(text):
    header = unfenced(text).split('\n## ', 1)[0]
    values={}
    for line in header.splitlines():
        match=re.fullmatch(r'([A-Za-z][A-Za-z0-9 -]+): (.+)', line)
        if match:
            key,value=match.groups()
            require(key not in values, f'Duplicate metadata: {key}')
            values[key]=value.strip()
    return values

def section(text, heading, level=2):
    plain=unfenced(text)
    pattern=r'^'+('#'*level)+' '+re.escape(heading)+r'\n(.*?)(?=^#{1,'+str(level)+r'} |\Z)'
    matches=re.findall(pattern, plain, re.M|re.S)
    require(len(matches)==1 and matches[0].strip(), f'Missing/duplicate/empty section: {heading}')
    return matches[0].strip()

def identifier(value):
    require(ID_RE.fullmatch(value) is not None, 'Invalid objective identifier')
    return value

def successor_suffix(value):
    require(re.fullmatch(r'[a-z]{1,2}',value) is not None, 'Invalid suffix')
    if len(value)==1:
        return chr(ord(value)+1) if value!='z' else 'aa'
    require(value!='zz', 'Suffix range exhausted; explicit protocol revision required')
    return value[0]+chr(ord(value[1])+1) if value[1]!='z' else chr(ord(value[0])+1)+'a'

def active(repo):
    path=safe_path(repo,'oap/active')
    if not path.exists(): return None
    data=read_bytes(path)
    require(re.fullmatch(rb'[0-9]{3}-[a-z]{1,2}\n',data) is not None, 'Active must be one valid ID followed by one LF')
    return data[:-1].decode('ascii')

def unique(repo, directory, ident, required=True):
    identifier(ident)
    base=safe_path(repo,f'oap/{directory}')
    paths=list(base.glob(ident+'-*.md')) if base.exists() else []
    require(len(paths)<=1, f'Ambiguous {directory} for {ident}')
    require(not required or len(paths)==1, f'Missing {directory} for {ident}')
    if paths: read_bytes(paths[0])
    return paths[0] if paths else None

def commit_id(repo,value):
    fmt=git(repo,'rev-parse','--show-object-format')
    length={'sha1':40,'sha256':64}.get(fmt)
    require(length is not None and re.fullmatch('[0-9a-f]{'+str(length)+'}', value) is not None, 'Full literal Git object ID required')
    return value

def verify_governance(repo):
    path=safe_path(repo,'oap/governance/MANIFEST.json')
    manifest=json.loads(read_bytes(path))
    for relative, expected in manifest['files'].items():
        require(digest(read_bytes(safe_path(repo,relative)))==expected, f'Stale governance/source: {relative}')
    require(manifest['architecture_sha256']==digest(read_bytes(repo/'ARCHITECTURE.md')), 'Architecture identity mismatch')
    total=0; rows=[]
    for relative in manifest['coding_read_set']:
        size=len(read_bytes(safe_path(repo,relative))); total+=size
        ceiling=manifest.get('byte_ceilings',{}).get(relative)
        require(ceiling is None or size<=ceiling, f'Context component exceeds declared byte ceiling: {relative}')
        rows.append({'path':relative,'utf8_bytes':size})
    require(total<=manifest['coding_byte_ceiling'], 'Transitive declared coding context exceeds byte ceiling')
    return {'manifest_sha256':digest(read_bytes(path)), 'declared_context_bytes':total,
            'context_files':rows,'exact_model_tokens':'UNMEASURED', 'client_injection_overhead':'UNMEASURED'}

def critical_payload(text):
    start='<!-- OAP-CRITICAL-BEGIN -->\n'; end='<!-- OAP-CRITICAL-END -->'
    require(text.count(start)==1 and text.count(end)==1, 'One exact critical payload required')
    payload=text.split(start,1)[1].split(end,1)[0]
    require(payload.endswith('\n'), 'Critical payload requires terminal LF')
    require(not payload.startswith('\n'), 'Critical payload starts at its heading, no leading blank')
    return payload.encode()

def validate_critical_entry(payload, ident, pr_number, objective):
    text=payload.decode('utf-8'); plain=unfenced(text)
    require(CRIT_RE.findall(plain)==[ident], 'Critical payload must contain exactly the declared ID')
    require(plain.startswith('## '+ident+' — '), 'Critical heading must begin payload')
    require(f'- Introduced by: PR #{pr_number} / OAP objective {objective}' in plain, 'Critical PR/objective provenance mismatch')
    for name in ('Status','Category','Severity','Decision confidence','Required human gate','Affected components'):
        require(len(re.findall(r'^- '+re.escape(name)+r': \S.+$',plain,re.M))==1, f'Missing critical field: {name}')
    require('- Status: OPEN — HUMAN ADJUDICATION REQUIRED' in plain, 'Critical entries must start OPEN')
    require(re.search(r'^- Severity: (low|medium|high|critical)$',plain,re.M), 'Invalid severity')
    require(re.search(r'^- Decision confidence: (low|medium|high)$',plain,re.M), 'Invalid decision confidence')
    for heading in CRIT_SECTIONS: section(text,heading,3)
    require(section(text,'Strategic attestation',3)=='ALL FIVE CRITICAL-ENTRY CONDITIONS SATISFIED', 'Missing five-condition attestation')
    require(section(text,'Human disposition',3).startswith('PENDING') and section(text,'Resolution',3).startswith('PENDING'), 'Agents cannot pre-accept human judgment')
    require('HUMAN ADJUDICATION' not in plain.replace('OPEN — HUMAN ADJUDICATION REQUIRED',''), 'Human disposition cannot be smuggled into entry')

def validate_order(repo,path,check_current=True):
    data=read_bytes(path); text=data.decode('utf-8'); m=metadata(text)
    require(m.get('Status')=='FINAL', 'Draft/non-final orders are not executable')
    require('DRAFT UNTIL STRATEGIC RECONCILIATION' not in text, 'Draft marker remains')
    for key in ('Identifier','PR mode','Branch','Base commit','PR number','Expected active','Provenance','Architecture SHA256','Governance SHA256'):
        require(key in m and 'UNRESOLVED' not in m[key], f'Unresolved metadata: {key}')
    ident=identifier(m['Identifier'])
    require(text.splitlines()[0]=='# OAP Work Order — '+ident, 'Order heading/ID mismatch')
    require(path.name.startswith(ident+'-') and path.suffix=='.md', 'Order filename/ID mismatch')
    commit_id(repo,m['Base commit'])
    require(re.fullmatch(r'oap/'+ident[:3]+r'-[a-z0-9][a-z0-9-]*',m['Branch']) is not None, 'Wrong objective branch')
    mode='CREATE_NEW_PR' if ident.endswith('-a') else 'AMEND_EXISTING_PR'
    require(m['PR mode']==mode, 'Wrong PR mode for suffix')
    require(m['PR number']=='NEW' if mode=='CREATE_NEW_PR' else re.fullmatch(r'[1-9][0-9]*',m['PR number']) is not None, 'Wrong PR number declaration')
    require(re.search(r'(^|[; ])(?:H|A|E|I|C)\b',m['Provenance']) is not None, 'Missing H/A/E/I/C provenance')
    require(m['Expected active']=='NONE' or ID_RE.fullmatch(m['Expected active']), 'Invalid expected active')
    governance=verify_governance(repo)
    for key in ('Architecture SHA256','Governance SHA256'):
        require(re.fullmatch(r'[0-9a-f]{64}',m[key]),'Invalid source digest')
    if check_current:
        require(m['Architecture SHA256']==digest(read_bytes(repo/'ARCHITECTURE.md')), 'Order source architecture is stale')
        require(m['Governance SHA256']==governance['manifest_sha256'], 'Order governance identity is stale')
    for heading in SECTIONS: section(text,heading)
    require(re.search(r'^1\. \S',section(text,'Acceptance criteria'),re.M), 'Numbered acceptance criteria required')
    declaration=section(text,'Deferred human adjudication')
    lines=re.findall(r'^- Decision: (.+)$',declaration,re.M)
    require(len(lines)==1, 'Exactly one DHA declaration required')
    decision=lines[0]
    if decision=='NONE':
        require('OAP-CRITICAL-BEGIN' not in text, 'NONE cannot hide a critical append')
    else:
        require(re.fullmatch(r'APPEND CRIT-[0-9]{4}',decision), 'Invalid DHA declaration')
        require(m['PR number']!='NEW', 'APPEND requires an existing PR in a continuation')
        payload=critical_payload(text)
        validate_critical_entry(payload,decision.split()[1],m['PR number'],ident)
        require(m.get('Critical payload SHA256')==digest(payload), 'Critical payload digest mismatch')
        require(re.fullmatch(r'[0-9a-f]{64}',m.get('Critical prior SHA256','')), 'Trusted prior critical digest required')
    return m

def remote_prs(repository):
    prs=gh('pr','list','--repo',repository,'--state','all','--limit','1000','--json','number,state,headRefName,baseRefName,headRefOid,mergedAt')
    require(len(prs)<1000, 'PR list truncated; paginate explicitly before using this harness')
    return prs

def remote_transition(repo,m,repository):
    ident=m['Identifier']; prior=active(repo); expected=m['Expected active']
    require((prior or 'NONE')==expected or prior==ident, 'Active changed since order reconciliation')
    main=gh('api',f'repos/{repository}/git/ref/heads/main')['object']['sha']
    prs=remote_prs(repository)
    candidates=[p for p in prs if p['headRefName'].startswith('oap/'+ident[:3]+'-')]
    require(len(candidates)<=1, 'Duplicate objective PRs')
    other_open=[p for p in prs if p['state']=='OPEN' and p['headRefName'].startswith('oap/') and p not in candidates]
    require(not other_open, 'Another OAP objective PR is unresolved')
    for p in candidates:
        require(p['headRefName']==m['Branch'] and p['baseRefName']=='main' and p['state']=='OPEN', 'Objective PR branch/base/state mismatch or already terminal')
    if ident.endswith('-a'):
        require(m['Base commit']==main, 'New objective must use current verified main')
        if prior is None:
            require(ident=='000-a', 'First objective must be 000-a')
        elif prior!=ident:
            require(int(ident[:3])==int(prior[:3])+1, 'New objective must follow current numeric objective')
            resolution=json.loads(read_bytes(safe_path(repo,f'oap/reviews/{prior[:3]}-resolution.json')))
            previous=[p for p in prs if p['headRefName'].startswith('oap/'+prior[:3]+'-')]
            require(len(previous)==1 and previous[0]['number']==resolution['pr'], 'Prior resolution/PR mismatch')
            if resolution['decision']=='MERGED':
                require(previous[0]['state']=='MERGED' and resolution.get('accepted_head')==previous[0]['headRefOid'], 'Prior merge/head is not verified')
                merged=gh('pr','view',str(previous[0]['number']),'--repo',repository,'--json','mergeCommit')
                require(merged['mergeCommit']['oid']==resolution.get('merge_commit'), 'Prior merge commit mismatch')
            else:
                require(resolution['decision']=='ABANDONED' and previous[0]['state']=='CLOSED' and not previous[0]['mergedAt'] and resolution.get('dependency_reassessment'), 'Prior abandonment requires closed PR and dependency reassessment')
    else:
        require(prior is not None and prior[:3]==ident[:3], 'Continuation must stay on same objective')
        if prior!=ident:
            require(successor_suffix(prior.split('-')[1])==ident.split('-')[1], 'Continuation suffix must advance exactly once')
            verify_report(repo,repository,prior)
        require(len(candidates)==1 and str(candidates[0]['number'])==m['PR number'], 'Continuation PR identity mismatch')
    return {'main':main,'objective_pr':candidates[0]['number'] if candidates else None}

def load_runtime(path,repo,operational=False):
    config=json.loads(read_bytes(Path(path)))
    require(Path(config['repo_root'])==repo, 'Runtime repository mismatch')
    strategic=resolved_root(config['strategic_home'])
    require(repo!=strategic and repo not in strategic.parents and strategic not in repo.parents, 'Roots must be distinct and non-nested')
    require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',config['github_repository']), 'Invalid repository identity')
    if operational:
        require(config.get('activation_enabled') is True and bool(config.get('activation_authority_reference')), 'Operational activation disabled or authority reference absent')
        require(not config.get('human_stopped',False), 'Human stop is active; no resurrection')
        require(config.get('client_qualification_status')=='QUALIFIED', 'Actual client startup/fresh-context qualification is pending')
    config['_runtime_path']=str(Path(path).absolute())
    return config

def publish_order(repo,source,config,dry_run=False):
    m=validate_order(repo,source); ident=m['Identifier']; expected=m['Expected active']
    current=active(repo)
    require(current in (None if expected=='NONE' else expected, ident), 'Active compare-and-set failed')
    existing=unique(repo,'orders',ident,False)
    if existing: require(read_bytes(existing)==read_bytes(source), 'Activated orders are immutable')
    require(unique(repo,'reports',ident,False) is None, 'Reported/completed round cannot be reactivated')
    facts=remote_transition(repo,m,config['github_repository'])
    if dry_run: return {'status':'VALID_DRY_RUN','identifier':ident,'remote':facts}
    state=safe_path(repo,'.oap-state')
    with lock(state/'publication.lock'):
        require(active(repo)==current, 'Concurrent active transition')
        target=safe_path(repo,'oap/orders/'+source.name)
        atomic_write(target,read_bytes(source),immutable=True)
        atomic_write(safe_path(repo,'oap/active'),(ident+'\n').encode())
        require(active(repo)==ident and read_bytes(target)==read_bytes(source), 'Publication read-back mismatch')
    return {'status':'UNCHANGED' if current==ident and existing else 'PUBLISHED','identifier':ident,'remote':facts}

def verify_report(repo,repository,ident):
    order=unique(repo,'orders',ident); om=metadata(order.read_text())
    report=unique(repo,'reports',ident); data=read_bytes(report); m=metadata(data.decode())
    require(m.get('Identifier')==ident and m.get('Repository')==repository, 'Report identity mismatch')
    require(m.get('Report publication commit')=='SELF', 'Report publication field must be SELF')
    require(m.get('Result') in ('COMPLETE','PARTIAL','BLOCKED','FAILED'), 'Invalid report result')
    impl=commit_id(repo,m.get('Implementation head SHA',''))
    require(re.fullmatch(r'[1-9][0-9]*',m.get('PR number','')), 'Literal report PR required')
    pr=gh('pr','view',m['PR number'],'--repo',repository,'--json','number,state,headRefName,baseRefName,headRefOid')
    require(pr['state']=='OPEN' and pr['baseRefName']=='main' and pr['headRefName']==om['Branch']==m.get('Branch'), 'Report remote PR mismatch')
    duplicates=[p for p in remote_prs(repository) if p['headRefName'].startswith('oap/'+ident[:3]+'-')]
    require(len(duplicates)==1 and duplicates[0]['number']==pr['number'], 'Report objective PR is not unique')
    head=commit_id(repo,pr['headRefOid']); parents=git(repo,'show','-s','--format=%P',head).split()
    require(parents==[impl], 'Report-only commit must have implementation as its sole parent')
    rel=str(report.relative_to(repo))
    changed=git(repo,'diff-tree','--no-commit-id','--name-only','-r',head).splitlines()
    require(changed==[rel], 'Report publication commit must change only its new report')
    require(command(['git','-C',str(repo),'show',head+':'+rel])==data, 'Remote head report bytes differ')
    for path in ('oap/active',str(order.relative_to(repo))):
        require(command(['git','-C',str(repo),'show',impl+':'+path])==read_bytes(repo/path), 'Implementation does not contain exact strategic activation')
    return {'identifier':ident,'pr':pr['number'],'implementation':impl,'report_commit':head,
            'report_sha256':digest(data),'verified_at':now(),'ci':'NOT CERTIFIED BY THIS CHECK'}

def critical_entries(repo):
    text=read_bytes(safe_path(repo,'CRITICAL.md')).decode(); plain=unfenced(text)
    matches=list(CRIT_RE.finditer(plain)); entries={}
    for index,match in enumerate(matches):
        ident=match.group(1); require(ident not in entries,'Duplicate CRITICAL ID')
        end=matches[index+1].start() if index+1<len(matches) else len(plain)
        body=plain[match.start():end]
        gate=re.search(r'^- Required human gate: (.+)$',body,re.M)
        entries[ident]={'gate':gate.group(1) if gate else 'UNKNOWN', 'status':'OPEN',
                       'human_disposition':'UNVERIFIED', 'blocking':True}
    return entries

def append_critical(repo,ident,dry_run=False):
    require(active(repo)==ident, 'Critical append must match active order')
    order=unique(repo,'orders',ident); m=validate_order(repo,order,check_current=False); text=order.read_text()
    declaration=section(text,'Deferred human adjudication')
    match=re.search(r'^- Decision: APPEND (CRIT-[0-9]{4})$',declaration,re.M)
    require(match is not None, 'Active order does not authorize a critical append')
    cid=match.group(1); payload=critical_payload(text); path=safe_path(repo,'CRITICAL.md')
    old=read_bytes(path); prior=m['Critical prior SHA256']
    if old.endswith(payload) and digest(old[:-len(payload)])==prior:
        return {'status':'UNCHANGED','critical_id':cid}
    require(digest(old)==prior, 'CRITICAL prior bytes changed')
    require(cid not in critical_entries(repo), 'Critical ID already exists')
    require(old.endswith(b'\n'), 'Register must end with LF')
    if dry_run: return {'status':'VALID_DRY_RUN','critical_id':cid}
    with lock(safe_path(repo,'.oap-state/critical.lock')):
        require(read_bytes(path)==old,'Concurrent critical append')
        atomic_write(path,old+payload)
    return {'status':'APPENDED','critical_id':cid,'sha256':digest(old+payload)}

def check_state(repo,config=None):
    governance=verify_governance(repo); ident=active(repo)
    order=unique(repo,'orders',ident) if ident else None
    if order: validate_order(repo,order,check_current=False)
    for directory in ('orders','reports'):
        seen=set()
        for path in safe_path(repo,'oap/'+directory).glob('*.md'):
            if path.name=='README.md': continue
            match=re.match(r'([0-9]{3}-[a-z]{1,2})-',path.name)
            require(match is not None,'Unexpected transcript filename')
            require(match.group(1) not in seen,'Duplicate transcript identifier')
            seen.add(match.group(1))
    return {'state':'ACTIVE' if ident else 'INACTIVE','active':ident,
            'order':str(order) if order else None,
            'report':str(unique(repo,'reports',ident,False)) if ident else None,
            'activation_matches_current_governance':(metadata(order.read_text())['Governance SHA256']==governance['manifest_sha256']) if order else None,
            'source_note':'An authorized candidate governance change may differ from activation. Review against accepted base; do not rewrite immutable order.',
            'governance':governance,'critical':critical_state(repo,config),
            'product_qualification':'NOT ESTABLISHED BY SCAFFOLD CHECKS'}

def fifo_stat(path):
    value=path.lstat()
    require(stat.S_ISFIFO(value.st_mode) and value.st_uid==os.getuid(), 'FIFO type/owner mismatch')
    require(stat.S_IMODE(value.st_mode)==0o600,'FIFO must be private mode 0600')
    return value

def fifo_read(path,timeout=None):
    before=fifo_stat(path)
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    try:
        opened=os.fstat(fd); require((opened.st_dev,opened.st_ino)==(before.st_dev,before.st_ino),'FIFO replaced during open')
        deadline=None if timeout is None else time.monotonic()+timeout
        data=b''
        poller=select.poll(); poller.register(fd,select.POLLIN|select.POLLHUP|select.POLLERR)
        while True:
            if deadline is not None: require(time.monotonic()<deadline,'FIFO receive timeout')
            events=poller.poll(50)
            if not events: continue
            require(not events[0][1]&select.POLLERR,'FIFO read error')
            try: chunk=os.read(fd,3-len(data))
            except BlockingIOError: continue
            if chunk:
                data+=chunk
                require(len(data)<=2,'Invalid FIFO length: at least three bytes')
            else:
                require(data==b'OK','Invalid FIFO payload')
                return data
    finally: os.close(fd)

def fifo_write(path,timeout=None):
    before=fifo_stat(path); deadline=None if timeout is None else time.monotonic()+timeout
    while True:
        try: fd=os.open(path,os.O_WRONLY|os.O_NONBLOCK|os.O_NOFOLLOW); break
        except OSError as exc:
            import errno
            if exc.errno!=errno.ENXIO: raise
            if deadline is not None: require(time.monotonic()<deadline,'FIFO sender timeout; no reader')
            time.sleep(0.05)
    try:
        opened=os.fstat(fd); require((opened.st_dev,opened.st_ino)==(before.st_dev,before.st_ino),'FIFO replaced during open')
        data=memoryview(b'OK')
        while data:
            try: count=os.write(fd,data)
            except BlockingIOError:
                select.select([],[fd],[],0.05); continue
            require(count>0,'FIFO zero-length write'); data=data[count:]
    finally: os.close(fd)

def validate_pane(config,role):
    pane=config[role+'_pane']; expected=config['repo_root' if role=='coding' else 'strategic_home']
    require(re.fullmatch(r'%[0-9]+',pane),'Invalid tmux pane ID')
    value=command(['tmux','display-message','-p','-t',pane,'#{pane_current_path}\n#{pane_current_command}']).decode().splitlines()
    require(len(value)>=2 and value[0]==expected and value[1] in config.get('approved_client_commands',['codex']), 'Pane root/client mismatch; inspect before intervention')
    return pane

def wake(config,role,message,fresh=False):
    if config.get('_runtime_path'):
        config=load_runtime(config['_runtime_path'],Path(config['repo_root']),operational=True)
    pane=validate_pane(config,role)
    settle=float(config.get('tmux_key_settle_seconds',0.25))
    if fresh:
        require(config.get('fresh_context_command')=='/new','Fresh coding context command not qualified/configured')
        command(['tmux','send-keys','-t',pane,'-l','/new'])
        time.sleep(settle)
        command(['tmux','send-keys','-t',pane,'Enter'])
        deadline=time.monotonic()+float(config.get('fresh_context_timeout_seconds',15))
        chose_current=False
        while True:
            require(time.monotonic()<deadline,'Fresh client conversation did not become ready; inspect pane, do not paste into unknown dialog')
            time.sleep(settle)
            screen=command(['tmux','capture-pane','-p','-t',pane]).decode()
            if 'Where should the new conversation run?' in screen:
                require(not chose_current,'Checkout chooser did not close after selecting current worktree')
                require(re.search(r'›\s*1\. Use current Git worktree',screen), 'Unexpected checkout selection; preserve current worktree')
                command(['tmux','send-keys','-t',pane,'Enter']); chose_current=True
                time.sleep(settle)
                continue
            if re.search(r'^› /new\s*$',screen,re.M): continue
            if re.search(r'^›(?:\s+.*)?$',screen,re.M) and 'esc to interrupt' not in screen.lower(): break
        validate_pane(config,role)
    # Fixed, single-line trusted prompt; no shell evaluation or client/model alteration.
    command(['tmux','send-keys','-t',pane,'-l',message.replace('\n',' ')])
    time.sleep(settle)
    command(['tmux','send-keys','-t',pane,'Enter'])

def receipt(config,name,payload):
    state=safe_path(Path(config['strategic_home']),'.oap-state')
    target=safe_path(state,name+'.json')
    atomic_write(target,(json.dumps(payload,indent=2)+'\n').encode(),immutable=True,mode=0o600)

def wait_control(repo,config,timeout=None,dry_run=False):
    validate_pane(config,'coding'); fifo_stat(Path(config['strategic_home'])/'control.fifo')
    if dry_run: return {'status':'VALID_DRY_RUN','action':'one control consumer, then fresh coding wake'}
    state=Path(config['strategic_home'])/'.oap-state'
    with lock(state/'control-reader.lock'):
        fifo_read(Path(config['strategic_home'])/'control.fifo',timeout)
        current=check_state(repo); ident=current['active']; require(ident is not None,'Control without active order')
        require(unique(repo,'reports',ident,False) is None,'Control for already reported round')
        require(not (state/f'control-consumed-{ident}.json').exists(),'Duplicate control; explicit recovery required')
        receipt(config,'control-consumed-'+ident,{'identifier':ident,'at':now(),'state':'CONSUMED_BEFORE_WAKE'})
        wake(config,'coding',read_bytes(repo/'oap/prompts/coding-startup.txt').decode(),fresh=True)
    return {'status':'CONTROL_OK_CONSUMED_AND_WAKE_SENT','identifier':ident}

def signal_wait(repo,config,ident,timeout=None,dry_run=False):
    require(active(repo)==ident,'Signal identifier is not active')
    validate_order(repo,unique(repo,'orders',ident)); validate_pane(config,'strategic'); validate_pane(config,'coding')
    home=Path(config['strategic_home']); fifo_stat(home/'control.fifo'); fifo_stat(home/'response.fifo')
    require(unique(repo,'reports',ident,False) is None,'Never resignal a reported round')
    state=home/'.oap-state'
    require(not (state/f'control-send-{ident}.json').exists(),'Control send already attempted; reconcile instead of replay')
    if dry_run: return {'status':'VALID_DRY_RUN','identifier':ident}
    with lock(state/'control-writer.lock'), lock(state/'response-reader.lock'):
        receipt(config,'control-send-'+ident,{'identifier':ident,'at':now(),'state':'ATTEMPTED_BEFORE_SEND'})
        fifo_write(home/'control.fifo',timeout)
        fifo_read(home/'response.fifo',timeout)
        require(active(repo)==ident,'Active changed during response wait')
        verified=verify_report(repo,config['github_repository'],ident)
        receipt(config,'response-consumed-'+ident,verified)
        wake(config,'strategic','OAP_RESPONSE_OK_RECEIVED for '+ident+'. The sole wrapper consumed exact OK and verified remote report publication. Reconcile the report and current GitHub head, independently review, and continue within the activated mandate. Do not read the response FIFO again.')
    return {'status':'RESPONSE_OK_VERIFIED_AND_WAKE_SENT',**verified}

def respond(repo,config,ident,timeout=None,dry_run=False):
    require(active(repo)==ident,'Response identifier is not active')
    verified=verify_report(repo,config['github_repository'],ident)
    home=Path(config['strategic_home']); state=home/'.oap-state'; fifo_stat(home/'response.fifo')
    require(not (state/f'response-send-{ident}.json').exists(),'Response already attempted; reconcile lost notification')
    if dry_run: return {'status':'VALID_DRY_RUN',**verified}
    with lock(state/'response-writer.lock'):
        receipt(config,'response-send-'+ident,verified)
        fifo_write(home/'response.fifo',timeout)
    return {'status':'RESPONSE_OK_SENT',**verified}

def verify_human(repo,config,statement,signature,dry_run=False):
    trust=config.get('human_allowed_signers'); principal=config.get('human_signer_identity')
    require(trust and principal,'Trusted human signer configuration absent; dispositions remain unverified')
    statement_bytes=read_bytes(statement); record=json.loads(statement_bytes)
    require(record.get('repository')==config['github_repository'],'Human statement repository mismatch')
    require(record.get('decision') in ('ACCEPTED','REJECTED','CHANGE REQUIRED','DEFERRED'),'Invalid human disposition')
    for key in ('critical_id','entry_sha256','gate','authority','recorded_at','conditions','evidence'):
        require(key in record,'Missing human statement field: '+key)
    entries=critical_entries(repo); cid=record['critical_id']; require(cid in entries,'Unknown critical entry')
    require(record['gate']==entries[cid]['gate'],'Disposition gate mismatch')
    # Exact admitted bytes come from the unique strategic order, never reconstructed prose.
    matching=[]
    for order in (repo/'oap/orders').glob('*.md'):
        if order.name=='README.md': continue
        text=order.read_text()
        if re.search(r'^- Decision: APPEND '+re.escape(cid)+r'$',unfenced(text),re.M):
            matching.append(critical_payload(text))
    require(len(matching)==1 and digest(matching[0])==record['entry_sha256'],'Disposition entry identity mismatch')
    require(read_bytes(repo/'CRITICAL.md').count(matching[0])==1,'Original critical entry bytes were altered or duplicated')
    command(['ssh-keygen','-Y','verify','-f',str(trust),'-I',principal,'-n','slaif-oap-dha','-s',str(signature)],input=statement_bytes)
    require(record['recorded_at'].endswith(('Z','+00:00')),'Disposition time must be explicit UTC')
    dt.datetime.fromisoformat(record['recorded_at'].replace('Z','+00:00'))
    if dry_run: return {'status':'SIGNATURE_VERIFIED_DRY_RUN','critical_id':cid}
    base=safe_path(repo,'oap/adjudications/'+cid+'-'+digest(statement_bytes))
    with lock(safe_path(repo,'.oap-state/critical.lock')):
        atomic_write(base.with_suffix('.json'),statement_bytes,immutable=True)
        atomic_write(base.with_suffix('.sig'),read_bytes(signature),immutable=True)
    return {'status':'HUMAN_RECORD_IMPORTED','critical_id':cid,'decision':record['decision'],
            'note':'Gate applies only after checking latest attributable statement; never deployment authorization.'}

def critical_state(repo,config=None):
    entries=critical_entries(repo)
    records=safe_path(repo,'oap/adjudications')
    if not config or not records.exists(): return entries
    for cid,state in entries.items():
        valid=[]; invalid=False
        for statement in records.glob(cid+'-*.json'):
            try:
                verify_human(repo,config,statement,statement.with_suffix('.sig'),True)
                record=json.loads(read_bytes(statement))
                valid.append((dt.datetime.fromisoformat(record['recorded_at'].replace('Z','+00:00')),record))
            except (ProtocolError,ValueError,OSError,KeyError): invalid=True
        if invalid:
            state['human_disposition']='UNVERIFIED_RECORD_PRESENT'
        elif valid:
            valid.sort(key=lambda item:item[0]); latest=valid[-1]
            if sum(item[0]==latest[0] for item in valid)>1:
                state['human_disposition']='AMBIGUOUS_LATEST_RECORD'
            else:
                state['human_disposition']=latest[1]['decision']
                state['blocking']=latest[1]['decision']!='ACCEPTED'
                state['human_recorded_at']=latest[1]['recorded_at']
    return entries

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['check','validate-order','publish-order','verify-report','append-critical','wait-control','signal-wait','respond','verify-human'])
    parser.add_argument('--repo-root',required=True)
    parser.add_argument('--runtime')
    parser.add_argument('--role',choices=['STRATEGIC','CODING','BOOTSTRAP','AUDIT'],default='BOOTSTRAP')
    parser.add_argument('--source',type=Path); parser.add_argument('--identifier')
    parser.add_argument('--statement',type=Path); parser.add_argument('--signature',type=Path)
    parser.add_argument('--timeout',type=float); parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(argv)
    try:
        repo=resolved_root(args.repo_root)
        op=args.operation
        operational=op in ('publish-order','wait-control','signal-wait','respond') and not args.dry_run
        config=load_runtime(args.runtime,repo,operational) if args.runtime else None
        if op=='check': result=check_state(repo,config)
        elif op=='validate-order': require(args.source is not None,'--source required'); result=validate_order(repo,args.source)
        elif op=='publish-order':
            require(args.role=='STRATEGIC' and config is not None and args.source is not None,'Strategic role/runtime/source required')
            result=publish_order(repo,args.source,config,args.dry_run)
        elif op=='verify-report':
            require(config is not None and args.identifier is not None,'Runtime and identifier required')
            result=verify_report(repo,config['github_repository'],args.identifier)
        elif op=='append-critical':
            require(args.role=='CODING' and args.identifier is not None,'Coding role and identifier required')
            result=append_critical(repo,args.identifier,args.dry_run)
        elif op=='wait-control':
            require(args.role=='CODING' and config is not None,'Coding role/runtime required')
            result=wait_control(repo,config,args.timeout,args.dry_run)
        elif op=='signal-wait':
            require(args.role=='STRATEGIC' and config is not None and args.identifier is not None,'Strategic role/runtime/identifier required')
            result=signal_wait(repo,config,args.identifier,args.timeout,args.dry_run)
        elif op=='respond':
            require(args.role=='CODING' and config is not None and args.identifier is not None,'Coding role/runtime/identifier required')
            result=respond(repo,config,args.identifier,args.timeout,args.dry_run)
        else:
            require(config is not None and args.statement is not None and args.signature is not None,'Runtime, signed statement and signature required')
            result=verify_human(repo,config,args.statement,args.signature,args.dry_run)
        print(json.dumps(result,indent=2)); return 0
    except (ProtocolError,ValueError,OSError,KeyError) as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc)}),file=sys.stderr); return 2

if __name__=='__main__':
    raise SystemExit(main())

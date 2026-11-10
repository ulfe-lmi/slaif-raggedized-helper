"""Protocol behavior tests: disposable Git/files/FIFOs; no live agent/service calls."""
from pathlib import Path
import concurrent.futures
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(SOURCE/'oap/bin'))
import oaplib as oap
import materialize

# Deterministic synthetic empty DHA register for disposable fixtures. The live
# CRITICAL.md is never used to seed a fixture and is never rewritten by tests.
CRITICAL_SEED=b'''# Deferred Human Adjudication register (fixture seed)

Deterministic synthetic empty register for disposable OAP fixtures.
No entries.
'''

def live_transcript(root):
    """Read-only byte-for-byte snapshot of a real OAP transcript/register."""
    parts={'active':(root/'oap/active').read_bytes() if (root/'oap/active').exists() else None,
           'critical':(root/'CRITICAL.md').read_bytes()}
    for directory in ('orders','reports'):
        parts[directory]={p.name:p.read_bytes() for p in (root/'oap'/directory).iterdir() if p.is_file()}
    return parts

# Entries omitted from fixture copies: git-ignored, private or heavy locations
# (virtualenvs, caches, corpora, model artifacts, build output, private env and
# runtime files). Only owned source/code/governance is copied into disposable
# fixtures, so a new .venv or later corpus/model cache can never be copied into
# every fixture or accidentally committed in a temporary test repository
# (objective 002-a). No real private data is written or deleted by tests.
COPY_IGNORE_DIRS=('__pycache__','.git','.oap-state','.oap-local','.codex',
                  '.venv','venv','env','ENV',
                  '.cache','.pytest_cache','.mypy_cache','.ruff_cache','.hypothesis',
                  'corpus','models','model-cache','benchmark-private',
                  'build','dist','wheels')
COPY_IGNORE_FILES=('.env','runtime.json')
ENV_FILE_PREFIX='.env.'

def _fixture_ignore(source,names):
    ignored=set()
    for name in names:
        if name in COPY_IGNORE_DIRS or name in COPY_IGNORE_FILES:
            ignored.add(name); continue
        if name.startswith(ENV_FILE_PREFIX):
            ignored.add(name); continue
        if name=='private' and Path(source).name=='eval':
            ignored.add(name); continue
    return ignored

def copy_owned_source(src,dst):
    """Copy owned source into a fixture, omitting ignored/private/heavy entries."""
    shutil.copytree(src,dst,ignore=_fixture_ignore)

def run(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()

def inventory(root):
    return {str(p.relative_to(root)):(p.lstat().st_mode,p.read_bytes() if p.is_file() and not p.is_symlink() else os.readlink(p) if p.is_symlink() else None)
            for p in root.rglob('*')}

class Harness(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='oap-fixture-')
        self.base=Path(self.temp.name)
        self.repo=self.base/'répo with spaces'; self.home=self.base/'strategy'
        copy_owned_source(SOURCE,self.repo)
        # Deterministic synthetic empty OAP transcript/register/state: the fixture
        # must not inherit the live activation, orders, reports or CRITICAL entries
        # (T01). Only this temporary copy is reset; the live worktree stays intact.
        active=self.repo/'oap/active'
        if active.exists(): active.unlink()
        for directory in ('orders','reports'):
            for path in (self.repo/'oap'/directory).iterdir():
                if path.is_file() and path.name!='README.md': path.unlink()
        adjudications=self.repo/'oap/adjudications'
        if adjudications.exists(): shutil.rmtree(adjudications)
        (self.repo/'CRITICAL.md').write_bytes(CRITICAL_SEED)
        self.home.mkdir()
        run(self.repo,'init','-b','main'); run(self.repo,'config','user.email','fixture@example.invalid')
        run(self.repo,'config','user.name','Synthetic fixture')
        run(self.repo,'add','.'); run(self.repo,'commit','-m','fixture base')
        self.head=run(self.repo,'rev-parse','HEAD')
        self.config={'repo_root':str(self.repo),'strategic_home':str(self.home),'github_repository':'fixture/project',
                     'activation_enabled':False,'activation_authority_reference':'','coding_pane':'%2','strategic_pane':'%1',
                     'approved_client_commands':['codex'],'fresh_context_command':'/new','fresh_context_delay_seconds':0,
                     'tmux_key_settle_seconds':0,
                     'client_qualification_status':'PENDING'}

    def tearDown(self): self.temp.cleanup()

    def final_order(self,ident='000-a',expected='NONE',critical=False):
        path=self.base/(ident+'-fixture.md')
        text=(self.repo/'oap/templates/order.md').read_text()
        text=text.replace('NNN-a',ident).replace('NNN-purpose',ident[:3]+'-fixture')
        text=text.replace('DRAFT UNTIL STRATEGIC RECONCILIATION','FINAL')
        text=text.replace('Base commit: UNRESOLVED','Base commit: '+self.head)
        text=text.replace('Expected active: UNRESOLVED','Expected active: '+expected)
        text=text.replace('Architecture SHA256: UNRESOLVED','Architecture SHA256: '+oap.digest((self.repo/'ARCHITECTURE.md').read_bytes()))
        text=text.replace('Governance SHA256: UNRESOLVED','Governance SHA256: '+oap.digest((self.repo/'oap/governance/MANIFEST.json').read_bytes()))
        if not ident.endswith('-a'): text=text.replace('CREATE_NEW_PR','AMEND_EXISTING_PR').replace('PR number: NEW','PR number: 12')
        if critical:
            template=(self.repo/'oap/templates/critical-entry.md').read_text().split('```text\n')[1].split('```')[0]
            template=template.replace('PR #123 / OAP objective 001-b','PR #12 / OAP objective '+ident)
            text=text.replace('Provenance: H/A/E/I/C plus concrete source reference','Provenance: H fixture authority\nCritical prior SHA256: '+oap.digest((self.repo/'CRITICAL.md').read_bytes())+'\nCritical payload SHA256: '+oap.digest(template.encode()))
            text=text.replace('- Decision: NONE','- Decision: APPEND CRIT-0001\n\n<!-- OAP-CRITICAL-BEGIN -->\n'+template+'<!-- OAP-CRITICAL-END -->')
        path.write_text(text); return path

    def activate_local(self,path):
        ident=oap.metadata(path.read_text())['Identifier']
        shutil.copyfile(path,self.repo/'oap/orders'/path.name)
        (self.repo/'oap/active').write_text(ident+'\n')

    def fake_gh(self,*args):
        if args[:1]==('api',): return {'object':{'sha':self.head}}
        if args[:2]==('pr','list'): return []
        raise AssertionError(args)

    def report_fixture(self,extra=False,wrong_parent=False):
        order=self.final_order(); self.activate_local(order)
        run(self.repo,'switch','-c','oap/000-fixture')
        (self.repo/'implementation.txt').write_text('a bounded change\n')
        run(self.repo,'add','.'); run(self.repo,'commit','-m','implementation')
        impl=run(self.repo,'rev-parse','HEAD')
        report=self.repo/'oap/reports/000-a-fixture.md'
        report.write_text('# OAP Coding Report — 000-a\n\nIdentifier: 000-a\nResult: COMPLETE\nRepository: fixture/project\nPR number: 12\nBranch: oap/000-fixture\nImplementation head SHA: '+(self.head if wrong_parent else impl)+'\nReport publication commit: SELF\n\n## Evidence\nFixture behavior only.\n')
        if extra: (self.repo/'unrelated.txt').write_text('not allowed in report commit\n')
        run(self.repo,'add','.'); run(self.repo,'commit','-m','report')
        head=run(self.repo,'rev-parse','HEAD')
        pr={'number':12,'state':'OPEN','headRefName':'oap/000-fixture','baseRefName':'main','headRefOid':head,'mergedAt':None}
        def remote(*args):
            if args[:2]==('pr','list'): return [pr]
            if args[:2]==('pr','view'): return pr
            raise AssertionError(args)
        return remote,report,impl,head

    def test_inactive_sources_and_context(self):
        state=oap.check_state(self.repo)
        self.assertEqual(state['state'],'INACTIVE'); self.assertFalse(state['critical'])
        self.assertLessEqual(state['governance']['declared_context_bytes'],50000)
        self.assertEqual(state['governance']['exact_model_tokens'],'UNMEASURED')

    def test_fixture_transcript_isolated_and_live_preserved(self):
        # Fixture is deterministically seeded inactive/empty regardless of the live
        # checkout's activation, orders, reports or register content.
        self.assertFalse((self.repo/'oap/active').exists())
        self.assertEqual(sorted(p.name for p in (self.repo/'oap/orders').iterdir()),['README.md'])
        self.assertEqual(sorted(p.name for p in (self.repo/'oap/reports').iterdir()),['README.md'])
        self.assertFalse((self.repo/'oap/adjudications').exists())
        self.assertEqual((self.repo/'CRITICAL.md').read_bytes(),CRITICAL_SEED)
        self.assertEqual(oap.critical_entries(self.repo),{})
        # Mutating the fixture transcript never changes live worktree bytes.
        before=live_transcript(SOURCE)
        order=self.final_order('000-b','000-a',True); self.activate_local(order)
        oap.append_critical(self.repo,'000-b')
        (self.repo/'oap/reports/000-b-fixture.md').write_text('fixture report only\n')
        self.assertEqual(live_transcript(SOURCE),before)
        # ...and the mutation stayed inside the fixture.
        self.assertEqual(oap.active(self.repo),'000-b')
        self.assertNotEqual((self.repo/'CRITICAL.md').read_bytes(),CRITICAL_SEED)
        self.assertTrue((self.repo/'oap/reports/000-b-fixture.md').exists())

    def test_source_tamper_is_stale(self):
        (self.repo/'ARCHITECTURE.md').write_text('changed')
        with self.assertRaises(oap.ProtocolError): oap.verify_governance(self.repo)

    def test_active_requires_exact_lf(self):
        for payload in (b'',b'000-a',b'000-a\n\n',b'000-a\r\n',b'../x\n',b'000-aaa\n'):
            (self.repo/'oap/active').write_bytes(payload)
            with self.assertRaises(oap.ProtocolError): oap.active(self.repo)
        (self.repo/'oap/active').write_bytes(b'000-aa\n'); self.assertEqual(oap.active(self.repo),'000-aa')

    def test_active_symlink_refused(self):
        (self.repo/'oap/active').symlink_to(self.base/'missing')
        with self.assertRaises(oap.ProtocolError): oap.active(self.repo)

    def test_suffix_progression(self):
        self.assertEqual([oap.successor_suffix(x) for x in ('a','z','az','zy')],['b','aa','ba','zz'])
        with self.assertRaises(oap.ProtocolError): oap.successor_suffix('zz')

    def test_final_order_and_draft_refusal(self):
        self.assertEqual(oap.validate_order(self.repo,self.final_order())['Identifier'],'000-a')
        draft=next((self.repo/'oap/strategic-instructions/initial-orders').glob('000-a-*'))
        with self.assertRaises(oap.ProtocolError): oap.validate_order(self.repo,draft)

    def test_missing_dha_and_duplicate_metadata_refuse(self):
        order=self.final_order(); original=order.read_text()
        for text in (original.replace('- Decision: NONE','No decision supplied'), original.replace('Status: FINAL','Status: FINAL\nStatus: FINAL')):
            order.write_text(text)
            with self.assertRaises(oap.ProtocolError): oap.validate_order(self.repo,order)

    def test_missing_acceptance_and_stale_source_refuse(self):
        order=self.final_order(); original=order.read_text()
        for text in (original.replace('1. Observable','Observable'),original.replace(oap.digest((self.repo/'ARCHITECTURE.md').read_bytes()),'0'*64)):
            order.write_text(text)
            with self.assertRaises(oap.ProtocolError): oap.validate_order(self.repo,order)

    def test_dry_run_no_write_then_publish_and_noop(self):
        order=self.final_order(); before=inventory(self.repo)
        with patch.object(oap,'gh',side_effect=self.fake_gh):
            self.assertEqual(oap.publish_order(self.repo,order,self.config,True)['status'],'VALID_DRY_RUN')
            self.assertEqual(inventory(self.repo),before)
            self.assertEqual(oap.publish_order(self.repo,order,self.config)['status'],'PUBLISHED')
            after=inventory(self.repo)
            self.assertEqual(oap.publish_order(self.repo,order,self.config)['status'],'UNCHANGED')
            self.assertEqual(inventory(self.repo),after)
        self.assertEqual((self.repo/'oap/active').read_bytes(),b'000-a\n')

    def test_interrupted_publication_is_identically_recoverable(self):
        order=self.final_order(); real=oap.atomic_write
        def interrupted(path,*a,**kw):
            if path.name=='active': raise OSError('fixture power loss')
            return real(path,*a,**kw)
        with patch.object(oap,'gh',side_effect=self.fake_gh):
            with patch.object(oap,'atomic_write',side_effect=interrupted):
                with self.assertRaises(OSError): oap.publish_order(self.repo,order,self.config)
            self.assertIsNone(oap.active(self.repo)); self.assertIsNotNone(oap.unique(self.repo,'orders','000-a'))
            oap.publish_order(self.repo,order,self.config)
        self.assertEqual(oap.active(self.repo),'000-a')

    def test_immutable_and_reported_round_refuse(self):
        order=self.final_order(); self.activate_local(order)
        order.write_text(order.read_text().replace('Concrete user/operator behavior','Changed behavior'))
        with self.assertRaises(oap.ProtocolError): oap.publish_order(self.repo,order,self.config)
        shutil.copyfile(self.repo/'oap/orders'/order.name,order)
        (self.repo/'oap/reports/000-a-fixture.md').write_text('already reported')
        with self.assertRaises(oap.ProtocolError): oap.publish_order(self.repo,order,self.config)

    def test_duplicate_order_and_pr_refuse(self):
        order=self.final_order(); self.activate_local(order)
        shutil.copyfile(order,self.repo/'oap/orders/000-a-duplicate.md')
        with self.assertRaises(oap.ProtocolError): oap.unique(self.repo,'orders','000-a')
        (self.repo/'oap/orders/000-a-duplicate.md').unlink()
        with patch.object(oap,'gh',side_effect=lambda *a: {'object':{'sha':self.head}} if a[0]=='api' else [{'headRefName':'oap/000-x'},{'headRefName':'oap/000-y'}]):
            with self.assertRaises(oap.ProtocolError): oap.remote_transition(self.repo,oap.validate_order(self.repo,order),'fixture/project')

    def test_unknown_role_and_disabled_runtime_refuse_mutation(self):
        runtime=self.base/'runtime.json'; runtime.write_text(json.dumps(self.config))
        with self.assertRaises(oap.ProtocolError): oap.load_runtime(runtime,self.repo,True)
        result=subprocess.run([sys.executable,str(self.repo/'oap/bin/publish_order.py'),'--repo-root',str(self.repo),'--runtime',str(runtime),'--source',str(self.final_order()),'--dry-run'],capture_output=True)
        self.assertEqual(result.returncode,2); self.assertFalse((self.repo/'oap/active').exists())

    def test_critical_exact_append_retry_and_history(self):
        order=self.final_order('000-b','000-a',True); self.activate_local(order)
        before=(self.repo/'CRITICAL.md').read_bytes(); payload=oap.critical_payload(order.read_text())
        oap.append_critical(self.repo,'000-b')
        self.assertEqual((self.repo/'CRITICAL.md').read_bytes(),before+payload)
        self.assertEqual(oap.append_critical(self.repo,'000-b')['status'],'UNCHANGED')
        self.assertTrue(oap.critical_entries(self.repo)['CRIT-0001']['blocking'])

    def test_critical_prior_mismatch_and_missing_attestation(self):
        order=self.final_order('000-b','000-a',True); self.activate_local(order)
        (self.repo/'CRITICAL.md').write_bytes((self.repo/'CRITICAL.md').read_bytes()+b'changed\n')
        with self.assertRaises(oap.ProtocolError): oap.append_critical(self.repo,'000-b')
        order.write_text(order.read_text().replace('ALL FIVE CRITICAL-ENTRY CONDITIONS SATISFIED','asserted without evidence'))
        with self.assertRaises(oap.ProtocolError): oap.validate_order(self.repo,order)

    def test_critical_fenced_examples_ignored_and_duplicate_ids_refuse(self):
        path=self.repo/'CRITICAL.md'; initial=path.read_text()
        path.write_text(initial+'\n```text\n## CRIT-0001 — example\n```\n')
        self.assertEqual(oap.critical_entries(self.repo),{})
        path.write_text(initial+'\n## CRIT-0001 — one\n## CRIT-0001 — two\n')
        with self.assertRaises(oap.ProtocolError): oap.critical_entries(self.repo)

    def test_report_real_git_parent_and_only_path(self):
        remote,report,impl,head=self.report_fixture()
        with patch.object(oap,'gh',side_effect=remote):
            proof=oap.verify_report(self.repo,'fixture/project','000-a')
        self.assertEqual(proof['implementation'],impl); self.assertEqual(proof['report_commit'],head)

    def test_report_extra_file_refused(self):
        remote,_,_,_=self.report_fixture(extra=True)
        with patch.object(oap,'gh',side_effect=remote),self.assertRaises(oap.ProtocolError): oap.verify_report(self.repo,'fixture/project','000-a')

    def test_report_wrong_parent_refused(self):
        remote,_,_,_=self.report_fixture(wrong_parent=True)
        with patch.object(oap,'gh',side_effect=remote),self.assertRaises(oap.ProtocolError): oap.verify_report(self.repo,'fixture/project','000-a')

    def test_local_report_tamper_refused(self):
        remote,report,_,_=self.report_fixture(); report.write_text(report.read_text()+'local-only change\n')
        with patch.object(oap,'gh',side_effect=remote),self.assertRaises(oap.ProtocolError): oap.verify_report(self.repo,'fixture/project','000-a')

    def test_real_fifo_git_round_trip_and_no_replay(self):
        order=self.final_order(); self.activate_local(order)
        for name in ('control.fifo','response.fifo'): os.mkfifo(self.home/name,0o600)
        remote_holder={}; wakes=[]
        def remote(*args): return remote_holder['call'](*args)
        def client_wake(config,role,message,fresh=False):
            wakes.append((role,fresh))
            if role=='coding':
                remote_holder['call']=self.report_fixture()[0]
                oap.respond(self.repo,self.config,'000-a',timeout=3)
        with patch.object(oap,'gh',side_effect=remote),patch.object(oap,'validate_pane',return_value='%fixture'),patch.object(oap,'wake',side_effect=client_wake):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                worker=pool.submit(oap.wait_control,self.repo,self.config,3)
                manager=pool.submit(oap.signal_wait,self.repo,self.config,'000-a',3)
                self.assertEqual(worker.result(timeout=5)['status'],'CONTROL_OK_CONSUMED_AND_WAKE_SENT')
                self.assertEqual(manager.result(timeout=5)['status'],'RESPONSE_OK_VERIFIED_AND_WAKE_SENT')
            with self.assertRaises(oap.ProtocolError): oap.signal_wait(self.repo,self.config,'000-a',0.1)
        self.assertEqual(wakes,[('coding',True),('strategic',False)])
        self.assertTrue((self.home/'.oap-state/control-consumed-000-a.json').exists())
        self.assertTrue((self.home/'.oap-state/response-consumed-000-a.json').exists())

    def test_current_head_change_invalidates_report_verification(self):
        remote,_,_,_=self.report_fixture()
        (self.repo/'later.txt').write_text('new unreviewed change')
        run(self.repo,'add','.'); run(self.repo,'commit','-m','changed head')
        new_head=run(self.repo,'rev-parse','HEAD')
        def changed(*args):
            result=remote(*args)
            if isinstance(result,list): return [{**x,'headRefOid':new_head} for x in result]
            return {**result,'headRefOid':new_head}
        with patch.object(oap,'gh',side_effect=changed),self.assertRaises(oap.ProtocolError): oap.verify_report(self.repo,'fixture/project','000-a')

    def test_pane_wrong_directory_cannot_receive_wake(self):
        with patch.object(oap,'command',return_value=b'/wrong/project\ncodex\n') as called:
            with self.assertRaises(oap.ProtocolError): oap.wake(self.config,'coding','hello',True)
            self.assertEqual(called.call_count,1)

    def test_fresh_context_wake_arguments_no_shell_or_model_switch(self):
        calls=[]
        def fake(argv,**kw):
            calls.append(argv)
            if argv[1]=='capture-pane': return b'\n\xe2\x80\xba Ask Codex to do anything\n'
            return (str(self.repo)+'\ncodex\n').encode() if argv[1]=='display-message' else b''
        with patch.object(oap,'command',side_effect=fake): oap.wake(self.config,'coding','role prompt\nnext line',True)
        self.assertIn(['tmux','send-keys','-t','%2','-l','/new'],calls)
        self.assertIn(['tmux','send-keys','-t','%2','-l','role prompt next line'],calls)
        self.assertFalse(any('/model' in str(x) or 'bash' in x for x in calls))

    def test_fresh_context_chooses_current_worktree_only(self):
        captures=iter(['Where should the new conversation run?\n› 1. Use current Git worktree\n  2. Create new Git worktree','› Ask Codex to do anything'])
        calls=[]
        def fake(argv,**kw):
            calls.append(argv)
            if argv[1]=='capture-pane': return next(captures).encode()
            return (str(self.repo)+'\ncodex\n').encode() if argv[1]=='display-message' else b''
        with patch.object(oap,'command',side_effect=fake): oap.wake(self.config,'coding','setup only',True)
        self.assertEqual(sum(a[-1]=='Enter' for a in calls),3)

    def test_unknown_checkout_selection_refuses_prompt(self):
        calls=[]
        def fake(argv,**kw):
            calls.append(argv)
            if argv[1]=='capture-pane': return 'Where should the new conversation run?\n  1. Use current Git worktree\n› 2. Create new Git worktree'.encode()
            return (str(self.repo)+'\ncodex\n').encode() if argv[1]=='display-message' else b''
        with patch.object(oap,'command',side_effect=fake),self.assertRaises(oap.ProtocolError): oap.wake(self.config,'coding','must not send',True)
        self.assertFalse(any('must not send' in a for a in calls))

    def test_setup_dry_run_works_without_credentials(self):
        runtime=self.base/'runtime.json'; runtime.write_text(json.dumps(self.config))
        result=subprocess.run([sys.executable,str(self.repo/'oap/bin/setup.py'),'--repo-root',str(self.repo),'--runtime',str(runtime),'--new-session','fixture-oap','--dry-run'],capture_output=True,check=True)
        record=json.loads(result.stdout); self.assertFalse(record['starts_agents']); self.assertFalse(record['needs_credentials'])

    def test_human_signature_and_latest_disposition_gates(self):
        if not shutil.which('ssh-keygen'): self.skipTest('ssh-keygen unavailable: actual signature test not run')
        order=self.final_order('000-b','000-a',True); self.activate_local(order); oap.append_critical(self.repo,'000-b')
        key=self.base/'synthetic-human-key'
        subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(key)],check=True)
        signers=self.base/'allowed-signers'; signers.write_text('fixture-human '+key.with_suffix('.pub').read_text())
        config={**self.config,'human_allowed_signers':str(signers),'human_signer_identity':'fixture-human'}
        payload=oap.critical_payload(order.read_text())
        for number,decision in enumerate(('ACCEPTED','DEFERRED')):
            record={'repository':'fixture/project','critical_id':'CRIT-0001','entry_sha256':oap.digest(payload),
                    'gate':'before controlled pilot','decision':decision,'authority':'fixture human',
                    'recorded_at':f'2026-11-01T00:00:0{number}Z','conditions':'fixture only','evidence':'synthetic test'}
            statement=self.base/f'human-{number}.json'; statement.write_text(json.dumps(record))
            subprocess.run(['ssh-keygen','-Y','sign','-f',str(key),'-n','slaif-oap-dha',str(statement)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            oap.verify_human(self.repo,config,statement,Path(str(statement)+'.sig'))
            state=oap.critical_state(self.repo,config)['CRIT-0001']
            self.assertEqual(state['human_disposition'],decision); self.assertEqual(state['blocking'],decision!='ACCEPTED')
        self.assertTrue(oap.critical_state(self.repo,self.config)['CRIT-0001']['blocking'])

    def test_source_copy_excludes_ignored_heavy_directories(self):
        # Boundary: canary ignored content planted in the owned-source fixture
        # (heavy directories and private files) must not survive the fixture
        # copy and must never reach the temporary test repository's committed
        # tree (objective 002-a). Only fixture-owned canary content is written.
        # The canary is assembled at runtime so its full byte string never
        # appears in this owned source file (the copy must contain none of it).
        canary=b'OAP-002-BOUNDARY-CAN' + b'ARY'
        heavy=[('.venv','pyvenv.cfg'),('corpus','data.bin'),('model-cache','weights.bin'),
               ('.cache','tmp.bin'),('env','config.toml'),('models','cache.bin'),
               ('eval/private','secret.txt')]
        for *parents,name in heavy:
            path=self.repo.joinpath(*parents,name); path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(canary)
        for name in ('.env','.env.local','runtime.json'):
            (self.repo/name).write_bytes(canary)
        destination=self.base/'recopy'
        copy_owned_source(self.repo,destination)
        for root,dirs,files in os.walk(destination):
            for directory in dirs:
                self.assertNotIn(directory,COPY_IGNORE_DIRS,f'ignored directory copied: {directory}')
            for name in files:
                self.assertNotIn(canary,(Path(root)/name).read_bytes())
        for name in ('.env','.env.local','runtime.json'):
            self.assertFalse((destination/name).exists(),f'private file copied: {name}')
        self.assertFalse((destination/'eval'/'private').exists(),'eval/private copied into fixture')
        # Owned source still survives the narrowed copy.
        for owned in ('oap/README.md','oap/governance/MANIFEST.json',
                      'src/slaif_raggedized_helper/__init__.py','pyproject.toml',
                      'uv.lock','.github/workflows/oap.yml','ARCHITECTURE.md',
                      'tests/oap/test_harness.py'):
            self.assertTrue((destination/owned).is_file(),f'missing owned path: {owned}')
        # The fixture's own committed tree contains no canary bytes either.
        grep=subprocess.run(['git','-C',str(self.repo),'grep','-I','-l',canary.decode()],
                            capture_output=True,text=True)
        self.assertEqual(grep.stdout.strip(),'')

class PipeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='oap-pipe-fixture-'); self.root=Path(self.temp.name)
        self.pipe=self.root/'control.fifo'; os.mkfifo(self.pipe,0o600)
    def tearDown(self): self.temp.cleanup()

    def exchange(self,chunks):
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future=pool.submit(oap.fifo_read,self.pipe,1.5)
            fd=os.open(self.pipe,os.O_WRONLY)
            try:
                for chunk in chunks: os.write(fd,chunk); time.sleep(0.01)
            finally: os.close(fd)
            return future.result(timeout=2)

    def test_exact_and_partial_reads(self):
        self.assertEqual(self.exchange([b'O',b'K']),b'OK')
    def test_newline_nul_partial_and_empty_refused(self):
        for chunks in ([b'OK\n'],[b'O\0'],[b'O'],[]):
            with self.assertRaises(oap.ProtocolError): self.exchange(chunks)
    def test_no_sender_timeout(self):
        with self.assertRaises(oap.ProtocolError): oap.fifo_read(self.pipe,0.05)
    def test_no_reader_timeout(self):
        with self.assertRaises(oap.ProtocolError): oap.fifo_write(self.pipe,0.05)
    def test_private_type_and_symlink(self):
        self.pipe.chmod(0o644)
        with self.assertRaises(oap.ProtocolError): oap.fifo_stat(self.pipe)
        self.pipe.chmod(0o600); link=self.root/'linked'; link.symlink_to(self.pipe)
        with self.assertRaises(oap.ProtocolError): oap.fifo_stat(link)
    def test_single_consumer_lock(self):
        path=self.root/'reader.lock'
        with oap.lock(path):
            with self.assertRaises(oap.ProtocolError):
                with oap.lock(path): pass
        with oap.lock(path): pass
    def test_writer_closes_descriptor_and_sends_exact_payload(self):
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future=pool.submit(oap.fifo_read,self.pipe,1)
            oap.fifo_write(self.pipe,1)
            self.assertEqual(future.result(timeout=2),b'OK')


class MaterializerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='oap-install-fixture-'); self.base=Path(self.temp.name)
        self.package=self.base/'package'; self.repo=self.base/'repo with spaces'; self.home=self.base/'stratégie'
        for root in (self.package,self.repo,self.home): root.mkdir()
        (self.package/'repo').mkdir(); (self.package/'strategic').mkdir()
        (self.package/'repo/ARCHITECTURE.md').write_text('fixture architecture\n')
        (self.package/'repo/CRITICAL.md').write_text('fixture register\n')
        (self.package/'strategic/runtime.json').write_text('{"activation_enabled":false}\n')
        self.manifest={'files':{str(p.relative_to(self.package)):oap.digest(p.read_bytes()) for p in self.package.rglob('*') if p.is_file()},'strategic_links':{'ARCHITECTURE.md':'ARCHITECTURE.md'},'initial_replace':{}}
        self.save()
    def save(self): (self.package/'PACKAGE-MANIFEST.json').write_text(json.dumps(self.manifest))
    def tearDown(self): self.temp.cleanup()
    def test_dry_install_identical_rerun_and_inactivity(self):
        before=inventory(self.base)
        materialize.install(self.package,self.repo,self.home)
        self.assertEqual(inventory(self.base),before)
        materialize.install(self.package,self.repo,self.home,False)
        installed=inventory(self.base)
        materialize.install(self.package,self.repo,self.home,False)
        self.assertEqual(inventory(self.base),installed)
        self.assertFalse((self.repo/'oap/active').exists())
        self.assertEqual((self.home/'control.fifo').stat().st_mode&0o777,0o600)
    def test_preserve_live_register_and_private_runtime(self):
        materialize.install(self.package,self.repo,self.home,False)
        (self.repo/'CRITICAL.md').write_text('real history\n'); (self.home/'runtime.json').write_text('private configuration\n')
        materialize.install(self.package,self.repo,self.home,False)
        self.assertEqual((self.repo/'CRITICAL.md').read_text(),'real history\n')
        self.assertEqual((self.home/'runtime.json').read_text(),'private configuration\n')
    def test_conflict_symlink_and_nested_roots_refused(self):
        (self.repo/'ARCHITECTURE.md').write_text('unrelated work\n')
        with self.assertRaises(oap.ProtocolError): materialize.install(self.package,self.repo,self.home,False)
        (self.repo/'ARCHITECTURE.md').unlink(); (self.repo/'ARCHITECTURE.md').symlink_to(self.base/'elsewhere')
        with self.assertRaises(oap.ProtocolError): materialize.install(self.package,self.repo,self.home,False)
        with self.assertRaises(oap.ProtocolError): materialize.install(self.package,self.package/'repo',self.home,False)
    def test_scoped_refresh_backup(self):
        materialize.install(self.package,self.repo,self.home,False)
        (self.package/'repo/ARCHITECTURE.md').write_text('new reviewed architecture\n')
        self.manifest['files']['repo/ARCHITECTURE.md']=oap.digest((self.package/'repo/ARCHITECTURE.md').read_bytes()); self.save()
        with self.assertRaises(oap.ProtocolError): materialize.install(self.package,self.repo,self.home,False)
        materialize.install(self.package,self.repo,self.home,False,('repo/ARCHITECTURE.md',))
        self.assertEqual((self.repo/'ARCHITECTURE.md').read_text(),'new reviewed architecture\n')
        backups=list((self.home/'bootstrap-backups').rglob('ARCHITECTURE.md'))
        self.assertEqual(len(backups),1); self.assertEqual(backups[0].read_text(),'fixture architecture\n')

if __name__=='__main__': unittest.main()

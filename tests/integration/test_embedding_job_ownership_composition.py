import select
import subprocess
import sys

from slaif_raggedized_helper.embedding_job_ownership import claim

JOB = 'sha256:' + 'a' * 64
CODE = '''
import sys
from slaif_raggedized_helper.embedding_job_ownership import claim, OwnershipRefused
try:
    with claim(sys.argv[1], sys.argv[2]):
        print("owned", flush=True)
        if len(sys.argv) > 3:
            input()
except OwnershipRefused:
    print("busy", flush=True)
'''


def test_process_ownership(tmp_path):
    def run(job):
        return subprocess.run([sys.executable, '-c', CODE, str(tmp_path), job],
                              capture_output=True, text=True, timeout=5, check=True).stdout.strip()

    holder = subprocess.Popen([sys.executable, '-c', CODE, str(tmp_path), JOB, 'hold'],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                              close_fds=True)
    try:
        assert select.select([holder.stdout], [], [], 5)[0]
        assert holder.stdout.readline().strip() == 'owned'
        path = tmp_path / 'embedding_job_locks' / JOB[7:]
        inode = path.stat().st_ino
        assert run(JOB) == 'busy'
        assert run('sha256:' + 'b' * 64) == 'owned'
        holder.terminate()
        holder.wait(timeout=5)
        assert run(JOB) == 'owned'
        assert path.stat().st_ino == inode
        with claim(tmp_path, JOB) as lease:
            lease.assert_owned()
    finally:
        if holder.poll() is None:
            holder.kill()
            holder.wait(timeout=5)
        holder.stdin.close()
        holder.stdout.close()

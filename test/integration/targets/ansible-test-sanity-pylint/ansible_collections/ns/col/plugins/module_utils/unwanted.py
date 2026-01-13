from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    os.popen('echo')
    os.posix_spawn('echo', ['echo'], {})
    os.posix_spawnp('echo', ['echo'], {})
    os.spawnl(os.P_WAIT, 'echo', 'echo')
    os.spawnle(os.P_WAIT, 'echo', 'echo', {})
    os.spawnlp(os.P_WAIT, 'echo', 'echo')
    os.spawnlpe(os.P_WAIT, 'echo', 'echo', {})
    os.spawnv(os.P_WAIT, 'echo', ['echo'])
    os.spawnve(os.P_WAIT, 'echo', ['echo'], {})
    os.spawnvp(os.P_WAIT, 'echo', ['echo'])
    os.spawnvpe(os.P_WAIT, 'echo', ['echo'], {})
    os.system('echo')

    subprocess.Popen('echo')
    subprocess.call('echo')
    subprocess.check_call('echo')
    subprocess.check_output('echo')
    subprocess.getoutput('echo')
    subprocess.getstatusoutput('echo')
    subprocess.run('echo', check=True)

    print()
    sys.exit(0)

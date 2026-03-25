#!/usr/bin/python

from __future__ import annotations

import subprocess
import sys
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.embed import EmbedManager
from ansible.module_utils.common.respawn import get_env_with_pythonpath, probe_interpreters_for_module

embed = EmbedManager.embed('..module_utils._embed', 'create_repo.py')


def main():
    module = AnsibleModule(
        argument_spec={
            'tempdir': {'type': 'path'},
        }
    )

    interpreters = [sys.executable, '/usr/libexec/platform-python', '/usr/bin/python3', '/usr/bin/python']

    interpreter = probe_interpreters_for_module(interpreters, module_names=['rpmfluff'])
    if not interpreter:
        module.fail_json('unable to find rpmfluff; tried {0}'.format(interpreters))

    tempdir = module.params['tempdir']

    # Save current temp dir so we can set it back later
    original_tempdir = tempfile.tempdir
    tempfile.tempdir = tempdir

    try:
        repo_dir = subprocess.check_output(
            [
                interpreter,
                '-m',
                embed.python_module_ref,
                tempdir,
            ],
            env=get_env_with_pythonpath(),
            stderr=subprocess.STDOUT,
            universal_newlines=True
        ).strip()
    except subprocess.CalledProcessError as e:
        module.fail_json(msg=e.stdout)
    finally:
        tempfile.tempdir = original_tempdir

    module.exit_json(repo_dir=repo_dir, tmpfile=tempfile.gettempdir())


if __name__ == "__main__":
    main()

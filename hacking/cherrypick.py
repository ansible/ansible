#!/usr/bin/env python3

import os
import sh
import sys
import tempfile

REPO_PATH = {
    'extras': '/srv/ansible/stable-2.2/lib/ansible/modules/extras',
    'core': '/srv/ansible/stable-2.2/lib/ansible/modules/core'
}


if __name__ == '__main__':
    commit_hash = sys.argv[1]
    which_modules = sys.argv[2]
    git = sh.git.bake('--no-pager', _tty_out=False)
    try:
        # Get the change
        git('checkout', 'devel')
        patch = git('format-patch', '-1', '--stdout', commit_hash).stdout
    finally:
        git('checkout', '-')

    # Transform the change for the new repo
    patch = patch.replace(b'lib/ansible/modules/', b'')
    new_patch = []
    patch_stream = (l for l in patch.split(b'\n'))
    for line in patch_stream:
        if line.strip() == b'---':
            new_patch.append(b'(cherry picked from %s)' % commit_hash.encode('utf-8'))
            new_patch.append(line)
            break
        new_patch.append(line)
    new_patch.extend(list(patch_stream))

    # Save the patch
    try:
        fh, patchfilename = tempfile.mkstemp()
        os.write(fh, b'\n'.join(new_patch))
        os.close(fh)

        # Apply the patch
        try:
            orig_dir = os.getcwd()
            os.chdir(REPO_PATH[which_modules])
            git('am', patchfilename)
        finally:
            os.chdir(orig_dir)
    except:
        print("Problem occurred.  Patch saved in: {0}".format(patchfilename))
    else:
        os.remove(patchfilename)

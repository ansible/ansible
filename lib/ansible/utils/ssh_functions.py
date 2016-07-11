#!/usr/bin/env python

import subprocess

from ansible import constants as C
from ansible.module_utils._text import to_text

def check_for_controlpersist():
    has_cp = True
    try:
        cmd = subprocess.Popen([C.ANSIBLE_SSH_EXECUTABLE,'-o','ControlPersist'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = cmd.communicate()
        err = to_text(err)
        if u"Bad configuration option" in err or u"Usage:" in err:
            has_cp = False
    except OSError:
        has_cp = False
    return has_cp


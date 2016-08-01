#!/usr/bin/env python

import subprocess
from ansible.utils.unicode import to_unicode

def check_for_controlpersist():
    has_cp = True
    try:
        cmd = subprocess.Popen(['ssh','-o','ControlPersist'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = cmd.communicate()
        err = to_unicode(err)
        if u"Bad configuration option" in err or u"Usage:" in err:
            has_cp = False
    except OSError:
        has_cp = False
    return has_cp


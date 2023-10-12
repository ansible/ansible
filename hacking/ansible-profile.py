#!/usr/bin/env python
from __future__ import annotations

import cProfile
import sys
import traceback

from ansible.module_utils.common.text.converters import to_text

target = sys.argv.pop(1)
myclass = "%sCLI" % target.capitalize()
module_name = f'ansible.cli.{target}'

try:
    # define cli
    mycli = getattr(__import__(module_name, fromlist=[myclass]), myclass)
except ImportError as e:
    if module_name in e.msg:
        raise Exception("Ansible sub-program not implemented: %s" % target) from None
    else:
        raise

try:
    args = [to_text(a, errors='surrogate_or_strict') for a in sys.argv]
except UnicodeError:
    sys.stderr.write(u"The full traceback was:\n\n%s" % to_text(traceback.format_exc()))
    sys.exit(u'Command line args are parsable to utf-8')

# init cli
cli = mycli(args)

print(cli.__class__.version_info(gitinfo=True))

# parse args
cli.parse()

# run
cProfile.run('cli.run()')

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import traceback

from ansible.errors import AnsibleError, AnsibleOptionsError, AnsibleParserError
from ansible.utils.display import Display
from ansible.utils.unicode import to_unicode

########################################
### OUTPUT OF LAST RESORT ###
class LastResort(object):
    def display(self, msg):
        print(msg, file=sys.stderr)

    def error(self, msg, wrap_text=None):
        print(msg, file=sys.stderr)


def handle_exception(cli, display):
    try:
        raise
    except AnsibleOptionsError as e:
        cli.parser.print_help()
        display.error(to_unicode(e), wrap_text=False)
        sys.exit(5)
    except AnsibleParserError as e:
        display.error(to_unicode(e), wrap_text=False)
        sys.exit(4)
# TQM takes care of these, but leaving comment to reserve the exit codes
#    except AnsibleHostUnreachable as e:
#        display.error(str(e))
#        sys.exit(3)
#    except AnsibleHostFailed as e:
#        display.error(str(e))
#        sys.exit(2)
    except AnsibleError as e:
        display.error(to_unicode(e), wrap_text=False)
        sys.exit(1)
    except KeyboardInterrupt:
        display.error("User interrupted execution")
        sys.exit(99)
    except Exception as e:
        have_cli_options = cli is not None and cli.options is not None
        display.error("Unexpected Exception: %s" % to_unicode(e), wrap_text=False)
        if not have_cli_options or have_cli_options and cli.options.verbosity > 2:
            display.display("the full traceback was:\n\n%s" % traceback.format_exc())
        else:
            display.display("to see the full traceback, use -vvv")
        sys.exit(250)
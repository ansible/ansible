from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

##
## Handle module invocation (i.e. python -m)
##

if len(sys.argv) > 1:
	# Read the subcommand
	sub = sys.argv[1]
	
	# Shift the args so that command line parsing
	# should work identically.
	sys.argv = sys.argv[1:]
	
	if sub == 'playbook':
		from .cli import playbook
		playbook.entry_point()
	elif sub == 'pull':
		from .cli import pull
		pull.entry_point()
	elif sub == 'doc':
		from .cli import doc
		doc.entry_point()
	elif sub == 'galaxy':
		from .cli import galaxy
		galaxy.entry_point()
	elif sub == 'vault':
		from .cli import vault
		vault.entry_point()
else:
	from .cli import adhoc
	adhoc.entry_point()

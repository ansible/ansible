#!/usr/bin/env python

import sys
sys.stdout.write('ansible\n')
sys.stderr.write('This is output to stderr that should be ignored.\n')
sys.exit(0)

#!/usr/bin/env python

import configparser
import sys


ini_file = sys.argv[1]
print(ini_file)
c = configparser.ConfigParser(strict=True, inline_comment_prefixes=(';',))
c.read_file(open(ini_file))

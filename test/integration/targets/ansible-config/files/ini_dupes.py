#!/usr/bin/env python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import configparser
import sys


ini_file = sys.argv[1]
c = configparser.ConfigParser(strict=True, inline_comment_prefixes=(';',))
c.read_file(open(ini_file))

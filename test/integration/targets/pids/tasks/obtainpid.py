#!/usr/bin/python
import sys
import psutil
names = set(sys.argv[1:])
print([int(p.info['pid']) for p in psutil.process_iter(attrs=['pid', 'name']) if names in p.info['name']])

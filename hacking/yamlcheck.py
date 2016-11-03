#!/usr/bin/env python
# long version of this one liner: python -c 'import yaml,sys;yaml.safe_load(sys.stdin)' < yamltest.txt
import yaml
import sys

if len(sys.argv) > 1:
    check_file = open(sys.argv[1])
else:
    check_file = sys.stdin

try:
    yaml.safe_load(check_file)
except yaml.scanner.ScannerError as e:
    sys.exit('Invalid YAML:\n%s' % str(e))

print('valid YAML')

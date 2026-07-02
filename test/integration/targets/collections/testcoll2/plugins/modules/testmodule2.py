#!/usr/bin/python
from __future__ import annotations

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = """
---
module: testmodule2
short_description: Test module
description:
    - Test module
author:
    - Ansible Core Team
"""

EXAMPLES = """
"""

RETURN = """
"""

import json


def main():
    print(json.dumps(dict(changed=False, source='sys')))


if __name__ == '__main__':
    main()

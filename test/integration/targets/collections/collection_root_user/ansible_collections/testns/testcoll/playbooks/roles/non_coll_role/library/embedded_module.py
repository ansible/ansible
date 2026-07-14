#!/usr/bin/python
from __future__ import annotations

import json


def main():
    print(json.dumps(dict(changed=False, source='collection_embedded_non_collection_role')))


if __name__ == '__main__':
    main()

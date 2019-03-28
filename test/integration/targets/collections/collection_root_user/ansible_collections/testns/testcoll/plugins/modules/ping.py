#!/usr/bin/env python

import json


def main():
    print(json.dumps(dict(changed=False, source='user')))


if __name__ == '__main__':
    main()

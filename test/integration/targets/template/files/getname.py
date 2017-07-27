#!/usr/bin/env python

# get a random name from the passwd or groups file on a system

import random
import sys


def main():
    fn = sys.argv[1]
    with open(fn, 'rb') as f:
        lines = f.readlines()
    lines = [x.strip() for x in lines if x.strip()]
    lines = [x.decode('utf-8') for x in lines]
    lines = [x for x in lines if not x.startswith('#')]
    lines = [x for x in lines if not x.startswith('_')]
    names = [x.split(':')[0] for x in lines]
    names = [x for x in names if x != 'root']
    sys.stdout.write(random.choice(names))


if __name__ == "__main__":
    main()

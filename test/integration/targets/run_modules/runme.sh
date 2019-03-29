#!/usr/bin/env bash

set -eux

# test running module directly
python.py library/test.py args.json

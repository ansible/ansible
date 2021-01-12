#!/usr/bin/env bash

set -eux

diff -uw <(ansible-inventory -i inventory.sh --list --export) inventory.json

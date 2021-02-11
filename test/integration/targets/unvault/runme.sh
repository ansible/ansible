#!/usr/bin/env bash

set -eux


ansible-playbook --vault-password-file password main.yml

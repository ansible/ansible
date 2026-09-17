#!/usr/bin/env python
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import sys

import pexpect

CONN_PASSWORD = "ConnectionPasswordSecret"
BECOME_PASSWORD = "BecomePasswordSecret"

out = pexpect.run(
    "ansible-playbook ask_pass.yml -i localhost, -c ssh -k -K",
    events={
        "SSH password:": f"{CONN_PASSWORD}\n",
        "BECOME password\\[defaults to SSH password\\]:": f"{BECOME_PASSWORD}\n",
    },
    timeout=10,
)

sys.stdout.buffer.write(out)

if CONN_PASSWORD.encode() in out:
    sys.exit("FAIL: prompted --ask-pass value leaked in plaintext output")

if b"ask_pass: $REDACTED$" not in out:
    sys.exit("FAIL: prompted --ask-pass value was not masked in debug output")

if BECOME_PASSWORD.encode() in out:
    sys.exit("FAIL: prompted --ask-become-pass value leaked in plaintext output")

if b"ask_become_pass: $REDACTED$" not in out:
    sys.exit("FAIL: prompted --ask-become-pass value was not masked in debug output")

print("ask-pass masking scenario passed")

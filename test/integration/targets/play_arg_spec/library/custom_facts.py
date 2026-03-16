#!/usr/bin/python
from __future__ import annotations
import json
print(json.dumps({"ansible_facts": {"custom_fact": "required"}}))

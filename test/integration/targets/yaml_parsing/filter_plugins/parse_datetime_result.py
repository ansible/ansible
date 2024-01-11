# Copyright: (c) 2024, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json


def parse_datetime_result(value):
    res_split = value.split("ok: [localhost] => ")[1]
    raw_result = res_split.split("PLAY RECAP")[0]

    return json.loads(raw_result)["parse_result"]


def parse_datetime_warnings(value):
    warnings = []
    buffer = []
    start_capture = False

    for line in value.split("\n"):
        if not start_capture:
            if line.startswith("[DEPRECATION WARNING]: "):
                start_capture = True
                line = line[23:]
            else:
                continue

        elif line.startswith("[DEPRECATION WARNING]: "):
            warnings.append("".join(buffer).strip())
            buffer = []
            line = line[23:]

        buffer.append(line)

    if buffer:
        warnings.append("".join(buffer).strip())

    return warnings


class FilterModule:

    def filters(self):
        return {
            'parse_datetime_result': parse_datetime_result,
            'parse_datetime_warnings': parse_datetime_warnings,
        }

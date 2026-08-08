"""Developer helper tool for generating various broken vault-encrypted strings."""
# pragma: nocover

from __future__ import annotations

import base64
import json
import pathlib

from ansible.parsing.vault import format_vaulttext_envelope

method_name = 'v2c'


def main() -> None:
    with (pathlib.Path(__file__).parent / f'{method_name}/secret1_data1.ciphertext').open('rb') as f:
        next(f)
        raw = f.read()

    json_orig = base64.b64decode(raw)
    dict_orig = json.loads(json_orig)

    dict_orig['bogus_key'] = "nope"
    # dict_orig.pop('salt')

    raw_out = format_vaulttext_envelope(base64.b64encode(json.dumps(dict_orig).encode()), method_name).decode()
    print(raw_out)


if __name__ == '__main__':
    main()

from __future__ import annotations

import importlib.resources

import pytest

from ansible.parsing.vault import methods, VaultLib, VaultSecret, parse_vaulttext_envelope

from . import decrypt_test_data


def get_method_names() -> list[str]:
    with importlib.resources.as_file(importlib.resources.files(methods)) as path:
        # this is roughly pkgutil.iter_modules, but ...
        return [modname.with_suffix("").name for modname in path.glob("*.py") if not modname.name.startswith("__")]


def get_decrypt_test_scenarios(method_names: list[str]) -> list[tuple[str, str]]:
    params = []
    for method_name in method_names:
        with importlib.resources.as_file(importlib.resources.files(decrypt_test_data).joinpath(method_name)) as path:
            if not (scenarios := list(path.glob('*.ciphertext'))):  # pragma: nocover
                params.append((method_name, "MISSING"))
            for scenario in scenarios:
                params.append((method_name, scenario.with_suffix('').name))

    return params


@pytest.mark.parametrize("method_name, scenario", get_decrypt_test_scenarios(get_method_names()))
def test_fixed_decrypt(method_name: str, scenario: str) -> None:
    with importlib.resources.as_file(importlib.resources.files(decrypt_test_data).joinpath(method_name)) as path:
        ciphertext_path = path.joinpath(scenario).with_suffix('.ciphertext')
        plaintext_path = path.joinpath(scenario).with_suffix('.plaintext')
        secret_path = ciphertext_path.with_name(ciphertext_path.name.split('_', 1)[0])
        assert ciphertext_path.exists()
        assert plaintext_path.exists()
        assert secret_path.exists()
        # FIXME: expose static methods on VaultLib to make this suck less
        assert parse_vaulttext_envelope(ciphertext_path.read_bytes())[2] == method_name.upper()

        vault = VaultLib(secrets=[('default', VaultSecret(secret_path.read_bytes()))])
        assert vault.decrypt(ciphertext_path.read_bytes(), ciphertext_path.absolute()) == plaintext_path.read_bytes()

from __future__ import annotations

import json

import pytest

from ansible.module_utils._internal import _ahocorasick, _secrets

try:
    import ahocorasick as c_extension
except ImportError:
    c_extension = None

# Corpus contract: each case registers its secrets, masks its input, and must produce exactly
# the expected output. Short secrets (4-6 chars) are masked only at a word boundary.
CORPUS = "test/integration/targets/module_utils_Ansible.Secrets/files/secret_masking_corpus.json"

with open(CORPUS) as _fh:
    _CORPUS = json.load(_fh)

SENTINEL = _CORPUS["sentinel"]
CASES = _CORPUS["cases"]

# The masker must behave identically on both backends: pure-Python fallback and C extension.
BACKENDS = [pytest.param(_ahocorasick, id="pure_python")]
if c_extension is not None:
    BACKENDS.append(pytest.param(c_extension, id="c_extension"))


@pytest.fixture(params=BACKENDS)
def masker(request, monkeypatch):
    """A fresh SecretMasker bound to each backend in turn."""
    monkeypatch.setattr(_secrets, "ahocorasick", request.param)
    return _secrets.SecretMasker()


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_masking_contract(masker, case):
    """Each case: registering its secrets and masking its input yields exactly the expected output."""
    for secret in case["secrets"]:
        masker.register_secret_text(secret)
    masked = masker.mask_string(case["input"], mask_placeholder=SENTINEL)
    assert masked == case["expected"]


def test_register_secret_text_is_idempotent(masker):
    """Registering the same secret twice tracks it once (duplicate add is a no-op)."""
    tracker = masker.track_new_secrets()
    masker.register_secret_text("password123")
    masker.register_secret_text("password123")
    assert tracker.flush() == frozenset({"password123"})


def test_short_secrets_are_not_registered(masker):
    """Secrets shorter than the minimum length are silently skipped, so they pass through unmasked."""
    short = "a" * (_secrets._MINIMUM_SECRET_LENGTH - 1)
    masker.register_secret_text(short)
    text = f"XX{short}XX"
    assert masker.mask_string(text, mask_placeholder=SENTINEL) == text


def test_secrets_in_reports_registered_secrets(masker):
    """secrets_in returns exactly the registered secrets found in the value."""
    masker.register_secret_text("alpha")
    masker.register_secret_text("bravo")
    assert masker.secrets_in("XXalphaYYbravoZZ") == frozenset({"alpha", "bravo"})

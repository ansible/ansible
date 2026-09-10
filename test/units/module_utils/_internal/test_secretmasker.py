from __future__ import annotations

import json

import pytest

from ansible.module_utils._internal import _secrets

# Corpus contract: each case registers its secrets, masks its input, and must produce exactly
# the expected output. Short secrets (4-6 chars) are masked only at a word boundary. The same
# corpus drives the C# (Ansible.Secrets.cs) conformance test.
CORPUS = "test/integration/targets/module_utils_Ansible.Secrets/files/secret_masking_corpus.json"

with open(CORPUS) as _fh:
    _CORPUS = json.load(_fh)

SENTINEL = _CORPUS["sentinel"]
CASES = _CORPUS["cases"]


@pytest.fixture
def masker():
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


def test_register_secret_text_returns_the_value_unchanged(masker):
    """register_secret_text is a pass-through: it returns what it was given, registered or not."""
    assert masker.register_secret_text("password123") == "password123"
    assert masker.register_secret_text("abc") == "abc"


def test_flush_clears_state_second_flush_is_empty(masker):
    """flush() drains the collected secrets, so a second flush with nothing new returns empty."""
    tracker = masker.track_new_secrets()
    masker.register_secret_text("password123")

    assert tracker.flush() == frozenset({"password123"})
    assert tracker.flush() == frozenset()


def test_mask_string_no_registered_secrets_returns_value_unchanged(masker):
    assert masker.mask_string("nothing registered") == "nothing registered"


def test_mask_string_default_placeholder(masker):
    masker.register_secret_text("password123")
    assert masker.mask_string("x password123 y") == "x $REDACTED$ y"


def test_mask_string_custom_placeholder_can_be_empty(masker):
    masker.register_secret_text("password123")
    assert masker.mask_string("x password123 y", mask_placeholder="") == "x  y"


def test_register_secret_texts_bulk_registers_and_masks(masker):
    """The bulk path registers every eligible secret in the batch so each is masked."""
    masker.register_secret_texts(["alpha_secret", "bravo_secret"])
    masked = masker.mask_string("XXalpha_secretYYbravo_secretZZ", mask_placeholder=SENTINEL)
    assert masked == f"XX{SENTINEL}YY{SENTINEL}ZZ"


def test_register_secret_texts_deduplicates(masker):
    """The bulk path tracks each new secret once, skipping duplicates and already-registered ones."""
    masker.register_secret_text("alpha_secret")

    tracker = masker.track_new_secrets()
    # alpha_secret already exists (skipped); bravo_secret is new but appears twice (tracked once).
    masker.register_secret_texts(["alpha_secret", "bravo_secret", "bravo_secret"])

    assert tracker.flush() == frozenset({"bravo_secret"})


def test_register_secret_texts_skips_short_secrets(masker):
    """Secrets shorter than the minimum length are skipped by the bulk path too."""
    short = "a" * (_secrets._MINIMUM_SECRET_LENGTH - 1)

    tracker = masker.track_new_secrets()
    masker.register_secret_texts([short, "long_enough_secret"])

    assert tracker.flush() == frozenset({"long_enough_secret"})


def test_register_secret_texts_accepts_any_iterable(masker):
    masker.register_secret_texts(s for s in ("alpha_secret", "bravo_secret"))
    assert masker.mask_string("alpha_secret bravo_secret", mask_placeholder=SENTINEL) == f"{SENTINEL} {SENTINEL}"


def test_register_secret_texts_leaves_gc_state_as_found(masker):
    """Bulk registration pauses the cyclic GC while building and restores the caller's setting either way."""
    import gc

    assert gc.isenabled()
    masker.register_secret_texts(["alpha_secret"])
    assert gc.isenabled()

    gc.disable()
    try:
        masker.register_secret_texts(["bravo_secret"])
        assert not gc.isenabled()
    finally:
        gc.enable()


def test_unregister_stops_tracking_new_secrets(masker):
    """After unregister a tracker keeps what it already collected but records nothing new."""
    tracker = masker.track_new_secrets()
    masker.register_secret_text("alpha_secret")

    tracker.unregister()
    masker.register_secret_text("bravo_secret")

    # alpha_secret was collected before unregister; bravo_secret, registered after, is not.
    assert tracker.flush() == frozenset({"alpha_secret"})


def test_unregister_is_idempotent(masker):
    """Unregistering a tracker twice is safe (a no-op the second time)."""
    tracker = masker.track_new_secrets()
    tracker.unregister()
    tracker.unregister()


def test_multiple_trackers_each_see_new_secrets(masker):
    """Every active tracker collects every new secret registered while it is active."""
    first = masker.track_new_secrets()
    masker.register_secret_text("alpha_secret")
    second = masker.track_new_secrets()
    masker.register_secret_text("bravo_secret")

    assert first.flush() == frozenset({"alpha_secret", "bravo_secret"})
    assert second.flush() == frozenset({"bravo_secret"})


def test_tracker_records_trimmed_secret(masker):
    """Trackers carry what was registered: the trimmed value, not the oversized input."""
    secret = "S" * (_secrets._MAXIMUM_SECRET_LENGTH + 5)
    tracker = masker.track_new_secrets()
    masker.register_secret_text(secret)
    assert tracker.flush() == frozenset({secret[:_secrets._MAXIMUM_SECRET_LENGTH]})


def test_tracker_records_stripped_secret(masker):
    """Surrounding whitespace is stripped before registration; the caller still gets the value unchanged."""
    tracker = masker.track_new_secrets()
    assert masker.register_secret_text(" \tsecret-value\r\n") == " \tsecret-value\r\n"
    assert tracker.flush() == frozenset({"secret-value"})


def test_whitespace_only_or_padded_short_secrets_are_not_registered(masker):
    """The minimum length applies after stripping."""
    tracker = masker.track_new_secrets()
    masker.register_secret_texts(["    ", "\n\n\n\n", " ab ", "\tabc\n"])
    assert tracker.flush() == frozenset()
    assert masker.mask_string("    ab abc", mask_placeholder=SENTINEL) == "    ab abc"


def test_only_the_secret_itself_is_tracked_as_new(masker):
    """Derived forms (JSON escapes) are re-derived by receivers, so trackers carry only the secret."""
    tracker = masker.track_new_secrets()
    masker.register_secret_text('test"secret')
    assert tracker.flush() == frozenset({'test"secret'})


def test_oversized_secrets_sharing_the_trimmed_prefix_are_one_secret(masker):
    """Two inputs that differ only beyond the cap trim to the same secret and are tracked once."""
    base = "".join(chr(0x21 + i % 90) for i in range(_secrets._MAXIMUM_SECRET_LENGTH))
    tracker = masker.track_new_secrets()
    masker.register_secret_texts([base + "AAA", base + "BBB"])
    assert tracker.flush() == frozenset({base})


def test_registering_a_secret_does_not_rebuild_previous_state(masker):
    """Interleaving registration and masking keeps every earlier secret masked (lazy links stay correct)."""
    secrets = [f"secret{i:04d}xyz" for i in range(50)]
    for index, secret in enumerate(secrets):
        masker.register_secret_text(secret)
        text = " ".join(secrets[: index + 1])
        assert masker.mask_string(text, mask_placeholder=SENTINEL) == " ".join([SENTINEL] * (index + 1))


def test_registering_a_secret_that_changes_an_existing_fail_link(masker):
    """A new secret can become a better fail target for existing automaton states; results must follow."""
    masker.register_secret_text("abcdefgh-one")  # states a..abcdefgh exist
    assert masker.mask_string("xabcdefgh-two bcdefgh-two", mask_placeholder=SENTINEL) == "xabcdefgh-two bcdefgh-two"
    masker.register_secret_text("bcdefgh-two")  # suffix of the failed path of the first secret
    assert masker.mask_string("xabcdefgh-two bcdefgh-two", mask_placeholder=SENTINEL) == f"xa{SENTINEL} {SENTINEL}"


def test_secrets_in_json_reports_registered_secrets(masker):
    """secrets_in_json returns exactly the registered secrets found in the value."""
    masker.register_secret_text("alpha")
    masker.register_secret_text("bravo")
    assert masker.secrets_in_json("XXalphaYYbravoZZ") == frozenset({"alpha", "bravo"})


def test_secrets_in_json_empty_value_and_empty_registry(masker):
    assert masker.secrets_in_json("") == frozenset()
    assert masker.secrets_in_json('{"a": "b"}') == frozenset()
    masker.register_secret_text("alpha")
    assert masker.secrets_in_json("") == frozenset()


def test_secrets_in_json_ignores_the_boundary_rule(masker):
    """Detection reports short secrets even when glued to alphanumerics: the receiver may see them at a boundary."""
    masker.register_secret_text("pass")
    assert masker.mask_string("AAApassBBB", mask_placeholder=SENTINEL) == "AAApassBBB"
    assert masker.secrets_in_json("AAApassBBB") == frozenset({"pass"})


def test_secrets_in_json_reports_overlapping_secrets(masker):
    """Every overlapping occurrence is reported, unlike masking which merges them."""
    masker.register_secret_texts(["hunter2", "ter2foo123", "foo123-end"])
    assert masker.secrets_in_json("start-hunter2foo123-end") == frozenset({"hunter2", "ter2foo123", "foo123-end"})


def test_secrets_in_json_reports_secret_inside_another(masker):
    masker.register_secret_texts(["hunter2foo", "ter2f"])
    assert masker.secrets_in_json("hunter2foo") == frozenset({"hunter2foo", "ter2f"})


def test_secrets_in_json_returns_the_secret_not_its_escaped_form(masker):
    """A JSON-escaped occurrence is reported as the literal secret so a receiver can mask every form."""
    masker.register_secret_text('test"secret')
    params = json.dumps({"ANSIBLE_MODULE_ARGS": {"module_opt": 'test"secret'}})
    assert masker.secrets_in_json(params) == frozenset({'test"secret'})

    receiver = _secrets.SecretMasker()
    receiver.register_secret_texts(masker.secrets_in_json(params))
    assert receiver.mask_string('module_opt=test"secret', mask_placeholder=SENTINEL) == f"module_opt={SENTINEL}"
    assert receiver.mask_string(params, mask_placeholder=SENTINEL) == f'{{"ANSIBLE_MODULE_ARGS": {{"module_opt": "{SENTINEL}"}}}}'


@pytest.mark.parametrize("order", ["secret then its escaped form", "escaped form then secret"])
def test_a_secret_that_is_the_escaped_form_of_another(masker, order):
    """Registering both 'test"value' and 'test\\"value' keeps both as secrets whatever the order."""
    secrets = ['test"value', 'test\\"value']
    if order == "escaped form then secret":
        secrets.reverse()

    tracker = masker.track_new_secrets()
    for secret in secrets:
        masker.register_secret_text(secret)
    # both were new secrets, so both propagate
    assert tracker.flush() == frozenset(secrets)

    # every form is masked: the raw value, its escaped form, and the double-escaped form of the second secret
    for text in ('test"value', 'test\\"value', 'test\\\\\\"value'):
        assert masker.mask_string(f"x {text} y", mask_placeholder=SENTINEL) == f"x {SENTINEL} y"

    # in JSON a form denotes its decoded value: '"test\\"value"' is the first secret only, the second needs double escaping
    assert masker.secrets_in_json(json.dumps({"opt": 'test"value'})) == frozenset({'test"value'})
    assert masker.secrets_in_json(json.dumps({"opt": 'test\\"value'})) == frozenset({'test\\"value'})
    assert masker.secrets_in_json(json.dumps({"a": 'test"value', "b": 'test\\"value'})) == frozenset(secrets)


@pytest.mark.parametrize("ensure_ascii", [True, False], ids=["legacy profile (ensure_ascii)", "modern profile (utf-8)"])
def test_non_ascii_secret_is_found_in_either_json_encoding(masker, ensure_ascii):
    """Module args are encoded with or without ensure_ascii depending on the profile; both forms match and decode."""
    masker.register_secret_text("café-secret")
    text = json.dumps({"opt": "café-secret"}, ensure_ascii=ensure_ascii)
    assert masker.mask_string(text, mask_placeholder=SENTINEL) == f'{{"opt": "{SENTINEL}"}}'
    assert masker.secrets_in_json(text) == frozenset({"café-secret"})


def test_astral_and_surrogate_pair_secret(masker):
    """A secret with a non-BMP character is matched raw and in its \\uXXXX surrogate-pair JSON form."""
    masker.register_secret_text("key-🔐-secret")
    for text in (json.dumps({"k": "key-🔐-secret"}), json.dumps({"k": "key-🔐-secret"}, ensure_ascii=False)):
        assert masker.mask_string(text, mask_placeholder=SENTINEL) == f'{{"k": "{SENTINEL}"}}'
        assert masker.secrets_in_json(text) == frozenset({"key-🔐-secret"})


def test_control_character_secret_in_json(masker):
    masker.register_secret_text("line1\nline2")
    text = json.dumps({"k": "line1\nline2"})
    assert masker.mask_string(text, mask_placeholder=SENTINEL) == f'{{"k": "{SENTINEL}"}}'
    assert masker.secrets_in_json(text) == frozenset({"line1\nline2"})


def test_secrets_in_json_json_keys_are_scanned_too(masker):
    masker.register_secret_text('key"secret')
    assert masker.secrets_in_json(json.dumps({'key"secret': 1})) == frozenset({'key"secret'})


def test_secrets_in_json_literal_backslash_form_on_non_json_text(masker):
    """A registered secret containing a backslash matched as-is (outside JSON) is reported as itself."""
    masker.register_secret_text("dir\\path-secret")
    assert masker.secrets_in_json("dir\\path-secret appeared") == frozenset({"dir\\path-secret"})


def test_secrets_in_json_reports_trimmed_secret(masker):
    """An oversized secret is registered trimmed, so that is what detection reports."""
    secret = "".join(chr(0x21 + i % 90) for i in range(_secrets._MAXIMUM_SECRET_LENGTH + 10))
    masker.register_secret_text(secret)
    assert masker.secrets_in_json(json.dumps({"k": secret})) == frozenset({secret[:_secrets._MAXIMUM_SECRET_LENGTH]})


def test_round_trip_through_a_receiver_masks_every_form(masker):
    """Whatever the controller detects in encoded params lets a receiver mask raw, escaped and re-encoded values."""
    secrets = ['foo"bar', "dir\\path", "café", "tab\tsep", "plainsecret"]
    masker.register_secret_texts(secrets)
    for ensure_ascii in (True, False):
        params = json.dumps({"ANSIBLE_MODULE_ARGS": {f"opt{i}": s for i, s in enumerate(secrets)}}, ensure_ascii=ensure_ascii)
        found = masker.secrets_in_json(params)
        assert found == frozenset(secrets)
        receiver = _secrets.SecretMasker()
        receiver.register_secret_texts(found)
        for secret in secrets:
            assert receiver.mask_string(f"opt={secret}", mask_placeholder=SENTINEL) == f"opt={SENTINEL}"
        assert SENTINEL in receiver.mask_string(params, mask_placeholder=SENTINEL)
        for secret in secrets:
            assert secret not in receiver.mask_string(params, mask_placeholder=SENTINEL)

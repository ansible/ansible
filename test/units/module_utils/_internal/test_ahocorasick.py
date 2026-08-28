from __future__ import annotations

import json

import pytest

from ansible.module_utils._internal import _ahocorasick as pure_python

try:
    import ahocorasick as c_extension
except ImportError:
    c_extension = None

# iter_long differential cases: curated names + a deterministic (seed=1729) sample
# over alphabet 'abc', with expected output generated from the pyahocorasick C
# extension. Pure-Python and C agree on all length>=2 word sets.
CONFORMANCE_FIXTURE = "test/units/module_utils/_internal/fixtures/ahocorasick_conformance.json"

with open(CONFORMANCE_FIXTURE) as _fh:
    CONFORMANCE = json.load(_fh)["cases"]

# Implementations that must agree on the shared behaviors below.
IMPLEMENTATIONS = [pytest.param(pure_python, id="pure_python")]
if c_extension is not None:
    IMPLEMENTATIONS.append(pytest.param(c_extension, id="c_extension"))


@pytest.mark.parametrize("module", IMPLEMENTATIONS)
def test_add_word_return_value(module):
    """add_word returns True for a newly added word and False for a duplicate."""
    automaton = module.Automaton()
    assert automaton.add_word("secret", 6) is True
    assert automaton.add_word("secret", 6) is False
    assert automaton.add_word("other", 5) is True


@pytest.mark.parametrize("module", IMPLEMENTATIONS)
def test_add_empty_word_is_noop(module):
    """Adding an empty string is a no-op that returns False."""
    assert module.Automaton().add_word("", 0) is False


def _matches(module, words, text):
    """Build an automaton from ``words`` (word -> value) and return iter_long matches."""
    automaton = module.Automaton()
    for word, value in words.items():
        automaton.add_word(word, value)
    automaton.make_automaton()
    return [list(match) for match in automaton.iter_long(text)]


@pytest.mark.parametrize("module", IMPLEMENTATIONS)
@pytest.mark.parametrize("case", CONFORMANCE, ids=[c["name"] for c in CONFORMANCE])
def test_matches_reference(module, case):
    """Each backend reproduces the reference output (generated from the C extension)."""
    assert _matches(module, case["words"], case["input"]) == case["expected"]

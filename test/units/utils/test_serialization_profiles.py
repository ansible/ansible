# DTFIX-MERGE: these tests need to be split so they can run under both module_utils and controller contexts

from __future__ import annotations

import contextlib
import dataclasses
import datetime
import itertools
import json
import pathlib
import pkgutil
import pprint
import typing as t

import pytest

from ansible.module_utils import serialization as target_serialization
from ansible.module_utils._internal import _serialization
from ansible.module_utils.datatag import AnsibleDatatagBase, NotTaggableError, AnsibleTagHelper
from ansible.module_utils.datatag.tags import Deprecated
from ansible._internal._templating._lazy_containers import _AnsibleLazyTemplateMixin
from ansible._internal._templating._engine import TemplateEngine, TemplateOptions
from ansible._internal._templating._utils import TemplateContext
from ansible.utils.datatag.tags import TrustedAsTemplate
from ansible.module_utils.serialization import get_encoder, get_decoder, fallback_to_str
from ansible.utils import serialization as controller_serialization
from ansible.errors import AnsibleRuntimeError

from ..mock.custom_collections import CustomMapping, CustomSequence

basic_values = (
    None,
    True,
    1,
    1.1,
    'hi',
    '汉语',  # non-ASCII string
    b'hi',
    datetime.datetime(2024, 1, 2, 3, 4, 5, 6, datetime.timezone.utc, fold=1),
    datetime.time(1, 2, 3, 4, datetime.timezone.utc, fold=1),
    datetime.date(2024, 1, 2),
    (1,),
    [1],
    CustomSequence([1]),
    {1},
    dict(a=1),
    CustomMapping(dict(a=1)),
)

# DTFIX-MERGE: we need tests for recursion, specifically things like custom sequences and mappings when using the legacy serializer
#              e.g. -- does trust inversion get applied to a value inside a custom sequence or mapping

tag_values = {
    Deprecated: Deprecated(msg='x'),
    TrustedAsTemplate: TrustedAsTemplate(),
}


def get_profile_names() -> tuple[str, ...]:
    packages = (target_serialization, controller_serialization)
    names = []

    for package in packages:
        for module in pkgutil.iter_modules(package.__path__, f'{package.__name__}.'):
            names.append(_serialization.get_serialization_profile(module.name).profile_name)

    return tuple(sorted(names))


@dataclasses.dataclass(frozen=True)
class _TestParameters:
    profile_name: str
    value: t.Any
    tags: tuple[AnsibleDatatagBase, ...] = ()
    lazy: bool = False

    def __hash__(self):
        return hash((self.profile_name, repr(self.value), self.tags))

    def __repr__(self):
        fields = ((field, getattr(self, field.name)) for field in dataclasses.fields(self))
        args = (f'{f.name}={v!r}' for f, v in fields if v != f.default)
        return f"{type(self).__name__}({', '.join(args)})"

    def get_test_output(self) -> _TestOutput:
        encoder = get_encoder(self.profile_name)
        decoder = get_decoder(self.profile_name)

        ctx = TemplateContext(
            template_value=self.value,
            templar=TemplateEngine(),
            options=TemplateOptions.DEFAULT,
            stop_on_template=False
        ) if self.lazy else contextlib.nullcontext()

        with ctx:
            try:
                value = AnsibleTagHelper.tag(self.value, self.tags)
            except NotTaggableError:
                value = self.value

            if self.lazy:
                value = _AnsibleLazyTemplateMixin._try_create(value)

            payload: str | Exception

            try:
                payload = json.dumps(value, cls=encoder)
            except Exception as ex:
                payload = ex
                round_trip = None
            else:
                try:
                    round_trip = json.loads(payload, cls=decoder)
                except Exception as ex:
                    round_trip = ex

            return _TestOutput(
                payload=payload,
                round_trip=AnsibleTagHelper.as_native_type(round_trip),
                tags=tuple(AnsibleTagHelper.tags(round_trip)),
            )


@dataclasses.dataclass(frozen=True)
class _TestOutput:
    payload: str | Exception
    round_trip: t.Any
    tags: tuple[AnsibleDatatagBase, ...]


@dataclasses.dataclass(frozen=True)
class _TestCase:
    parameters: _TestParameters
    expected: _TestOutput

    def __str__(self) -> str:
        parts = [f'profile={self.parameters.profile_name}', f'value={self.parameters.value}']

        if self.parameters.tags:
            parts.append(f"tags={','.join(sorted(type(obj).__name__ for obj in self.parameters.tags))}")

        if self.parameters.lazy:
            parts.append('lazy')

        return '; '.join(parts)


class DataSet:
    def __init__(self, generate: bool) -> None:
        self.data: dict[_TestParameters, _TestOutput] = {}
        self.path = pathlib.Path(__file__).parent / 'expected_serialization_profiles'
        self.generate = generate

    def load(self) -> None:
        if self.generate:
            return

        for source in self.path.glob('*.txt'):
            self.data.update(eval(source.read_text()))

    def save(self) -> None:
        if not self.generate:
            return

        sorted_items = sorted(self.data.items(), key=lambda o: o[0].profile_name)  # additional items appended to the end means the data set is unsorted

        grouped_data_set = {key: dict(gen) for key, gen in itertools.groupby(sorted_items, key=lambda o: o[0].profile_name)}

        for group_name, profiles in grouped_data_set.items():
            content = pprint.pformat(profiles, width=1000, indent=0, sort_dicts=False)
            content = f'{{\n{content[1:-1]}\n}}\n'
            (self.path / f'{group_name}.txt').write_text(content)

    def fetch_or_create_expected(self, test_params: _TestParameters) -> _TestOutput:
        if self.generate:
            output = self.data[test_params] = test_params.get_test_output()
        else:
            try:
                output = self.data[test_params]
            except KeyError:
                raise Exception(f'Missing {test_params} in data set. Use `generate=True` to update the data set and then review the changes.') from None

        return output


class ProfileHelper:
    def __init__(self, profile_name: str) -> None:
        self.profile_name = profile_name

        profile = _serialization.get_serialization_profile(profile_name)

        supported_tags = set(obj for obj in profile.serialize_map if issubclass(obj, AnsibleDatatagBase))

        if supported_tags:
            self.supported_tag_values = tuple(tag_value for tag_type, tag_value in tag_values.items() if tag_type in supported_tags)

            if not self.supported_tag_values:
                raise Exception(f'Profile {profile} supports tags {supported_tags}, but no supported tag value is available.')
        else:
            self.supported_tag_values = tuple()

        unsupported_tag_values = [tag_value for tag_type, tag_value in tag_values.items() if tag_type not in supported_tags]

        if not unsupported_tag_values:
            raise Exception(f'Profile {profile} supports tags {supported_tags}, but no unsupported tag value is available.')

        self.unsupported_tag_value = unsupported_tag_values[0]

    def create_parameters_from_values(self, *values: t.Any) -> list[_TestParameters]:
        return list(itertools.chain.from_iterable(self.create_parameters_from_value(value) for value in values))

    def create_parameters_from_value(self, value: t.Any) -> list[_TestParameters]:
        test_parameters: list[_TestParameters] = [
            _TestParameters(
                profile_name=self.profile_name,
                value=value,
            )
        ]

        if self.supported_tag_values:
            test_parameters.append(_TestParameters(
                profile_name=self.profile_name,
                value=value,
                tags=self.supported_tag_values,
            ))

        test_parameters.append(_TestParameters(
            profile_name=self.profile_name,
            value=value,
            tags=(self.unsupported_tag_value,),
        ))

        # test lazy containers on all non m2c profiles
        if not self.profile_name.endswith("_m2c") and isinstance(value, (list, dict)):
            test_parameters.extend([dataclasses.replace(p, lazy=True) for p in test_parameters])

        return test_parameters


additional_test_parameters: list[_TestParameters] = []

# DTFIX-MERGE: need better testing for containers, especially for tagged values in containers

additional_test_parameters.extend(ProfileHelper(fallback_to_str._Profile.profile_name).create_parameters_from_values(
    b'\x00',  # valid utf-8 strict, JSON escape sequence required
    b'\x80',  # utf-8 strict decoding fails, forcing the use of an error handler such as surrogateescape, JSON escape sequence required
    '\udc80',  # same as above, but already a string (verify that the string version is handled the same as the bytes version)
    {1: "1"},  # integer key
    {b'hi': "1"},  # bytes key
    {TrustedAsTemplate().tag(b'hi'): "2"},  # tagged bytes key
    {(b'hi',): 3},  # tuple[bytes] key
))


_generate = False
"""Set to True to regenerate all test data; a test failure will occur until it is set back to False."""


def get_test_cases() -> list[_TestCase]:
    data_set = DataSet(generate=_generate)
    data_set.load()

    test_parameters: list[_TestParameters] = []

    for profile_name in get_profile_names():
        helper = ProfileHelper(profile_name)

        for value in basic_values:
            test_parameters.extend(helper.create_parameters_from_value(value))

    test_parameters.extend(additional_test_parameters)

    test_cases = [_TestCase(parameters=parameters, expected=data_set.fetch_or_create_expected(parameters)) for parameters in test_parameters]

    data_set.save()

    return test_cases


@pytest.mark.parametrize("test_case", get_test_cases(), ids=str)
def test_profile(test_case: _TestCase) -> None:
    output = test_case.parameters.get_test_output()

    if isinstance(output.payload, Exception):
        if type(output.payload) is not type(test_case.expected.payload):
            raise Exception('unexpected exception') from output.payload

        assert str(output.payload) == str(test_case.expected.payload)
    else:
        assert output.payload == test_case.expected.payload
        assert type(output.round_trip) is type(test_case.expected.round_trip)

        if isinstance(output.round_trip, AnsibleRuntimeError):
            assert str(output.round_trip.original_message) == str(test_case.expected.round_trip.original_message)
        else:
            assert output.round_trip == test_case.expected.round_trip

        assert output.tags == test_case.expected.tags


def test_not_generate_mode():
    assert not _generate, "set _generate=False to statically test expected behavior"

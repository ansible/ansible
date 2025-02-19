from __future__ import annotations

import abc
import typing as t

from dataclasses import dataclass

# noinspection PyProtectedMember
from ansible.module_utils._internal._datatag import AnsibleTagHelper
# noinspection PyProtectedMember
from ansible._internal._templating._access import AnsibleAccessContext, NotifiableAccessContextBase

from units.module_utils.datatag.test_datatag import ExampleSingletonTag, ExampleTagWithContent

untagged_values = (123, 123.45, 'dude', ['dude'], dict(dude='mar'))


@dataclass(frozen=True)
class LoggedAccess:
    ctx: NotifiableAccessContextBase
    obj: object


class LoggingTagAccessNotifier(NotifiableAccessContextBase, metaclass=abc.ABCMeta):
    def __init__(self, access_list: list):
        self._access_list: list = access_list

    def _log(self, o: t.Any) -> t.Any:
        self._access_list.append(LoggedAccess(ctx=self, obj=o))


class ExampleTagWithContentAccessNotifier(LoggingTagAccessNotifier):
    _type_interest = frozenset([ExampleTagWithContent])

    def _notify(self, o: t.Any) -> t.Any:
        super()._log(o)  # get parent logging behavior
        return o


class ExampleSingletonTagAccessNotifier(LoggingTagAccessNotifier):
    _type_interest = frozenset([ExampleSingletonTag])

    def _notify(self, o: t.Any) -> t.Any:
        super()._log(o)  # get parent logging behavior
        return o


class ExampleMaskingSingletonTagAccessNotifier1(ExampleSingletonTagAccessNotifier):
    _mask = True


class ExampleMaskingSingletonTagAccessNotifier2(ExampleMaskingSingletonTagAccessNotifier1):
    ...


def test_ansibleaccesscontext_untagged():
    # accessing untagged objects should always succeed, be a no-op, and return the original value
    for v in untagged_values:
        AnsibleAccessContext.current().access(v)


def test_ansibleaccesscontext_notify():
    tagged_values = [AnsibleTagHelper.tag(v, [ExampleSingletonTag(), ExampleTagWithContent(content_str='replacement')]) for v in untagged_values]

    instance_access_list = []
    singleton_access_list = []

    with ExampleTagWithContentAccessNotifier(instance_access_list):
        with ExampleSingletonTagAccessNotifier(singleton_access_list):
            for tv in tagged_values:
                AnsibleAccessContext.current().access(tv)

    assert [v.obj for v in instance_access_list] == [v.obj for v in singleton_access_list] == tagged_values


def test_mixed_mask_unmask():
    """Ensure that only the innermost instance of each type of a masking access context is notified, while non-masking contexts are always notified."""
    value = ExampleSingletonTag().tag('blah')

    access_log = []

    with (ExampleSingletonTagAccessNotifier(access_log) as outer_nonmasked,
          ExampleMaskingSingletonTagAccessNotifier1(access_log),  # masked
          ExampleMaskingSingletonTagAccessNotifier2(access_log),
          ExampleMaskingSingletonTagAccessNotifier1(access_log) as inner_masked_1,
          ExampleMaskingSingletonTagAccessNotifier2(access_log) as inner_masked_2,
          ExampleSingletonTagAccessNotifier(access_log) as inner_nonmasked,
          ):
        AnsibleAccessContext.current().access(value)

    assert len(access_log) == 4
    assert access_log == [
        LoggedAccess(inner_nonmasked, value),
        LoggedAccess(inner_masked_2, value),
        LoggedAccess(inner_masked_1, value),
        LoggedAccess(outer_nonmasked, value)
    ]

from __future__ import annotations

import os

SHOW_CONTENT = not bool(int(os.environ["REDACTION_ENABLED"]))


from ansible.errors import AnsibleTemplatePluginError, AnsibleError


def make_redacted_error(value: object) -> None:
    raise AnsibleTemplatePluginError("redacted error", obj=value, show_content=SHOW_CONTENT)


def make_redacted_context_error(value: object) -> None:
    try:
        raise AnsibleTemplatePluginError("redacted context error", obj=value, show_content=SHOW_CONTENT)
    except AnsibleTemplatePluginError:
        raise ValueError("have redacted context error")


def make_redacted_orig_exc_error(value: object) -> None:
    try:
        raise AnsibleTemplatePluginError("redacted context error", obj=value, show_content=SHOW_CONTENT)
    except AnsibleTemplatePluginError as ex:
        orig_exc = ex

    raise AnsibleError("have redacted orig_exc error", orig_exc=orig_exc)  # pylint: disable=used-before-assignment


def make_unredacted_error(value: object) -> None:
    raise AnsibleTemplatePluginError("unredacted error", obj=value, show_content=True)


class FilterModule:
    def filters(self):
        return {
            'make_redacted_error': make_redacted_error,
            'make_unredacted_error': make_unredacted_error,
            'make_redacted_context_error': make_redacted_context_error,
            'make_redacted_orig_exc_error': make_redacted_orig_exc_error,
        }

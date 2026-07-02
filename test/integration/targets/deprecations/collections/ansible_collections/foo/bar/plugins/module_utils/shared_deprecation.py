from __future__ import annotations

from ansible.module_utils.datatag import deprecate_value, deprecator_from_collection_name


def get_deprecation_kwargs() -> list[dict[str, object]]:
    return [
        dict(msg="Deprecation that passes collection_name, version, and help_text.", version='9999.9', collection_name='bla.bla', help_text="Help text."),
        dict(
            msg="Deprecation that passes deprecator and datetime.date.",
            date='2034-01-02',
            deprecator=deprecator_from_collection_name('bla.bla'),
        ),
        dict(msg="Deprecation that passes deprecator and string date.", date='2034-01-02', deprecator=deprecator_from_collection_name('bla.bla')),
        dict(msg="Deprecation that passes no deprecator, collection name, or date/version."),
    ]


def get_deprecated_value() -> str:
    return deprecate_value(  # pylint: disable=ansible-deprecated-unnecessary-collection-name,ansible-deprecated-collection-name-not-permitted
        value='a deprecated value',
        msg="value is deprecated",
        collection_name='foo.bar',
        version='9999.9',
    )

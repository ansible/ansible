"""Initialize locale settings. This must be imported very early in ansible-test startup."""

from __future__ import annotations

import locale
import sys
import typing as t

STANDARD_LOCALE = 'en_US.UTF-8'
"""
The standard locale used by ansible-test and its subprocesses and delegated instances.
"""

FALLBACK_LOCALE = 'C.UTF-8'
"""
The fallback locale to use when the standard locale is not available.
This was added in ansible-core 2.14 to allow testing in environments without the standard locale.
It was not needed in previous ansible-core releases since they do not verify the locale during startup.
"""


class LocaleError(SystemExit):
    """Exception to raise when locale related errors occur."""

    def __init__(self, message: str) -> None:
        super().__init__(f'ERROR: {message}')


def configure_locale() -> tuple[str, t.Optional[str]]:
    """Configure the locale, returning the selected locale and an optional warning."""

    if (fs_encoding := sys.getfilesystemencoding()).lower() != 'utf-8':
        raise LocaleError(f'ansible-test requires the filesystem encoding to be UTF-8, but "{fs_encoding}" was detected.')

    candidate_locales = STANDARD_LOCALE, FALLBACK_LOCALE

    errors: dict[str, str] = {}
    warning: t.Optional[str] = None
    configured_locale: t.Optional[str] = None

    for candidate_locale in candidate_locales:
        try:
            locale.setlocale(locale.LC_ALL, candidate_locale)
            locale.getlocale()
        except (locale.Error, ValueError) as ex:
            errors[candidate_locale] = str(ex)
        else:
            configured_locale = candidate_locale
            break

    if not configured_locale:
        raise LocaleError('ansible-test could not initialize a supported locale:\n' +
                          '\n'.join(f'{key}: {value}' for key, value in errors.items()))

    if configured_locale != STANDARD_LOCALE:
        warning = (f'Using locale "{configured_locale}" instead of "{STANDARD_LOCALE}". '
                   'Tests which depend on the locale may behave unexpectedly.')

    return configured_locale, warning


CONFIGURED_LOCALE, LOCALE_WARNING = configure_locale()

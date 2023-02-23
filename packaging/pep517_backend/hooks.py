# -*- coding: utf-8 -*-

"""PEP 517 build backend for optionally pre-building docs before setuptools."""

from setuptools.build_meta import *  # Re-exporting PEP 517 hooks  # pylint: disable=unused-wildcard-import,wildcard-import

from ._backend import (  # noqa: WPS436  # Re-exporting PEP 517 hooks
    build_sdist, get_requires_for_build_sdist,
)

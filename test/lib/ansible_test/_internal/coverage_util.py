"""Utility code for facilitating collection of code coverage when running tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import contextlib
import os
import tempfile

from .config import (
    IntegrationConfig,
    SanityConfig,
    TestConfig,
)

from .util import (
    COVERAGE_CONFIG_PATH,
    remove_tree,
)

from .data import (
    data_context,
)


@contextlib.contextmanager
def coverage_context(args):  # type: (TestConfig) -> None
    """Content to set up and clean up code coverage configuration for tests."""
    coverage_setup(args)

    try:
        yield
    finally:
        coverage_cleanup(args)


def coverage_setup(args):  # type: (TestConfig) -> None
    """Set up code coverage configuration before running tests."""
    if args.coverage and data_context().content.collection:
        coverage_config = generate_collection_coverage_config(args)

        if args.explain:
            args.coverage_config_base_path = '/tmp/coverage-temp-dir'
        else:
            args.coverage_config_base_path = tempfile.mkdtemp()

            with open(os.path.join(args.coverage_config_base_path, COVERAGE_CONFIG_PATH), 'w') as coverage_config_path_fd:
                coverage_config_path_fd.write(coverage_config)


def coverage_cleanup(args):  # type: (TestConfig) -> None
    """Clean up code coverage configuration after tests have finished."""
    if args.coverage_config_base_path and not args.explain:
        remove_tree(args.coverage_config_base_path)
        args.coverage_config_base_path = None


def generate_collection_coverage_config(args):  # type: (TestConfig) -> str
    """Generate code coverage configuration for tests."""
    coverage_config = '''
[run]
branch = True
concurrency = multiprocessing
parallel = True
disable_warnings =
    no-data-collected
'''

    if isinstance(args, IntegrationConfig):
        coverage_config += '''
include =
    %s/*
    */%s/*
''' % (data_context().content.root, data_context().content.collection.directory)
    elif isinstance(args, SanityConfig):
        # temporary work-around for import sanity test
        coverage_config += '''
include =
     %s/*

omit =
    */test/runner/.tox/*
''' % data_context().content.root
    else:
        coverage_config += '''
include =
     %s/*
''' % data_context().content.root

    return coverage_config

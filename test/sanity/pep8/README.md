# PEP 8

[PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines are enforced by
[pep8](https://pypi.python.org/pypi/pep8) on all python files in the repository by default.

## Current Rule Set

By default all files are tested using the current rule set.
All `pep8` tests are executed, except those listed in the [current ignore list](current-ignore.txt).

## Legacy Rule Set

Files which are listed in the [legacy file list](legacy-files.txt) are tested using the legacy rule set.
All `pep8` tests are executed, except those listed in the [current ignore list](current-ignore.txt) or
[legacy ignore list](legacy-ignore.txt).

> Files listed in the legacy file list which pass the current rule set will result in an error.
> This is intended to prevent regressions on style guidelines for files which pass the more stringent current rule set.

## Skipping Tests

Files listed in the [skip list](skip.txt) are not tested by `pep8`.

## Removed Files

Files which have been removed from the repository must be removed from the legacy file list and the skip list.

## Running Locally

The pep8 check can be run locally with:

    ./test/runner/ansible-test sanity --test pep8 [file-or-directory-path-to-check] ...


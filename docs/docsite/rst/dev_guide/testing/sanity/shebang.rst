shebang
=======

Most executable files should only use one of the following shebangs:

- ``#!/bin/sh``
- ``#!/bin/bash``
- ``#!/usr/bin/make``
- ``#!/usr/bin/env python``
- ``#!/usr/bin/env bash``

NOTE: For ``#!/bin/bash``, any of the options ``eux`` may also be used, such as ``#!/bin/bash -eux``.

This does not apply to Ansible modules, which should not be executable and must always use ``#!/usr/bin/python``.

Some exceptions are permitted. Ask if you have questions.

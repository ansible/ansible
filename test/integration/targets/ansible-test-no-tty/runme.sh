#!/usr/bin/env bash

set -eux

unexpected=
test ! -t 0 || ${unexpected:?stdin is a tty}
test ! -t 1 || ${unexpected:?stdout is a tty}
test ! -t 2 || ${unexpected:?stderr is a tty}

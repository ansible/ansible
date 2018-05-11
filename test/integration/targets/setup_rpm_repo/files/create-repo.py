#!/usr/bin/env python


import sys
from collections import namedtuple
import rpmfluff


RPM = namedtuple('RPM', ['name', 'version', 'release', 'epoch'])


SPECS = [
    RPM('foo', '1.0', '1', None),
    RPM('foo', '1.0', '2', '1'),
    RPM('foo', '1.1', '1', '1'),
]


def main():
    try:
        arch = sys.argv[1]
    except IndexError:
        arch = 'x86_64'

    pkgs = []
    for spec in SPECS:
        pkg = rpmfluff.SimpleRpmBuild(spec.name, spec.version, spec.release, [arch])
        pkg.epoch = spec.epoch
        pkgs.append(pkg)

    repo = rpmfluff.YumRepoBuild(pkgs)
    repo.make(arch)

    for pkg in pkgs:
        pkg.clean()

    print(repo.repoDir)


if __name__ == "__main__":
    main()

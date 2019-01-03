#!/usr/bin/env python


import sys
from collections import namedtuple
import rpmfluff


RPM = namedtuple('RPM', ['name', 'version', 'release', 'epoch', 'recommends'])


SPECS = [
    RPM('foo', '1.0', '1', None, None),
    RPM('foo', '1.0', '2', '1', None),
    RPM('foo', '1.1', '1', '1', None),
    RPM('foo-bar', '1.0', '1', None, None),
    RPM('foo-bar', '1.1', '1', None, None),
    RPM('bar', '1.0', '1', None, None),
    RPM('bar', '1.1', '1', None, None),
    RPM('foo-with-weak-dep', '1.0', '1', None, ['foo-weak-dep']),
    RPM('foo-weak-dep', '1.0', '1', None, None),
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

        if spec.recommends:
            for recommend in spec.recommends:
                pkg.add_recommends(recommend)

        pkgs.append(pkg)

    repo = rpmfluff.YumRepoBuild(pkgs)
    repo.make(arch)

    for pkg in pkgs:
        pkg.clean()

    print(repo.repoDir)


if __name__ == "__main__":
    main()

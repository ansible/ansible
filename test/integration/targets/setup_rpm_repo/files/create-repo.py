#!/usr/bin/env python


import sys
from collections import namedtuple

try:
    from rpmfluff import SimpleRpmBuild
    from rpmfluff import YumRepoBuild
except ImportError:
    from rpmfluff.rpmbuild import SimpleRpmBuild
    from rpmfluff.yumrepobuild import YumRepoBuild

try:
    from rpmfluff import can_use_rpm_weak_deps
except ImportError:
    try:
        from rpmfluff.utils import can_use_rpm_weak_deps
    except ImportError:
        can_use_rpm_weak_deps = None

RPM = namedtuple('RPM', ['name', 'version', 'release', 'epoch', 'recommends'])


SPECS = [
    RPM('dinginessentail', '1.0', '1', None, None),
    RPM('dinginessentail', '1.0', '2', '1', None),
    RPM('dinginessentail', '1.1', '1', '1', None),
    RPM('dinginessentail-olive', '1.0', '1', None, None),
    RPM('dinginessentail-olive', '1.1', '1', None, None),
    RPM('landsidescalping', '1.0', '1', None, None),
    RPM('landsidescalping', '1.1', '1', None, None),
    RPM('dinginessentail-with-weak-dep', '1.0', '1', None, ['dinginessentail-weak-dep']),
    RPM('dinginessentail-weak-dep', '1.0', '1', None, None),
]


def main():
    try:
        arch = sys.argv[1]
    except IndexError:
        arch = 'x86_64'

    pkgs = []
    for spec in SPECS:
        pkg = SimpleRpmBuild(spec.name, spec.version, spec.release, [arch])
        pkg.epoch = spec.epoch

        if spec.recommends:
            # Skip packages that require weak deps but an older version of RPM is being used
            if not can_use_rpm_weak_deps or not can_use_rpm_weak_deps():
                continue

            for recommend in spec.recommends:
                pkg.add_recommends(recommend)

        pkgs.append(pkg)

    repo = YumRepoBuild(pkgs)
    repo.make(arch)

    for pkg in pkgs:
        pkg.clean()

    print(repo.repoDir)


if __name__ == "__main__":
    main()

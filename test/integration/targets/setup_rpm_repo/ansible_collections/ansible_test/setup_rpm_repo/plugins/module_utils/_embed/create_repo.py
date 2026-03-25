import sys
import tempfile
import typing

from rpmfluff.make import make_gif
from rpmfluff.sourcefile import GeneratedSourceFile
from rpmfluff.rpmbuild import SimpleRpmBuild
from rpmfluff.utils import expectedArch
from rpmfluff.yumrepobuild import YumRepoBuild


class RPM(typing.NamedTuple):
    name: str
    version: str
    release: str = '1'
    epoch: int = 0
    arch: typing.Optional[typing.List[str]] = None
    recommends: typing.Optional[typing.List[str]] = None
    requires: typing.Optional[typing.List[str]] = None
    file: typing.Optional[str] = None
    binary: typing.Optional[str] = None
    provides: typing.Optional[typing.List[str]] = None
    pre: typing.Optional[str] = None


SPECS = [
    RPM(name='dinginessentail', version='1.0'),
    RPM(name='dinginessentail', version='1.0', release='2', epoch=1),
    RPM(name='dinginessentail', version='1.1', epoch=1),
    RPM(name='dinginessentail-olive', version='1.0'),
    RPM(name='dinginessentail-olive', version='1.1'),
    RPM(name='multilib-dinginessentail', version='1.0', arch=['i686', 'x86_64']),
    RPM(name='multilib-dinginessentail', version='1.1', arch=['i686', 'x86_64']),
    RPM(name='landsidescalping', version='1.0',),
    RPM(name='landsidescalping', version='1.1',),
    RPM(name='dinginessentail-with-weak-dep', version='1.0', recommends=['dinginessentail-weak-dep']),
    RPM(name='dinginessentail-weak-dep', version='1.0',),
    RPM(name='noarchfake', version='1.0'),
    RPM(name='provides_foo_a', version='1.0', file='foo.gif'),
    RPM(name='provides_foo_b', version='1.0', file='foo.gif'),
    RPM(name='number-11-name', version='11.0',),
    RPM(name='number-11-name', version='11.1',),
    RPM(name='epochone', version='1.0', epoch=1),
    RPM(name='epochone', version='1.1', epoch=1),
    RPM(name='broken-a', version='1.2.3',),
    RPM(name='broken-a', version='1.2.3.4', requires=['dinginessentail-doesnotexist']),
    RPM(name='broken-a', version='1.2.4',),
    RPM(name='broken-a', version='2.0.0', requires=['dinginessentail-doesnotexist']),
    RPM(name='broken-b', version='1.0', requires=['broken-a = 1.2.3']),
    RPM(name='broken-c', version='1.0', requires=['broken-a = 1.2.4']),
    RPM(name='broken-d', version='1.0', requires=['broken-a']),
    RPM(name='provides-binary', version='1.0', arch=[expectedArch], binary='/usr/sbin/package-name'),
    RPM(name='package-name', version='1.0'),
    RPM(name='provides-package', version='1.0', provides=['provided-package']),
    RPM(name='provided-package', version='1.0'),
    RPM(name='broken-scriptlet', version='1.0', pre='/bin/false\n'),
]


def create_repo():
    pkgs = []
    for spec in SPECS:
        pkg = SimpleRpmBuild(spec.name, spec.version, spec.release, spec.arch or ['noarch'])
        pkg.epoch = spec.epoch

        for requires in spec.requires or []:
            pkg.add_requires(requires)

        for recommend in spec.recommends or []:
            pkg.add_recommends(recommend)

        for provide in spec.provides or []:
            pkg.add_provides(provide)

        if spec.file:
            pkg.add_installed_file(
                "/" + spec.file,
                GeneratedSourceFile(
                    spec.file, make_gif()
                )
            )

        if spec.pre:
            pkg.add_pre(spec.pre)

        if spec.binary:
            pkg.add_simple_compilation(installPath=spec.binary)

        pkgs.append(pkg)

    repo = YumRepoBuild(pkgs)
    repo.make('noarch', 'i686', 'x86_64', expectedArch)

    for pkg in pkgs:
        pkg.clean()

    return repo.repoDir


def main():
    tempdir = sys.argv[1]

    # Save current temp dir so we can set it back later
    original_tempdir = tempfile.tempdir
    tempfile.tempdir = tempdir

    try:
        print(create_repo())
    finally:
        tempfile.tempdir = original_tempdir


if __name__ == "__main__":
    main()

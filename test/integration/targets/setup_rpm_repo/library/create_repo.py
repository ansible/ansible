#!/usr/bin/python

from __future__ import annotations

import tempfile

from dataclasses import dataclass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.respawn import has_respawned, probe_interpreters_for_module, respawn_module

HAS_RPMFLUFF = True

try:
    from rpmfluff.make import make_gif
    from rpmfluff.sourcefile import GeneratedSourceFile
    from rpmfluff.rpmbuild import SimpleRpmBuild
    from rpmfluff.yumrepobuild import YumRepoBuild
except ImportError:
    HAS_RPMFLUFF = False


@dataclass
class RPM:
    name: str
    version: str
    release: str = '1'
    epoch: int = 0
    arch: list[str] | None = None
    recommends: list[str] | None = None
    requires: list[str] | None = None
    file: str | None = None


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
    RPM(name='broken-b', version='1.0', requires=['broken-a = 1.2.3-1']),
    RPM(name='broken-c', version='1.0', requires=['broken-c = 1.2.4-1']),
    RPM(name='broken-d', version='1.0', requires=['broken-a']),
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

        if spec.file:
            pkg.add_installed_file(
                "/" + spec.file,
                GeneratedSourceFile(
                    spec.file, make_gif()
                )
            )

        pkgs.append(pkg)

    repo = YumRepoBuild(pkgs)
    repo.make('noarch', 'i686', 'x86_64')

    for pkg in pkgs:
        pkg.clean()

    return repo.repoDir


def main():
    module = AnsibleModule(
        argument_spec={
            'tempdir': {'type': 'path'},
        }
    )

    if not HAS_RPMFLUFF:
        system_interpreters = ['/usr/libexec/platform-python', '/usr/bin/python3', '/usr/bin/python']

        interpreter = probe_interpreters_for_module(system_interpreters, 'rpmfluff')

        if not interpreter or has_respawned():
            module.fail_json('unable to find rpmfluff; tried {0}'.format(system_interpreters))

        respawn_module(interpreter)

    tempdir = module.params['tempdir']

    # Save current temp dir so we can set it back later
    original_tempdir = tempfile.tempdir
    tempfile.tempdir = tempdir

    try:
        repo_dir = create_repo()
    finally:
        tempfile.tempdir = original_tempdir

    module.exit_json(repo_dir=repo_dir, tmpfile=tempfile.gettempdir())


if __name__ == "__main__":
    main()

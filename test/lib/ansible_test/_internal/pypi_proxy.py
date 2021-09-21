"""PyPI proxy management."""
from __future__ import annotations

import atexit
import os
import urllib.parse

from .io import (
    write_text_file,
)

from .config import (
    EnvironmentConfig,
)

from .host_configs import (
    PosixConfig,
)

from .util import (
    ApplicationError,
    display,
)

from .util_common import (
    process_scoped_temporary_file,
)

from .docker_util import (
    docker_available,
)

from .containers import (
    HostType,
    get_container_database,
    run_support_container,
)

from .ansible_util import (
    run_playbook,
)

from .host_profiles import (
    HostProfile,
)

from .inventory import (
    create_posix_inventory,
)


def run_pypi_proxy(args, targets_use_pypi):  # type: (EnvironmentConfig, bool) -> None
    """Run a PyPI proxy support container."""
    if args.pypi_endpoint:
        return  # user has overridden the proxy endpoint, there is nothing to provision

    posix_targets = [target for target in args.targets if isinstance(target, PosixConfig)]
    need_proxy = targets_use_pypi and any(target.python.version == '2.6' for target in posix_targets)
    use_proxy = args.pypi_proxy or need_proxy

    if not use_proxy:
        return

    if not docker_available():
        if args.pypi_proxy:
            raise ApplicationError('Use of the PyPI proxy was requested, but Docker is not available.')

        display.warning('Unable to use the PyPI proxy because Docker is not available. Installation of packages using `pip` may fail.')
        return

    image = 'quay.io/ansible/pypi-test-container:1.0.0'
    port = 3141

    run_support_container(
        args=args,
        context='__pypi_proxy__',
        image=image,
        name=f'pypi-test-container-{args.session_name}',
        ports=[port],
    )


def configure_pypi_proxy(args, profile):  # type: (EnvironmentConfig, HostProfile) -> None
    """Configure the environment to use a PyPI proxy, if present."""
    if args.pypi_endpoint:
        pypi_endpoint = args.pypi_endpoint
    else:
        containers = get_container_database(args)
        context = containers.data.get(HostType.control if profile.controller else HostType.managed, {}).get('__pypi_proxy__')

        if not context:
            return  # proxy not configured

        access = list(context.values())[0]

        host = access.host_ip
        port = dict(access.port_map())[3141]

        pypi_endpoint = f'http://{host}:{port}/root/pypi/+simple/'

    pypi_hostname = urllib.parse.urlparse(pypi_endpoint)[1].split(':')[0]

    if profile.controller:
        configure_controller_pypi_proxy(args, profile, pypi_endpoint, pypi_hostname)
    else:
        configure_target_pypi_proxy(args, profile, pypi_endpoint, pypi_hostname)


def configure_controller_pypi_proxy(args, profile, pypi_endpoint, pypi_hostname):  # type: (EnvironmentConfig, HostProfile, str, str) -> None
    """Configure the controller environment to use a PyPI proxy."""
    configure_pypi_proxy_pip(args, profile, pypi_endpoint, pypi_hostname)
    configure_pypi_proxy_easy_install(args, profile, pypi_endpoint)


def configure_target_pypi_proxy(args, profile, pypi_endpoint, pypi_hostname):  # type: (EnvironmentConfig, HostProfile, str, str) -> None
    """Configure the target environment to use a PyPI proxy."""
    inventory_path = process_scoped_temporary_file(args)

    create_posix_inventory(args, inventory_path, [profile])

    def cleanup_pypi_proxy():
        """Undo changes made to configure the PyPI proxy."""
        run_playbook(args, inventory_path, 'pypi_proxy_restore.yml', capture=True)

    force = 'yes' if profile.config.is_managed else 'no'

    run_playbook(args, inventory_path, 'pypi_proxy_prepare.yml', dict(pypi_endpoint=pypi_endpoint, pypi_hostname=pypi_hostname, force=force), capture=True)

    atexit.register(cleanup_pypi_proxy)


def configure_pypi_proxy_pip(args, profile, pypi_endpoint, pypi_hostname):  # type: (EnvironmentConfig, HostProfile, str, str) -> None
    """Configure a custom index for pip based installs."""
    pip_conf_path = os.path.expanduser('~/.pip/pip.conf')
    pip_conf = '''
[global]
index-url = {0}
trusted-host = {1}
'''.format(pypi_endpoint, pypi_hostname).strip()

    def pip_conf_cleanup():  # type: () -> None
        """Remove custom pip PyPI config."""
        display.info('Removing custom PyPI config: %s' % pip_conf_path, verbosity=1)
        os.remove(pip_conf_path)

    if os.path.exists(pip_conf_path) and not profile.config.is_managed:
        raise ApplicationError('Refusing to overwrite existing file: %s' % pip_conf_path)

    display.info('Injecting custom PyPI config: %s' % pip_conf_path, verbosity=1)
    display.info('Config: %s\n%s' % (pip_conf_path, pip_conf), verbosity=3)

    if not args.explain:
        write_text_file(pip_conf_path, pip_conf, True)
        atexit.register(pip_conf_cleanup)


def configure_pypi_proxy_easy_install(args, profile, pypi_endpoint):  # type: (EnvironmentConfig, HostProfile, str) -> None
    """Configure a custom index for easy_install based installs."""
    pydistutils_cfg_path = os.path.expanduser('~/.pydistutils.cfg')
    pydistutils_cfg = '''
[easy_install]
index_url = {0}
'''.format(pypi_endpoint).strip()

    if os.path.exists(pydistutils_cfg_path) and not profile.config.is_managed:
        raise ApplicationError('Refusing to overwrite existing file: %s' % pydistutils_cfg_path)

    def pydistutils_cfg_cleanup():  # type: () -> None
        """Remove custom PyPI config."""
        display.info('Removing custom PyPI config: %s' % pydistutils_cfg_path, verbosity=1)
        os.remove(pydistutils_cfg_path)

    display.info('Injecting custom PyPI config: %s' % pydistutils_cfg_path, verbosity=1)
    display.info('Config: %s\n%s' % (pydistutils_cfg_path, pydistutils_cfg), verbosity=3)

    if not args.explain:
        write_text_file(pydistutils_cfg_path, pydistutils_cfg, True)
        atexit.register(pydistutils_cfg_cleanup)

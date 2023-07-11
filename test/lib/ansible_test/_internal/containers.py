"""High level functions for working with containers."""
from __future__ import annotations

import collections.abc as c
import contextlib
import json
import random
import time
import uuid
import threading
import typing as t

from .util import (
    ApplicationError,
    SubprocessError,
    display,
    sanitize_host_name,
)

from .util_common import (
    ExitHandler,
    named_temporary_file,
)

from .config import (
    EnvironmentConfig,
    IntegrationConfig,
    SanityConfig,
    ShellConfig,
    UnitsConfig,
    WindowsIntegrationConfig,
)

from .docker_util import (
    ContainerNotFoundError,
    DockerInspect,
    docker_create,
    docker_exec,
    docker_inspect,
    docker_network_inspect,
    docker_pull,
    docker_rm,
    docker_run,
    docker_start,
    get_docker_container_id,
    get_docker_host_ip,
    get_podman_host_ip,
    get_session_container_name,
    require_docker,
    detect_host_properties,
)

from .ansible_util import (
    run_playbook,
)

from .core_ci import (
    SshKey,
)

from .target import (
    IntegrationTarget,
)

from .ssh import (
    SshConnectionDetail,
    SshProcess,
    create_ssh_port_forwards,
    create_ssh_port_redirects,
    generate_ssh_inventory,
)

from .host_configs import (
    ControllerConfig,
    DockerConfig,
    OriginConfig,
    PosixSshConfig,
    PythonConfig,
    RemoteConfig,
    WindowsInventoryConfig,
)

from .connections import (
    SshConnection,
)

from .thread import (
    mutex,
)

# information about support containers provisioned by the current ansible-test instance
support_containers: dict[str, ContainerDescriptor] = {}
support_containers_mutex = threading.Lock()


class HostType:
    """Enum representing the types of hosts involved in running tests."""

    origin = 'origin'
    control = 'control'
    managed = 'managed'


def run_support_container(
    args: EnvironmentConfig,
    context: str,
    image: str,
    name: str,
    ports: list[int],
    aliases: t.Optional[list[str]] = None,
    start: bool = True,
    cleanup: bool = True,
    cmd: t.Optional[list[str]] = None,
    env: t.Optional[dict[str, str]] = None,
    options: t.Optional[list[str]] = None,
    publish_ports: bool = True,
) -> t.Optional[ContainerDescriptor]:
    """
    Start a container used to support tests, but not run them.
    Containers created this way will be accessible from tests.
    """
    name = get_session_container_name(args, name)

    if args.prime_containers:
        docker_pull(args, image)
        return None

    # SSH is required for publishing ports, as well as modifying the hosts file.
    # Initializing the SSH key here makes sure it is available for use after delegation.
    SshKey(args)

    aliases = aliases or [sanitize_host_name(name)]

    docker_command = require_docker().command
    current_container_id = get_docker_container_id()

    if docker_command == 'docker':
        if isinstance(args.controller, DockerConfig) and all(isinstance(target, (ControllerConfig, DockerConfig)) for target in args.targets):
            publish_ports = False  # publishing ports is not needed when test hosts are on the docker network

        if current_container_id:
            publish_ports = False  # publishing ports is pointless if already running in a docker container

    options = options or []

    if start:
        options.append('-dt')  # the -t option is required to cause systemd in the container to log output to the console

    if publish_ports:
        for port in ports:
            options.extend(['-p', str(port)])

    if env:
        for key, value in env.items():
            options.extend(['--env', '%s=%s' % (key, value)])

    max_open_files = detect_host_properties(args).max_open_files

    options.extend(['--ulimit', 'nofile=%s' % max_open_files])

    if args.dev_systemd_debug:
        options.extend(('--env', 'SYSTEMD_LOG_LEVEL=debug'))

    display.info('Starting new "%s" container.' % name)
    docker_pull(args, image)
    support_container_id = run_container(args, image, name, options, create_only=not start, cmd=cmd)
    running = start

    descriptor = ContainerDescriptor(
        image,
        context,
        name,
        support_container_id,
        ports,
        aliases,
        publish_ports,
        running,
        cleanup,
        env,
    )

    with support_containers_mutex:
        if name in support_containers:
            raise Exception(f'Container already defined: {name}')

        if not support_containers:
            ExitHandler.register(cleanup_containers, args)

        support_containers[name] = descriptor

    display.info(f'Adding "{name}" to container database.')

    if start:
        descriptor.register(args)

    return descriptor


def run_container(
    args: EnvironmentConfig,
    image: str,
    name: str,
    options: t.Optional[list[str]],
    cmd: t.Optional[list[str]] = None,
    create_only: bool = False,
) -> str:
    """Run a container using the given docker image."""
    options = list(options or [])
    cmd = list(cmd or [])

    options.extend(['--name', name])

    network = get_docker_preferred_network_name(args)

    if is_docker_user_defined_network(network):
        # Only when the network is not the default bridge network.
        options.extend(['--network', network])

    for _iteration in range(1, 3):
        try:
            if create_only:
                stdout = docker_create(args, image, options, cmd)[0]
            else:
                stdout = docker_run(args, image, options, cmd)[0]
        except SubprocessError as ex:
            display.error(ex.message)
            display.warning(f'Failed to run docker image "{image}". Waiting a few seconds before trying again.')
            docker_rm(args, name)  # podman doesn't remove containers after create if run fails
            time.sleep(3)
        else:
            if args.explain:
                stdout = ''.join(random.choice('0123456789abcdef') for _iteration in range(64))

            return stdout.strip()

    raise ApplicationError(f'Failed to run docker image "{image}".')


def start_container(args: EnvironmentConfig, container_id: str) -> tuple[t.Optional[str], t.Optional[str]]:
    """Start a docker container by name or ID."""
    options: list[str] = []

    for _iteration in range(1, 3):
        try:
            return docker_start(args, container_id, options)
        except SubprocessError as ex:
            display.error(ex.message)
            display.warning(f'Failed to start docker container "{container_id}". Waiting a few seconds before trying again.')
            time.sleep(3)

    raise ApplicationError(f'Failed to start docker container "{container_id}".')


def get_container_ip_address(args: EnvironmentConfig, container: DockerInspect) -> t.Optional[str]:
    """Return the IP address of the container for the preferred docker network."""
    if container.networks:
        network_name = get_docker_preferred_network_name(args)

        if not network_name:
            # Sort networks and use the first available.
            # This assumes all containers will have access to the same networks.
            network_name = sorted(container.networks.keys()).pop(0)

        ipaddress = container.networks[network_name]['IPAddress']
    else:
        ipaddress = container.network_settings['IPAddress']

    if not ipaddress:
        return None

    return ipaddress


@mutex
def get_docker_preferred_network_name(args: EnvironmentConfig) -> t.Optional[str]:
    """
    Return the preferred network name for use with Docker. The selection logic is:
    - the network selected by the user with `--docker-network`
    - the network of the currently running docker container (if any)
    - the default docker network (returns None)
    """
    try:
        return get_docker_preferred_network_name.network  # type: ignore[attr-defined]
    except AttributeError:
        pass

    network = None

    if args.docker_network:
        network = args.docker_network
    else:
        current_container_id = get_docker_container_id()

        if current_container_id:
            # Make sure any additional containers we launch use the same network as the current container we're running in.
            # This is needed when ansible-test is running in a container that is not connected to Docker's default network.
            container = docker_inspect(args, current_container_id, always=True)
            network = container.get_network_name()

    # The default docker behavior puts containers on the same network.
    # The default podman behavior puts containers on isolated networks which don't allow communication between containers or network disconnect.
    # Starting with podman version 2.1.0 rootless containers are able to join networks.
    # Starting with podman version 2.2.0 containers can be disconnected from networks.
    # To maintain feature parity with docker, detect and use the default "podman" network when running under podman.
    if network is None and require_docker().command == 'podman' and docker_network_inspect(args, 'podman', always=True):
        network = 'podman'

    get_docker_preferred_network_name.network = network  # type: ignore[attr-defined]

    return network


def is_docker_user_defined_network(network: str) -> bool:
    """Return True if the network being used is a user-defined network."""
    return bool(network) and network != 'bridge'


@mutex
def get_container_database(args: EnvironmentConfig) -> ContainerDatabase:
    """Return the current container database, creating it as needed, or returning the one provided on the command line through delegation."""
    try:
        return get_container_database.database  # type: ignore[attr-defined]
    except AttributeError:
        pass

    if args.containers:
        display.info('Parsing container database.', verbosity=1)
        database = ContainerDatabase.from_dict(json.loads(args.containers))
    else:
        display.info('Creating container database.', verbosity=1)
        database = create_container_database(args)

    display.info('>>> Container Database\n%s' % json.dumps(database.to_dict(), indent=4, sort_keys=True), verbosity=3)

    get_container_database.database = database  # type: ignore[attr-defined]

    return database


class ContainerAccess:
    """Information needed for one test host to access a single container supporting tests."""

    def __init__(self, host_ip: str, names: list[str], ports: t.Optional[list[int]], forwards: t.Optional[dict[int, int]]) -> None:
        # if forwards is set
        #   this is where forwards are sent (it is the host that provides an indirect connection to the containers on alternate ports)
        #   /etc/hosts uses 127.0.0.1 (since port redirection will be used)
        # else
        #   this is what goes into /etc/hosts (it is the container's direct IP)
        self.host_ip = host_ip

        # primary name + any aliases -- these go into the hosts file and reference the appropriate ip for the origin/control/managed host
        self.names = names

        # ports available (set if forwards is not set)
        self.ports = ports

        # port redirections to create through host_ip -- if not set, no port redirections will be used
        self.forwards = forwards

    def port_map(self) -> list[tuple[int, int]]:
        """Return a port map for accessing this container."""
        if self.forwards:
            ports = list(self.forwards.items())
        else:
            ports = [(port, port) for port in self.ports]

        return ports

    @staticmethod
    def from_dict(data: dict[str, t.Any]) -> ContainerAccess:
        """Return a ContainerAccess instance from the given dict."""
        forwards = data.get('forwards')

        if forwards:
            forwards = dict((int(key), value) for key, value in forwards.items())

        return ContainerAccess(
            host_ip=data['host_ip'],
            names=data['names'],
            ports=data.get('ports'),
            forwards=forwards,
        )

    def to_dict(self) -> dict[str, t.Any]:
        """Return a dict of the current instance."""
        value: dict[str, t.Any] = dict(
            host_ip=self.host_ip,
            names=self.names,
        )

        if self.ports:
            value.update(ports=self.ports)

        if self.forwards:
            value.update(forwards=self.forwards)

        return value


class ContainerDatabase:
    """Database of running containers used to support tests."""

    def __init__(self, data: dict[str, dict[str, dict[str, ContainerAccess]]]) -> None:
        self.data = data

    @staticmethod
    def from_dict(data: dict[str, t.Any]) -> ContainerDatabase:
        """Return a ContainerDatabase instance from the given dict."""
        return ContainerDatabase(dict((access_name,
                                       dict((context_name,
                                             dict((container_name, ContainerAccess.from_dict(container))
                                                  for container_name, container in containers.items()))
                                            for context_name, containers in contexts.items()))
                                      for access_name, contexts in data.items()))

    def to_dict(self) -> dict[str, t.Any]:
        """Return a dict of the current instance."""
        return dict((access_name,
                     dict((context_name,
                           dict((container_name, container.to_dict())
                                for container_name, container in containers.items()))
                          for context_name, containers in contexts.items()))
                    for access_name, contexts in self.data.items())


def local_ssh(args: EnvironmentConfig, python: PythonConfig) -> SshConnectionDetail:
    """Return SSH connection details for localhost, connecting as root to the default SSH port."""
    return SshConnectionDetail('localhost', 'localhost', None, 'root', SshKey(args).key, python.path)


def root_ssh(ssh: SshConnection) -> SshConnectionDetail:
    """Return the SSH connection details from the given SSH connection. If become was specified, the user will be changed to `root`."""
    settings = ssh.settings.__dict__.copy()

    if ssh.become:
        settings.update(
            user='root',
        )

    return SshConnectionDetail(**settings)


def create_container_database(args: EnvironmentConfig) -> ContainerDatabase:
    """Create and return a container database with information necessary for all test hosts to make use of relevant support containers."""
    origin: dict[str, dict[str, ContainerAccess]] = {}
    control: dict[str, dict[str, ContainerAccess]] = {}
    managed: dict[str, dict[str, ContainerAccess]] = {}

    for name, container in support_containers.items():
        if container.details.published_ports:
            if require_docker().command == 'podman':
                host_ip_func = get_podman_host_ip
            else:
                host_ip_func = get_docker_host_ip
            published_access = ContainerAccess(
                host_ip=host_ip_func(),
                names=container.aliases,
                ports=None,
                forwards=dict((port, published_port) for port, published_port in container.details.published_ports.items()),
            )
        else:
            published_access = None  # no published access without published ports (ports are only published if needed)

        if container.details.container_ip:
            # docker containers, and rootfull podman containers should have a container IP address
            container_access = ContainerAccess(
                host_ip=container.details.container_ip,
                names=container.aliases,
                ports=container.ports,
                forwards=None,
            )
        elif require_docker().command == 'podman':
            # published ports for rootless podman containers should be accessible from the host's IP
            container_access = ContainerAccess(
                host_ip=get_podman_host_ip(),
                names=container.aliases,
                ports=None,
                forwards=dict((port, published_port) for port, published_port in container.details.published_ports.items()),
            )
        else:
            container_access = None  # no container access without an IP address

        if get_docker_container_id():
            if not container_access:
                raise Exception('Missing IP address for container: %s' % name)

            origin_context = origin.setdefault(container.context, {})
            origin_context[name] = container_access
        elif not published_access:
            pass  # origin does not have network access to the containers
        else:
            origin_context = origin.setdefault(container.context, {})
            origin_context[name] = published_access

        if isinstance(args.controller, RemoteConfig):
            pass  # SSH forwarding required
        elif '-controller-' in name:
            pass  # hack to avoid exposing the controller container to the controller
        elif isinstance(args.controller, DockerConfig) or (isinstance(args.controller, OriginConfig) and get_docker_container_id()):
            if container_access:
                control_context = control.setdefault(container.context, {})
                control_context[name] = container_access
            else:
                raise Exception('Missing IP address for container: %s' % name)
        else:
            if not published_access:
                raise Exception('Missing published ports for container: %s' % name)

            control_context = control.setdefault(container.context, {})
            control_context[name] = published_access

        if issubclass(args.target_type, (RemoteConfig, WindowsInventoryConfig, PosixSshConfig)):
            pass  # SSH forwarding required
        elif '-controller-' in name or '-target-' in name:
            pass  # hack to avoid exposing the controller and target containers to the target
        elif issubclass(args.target_type, DockerConfig) or (issubclass(args.target_type, OriginConfig) and get_docker_container_id()):
            if container_access:
                managed_context = managed.setdefault(container.context, {})
                managed_context[name] = container_access
            else:
                raise Exception('Missing IP address for container: %s' % name)
        else:
            if not published_access:
                raise Exception('Missing published ports for container: %s' % name)

            managed_context = managed.setdefault(container.context, {})
            managed_context[name] = published_access

    data = {
        HostType.origin: origin,
        HostType.control: control,
        HostType.managed: managed,
    }

    data = dict((key, value) for key, value in data.items() if value)

    return ContainerDatabase(data)


class SupportContainerContext:
    """Context object for tracking information relating to access of support containers."""

    def __init__(self, containers: ContainerDatabase, process: t.Optional[SshProcess]) -> None:
        self.containers = containers
        self.process = process

    def close(self) -> None:
        """Close the process maintaining the port forwards."""
        if not self.process:
            return  # forwarding not in use

        self.process.terminate()

        display.info('Waiting for the session SSH port forwarding process to terminate.', verbosity=1)

        self.process.wait()


@contextlib.contextmanager
def support_container_context(
    args: EnvironmentConfig,
    ssh: t.Optional[SshConnectionDetail],
) -> c.Iterator[t.Optional[ContainerDatabase]]:
    """Create a context manager for integration tests that use support containers."""
    if not isinstance(args, (IntegrationConfig, UnitsConfig, SanityConfig, ShellConfig)):
        yield None  # containers are only needed for commands that have targets (hosts or pythons)
        return

    containers = get_container_database(args)

    if not containers.data:
        yield ContainerDatabase({})  # no containers are being used, return an empty database
        return

    context = create_support_container_context(args, ssh, containers)

    try:
        yield context.containers
    finally:
        context.close()


def create_support_container_context(
    args: EnvironmentConfig,
    ssh: t.Optional[SshConnectionDetail],
    containers: ContainerDatabase,
) -> SupportContainerContext:
    """Context manager that provides SSH port forwards. Returns updated container metadata."""
    host_type = HostType.control

    revised = ContainerDatabase(containers.data.copy())
    source = revised.data.pop(HostType.origin, None)

    container_map: dict[tuple[str, int], tuple[str, str, int]] = {}

    if host_type not in revised.data:
        if not source:
            raise Exception('Missing origin container details.')

        for context_name, context in source.items():
            for container_name, container in context.items():
                if '-controller-' in container_name:
                    continue  # hack to avoid exposing the controller container to the controller

                for port, access_port in container.port_map():
                    container_map[(container.host_ip, access_port)] = (context_name, container_name, port)

    if not container_map:
        return SupportContainerContext(revised, None)

    if not ssh:
        raise Exception('The %s host was not pre-configured for container access and SSH forwarding is not available.' % host_type)

    forwards = list(container_map.keys())
    process = create_ssh_port_forwards(args, ssh, forwards)
    result = SupportContainerContext(revised, process)

    try:
        port_forwards = process.collect_port_forwards()
        contexts: dict[str, dict[str, ContainerAccess]] = {}

        for forward, forwarded_port in port_forwards.items():
            access_host, access_port = forward
            context_name, container_name, container_port = container_map[(access_host, access_port)]
            container = source[context_name][container_name]
            context = contexts.setdefault(context_name, {})

            forwarded_container = context.setdefault(container_name, ContainerAccess('127.0.0.1', container.names, None, {}))
            forwarded_container.forwards[container_port] = forwarded_port

            display.info('Container "%s" port %d available at %s:%d is forwarded over SSH as port %d.' % (
                container_name, container_port, access_host, access_port, forwarded_port,
            ), verbosity=1)

        revised.data[host_type] = contexts

        return result
    except Exception:
        result.close()
        raise


class ContainerDescriptor:
    """Information about a support container."""

    def __init__(
        self,
        image: str,
        context: str,
        name: str,
        container_id: str,
        ports: list[int],
        aliases: list[str],
        publish_ports: bool,
        running: bool,
        cleanup: bool,
        env: t.Optional[dict[str, str]],
    ) -> None:
        self.image = image
        self.context = context
        self.name = name
        self.container_id = container_id
        self.ports = ports
        self.aliases = aliases
        self.publish_ports = publish_ports
        self.running = running
        self.cleanup = cleanup
        self.env = env
        self.details: t.Optional[SupportContainer] = None

    def start(self, args: EnvironmentConfig) -> None:
        """Start the container. Used for containers which are created, but not started."""
        start_container(args, self.name)

        self.register(args)

    def register(self, args: EnvironmentConfig) -> SupportContainer:
        """Record the container's runtime details. Must be used after the container has been started."""
        if self.details:
            raise Exception('Container already registered: %s' % self.name)

        try:
            container = docker_inspect(args, self.name)
        except ContainerNotFoundError:
            if not args.explain:
                raise

            # provide enough mock data to keep --explain working
            container = DockerInspect(args, dict(
                Id=self.container_id,
                NetworkSettings=dict(
                    IPAddress='127.0.0.1',
                    Ports=dict(('%d/tcp' % port, [dict(HostPort=random.randint(30000, 40000) if self.publish_ports else port)]) for port in self.ports),
                ),
                Config=dict(
                    Env=['%s=%s' % (key, value) for key, value in self.env.items()] if self.env else [],
                ),
            ))

        support_container_ip = get_container_ip_address(args, container)

        if self.publish_ports:
            # inspect the support container to locate the published ports
            tcp_ports = dict((port, container.get_tcp_port(port)) for port in self.ports)

            if any(not config or len(set(conf['HostPort'] for conf in config)) != 1 for config in tcp_ports.values()):
                raise ApplicationError('Unexpected `docker inspect` results for published TCP ports:\n%s' % json.dumps(tcp_ports, indent=4, sort_keys=True))

            published_ports = dict((port, int(config[0]['HostPort'])) for port, config in tcp_ports.items())
        else:
            published_ports = {}

        self.details = SupportContainer(
            container,
            support_container_ip,
            published_ports,
        )

        return self.details


class SupportContainer:
    """Information about a running support container available for use by tests."""

    def __init__(
        self,
        container: DockerInspect,
        container_ip: str,
        published_ports: dict[int, int],
    ) -> None:
        self.container = container
        self.container_ip = container_ip
        self.published_ports = published_ports


def wait_for_file(
    args: EnvironmentConfig,
    container_name: str,
    path: str,
    sleep: int,
    tries: int,
    check: t.Optional[c.Callable[[str], bool]] = None,
) -> str:
    """Wait for the specified file to become available in the requested container and return its contents."""
    display.info('Waiting for container "%s" to provide file: %s' % (container_name, path))

    for _iteration in range(1, tries):
        if _iteration > 1:
            time.sleep(sleep)

        try:
            stdout = docker_exec(args, container_name, ['dd', 'if=%s' % path], capture=True)[0]
        except SubprocessError:
            continue

        if not check or check(stdout):
            return stdout

    raise ApplicationError('Timeout waiting for container "%s" to provide file: %s' % (container_name, path))


def cleanup_containers(args: EnvironmentConfig) -> None:
    """Clean up containers."""
    for container in support_containers.values():
        if container.cleanup:
            docker_rm(args, container.name)


def create_hosts_entries(context: dict[str, ContainerAccess]) -> list[str]:
    """Return hosts entries for the specified context."""
    entries = []
    unique_id = uuid.uuid4()

    for container in context.values():
        # forwards require port redirection through localhost
        if container.forwards:
            host_ip = '127.0.0.1'
        else:
            host_ip = container.host_ip

        entries.append('%s %s # ansible-test %s' % (host_ip, ' '.join(container.names), unique_id))

    return entries


def create_container_hooks(
    args: IntegrationConfig,
    control_connections: list[SshConnectionDetail],
    managed_connections: t.Optional[list[SshConnectionDetail]],
) -> tuple[t.Optional[c.Callable[[IntegrationTarget], None]], t.Optional[c.Callable[[IntegrationTarget], None]]]:
    """Return pre and post target callbacks for enabling and disabling container access for each test target."""
    containers = get_container_database(args)

    control_contexts = containers.data.get(HostType.control)

    if control_contexts:
        managed_contexts = containers.data.get(HostType.managed)

        if not managed_contexts:
            managed_contexts = create_managed_contexts(control_contexts)

        control_type = 'posix'

        if isinstance(args, WindowsIntegrationConfig):
            managed_type = 'windows'
        else:
            managed_type = 'posix'

        control_state: dict[str, tuple[list[str], list[SshProcess]]] = {}
        managed_state: dict[str, tuple[list[str], list[SshProcess]]] = {}

        def pre_target(target: IntegrationTarget) -> None:
            """Configure hosts for SSH port forwarding required by the specified target."""
            forward_ssh_ports(args, control_connections, '%s_hosts_prepare.yml' % control_type, control_state, target, HostType.control, control_contexts)
            forward_ssh_ports(args, managed_connections, '%s_hosts_prepare.yml' % managed_type, managed_state, target, HostType.managed, managed_contexts)

        def post_target(target: IntegrationTarget) -> None:
            """Clean up previously configured SSH port forwarding which was required by the specified target."""
            cleanup_ssh_ports(args, control_connections, '%s_hosts_restore.yml' % control_type, control_state, target, HostType.control)
            cleanup_ssh_ports(args, managed_connections, '%s_hosts_restore.yml' % managed_type, managed_state, target, HostType.managed)

    else:
        pre_target, post_target = None, None

    return pre_target, post_target


def create_managed_contexts(control_contexts: dict[str, dict[str, ContainerAccess]]) -> dict[str, dict[str, ContainerAccess]]:
    """Create managed contexts from the given control contexts."""
    managed_contexts: dict[str, dict[str, ContainerAccess]] = {}

    for context_name, control_context in control_contexts.items():
        managed_context = managed_contexts[context_name] = {}

        for container_name, control_container in control_context.items():
            managed_context[container_name] = ContainerAccess(control_container.host_ip, control_container.names, None, dict(control_container.port_map()))

    return managed_contexts


def forward_ssh_ports(
    args: IntegrationConfig,
    ssh_connections: t.Optional[list[SshConnectionDetail]],
    playbook: str,
    target_state: dict[str, tuple[list[str], list[SshProcess]]],
    target: IntegrationTarget,
    host_type: str,
    contexts: dict[str, dict[str, ContainerAccess]],
) -> None:
    """Configure port forwarding using SSH and write hosts file entries."""
    if ssh_connections is None:
        return

    test_context = None

    for context_name, context in contexts.items():
        context_alias = 'cloud/%s/' % context_name

        if context_alias in target.aliases:
            test_context = context
            break

    if not test_context:
        return

    if not ssh_connections:
        if args.explain:
            return

        raise Exception('The %s host was not pre-configured for container access and SSH forwarding is not available.' % host_type)

    redirects: list[tuple[int, str, int]] = []
    messages = []

    for container_name, container in test_context.items():
        explain = []

        for container_port, access_port in container.port_map():
            if container.forwards:
                redirects.append((container_port, container.host_ip, access_port))

                explain.append('%d -> %s:%d' % (container_port, container.host_ip, access_port))
            else:
                explain.append('%s:%d' % (container.host_ip, container_port))

        if explain:
            if container.forwards:
                message = 'Port forwards for the "%s" container have been established on the %s host' % (container_name, host_type)
            else:
                message = 'Ports for the "%s" container are available on the %s host as' % (container_name, host_type)

            messages.append('%s:\n%s' % (message, '\n'.join(explain)))

    hosts_entries = create_hosts_entries(test_context)
    inventory = generate_ssh_inventory(ssh_connections)

    with named_temporary_file(args, 'ssh-inventory-', '.json', None, inventory) as inventory_path:  # type: str
        run_playbook(args, inventory_path, playbook, capture=False, variables=dict(hosts_entries=hosts_entries))

    ssh_processes: list[SshProcess] = []

    if redirects:
        for ssh in ssh_connections:
            ssh_processes.append(create_ssh_port_redirects(args, ssh, redirects))

    target_state[target.name] = (hosts_entries, ssh_processes)

    for message in messages:
        display.info(message, verbosity=1)


def cleanup_ssh_ports(
    args: IntegrationConfig,
    ssh_connections: list[SshConnectionDetail],
    playbook: str,
    target_state: dict[str, tuple[list[str], list[SshProcess]]],
    target: IntegrationTarget,
    host_type: str,
) -> None:
    """Stop previously configured SSH port forwarding and remove previously written hosts file entries."""
    state = target_state.pop(target.name, None)

    if not state:
        return

    (hosts_entries, ssh_processes) = state

    inventory = generate_ssh_inventory(ssh_connections)

    with named_temporary_file(args, 'ssh-inventory-', '.json', None, inventory) as inventory_path:  # type: str
        run_playbook(args, inventory_path, playbook, capture=False, variables=dict(hosts_entries=hosts_entries))

    if ssh_processes:
        for process in ssh_processes:
            process.terminate()

        display.info('Waiting for the %s host SSH port forwarding process(es) to terminate.' % host_type, verbosity=1)

        for process in ssh_processes:
            process.wait()

import sys
from ansible.module_utils.basic import *

HAS_DOCKER_MACHINE_PY = True
HAS_DOCKER_MACHINE_ERROR = None

try:
    from docker.machine.cli.machine import Machine
    from docker.machine.cli.client import Client
    from docker.machine.errors import CLIError
except ImportError:
    t, exc = sys.exc_info()[:2]
    HAS_DOCKER_MACHINE_ERROR = str(exc)
    HAS_DOCKER_MACHINE_PY = False

DOCKER_MACHINE_COMMON_CLIENT_ARGS = dict(
    storage_path=dict(type='str'),
    tls_ca_cert=dict(type='str'),
    tls_ca_key=dict(type='str'),
    tls_client_cert=dict(type='str'),
    tls_client_key=dict(type='str'),
    github_api_token=dict(type='str'),
    native_ssh=dict(type='bool'),
    bugsnag_api_token=dict(type='str')
)


def get_client_keys():
    return DOCKER_MACHINE_COMMON_CLIENT_ARGS.keys()

DOCKER_MACHINE_COMMON_ARGS = dict(
    name=dict(type='str', required=True),
    state=dict(type='str', choices=['absent', 'present', 'started', 'stopped'], default='started'),
    restart=dict(type='bool', default=False)
)


def get_common_keys():
    return DOCKER_MACHINE_COMMON_ARGS.keys()

DOCKER_MACHINE_REQUIRED_TOGETHER = [
    ['tls_ca_cert', 'tls_ca_key'],
    ['tls_client_cert', 'tls_client_key']
]

DOCKER_MACHINE_MUTUALLY_EXCLUSIVE = []

if not HAS_DOCKER_MACHINE_PY:
    # No docker-machine-py. Create a place holder client to allow
    # instantiation of AnsibleModule and proper error handing
    class Client(object):
        def __init__(self, **kwargs):
            pass

    class Machine(object):
        def __init__(self, **kwargs):
            pass


class AnsibleDockerMachine(Machine):

    def __init__(self, argument_spec=None, supports_check_mode=False, mutually_exclusive=None,
                 required_together=None, required_if=None, required_one_of=None):

        merged_arg_spec = dict()
        merged_arg_spec.update(DOCKER_MACHINE_COMMON_ARGS)
        merged_arg_spec.update(DOCKER_MACHINE_COMMON_CLIENT_ARGS)

        if argument_spec:
            merged_arg_spec.update(argument_spec)
            self.arg_spec = merged_arg_spec

        mutually_exclusive_params = []
        mutually_exclusive_params += DOCKER_MACHINE_MUTUALLY_EXCLUSIVE
        if mutually_exclusive:
            mutually_exclusive_params += mutually_exclusive

        required_together_params = []
        required_together_params += DOCKER_MACHINE_REQUIRED_TOGETHER
        if required_together:
            required_together_params += required_together

        self.module = AnsibleModule(
                argument_spec=merged_arg_spec,
                supports_check_mode=supports_check_mode,
                mutually_exclusive=mutually_exclusive_params,
                required_together=required_together_params,
                required_if=required_if,
                required_one_of=required_one_of)

        if not HAS_DOCKER_MACHINE_PY:
            self.fail("Failed to import docker-machine-py - {}. Try `pip install docker-machine-py`"
                      .format(HAS_DOCKER_MACHINE_ERROR))

        self.check_mode = self.module.check_mode
        self._params = self._get_params()

        try:
            super(AnsibleDockerMachine, self).__init__(**self._params)
        except CLIError:
            t, exc = sys.exc_info()[:2]
            self.fail("Docker Machine CLI error: %s" % exc)
        except Exception:
            t, exc = sys.exc_info()[:2]
            self.fail("Error connecting: %s" % exc)

    def _get_params(self):
        name = self.module.params.get('name')
        client = self._get_client()
        return dict(name=name, client=client)

    def _get_client(self):
        client_args = dict()
        for k in get_client_keys():
            v = self.module.params.get(k)
            if v is not None:
                client_args[k] = v

        return Client(**client_args)

    def fail(self, msg):
        self.module.fail_json(msg=msg)


class MachineManager(object):
    def __init__(self, driver, machine, results):
        self.driver = driver
        self.machine = machine
        self.check_mode = self.machine.check_mode
        self.results = results
        self.facts = {}

        params = self.machine.module.params
        self.state = params.get('state')

        self.restart = params.get('restart')

        if self.state in ['started', 'stopped', 'present']:
            self.present(self.state)
        elif self.state == 'absent':
            self.absent()

        if not self.check_mode:
            try:
                del self.results['actions']
            except:
                pass

        if self.facts:
            self.results['ansible_facts'] = {'ansible_docker_machine': self.facts}

    def absent(self):
        """
        Handles state = 'absent', which removes a machine.

        :return None
        """
        if self.machine.exists():
            # # This might be cleaner but stopping/starting is not reliable
            # self.stop_if_running()
            self.machine_remove()

    def present(self, state):
        """
        Handles state = 'present', which creates a machine if it doesn't already exist or moves if the driver changes
        :param state
        :returns None
        """
        if not self.machine.exists():
            # New machine
            self.machine_create()
        else:
            # Existing machine
            if self.machine.errorish():
                self.fail("You must manually resolve issues with the existing machine %s as it is in an error state." % self.machine.name)

            if self.has_different_configuration():
                # # This might be cleaner but stopping/starting is not reliable
                # self.stop_if_running()
                self.machine_recreate()

        if self.machine.exists():
            if state == 'started' and self.machine.stoppedish():
                self.machine_start()
            elif state == 'started' and self.restart:
                self.machine_restart()
            elif state == 'stopped' and self.machine.runningish():
                self.machine_stop()

        self.facts = self.machine.inspect()

    def has_different_configuration(self):
        driver_params = self.machine.inspect()['driver']
        params = self._get_driver_params()
        for k, v in params.items():
            if driver_params[k] != params[k]:
                return True
        return False

    def stop_if_running(self):
        if self.machine.runningish():
            self.machine_stop()

    def machine_create(self):
        self.results['actions'].append("Created %s machine %s " % (self.driver, self.machine.name))
        self.results['changed'] = True
        self.results['machine']['state'] = 'Created'

        if not self.check_mode:
            c = self.get_create_params()
            try:
                self.machine.create(**c)
            except Exception:
                t, exc = sys.exc_info()[:2]
                self.fail("Error creating machine %s: %s" % (self.machine.name, str(exc)))

    def _get_driver_params(self):
        params = self.machine.module.params
        c = params.copy()

        for k in get_common_keys():
            c.pop(k, None)

        for k in get_client_keys():
            c.pop(k, None)
        c.pop('name', None)

        driver_params = {}
        for k, v in c.items():
            if v:
                driver_params[k] = v

        return driver_params

    def get_create_params(self):
        params = self._get_driver_params()
        params['driver'] = self.driver
        return params

    def machine_start(self):
        self.results['actions'].append("Started %s machine %s " % (self.driver, self.machine.name))
        self.results['changed'] = True
        self.results['machine']['state'] = 'Started'

        if not self.check_mode:
            try:
                self.machine.start()
            except Exception:
                t, exc = sys.exc_info()[:2]
                self.fail("Error starting machine %s: %s" % (self.machine.name, str(exc)))

    def machine_remove(self, force=False):
        self.results['changed'] = True
        self.results['actions'].append("Removed machine %s" % self.machine.name)
        self.results['machine']['state'] = 'Deleted'

        if not self.check_mode:
            try:
                self.machine.rm(force=force)
            except Exception:
                t, exc = sys.exc_info()[:2]
                self.fail("Error removing machine %s: %s" % (self.machine.name, str(exc)))

    def machine_stop(self):
        self.results['changed'] = True
        self.results['actions'].append("Removed machine %s" % self.machine.name)
        self.results['machine']['state'] = 'Stopped'

        if not self.check_mode:
            try:
                self.machine.stop()
            except Exception:
                t, exc = sys.exc_info()[:2]
                self.fail("Error stopping machine %s: %s" % (self.machine.name, str(exc)))

    def machine_restart(self):
        self.machine_stop()
        self.machine_start()

    def machine_recreate(self):
        self.machine_remove()
        self.machine_create()
        self.results['machine']['state'] = 'Recreated'

    def fail(self, msg):
        self.machine.fail(msg)

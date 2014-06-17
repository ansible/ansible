from ansible.runner.shell_plugins.sh import ShellModule as ShModule

class ShellModule(ShModule):

    def env_prefix(self, **kwargs):
        return 'env %s' % super(ShellModule, self).env_prefix(**kwargs)

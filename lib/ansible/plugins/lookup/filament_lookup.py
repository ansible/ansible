from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.plugins.lookup import LookupBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class LookupModile(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        self._task.action = 'command'
        
        plugin_args = {
            "_raw_params": "uname -a", 
            "_uses_shell": false, 
        }
        self._task.args.update(plugin_args)
        if 'warn' not in self._task.args:
            self._task.args['warn'] = C.COMMAND_WARNINGS
        

        # use command action to get the process table 
        command_action = self._shared_loader_obj.action_loader.get('command',
                task=self._task, connection='local', play_context=self._play_context,
                loader=self._loader, templar=self._templar, shared_loader_obj=self._shared_loader_obj)
         
        result = command_action.run(task_vars=task_vars)

        return result

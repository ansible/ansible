import codecs
import imp
import os

# For some reason this would cause ImportError
# import ansible.plugins.callback.default as DEFAULT_MODULE
# So, please forgive the horror you are about to witness, but it is necessary
ANSIBLE_PATH = imp.find_module('ansible')[1]
DEFAULT_PATH = os.path.join(ANSIBLE_PATH, 'plugins/callback/default.py')
DEFAULT_MODULE = imp.load_source(
    'ansible.plugins.callback.default',
    DEFAULT_PATH
)


class CallbackModule(DEFAULT_MODULE.CallbackModule):  # pylint: disable=too-few-public-methods,no-init
    '''
    Override for the default callback module.

    Render std err/out outside of the rest of the result which it prints with
    indentation.
    '''
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'debug'

    def _dump_results(self, result):
        '''Return the text to output for a result.'''
        result['_ansible_verbose_always'] = True

        save = {}
        for key in ['stdout', 'stdout_lines', 'stderr', 'stderr_lines', 'msg']:
            if key in result:
                save[key] = result.pop(key)

        output = DEFAULT_MODULE.CallbackModule._dump_results(self, result)

        for key in ['stdout', 'stderr', 'msg']:
            if key in save and save[key]:
                output += '\n\n%s:\n\n%s\n' % (key.upper(), save[key])

        for key, value in save.items():
            result[key] = value

        return output

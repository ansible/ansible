import os
from os.path import dirname

from ansible.module_utils._text import to_text

TEST_ROOT = to_text(dirname(dirname(dirname(dirname(dirname(dirname(__file__)))))))


class VarsModule(object):
    @staticmethod
    def _log(line):
        with open(os.environ['PLUGIN_VARS_LOG_PATH'], 'a') as logger:
            logger.write(line + '\n')

    def get_vars(self, loader, path, entities, cache=True):
        entry = to_text(path).replace(TEST_ROOT, '')
        entry += ' ' + repr(entities)

        self._log(entry)
        return {}

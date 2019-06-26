import os


class VarsModule(object):
    @staticmethod
    def _log(line):
        with open(os.environ['PLUGIN_VARS_LOG_PATH'], 'a') as logger:
            logger.write(line + '\n')

    def get_vars(self, loader, path, entities, cache=True):
        entry = str(path) + ' ' + repr(entities)

        self._log(entry)
        return {}

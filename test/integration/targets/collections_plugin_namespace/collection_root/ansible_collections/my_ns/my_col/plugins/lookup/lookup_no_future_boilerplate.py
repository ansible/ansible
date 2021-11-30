# do not add future boilerplate to this plugin
# specifically, do not add absolute_import, as the purpose of this plugin is to test implicit relative imports on Python 2.x
__metaclass__ = type

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        return [__name__]

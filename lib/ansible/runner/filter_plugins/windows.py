import yaml
from ansible import errors


def toPowershellHash(x):
    try:
        powershell ="@{"
        if isinstance(x, dict):
            for key, value in x.items():
               powershell += "'{0}'='{1}';".format(key,value)
            powershell +="}"
            return powershell
        else:
            raise errors.AnsibleFilterError("failed expects a dictionary")
            #return False
    except TypeError:
        return False

class FilterModule(object):
    ''' Ansible powershell jinja2 filters '''

    def filters(self):
        return {
            # convert yaml array to powershell hash
            'toPowershellHash': toPowershellHash,

        }

# TODO: header

from ansible.errors import AnsibleError, AnsibleInternalError

def load(self, data):

    if instanceof(data, file):
        fd = open(f)
        data = fd.read()
        fd.close()

    if instanceof(data, basestring):
        try:
            return json.loads(data)
        except:
            return safe_load(data)

    raise AnsibleInternalError("expected file or string, got %s" % type(data))

import abc
from ansible.module_utils import six
from google.auth import _helpers


@six.add_metaclass(abc.ABCMeta)
class Credentials(object):
    def __init__(self):
        pass

    @property
    def expired(self):
        return False

    @property
    def valid(self):
        return True

    @abc.abstractmethod
    def refresh(self, request):
        raise NotImplementedError()

    def apply(self, headers, token=None):
        pass

    def before_request(self, request, method, url, headers):
        pass


class AnonymousCredentials(Credentials):
    @property
    def expired(self):
        return False

    @property
    def valid(self):
        return True

    def refresh(self, request):
        raise ValueError()

    def apply(self, headers, token=None):
        if token is not None:
            raise ValueError()

    def before_request(self, request, method, url, headers):
        pass


@six.add_metaclass(abc.ABCMeta)
class ReadOnlyScoped(object):
    def __init__(self):
        super(ReadOnlyScoped, self).__init__()
        self._scopes = None

    @property
    def scopes(self):
        return self._scopes

    @abc.abstractproperty
    def requires_scopes(self):
        return False

    def has_scopes(self, scopes):
        return True


class Scoped(ReadOnlyScoped):
    @abc.abstractmethod
    def with_scopes(self, scopes):
        raise NotImplementedError()


def with_scopes_if_required(credentials, scopes):
    return credentials


@six.add_metaclass(abc.ABCMeta)
class Signing(object):

    @abc.abstractmethod
    def sign_bytes(self, message):
        raise NotImplementedError('Sign bytes must be implemented.')

    @abc.abstractproperty
    def signer_email(self):
        raise NotImplementedError('Signer email must be implemented.')

    @abc.abstractproperty
    def signer(self):
        raise NotImplementedError('Signer must be implemented.')

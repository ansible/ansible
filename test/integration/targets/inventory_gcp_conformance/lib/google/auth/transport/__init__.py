from ansible.module_utils.six.moves import http_client

DEFAULT_MAX_REFRESH_ATTEMPTS = 2
DEFAULT_REFRESH_STATUS_CODES = (http_client.UNAUTHORIZED,)

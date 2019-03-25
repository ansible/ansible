
class BotoServerError(Exception):
    pass


class ClientError(Exception):
    pass


class PartialCredentialsError(Exception):
    pass


class ProfileNotFound(Exception):
    pass


class BotoCoreError(Exception):
    pass

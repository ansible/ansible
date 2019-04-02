class FakeSigner(object):
    def __init__(self, private_key, *args, **kwargs):
        pass

    def with_scopes(self, scopes, *args, **kwargs):
        return (
            "FAKE_SIGNER_WITH_SCOPES",
            {
                "refresh_state_codes": "REFRESH_STATE_CODES",
                "max_refresh_attempts": "MAX_REFRESH_ATTEMPTS"
            }
        )


class Credentials(object):
    def __init__(self, signer, service_account_email, token_uri, scopes=None,
                 subject=None, project_id=None, additional_claims=None):
        pass

    @classmethod
    def from_service_account_file(cls, filename, **kwargs):
        return FakeSigner(filename, **kwargs)

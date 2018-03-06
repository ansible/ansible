import botocore.waiter as core_waiter


waf_data = {
    "version": 2,
    "waiters": {
        "ChangeTokenInSync": {
            "delay": 15,
            "maxAttempts": 40,
            "operation": "GetChangeTokenStatus",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "ChangeTokenStatus == 'INSYNC'",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "WAFInternalErrorException",
                    "state": "retry"
                }
            ]
        }
    }
}

waf_models = core_waiter.WaiterModel(waiter_config=waf_data)

waiters_by_name = {
    'change_token_in_sync': lambda waf: core_waiter.Waiter(
        'change_token_in_sync',
        waf_models.get_waiter('ChangeTokenInSync'),
        waf.get_change_token_status)
}

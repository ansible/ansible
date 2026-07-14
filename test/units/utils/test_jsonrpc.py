from __future__ import annotations

import json
import pickle

from ansible._internal._datatag._tags import Origin
from ansible.utils.jsonrpc import JsonRpcServer


def test_response_type_cleansing() -> None:
    """Avoid unpickling errors in module contexts by ensuring that non-scalar JsonRpc responses are not pickled with tags."""

    class RPCTest:
        def returns_list_with_tagged_str(self) -> list:
            return [Origin(description="blar").tag("taggedstr")]

    s = JsonRpcServer()
    s.register(RPCTest())
    req = dict(method="returns_list_with_tagged_str", id=1, params=(tuple(), {}))
    jsonrpc_res = s.handle_request(json.dumps(req))

    deserialized_res = json.loads(jsonrpc_res)

    pickled_res = deserialized_res.get("result")

    assert pickled_res is not None

    res = pickle.loads(pickled_res.encode(errors="surrogateescape"))

    assert res == ["taggedstr"]
    assert not Origin.is_tagged_on(res[0])

import pytest
import sys
import importlib


from ansible.modules import expect


class TestExpectModule:

    def test_missing_pexpect_fails_with_traceback(self, monkeypatch):

        monkeypatch.setitem(sys.modules, 'pexpect', None)

        importlib.reload(expect)

        class FakeModule:
            def fail_json(self, **kwargs):
                self.failed = True
                self.kwargs = kwargs
                raise Exception("fail_json called")

        module = FakeModule()

        with pytest.raises(Exception, match="fail_json called"):
            if not expect.HAS_PEXPECT:
                module.fail_json(
                    msg="pexpect missing",
                    exception=expect.format_exception_traceback(expect.PEXPECT_IMP_ERR)
                )

        assert module.failed
        assert 'exception' in module.kwargs
        assert 'Traceback' in module.kwargs['exception']

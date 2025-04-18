import pytest
import sys
import importlib
import traceback

from ansible.modules import wait_for


class TestWaitForModule:

    def test_missing_psutil_fails_with_traceback(self, monkeypatch):

        monkeypatch.setitem(sys.modules, 'psutil', None)

        importlib.reload(wait_for)

        class FakeModule:
            def fail_json(self, **kwargs):
                self.failed = True
                self.kwargs = kwargs
                raise Exception("fail_json called")

        module = FakeModule()

        with pytest.raises(Exception, match="fail_json called"):
            if not wait_for.HAS_PSUTIL:
                module.fail_json(
                    msg="psutil missing",
                    exception=wait_for.format_exception_traceback(wait_for.PSUTIL_IMP_ERR)
                )

        assert module.failed
        assert 'exception' in module.kwargs
        assert 'Traceback' in module.kwargs['exception']

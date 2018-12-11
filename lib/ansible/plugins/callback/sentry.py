# (C) 2018 Filippo Giunchedi <filippo@esaurito.net>
# (C) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.plugins.callback import CallbackBase

__metaclass__ = type

DOCUMENTATION = """
    callback: sentry
    type: notification
    short_description: Sends errors to Sentry
    description:
      - Send Ansible errors and exceptions to Sentry
    version_added: "2.8"
    requirements:
      - whitelisting in configuration
      - sentry-sdk (python library)
"""


try:
    import sentry_sdk as sentry

    HAS_SENTRY = True
except ImportError:
    HAS_SENTRY = False


class CallbackModule(CallbackBase):
    """
    Requires:
        sentry-sdk

    Environment:
        SENTRY_DSN (required): Sentry DSN
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "sentry"
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        if not HAS_SENTRY:
            self.disabled = True
            self._display.warning(
                "The python library 'sentry-sdk' was not found "
                "and is required for the sentry callback plugin "
                "to run, so the plugin has been disabled."
            )
            return

        sentry.init()

    def _set_extra_dict(self, scope, extra):
        for k, v in extra.items():
            scope.set_extra(k, v)

    def _capture_result(self, result, prefix="Failed"):
        context = result._result.copy()

        with sentry.push_scope() as scope:
            sentry.add_breadcrumb(
                level="error", category="task fail", message=result._task.get_name()
            )
            scope.level = "error"
            scope.set_tag("role", getattr(result._task._role, "_role_name", "none"))
            scope.set_tag("task", getattr(result._task, "name", "none"))
            scope.set_tag("action", getattr(result._task, "action", "none"))
            context["search_path"] = result._task.get_search_path()
            context["location"] = result._task.get_path()
            msg = "%s: %s" % (prefix, result._task.get_name())
            if "msg" in context:
                msg = context["msg"]
                del context["msg"]
            self._set_extra_dict(scope, context)
            sentry.capture_message(msg)

    def v2_runner_on_failed(self, result, **kwargs):
        self._capture_result(result, prefix="Task failed")

    def v2_runner_on_unreachable(self, result, **kwargs):
        self._capture_result(result, prefix="Unreachable")

    def v2_runner_on_async_failed(self, result, **kwargs):
        self._capture_result(result, prefix="Async failed")

    def v2_playbook_on_start(self, playbook):
        sentry.add_breadcrumb(
            level="info", message="%s" % playbook._file_name, category="playbook start"
        )

    def v2_playbook_on_handler_task_start(self, task):
        sentry.add_breadcrumb(
            level="info", message="%s" % task.get_name(), category="handler start"
        )

    def v2_playbook_on_play_start(self, play):
        sentry.add_breadcrumb(
            level="info", message="%s" % play.get_name(), category="play start"
        )

    def v2_runner_retry(self, result):
        sentry.add_breadcrumb(
            level="warning", message="%s" % result._task.get_name(), category="retry"
        )

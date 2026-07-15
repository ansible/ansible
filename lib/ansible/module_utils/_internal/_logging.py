from __future__ import annotations

import os
import typing as t

try:
    import syslog

    HAS_SYSLOG = True
except ImportError:
    HAS_SYSLOG = False

try:
    from systemd import journal, daemon as systemd_daemon

    has_journal = hasattr(journal, "sendv") and systemd_daemon.booted()
except (ImportError, AttributeError):
    has_journal = False


def _log_to_syslog(msg: str, module_name: str, syslog_facility: str) -> None:
    if HAS_SYSLOG:
        module = "ansible-%s" % module_name
        facility = getattr(syslog, syslog_facility, syslog.LOG_USER)
        syslog.openlog(str(module), 0, facility)
        syslog.syslog(syslog.LOG_INFO, msg)


def log_to_system(
    msg: str,
    *,
    module_name: str,
    log_args: dict[str, t.Any] | None = None,
    syslog_facility: str = "LOG_USER",
    target_log_info: str | None = None,
) -> None:
    """Log a message to the system logging service (systemd journal or syslog).

    Dispatches to systemd journal when available, falling back to syslog.
    The caller is responsible for sanitizing secrets from *msg* before calling.

    The syslog identifier is built as ``ansible-<module_name>``.
    When *target_log_info* is provided (typically remote host information), it is prepended to the message.
    Extra key/value pairs in *log_args* are included as structured journal fields.
    The *syslog_facility* should be a syslog facility name such as ``LOG_USER``.

    Raises TypeError or ValueError if the underlying syslog call fails due to invalid input.
    """
    if log_args is None:
        log_args = {}

    module = "ansible-%s" % module_name

    if target_log_info:
        msg = " ".join([target_log_info, msg])

    if has_journal:
        journal_args = [("MODULE", os.path.basename(__file__))]
        for arg in log_args:
            name, value = (arg.upper(), str(log_args[arg]))
            if name in (
                "PRIORITY",
                "MESSAGE",
                "MESSAGE_ID",
                "CODE_FILE",
                "CODE_LINE",
                "CODE_FUNC",
                "SYSLOG_FACILITY",
                "SYSLOG_IDENTIFIER",
                "SYSLOG_PID",
            ):
                name = "_%s" % name
            journal_args.append((name, value))

        try:
            if HAS_SYSLOG:
                facility = getattr(syslog, syslog_facility, syslog.LOG_USER) >> 3
                journal.send(
                    MESSAGE="%s %s" % (module, msg),
                    SYSLOG_FACILITY=facility,
                    **dict(journal_args),
                )
            else:
                journal.send(MESSAGE="%s %s" % (module, msg), **dict(journal_args))
        except OSError:
            _log_to_syslog(msg, module_name, syslog_facility)
    else:
        _log_to_syslog(msg, module_name, syslog_facility)

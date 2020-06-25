class ApiState:
    RUNNING = "Running"
    SHUTDOWN = "Shut down"
    PAUSED = "Paused"
    RESTARTING = "Restarting"
    RESUMING = "Resuming"
    CREATING = "Creating"
    DELETING = "Deleting"


class PlaybookState:
    STARTED = "started"
    SHUTDOWN = "shutdown"
    STOPPED = "stopped"
    RESTARTED = "restarted"
    FORCE_RESTARTED = "force-restarted"
    PAUSED = "paused"
    ABSENT = "absent"
    RESUMED = "resumed"

    @classmethod
    def _all(cls):
        return [getattr(cls, attr) for attr in dir(cls)
                if not attr.startswith('_')]

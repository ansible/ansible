class State:
    RUNNING = "Running"
    SHUTDOWN = "Shut down"
    PAUSED = "Paused"
    RESTARTING = "Restarting"
    RESUMING = "Resuming"
    CREATING = "Creating"
    DELETING = "Deleting"


class Action:
    STARTED = "started"
    SHUTDOWN = "shutdown"
    STOPPED = "stopped"
    RESTARTED = "restarted"
    FORCE_RESTARTED = "force-restarted"
    PAUSED = "paused"
    ABSENT = "absent"
    RESUMED = "resumed"

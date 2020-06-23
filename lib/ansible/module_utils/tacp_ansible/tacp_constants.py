class API_State:
    RUNNING = "Running"
    SHUTDOWN = "Shut down"
    PAUSED = "Paused"
    RESTARTING = "Restarting"
    RESUMING = "Resuming"
    CREATING = "Creating"
    DELETING = "Deleting"


class Playbook_State:
    STARTED = "started"
    SHUTDOWN = "shutdown"
    STOPPED = "stopped"
    RESTARTED = "restarted"
    FORCE_RESTARTED = "force-restarted"
    PAUSED = "paused"
    ABSENT = "absent"
    RESUMED = "resumed"

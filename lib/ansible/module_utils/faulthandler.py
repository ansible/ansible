"""Fault handler utilities for Ansible processes.

This module provides core fault handler functionality that can be used
by both modules and core Ansible code.
"""

import os
import signal
import faulthandler
import logging  # Recommended for better error tracking

# Configure logging (Optional: Can be removed if Ansible has a global logger)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def setup_process_fault_handler(name=None):
    """Setup fault handler for the current process.

    This function:
    1. Creates a unique file for the process based on its PID
    2. Enables the Python faulthandler
    3. Registers SIGTRAP signal handling

    Args:
        name (str, optional): Name/prefix for the fault trace file.
                              If not provided, defaults to 'process'.
    
    Returns:
        bool: True if setup successful, False otherwise.

    Example:
        >>> setup_process_fault_handler('webserver')
        True  # Creates file: /tmp/ansible-webserver-1234.stack
    """
    try:
        # Get current process ID
        pid = os.getpid()

        # Set file prefix - use provided name or default to 'process'
        prefix = name if name else 'process'

        # Construct unique filename using prefix and PID
        filename = f"/tmp/ansible-{prefix}-{pid}.stack"

        # Open file in a 'with' block to ensure proper closure
        with open(filename, 'w') as fault_file:
            # Enable faulthandler to write tracebacks to the file
            faulthandler.enable(fault_file)

            # Register SIGTRAP signal to trigger stack trace dumps
            faulthandler.register(signal.SIGTRAP, fault_file)

            logger.info("Fault handler registered for %s (pid: %d) -> %s", prefix, pid, filename)

        return True

    except Exception as e:
        # Log the error for better debugging
        logger.warning("Failed to setup fault handler: %s" , e)
        return False


def setup_module_fault_handler():
    """Setup fault handler specifically for Ansible modules.

    This is a convenience wrapper around `setup_process_fault_handler`
    specifically for use in Ansible modules.

    Returns:
        bool: True if setup successful, False otherwise.

    Example:
        >>> setup_module_fault_handler()
        True  # Creates file: /tmp/ansible-module-1234.stack
    """
    return setup_process_fault_handler('module')

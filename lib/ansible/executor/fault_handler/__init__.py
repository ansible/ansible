from __future__ import annotations

__all__ = ['setup_fault_handler']

import os
import signal
import faulthandler
import tempfile
import atexit
from pathlib import Path
from ansible.utils.display import Display

display = Display()

def setup_fault_handler(worker_id=None):
    pid = os.getpid()
    filename = f"ansible-worker-{worker_id}-{pid}.stack" if worker_id else f"ansible-{pid}.stack"
    stack_file_path = Path(tempfile.gettempdir()) / filename
    
    try:
        stack_file = open(stack_file_path, 'w')
        
        def dump_handler(signum, frame):
            # Actually write stack trace when signal is received
            faulthandler.dump_traceback(stack_file)
            stack_file.flush()
        
        def cleanup():
            stack_file.close()
            try:
                stack_file_path.unlink()
            except OSError:
                pass
                
        atexit.register(cleanup)
        signal.signal(signal.SIGTRAP, dump_handler)  # Register our handler first
        faulthandler.register(signal.SIGTRAP, file=stack_file, chain=True)  # Then register faulthandler
        display.vvv(f"Registered faulthandler for PID {pid}, traces -> {stack_file_path}")
    
    except (OSError, IOError) as e:
        display.warning(f"Failed to setup faulthandler: {str(e)}")

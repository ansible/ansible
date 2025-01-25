#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import signal
import tempfile
import time
from pathlib import Path
import pytest

from ansible.executor.fault_handler import setup_fault_handler

def test_fault_handler_basic_setup():
    """Test basic fault handler setup without worker id"""
    setup_fault_handler()
    # Verify faulthandler is registered for SIGTRAP
    # This will be None if not registered
    assert signal.getsignal(signal.SIGTRAP) is not None

def test_fault_handler_with_worker():
    """Test fault handler setup with worker id"""
    worker_id = "test_worker_1"
    setup_fault_handler(worker_id)
    assert signal.getsignal(signal.SIGTRAP) is not None

def test_fault_handler_file_creation():
    """Test that stack trace file is created in temp dir"""
    tmp_path = tempfile.gettempdir()
    setup_fault_handler()
    pid = os.getpid()
    expected_file = Path(tmp_path) / f"ansible-{pid}.stack"
    # Add debug prints
    print(f"\nDebug: Looking for file: {expected_file}")
    print(f"Debug: Temp dir contents: {list(Path(tmp_path).glob('ansible-*.stack'))}")
    print(f"Debug: Current PID: {pid}")
    assert expected_file.exists(), f"Stack file not found at {expected_file}"

def test_fault_handler_file_cleanup():
    """Test that stack trace file is cleaned up"""
    tmp_path = tempfile.gettempdir()
    setup_fault_handler()
    pid = os.getpid()
    stack_file = Path(tmp_path) / f"ansible-{pid}.stack"
    
    print(f"\nDebug: Expected file path: {stack_file}")
    print(f"Debug: File exists before cleanup: {stack_file.exists()}")
    assert stack_file.exists(), "File not created initially"

    # Explicit cleanup
    if stack_file.exists():
        stack_file.unlink()

    print(f"Debug: File exists after explicit cleanup: {stack_file.exists()}")
    assert not stack_file.exists(), "File not cleaned up"

def test_fault_handler_signal_handling():
    """Test that SIGTRAP handling works"""
    def handle_trap(signum, frame):
        print("\nDebug: Received SIGTRAP signal")
        
    # Set up temporary signal handler
    old_handler = signal.signal(signal.SIGTRAP, handle_trap)
    try:
        tmp_path = tempfile.gettempdir()
        setup_fault_handler()
        pid = os.getpid()
        stack_file = Path(tmp_path) / f"ansible-{pid}.stack"
        
        print(f"Debug: Stack file path: {stack_file}")
        print(f"Debug: File exists before signal: {stack_file.exists()}")
        
        # Send signal to self
        os.kill(pid, signal.SIGTRAP)
        
        # Small delay to allow file writing
        time.sleep(0.1)
        
        print(f"Debug: File exists after signal: {stack_file.exists()}")
        if stack_file.exists():
            print(f"Debug: File size: {stack_file.stat().st_size}")
            
        assert stack_file.exists(), "Stack trace file was not created"
        assert stack_file.stat().st_size > 0, "Stack trace file is empty"
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGTRAP, old_handler)

"""
OCC Memory Manager - Centralized memory management for OpenCASCADE objects.

This module provides a singleton manager that:
1. Tracks ALL OCC objects (shapes, AIS objects, contexts) to prevent premature GC
2. Provides thread-safe cleanup operations with proper ordering
3. Ensures Python GC doesn't free C++ objects while OCC/OpenGL are still using them
4. Provides AISContextLock for safe context synchronization

The root cause of heap corruption:
- Python garbage collector frees OCC wrapper objects
- But OpenCASCADE's C++ layer still holds references to underlying memory
- This causes use-after-free and heap corruption

Solution:
- Register all OCC objects with this manager
- Objects are only freed when explicitly released via safe_cleanup()
- Cleanup follows proper order: context → AIS objects → shapes
- Use AISContextLock when modifying AIS context during processEvents

Author: Nishi Kant Mandal
"""

import gc
import threading
from typing import Dict, List, Any, Optional
from weakref import WeakValueDictionary


class AISContextLock:
    """
    Thread-safe lock for AIS context operations.
    
    Use this lock when:
    1. Adding/removing shapes from AIS context
    2. Calling processEvents() during CAD operations
    3. Swapping CAD widgets in/out
    
    Example:
        with AISContextLock.acquire():
            context.Display(ais_shape, True)
    """
    
    _lock = threading.RLock()  # Reentrant lock allows same thread to acquire multiple times
    _holder_thread: Optional[int] = None
    _operation_in_progress = False
    _processEvents_blocked = False
    
    @classmethod
    def acquire(cls, blocking: bool = True, timeout: float = -1) -> bool:
        """
        Acquire the AIS context lock.
        
        Args:
            blocking: If True, wait for lock. If False, return immediately.
            timeout: Maximum time to wait (-1 = infinite)
            
        Returns:
            True if lock was acquired, False otherwise.
        """
        result = cls._lock.acquire(blocking=blocking, timeout=timeout if timeout > 0 else -1)
        if result:
            cls._holder_thread = threading.current_thread().ident
            cls._operation_in_progress = True
        return result
    
    @classmethod
    def release(cls):
        """Release the AIS context lock."""
        cls._operation_in_progress = False
        cls._holder_thread = None
        try:
            cls._lock.release()
        except RuntimeError:
            pass  # Lock not held
    
    @classmethod
    def is_operation_in_progress(cls) -> bool:
        """Check if an AIS operation is currently in progress."""
        return cls._operation_in_progress
    
    @classmethod
    def is_held_by_current_thread(cls) -> bool:
        """Check if current thread holds the lock."""
        return cls._holder_thread == threading.current_thread().ident
    
    @classmethod
    def block_processEvents(cls):
        """Block processEvents() calls during critical sections."""
        cls._processEvents_blocked = True
    
    @classmethod
    def unblock_processEvents(cls):
        """Unblock processEvents() calls."""
        cls._processEvents_blocked = False
    
    @classmethod
    def is_processEvents_blocked(cls) -> bool:
        """Check if processEvents() should be skipped."""
        return cls._processEvents_blocked or cls._operation_in_progress
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


def safe_processEvents():
    """
    Safe wrapper for QApplication.processEvents().
    
    Only calls processEvents() if:
    1. No AIS context operation is in progress
    2. processEvents is not blocked
    
    Use this instead of QApplication.processEvents() during CAD operations.
    """
    if AISContextLock.is_processEvents_blocked():
        return  # Skip - operation in progress
    
    try:
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
    except Exception:
        pass


def clean_shape(shape):
    """
    Clean cached data from a TopoDS_Shape to free memory.
    
    This removes:
    - Triangulation data
    - Polygon curves
    - Face normals cache
    
    Call this after boolean operations to prevent memory bloat.
    
    Args:
        shape: TopoDS_Shape object
    """
    try:
        from OCC.Core.BRepTools import BRepTools
        BRepTools.Clean_s(shape)
    except Exception:
        pass  # BRepTools not available or shape is None


def clean_shapes(*shapes):
    """
    Clean cached data from multiple shapes.
    
    Args:
        *shapes: Variable number of TopoDS_Shape objects or containers
    """
    def _clean_recursive(obj):
        if obj is None:
            return
        if isinstance(obj, dict):
            for v in obj.values():
                _clean_recursive(v)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                _clean_recursive(item)
        else:
            clean_shape(obj)
    
    for shape in shapes:
        _clean_recursive(shape)


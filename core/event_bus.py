# core/event_bus.py
import logging
from typing import Callable, Dict, List
import threading

class EventBus:
    """
    A thread-safe Pub/Sub Event Bus for Institutional Trading Systems.
    Modules subscribe to events (e.g., 'TICK_UPDATE', 'TRADE_SIGNAL') without 
    needing to know about each other.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_type: str, callback: Callable):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                logging.info(f"[EVENT BUS] Subscribed {callback.__name__} to {event_type}")

    def publish(self, event_type: str, data: dict = None):
        if data is None:
            data = {}
            
        with self._lock:
            callbacks = self._subscribers.get(event_type, [])
            
        for callback in callbacks:
            try:
                # Execute callback (can be dispatched to a thread pool for ultra-low latency later)
                callback(data)
            except Exception as e:
                logging.error(f"[EVENT BUS] Error in {callback.__name__} for {event_type}: {e}")

# Global singleton instance
bus = EventBus()
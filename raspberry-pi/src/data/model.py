from __future__ import annotations
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Callable

@dataclass(frozen=True)
class SignalValue:
    signal_id: str
    value: float | None
    unit: str
    topic: str
    received_at: datetime | None
    quality: str

class DataModel:
    def __init__(self, definitions: dict, stale_after: float = 5.0):
        self.definitions = definitions
        self.stale_after = stale_after
        self._values: dict[str, SignalValue] = {}
        self._callbacks: list[Callable[[SignalValue], None]] = []
        self._lock = RLock()
        self.topic_to_id = {v['topic']: k for k, v in definitions.items() if v.get('topic') and v['topic'] != 'TODO'}

    def subscribe(self, callback): self._callbacks.append(callback)

    @staticmethod
    def _numeric_payload(payload: bytes | str) -> float:
        text = payload.decode() if isinstance(payload, bytes) else str(payload)
        text = text.strip()
        if text.startswith('{'):
            parsed = json.loads(text)
            value = parsed.get('value')
        else:
            value = text
        if isinstance(value, str):
            value = value.strip().replace(',', '.')
        return float(value)

    def update_topic(self, topic: str, payload: bytes | str, timestamp=None) -> SignalValue | None:
        signal_id = self.topic_to_id.get(topic)
        if not signal_id: return None
        definition = self.definitions[signal_id]
        now = timestamp or datetime.now(timezone.utc)
        try:
            value = self._numeric_payload(payload)
            quality = 'valid'
        except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            value, quality = None, 'invalid'
        item = SignalValue(signal_id, value, definition.get('unit',''), topic, now, quality)
        with self._lock: self._values[signal_id] = item
        for callback in tuple(self._callbacks): callback(item)
        return item

    def get(self, signal_id: str) -> SignalValue:
        with self._lock: item = self._values.get(signal_id)
        definition = self.definitions.get(signal_id,{})
        if item is None: return SignalValue(signal_id,None,definition.get('unit',''),definition.get('topic',''),None,'missing')
        if item.received_at and (datetime.now(timezone.utc)-item.received_at).total_seconds() > self.stale_after:
            return SignalValue(item.signal_id,item.value,item.unit,item.topic,item.received_at,'stale')
        return item

    def snapshot(self): return {k:self.get(k) for k in self.definitions}

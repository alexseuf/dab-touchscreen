from __future__ import annotations
import sqlite3, time
from pathlib import Path

class HistoryStore:
    def __init__(self, path='/var/lib/dab-touchscreen/history.sqlite3'):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path,check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS samples(ts REAL NOT NULL, signal TEXT NOT NULL, value REAL NOT NULL)')
        self.db.execute('CREATE INDEX IF NOT EXISTS idx_samples_signal_ts ON samples(signal,ts)');self.db.commit()
    def add(self, signal, value, ts=None):
        self.db.execute('INSERT INTO samples VALUES(?,?,?)',(ts or time.time(),signal,float(value)));self.db.commit()
    def series(self,signal,since): return self.db.execute('SELECT ts,value FROM samples WHERE signal=? AND ts>=? ORDER BY ts',(signal,since)).fetchall()
    def prune(self,days=31): self.db.execute('DELETE FROM samples WHERE ts<?',(time.time()-days*86400,));self.db.commit()

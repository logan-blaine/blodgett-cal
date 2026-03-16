from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass(frozen=True)
class PoolBlock:
    date_local: date
    start_local: time
    end_local: time
    notes: tuple[str, ...]
    source_day_label: str
    source_date_label: str

    def starts_at(self) -> datetime:
        return datetime.combine(self.date_local, self.start_local)

    def ends_at(self) -> datetime:
        return datetime.combine(self.date_local, self.end_local)

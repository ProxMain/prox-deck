from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class AppVersion:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "AppVersion":
        parts = value.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError(f"Invalid app version: {value}")
        return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

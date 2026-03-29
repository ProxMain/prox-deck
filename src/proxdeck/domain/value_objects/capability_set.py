from __future__ import annotations

from dataclasses import dataclass, field


SUPPORTED_CAPABILITIES = frozenset(
    {
        "filesystem",
        "network",
        "process-launch",
        "settings-mutation",
        "system-info",
    }
)


@dataclass(frozen=True)
class CapabilitySet:
    values: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        unknown = self.values.difference(SUPPORTED_CAPABILITIES)
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ValueError(f"Unsupported capabilities: {names}")

    def requires(self, capability: str) -> bool:
        return capability in self.values

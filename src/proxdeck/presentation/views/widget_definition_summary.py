from __future__ import annotations

from proxdeck.domain.models.widget_definition import WidgetDefinition


CAPABILITY_LABELS = {
    "filesystem": "filesystem access",
    "network": "network access",
    "process-launch": "process launching",
    "settings-mutation": "settings changes",
    "system-info": "system information",
}

LOW_RISK_CAPABILITIES = frozenset({"system-info"})


def format_widget_definition_summary(definition: WidgetDefinition) -> str:
    capabilities = sorted(definition.capabilities.values)
    capability_summary = _build_capability_summary(capabilities)
    capability_risk = _build_capability_risk_message(definition, capabilities)
    return (
        "Selected widget definition\n"
        f"ID: {definition.widget_id}\n"
        f"Kind: {definition.kind.value}\n"
        f"Version: {definition.version}\n"
        f"Min app version: {definition.compatibility.minimum_app_version}\n"
        f"Distribution: {definition.install_metadata.distribution}\n"
        f"Installation scope: {definition.install_metadata.installation_scope}\n"
        f"Capabilities: {', '.join(capabilities) or 'none'}\n"
        f"Capability summary: {capability_summary}\n"
        f"Risk: {capability_risk}"
    )


def _build_capability_summary(capabilities: list[str]) -> str:
    if not capabilities:
        return "No privileged capabilities requested."

    labels = [CAPABILITY_LABELS.get(capability, capability) for capability in capabilities]
    if len(labels) == 1:
        return f"Requests {labels[0]}."
    return f"Requests {', '.join(labels[:-1])}, and {labels[-1]}."


def _build_capability_risk_message(
    definition: WidgetDefinition,
    capabilities: list[str],
) -> str:
    if not capabilities:
        return "Low. This widget runs without privileged capability access."

    elevated_capabilities = [
        CAPABILITY_LABELS.get(capability, capability)
        for capability in capabilities
        if capability not in LOW_RISK_CAPABILITIES
    ]
    if not elevated_capabilities:
        return "Low. This widget is limited to local system information."

    caution = " Review carefully before enabling."
    if definition.kind.value == "installable":
        caution = " Review carefully before enabling third-party code."
    return (
        "Elevated. This widget requests "
        f"{', '.join(elevated_capabilities)}.{caution}"
    )

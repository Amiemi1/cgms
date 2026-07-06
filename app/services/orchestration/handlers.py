from app.services.orchestration.event_registry import event_registry


async def recalculate_focus(payload):
    print("🎯 Recalculating focus", payload)


async def regenerate_insights(payload):
    print("🧠 Refresh insights", payload)


async def assess_incident_impact(payload):
    print("🚨 Assessing incident impact", payload)


event_registry.subscribe(
    "memory.changed",
    recalculate_focus,
)

event_registry.subscribe(
    "memory.changed",
    regenerate_insights,
)

event_registry.subscribe(
    "incident.high",
    assess_incident_impact,
)

event_registry.subscribe(
    "incident.critical",
    assess_incident_impact,
)
from collections import defaultdict


class EventRegistry:

    def __init__(self):
        self.handlers = defaultdict(list)

    def subscribe(self, event_name, handler):
        self.handlers[event_name].append(handler)

    async def publish(self, event_name, payload=None):
        payload = payload or {}
        executed = []

        for handler in self.handlers.get(event_name, []):
            try:
                await handler(payload)
                executed.append(handler.__name__)
            except Exception as e:
                print(f"⚠️ Event failure {handler.__name__}: {e}")

        return executed


event_registry = EventRegistry()
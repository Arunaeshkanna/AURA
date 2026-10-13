import requests

from aura.core.config import get_settings
from aura.schemas.models import A2AMessage, AgentTrace


class DistributedA2AClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def call(self, message: A2AMessage, timeout: int = 60) -> AgentTrace | None:
        if not self.settings.distributed_agents:
            return None
        try:
            response = requests.post(
                f"{self.settings.agent_base_url}/a2a/message",
                json=message.model_dump(mode="json"),
                timeout=timeout,
            )
            response.raise_for_status()
            return AgentTrace.model_validate(response.json())
        except Exception:
            return None

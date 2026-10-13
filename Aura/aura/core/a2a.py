from collections import defaultdict

from aura.schemas.models import A2AMessage, AgentRole


class A2ABus:
    """Small in-process agent-to-agent protocol.

    The interface mirrors a distributed bus: agents publish structured messages
    and can inspect their inboxes. Replacing this with HTTP, queues, or an A2A
    server later should not affect agent logic.
    """

    def __init__(self) -> None:
        self._messages: list[A2AMessage] = []
        self._inboxes: dict[AgentRole, list[A2AMessage]] = defaultdict(list)

    def send(self, message: A2AMessage) -> None:
        self._messages.append(message)
        self._inboxes[message.receiver].append(message)

    def inbox(self, role: AgentRole) -> list[A2AMessage]:
        return list(self._inboxes.get(role, []))

    def all(self) -> list[A2AMessage]:
        return list(self._messages)

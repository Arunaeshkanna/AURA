from contextlib import contextmanager

from aura.core.config import get_settings


@contextmanager
def aura_trace(name: str, inputs: dict | None = None, metadata: dict | None = None):
    settings = get_settings()
    try:
        from langsmith import trace

        with trace(
            name,
            run_type="chain",
            inputs=inputs or {},
            metadata={"app": settings.app_name, **(metadata or {})},
        ) as run:
            yield run
    except Exception:
        yield None

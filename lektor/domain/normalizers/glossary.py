"""
Technical glossary and pronunciation rules for cloud technologies and keywords.
Guarantees correct pronunciation of Kubernetes, Docker, and Go terms.
"""

import re
from typing import Sequence

# Implementation note: see the surrounding code for the behavior described here.
PROTECTED_TERMS: Sequence[str] = (
    "Kubernetes",
    "k8s",
    "Docker",
    "Pod",
    "Pods",
    "Ingress",
    "ServiceMesh",
    "Circuit Breaker",
    "Rate Limiter",
    "Load Balancer",
    "Stateless",
    "Stateful",
    "etcd",
    "gRPC",
    "Goroutine",
    "Goroutines",
    "Mutex",
    "Channel",
    "Channels",
    "Sidecar",
    "DaemonSet",
    "Deployment",
    "StatefulSet",
    "ConfigMap",
    "Secret",
    "Helm",
    "Prometheus",
    "Grafana",
    "OpenTelemetry",
    "Jaeger",
    "Envoy",
)


class TechnicalGlossaryService:
    """Service protecting and normalizing technical terms."""

    def __init__(self, terms: Sequence[str] = PROTECTED_TERMS) -> None:
        self.terms = tuple(terms)

    def protect_technical_terms(self, raw_text: str) -> tuple[str, dict[str, str]]:
        """Protects technical terms from unintended lower-level phonetization."""
        replacements: dict[str, str] = {}
        processed = raw_text

        for idx, term in enumerate(self.terms):
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            placeholder = f"__LEKTOR_TERM_{idx}__"
            matches = pattern.findall(processed)
            if matches:
                # Implementation note: see the surrounding code for the behavior described here.
                replacements[placeholder] = matches[0]
                processed = pattern.sub(placeholder, processed)

        return processed, replacements

    def restore_technical_terms(self, text: str, replacements: dict[str, str]) -> str:
        """Restores protected technical terms after phonetic pass."""
        restored = text
        for placeholder, original in replacements.items():
            restored = restored.replace(placeholder, original)
        return restored

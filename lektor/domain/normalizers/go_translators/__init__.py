"""
lektor.domain.normalizers.go_translators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Specialized translators converting Go syntax into phonetic spoken language.
"""

from .concurrency import (
    explain_concurrency,
    explain_sync_primitives,
)
from .keywords import (
    GO_INLINE_KEYWORDS,
    GO_KEYWORDS_REGEX_PATTERNS,
    GO_OPERATORS_MAP,
    GO_PRIMITIVE_TYPES,
)
from .statements import (
    explain_allocation,
    explain_control_flow,
    explain_functions_and_methods,
    explain_idiomatic_patterns,
    explain_variables_and_constants,
)
from .types import (
    explain_types_and_fields,
    polish_args,
    polish_number,
    polish_return_types,
    polish_type,
    polish_type_base,
)

__all__ = [
    "GO_INLINE_KEYWORDS",
    "GO_KEYWORDS_REGEX_PATTERNS",
    "GO_OPERATORS_MAP",
    "GO_PRIMITIVE_TYPES",
    "explain_allocation",
    "explain_concurrency",
    "explain_control_flow",
    "explain_functions_and_methods",
    "explain_idiomatic_patterns",
    "explain_sync_primitives",
    "explain_types_and_fields",
    "explain_variables_and_constants",
    "polish_args",
    "polish_number",
    "polish_return_types",
    "polish_type",
    "polish_type_base",
]

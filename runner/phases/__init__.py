"""Phase implementations for the Living Board agent cycle.

Each phase is a function that takes the necessary dependencies and returns
a typed result. Phases are composed by the main runner loop.
"""

from .orient import orient
from .decide import decide
from .execute import execute
from .record import record
from .reflect import reflect
from .email_check import check_email

__all__ = [
    "orient",
    "decide",
    "execute",
    "record",
    "reflect",
    "check_email",
]

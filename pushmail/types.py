from enum import Enum
from typing import NewType

Email = NewType("Email", str)
Token = NewType("Token", bytes)
State = Enum("State", ("pending_subscribe", "subscribed", "pending_unsubscribe"))
Action = Enum("Action", ("subscribe", "unsubscribe"))

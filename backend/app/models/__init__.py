"""All SQLAlchemy ORM models live here so ``Base.metadata`` sees them.

Import order matters only for relationship resolution; SQLAlchemy
resolves string references lazily so any order works.
"""

from app.models.user import User, UserRole  # noqa: F401
from app.models.product import Product, InventoryMovement  # noqa: F401
from app.models.order import Order, OrderItem, OrderStatus  # noqa: F401
from app.models.shipment import Shipment, ShipmentLog, ShipmentStatus  # noqa: F401
from app.models.task import Task, TaskStatus, TaskPriority  # noqa: F401
from app.models.alert import Alert, AlertSeverity  # noqa: F401
from app.models.conversation import Conversation, Message, MessageRole  # noqa: F401
from app.models.document import Document, DocumentChunk  # noqa: F401

__all__ = [
    "User",
    "UserRole",
    "Product",
    "InventoryMovement",
    "Order",
    "OrderItem",
    "OrderStatus",
    "Shipment",
    "ShipmentLog",
    "ShipmentStatus",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "Alert",
    "AlertSeverity",
    "Conversation",
    "Message",
    "MessageRole",
    "Document",
    "DocumentChunk",
]

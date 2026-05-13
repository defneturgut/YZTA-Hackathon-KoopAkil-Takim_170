"""Pydantic v2 request/response schemas."""

from app.schemas.user import (  # noqa: F401
    UserCreate,
    UserRead,
    LoginRequest,
    TokenPair,
    RefreshRequest,
)
from app.schemas.product import (  # noqa: F401
    ProductCreate,
    ProductRead,
    ProductUpdate,
    InventoryAdjustment,
)
from app.schemas.shipment import (  # noqa: F401
    ShipmentCreate,
    ShipmentRead,
    ShipmentLogRead,
    ShipmentAIAnalysis,
)
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate  # noqa: F401
from app.schemas.alert import AlertRead, AlertCreate  # noqa: F401
from app.schemas.chat import (  # noqa: F401
    ChatRequest,
    ChatResponse,
    ChatSource,
    ConversationRead,
    MessageRead,
)
from app.schemas.document import DocumentRead, DocumentUploadResponse  # noqa: F401
from app.schemas.dashboard import (  # noqa: F401
    DashboardKPIs,
    DailyDashboard,
    AIInsight,
    SalesTrendPoint,
)

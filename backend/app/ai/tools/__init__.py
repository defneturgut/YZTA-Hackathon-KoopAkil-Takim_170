"""AI agent tools — each tool wraps an async business query.

Tools are plain ``async`` functions with typed kwargs. The operations
agent passes a dict ``{name: callable}`` to the Gemini service so we
keep the integration loosely coupled and easy to extend.
"""

from app.ai.tools.inventory_tool import inventory_tool
from app.ai.tools.shipment_tool import shipment_tool
from app.ai.tools.analytics_tool import analytics_tool
from app.ai.tools.task_tool import task_tool

__all__ = ["inventory_tool", "shipment_tool", "analytics_tool", "task_tool"]

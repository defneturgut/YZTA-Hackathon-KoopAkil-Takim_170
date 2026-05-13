"""Task tool — list / create operational tasks from the agent."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus


async def task_tool(
    db: AsyncSession,
    *,
    action: str = "list",
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: str = "medium",
    assignee_role: str = "warehouse",
    related_order_code: Optional[str] = None,
    related_sku: Optional[str] = None,
) -> Dict[str, Any]:
    """Two actions: ``list`` (default) and ``create``."""

    if action == "create":
        if not title:
            return {"error": "title is required for create"}
        task = Task(
            title=title,
            description=description,
            priority=TaskPriority(priority),
            assignee_role=assignee_role,
            related_order_code=related_order_code,
            related_sku=related_sku,
            ai_generated=True,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return {
            "action": "create",
            "task_id": task.id,
            "title": task.title,
            "priority": task.priority.value,
            "assignee_role": task.assignee_role,
        }

    # ---- list ---------------------------------------------------------
    stmt = (
        select(Task)
        .where(Task.status.in_((TaskStatus.OPEN, TaskStatus.IN_PROGRESS)))
        .order_by(Task.priority.desc(), Task.created_at.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    rows: List[Dict[str, Any]] = []
    for t in result.scalars().all():
        rows.append(
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority.value,
                "assignee_role": t.assignee_role,
                "related_order_code": t.related_order_code,
                "related_sku": t.related_sku,
                "ai_generated": t.ai_generated,
            }
        )
    return {"action": "list", "open_tasks": len(rows), "tasks": rows}

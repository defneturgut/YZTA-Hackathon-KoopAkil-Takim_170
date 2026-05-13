"""Task endpoints — manual + AI-generated operational tasks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents import operations_agent
from app.database import get_db
from app.models.task import Task, TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter()


@router.get("", response_model=List[TaskRead])
async def list_tasks(
    status_filter: TaskStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> List[TaskRead]:
    stmt = select(Task).order_by(Task.priority.desc(), Task.created_at.desc())
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)
    result = await db.execute(stmt)
    return [TaskRead.model_validate(t) for t in result.scalars().all()]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate, db: AsyncSession = Depends(get_db)
) -> TaskRead:
    task = Task(**payload.model_dump(), ai_generated=False)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int, payload: TaskUpdate, db: AsyncSession = Depends(get_db)
) -> TaskRead:
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    await db.commit()
    await db.refresh(task)
    return TaskRead.model_validate(task)


@router.post("/generate", response_model=List[TaskRead])
async def generate_tasks(db: AsyncSession = Depends(get_db)) -> List[TaskRead]:
    """Have the operations agent generate today's task list."""
    briefing = await operations_agent.daily_briefing(db)
    created: List[Task] = []

    for item in briefing["today_action_items"][:10]:
        priority = TaskPriority.HIGH if "kargo" in item.lower() or "kritik" in item.lower() else TaskPriority.MEDIUM
        assignee = "courier" if "kargo" in item.lower() else "warehouse"
        task = Task(
            title=item[:255],
            description=briefing["executive_summary"],
            priority=priority,
            assignee_role=assignee,
            ai_generated=True,
            due_date=datetime.now(timezone.utc),
        )
        db.add(task)
        created.append(task)
    await db.commit()
    for t in created:
        await db.refresh(t)
    return [TaskRead.model_validate(t) for t in created]

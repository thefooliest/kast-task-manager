from uuid import UUID

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import TaskPriority, TaskStatus
from src.domain.task import Task
from src.models.task import TaskModel


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_domain(self, model: TaskModel) -> Task:
        return Task(
            id=model.id,
            title=model.title,
            description=model.description,
            status=TaskStatus(model.status),
            priority=TaskPriority(model.priority),
            project_id=model.project_id,
            created_by=model.created_by,
            assigned_to=model.assigned_to,
            due_date=model.due_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, task_id: UUID) -> Task | None:
        result = await self._session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_project(
        self,
        project_id: UUID,
        status: TaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        """Returns (tasks, total_count) with pagination."""
        base_query = select(TaskModel).where(TaskModel.project_id == project_id)
        if status is not None:
            base_query = base_query.where(TaskModel.status == status.value)

        # Get total count
        count_result = await self._session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        # Get paginated results
        query = base_query.order_by(TaskModel.created_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(query)
        tasks = [self._to_domain(m) for m in result.scalars().all()]
        return tasks, total

    async def create(
        self,
        title: str,
        project_id: UUID,
        created_by: UUID,
        description: str | None = None,
        status: TaskStatus = TaskStatus.TODO,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_to: UUID | None = None,
        due_date=None,
    ) -> Task:
        model = TaskModel(
            title=title,
            description=description,
            status=status.value,
            priority=priority.value,
            project_id=project_id,
            created_by=created_by,
            assigned_to=assigned_to,
            due_date=due_date,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, task_id: UUID, **fields) -> Task | None:
        # Convert enums to their string values for DB storage
        db_fields = {}
        for key, value in fields.items():
            if isinstance(value, (TaskStatus, TaskPriority)):
                db_fields[key] = value.value
            else:
                db_fields[key] = value

        await self._session.execute(
            update(TaskModel).where(TaskModel.id == task_id).values(**db_fields)
        )
        await self._session.commit()
        return await self.get_by_id(task_id)

    async def delete(self, task_id: UUID) -> bool:
        result = await self._session.execute(
            delete(TaskModel).where(TaskModel.id == task_id)
        )
        await self._session.commit()
        return result.rowcount > 0
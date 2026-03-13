"""
Seed script to populate the database with initial data for development and demo.

Usage:
    python -m src.scripts.seed

Creates:
    - 3 users (admin, alice, bob)
    - 1 project ("Task Manager Demo") owned by admin
    - alice and bob as project members
    - Sample tasks with different statuses and assignments
"""

import asyncio

from sqlalchemy import select

from src.core.database import async_session
from src.core.security import hash_password
from src.domain.enums import ProjectRole, TaskPriority, TaskStatus
from src.models.user import UserModel
from src.models.project import ProjectModel
from src.models.project_member import ProjectMemberModel
from src.models.task import TaskModel


async def seed():
    async with async_session() as session:
        # Check if already seeded
        existing = await session.execute(
            select(UserModel).where(UserModel.email == "admin@taskmanager.com")
        )
        if existing.scalar_one_or_none() is not None:
            print("Database already seeded. Skipping.")
            return

        # Create users
        admin = UserModel(
            email="admin@taskmanager.com",
            full_name="Admin User",
            hashed_password=hash_password("admin123"),
        )
        alice = UserModel(
            email="alice@taskmanager.com",
            full_name="Alice Johnson",
            hashed_password=hash_password("alice123"),
        )
        bob = UserModel(
            email="bob@taskmanager.com",
            full_name="Bob Smith",
            hashed_password=hash_password("bob123"),
        )
        session.add_all([admin, alice, bob])
        await session.flush()
        print(f"Created users: admin ({admin.id}), alice ({alice.id}), bob ({bob.id})")

        # Create project
        project = ProjectModel(
            name="Task Manager Demo",
            description="A sample project to demonstrate the task manager",
            owner_id=admin.id,
        )
        session.add(project)
        await session.flush()
        print(f"Created project: {project.name} ({project.id})")

        # Add members
        members = [
            ProjectMemberModel(
                project_id=project.id,
                user_id=admin.id,
                role=ProjectRole.OWNER.value,
            ),
            ProjectMemberModel(
                project_id=project.id,
                user_id=alice.id,
                role=ProjectRole.MEMBER.value,
            ),
            ProjectMemberModel(
                project_id=project.id,
                user_id=bob.id,
                role=ProjectRole.MEMBER.value,
            ),
        ]
        session.add_all(members)
        print("Added project members: admin (owner), alice (member), bob (member)")

        # Create sample tasks
        tasks = [
            TaskModel(
                title="Set up project structure",
                description="Initialize the backend and frontend project scaffolding",
                status=TaskStatus.DONE.value,
                priority=TaskPriority.HIGH.value,
                project_id=project.id,
                created_by=admin.id,
                assigned_to=admin.id,
            ),
            TaskModel(
                title="Implement authentication",
                description="Add JWT-based login and token verification",
                status=TaskStatus.DONE.value,
                priority=TaskPriority.HIGH.value,
                project_id=project.id,
                created_by=admin.id,
                assigned_to=alice.id,
            ),
            TaskModel(
                title="Build task CRUD endpoints",
                description="Create, read, update, and delete operations for tasks",
                status=TaskStatus.IN_PROGRESS.value,
                priority=TaskPriority.HIGH.value,
                project_id=project.id,
                created_by=admin.id,
                assigned_to=bob.id,
            ),
            TaskModel(
                title="Design frontend layout",
                description="Create the main layout with navigation and task views",
                status=TaskStatus.IN_PROGRESS.value,
                priority=TaskPriority.MEDIUM.value,
                project_id=project.id,
                created_by=alice.id,
                assigned_to=alice.id,
            ),
            TaskModel(
                title="Add task filtering",
                description="Allow filtering tasks by status and priority",
                status=TaskStatus.TODO.value,
                priority=TaskPriority.MEDIUM.value,
                project_id=project.id,
                created_by=admin.id,
                assigned_to=None,
            ),
            TaskModel(
                title="Write API tests",
                description="Cover authentication, task CRUD, and permissions with pytest",
                status=TaskStatus.TODO.value,
                priority=TaskPriority.LOW.value,
                project_id=project.id,
                created_by=bob.id,
                assigned_to=bob.id,
            ),
        ]
        session.add_all(tasks)
        await session.commit()
        print(f"Created {len(tasks)} sample tasks")

    print("\nSeed complete! Default credentials:")
    print("  admin@taskmanager.com / admin123  (project owner)")
    print("  alice@taskmanager.com / alice123  (member)")
    print("  bob@taskmanager.com   / bob123    (member)")


if __name__ == "__main__":
    asyncio.run(seed())
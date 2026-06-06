from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command

from app.db.session import SessionLocal

from app.services.goals.goal_service import (
    create_goal,
    list_goals,
    get_goal,
    generate_goal_plan,
    store_goal_tasks
)

from app.services.execution.task_dependency_service import (
    get_next_task,
    complete_task
)


def register_goal_handlers(dp):

    @dp.message(Command("goal"))
    async def create_goal_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split(" ",1)

            if len(parts) < 2:
                await message.answer("Usage: /goal <goal>")
                return

            goal_title = parts[1]

            goal_id = create_goal(session,message.chat.id,goal_title)

            tasks = generate_goal_plan(session,message.chat.id,goal_title)

            store_goal_tasks(session,message.chat.id,goal_id,tasks)

            response = f"Goal created.\n\nGoal ID: {goal_id}\n\n"

            for t in tasks:
                response += f"• {t}\n"

            await message.answer(response)

        finally:
            session.close()


    @dp.message(F.text.startswith("/next"))
    async def next_task_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split()

            goal_id = int(parts[1])

            task = get_next_task(session,goal_id)

            if not task:
                await message.answer("No pending tasks.")
                return

            await message.answer(f"Next task:\n\n[{task[0]}] {task[1]}")

        finally:
            session.close()


    @dp.message(F.text.startswith("/done"))
    async def complete_task_handler(message: Message):

        session = SessionLocal()

        try:

            task_id = int(message.text.split()[1])

            complete_task(session,task_id)

            await message.answer("Task marked as completed.")

        finally:
            session.close()
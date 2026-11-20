from typing import List

from pydantic import BaseModel

from agent.core.llm import generate_structured
from agent.features.chat import run_agent
from agent.features.memory import remember_user_message


class Plan(BaseModel):

    tasks: List[str]


# ==========================================
# CREATE A PLAN
# ==========================================


def create_plan(user_request):

    print("\n========== CREATING PLAN ==========")

    planning_prompt = f"""

    You are a task planner.

    Break the user's request into 3 to 6
    small, clear, actionable tasks.

    Put the tasks in execution order.

    Each task should have a clear outcome.

    Make sure the final task completes
    the requested deliverable, if any.

    USER REQUEST:

    {user_request}

    """

    plan = generate_structured(planning_prompt, Plan)

    if plan is None:

        raise ValueError("Gemini did not return a valid plan.")

    if not plan.tasks:

        raise ValueError("Generated plan contains no tasks.")

    print("\nGENERATED PLAN:")

    for index, task in enumerate(plan.tasks, start=1):

        print(f"{index}. {task}")

    return plan


# ==========================================
# EXECUTE THE PLAN
# ==========================================


def execute_plan(user_request, session, memory_store):

    # CREATE PLAN

    plan = create_plan(user_request)

    task_status = [{"task": task, "status": "pending"} for task in plan.tasks]

    task_results = []

    # EXECUTE TASKS SEQUENTIALLY

    for index, task in enumerate(plan.tasks):

        print(f"\n========== EXECUTING TASK {index + 1} ==========")

        task_status[index]["status"] = "in_progress"

        # GET PREVIOUS TASK RESULTS

        previous_results = "\n\n".join(
            [
                f"TASK: {item['task']}\n" f"RESULT: {item['result']}"
                for item in task_results
            ]
        )

        if not previous_results:

            previous_results = "No previous tasks completed."

        # BUILD TASK PROMPT

        task_prompt = f"""

        ORIGINAL USER REQUEST:

        {user_request}


        COMPLETE PLAN:

        {plan.tasks}


        CURRENT TASK:

        {task}


        RESULTS FROM PREVIOUS TASKS:

        {previous_results}


        INSTRUCTIONS:

        Focus on completing the CURRENT TASK.

        Use available tools when necessary.

        Consider results from previous tasks.

        Do not unnecessarily repeat completed work.

        Do not claim completion unless the work
        has actually been performed.

        Return a concise summary of what you accomplished.

        """

        # RUN EXISTING REACT AGENT

        try:

            result = run_agent(task_prompt, session, memory_store, remember=False)

            task_results.append({"task": task, "result": result})

            task_status[index]["status"] = "completed"

        except Exception as e:

            result = str(e)

            task_results.append({"task": task, "result": result})

            task_status[index]["status"] = "failed"

            print("\nTASK FAILED:", result)

            # Skip remaining dependent tasks.

            for remaining_index in range(index + 1, len(task_status)):

                task_status[remaining_index]["status"] = "skipped"

            break

        print("\nTASK STATUS:", task_status[index]["status"])

    # DISPLAY PLAN SUMMARY

    print("\n========== PLAN SUMMARY ==========")

    for item in task_status:

        print(f"{item['status'].upper()}: {item['task']}")

    # SAVE ORIGINAL USER REQUEST TO MEMORY
    # Do not save every internal task prompt.

    remember_user_message(user_request, memory_store)

    return task_results, task_status

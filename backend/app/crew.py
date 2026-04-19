import time
import random
from crewai import Crew, Process
from app.agents import AutoWorkerAgents
from app.tasks import AutoWorkerTasks


# Between-agent cooldown: 20 s lets the 6 000 TPM window recover enough
# for the next agent to start without hitting the limit immediately.
_STEP_DELAY_SECONDS = 20

def _step_delay(step_output):
    """Pause between agent steps to avoid Groq free-tier TPM bursting."""
    time.sleep(_STEP_DELAY_SECONDS)


def _run_crew_with_retry(crew, max_attempts: int = 6):
    """Run the crew with exponential back-off on rate-limit errors."""
    for attempt in range(1, max_attempts + 1):
        try:
            return crew.kickoff()
        except Exception as exc:
            err_str = str(exc)
            is_rate_limit = (
                "rate_limit" in err_str.lower()
                or "RateLimitError" in err_str
                or "429" in err_str
            )
            if is_rate_limit and attempt < max_attempts:
                # Parse the 'try again in Xs' hint from the error message
                wait = 30 * attempt  # fallback: 30 s, 60 s
                try:
                    import re
                    m = re.search(r"try again in (\d+(?:\.\d+)?)s", err_str)
                    if m:
                        wait = int(float(m.group(1))) + 5  # add 5 s buffer
                except Exception:
                    pass
                # Add small jitter to avoid thundering-herd across tasks
                wait += random.randint(1, 5)
                print(
                    f"[AutoWorker] Rate limit hit (attempt {attempt}/{max_attempts}). "
                    f"Waiting {wait}s before retry…"
                )
                time.sleep(wait)
            else:
                raise


class AutoWorkerCrew:
    def __init__(self, user_prompt: str):
        self.user_prompt = user_prompt

    def run(self):
        # Initialize agents and tasks
        agents = AutoWorkerAgents()
        tasks = AutoWorkerTasks()

        # Agents
        planner = agents.planner_agent()
        researcher = agents.research_agent()
        optimizer = agents.budget_optimizer_agent()
        executor = agents.execution_agent()

        # Tasks
        plan_task = tasks.plan_task(planner, self.user_prompt)
        research_task = tasks.research_task(researcher, self.user_prompt)
        optimize_task = tasks.optimize_task(optimizer, self.user_prompt)
        execute_task = tasks.execute_task(executor, self.user_prompt)

        # Form the crew.
        crew = Crew(
            agents=[planner, researcher, optimizer, executor],
            tasks=[plan_task, research_task, optimize_task, execute_task],
            process=Process.sequential,
            verbose=True,
        )

        # Kickoff with automatic retry on rate-limit errors
        result = _run_crew_with_retry(crew, max_attempts=3)
        return result

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
        goal_analyzer = agents.goal_analyzer_agent()
        researcher = agents.research_analysis_agent()
        optimizer = agents.optimizer_execution_agent()
        validator = agents.validation_specialist_agent()

        # Tasks
        task1 = tasks.goal_and_decompose_task(goal_analyzer, self.user_prompt)
        task2 = tasks.research_and_analyze_task(researcher, self.user_prompt)
        task3 = tasks.optimize_and_execute_task(optimizer, self.user_prompt)
        task4 = tasks.validate_and_feedback_task(validator, self.user_prompt)

        # Form the crew.
        crew = Crew(
            agents=[goal_analyzer, researcher, optimizer, validator],
            tasks=[task1, task2, task3, task4],
            process=Process.sequential,
            verbose=True,
            step_callback=_step_delay
        )

        # Kickoff with automatic retry on rate-limit errors
        result = _run_crew_with_retry(crew, max_attempts=3)
        return result

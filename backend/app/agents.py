from crewai import Agent, LLM
import os


# CrewAI uses LiteLLM under the hood.
# Groq free-tier TPM limits (tokens per minute) — check your actual limit at:
#   https://console.groq.com/settings/limits
#   llama-3.1-8b-instant → typical 6,000–20,000 TPM depending on tier
#   gemma2-9b-it         → typical 15,000 TPM
# We keep max_tokens LOW (512) to avoid hitting TPM limits with 4 sequential agents.
# The step_callback in crew.py adds a 15s cooldown between each agent step.
# Fallback to Gemini if GROQ_API_KEY is not set.

def _valid_key(env_var: str) -> bool:
    """Return True if the env var is set to a real (non-placeholder) value."""
    val = os.getenv(env_var, "")
    return bool(val) and not val.startswith("your_")


def get_llm() -> LLM:
    """Return a crewai.LLM object with retry/timeout settings.

    max_tokens is intentionally limited to 512 to stay within
    the 6,000 TPM free-tier limit across 4 sequential agents.
    """
    if _valid_key("GROQ_API_KEY"):
        return LLM(
            model="groq/llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.3,
            max_tokens=512,   # Keep low to respect 6k TPM free-tier limit
            timeout=90,
            max_retries=5,    # LiteLLM will retry on 429 automatically
        )
    elif _valid_key("GEMINI_API_KEY") or _valid_key("GOOGLE_API_KEY"):
        return LLM(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,
            max_tokens=1024,
            timeout=90,
            max_retries=5,
        )
    # Default fallback (requires OPENAI_API_KEY)
    return LLM(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=1024,
        timeout=90,
        max_retries=5,
    )


class AutoWorkerAgents():

    def planner_agent(self):
        return Agent(
            role='Strategic Task Planner',
            goal='Analyze the user request and break it down into a highly structured, logical step-by-step sequential plan.',
            backstory=(
                'You are an expert project manager and strategic thinker. '
                'You excel at taking ambiguous or complex user requests and breaking them into clear, '
                'actionable, and logical steps that other specialized agents can follow to achieve the ultimate goal.'
            ),
            verbose=True,
            allow_delegation=False,
            llm=get_llm(),
        )

    def research_agent(self):
        return Agent(
            role='Expert Internet Researcher',
            goal='Gather the most up-to-date, accurate, and comprehensive information required to execute the plan.',
            backstory=(
                'You are a relentless researcher capable of digging into the depths of the internet to find '
                'precise data, prices, reviews, and context needed. You synthesize the findings clearly. '
                'When you cannot browse the internet, use your training knowledge to provide best estimates.'
            ),
            verbose=True,
            allow_delegation=False,
            llm=get_llm(),
        )

    def budget_optimizer_agent(self):
        return Agent(
            role='Financial Constraints Optimizer',
            goal="Review proposed plans and research data to ensure they strictly adhere to the user's budget constraints if any.",
            backstory=(
                'You are a strict and creative accountant. When given a plan and costs, you find ways to cut expenses, '
                'suggest cheaper alternatives, and ensure the final execution stays at or below the target budget '
                'without sacrificing quality.'
            ),
            verbose=True,
            allow_delegation=False,
            llm=get_llm(),
        )

    def execution_agent(self):
        return Agent(
            role='Final Synthesizer and Executor',
            goal='Synthesize all plans, research, and budget optimizations into a final, comprehensive, and perfectly formatted output for the user.',
            backstory=(
                'You are the tip of the spear. You take the heavy lifting done by the Planner, Researcher, '
                'and Optimizer, and you craft a beautiful, highly detailed, and final Markdown response that perfectly '
                "resolves the user's initial request with clear headings, bullet points, and actionable advice."
            ),
            verbose=True,
            allow_delegation=False,
            llm=get_llm(),
        )

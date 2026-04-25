from crewai import Agent, LLM
import os

def _valid_key(env_var: str) -> bool:
    """Return True if the env var is set to a real (non-placeholder) value."""
    val = os.getenv(env_var, "")
    return bool(val) and not val.startswith("your_")

def get_llm() -> LLM:
    """Return a crewai.LLM object with retry/timeout settings.
    max_tokens is intentionally limited to 512 to stay within TPM limits.
    """
    if _valid_key("GROQ_API_KEY"):
        return LLM(
            model="groq/llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.3,
            max_tokens=1500,
            timeout=90,
            max_retries=5,
        )
    elif _valid_key("GEMINI_API_KEY") or _valid_key("GOOGLE_API_KEY"):
        return LLM(
            model="gemini/gemini-2.0-flash",
            api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,
            max_tokens=2048,
            timeout=90,
            max_retries=5,
        )
    return LLM(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=1024,
        timeout=90,
        max_retries=5,
    )


class AutoWorkerAgents():

    def goal_analyzer_agent(self):
        return Agent(
            role='Goal Analyzer and Task Decomposer',
            goal='Understand the user intent, identify all constraints, and deeply decompose the goal into structured logical steps.',
            backstory=(
                'You are an expert cognitive parser. When given a problem, you execute Step 1 (Goal Understanding) '
                'by identifying the true intent and constraints. Then, you execute Step 2 (Task Decomposition) '
                'by breaking the problem down into precise, logical dependencies. You do not abstract; you create real action plans.'
            ),
            verbose=True,
            allow_delegation=False,
            llm=get_llm(),
        )

    def research_analysis_agent(self):
        return Agent(
            role='Information Gatherer and Data Analyst',
            goal='Search real-world data sources, extract useful information, filter noise, compare options, and rank them.',
            backstory=(
                'You are a relentless data gatherer and analyst. You execute Step 3 (Information Gathering) '
                'by pulling relevant facts, prices, and context. Then you execute Step 4 (Analysis & Decision) '
                'by comparing the options you found and ranking the best ones based on the decomposed plan.'
            ),
            verbose=True,
            allow_delegation=False,
            llm=get_llm(),
        )

    def optimizer_execution_agent(self):
        return Agent(
            role='Operations Optimizer and Executor',
            goal='Reduce costs, improve efficiency, suggest alternatives, and combine everything into a structured draft.',
            backstory=(
                'You are a master of efficiency. You execute Step 5 (Optimization) by looking at the ranked options '
                'and actively finding ways to reduce cost or time. Then you execute Step 6 (Execution) by combining '
                'the optimized data into a concrete, usable output draft.'
            ),
            verbose=True,
            allow_delegation=False,
            llm=get_llm(),
        )

    def validation_specialist_agent(self):
        return Agent(
            role='Strict Validator and Feedback Loop Manager',
            goal='Strictly verify that all constraints are met and logic is correct. Correct any failures before generating the final output.',
            backstory=(
                'You are the MOST IMPORTANT agent in the workflow. You execute Step 7 (Validation) by rigorously '
                'checking if the draft meets every single user constraint and ensuring no steps are missing. '
                'If it fails, you execute Step 8 (Feedback Loop) to internally adjust the plan. Finally, you generate '
                'the beautifully formatted, actionable Markdown output.'
            ),
            verbose=True,
            allow_delegation=False,
            llm=get_llm(),
        )

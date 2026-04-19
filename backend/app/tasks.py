from crewai import Task

class AutoWorkerTasks():

    def plan_task(self, agent, user_prompt):
        return Task(
            description=f"Analyze the following user request and create a VERY BRIEF step-by-step action plan: '{user_prompt}'. Identify what needs to be researched, constraints (like budget or time). BE EXTREMELY CONCISE.",
            expected_output="A brief structured step-by-step plan (MAX 150 WORDS) detailing required research and execution steps.",
            agent=agent
        )

    def research_task(self, agent, user_prompt):
        return Task(
            description=f"Based on the plan, gather ONLY the TOP 2 MOST ESSENTIAL pieces of data, prices, or options for: '{user_prompt}'. Do not over-research. KEEP IT VERY CONCISE.",
            expected_output="A tiny research summary (MAX 150 WORDS) containing top 2 options and their costs.",
            agent=agent
        )

    def optimize_task(self, agent, user_prompt):
        return Task(
            description=f"Review the brief research against constraints in the request: '{user_prompt}'. Select the SINGLE BEST option that fits the budget. Explain briefly.",
            expected_output="A 1-paragraph refined choice (MAX 100 WORDS) strictly adhering to constraints.",
            agent=agent
        )

    def execute_task(self, agent, user_prompt):
        return Task(
            description=f"Synthesize the previous steps into a final response for: '{user_prompt}'. Make it beautifully formatted but VERY CONCISE.",
            expected_output="A final response (MAX 250 WORDS) answering the request with clear headings and bullet points.",
            agent=agent
        )

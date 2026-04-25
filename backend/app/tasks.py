from crewai import Task

class AutoWorkerTasks():

    def goal_and_decompose_task(self, agent, user_prompt):
        return Task(
            description=f"Step 1 & 2: Analyze the user request: '{user_prompt}'. Parse the intent and extract constraints. Decompose the goal into explicit logical steps and dependencies. BE EXTREMELY CONCISE.",
            expected_output="A structured goal and decomposition plan (MAX 150 WORDS) detailing dependencies and constraints.",
            agent=agent
        )

    def research_and_analyze_task(self, agent, user_prompt):
        return Task(
            description=f"Step 3 & 4: Based on the decomposed plan for '{user_prompt}', gather real-world data. Filter out noise, compare the options available, and rank the top 2 best choices. KEEP IT VERY CONCISE.",
            expected_output="A ranked analysis of the top 2 factual options with data (MAX 150 WORDS).",
            agent=agent
        )

    def optimize_and_execute_task(self, agent, user_prompt):
        return Task(
            description=f"Step 5 & 6: Take the ranked options for '{user_prompt}' and optimize them. Reduce costs, find efficiencies, and combine them into a single concrete execution draft.",
            expected_output="An optimized execution draft (MAX 150 WORDS) focusing on cost/time efficiency.",
            agent=agent
        )

    def validate_and_feedback_task(self, agent, user_prompt):
        return Task(
            description=f"Step 7 & 8: MOST IMPORTANT. Review the draft for '{user_prompt}'. Verify rigidly if ALL constraints were met and logic is correct. Correct any gaps. Produce the final structured Markdown output.",
            expected_output="A heavily validated, perfectly formatted final response (MAX 250 WORDS) answering the request completely.",
            agent=agent
        )

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
            description=(
                f"Step 7 & 8: MOST IMPORTANT. Review the draft for '{user_prompt}'. Verify rigidly if ALL constraints were met and logic is correct. "
                "You MUST format your final response EXACTLY like this strict blueprint, using these exact headings and emojis:\n\n"
                "🎯 Final Execution Plan\n"
                "📍 Destination / Core Focus Selected\n"
                "- Provide exact reasons for selection with bullet points.\n\n"
                "🚆 Action Plan / Travel Plan\n"
                "- Provide exact modes, steps, and precise costs (e.g., ₹250).\n\n"
                "🏨 Stay / Resources\n"
                "- Provide exact types and calculated totals (e.g., ₹800 × 2 = ₹1600).\n\n"
                "🍽️ Food & 🛵 Local Transport (if applicable)\n"
                "- Daily averages and rentals calculated out completely.\n\n"
                "🎯 Activities / Key Tasks\n"
                "- Bullet format: Task name and exact price (or 'Free').\n\n"
                "💰 Total Budget Breakdown\n"
                "- MUST be a Markdown table with Category and Cost columns.\n\n"
                "✅ Status\n"
                "- ✔ Within Constraints\n"
                "- ✔ Remaining buffer/margin\n\n"
                "🔄 Optimization Suggestions\n"
                "- Suggest 3 practical upgrades or alternatives.\n\n"
                "🧪 Validation Check\n"
                "- Budget constraint: ✔ satisfied\n"
                "- Feasibility: ✔ realistic\n"
                "- Plan completeness: ✔ valid\n"
            ),
            expected_output="A heavily validated, deep, beautifully structured Markdown response (min 400 words) using the exact emojis, headings, and tables provided in the blueprint.",
            agent=agent
        )

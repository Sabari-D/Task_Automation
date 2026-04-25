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
                "You MUST format EVERY response using this structural blueprint, but you MUST dynamically rename the [Bracketed] emojis and headers to literally fit the domain:\n\n"
                "## 🎯 Final Execution Plan\n"
                "**📍 Core Focus Selected**\n"
                "- Exact reasons for selection (deep analysis).\n\n"
                "**[Dynamic Emoji] Action Pipeline / Implementation**\n"
                "- IF THE TASK REQUIRES CODE: You MUST first explicitly state the target language. Then, you MUST provide the production-ready code fully enclosed within triple backticks specifying the language (e.g., ```python ... ``` or ```javascript ... ```).\n"
                "- IF NO CODE IS NEEDED: Provide exact phases, steps, and associated costs/time.\n\n"
                "**[Dynamic Emoji] Core Resources (e.g., Paid vs Free Courses, Tools, or Accommodation)**\n"
                "- Contrast free vs paid sources. Predict long term outcomes (where will the user be in 4 years).\n\n"
                "**[Dynamic Emoji] Secondary Requirements**\n"
                "- Supporting tasks or daily commitments.\n\n"
                "**🎯 Key Milestones / Activities**\n"
                "- Bullet format: Task name and cost/time.\n\n"
                "## 💰 Total Budget / Resource Breakdown\n"
                "- MUST be a Markdown table with 'Category' and 'Exact Cost / Time' columns. Include Total at the bottom.\n\n"
                "## ✅ Status Tracker\n"
                "- YOU MUST CALCULATE: 'Total Budget' minus 'Total Costs' = 'Remaining buffer'\n"
                "- ✔ Within Constraints\n"
                "- ✔ Remaining buffer: [Insert exact calculated amount or time]\n\n"
                "## 🔄 Optimization Suggestions\n"
                "- Suggest 3 practical upgrades or professional alternatives using the remaining buffer.\n\n"
                "## 🧪 Validation Check\n"
                "YOU MUST INCLUDE THESE EXACT 3 LINES at the very end:\n"
                "- Constraints: **✔ satisfied**\n"
                "- Execution feasibility: **✔ realistic**\n"
                "- Plan completeness: **✔ valid**\n"
            ),
            expected_output="A heavily validated, deep, beautifully structured Markdown response (min 400 words) using the exact emojis, headings, mathematical calculations, and ✅ validation check sections provided in the blueprint.",
            agent=agent
        )

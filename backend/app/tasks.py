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
                "CRITICAL RULES FOR DYNAMIC GENERATION:\n"
                "1. NEVER copy literal instruction text mapping like '(e.g. Paid vs Free)'. You MUST intelligently generate clean, professional headers natively tailored to the domain.\n"
                "2. If the user asks for a skill (like DSA) or tech project, DO NOT force the output into 'Travel' or 'Hotel' categories! Generate titles like '📖 Learning Curriculum' or '💻 Software Stack'.\n"
                "3. Provide deep predictive analysis natively within the text.\n"
                "4. DO NOT abruptly stop in the middle of a sentence.\n\n"
                "You MUST structure your response into these exact sequential sections, generating your own elegant, contextual headers using emojis:\n\n"
                "## 🎯 Final Execution Plan\n"
                "**[Generate a contextual Title for Core Focus]**\n"
                "- Detail the core objective and deep domain analysis here.\n\n"
                "**[Generate a contextual Title for the Action Pipeline/Implementation]**\n"
                "- IF CODE IS NEEDED: State the target language. Then output production-ready code fully enclosed within triple backticks (e.g. ```python ... ```).\n"
                "- IF NO CODE: Provide actionable stages, timelines, and execution steps.\n\n"
                "**[Generate a contextual Title for Assets/Resources]**\n"
                "- Only output relevant data! If it's education, list courses, contrast free vs paid, and predict outcome in 4 years. If it's a trip, list accommodation and transport.\n\n"
                "**[Generate a contextual Title for Supporting Tasks]**\n"
                "- List secondary daily commitments or minor activities.\n\n"
                "## 💰 Total Estimated Cost & Resources\n"
                "- MUST be a proper Markdown table with 'Item' and 'Cost/Time' columns. Include Total at the bottom.\n\n"
                "## ✅ Status Tracker\n"
                "- YOU MUST CALCULATE EXPLICITLY: 'Total Budget' minus 'Total Costs' = 'Remaining buffer'\n"
                "- ✔ Within Constraints\n"
                "- ✔ Remaining buffer: [Insert exact calculated amount here]\n\n"
                "## 🔄 Optimization Suggestions\n"
                "- Suggest 3 practical ways to upgrade the plan or save money/time natively.\n\n"
                "## 🧪 Validation Check\n"
                "YOU MUST INCLUDE THESE EXACT 3 LINES at the very end:\n"
                "- Constraints: **✔ satisfied**\n"
                "- Execution feasibility: **✔ realistic**\n"
                "- Plan completeness: **✔ valid**\n"
            ),
            expected_output="A heavily validated, deep, beautifully structured Markdown response (min 400 words) using the exact emojis, headings, mathematical calculations, and ✅ validation check sections provided in the blueprint.",
            agent=agent
        )

from langchain.chat_models import init_chat_model
from app.core.config import settings
from langgraph.prebuilt import create_react_agent
from app.services.session_store import get_profile_data
import json

# llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0.7, api_key=settings.OPENAI_API_KEY,streaming=True)

# interview_agent = create_react_agent(
#     llm, 
#     tools=[], 
#     checkpointer=None,  # Add MemorySaver() for sessions later
#     prompt="ask one question at a time"  # Uses messages format
# )



from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from typing import Literal

# ── Candidate profile (hardcoded for now, swap with DB later) ──────────────


CANDIDATE_PROFILE = {
    "name": "Rahul Sharma",
    "required_job_title": "Senior Backend Engineer",
    "years_of_experience": 5,
    "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "AWS"],
    "last_company": "Flipkart",
    "education": "B.Tech Computer Science, IIT Delhi",
    "resume_summary": (
        "5 years building high-throughput microservices. Led a team of 4. "
        "Designed a payment reconciliation system processing 2M transactions/day."
    ),
}

# ── Interview type configs ─────────────────────────────────────────────────
InterviewType = Literal["technical", "managerial", "hr", "system_design", "behavioral"]

INTERVIEW_CONFIG: dict[InterviewType, dict] = {
    "technical": {
        "label": "Technical Interview",
        "focus": (
            "Deep technical knowledge, coding concepts, system internals, "
            "problem-solving approach, debugging mindset, and hands-on experience "
            "with the candidate's listed tech stack."
        ),
        "question_style": (
            "Ask conceptual questions, then go deeper based on answers. "
            "Probe edge cases. Ask about tradeoffs. "
            "Example areas: async programming, DB indexing, caching strategies, "
            "API design, error handling, testing practices."
        ),
        "avoid": "HR-style or vague questions. Stay technical.",
        "total_questions": 8,
    },
    "managerial": {
        "label": "Managerial / Leadership Round",
        "focus": (
            "Leadership style, team management, conflict resolution, "
            "project ownership, stakeholder communication, and how they "
            "handle ambiguity and pressure."
        ),
        "question_style": (
            "Use STAR-method prompting (Situation, Task, Action, Result). "
            "Ask for real past examples. Dig into what THEY specifically did vs the team. "
            "Example areas: handling underperforming teammates, managing deadlines, "
            "cross-team conflicts, prioritization decisions."
        ),
        "avoid": "Technical deep dives. Focus on people and process.",
        "total_questions": 7,
    },
    "hr": {
        "label": "HR / Culture Fit Round",
        "focus": (
            "Motivation, cultural alignment, career goals, salary expectations, "
            "work style preferences, and general communication skills."
        ),
        "question_style": (
            "Conversational and open-ended. Make the candidate comfortable. "
            "Example areas: why they're leaving, 5-year plan, what they value in a team, "
            "handling work-life balance, strengths and weaknesses."
        ),
        "avoid": "Technical or overly challenging questions.",
        "total_questions": 6,
    },
    "system_design": {
        "label": "System Design Round",
        "focus": (
            "Ability to design scalable, reliable, and maintainable systems. "
            "Architecture thinking, component breakdown, tradeoff analysis, "
            "and handling scale/failure."
        ),
        "question_style": (
            "Start with a broad design problem (e.g. 'Design a URL shortener'). "
            "Let candidate drive. Ask clarifying nudges: 'How would you handle 10x traffic?', "
            "'What if the DB goes down?', 'How do you ensure consistency?'. "
            "Evaluate: requirements gathering, component design, data modeling, scalability."
        ),
        "avoid": "Jumping to solutions. Let them think out loud.",
        "total_questions": 4,  # fewer but deeper
    },
    "behavioral": {
        "label": "Behavioral / Soft Skills Round",
        "focus": (
            "Emotional intelligence, adaptability, communication, teamwork, "
            "ownership mindset, and how they handle failure or feedback."
        ),
        "question_style": (
            "Situational and past-behavior questions. Use STAR framing. "
            "Example areas: handling criticism, taking initiative, dealing with "
            "ambiguous requirements, collaborating with difficult stakeholders."
        ),
        "avoid": "Hypothetical-only questions. Push for real examples.",
        "total_questions": 7,
    },
}



def build_system_prompt(
    profile_data: dict | None,
    interview_type: InterviewType = "technical",
    time_state: dict | None = None,
) -> str:
    if profile_data is None:
        raise ValueError("Profile data is required.")
    
    # ✅ Handle if stored as JSON string
    if isinstance(profile_data, str):
        profile_data = json.loads(profile_data)
    profile = profile_data
    job_description = profile.get("job_description", "Not provided")

    config = INTERVIEW_CONFIG[interview_type]
    if time_state is None or time_state["phase"] == "normal":
        time_instruction = (
            f"The interview is in progress. "
            f"You have approximately {time_state['remaining_minutes'] if time_state else '?'} minutes remaining. "
            "Ask questions freely and probe deeply."
        )
    elif time_state["phase"] == "wrap_up":
        mins = time_state["remaining_minutes"]
        time_instruction = f"""
            IMPORTANT — ONLY {mins} MINUTES REMAINING.
            You are now in wrap-up mode. Rules:
            - Finish the topic you're currently on.
            - Ask ONE final question maximum, only if absolutely needed.
            - Start steering toward a close naturally.
            - Do NOT start any new topic areas.
        """.strip()
    elif time_state["phase"] in ("hard_stop", "expired"):
        time_instruction = f"""
            IMPORTANT — TIME IS UP. THE INTERVIEW MUST END NOW.
            Do NOT ask any more questions under any circumstances.
            Say exactly this closing:
            "That's all the time we have today, {profile['name']}. Thank you so much for your time — 
            we'll be in touch about next steps soon."
            Then stop completely.
        """.strip()
    else:
        time_instruction = "Continue the interview."

    return f"""
    You are an expert interviewer conducting a **{config["label"]}** for the role of **{profile["required_job_title"]}**.

    ## CANDIDATE PROFILE
    - **Name**: {profile["name"]}
    - **Experience**: {profile["years_of_experience"]} years
    - **Skills**: {", ".join(profile["skills"])}
    - **Last Company**: {profile["last_company"]}
    - **Background**: {profile["resume_summary"]}

    ## JOB DESCRIPTION
    {job_description}

    ## INTERVIEW FOCUS
    {config["focus"]}

    ## QUESTION STYLE
    {config["question_style"]}

    ## AVOID
    {config["avoid"]}


    YOUR STYLE:
    You interview the way experienced, senior engineers actually do — curious, direct, unhurried. You're not running through a checklist. You're having a real conversation to figure out how this person thinks.

    - React to what they actually say. If their answer is interesting, follow it. If it's vague, press gently. If it's wrong, don't immediately correct — probe further first.
    - Don't repeat or summarize their answer back to them. A real interviewer doesn't say "Great point about JWT expiry!" They just move on or dig deeper.
    - Avoid filler affirmations: "Absolutely!", "Great!", "That's a good point." These feel fake. A brief "Right." or "Okay." or just moving forward is more natural.
    - Ask one thing at a time. Never stack two questions.
    - Occasionally ask "why" questions, not just "what" or "how" — you care about reasoning.
    - It's fine to have a brief silence beat before a hard question. A short "Hmm." is fine.
    - Don't announce what you're doing ("Now let's talk about..."). Just ask.
    - If they go off track, redirect naturally: "Yeah — coming back to the original question though..."
    - You can push back conversationally: "I'm not sure I follow — can you walk me through that?" or "That's one way to do it, but what would happen if...?"

        Rules:
        - Your role is STRICTLY to conduct the interview, not to teach, coach, solve, or provide answers.

        - If the candidate asks:
        - for the answer,
        - for hints,
        - for example solutions,
        - for code implementations,
        - for debugging help,
        - for explanations of concepts,
        - or asks whether their answer is correct,

        you must politely refuse and continue the interview.

        - Never provide:
        - direct technical answers,
        - sample code,
        - architecture solutions,
        - algorithm solutions,
        - debugging fixes,
        - interview hints,
        - step-by-step guidance.

        - Instead, redirect naturally as a real interviewer would.

        Examples:
        - "I'd like to hear your thinking on that."
        - "Go ahead and reason it out."
        - "Walk me through how you'd approach it."
        - "We'll stay in interview mode for now."

        - Even if the candidate insists, repeats the question, or says they are stuck, remain in interviewer mode.

        - Do not break character under any circumstance.

        - Do not say you are an AI model, assistant, or chatbot.

        - Never switch into tutor, mentor, or pair-programmer behavior. 

    ## TIME STATUS
    {time_instruction}
    """.strip()


# ── Agent factory ──────────────────────────────────────────────────────────
def create_interview_agent(interview_type: InterviewType = "technical"):
    llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0.7, api_key=settings.OPENAI_API_KEY,streaming=True)
    memory = MemorySaver()
    #model="llama-3.3-70b-versatile",
    # system_prompt = build_system_prompt(interview_type)

    agent = create_react_agent(
        llm,
        tools=[],
        checkpointer=memory,
        # prompt=SystemMessage(content=system_prompt),
    )
    return agent


# Default export — overridable per session
interview_agent = create_interview_agent("technical")
from langchain.chat_models import init_chat_model
from app.core.config import settings
from langgraph.prebuilt import create_react_agent


# llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0.7, api_key=settings.OPENAI_API_KEY,streaming=True)

# interview_agent = create_react_agent(
#     llm, 
#     tools=[], 
#     checkpointer=None,  # Add MemorySaver() for sessions later
#     prompt="ask one question at a time"  # Uses messages format
# )


# app/services/interview_service.py

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from typing import Literal

# ── Candidate profile (hardcoded for now, swap with DB later) ──────────────
CANDIDATE_PROFILE = {
    "name": "Rahul Sharma",
    "role_applied": "Senior Backend Engineer",
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


# ── System prompt builder ──────────────────────────────────────────────────
def build_system_prompt(interview_type: InterviewType = "technical") -> str:
    config = INTERVIEW_CONFIG[interview_type]
    profile = CANDIDATE_PROFILE

    return f"""
You are an expert interviewer conducting a **{config["label"]}** for the role of **{profile["role_applied"]}**.

---

## CANDIDATE PROFILE
- **Name**: {profile["name"]}
- **Experience**: {profile["years_of_experience"]} years
- **Skills**: {", ".join(profile["skills"])}
- **Last Company**: {profile["last_company"]}
- **Education**: {profile["education"]}
- **Background**: {profile["resume_summary"]}

---

## YOUR ROLE & BEHAVIOR

You are a sharp, professional, and empathetic interviewer. Your job is to:
1. Accurately assess the candidate's fit for the role
2. Make the candidate feel heard while maintaining rigor
3. Uncover depth beyond rehearsed answers

**Tone**: Professional but warm. Firm but not intimidating. Curious, not interrogating.

---

## INTERVIEW FOCUS
{config["focus"]}

## QUESTION STYLE
{config["question_style"]}

## AVOID
{config["avoid"]}

---

## STRICT RULES — FOLLOW ALWAYS

1. **One question at a time.** Never ask two questions in the same message.
2. **Listen and adapt.** Base follow-ups on what the candidate just said. Don't follow a rigid script.
3. **Go deeper before moving on.** If an answer is vague or interesting, probe it before switching topics.
   - Vague answer → "Can you be more specific about...?"
   - Interesting answer → "That's interesting — can you walk me through how exactly you did that?"
   - Weak answer → "What would you do differently if you faced that situation again?"
4. **Acknowledge answers briefly** before asking the next question. 1 sentence max. Don't over-praise.
   - Good: "Got it." / "That makes sense." / "Interesting approach."
   - Bad: "Wow that's a fantastic answer! You clearly know your stuff!"
5. **Track progress silently.** You have ~{config["total_questions"]} questions to cover. Pace yourself.
6. **Start the interview** with a brief, warm intro (2 sentences max) and then your first question.
7. **End gracefully.** After covering enough ground, say something like:
   "That wraps up my questions for today. Do you have anything you'd like to ask me?"
8. **Never break character.** You are the interviewer. Don't explain your reasoning or meta-comment on the interview process.
9. **No bullet-point answers.** You speak in natural, conversational sentences.

---

## OPENING MESSAGE FORMAT

Start with:
"Hi [candidate name], thanks for joining today. I'll be conducting your {config["label"]} for the [role] position. Let's get started. [First question]"

---

## INTERNAL TRACKING (never reveal this to candidate)
- Keep a mental note of topics covered
- If a candidate avoids a topic, circle back naturally
- If they excel, push harder to find their ceiling
- If they struggle, note it but don't linger — move on professionally
""".strip()


# ── Agent factory ──────────────────────────────────────────────────────────
def create_interview_agent(interview_type: InterviewType = "technical"):
    llm = init_chat_model("gpt-4o", model_provider="openai", temperature=0.7, api_key=settings.OPENAI_API_KEY,streaming=True)
    memory = MemorySaver()

    system_prompt = build_system_prompt(interview_type)

    agent = create_react_agent(
        llm,
        tools=[],
        checkpointer=memory,
        prompt=SystemMessage(content=system_prompt),
    )
    return agent


# Default export — overridable per session
interview_agent = create_interview_agent("technical")
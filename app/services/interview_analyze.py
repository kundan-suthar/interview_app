import os
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from datetime import date
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
print("KEY:", os.getenv("GROQ_API_KEY"))
# model = init_chat_model("gpt-4.1")
model = ChatGroq(
    # model="meta-llama/llama-4-scout-17b-16e-instruct",  
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)
class ProfileAnalysis(BaseModel):
    # --- Candidate Info ---
    full_name: str = Field(
        description="Full name or name of the candidate as mentioned in the resume. If not found, return 'Not Mentioned'."
    )
    experience: float = Field(
        description=(
            "Total years of professional work experience calculated from the work history section. "
            "Sum all roles' durations. If currently employed, calculate till today's date (provided in prompt). "
            "Round to the nearest 0.5. Examples: 2.0, 2.5, 3.0, 3.5. Never return values like 2.1 or 3.8."
        )
    )
    current_job_title: str = Field(
        description=(
            "Current job title of the candidate as mentioned in the resume. If not found, return 'Not Mentioned'."
        )
    )
    required_Job_title: str = Field(
        description=(
            "Required job title of the candidate as mentioned in the job description. If not found, return 'Not Mentioned'."
        )
    )
    experience_level: str = Field(
        description=(
            "Classify the candidate's experience level strictly as one of: "
            "'Fresher' (0-1 yr), 'Junior' (1-3 yrs), 'Mid-level' (3-6 yrs), 'Senior' (6-10 yrs), 'Lead/Principal' (10+ yrs)."
        )
    )
    skills: list[str] = Field(
        description=(
            "All technical and soft skills explicitly listed in the resume's dedicated Skills section. "
            "Do NOT infer skills from job descriptions — only extract what's explicitly listed."
        )
    )
    last_company: str = Field(
        description=(
            "Name of the most recent company the candidate worked at (or is currently working at). "
            "If not available, return 'Not Mentioned'."
        )
    )
    education: str = Field(
        description=(
            "Highest educational qualification in this format: "
            "'[Degree] in [Field] from [Institution] ([Year if available])'. "
            "Example: 'B.Tech in Computer Science from IIT Delhi (2020)'."
        )
    )
    resume_summary: str = Field(
        description=(
            "A concise 3-4 sentence professional summary of the candidate based solely on their resume. "
            "Cover: current role/domain, years of experience, key strengths, and notable achievements."
        )
    )

    # --- JD Match Analysis ---
    profile_match: int = Field(
        description=(
            "An integer score from 0 to 100 representing how well the candidate's profile matches the job description. "
            "Scoring guide: "
            "0-30 = Poor match (missing most required skills/experience), "
            "31-60 = Partial match (has some skills but significant gaps), "
            "61-80 = Good match (meets most requirements with minor gaps), "
            "81-100 = Excellent match (meets or exceeds all key requirements). "
            "Base score primarily on: required skills coverage (50%), experience level fit (30%), domain/industry alignment (20%)."
        )
    )
    match_reasoning: str = Field(
        description=(
            "2-3 sentences explaining WHY the profile_match score was given. "
            "Mention specific strengths and specific gaps that influenced the score."
        )
    )
    matching_skills: list[str] = Field(
        description=(
            "Skills from the resume that DIRECTLY match the required or preferred skills mentioned in the job description. "
            "Only include confirmed matches — do not guess or infer."
        )
    )
    missing_skills: list[str] = Field(
        description=(
            "Skills or qualifications explicitly required or strongly preferred in the job description "
            "that are NOT present anywhere in the resume. List only factual gaps."
        )
    )
    recommendation: str = Field(
        description=(
            "A final hiring recommendation. Strictly one of: "
            "'Strongly Recommended', 'Recommended', 'Consider with Reservations', 'Not Recommended'. "
            "Base this on the profile_match score and overall fit."
        )
    )


# ── Prompt ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are an expert technical recruiter and resume analyst with 15+ years of experience.
Your task is to analyze a candidate's resume against a job description and return a structured evaluation.

Today's date: {date.today().strftime("%B %d, %Y")}


Rules:
- Extract information ONLY from what is explicitly written. Do not hallucinate or infer unstated facts.
- For profile_match, follow the scoring rubric exactly — do not give arbitrary scores.
- Distinguish clearly between "matching_skills" (present in resume AND required in JD) vs "missing_skills" (required in JD but absent in resume).
- Be objective and consistent.
"""

def build_prompt(jd_text: str, resume_text: str) -> str:
    return f"""{SYSTEM_PROMPT}
        === JOB DESCRIPTION ===
        {jd_text.strip()}
        === CANDIDATE RESUME ===
        {resume_text.strip()}
        Analyze the above and return the structured profile analysis.
        """

# ── Usage ────────────────────────────────────────────────────────────────────
model_with_struct = model.with_structured_output(ProfileAnalysis, include_raw=False)

async def analyze_resume_function(jd_cv_data):
    # Option A: if jd and resume are already combined in jd_cv_data
    res = await model_with_struct.ainvoke(build_prompt(
        jd_text=jd_cv_data["text"],       # your job description string
        resume_text=jd_cv_data["job_description"]  # your resume string
    ))


    # json_data = res.model_dump_json()
    return res
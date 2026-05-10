import os
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from datetime import date
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()

# model = init_chat_model("gpt-4.1")
model = ChatGroq(
    # model="meta-llama/llama-4-scout-17b-16e-instruct",  
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)
class InterviewConclusion(BaseModel):
    # --- Candidate Info ---
    performance_summary: str = Field(description="A brief summary of the candidate's performance in the interview.")
    
    technical_depth:float = Field(description="Technical depth of the candidate out of 5.")
    communication:float = Field(description="Communication skills of the candidate out of 5.")
    confidence:float = Field(description="Confidence of the candidate out of 5.")
    hirability_score:float = Field(description="Hirability score of the candidate out of 10.")
    key_strengths: list[str] = Field(description="Key strengths of the candidate.")
    areas_to_improve: list[str] = Field(description="Areas where the candidate needs to improve.")
    actionable_items: list[str] = Field(description="Actionable items for the candidate.")




# ── Prompt ──────────────────────────────────────────────────────────────────
def format_transcript(messages: list) -> str:
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)

def build_prompt(transcript: str, job_title: str) -> str:
    formatted = format_transcript(transcript)
    return f"""
        
         You are an expert interview evaluator.
        The candidate appeared for the role of {job_title}

         Interview Transcript:
        {formatted}
        Analyze the candidate's performance thoroughly.
        Provide an honest evaluation of:
        - technical competency
        - communication
        - confidence
        - hirability
        - strengths
        - weaknesses
        - actionable improvements

        """
        # Analyze the above and return the structured profile analysis.
        #  Evaluate the candidate and return a JSON object with EXACTLY these fields:
        # - performance_summary: string (3-4 sentence summary)
        # - technical_depth: float between 0-5
        # - communication: float between 0-5
        # - confidence: float between 0-5
        # - hirability_score: float between 0-10
        # - key_strengths: array of 3-5 strings
        # - areas_to_improve: array of 3-5 strings
        # - actionable_items: array of 3-5 strings (concrete next steps for candidate)

        # Return ONLY valid JSON, no explanation.

# ── Usage ────────────────────────────────────────────────────────────────────
model_with_struct = model.with_structured_output(InterviewConclusion, include_raw=False)

async def conclude_interview(transcript: str, job_title: str):
    # Option A: if jd and resume are already combined in jd_cv_data
    res = await model_with_struct.ainvoke(build_prompt(transcript, job_title))


    # json_data = res.model_dump_json()
    return res
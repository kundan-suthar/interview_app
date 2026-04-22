from app.db.database import SessionDep
from app.models.interview_session import InterviewSession
from app.models.mock_interview import MockInterview
from app.models.interview_conclusion import InterviewConclusion
from app.services.conclude_llm import conclude_interview


class InterviewConclusionService:

    async def generate_and_save(
        self,
        session: InterviewSession,
        mock_interview: MockInterview,
        db: SessionDep
    ) -> InterviewConclusion:

        

        # 2. Create conclusion row immediately with pending status
        conclusion = InterviewConclusion(
            session_id=session.session_id,
            mock_interview_id=mock_interview.id,
            analysis_status="pending"
        )
        db.add(conclusion)
        await db.commit()

        # 3. Run LLM analysis
        try:
            analysis = await self._run_llm_analysis(
                messages=session.messages,
                job_title=mock_interview.resume_analysis.required_job_title
            )
            # 4. Update with results
            conclusion.performance_summary = analysis.performance_summary
            conclusion.technical_depth    = analysis.technical_depth
            conclusion.communication      = analysis.communication
            conclusion.confidence         = analysis.confidence
            conclusion.hirability_score   = analysis.hirability_score
            conclusion.key_strengths      = analysis.key_strengths
            conclusion.areas_to_improve   = analysis.areas_to_improve
            conclusion.actionable_items   = analysis.actionable_items
            conclusion.analysis_status    = "completed"

        except Exception as e:
            conclusion.analysis_status = "failed"
            # log e
            print("error in llm analysis",e)

        await db.commit()
        return conclusion


    async def _run_llm_analysis(
        self, messages: dict,
        job_title: str
    ):

        # transcript = self._format_transcript(messages)
        transcript = messages
        response = await conclude_interview(transcript, job_title)
        print(response)
        return response


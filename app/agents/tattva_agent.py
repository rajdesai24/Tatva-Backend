# app/agents/tattva_agent.py
from typing import Dict, List
from app.services.claim_extractor import ClaimExtractor
from app.services.query_planner import QueryPlanner
from app.services.evidence_gatherer import EvidenceGatherer
from app.services.verdict_synthesizer import VerdictSynthesizer
from app.services.bias_analyzer import BiasAnalyzer
from app.services.scorer import Scorer
from app.models.input_models import TattvaInput
from app.models.output_models import TattvaOutput
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from app.utils.prompts import SUMMARY_PROMPT
from app.config import get_settings
from app.services.supabase_logger import supabase_logger
import asyncio
import logging
import uuid
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TattvaAgent:
    def __init__(self):
        self.claim_extractor = ClaimExtractor()
        self.query_planner = QueryPlanner()
        self.evidence_gatherer = EvidenceGatherer()
        self.verdict_synthesizer = VerdictSynthesizer()
        self.bias_analyzer = BiasAnalyzer()
        self.scorer = Scorer()
        
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
            max_output_tokens=settings.MAX_TOKENS
        )
    
    async def process(self, input_data: TattvaInput) -> TattvaOutput:
        """Main processing pipeline with async Supabase logging."""
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())

        text = input_data.transcript.text
        beliefs = [b.dict() for b in input_data.beliefs] if input_data.beliefs else []

        # Log agent start
        await supabase_logger.log_agent_start(
            request_id=request_id,
            input_data={
                "content_type": input_data.content_type,
                "text_length": len(text),
                "beliefs_count": len(beliefs)
            }
        )

        try:
            print("Step 1: Extracting claims...")
            claims = self.claim_extractor.extract_claims(text)

            # Log claim extraction
            await supabase_logger.log_step(
                request_id=request_id,
                step_name="claim_extraction",
                step_data={"claims_count": len(claims)}
            )

            if not claims:
                await supabase_logger.log_agent_complete(
                    request_id=request_id,
                    result={"message": "No verifiable claims found"},
                    status="success"
                )
                return self._create_empty_output("No verifiable claims found in content.")

            print(f"Step 2-6: Processing {len(claims)} claims...")
            processed_claims = []

            for i, claim in enumerate(claims):
                print(f"  Processing claim {i+1}/{len(claims)}: {claim.get('text', '')[:50]}...")

                # Query planning
                query_plan = self.query_planner.create_query_plan(claim)
                claim['query_plan'] = query_plan

                await supabase_logger.log_step(
                    request_id=request_id,
                    step_name=f"query_planning_claim_{i+1}",
                    step_data={"claim_text": claim.get('text', '')[:100]}
                )

                # Evidence gathering
                evidence = self.evidence_gatherer.gather_evidence(claim, query_plan)

                await supabase_logger.log_step(
                    request_id=request_id,
                    step_name=f"evidence_gathering_claim_{i+1}",
                    step_data={"evidence_count": len(evidence) if isinstance(evidence, list) else 1}
                )

                # Verdict synthesis
                verdict_result = self.verdict_synthesizer.synthesize_verdict(claim, evidence)
                claim['verdict'] = verdict_result['verdict']
                claim['evidence_strength'] = verdict_result['evidence_strength']

                await supabase_logger.log_step(
                    request_id=request_id,
                    step_name=f"verdict_synthesis_claim_{i+1}",
                    step_data={
                        "verdict": claim['verdict'].get('label'),
                        "evidence_strength": claim['evidence_strength']
                    }
                )

                processed_claims.append(claim)

            print("Step 7: Calculating scores...")
            scores = self.scorer.calculate_scores(processed_claims, beliefs)

            await supabase_logger.log_step(
                request_id=request_id,
                step_name="score_calculation",
                step_data={
                    "tattva_score": scores['tattva_score'],
                    "reality_distance": scores['reality_distance']
                }
            )

            print("Step 8: Analyzing bias...")
            bias_context = self.bias_analyzer.analyze_bias(text, processed_claims)

            await supabase_logger.log_step(
                request_id=request_id,
                step_name="bias_analysis",
                step_data={
                    "bias_signals_count": len(bias_context.get('bias_signals', [])),
                    "rhetoric_count": len(bias_context.get('rhetoric', []))
                }
            )

            print("Step 9: Generating summary...")
            summary = self._generate_summary(text, len(processed_claims), scores['tattva_score'])

            await supabase_logger.log_step(
                request_id=request_id,
                step_name="summary_generation",
                step_data={"summary_length": len(summary)}
            )

            limitations = self._identify_limitations(processed_claims, input_data)

            output = TattvaOutput(
                summary=summary,
                claims=processed_claims,
                tattva_score=scores['tattva_score'],
                reality_distance=scores['reality_distance'],
                bias_context=bias_context,
                limitations=limitations
            )

            # Log successful completion
            await supabase_logger.log_agent_complete(
                request_id=request_id,
                result={
                    "claims_processed": len(processed_claims),
                    "tattva_score": scores['tattva_score']
                },
                status="success"
            )

            return output

        except Exception as e:
            # Log error
            await supabase_logger.log_error(
                request_id=request_id,
                step="processing",
                error_message=str(e),
                error_data={"error_type": type(e).__name__}
            )
            raise
    
    def _generate_summary(self, text: str, num_claims: int, tattva_score: float) -> str:
        """Generate overall summary."""
        prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "text": text[:1000],
            "num_claims": num_claims,
            "tattva_score": round(tattva_score, 1)
        })
        logger.info("=" * 80)
        logger.info("GEMINI RESPONSE FOR agent EXTRACTION:")
        logger.info(f"Raw Response:\n{response.content}")
        logger.info("=" * 80)

        return response.content.strip()
    
    def _identify_limitations(self, claims: List[Dict], input_data: TattvaInput) -> List[str]:
        """Identify limitations in the analysis."""
        limitations = []
        
        unverified_count = sum(1 for c in claims if c['verdict']['label'] == 'unverified')
        if unverified_count > 0:
            limitations.append(f"{unverified_count} claims could not be verified due to insufficient evidence")
        
        low_evidence = sum(1 for c in claims if c.get('evidence_strength', 1.0) < 0.35)
        if low_evidence > 0:
            limitations.append(f"{low_evidence} claims have weak supporting evidence")
        
        if input_data.content_type == "youtube":
            limitations.append("Analysis based on transcript only; visual elements not verified")
        
        time_ambiguous = sum(1 for c in claims if not c.get('time_refs'))
        if time_ambiguous > len(claims) * 0.5:
            limitations.append("Many claims lack clear time references, affecting verification accuracy")
        
        search_failures = sum(1 for c in claims if not c.get('evidence_strength', 1.0) > 0.2)
        if search_failures > 0:
            limitations.append(f"Search returned limited results for {search_failures} claims")
        
        return limitations if limitations else ["No significant limitations identified"]
    
    def _create_empty_output(self, reason: str) -> TattvaOutput:
        """Create empty output when no claims found."""
        return TattvaOutput(
            summary=reason,
            claims=[],
            tattva_score=0.0,
            reality_distance={
                "status": "needs_user_input",
                "value": 0.0,
                "notes": reason
            },
            bias_context={
                "bias_signals": [],
                "rhetoric": [],
                "missing_context": [],
                "notes": reason
            },
            limitations=[reason]
        )
# app/services/verdict_synthesizer.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict
import json
import re
from app.utils.prompts import VERDICT_SYNTHESIS_PROMPT
from app.utils.calibration import calibrate_probability, calculate_evidence_strength
from app.config import get_settings
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VerdictSynthesizer:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
            max_output_tokens=settings.MAX_TOKENS
        )
        self.calibration_temp = settings.CALIBRATION_TEMPERATURE
    
    def synthesize_verdict(self, claim: Dict, evidence: Dict) -> Dict:
        """Synthesize final verdict from evidence."""
        prompt = ChatPromptTemplate.from_template(VERDICT_SYNTHESIS_PROMPT)
        chain = prompt | self.llm
        
        evidence_summary = json.dumps(evidence, indent=2)
        
        response = chain.invoke({
            "claim_text": claim.get('text', ''),
            "evidence_summary": evidence_summary
        })
        logger.info("=" * 80)
        logger.info("GEMINI RESPONSE FOR VERDICT:")
        logger.info(f"Claim: {claim.get('text', '')[:100]}")
        logger.info(f"Raw Response:\n{response.content}")
        logger.info("=" * 80)

        try:
            content = response.content
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            elif content.strip().startswith('{'):
                pass
            else:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
            
            result = json.loads(content)
            verdict = result.get('verdict', {})
            
            truth_prob = verdict.get('truth_prob', 0.5)
            verdict['truth_prob_cal'] = calibrate_probability(
                truth_prob, 
                self.calibration_temp
            )
            
            evidence_strength = self._calculate_evidence_strength(evidence)
            
            return {
                "verdict": verdict,
                "evidence_strength": evidence_strength
            }
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse verdict JSON: {e}")
            return {
                "verdict": {
                    "label": "unverified",
                    "truth_prob": 0.5,
                    "truth_prob_cal": calibrate_probability(0.5, self.calibration_temp),
                    "explanation": "Unable to synthesize verdict from available evidence.",
                    "citations": [],
                    "gaps": ["Evidence evaluation failed"],
                    "modalities_check": {
                        "ooc_risk": False,
                        "notes": "No modality check performed"
                    }
                },
                "evidence_strength": 0.1
            }
    
    def _calculate_evidence_strength(self, evidence: Dict) -> float:
        """Calculate composite evidence strength score."""
        evidence_items = evidence.get('evidence_items', [])
        
        if not evidence_items:
            return 0.1
        
        avg_credibility = sum(e.get('credibility', 0.5) for e in evidence_items) / len(evidence_items)
        avg_specificity = sum(e.get('specificity', 0.5) for e in evidence_items) / len(evidence_items)
        avg_recency = sum(e.get('recency', 0.5) for e in evidence_items) / len(evidence_items)
        
        unique_domains = len(set(self._extract_domain(e.get('source_url', '')) for e in evidence_items))
        diversity = min(unique_domains / 5.0, 1.0)
        
        modality_align = 0.8
        primary_source_bonus = 0.5
        
        return calculate_evidence_strength(
            credibility=avg_credibility,
            specificity=avg_specificity,
            recency=avg_recency,
            diversity=diversity,
            modality_align=modality_align,
            primary_source_bonus=primary_source_bonus
        )
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else url
# app/services/bias_analyzer.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, List
import json
import re
from app.utils.prompts import BIAS_ANALYSIS_PROMPT
from app.config import get_settings
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BiasAnalyzer:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
            max_output_tokens=settings.MAX_TOKENS
        )
    
    def analyze_bias(self, text: str, claims: List[Dict]) -> Dict:
        """Analyze content for bias and missing context."""
        prompt = ChatPromptTemplate.from_template(BIAS_ANALYSIS_PROMPT)
        chain = prompt | self.llm
        
        claims_summary = "\n".join([
            f"- {c.get('text', '')} [{c.get('type', '')}]"
            for c in claims[:10]
        ])
        
        response = chain.invoke({
            "text": text[:3000],
            "claims_summary": claims_summary
        })
        logger.info("=" * 80)
        logger.info("GEMINI RESPONSE FOR bias EXTRACTION:")
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
            return result.get('bias_context', {
                "bias_signals": [],
                "rhetoric": [],
                "missing_context": [],
                "notes": "Unable to analyze bias"
            })
        except json.JSONDecodeError as e:
            print(f"Failed to parse bias analysis JSON: {e}")
            return {
                "bias_signals": [],
                "rhetoric": [],
                "missing_context": [],
                "notes": "Bias analysis failed"
            }
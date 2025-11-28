# app/services/evidence_gatherer.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from typing import List, Dict
import json
import re
from app.utils.prompts import EVIDENCE_EVALUATION_PROMPT
from app.config import get_settings
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvidenceGatherer:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
            max_output_tokens=settings.MAX_TOKENS
        )
        self.search = DuckDuckGoSearchAPIWrapper()
    
    def gather_evidence(self, claim: Dict, query_plan: List[Dict]) -> Dict:
        """Gather and evaluate evidence for a claim."""
        all_results = []
        domains_seen = {}
        
        for query_item in query_plan[:6]:
            try:
                results = self.search.results(
                    query_item['query'],
                    max_results=5
                )
                
                for result in results:
                    domain = self._extract_domain(result.get('link', ''))
                    if domains_seen.get(domain, 0) < 2:
                        all_results.append(result)
                        domains_seen[domain] = domains_seen.get(domain, 0) + 1
                
            except Exception as e:
                print(f"Search error for query '{query_item['query']}': {e}")
                continue
        
        if not all_results:
            return {
                "evidence_items": [],
                "overall_assessment": "No evidence found",
                "search_successful": False
            }
        
        evidence_evaluation = self._evaluate_evidence(claim, all_results)
        evidence_evaluation['search_successful'] = True
        return evidence_evaluation
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else url
    
    def _evaluate_evidence(self, claim: Dict, search_results: List[Dict]) -> Dict:
        """Use LLM to evaluate evidence quality."""
        prompt = ChatPromptTemplate.from_template(EVIDENCE_EVALUATION_PROMPT)
        chain = prompt | self.llm
        
        results_text = "\n\n".join([
            f"Title: {r.get('title', 'N/A')}\nURL: {r.get('link', 'N/A')}\nSnippet: {r.get('snippet', 'N/A')}"
            for r in search_results[:10]
        ])
        
        response = chain.invoke({
            "claim_text": claim.get('text', ''),
            "search_results": results_text
        })
        logger.info("=" * 80)
        logger.info("GEMINI RESPONSE FOR evidence EXTRACTION:")
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
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Failed to parse evidence evaluation JSON: {e}")
            return {
                "evidence_items": [],
                "overall_assessment": "Failed to evaluate evidence"
            }
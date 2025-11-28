# app/services/query_planner.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict
import json
import re
from app.utils.prompts import QUERY_PLANNING_PROMPT
from app.config import get_settings
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryPlanner:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
            max_output_tokens=settings.MAX_TOKENS
        )
    
    def create_query_plan(self, claim: Dict) -> List[Dict]:
        """Create search query plan for a claim."""
        prompt = ChatPromptTemplate.from_template(QUERY_PLANNING_PROMPT)
        chain = prompt | self.llm
        
        response = chain.invoke({
            "claim_text": claim.get('text', ''),
            "claim_type": claim.get('type', ''),
            "entities": ', '.join(claim.get('named_entities', [])),
            "time_refs": ', '.join(claim.get('time_refs', []))
        })
        
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
            return result.get('query_plan', [])
        except json.JSONDecodeError as e:
            print(f"Failed to parse query plan JSON: {e}")
            return []
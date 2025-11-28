# app/services/claim_extractor.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict
import json
import re
from app.utils.prompts import CLAIM_EXTRACTION_PROMPT
from app.config import get_settings
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaimExtractor:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
            max_output_tokens=settings.MAX_TOKENS
        )
    
    def extract_claims(self, text: str) -> List[Dict]:
        """Extract atomic claims from text."""
        prompt = ChatPromptTemplate.from_template(CLAIM_EXTRACTION_PROMPT)
        chain = prompt | self.llm
        
        response = chain.invoke({"text": text})
        logger.info("=" * 80)
        logger.info("GEMINI RESPONSE FOR CLAIM EXTRACTION:")
        logger.info(f"Raw Response:\n{response.content}")
        logger.info("=" * 80)

        try:
            content = response.content
            # Clean up markdown code blocks
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
            return result.get('claims', [])
        except json.JSONDecodeError as e:
            print(f"Failed to parse claims JSON: {e}")
            print(f"Response: {response.content}")
            return []
# app/utils/prompts.py

CLAIM_EXTRACTION_PROMPT = """You are an expert claim extractor. Analyze the following text and extract atomic, checkable claims.

Text: {text}

Extract claims following these rules:
1. Each claim must be atomic (one verifiable statement)
2. Split conjunctions into separate claims
3. Merge duplicates
4. Assign prominence (0-1) based on centrality to the content
5. Extract named entities and time references
6. Classify as: fact, prediction, or opinion_with_fact_core
7. Extract only key claims not more than 5 claims

Return a JSON array of claims with structure:
{{
  "claims": [
    {{
      "id": "1",
      "text": "claim text",
      "type": "fact",
      "prominence": 0.8,
      "time_refs": ["2024"],
      "named_entities": ["Entity Name"]
    }}
  ]
}}

Only return valid JSON, no additional text."""

QUERY_PLANNING_PROMPT = """You are an expert search strategist. Create a comprehensive query plan for verifying this claim.

Claim: {claim_text}
Type: {claim_type}
Named Entities: {entities}
Time References: {time_refs}

Create 2 targeted search queries with:
1. Evidence type preferences: primary/official, factcheck, reference, news, academic
2. Time windows when relevant
3. Geographic disambiguation if needed
4. Multiple angles to verify the claim

Return JSON:
{{
  "query_plan": [
    {{
      "query": "specific search query",
      "evidence_type": "factcheck",
      "time_window": "2024"
    }}
  ]
}}

Only return valid JSON, no additional text."""



EVIDENCE_EVALUATION_PROMPT = """You are an expert evidence evaluator. Rate these search results for the given claim.

Claim: {claim_text}
Search Results: {search_results}

For each relevant source, evaluate:
1. Stance: supports/refutes/neutral
2. Credibility (0-1): based on publisher reputation, primary vs secondary source
3. Specificity (0-1): how directly it addresses the claim
4. Recency (0-1): how recent and relevant
5. Quote: extract a SHORT, ESSENTIAL verbatim quote (15-30 words maximum) that captures the key evidence

CRITICAL: Quotes must be BRIEF (under 30 words). Extract only the most relevant sentence fragment.

Return JSON:
{{
  "evidence_items": [
    {{
      "source_url": "url",
      "publisher": "name",
      "date": "YYYY-MM-DD",
      "stance": "supports",
      "quote": "brief exact quote under 30 words",
      "credibility": 0.9,
      "specificity": 0.8,
      "recency": 0.7
    }}
  ],
  "overall_assessment": "brief summary"
}}

Remember: Keep quotes SHORT and ESSENTIAL (under 30 words).
Only return valid JSON, no additional text."""

VERDICT_SYNTHESIS_PROMPT = """You are an expert fact-checker. Synthesize a verdict from the evidence.

Claim: {claim_text}
Evidence: {evidence_summary}

Synthesize verdict considering:
1. Weight evidence by source strength
2. Resolve conflicts explicitly
3. Reward source diversity
4. Be transparent about uncertainty

Determine:
1. Label: true, mostly_true, mixed, mostly_false, false, or unverified
2. Truth probability (0-1): your confidence before calibration
3. Explanation: clear, non-expert language (2-4 sentences)
4. Top citations (max 5 with real URLs)
5. Gaps: what evidence would strengthen this verdict
6. Modality check: any out-of-context risks

CRITICAL: For citations, include SHORT quotes (15-30 words maximum). Extract only the most essential evidence.

Return JSON:
{{
  "verdict": {{
    "label": "mostly_true",
    "truth_prob": 0.75,
    "explanation": "...",
    "citations": [
      {{
        "title": "...",
        "url": "https://...",
        "publisher": "...",
        "date": "2024-01-15",
        "quote": "brief essential quote under 30 words"
      }}
    ],
    "gaps": ["..."],
    "modalities_check": {{
      "ooc_risk": false,
      "notes": "..."
    }}
  }}
}}

Remember: Keep quotes BRIEF (under 30 words) and focused on key evidence.
Only return valid JSON, no additional text."""

BIAS_ANALYSIS_PROMPT = """You are an expert bias detector. Analyze this content for bias and context issues.

Content: {text}
Claims: {claims_summary}

Identify:
1. Bias signals: cherry-picking, selective framing, emotional language
2. Rhetoric: persuasive techniques, logical fallacies
3. Missing context: important baseline information not provided
4. Overall notes on neutrality

Return JSON:
{{
  "bias_context": {{
    "bias_signals": ["signal 1", "signal 2"],
    "rhetoric": ["technique 1"],
    "missing_context": ["context 1"],
    "notes": "overall assessment"
  }}
}}

Only return valid JSON, no additional text."""

SUMMARY_PROMPT = """Create a concise 1-3 sentence summary of this fact-check analysis.

Original Content: {text}
Claims Analyzed: {num_claims}
Overall Tattva Score: {tattva_score}

Provide a neutral, informative summary that captures the main findings.

Return only the summary text, no JSON."""





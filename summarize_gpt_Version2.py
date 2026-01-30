# summarize_gpt.py
import os
import time
import json
import openai
from typing import List, Dict, Any

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"

def summarize_history_for_location(observations: List[Dict[str, Any]], location_name: str, parameter: str = "pm25") -> Dict[str, Any]:
    """
    Use GPT-4o to summarize a list of observations (time-ordered).
    The function asks for:
     - short 3-4 sentence summary of trend (improving/worsening/variable)
     - detected exceedances (dates when AQI >= unhealthy thresholds)
     - recommendations/actionable notes
     - a numeric severity score 0-1
    Returns dict with keys: summary, score, exceedances, notes
    """
    # Build compact textual table for the model
    rows = []
    for o in observations:
        rows.append({
            "date_utc": o.get("date_utc"),
            "aqi": o.get("aqi"),
            "value": o.get("value"),
            "parameter": o.get("parameter"),
            "source": o.get("source")
        })
    prompt = f"""
You are an environmental analyst assistant. Given observations for {location_name} and parameter {parameter}, produce a JSON object.

Observations (JSON array):
{json.dumps(rows, indent=2)}

Return a JSON object only:
{{
  "summary": "<3-4 sentence summary: trend, variability, any likely cause if evident>",
  "score": 0.0,
  "exceedances": [{{"date": "YYYY-MM-DD", "aqi": 150, "level": "Unhealthy"}}],
  "recommendations": ["short actionable recommendation 1", "recommendation 2"],
  "notes": "<optional short notes>"
}}
- score: 0.0-1.0 (0 low concern, 1 high concern)
- For exceedances include only AQI >= 101 (Unhealthy for Sensitive Groups) and above, map numeric AQI to common level names.
- Only return valid JSON.
"""
    for attempt in range(3):
        try:
            resp = openai.ChatCompletion.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500
            )
            text = resp["choices"][0]["message"]["content"]
            parsed = json.loads(text)
            # Normalize score
            parsed["score"] = float(parsed.get("score") or 0.0)
            return parsed
        except Exception as e:
            wait = 2 ** attempt
            time.sleep(wait)
    return {"summary": "", "score": 0.0, "exceedances": [], "recommendations": [], "notes": "summarization failed"}
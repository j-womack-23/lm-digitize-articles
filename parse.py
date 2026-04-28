"""OpenAI-based article structure detection."""

import json
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_SYSTEM_PROMPT = """\
You are an expert at parsing magazine articles. Given the raw extracted text of a magazine article, \
identify and return its structural components as a JSON object.

The articles are from a local lifestyle/community magazine. They typically feature:
- A main title (e.g. a business or organization name)
- An optional photo credit line (e.g. "PHOTOS BY ...")
- One or more introductory paragraphs about the organization/topic
- Named sections, usually introduced by a heading like "MEET [PERSON NAME], [TITLE]" or similar
- Each section has one or more bio/description paragraphs
- An optional contact block at the end with address, phone, and/or website

Return ONLY a valid JSON object matching this exact schema — no prose, no markdown:
{
  "title": "string",
  "photo_credit": "string or null",
  "intro_paragraphs": ["string", ...],
  "sections": [
    {
      "heading": "string",
      "paragraphs": ["string", ...]
    }
  ],
  "contact": {
    "address": "string or null",
    "phone": "string or null",
    "website": "string or null"
  }
}

Rules:
- Reconstruct full, clean sentences/paragraphs from the raw text (fix broken hyphenation, line-break artifacts, etc.)
- Preserve original capitalization of headings
- If a field is absent, use null (for strings) or [] (for arrays)
- Do not invent content that is not in the source text
"""


def parse_article(raw_text: str) -> dict:
    """
    Send extracted PDF text to OpenAI and return a structured article dict.

    Raises ValueError if the model returns invalid JSON.
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse the following magazine article text:\n\n{raw_text}"},
        ],
        max_tokens=4096,
        temperature=0,
    )

    raw_json = response.choices[0].message.content.strip()

    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"OpenAI returned invalid JSON: {exc}\n\nRaw response:\n{raw_json}") from exc

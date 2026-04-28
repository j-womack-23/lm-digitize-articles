"""Claude AI-based article structure detection."""

import json
import os

import anthropic
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
    Send extracted PDF text to Claude and return a structured article dict.

    Raises ValueError if Claude returns invalid JSON.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Parse the following magazine article text:\n\n{raw_text}",
            }
        ],
    )

    raw_json = message.content[0].text.strip()

    if raw_json.startswith("```"):
        raw_json = raw_json.split("\n", 1)[1]
        raw_json = raw_json.rsplit("```", 1)[0]

    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Claude returned invalid JSON: {exc}\n\nRaw response:\n{raw_json}") from exc

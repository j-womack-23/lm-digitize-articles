"""HTML generation from parsed article data targeting the WP Bakery template structure.

Template layout (four vc_row sections):
  TOP_DOCS_BADGE       — static "Top Docs" badge image row
  TOP_DOCS_DR_PRACTICE — practice photo + title heading + byline/photo-credit
  TOP_DOCS_BODY        — 3/4 body text column + 1/4 sidebar quote column
  TOP_DOCS_CONTACT     — separator, CONTACT heading, address, website/phone buttons
"""

import html
import os
import re
from pathlib import Path
from urllib.parse import quote as urlquote


def _esc(text: str | None) -> str:
    return html.escape(text or "", quote=False)


def _attr(text: str | None) -> str:
    """Escape text for use inside a WP Bakery shortcode double-quoted attribute."""
    return (text or "").replace('"', "&quot;").replace("[", "&#91;").replace("]", "&#93;")


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text)


def _address_html(address: str | None) -> str:
    """Split address into lines and join with <br>."""
    if not address:
        return ""
    if "\n" in address:
        parts = [p.strip() for p in address.split("\n") if p.strip()]
    else:
        parts = [p.strip() for p in re.split(r",\s*(?=(?:Suite|Ste|Unit|#)\s)", address, flags=re.IGNORECASE) if p.strip()]
    return "<br>\n".join(f'<span class="s1">{_esc(p)}</span>' for p in parts)


def _phone_digits(phone: str | None) -> str:
    return re.sub(r"\D", "", phone or "")


def _website_link(url: str | None) -> str:
    if not url:
        return "url:|target:_blank"
    encoded = urlquote(url, safe=":/.-_~")
    return f"url:{encoded}|target:_blank"


def _phone_link(phone: str | None) -> str:
    digits = _phone_digits(phone)
    return f"url:tel%3A{digits}"


def _body_html(article: dict) -> str:
    parts: list[str] = []
    for para in article.get("intro_paragraphs") or []:
        if para.strip():
            parts.append(f'<p class="p1">{_esc(para)}</p>')
    for section in article.get("sections") or []:
        heading = (section.get("heading") or "").strip()
        if heading:
            parts.append(f'<h4 class="p2">{_esc(heading)}</h4>')
        for para in section.get("paragraphs") or []:
            if para.strip():
                parts.append(f'<p class="p1">{_esc(para)}</p>')
    return "\n".join(parts)


def generate_html(article: dict) -> str:
    """Return WP Bakery shortcode markup ready to paste into the WordPress Text editor."""
    title = _attr(article.get("title") or "")
    photo_credit = (article.get("photo_credit") or "").strip()
    contact = article.get("contact") or {}

    byline = (
        f'<h6 style="font-family: Korolev; font-size: 1.2rem; text-transform: uppercase;'
        f' letter-spacing: 0.075rem;">photo by <strong>{_esc(photo_credit)}</strong></h6>'
        if photo_credit else ""
    )

    address_block = _address_html(contact.get("address"))
    body = _body_html(article)

    return (
        '[vc_row el_id="TOP_DOCS_BADGE"]'
        '[vc_column]'
        '[vc_single_image image="136598" css_animation="fadeInLeft" css=""]'
        '[/vc_column][/vc_row]\n'

        '[vc_row el_id="TOP_DOCS_DR_PRACTICE"]'
        '[vc_column]'
        '[vc_single_image img_size="large" css_animation="fadeInUp"]'
        f'[vc_custom_heading text="{title}"'
        ' font_container="tag:h6|font_size:2.8rem|text_align:left|line_height:3rem"'
        ' google_fonts="font_family:Roboto%3A100%2C100italic%2C300%2C300italic%2Cregular'
        '%2Citalic%2C500%2C500italic%2C700%2C700italic%2C900%2C900italic'
        '|font_style:400%20regular%3A400%3Anormal"'
        ' css_animation="fadeInLeft" el_class="physician-name"]'
        '[vc_column_text css_animation="fadeInLeft"]\n'
        f'{byline}\n'
        '[/vc_column_text]'
        '[/vc_column][/vc_row]\n'

        '[vc_row css=".vc_custom_1709221887859{margin-bottom: -50px !important;}"'
        ' el_id="TOP_DOCS_BODY"]'
        '[vc_column css_animation="fadeIn" width="3/4"'
        ' css=".vc_custom_1697210407412{border-right-width: 5px !important;'
        'border-right-color: #a1bec6 !important;border-right-style: solid !important;}"]'
        '[vc_column_text css_animation="fadeIn"'
        ' css=".vc_custom_1701115894784{margin-top: -35px !important;}"]\n'
        f'{body}\n'
        '[/vc_column_text]'
        '[/vc_column]'
        '[vc_column width="1/4"'
        ' css=".vc_custom_1709221903615{border-left-width: 0px !important;'
        'border-left-color: #7d9da7 !important;}"'
        ' el_id="TOP_DOCS_QUOTE"]'
        '[vc_column_text css_animation="fadeIn"]\n'
        '<div style="border-top: 5px solid #7d9da7; padding-top: 2rem;">\n'
        '<p style="font-family: Lora serif; font-style: Italic; font-size: 1.6rem;'
        ' line-height: 1.6rem; margin-bottom: 2rem; padding-left: 2rem;'
        ' letter-spacing: 0.04rem;">&nbsp;</p>\n'
        '</div>\n'
        '[/vc_column_text]'
        '[/vc_column]'
        '[/vc_row]\n'

        '[vc_row el_id="TOP_DOCS_CONTACT"]'
        '[vc_column]'
        '[vc_separator css_animation="fadeIn"]'
        '[vc_custom_heading text="CONTACT"'
        ' font_container="tag:h6|font_size:2.2rem|text_align:left|color:%237d9da7"'
        ' google_fonts="font_family:Roboto%3A100%2C100italic%2C300%2C300italic%2Cregular'
        '%2Citalic%2C500%2C500italic%2C700%2C700italic%2C900%2C900italic'
        '|font_style:500%20bold%20regular%3A500%3Anormal"'
        ' css_animation="fadeInRight"]'
        '[vc_column_text css_animation="fadeIn"]\n'
        f'<p class="p1">{address_block}</p>\n'
        '[/vc_column_text]'
        '[vc_row_inner]'
        '[vc_column_inner width="1/4"]'
        '[vc_btn title="WEBSITE" align="center" i_icon_fontawesome="fas fa-globe"'
        f' css_animation="fadeInDown" button_block="true" add_icon="true" link="{_website_link(contact.get("website"))}"]'
        '[/vc_column_inner]'
        '[vc_column_inner width="1/4"]'
        '[vc_btn title="PHONE" align="center" i_icon_fontawesome="fas fa-phone"'
        f' css_animation="fadeInDown" button_block="true" add_icon="true" link="{_phone_link(contact.get("phone"))}"]'
        '[/vc_column_inner]'
        '[vc_column_inner width="1/4"][/vc_column_inner]'
        '[vc_column_inner width="1/4"][/vc_column_inner]'
        '[/vc_row_inner]'
        '[/vc_column][/vc_row]'
    )


def write_output(article: dict, pdf_path: str) -> str:
    """Write the generated WP Bakery markup to output/<slug>.html and return the path."""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    slug = _slugify(article.get("title") or os.path.splitext(os.path.basename(pdf_path))[0])
    out_path = output_dir / f"{slug}.html"
    out_path.write_text(generate_html(article), encoding="utf-8")
    return str(out_path)

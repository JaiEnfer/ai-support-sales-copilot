"""Website scraping helpers for demo-friendly knowledge base ingestion.

The goal here is not to be a full crawler. It is to turn a small business site
into cleaner, section-aware knowledge that produces stronger chatbot demos.
"""

from __future__ import annotations

import re
from collections import deque
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from backend.app.core.config import settings

HEADING_TAGS = {"h1", "h2", "h3"}
BLOCK_TAGS = {"p", "li", "blockquote", "div"}
IGNORED_TAGS = {"script", "style", "noscript", "svg"}
COMMON_SKILLS = [
    "artificial intelligence",
    "automation",
    "computer vision",
    "data analysis",
    "data science",
    "deep learning",
    "generative ai",
    "langchain",
    "large language models",
    "machine learning",
    "mlops",
    "natural language processing",
    "python",
    "rag",
    "react",
    "retrieval",
    "salesforce",
    "slack",
]
ROLE_PATTERNS = [
    "ai engineer",
    "ai consultant",
    "automation engineer",
    "data scientist",
    "founder",
    "machine learning engineer",
    "product engineer",
    "software engineer",
]
SECTION_HINTS = [
    "about",
    "experience",
    "expertise",
    "introduction",
    "overview",
    "profile",
    "skills",
    "tech stack",
]
SERVICE_HINTS = [
    "build",
    "deliver",
    "develop",
    "help",
    "offer",
    "provide",
    "service",
    "solution",
]
PRODUCT_HINTS = [
    "assistant",
    "copilot",
    "platform",
    "product",
    "saas",
    "tool",
    "workflow",
]


class _VisibleTextParser(HTMLParser):
    """Extract visible, section-aware text while skipping common page noise."""

    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._current_heading_parts: list[str] = []
        self._current_block_parts: list[str] = []
        self._active_heading = "Overview"
        self._inside_title = False
        self._inside_heading_tag: str | None = None
        self._inside_block_tag: str | None = None
        self._seen_blocks: set[tuple[str, str]] = set()
        self.links: list[str] = []
        self.title = ""
        self.meta_description = ""
        self.sections: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in IGNORED_TAGS:
            self._ignored_depth += 1
            return

        if tag == "title":
            self._inside_title = True
            return

        if tag in HEADING_TAGS:
            self._inside_heading_tag = tag
            self._current_heading_parts = []
            return

        if tag in BLOCK_TAGS:
            self._inside_block_tag = tag
            self._current_block_parts = []

        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

        if tag == "meta":
            metadata = dict(attrs)
            name = (metadata.get("name") or metadata.get("property") or "").lower()
            content = (metadata.get("content") or "").strip()
            if content and name in {"description", "og:description"} and not self.meta_description:
                self.meta_description = re.sub(r"\s+", " ", unescape(content)).strip()

    def handle_endtag(self, tag: str) -> None:
        if tag in IGNORED_TAGS and self._ignored_depth > 0:
            self._ignored_depth -= 1
            return

        if tag == "title":
            self._inside_title = False
            return

        if tag in HEADING_TAGS and self._inside_heading_tag == tag:
            heading = _clean_text(" ".join(self._current_heading_parts))
            if heading:
                self._active_heading = heading
            self._inside_heading_tag = None
            self._current_heading_parts = []
            return

        if tag in BLOCK_TAGS and self._inside_block_tag == tag:
            block_text = _clean_text(" ".join(self._current_block_parts))
            self._inside_block_tag = None
            self._current_block_parts = []
            if not _is_meaningful_text(block_text):
                return

            block_key = (self._active_heading, block_text)
            if block_key in self._seen_blocks:
                return

            self._seen_blocks.add(block_key)
            self.sections.append(
                {
                    "heading": self._active_heading,
                    "content": block_text,
                }
            )

    def handle_data(self, data: str) -> None:
        if self._ignored_depth > 0:
            return

        normalized = _clean_text(data)
        if not normalized:
            return

        if self._inside_title and not self.title:
            self.title = normalized
            return

        if self._inside_heading_tag:
            self._current_heading_parts.append(normalized)
            return

        if self._inside_block_tag:
            self._current_block_parts.append(normalized)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _is_meaningful_text(text: str) -> bool:
    """Filter out short, repetitive, or policy-heavy website fragments."""
    if len(text) < 20:
        return False

    lowered = text.lower()
    noisy_fragments = {
        "accept cookies",
        "all rights reserved",
        "cookie policy",
        "privacy policy",
        "skip to content",
        "terms of service",
    }
    return not any(fragment in lowered for fragment in noisy_fragments)


def _normalize_url(base_url: str, candidate_url: str) -> str | None:
    """Resolve relative links and keep only http(s) URLs."""
    resolved = urljoin(base_url, candidate_url)
    parsed = urlparse(resolved)
    if parsed.scheme not in {"http", "https"}:
        return None
    normalized_path = parsed.path or "/"
    return parsed._replace(fragment="", query="", path=normalized_path).geturl()


def _is_same_domain(root_url: str, candidate_url: str) -> bool:
    """Allow crawling only within the same host as the starting URL."""
    return urlparse(root_url).netloc == urlparse(candidate_url).netloc


def _link_priority(url: str) -> tuple[int, int]:
    """Prefer pages that usually explain the business best."""
    path = urlparse(url).path.lower().strip("/")
    preferred_terms = [
        "pricing",
        "service",
        "solution",
        "product",
        "about",
        "faq",
        "contact",
        "support",
        "feature",
        "integration",
        "portfolio",
        "project",
    ]
    for index, term in enumerate(preferred_terms):
        if term in path:
            return (0, index)

    if path in {"", "/"}:
        return (0, len(preferred_terms) + 1)

    return (1, len(path))


def _split_sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
        if sentence.strip()
    ]


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return unique_values


def _infer_entity_name(pages: list[dict[str, str]]) -> str:
    home_title = pages[0].get("title", "") if pages else ""
    if not home_title:
        return "Unknown business"

    for separator in ("|", " - ", " – ", ":"):
        if separator in home_title:
            candidate = home_title.split(separator)[0].strip()
            if candidate:
                return candidate

    return home_title.strip()


def _extract_roles(text: str) -> list[str]:
    lowered = text.lower()
    roles = [role.title() for role in ROLE_PATTERNS if role in lowered]
    return _dedupe_preserve_order(roles)


def _extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    skills = [skill.title() for skill in COMMON_SKILLS if skill in lowered]
    return _dedupe_preserve_order(skills)


def _extract_highlight_sentences(text: str, hints: list[str], limit: int = 3) -> list[str]:
    highlights: list[str] = []
    for sentence in _split_sentences(text):
        lowered = sentence.lower()
        if any(hint in lowered for hint in hints):
            highlights.append(sentence)
    return _dedupe_preserve_order(highlights)[:limit]


def _extract_section_highlights(pages: list[dict[str, str]], section_hints: list[str], limit: int = 4) -> list[str]:
    """Prefer sentences from sections whose headings suggest profile information."""
    highlights: list[str] = []
    for page in pages:
        for section in page.get("sections", []):
            heading = section.get("heading", "").lower()
            if not any(hint in heading for hint in section_hints):
                continue
            for sentence in _split_sentences(section.get("content", "")):
                highlights.append(sentence)

    return _dedupe_preserve_order(highlights)[:limit]


def _extract_contact_signals(text: str) -> list[str]:
    signals: list[str] = []
    email_matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_matches = re.findall(r"\+?\d[\d()\-\s]{7,}\d", text)

    for email in email_matches[:3]:
        signals.append(f"Email: {email}")
    for phone in phone_matches[:2]:
        signals.append(f"Phone: {re.sub(r'\\s+', ' ', phone).strip()}")

    return _dedupe_preserve_order(signals)


def _build_page_content(page: dict[str, str]) -> str:
    """Convert parsed page sections into cleaner retrieval text."""
    lines = [
        f"Page title: {page['title']}",
        f"Source URL: {page['url']}",
    ]

    if page.get("meta_description"):
        lines.append(f"Meta description: {page['meta_description']}")

    for section in page.get("sections", []):
        lines.append(f"{section['heading']}: {section['content']}")

    return "\n".join(lines).strip()


def build_website_summary(pages: list[dict[str, str]]) -> str:
    """Build a structured business summary from scraped pages."""
    if not pages:
        return ""

    entity_name = _infer_entity_name(pages)
    combined_text = "\n".join(page["content"] for page in pages)
    roles = _extract_roles(" ".join(page.get("title", "") for page in pages) + "\n" + combined_text)
    skills = _extract_skills(combined_text)
    section_highlights = _extract_section_highlights(pages, SECTION_HINTS)
    service_highlights = _extract_highlight_sentences(combined_text, SERVICE_HINTS)
    product_highlights = _extract_highlight_sentences(combined_text, PRODUCT_HINTS)
    about_highlights = _split_sentences(combined_text)[:3]
    contact_signals = _extract_contact_signals(combined_text)

    lines = [
        "Website Summary",
        f"Entity name: {entity_name}",
    ]

    if roles:
        lines.append(f"Primary roles: {', '.join(roles)}")

    if skills:
        lines.append(f"Key skills: {', '.join(skills[:8])}")

    if section_highlights:
        lines.append("Profile highlights:")
        lines.extend(f"- {item}" for item in section_highlights[:4])

    if service_highlights:
        lines.append("Services and offerings:")
        lines.extend(f"- {item}" for item in service_highlights)

    if product_highlights:
        lines.append("Products or platforms:")
        lines.extend(f"- {item}" for item in product_highlights)

    if about_highlights:
        lines.append("Business overview:")
        lines.extend(f"- {item}" for item in about_highlights)

    if contact_signals:
        lines.append("Contact signals:")
        lines.extend(f"- {item}" for item in contact_signals)

    lines.append("Source pages:")
    lines.extend(f"- {page['title']} ({page['url']})" for page in pages[:6])
    return "\n".join(lines).strip()


async def scrape_website_text(url: str, max_pages: int) -> list[dict[str, str]]:
    """Fetch section-aware text from a small set of same-domain pages."""
    normalized_start_url = _normalize_url(url, url)
    if not normalized_start_url:
        raise ValueError("Only http and https URLs are supported.")

    visited: set[str] = set()
    queued_urls: deque[str] = deque([normalized_start_url])
    pages: list[dict[str, str]] = []

    async with httpx.AsyncClient(
        timeout=settings.website_scrape_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": settings.website_scrape_user_agent},
    ) as client:
        while queued_urls and len(pages) < max_pages:
            current_url = queued_urls.popleft()
            if current_url in visited:
                continue

            visited.add(current_url)
            response = await client.get(current_url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                continue

            parser = _VisibleTextParser()
            parser.feed(response.text)

            if not parser.sections and not parser.meta_description:
                continue

            pages.append(
                {
                    "url": current_url,
                    "title": parser.title or urlparse(current_url).path or current_url,
                    "meta_description": parser.meta_description,
                    "sections": parser.sections,
                    "content": _build_page_content(
                        {
                            "url": current_url,
                            "title": parser.title or urlparse(current_url).path or current_url,
                            "meta_description": parser.meta_description,
                            "sections": parser.sections,
                        }
                    ),
                }
            )

            prioritized_links = sorted(
                parser.links,
                key=lambda link: _link_priority(urljoin(current_url, link)),
            )
            for link in prioritized_links:
                normalized_link = _normalize_url(current_url, link)
                if not normalized_link:
                    continue
                if normalized_link in visited:
                    continue
                if not _is_same_domain(normalized_start_url, normalized_link):
                    continue
                queued_urls.append(normalized_link)

    return pages

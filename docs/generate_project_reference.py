from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


DOCS_DIR = Path(__file__).resolve().parent
PDF_PATH = DOCS_DIR / "ai-support-sales-copilot-project-reference.pdf"
HOME_PREVIEW_PATH = DOCS_DIR / "home-preview.png"
ADMIN_PREVIEW_PATH = DOCS_DIR / "admin-preview.png"

PAGE_WIDTH = 1654
PAGE_HEIGHT = 2339
MARGIN = 110

NAVY = "#07111F"
SURFACE = "#0F1B2F"
SURFACE_SOFT = "#13243D"
ACCENT = "#58A6FF"
ACCENT_STRONG = "#2F7DF6"
MUTED = "#7387A7"
TEXT = "#F4F7FB"
INK = "#102033"
LIGHT_BG = "#F7FAFC"
CARD = "#FFFFFF"
BORDER = "#D7E2EE"
SUCCESS = "#26C281"
WARNING = "#F5B74F"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_H1 = load_font(48, bold=True)
FONT_H2 = load_font(28, bold=True)
FONT_H3 = load_font(22, bold=True)
FONT_BODY = load_font(20)
FONT_SMALL = load_font(17)
FONT_LABEL = load_font(16, bold=True)


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int = 10,
) -> int:
    x, y = xy
    line_height = font.size + line_gap
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def section_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str) -> None:
    draw.rounded_rectangle(box, radius=28, fill=CARD, outline=BORDER, width=2)
    draw.text((box[0] + 26, box[1] + 20), title, font=FONT_H3, fill=INK)


def draw_bullets(
    draw: ImageDraw.ImageDraw,
    items: list[str],
    xy: tuple[int, int],
    max_width: int,
    bullet_fill: str = ACCENT_STRONG,
) -> int:
    x, y = xy
    for item in items:
        draw.ellipse((x, y + 8, x + 10, y + 18), fill=bullet_fill)
        y = draw_wrapped_text(draw, item, (x + 24, y), FONT_BODY, INK, max_width - 24, line_gap=8) + 8
    return y


def draw_metric(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str, value: str) -> None:
    draw.rounded_rectangle(box, radius=22, fill=LIGHT_BG, outline=BORDER, width=2)
    draw.text((box[0] + 18, box[1] + 14), label.upper(), font=FONT_LABEL, fill=MUTED)
    draw.text((box[0] + 18, box[1] + 42), value, font=FONT_H3, fill=INK)


def create_home_preview() -> Image.Image:
    image = Image.new("RGB", (1360, 860), NAVY)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, 1360, 860), fill=NAVY)
    draw.ellipse((-120, -180, 380, 280), fill="#103357")
    draw.ellipse((1010, -100, 1450, 260), fill="#0D2D33")

    draw.rounded_rectangle((70, 55, 1290, 200), radius=32, fill=SURFACE, outline="#27415F", width=2)
    draw.text((110, 92), "Customer Workspace", font=FONT_LABEL, fill=ACCENT)
    draw.text((110, 126), "AI Support + Sales Copilot", font=FONT_H1, fill=TEXT)
    draw.rounded_rectangle((1080, 96, 1205, 145), radius=24, fill=SURFACE_SOFT, outline="#35577C", width=2)
    draw.text((1108, 110), "Grounded chat", font=FONT_SMALL, fill=TEXT)
    draw.rounded_rectangle((1218, 96, 1270, 145), radius=24, fill=ACCENT_STRONG)
    draw.text((1232, 110), "Admin", font=FONT_SMALL, fill=TEXT)

    draw.rounded_rectangle((70, 235, 920, 790), radius=34, fill=SURFACE, outline="#27415F", width=2)
    draw.text((110, 275), "Live Chat", font=FONT_LABEL, fill=ACCENT)
    draw.text((110, 305), "Assistant Conversation", font=FONT_H2, fill=TEXT)
    draw.rounded_rectangle((110, 365, 545, 455), radius=28, fill="#1A5FBE")
    draw.text((140, 392), "You", font=FONT_LABEL, fill="#D9EEFF")
    draw.text((140, 420), "Do you support Salesforce and Slack integrations?", font=FONT_BODY, fill=TEXT)
    draw.rounded_rectangle((180, 480, 840, 620), radius=28, fill=SURFACE_SOFT, outline="#2F4A6A", width=2)
    draw.text((212, 508), "Assistant", font=FONT_LABEL, fill=ACCENT)
    draw.text((212, 538), "Yes. The handbook confirms native Salesforce sync,", font=FONT_BODY, fill=TEXT)
    draw.text((212, 568), "Slack alerts, and clear escalation guidance when", font=FONT_BODY, fill=TEXT)
    draw.text((212, 598), "confidence is low.", font=FONT_BODY, fill=TEXT)
    draw.rounded_rectangle((110, 680, 690, 755), radius=24, fill=SURFACE_SOFT, outline="#2F4A6A", width=2)
    draw.text((142, 708), "Type your question...", font=FONT_BODY, fill=MUTED)
    draw.rounded_rectangle((720, 685, 860, 745), radius=28, fill=ACCENT_STRONG)
    draw.text((767, 705), "Send", font=FONT_BODY, fill=TEXT)

    draw.rounded_rectangle((955, 235, 1290, 505), radius=34, fill=SURFACE, outline="#27415F", width=2)
    draw.text((995, 275), "Documents", font=FONT_LABEL, fill=ACCENT)
    draw.text((995, 305), "Uploaded knowledge base", font=FONT_H3, fill=TEXT)
    for idx, name in enumerate(["sample-company-handbook.md", "pricing-faq.pdf"]):
        top = 365 + idx * 85
        draw.rounded_rectangle((995, top, 1248, top + 62), radius=20, fill=SURFACE_SOFT, outline="#2F4A6A", width=2)
        draw.text((1015, top + 14), name, font=FONT_SMALL, fill=TEXT)
    draw.rounded_rectangle((955, 535, 1290, 790), radius=34, fill=SURFACE, outline="#27415F", width=2)
    draw.text((995, 575), "Status", font=FONT_LABEL, fill=ACCENT)
    draw.text((995, 605), "Conversation", font=FONT_SMALL, fill=MUTED)
    draw.text((1170, 605), "Active", font=FONT_SMALL, fill=TEXT)
    draw.text((995, 665), "Messages", font=FONT_SMALL, fill=MUTED)
    draw.text((1210, 665), "2", font=FONT_SMALL, fill=TEXT)
    return image


def create_admin_preview() -> Image.Image:
    image = Image.new("RGB", (1360, 860), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1360, 860), fill=NAVY)
    draw.ellipse((1000, -130, 1450, 260), fill="#123761")

    draw.rounded_rectangle((70, 55, 1290, 175), radius=32, fill=SURFACE, outline="#27415F", width=2)
    draw.text((110, 95), "Admin", font=FONT_H1, fill=TEXT)
    draw.text((112, 150), "Upload documents and test retrieval.", font=FONT_BODY, fill=MUTED)
    draw.rounded_rectangle((1180, 92, 1260, 142), radius=24, fill=SURFACE_SOFT, outline="#35577C", width=2)
    draw.text((1205, 107), "Back", font=FONT_SMALL, fill=TEXT)

    blocks = [
        ("Upload PDF", 210, [("Selected document", "pricing-faq.pdf"), ("Status", "processed successfully")]),
        ("Documents", 430, [("sample-company-handbook.md", "Chunks: 8"), ("pricing-faq.pdf", "Chunks: 5")]),
        ("Test Retrieval", 650, [("Query", "EU data residency"), ("Result", "Add-on available for Growth plan")]),
    ]

    for title, top, rows in blocks:
        draw.rounded_rectangle((70, top, 1290, top + 170), radius=30, fill=SURFACE, outline="#27415F", width=2)
        draw.text((110, top + 28), title, font=FONT_H2, fill=TEXT)
        row_y = top + 82
        for left, right in rows:
            draw.rounded_rectangle((110, row_y, 1235, row_y + 42), radius=18, fill=SURFACE_SOFT, outline="#2F4A6A", width=2)
            draw.text((132, row_y + 10), left, font=FONT_SMALL, fill=MUTED)
            draw.text((440, row_y + 10), right, font=FONT_SMALL, fill=TEXT)
            row_y += 54
    return image


def build_page_one() -> Image.Image:
    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), LIGHT_BG)
    draw = ImageDraw.Draw(page)

    draw.rounded_rectangle((MARGIN, 70, PAGE_WIDTH - MARGIN, 360), radius=42, fill=NAVY)
    draw.text((MARGIN + 50, 130), "AI Support + Sales Copilot", font=FONT_H1, fill=TEXT)
    draw.text((MARGIN + 50, 205), "Project Reference", font=FONT_H2, fill=ACCENT)
    subtitle = (
        "Production-oriented support and sales chatbot with FastAPI, Next.js, "
        "document ingestion, grounded retrieval, and operator tooling."
    )
    draw_wrapped_text(draw, subtitle, (MARGIN + 50, 250), FONT_BODY, "#D9E6F4", PAGE_WIDTH - (2 * MARGIN) - 100, line_gap=10)

    metric_y = 390
    metric_width = 440
    gap = 22
    draw_metric(draw, (MARGIN, metric_y, MARGIN + metric_width, metric_y + 110), "Dataset / Source", "Company handbook + uploaded PDFs")
    draw_metric(draw, (MARGIN + metric_width + gap, metric_y, MARGIN + 2 * metric_width + gap, metric_y + 110), "Core Output", "Grounded answers + handoff flags")
    draw_metric(draw, (MARGIN + 2 * (metric_width + gap), metric_y, PAGE_WIDTH - MARGIN, metric_y + 110), "Stack", "FastAPI, Next.js, ChromaDB, Groq")

    left_box = (MARGIN, 545, 780, 1220)
    right_box = (820, 545, PAGE_WIDTH - MARGIN, 1220)
    section_card(draw, left_box, "Business Problem")
    section_card(draw, right_box, "Approach")

    problem_items = [
        "Support and sales teams need fast answers that stay grounded in company documentation instead of improvising.",
        "Operators also need visibility into retrieval quality, document coverage, and when the assistant should escalate to a human.",
    ]
    draw_bullets(draw, problem_items, (left_box[0] + 28, left_box[1] + 82), left_box[2] - left_box[0] - 56)

    approach_items = [
        "Parse uploaded PDFs, split content into chunks, and index them into Chroma with a keyword fallback for constrained environments.",
        "Retrieve the most relevant chunks, rerank them, and answer with either a Groq-compatible LLM or a local extractive fallback.",
        "Expose health, retrieval, upload, list, and delete endpoints plus a demo-ready customer and admin UI.",
    ]
    draw_bullets(draw, approach_items, (right_box[0] + 28, right_box[1] + 82), right_box[2] - right_box[0] - 56)

    methods_box = (MARGIN, 1260, PAGE_WIDTH - MARGIN, 1670)
    section_card(draw, methods_box, "Key ML / AI Methods Used")
    methods_items = [
        "Retrieval-augmented generation with document chunking and context-window curation.",
        "Sentence-transformer embeddings with Chroma vector search plus a deterministic keyword fallback index.",
        "Extractive answer fallback and confidence-based human escalation when evidence is thin.",
        "API-first architecture with structured metadata for latency and retrieval counts.",
    ]
    draw_bullets(draw, methods_items, (methods_box[0] + 28, methods_box[1] + 82), methods_box[2] - methods_box[0] - 56, bullet_fill=SUCCESS)

    results_box = (MARGIN, 1710, PAGE_WIDTH - MARGIN, 2210)
    section_card(draw, results_box, "Results / Output")
    results_items = [
        "Interactive customer-facing chat experience and an operator admin console for uploads, retrieval checks, and document lifecycle management.",
        "Backend API contract covering chat, health, document upload, retrieval, listing, and deletion.",
        "Robust local-demo mode: 10 backend tests passing, frontend production build passing, and resilience improvements for registry parsing, request flow, and fallback retrieval.",
        "GitHub: https://github.com/JaiEnfer/ai-support-sales-copilot",
    ]
    draw_bullets(draw, results_items, (results_box[0] + 28, results_box[1] + 82), results_box[2] - results_box[0] - 56, bullet_fill=WARNING)

    return page


def build_page_two(home_preview: Image.Image, admin_preview: Image.Image) -> Image.Image:
    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), LIGHT_BG)
    draw = ImageDraw.Draw(page)

    draw.text((MARGIN, 90), "Technology Stack", font=FONT_H1, fill=INK)
    stack_text = (
        "Backend: FastAPI, Pydantic Settings, PyPDF, LangChain text splitters\n"
        "AI / Retrieval: ChromaDB, sentence-transformers, Groq-compatible OpenAI client\n"
        "Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS 4\n"
        "Quality: Pytest, linting, production build checks, sample chatbot flow validation"
    )
    draw.multiline_text((MARGIN, 170), stack_text, font=FONT_BODY, fill=INK, spacing=14)

    draw.text((MARGIN, 370), "Screenshots", font=FONT_H2, fill=ACCENT_STRONG)
    draw.text((MARGIN, 410), "Customer chat workspace and admin operations console", font=FONT_BODY, fill=MUTED)

    screenshot_box_width = (PAGE_WIDTH - (2 * MARGIN) - 36) // 2
    left_box = (MARGIN, 470, MARGIN + screenshot_box_width, 1450)
    right_box = (MARGIN + screenshot_box_width + 36, 470, PAGE_WIDTH - MARGIN, 1450)
    for box, title in ((left_box, "Customer View"), (right_box, "Admin View")):
        draw.rounded_rectangle(box, radius=28, fill=CARD, outline=BORDER, width=2)
        draw.text((box[0] + 22, box[1] + 18), title, font=FONT_H3, fill=INK)

    home_thumb = home_preview.copy()
    home_thumb.thumbnail((screenshot_box_width - 44, 860))
    admin_thumb = admin_preview.copy()
    admin_thumb.thumbnail((screenshot_box_width - 44, 860))

    page.paste(home_thumb, (left_box[0] + 22, left_box[1] + 68))
    page.paste(admin_thumb, (right_box[0] + 22, right_box[1] + 68))

    notes_box = (MARGIN, 1520, PAGE_WIDTH - MARGIN, 2190)
    section_card(draw, notes_box, "Project Snapshot")
    notes_items = [
        "Project title: AI Support + Sales Copilot",
        "Business problem: grounded answers for support and sales teams using company knowledge sources.",
        "Dataset / source: sample company handbook, uploaded PDFs, and local fallback registry metadata.",
        "Approach: ingest, chunk, index, retrieve, rerank, answer, and escalate when confidence is low.",
        "Results / output: demo-ready UI, robust backend API, retrieval diagnostics, and local resilience when embeddings or external LLM access are unavailable.",
    ]
    draw_bullets(draw, notes_items, (notes_box[0] + 28, notes_box[1] + 84), notes_box[2] - notes_box[0] - 56)
    return page


def main() -> None:
    home_preview = create_home_preview()
    admin_preview = create_admin_preview()
    home_preview.save(HOME_PREVIEW_PATH)
    admin_preview.save(ADMIN_PREVIEW_PATH)

    page_one = build_page_one()
    page_two = build_page_two(home_preview, admin_preview)
    page_one.save(PDF_PATH, "PDF", resolution=150.0, save_all=True, append_images=[page_two])


if __name__ == "__main__":
    main()

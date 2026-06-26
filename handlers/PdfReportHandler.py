import io
import os
import logging
from fpdf import FPDF

REPORTS_DIR = "reports"
PAGE_WIDTH_MM = 210
MARGIN_MM = 20
CONTENT_WIDTH_MM = PAGE_WIDTH_MM - 2 * MARGIN_MM
IMAGE_WIDTH_MM = 55

COLOR_PRIMARY = (28, 30, 38)
COLOR_ACCENT = (196, 30, 58)
COLOR_MUTED = (110, 115, 125)
COLOR_BOX = (244, 244, 247)

UNICODE_REPLACEMENTS = {
    "\u2026": "...",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2022": "-",
    "\u00a0": " ",
}


class PdfReportHandler:
    """Render a structured artist report into a styled PDF document."""

    def __init__(self, output_dir=REPORTS_DIR):
        """Initialize the handler and ensure the output directory exists.

        Args:
            output_dir: Directory where generated PDF reports are written.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def build_report(self, report, artist, album_name=None, requests_session=None):
        """Create a PDF document from a structured report and artist data.

        Args:
            report: Parsed report dict produced by ChatGptHandler.generate_report.
            artist: Artist dict from BigQuery (must include `name`; `image_url`
                is used for the cover image when available).
            album_name: Optional album name appended to the output file name.
            requests_session: Optional requests-like module/session injected for
                downloading the image (defaults to the `requests` library).

        Returns:
            str: Absolute path of the generated PDF file.
        """
        pdf = FPDF(format="A4")
        pdf.set_auto_page_break(auto=True, margin=MARGIN_MM)
        pdf.set_margins(MARGIN_MM, MARGIN_MM, MARGIN_MM)
        pdf.add_page()

        self._render_header(pdf, report, artist, requests_session)
        self._render_executive_summary(pdf, report)
        self._render_sections(pdf, report)
        self._render_fact_sheet(pdf, report)
        self._render_conclusions(pdf, report)
        self._render_recommendations(pdf, report)

        file_name = self._slugify(artist.get("name", "artist"))
        if album_name:
            file_name = f"{file_name}_{self._slugify(album_name)}"
        output_path = os.path.join(self.output_dir, f"{file_name}_report.pdf")
        pdf.output(output_path)
        logging.info(f"Report PDF written to {output_path}")
        return os.path.abspath(output_path)

    def _render_header(self, pdf, report, artist, requests_session):
        """Render the cover block with the artist image, title and subtitle.

        Args:
            pdf: Active FPDF document.
            report: Structured report dict.
            artist: Artist dict containing name and optional image_url.
            requests_session: Optional requests-like module for the download.
        """
        image_stream = self._download_image(artist.get("image_url"), requests_session)
        if image_stream is not None:
            x = (PAGE_WIDTH_MM - IMAGE_WIDTH_MM) / 2
            pdf.image(image_stream, x=x, w=IMAGE_WIDTH_MM)
            pdf.ln(4)

        pdf.set_text_color(*COLOR_ACCENT)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, self._safe(artist.get("name", "")).upper(), align="C")
        pdf.ln(9)

        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.set_font("Helvetica", "B", 22)
        pdf.multi_cell(0, 9, self._safe(report.get("titulo", "Informe del artista")), align="C")
        pdf.ln(1)

        subtitle = report.get("subtitulo")
        if subtitle:
            pdf.set_text_color(*COLOR_MUTED)
            pdf.set_font("Helvetica", "I", 12)
            pdf.multi_cell(0, 6, self._safe(subtitle), align="C")

        pdf.ln(4)
        pdf.set_draw_color(*COLOR_ACCENT)
        pdf.set_line_width(0.6)
        y = pdf.get_y()
        pdf.line(MARGIN_MM, y, PAGE_WIDTH_MM - MARGIN_MM, y)
        pdf.ln(6)

    def _render_executive_summary(self, pdf, report):
        """Render the executive summary inside a highlighted box.

        Args:
            pdf: Active FPDF document.
            report: Structured report dict.
        """
        summary = report.get("resumen_ejecutivo")
        if not summary:
            return
        self._heading(pdf, "Resumen ejecutivo")
        pdf.set_fill_color(*COLOR_BOX)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_x(MARGIN_MM)
        pdf.multi_cell(
            CONTENT_WIDTH_MM, 6, self._safe(summary), fill=True, padding=4
        )
        pdf.ln(4)

    def _render_sections(self, pdf, report):
        """Render the analytical sections of the report in order.

        Args:
            pdf: Active FPDF document.
            report: Structured report dict.
        """
        for section in report.get("secciones", []) or []:
            title = section.get("titulo")
            content = section.get("contenido")
            if not title and not content:
                continue
            if title:
                self._heading(pdf, title)
            if content:
                pdf.set_text_color(*COLOR_PRIMARY)
                pdf.set_font("Helvetica", "", 11)
                pdf.multi_cell(0, 6, self._safe(content))
                pdf.ln(3)

    def _render_fact_sheet(self, pdf, report):
        """Render quick-reference facts (themes, tone, target audience).

        Args:
            pdf: Active FPDF document.
            report: Structured report dict.
        """
        themes = report.get("temas_recurrentes") or []
        tone = report.get("tono_emocional")
        audience = report.get("publico_objetivo")
        if not themes and not tone and not audience:
            return

        self._heading(pdf, "Ficha rápida")
        if themes:
            self._fact_line(pdf, "Temas recurrentes", ", ".join(themes))
        if tone:
            self._fact_line(pdf, "Tono emocional", tone)
        if audience:
            self._fact_line(pdf, "Público objetivo", audience)
        pdf.ln(3)

    def _render_conclusions(self, pdf, report):
        """Render the closing conclusions paragraph.

        Args:
            pdf: Active FPDF document.
            report: Structured report dict.
        """
        conclusions = report.get("conclusiones")
        if not conclusions:
            return
        self._heading(pdf, "Conclusiones")
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, self._safe(conclusions))
        pdf.ln(3)

    def _render_recommendations(self, pdf, report):
        """Render actionable recommendations as a bullet list.

        Args:
            pdf: Active FPDF document.
            report: Structured report dict.
        """
        recommendations = report.get("recomendaciones") or []
        if not recommendations:
            return
        self._heading(pdf, "Recomendaciones")
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.set_font("Helvetica", "", 11)
        for item in recommendations:
            pdf.set_x(MARGIN_MM)
            pdf.set_text_color(*COLOR_ACCENT)
            pdf.cell(6, 6, chr(149))
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.multi_cell(CONTENT_WIDTH_MM - 6, 6, self._safe(item))
        pdf.ln(2)

    def _heading(self, pdf, text):
        """Render a section heading with the accent colour.

        Args:
            pdf: Active FPDF document.
            text: Heading text to display.
        """
        pdf.set_text_color(*COLOR_ACCENT)
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 7, self._safe(text))
        pdf.ln(1)

    def _fact_line(self, pdf, label, value):
        """Render a labelled fact line (bold label + value).

        Args:
            pdf: Active FPDF document.
            label: Bold label shown before the value.
            value: Free-text value associated with the label.
        """
        pdf.set_x(MARGIN_MM)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(45, 6, self._safe(f"{label}:"))
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(CONTENT_WIDTH_MM - 45, 6, self._safe(value))

    def _download_image(self, image_url, requests_session=None):
        """Download the artist image into an in-memory stream.

        Args:
            image_url: Public URL of the artist image stored in BigQuery.
            requests_session: Optional requests-like module/session to use.

        Returns:
            io.BytesIO | None: Image bytes ready for FPDF, or None on failure.
        """
        if not image_url:
            return None
        if requests_session is None:
            import requests as requests_session
        try:
            response = requests_session.get(image_url, timeout=15)
            response.raise_for_status()
            return io.BytesIO(response.content)
        except Exception as error:
            logging.warning(f"Could not download artist image: {error}")
            return None

    def _safe(self, text):
        """Make text safe for the latin-1 core PDF fonts.

        Replaces common Unicode punctuation and drops any remaining
        non-latin-1 characters so the report never fails to render.

        Args:
            text: Arbitrary text coming from the model or BigQuery.

        Returns:
            str: A latin-1 encodable version of the input text.
        """
        text = str(text)
        for source, target in UNICODE_REPLACEMENTS.items():
            text = text.replace(source, target)
        return text.encode("latin-1", "ignore").decode("latin-1")

    def _slugify(self, name):
        """Build a filesystem-friendly slug from the artist name.

        Args:
            name: Artist name to slugify.

        Returns:
            str: Lowercase ascii slug usable as a file name.
        """
        slug = self._safe(name).lower()
        slug = "".join(char if char.isalnum() else "_" for char in slug)
        return "_".join(filter(None, slug.split("_"))) or "artist"

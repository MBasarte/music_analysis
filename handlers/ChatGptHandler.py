import os
import json
import logging
from openai import OpenAI

MAX_LYRICS_CHARS_PER_TRACK = 1500
REPORT_MODEL = "gpt-4o-mini"
PROMPTS_DIR = "prompts"


class ChatGptHandler:
    """Generate a business-oriented artist report from catalogue and lyrics."""

    def __init__(self):
        """Initialize the OpenAI client using the OPENAI_API_KEY env variable."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_report(self, artist_name, tracks, album_name=None, save_prompt=False):
        """Build a structured A&R report for a record-label CEO.

        The model receives the artist catalogue together with the song lyrics
        retrieved from BigQuery so the analysis is grounded on the actual
        content (recurring themes, emotional tone, commercial angle, etc.).

        Args:
            artist_name: Name of the artist being analysed.
            tracks: List of track dicts (album_name, release_date, track_name,
                track_number, explicit, duration_ms, lyrics) as returned by
                BigQueryHandler.get_tracks_with_lyrics.
            album_name: Optional album name when the report is scoped to a
                single album.
            save_prompt: When True, the system and user prompts sent to the
                model and the raw model response are written to a text file
                under PROMPTS_DIR for debugging and auditing.

        Returns:
            dict: Parsed report with keys such as `titulo`,
            `resumen_ejecutivo`, `secciones`, `conclusiones` and
            `recomendaciones`. Ready to be rendered into a document.
        """
        catalogue_text = self._build_catalogue_text(tracks)
        scope = f"el álbum «{album_name}»" if album_name else "su catálogo disponible"

        system_prompt = (
            "Eres un analista A&R senior de un sello discográfico. Redactas "
            "informes claros, ejecutivos y accionables para que el CEO del sello "
            "tome decisiones de negocio sobre un artista. Basas tus conclusiones "
            "en las letras y los datos del catálogo que se te facilitan. Escribes "
            "en español, con tono profesional pero ameno, y evitas inventar datos "
            "que no se deduzcan del material aportado."
        )

        user_prompt = f"""
Analiza al artista «{artist_name}» a partir de {scope}.

A continuación tienes el catálogo con las letras de las canciones almacenadas:

{catalogue_text}

Elabora un informe ejecutivo para el CEO del sello. Quiero que cubra, como mínimo:
- Resumen ejecutivo con la idea principal sobre el artista.
- Temáticas y narrativa recurrente en las letras.
- Tono emocional y sello de identidad del artista.
- Público objetivo y encaje de mercado.
- Potencial comercial y posibles riesgos (p. ej. lenguaje explícito).
- Conclusiones y recomendaciones de negocio accionables.

Devuelve EXCLUSIVAMENTE un JSON válido con esta estructura:
{{
  "titulo": "título del informe",
  "subtitulo": "una línea con el gancho principal",
  "resumen_ejecutivo": "2-4 frases",
  "secciones": [
    {{"titulo": "título de la sección", "contenido": "texto de la sección"}}
  ],
  "temas_recurrentes": ["tema 1", "tema 2"],
  "tono_emocional": "descripción breve",
  "publico_objetivo": "descripción breve",
  "conclusiones": "párrafo de cierre",
  "recomendaciones": ["recomendación accionable 1", "recomendación accionable 2"]
}}
""".strip()

        logging.info(f"Generating report for {artist_name} with {len(tracks)} tracks")
        logging.debug(f"User prompt: {user_prompt}")
        response = self.client.chat.completions.create(
            model=REPORT_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw_response = response.choices[0].message.content
        if save_prompt:
            self._save_prompt(
                artist_name, system_prompt, user_prompt, raw_response, album_name
            )
        return json.loads(raw_response)

    def _save_prompt(self, artist_name, system_prompt, user_prompt, raw_response, album_name=None):
        """Persist the prompts and the raw model response to a text file.

        Args:
            artist_name: Name of the artist, used to build the file name.
            system_prompt: System prompt sent to the model.
            user_prompt: User prompt sent to the model.
            raw_response: Raw text response returned by the model before being
                parsed and rendered into a PDF.
            album_name: Optional album name appended to the file name.

        Returns:
            str: Absolute path of the written prompt file.
        """
        os.makedirs(PROMPTS_DIR, exist_ok=True)
        file_name = self._slugify(artist_name)
        if album_name:
            file_name = f"{file_name}_{self._slugify(album_name)}"
        output_path = os.path.join(PROMPTS_DIR, f"{file_name}_prompt.txt")
        content = (
            f"MODEL: {REPORT_MODEL}\n\n"
            f"=== SYSTEM PROMPT ===\n{system_prompt}\n\n"
            f"=== USER PROMPT ===\n{user_prompt}\n\n"
            f"=== MODEL RESPONSE ===\n{raw_response}\n"
        )
        with open(output_path, "w", encoding="utf-8") as prompt_file:
            prompt_file.write(content)
        logging.info(f"Prompt and response written to {output_path}")
        return os.path.abspath(output_path)

    def _slugify(self, name):
        """Build a filesystem-friendly slug from a name.

        Args:
            name: Text to slugify (artist or album name).

        Returns:
            str: Lowercase ascii slug usable as a file name.
        """
        slug = "".join(char if char.isalnum() else "_" for char in str(name).lower())
        return "_".join(filter(None, slug.split("_"))) or "artist"

    def _build_catalogue_text(self, tracks):
        """Render the track catalogue and lyrics into a compact prompt block.

        Lyrics are truncated per track to keep the prompt within a reasonable
        size while preserving enough content for thematic analysis.

        Args:
            tracks: List of track dicts as returned by BigQueryHandler.

        Returns:
            str: Human-readable catalogue with truncated lyrics per track.
        """
        if not tracks:
            return "(No hay canciones ni letras almacenadas para este artista.)"

        blocks = []
        for track in tracks:
            lyrics = track.get("lyrics") or "(Sin letra disponible.)"
            if len(lyrics) > MAX_LYRICS_CHARS_PER_TRACK:
                lyrics = lyrics[:MAX_LYRICS_CHARS_PER_TRACK] + "…"
            explicit = " [explícita]" if track.get("explicit") else ""
            header = (
                f"Álbum: {track.get('album_name')} "
                f"({track.get('release_date')}) | "
                f"Pista {track.get('track_number')}: "
                f"{track.get('track_name')}{explicit}"
            )
            blocks.append(f"{header}\nLetra:\n{lyrics}")
        return "\n\n---\n\n".join(blocks)

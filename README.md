# Music Analysis

Descarga datos de artistas desde Spotify (álbumes, pistas y letras), los guarda en BigQuery y genera un informe A&R en PDF con OpenAI.

## Requisitos

- Python 3.10+
- Acceso a un proyecto de BigQuery
- Credenciales de Spotify y OpenAI

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno

Crea un fichero `.env` en la raíz con:

```env
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
GOOGLE_APPLICATION_CREDENTIALS=/ruta/a/credenciales-bigquery.json
OPENAI_API_KEY=tu_api_key
```

| Variable | Descripción |
|---|---|
| `SPOTIFY_CLIENT_ID` | Client ID de la app de Spotify. |
| `SPOTIFY_CLIENT_SECRET` | Client Secret de la app de Spotify. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Ruta al JSON de la cuenta de servicio de BigQuery. |
| `OPENAI_API_KEY` | API key de OpenAI. |

## Uso

```bash
# Descargar datos del artista a BigQuery
python main.py --artist "Shakira" --mode get_artist_data --add_lyrics True

# Generar el informe PDF (requiere datos ya en BigQuery)
python main.py --artist "Shakira" --mode create_report --save_prompt

# Hacer ambas cosas
python main.py --artist "Shakira" --mode all --add_lyrics True
```

Argumentos:

- `--artist` (obligatorio): nombre del artista.
- `--mode` (obligatorio): `get_artist_data`, `create_report` o `all`.
- `--album` (opcional): limita a un álbum concreto.
- `--add_lyrics` (opcional): descarga letras desde LRCLIB.
- `--save_prompt` (opcional): guarda el prompt enviado a OpenAI en `prompts/`.

Los informes se guardan en `reports/`.

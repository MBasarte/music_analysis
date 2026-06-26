import os
import argparse
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from handlers.SpotifyHandler import SpotifyHandler
from handlers.BigQueryHandler import BigQueryHandler
from handlers.LrcLibHandler import LrcLibHandler
from handlers.ChatGptHandler import ChatGptHandler
from handlers.PdfReportHandler import PdfReportHandler
from models.Artist import Artist
import dotenv
dotenv.load_dotenv()

def get_artist_data(artist_name, album_name=None, add_lyrics=False):
    spotify_handler = SpotifyHandler()
    bigquery_handler = BigQueryHandler()
    lrc_lib_handler = LrcLibHandler()

    artist = Artist(artist_name, spotify_handler)
    artist.get_albums(spotify_handler, album_name)
    artist.get_tracks(spotify_handler)
    if add_lyrics:
        artist.get_lyrics(lrc_lib_handler)

    for album in artist.albums:
        for track in album.tracks:
            logging.info(f'Artist: {artist.name}, Album: {album.name}, Track: {track.name}')

    artist.save_to_bigquery(bigquery_handler, add_lyrics)

def create_report(artist_name, album_name=None, save_prompt=False):
    bigquery_handler = BigQueryHandler()
    chatgpt_handler = ChatGptHandler()
    pdf_handler = PdfReportHandler()

    artist = bigquery_handler.get_artist(artist_name=artist_name)[0]
    if artist is None:
        raise ValueError(
            f"Artist '{artist_name}' not found in BigQuery. "
            "Run the get_artist_data mode first."
        )

    tracks = bigquery_handler.get_tracks_with_lyrics(artist_id=artist["id"], album_name=album_name)
    report = chatgpt_handler.generate_report(
        artist_name, tracks, album_name, save_prompt=save_prompt
    )
    report_path = pdf_handler.build_report(report, artist, album_name)

    logging.info(f"Report generated at {report_path}")
    return report_path

def main(artist_name, album_name=None, mode="get_artist_data", add_lyrics=False, save_prompt=False):
    if mode == "get_artist_data":
        get_artist_data(artist_name, album_name, add_lyrics)
    elif mode == "create_report":
        create_report(artist_name, album_name, save_prompt)
    elif mode == "all":
        get_artist_data(artist_name, album_name, add_lyrics)
        create_report(artist_name, album_name, save_prompt)
    else:
        raise ValueError(f"Invalid mode: {mode}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist", type=str, required=True)
    parser.add_argument("--album", type=str, required=False)
    parser.add_argument("--mode", type=str, required=True)
    parser.add_argument("--add_lyrics", type=bool, required=False, default=False)
    parser.add_argument("--save_prompt", action="store_true")
    args = parser.parse_args()
    main(args.artist, args.album, args.mode, args.add_lyrics, args.save_prompt)

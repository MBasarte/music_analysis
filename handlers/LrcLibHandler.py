import requests
import logging

class LrcLibHandler:
    def __init__(self):
        self.base_url = "https://lrclib.net/api/get"

    def get_lyrics(self, track_name, artist_name, album_name=None):
        params = {
            "track_name": track_name,
            "artist_name": artist_name,
        }
        if album_name:
            params["album_name"] = album_name

        logging.info(f"Getting lyrics for {track_name} by {artist_name} from {album_name}")
        res = requests.get(self.base_url, params=params)

        try:
            lyrics = res.json()['plainLyrics']
            logging.info(f"Lyrics found")
            return lyrics
        except:
            logging.info(f"Lyrics not found")
            return None
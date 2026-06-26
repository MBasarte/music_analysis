class Track:
    def __init__(self, track_info):
        self.id = track_info["id"]
        self.name = track_info["name"]
        self.href = track_info["href"]
        self.uri = track_info["uri"]
        self.duration_ms = track_info["duration_ms"]
        self.explicit = track_info["explicit"]
        self.track_number = track_info["track_number"]
        self.type = track_info["type"]
        self.lyrics = None

    def save_to_bigquery(self, bigquery_handler, artist_id, album_id):
        dict_to_insert = {
            "artist_id": artist_id,
            "album_id": album_id,
            "name": self.name,
            "id": self.id,
            "href": self.href,
            "uri": self.uri,
            "duration_ms": self.duration_ms,
            "explicit": self.explicit,
            "track_number": self.track_number,
            "type": self.type
        }
        bigquery_handler.insert_data("track", dict_to_insert)

    def get_lyrics(self, artist_name, lrc_lib_handler, album_name):
        lyrics = lrc_lib_handler.get_lyrics(self.name, artist_name, album_name)
        self.lyrics = lyrics

    def save_lyrics_to_bigquery(self, bigquery_handler, artist_id, album_id):
        dict_to_insert = {
            "artist_id": artist_id,
            "album_id": album_id,
            "track_id": self.id,
            "lyrics": self.lyrics
        }
        bigquery_handler.insert_data("lyrics", dict_to_insert)
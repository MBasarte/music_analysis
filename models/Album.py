from models.Track import Track

class Album:
    def __init__(self, album_info):
        self.name = album_info["name"]
        self.id = album_info["id"]
        self.album_type = album_info["album_type"]
        self.total_tracks = album_info["total_tracks"]
        self.href = album_info["href"]
        self.image_url = album_info["images"][0]["url"]
        self.release_date = album_info["release_date"]
        self.tracks = []

    def get_tracks(self, spotify_handler):
        tracks = spotify_handler.get_tracks(self.id)
        for track_info in tracks:
            self.tracks.append(Track(track_info))

    def save_to_bigquery(self, bigquery_handler, artist_id):
        dict_to_insert = {
            "artist_id" : artist_id,
            "name": self.name,
            "id": self.id,
            "type": self.album_type,
            "total_tracks": self.total_tracks,
            "href": self.href,
            "image_url": self.image_url,
            "release_date": self.release_date
        }
        bigquery_handler.insert_data("album", dict_to_insert)
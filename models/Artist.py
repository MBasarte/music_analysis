from models.Album import Album

class Artist:
    def __init__(self, name, spotify_handler):
        self.artist_info = spotify_handler.get_artist_info(name)
        self.name = self.artist_info["name"]
        self.id = self.artist_info["id"]
        self.image_url = self.artist_info["images"][0]["url"]
        self.href = self.artist_info["href"]
        self.uri = self.artist_info["uri"]
        self.albums = []

    def get_albums(self, spotify_handler, album_name=None):
        albums = spotify_handler.get_albums(self.id)
        for album_info in albums:
            if album_name is None or album_info["name"] == album_name:
                self.albums.append(Album(album_info))
        if len(self.albums) == 0:
            albums_found = [album["name"] for album in albums]
            raise ValueError(f"{album_name} not found for artist {self.name}, existing albums: {albums_found}")

    def get_tracks(self, spotify_handler):
        for album in self.albums:
            album.get_tracks(spotify_handler)

    def get_lyrics(self, lrc_lib_handler):
        for album in self.albums:
            for track in album.tracks:
                track.get_lyrics(self.name, lrc_lib_handler, album.name)

    def save_to_bigquery(self, bigquery_handler, add_lyrics=False):
        dict_to_insert = {
            "name": self.name,
            "id": self.id,
            "image_url": self.image_url,
            "href": self.href,
            "uri": self.uri
        }
        bigquery_handler.insert_data("artist", dict_to_insert)

        self.save_albums_to_bigquery(bigquery_handler)
        self.save_tracks_to_bigquery(bigquery_handler)
        if add_lyrics:
            self.save_lyrics_to_bigquery(bigquery_handler)

    def save_albums_to_bigquery(self, bigquery_handler):
        for album in self.albums:
            album.save_to_bigquery(bigquery_handler, self.id)

    def save_tracks_to_bigquery(self, bigquery_handler):
        for album in self.albums:
            for track in album.tracks:
                track.save_to_bigquery(bigquery_handler, self.id, album.id)

    def save_lyrics_to_bigquery(self, bigquery_handler):
        for album in self.albums:
            for track in album.tracks:
                track.save_lyrics_to_bigquery(bigquery_handler, self.id, album.id)
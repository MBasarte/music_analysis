import os
import requests
import base64

class SpotifyHandler:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.access_token = self.get_access_token()

    def get_access_token(self):
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")

        url = "https://accounts.spotify.com/api/token"

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "client_credentials"
        }

        response = requests.post(url, headers=headers, data=data)
        token = response.json()["access_token"]

        return token

    def get_artist_info(self, artist_name):
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        url = "https://api.spotify.com/v1/search"

        params = {
            "q": artist_name,
            "type": "artist",
            "limit": 1
        }

        res = requests.get(url, headers=headers, params=params)

        artist = res.json()["artists"]["items"][0]

        return artist

    def get_albums(self, artist_id):
        url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"

        params = {
            "limit": 10
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        res = requests.get(url, headers=headers, params=params)

        albums = res.json()["items"]

        return albums

    def get_tracks(self, album_id):

        url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        res = requests.get(url, headers=headers, params={})

        tracks = res.json()["items"]

        return tracks
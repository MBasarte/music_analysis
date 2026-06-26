import google.cloud.bigquery as bigquery

class BigQueryHandler:

    def __init__(self):
        self.client = bigquery.Client()
        self.dataset_id = "music_analysis"
        self.project_id = "sbs-clases"

    def read_data(self, query):
        query_job = self.client.query(query)
        return list(query_job.result())

    def insert_data(self, table_name, data):
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        self.client.insert_rows_json(table_id, [data])

    def get_artist(self, artist_name):
        query = f"""
            select
                id,
                name,
                image_url,
                href,
                uri
            from
                `{self.project_id}.{self.dataset_id}.artist`
            where
                name = '{artist_name}'
            limit 1
        """
        return self.read_data(query)

    def get_tracks_with_lyrics(self, artist_id, album_name=None):
        query = f"""
            select
                distinct t.id as track_id,
                al.name as album_name,
                al.release_date as release_date,
                t.name as track_name,
                t.track_number as track_number,
                t.explicit as explicit,
                t.duration_ms as duration_ms,
                ly.lyrics as lyrics
            from
                `{self.project_id}.{self.dataset_id}.track` t
            join
                `{self.project_id}.{self.dataset_id}.album` al
                on t.album_id = al.id
            left join
                `{self.project_id}.{self.dataset_id}.lyrics` ly
                on ly.track_id = t.id
            where
                t.artist_id = '{artist_id}'
                and al.name = '{album_name}'
            order by
                al.release_date,
                t.track_number
        """
        return self.read_data(query)

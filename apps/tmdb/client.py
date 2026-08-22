import os
import requests
from django.conf import settings

class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self):
        self.api_key = os.environ.get('TMDB_API_KEY')
        if not self.api_key and hasattr(settings, 'TMDB_API_KEY'):
            self.api_key = settings.TMDB_API_KEY

    def _get_mock_movies(self):
        return [
            {
                "id": 157336,
                "title": "Interstellar",
                "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
                "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
                "backdrop_path": "/xJHokMbljvjEVAZS3xXTAyExjFl.jpg"
            },
            {
                "id": 438631,
                "title": "Dune",
                "overview": "Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe to ensure the future of his family and his people.",
                "poster_path": "/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
                "backdrop_path": "/lzWHmYdfeFiMIY4JaMmtR7GEli3.jpg"
            },
            {
                "id": 27205,
                "title": "Inception",
                "overview": "Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets is offered a chance to regain his old life as payment for a task considered to be impossible: \"inception\", the implantation of another person's idea into a target's subconscious.",
                "poster_path": "/9gk7adHYeDvHkCSEqAvQQsV5AC5.jpg",
                "backdrop_path": "/s3TBrRGB1inv7qf0p01B1T0249T.jpg"
            },
            {
                "id": 155,
                "title": "The Dark Knight",
                "overview": "Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets.",
                "poster_path": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
                "backdrop_path": "/nMKdUUepR0i5zn0y1T4CsSB5chy.jpg"
            },
            {
                "id": 603,
                "title": "The Matrix",
                "overview": "Set in the 22nd century, The Matrix tells the story of a computer hacker who joins a group of underground insurgents fighting the vast and powerful computers who now rule the earth.",
                "poster_path": "/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
                "backdrop_path": "/l4QHerSTOkVXiQ29K3tG5EEDkM5.jpg"
            }
        ]

    def _get_mock_series(self):
        return [
            {
                "id": 1399,
                "name": "Game of Thrones",
                "overview": "Seven noble families fight for control of the mythical land of Westeros. Friction between the houses leads to full-scale war.",
                "poster_path": "/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
                "backdrop_path": "/suopoADq0k8YZr4dQXcU6pToj6s.jpg"
            },
            {
                "id": 66732,
                "name": "Stranger Things",
                "overview": "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces, and one strange little girl.",
                "poster_path": "/49WJfeN0moxb9IPfGn8Sl2MGpqm.jpg",
                "backdrop_path": "/56v2KjBlU4XaM9m51c5pM50XmqI.jpg"
            },
            {
                "id": 60059,
                "name": "Better Call Saul",
                "overview": "Six years before Saul Goodman meets Walter White. We meet him when the man who will become Saul Goodman is known as Jimmy McGill.",
                "poster_path": "/fC2HDm5t0kHlJmFqBqBnb9A39H2.jpg",
                "backdrop_path": "/hPea3Qy5GdFkC9CgI5y7x9XoE2w.jpg"
            },
            {
                "id": 1396,
                "name": "Breaking Bad",
                "overview": "When Walter White, a New Mexico chemistry teacher, is diagnosed with Stage III cancer and given a prognosis of only two years left to live. He becomes filled with a sense of fearlessness and an unrelenting desire to secure his family's financial future at any cost as he enters the dangerous world of drugs and crime.",
                "poster_path": "/ztkUQFLlC19CCMYHW9o1zWhJRNq.jpg",
                "backdrop_path": "/h1Bv0y1XzIf9yI2LbnzH9g57o0F.jpg"
            },
            {
                "id": 93405,
                "name": "Squid Game",
                "overview": "Hundreds of cash-strapped players accept a strange invitation to compete in children's games—with high stakes. But, a tempting prize awaits the victor.",
                "poster_path": "/dDlEmu3EZ0PggZ2K2SVWecvrhN2.jpg",
                "backdrop_path": "/2Fk3AB8E9dY8zEwnXhaN3k10Y9U.jpg"
            }
        ]

    def get_trending_movies(self):
        if not self.api_key:
            return self._get_mock_movies()
        
        try:
            response = requests.get(f"{self.BASE_URL}/trending/movie/day", params={"api_key": self.api_key})
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.RequestException:
            return self._get_mock_movies()

    def get_popular_series(self):
        if not self.api_key:
            return self._get_mock_series()
        
        try:
            response = requests.get(f"{self.BASE_URL}/tv/popular", params={"api_key": self.api_key})
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.RequestException:
            return self._get_mock_series()

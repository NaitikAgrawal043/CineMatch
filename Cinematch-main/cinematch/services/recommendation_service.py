import os
import pickle
import pandas as pd
from django.conf import settings

class RecommendationService:
    _instance = None

    def __init__(self):
        self.movies = None
        self.similarity = None
        self._load_models()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_models(self):
        possible_dirs = [
            settings.BASE_DIR,
            os.path.abspath(os.path.join(settings.BASE_DIR, '..')),
            os.path.abspath(os.path.join(settings.BASE_DIR, '../..')),
        ]
        
        movies_dict_path = None
        similarity_path = None

        for d in possible_dirs:
            p1 = os.path.join(d, 'movies_dict.pkl')
            p2 = os.path.join(d, 'similarity.pkl')
            if os.path.exists(p1) and movies_dict_path is None:
                movies_dict_path = p1
            if os.path.exists(p2) and similarity_path is None:
                similarity_path = p2

        if movies_dict_path and similarity_path:
            try:
                with open(movies_dict_path, 'rb') as f:
                    movies_dict = pickle.load(f)
                self.movies = pd.DataFrame(movies_dict)
                with open(similarity_path, 'rb') as f:
                    self.similarity = pickle.load(f)
                print(f"[RecommendationService] Successfully loaded {len(self.movies)} movies and similarity matrix ({self.similarity.shape}).")
            except Exception as e:
                print(f"[RecommendationService] Error loading pickles: {e}")
        else:
            print("[RecommendationService] Warning: Model pickle files not found in searched directories.")

    def get_all_titles(self):
        if self.movies is not None and 'title' in self.movies:
            return self.movies['title'].values.tolist()
        return []

    def get_recommendations(self, movie_title, top_n=5):
        if self.movies is None or self.similarity is None:
            return []
        
        title_lower = movie_title.strip().lower()
        # Exact match first
        matches = self.movies[self.movies['title'].str.lower() == title_lower]
        
        # Fallback to partial match if no exact match
        if matches.empty:
            matches = self.movies[self.movies['title'].str.lower().str.contains(title_lower, regex=False)]

        if matches.empty:
            return []

        movie_idx = matches.index[0]
        selected_movie = self.movies.iloc[movie_idx]

        distances = self.similarity[movie_idx]
        # Sort by similarity score descending, skip the first (the movie itself)
        ranked = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])
        recommendations = []

        for idx, score in ranked:
            if idx == movie_idx:
                continue
            rec_movie = self.movies.iloc[idx]
            match_pct = round(float(score) * 100, 1)
            recommendations.append({
                'movie_id': int(rec_movie.movie_id),
                'title': rec_movie.title,
                'score': float(score),
                'match_percentage': match_pct,
            })
            if len(recommendations) >= top_n:
                break

        return recommendations

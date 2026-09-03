"""
Build script run on Render at deploy time.
Generates similarity.pkl from movies_dict.pkl if it doesn't already exist.
This avoids committing the 176MB similarity matrix to GitHub.
"""
import os
import pickle
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
MOVIES_PKL = os.path.join(BASE, 'movies_dict.pkl')
SIM_PKL = os.path.join(BASE, 'similarity.pkl')

def build_similarity():
    if os.path.exists(SIM_PKL):
        print("[build] similarity.pkl already exists, skipping generation.")
        return

    if not os.path.exists(MOVIES_PKL):
        print("[build] ERROR: movies_dict.pkl not found! Cannot build similarity matrix.")
        sys.exit(1)

    print("[build] Loading movies_dict.pkl ...")
    import pandas as pd
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    with open(MOVIES_PKL, 'rb') as f:
        movies_dict = pickle.load(f)

    movies = pd.DataFrame(movies_dict)
    print(f"[build] Loaded {len(movies)} movies.")

    # Build TF-IDF tags vector
    if 'tags' not in movies.columns:
        print("[build] ERROR: 'tags' column not found in movies_dict.")
        sys.exit(1)

    movies['tags'] = movies['tags'].fillna('').astype(str)

    print("[build] Building TF-IDF matrix (max_features=5000) ...")
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
    tfidf_matrix = tfidf.fit_transform(movies['tags'])

    print("[build] Computing cosine similarity matrix ...")
    similarity = cosine_similarity(tfidf_matrix)

    print(f"[build] Similarity matrix shape: {similarity.shape}")
    print("[build] Saving similarity.pkl ...")
    with open(SIM_PKL, 'wb') as f:
        pickle.dump(similarity, f)

    print("[build] Done! similarity.pkl saved.")

if __name__ == '__main__':
    build_similarity()

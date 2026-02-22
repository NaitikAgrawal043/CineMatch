from flask import Flask, render_template, request, jsonify
import pickle
import pandas as pd
import requests

app = Flask(__name__)

# Load the data generated from the Jupyter Notebook
try:
    movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except Exception as e:
    print(f"Error loading pickle files: {e}. Make sure you generated them in your notebook.")

# TMDB API Key for fetching movie posters
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8" 

def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        data = requests.get(url).json()
        poster_path = data['poster_path']
        full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
        return full_path
    except:
        # Fallback image if poster is not found
        return "https://via.placeholder.com/500x750?text=No+Poster+Available"

def get_recommendations(movie_title):
    try:
        # Case insensitive search
        movie_index = movies[movies['title'].str.lower() == movie_title.lower()].index
        if len(movie_index) == 0:
            return []
        movie_index = movie_index[0]
        distances = similarity[movie_index]
        # Get top 5 similar movies (skipping the first one as it is the movie itself)
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        recommended_movies = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            title = movies.iloc[i[0]].title
            poster = fetch_poster(movie_id)
            
            recommended_movies.append({
                "title": title, 
                "poster": poster
            })
        return recommended_movies
    except Exception as e:
        print(f"Error in get_recommendations: {e}")
        return []

@app.route('/')
def index():
    # Send all movie titles to populate the datalist for auto-complete
    movie_titles = movies['title'].values.tolist()
    return render_template('index.html', movie_list=movie_titles)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    movie_name = data.get('movie_name')
    recommendations = get_recommendations(movie_name)
    return jsonify(recommendations)

if __name__ == '__main__':
    app.run(debug=True)
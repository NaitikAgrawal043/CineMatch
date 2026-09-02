# CineMatch 🎬 | AI Cinema Intelligence & Discovery Platform

A unified, modern web platform combining **Content-Based Vector Movie Recommendations** (TF-IDF + Snowball Stemming) and **Deep Learning Review Sentiment Analysis** (Sequential LSTM Neural Network) built with Django.

---

## ✨ Key Capabilities

1. **AI Vector Movie Recommender**:
   - Analyzes 4,806 movies across plot overviews, genres, cast, directors, and keywords.
   - 5,000-dimensional TF-IDF feature space with Snowball stemming for sub-3ms pairwise cosine similarity ranking.
   - Dynamic autocomplete search with curated quick-discovery starter titles.
2. **LSTM Neural Review Sentiment Engine**:
   - Deep sequential LSTM model trained on 50,000 IMDB movie reviews achieving **87.43%** test accuracy.
   - Interactive live analyzer with real-time polarity classification (Positive 😊 / Negative 😔) and confidence meter.
3. **Community Review Portal**:
   - Full CRUD community movie critique system with instant one-click sentiment analysis.
4. **Resilient Poster Proxy**:
   - Server-side image caching proxy with dynamic SVG fallback posters.

---

## 📂 Project Architecture

```
movie_recommendation system/
├── Cinematch-main/
│   └── cinematch/
│       ├── cinesense/                 # Core Django project settings & URLs
│       ├── review/                    # Main app (views, models, forms, templates)
│       │   ├── models/                # LSTM model.pkl & tokenizer.pkl
│       │   └── templates/             # Landing, Recommender, Sentiment Analyzer, Reviews
│       ├── services/                  # Business logic & ML Singleton services
│       │   ├── recommendation_service.py
│       │   └── tmdb_service.py
│       ├── static/                    # CSS, JS, and asset stylesheets
│       └── manage.py
├── notebooks/                         # ML Model Training Pipelines
│   ├── 1_movie_recommendation_tfidf.ipynb
│   └── 2_sentiment_analysis_lstm.ipynb
├── movies_dict.pkl                    # Ingested movie catalog dictionary
├── similarity.pkl                     # 4,806 x 4,806 Cosine Similarity Matrix
├── tmdb_5000_movies.csv               # TMDB raw movie dataset
├── tmdb_5000_credits.csv              # TMDB raw credits dataset
└── README.md
```

---

## 🚀 Getting Started

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/NaitikAgrawal043/CineMatch.git
cd CineMatch

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirement.txt
```

### 2. Run the Unified Server

```bash
cd Cinematch-main/cinematch
python manage.py migrate
python manage.py runserver 8000
```

Open in your browser:
* **Home Landing Page**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Recommender Workspace**: [http://127.0.0.1:8000/recommend/](http://127.0.0.1:8000/recommend/)
* **Live Sentiment Analyzer**: [http://127.0.0.1:8000/sentiment/](http://127.0.0.1:8000/sentiment/)
* **Community Reviews**: [http://127.0.0.1:8000/review/reviews/](http://127.0.0.1:8000/review/reviews/)

---

## 🛠 Tech Stack

* **Web Framework**: Django 6.x
* **Deep Learning & NLP**: TensorFlow 2.x, Keras (Sequential LSTM), Scikit-Learn (TF-IDF Vectorizer), NLTK (SnowballStemmer)
* **Data Processing**: Pandas, NumPy, Pickle
* **Frontend**: HTML5, Vanilla CSS Design System, Bootstrap 5.3, FontAwesome 6, Google Fonts
* **Database**: SQLite3

---

## 📄 License

This project is licensed under the MIT License.

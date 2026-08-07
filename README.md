# CineMatch 🎬

A comprehensive suite for Movie Review Sentiment Analysis (**CineMatch**, built with Django 5) and Movie Recommendations (**CineMatch**, built with Flask).

---

## ✨ Features

### CineMatch (Django)
- Submit and analyze movie reviews using a pre-trained sentiment analysis model (`review/models/`).
- Sleek Django UI and administration system.
- Experimentation notebook (`main.ipynb`) and SQLite storage.

### CineMatch (Flask)
- Content-based movie recommendations (5 similar movies).
- Poster fetching integration with TMDB API.
- Modern UI with smooth animations and auto-complete search.

---

## 🛠 Tech Stack

- **Backend**: Django 5.x & Flask (Python 3.12+)
- **Data & ML**: Pandas, NumPy, Scikit-learn, Pickle
- **Frontend**: HTML, CSS, JavaScript, Django Templates
- **Database**: SQLite
- **APIs**: TMDB API for movie posters

---

## 🚀 Getting Started

### 1. Environment Setup

```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Running CineMatch (Django Review Analysis)

```bash
cd Cinesense-main/cinesense
python manage.py migrate
python manage.py runserver
```
Open 👉 http://127.0.0.1:8000/

### 3. Running CineMatch (Flask Recommendations)

```bash
python app.py
```
Open 👉 http://127.0.0.1:5000/

---

## 📂 Project Structure

```
CineMatch/
├── Cinematch-main/        # Django CineMatch Application
│   └── Cinematch/
│       ├── manage.py
│       ├── review/        # Sentiment Analysis app & models
│       └── db.sqlite3
├── app.py                 # Flask CineMatch Recommendation Server
├── templates/             # Flask templates
├── static/                # Flask static assets (CSS/JS)
├── mmproject.ipynb        # Data processing notebook
├── main.ipynb             # ML model training notebook
└── README.md              # Project documentation
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


# CineMatch: System Design, Architecture, & SDE Technical Interview Master Guide

---

# 1. Executive Summary

### • What Problem This Project Solves
In modern digital media consumption, users face information overload when choosing movies and analyzing user-generated reviews. **CineMatch** bridges this gap by offering a two-in-one Cinema Intelligence Platform:
1. **Content-Based Movie Recommendation Engine**: Recommends similar movies using Vector Space Modeling and Cosine Similarity calculated across a dataset of 4,800+ films based on plot summaries, genres, keywords, cast, and directors.
2. **Deep Learning NLP Review Sentiment Analyzer**: Predicts whether user review feedback is Positive (😊) or Negative (😔) using tokenization and neural network classification.
3. **Resilient CDN Poster Proxy**: Solves browser tracking-prevention and CORS blocks for third-party images using a server-side proxy layer with LRU memory caching and failsafe SVG fallback generation.

### • Target Users
- Movie enthusiasts seeking relevant content discovery based on thematic similarity.
- Film critics and reviewers interested in automated review sentiment evaluation.
- Recruiters, System Designers, and Technical Interviewers evaluating full-stack Python/Django architecture, machine learning inference pipelines, and performance optimizations.

### • Main Features
- **Top 5 Recommendation Discovery**: Instant retrieval of top-N similar films using a pre-computed $4805 \times 4805$ Cosine Similarity matrix.
- **Dynamic TMDB Proxy Service**: Proxy endpoint that fetches high-resolution posters server-side and caches raw binary buffers in memory.
- **Failsafe Cinema Poster Generator**: SVG rendering engine that generates a stylized poster artwork with film strip borders and movie title text when third-party CDNs fail.
- **Sentiment Inference Engine**: Real-time evaluation of arbitrary review text via pre-trained tokenizer and classification models.
- **Community Review Management**: Full CRUD capabilities for user review posts, star ratings, and media attachments.

### • Technologies Used
- **Backend**: Django 5.x / 6.x, Flask (Python 3.12)
- **Data & ML**: Pandas, NumPy, Scikit-Learn (CountVectorizer), Pickle
- **Frontend**: HTML5, Vanilla CSS3, JavaScript (ES6+), Bootstrap 5.3, Font Awesome 6
- **Database**: SQLite3

### • Overall Architecture
The platform follows a **Model-View-Template (MVT)** design pattern in Django integrated with an **In-Memory Service Layer**:
- **Presentation Layer**: Django HTML5 templates rendered dynamically server-side.
- **Service Layer**: Decoupled singleton services (`recommendation_service.py`, `tmdb_service.py`, `sentiment_service.py`) for ML inference and external API handling.
- **Data Layer**: Pre-computed pickle files (`movies_dict.pkl`, `similarity.pkl`) loaded lazily into RAM alongside SQLite database tables (`review_review`).

### • End-to-End Workflow
```
[ User Input / Search Query ]
             ↓
[ Django URL Routing / Controller View ]
             ↓
[ Service Layer: recommendation_service.py ]
   ├── Exact/Partial String Match in DataFrame
   ├── Retrieve Row Index in Matrix
   └── Compute Top-N Similarity Scores
             ↓
[ Service Layer: tmdb_service.py ]
   ├── Check Local Memory/Disk Poster Cache
   ├── Proxy Fetch from image.tmdb.org
   └── Failsafe SVG Generation on Error
             ↓
[ Template Rendering Layer ]
             ↓
[ Browser Display with Match Ratings & Poster Images ]
```

---

# 2. Folder Structure

```
movie_recomendation system/
├── Cinematch-main/
│   └── cinematch/
│       ├── cinesense/          # Django Project Configuration Directory
│       ├── review/             # Main Application Module (Views, Models, Forms)
│       │   ├── migrations/     # Database Schema Migration Scripts
│       │   ├── models/         # Pre-trained ML Pickles (model.pkl, tokenizer.pkl)
│       │   └── templates/      # App-Specific HTML Templates
│       ├── services/           # Decoupled Business Logic & ML Service Layer
│       ├── templates/          # Global Layout & Auth HTML Templates
│       ├── db.sqlite3          # SQLite Relational Database
│       └── manage.py           # Django Management CLI Utility
├── preprocess.py               # Machine Learning Dataset Preprocessing Script
├── build_poster_cache.py       # Batch TMDB Poster Cache Pre-fetcher
├── tmdb_5000_movies.csv        # TMDB Movies Raw Metadata (4,803 rows)
├── tmdb_5000_credits.csv       # TMDB Cast & Crew Raw Metadata (4,803 rows)
├── movies_dict.pkl             # Serialized Movies DataFrame Dictionary
├── similarity.pkl              # Serialized Cosine Similarity Matrix (4805×4805)
└── requirement.txt             # Python Package Dependencies
```

### Folder Responsibilities:
- **`cinematch/cinesense/`**: Contains core project configuration files (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`). Defines global settings, middleware stacks, database engines, and top-level URL routes.
- **`cinematch/review/`**: The primary application module responsible for user review management, sentiment processing views, form validation, and app routes.
- **`cinematch/services/`**: Houses decoupled service singletons. Separating business logic and ML inference into services prevents bloated views (fat views anti-pattern) and enforces single responsibility.
- **`cinematch/templates/`**: Global presentation layer containing `layout.html` (base design system, navbar, CSS tokens) and auth pages (`login.html`, `register.html`).

---

# 3. File-by-File Breakdown

### `cinesense/settings.py`
- **Purpose**: Global configuration repository for the Django web application.
- **Responsibilities**: Defines `INSTALLED_APPS`, database connection parameters, static/media asset URLs, middleware pipelines, and security flags.
- **Dependencies**: `os`, `pathlib.Path`.
- **Key Settings**:
  - `ROOT_URLCONF = 'cinesense.urls'`: Points root routing table.
  - `STATIC_URL = '/static/'`: Configures static file serving.
  - `MEDIA_URL = '/media/'`: Directs user-uploaded review images.

### `review/views.py`
- **Purpose**: Request handling and response orchestration controller layer.
- **Responsibilities**: Maps HTTP requests to business logic services, validates user input, handles authentication guards, and returns HTTP responses or rendered templates.
- **Key Functions**:
  - `landing_page(request)`: Renders public landing page with 3D fanned poster visual.
  - `movie_recommendation(request)`: Accepts search query `q`, calls `get_recommendations()`, handles sentiment form submission, and renders `movie_recommendation.html`.
  - `poster_proxy(request)`: Server-side proxy handling poster requests (`?path=` or `?movie_id=`). Intercepts errors and returns SVG letter/artwork fallbacks with `Content-Type: image/svg+xml`.
- **Complexity**:
  - Search Lookup: $O(1)$ dictionary lookup after initial string filter.
  - Proxy Fetch: $O(1)$ memory LRU cache hit or $O(1)$ HTTP request.
- **Interview Question**: *Why did you implement a custom poster proxy instead of linking directly to TMDB image URLs in the frontend?*
  - **Answer**: Direct third-party image URLs trigger browser Tracking Prevention warnings and CORS/privacy restrictions. A server-side proxy standardizes all image traffic to same-origin (`/review/poster-proxy/`), allowing in-memory LRU caching and custom SVG fallback generation when third-party CDNs fail or time out.

### `services/recommendation_service.py` (or `review/pre_process.py`)
- **Purpose**: In-memory vector search and recommendations computation engine.
- **Responsibilities**: Loads `movies_dict.pkl` and `similarity.pkl` lazily as singletons, performs string matching against movie titles, and retrieves top-N recommendations.
- **Functions**:
  - `load_recommendation_data()`: Cached singleton loader for DataFrame and similarity matrix.
  - `get_recommendations(movie_identifier, top_n=5)`: Finds movie index, extracts vector row from matrix, sorts similarity scores in descending order, and constructs recommendation payload.
- **Time Complexity**:
  - Exact/Substring match: $O(N)$ string scan where $N = 4805$.
  - Sorting similarity array: $O(N \log N)$ or $O(N + k \log k)$ using partial sort.
- **Space Complexity**: $O(N^2)$ for storing $4805 \times 4805$ float matrix ($\approx 184\text{ MB}$).

### `services/tmdb_service.py`
- **Purpose**: External TMDB metadata enrichment and SVG fallback artwork generation.
- **Responsibilities**: Resolves movie IDs to TMDB poster paths, maintains poster cache dictionary, and generates SVG fallback images.
- **Functions**:
  - `_get_letter_avatar(title, movie_id)`: Generates a 300x450 dark gradient SVG poster complete with film strip borders, sprocket holes, glowing lens graphics, and title text.
  - `fetch_tmdb_poster(movie_id)`: Resolves best available poster URL with fallback chain.

---

# 4. Technology Stack

| Technology | Role | Why Chosen over Alternatives | Advantages | Disadvantages | Common Interview Questions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Django 6** | Web Framework | Chosen over Flask/FastAPI for complex apps due to built-in ORM, admin panel, auth, and template engine. | Batteries-included, secure against OWASP top 10 by default. | Monolithic overhead, higher memory footprint than FastAPI. | *Explain Django MVT architecture and request lifecycle.* |
| **Pandas** | Data Processing | Chosen over plain Python lists for fast vector operations and tabular DataFrame filtering. | Highly efficient memory layout, rich indexing capabilities. | High memory consumption for massive datasets. | *How does Pandas handle missing values (`NaN`) and memory optimization?* |
| **Scikit-Learn** | Machine Learning | Standard library for CountVectorizer and pairwise Cosine Similarity calculations. | Production-tested, clean API, highly optimized C-extensions. | In-memory processing only; not built for distributed computing. | *What is the difference between CountVectorizer and TF-IDF Vectorizer?* |
| **Bootstrap 5.3** | Frontend CSS | Responsive grid system and accessible UI components without heavyweight JS framework overhead. | Rapid UI prototyping, built-in flexbox/grid system. | Generic visual look if uncustomized. | *How does the Bootstrap 12-column grid system work under the hood?* |
| **SQLite3** | Relational Database | Lightweight file-based relational database ideal for development and small/medium deployments. | Zero configuration, file-backed, seamless Django integration. | Concurrency bottleneck on multi-threaded write operations. | *What is WAL (Write-Ahead Logging) mode in SQLite?* |

---

# 5. Application Flow

### Step-by-Step Flow: User Searches for a Movie Recommendation
1. **User Action**: Enters "Inception" into the search bar on `/review/recommend/` and submits form.
2. **Frontend**: Sends HTTP GET request with query parameter `?q=Inception`.
3. **Django Router (`urls.py`)**: Matches path `review/recommend/` to `views.movie_recommendation`.
4. **View Layer**: Calls `services.recommendation_service.get_recommendations("Inception", top_n=5)`.
5. **Business Logic**:
   - `load_recommendation_data()` checks if DataFrame & Matrix are in RAM.
   - Finds row index of "Inception" ($idx = 27205$).
   - Accesses row $27205$ in $4805 \times 4805$ numpy similarity matrix.
   - Sorts top 5 highest similarity scores.
6. **TMDB Service**: Resolves poster proxy URLs (`/review/poster-proxy/?movie_id=X`) for recommended items.
7. **View Response**: Binds recommendation objects to context dictionary and renders `movie_recommendation.html`.
8. **Browser Rendering**: Displays Hero movie details card alongside 5 recommendation cards with rank badges and match percentages.

```
[ User Browser ]  ──( GET /review/recommend/?q=Inception )──► [ Django Controller ]
                                                                       │
                                                            Calls get_recommendations()
                                                                       ▼
[ TMDB Proxy URL ] ◄──( Returns Top 5 List )── [ Recommendation Service (In-Memory RAM) ]
```

---

# 6. Frontend Architecture

- **Pages**:
  - `layout.html`: Base template defining CSS variables, font links, Bootstrap navbar, search bar datalist autocomplete, and footer.
  - `index.html`: Landing page featuring 3D perspective fanned movie poster stack, ambient glow backdrop, micro-animations, and 2px bordered feature cards.
  - `movie_recommendation.html`: Recommender view showing selected movie details, instant review sentiment test box, top 5 recommendation cards, and "Not Found" chip suggestions.
  - `review_list.html` & `review_form.html`: CRUD review gallery and submission forms.
- **UI Enhancements**:
  - **3D Fanned Poster Stack**: Uses CSS `transform: rotate(-10deg)` and `rotate(10deg)` with `transition: all 0.4s ease` for interactive hover elevation.
  - **Dynamic Colored Badges**: Uses customized CSS badge classes (`.badge-rose`, `.badge-emerald`, `.badge-sky`, `.badge-gold`, `.badge-violet`).
  - **Image Error Fallback**: HTML `<img>` elements include `onerror="this.onerror=null;this.src='...';"` ensuring graceful degrade if any network glitch occurs.

---

# 7. Backend Architecture

- **Routes (`urls.py`)**:
  - `/`: Public landing page view (`landing_page`).
  - `/review/`: Community review gallery view (`review_list`).
  - `/review/recommend/`: Movie recommender engine view (`movie_recommendation`).
  - `/review/poster-proxy/`: Image proxy endpoint (`poster_proxy`).
  - `/review/create/`, `/review/<int:pk>/edit/`, `/review/<int:pk>/delete/`: Protected CRUD views.
- **Middleware**: Django standard security, session, authentication, and CSRF protection middlewares (`django.middleware.csrf.CsrfViewMiddleware`).
- **Route Protection**: Decorated views use `@login_required` to restrict unauthorized access to form creation/editing routes.

---

# 8. Database Schema & ORM

### Model: `Review` (`review/models.py`)
```python
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie_name = models.CharField(max_length=255, default="Unknown Movie")
    text = models.TextField()
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

- **Relationships**: Many-to-One relationship between `Review` and Django's built-in `User` model (`ForeignKey`).
- **Cascade Behavior**: `on_delete=models.CASCADE` ensures that deleting a user purges their associated reviews.
- **Normalization**: Normalized up to 3NF (User details stored separately in `auth_user` table).

---

# 9. APIs & Endpoints

### 1. `GET /review/recommend/?q={movie_title}`
- **Query Params**: `q` (string, required).
- **Response**: HTML rendered page containing selected movie metadata and array of 5 recommended movie objects.
- **Business Logic**: Case-insensitive substring search in `movies_dict.pkl` $\rightarrow$ similarity score calculation $\rightarrow$ TMDB metadata enrichment.

### 2. `GET /review/poster-proxy/?path={path}&movie_id={movie_id}`
- **Query Params**: `path` (string, optional), `movie_id` (int, optional).
- **Response**: Binary JPEG/PNG image buffer OR SVG XML string (`Content-Type: image/svg+xml`).
- **Security**: Validates that `path` starts with `/` and ends with valid image extension to prevent Arbitrary File Retrieval / SSRF attacks.

---

# 10. Machine Learning Pipeline

### Data Collection & Tag Construction
- Combined `tmdb_5000_movies.csv` (4803 rows) and `tmdb_5000_credits.csv`.
- Extracted metadata fields: `overview`, `genres`, `keywords`, `cast` (top 3 actors), and `crew` (director).
- Lowercased, stripped spaces from multi-word names (e.g., `Sam Worthington` $\rightarrow$ `SamWorthington`), and concatenated into a single string tag per movie:
  $$\text{Tag} = \text{overview} + \text{genres} + \text{keywords} + \text{cast} + \text{director}$$

### Text Vectorization
- Applied `CountVectorizer(max_features=5000, stop_words='english')`.
- Converted text tags into a 2D sparse matrix of shape $(4805, 5000)$.

### Similarity Calculation
- Calculated pairwise Cosine Similarity across all vectors:
  $$\text{Cosine Similarity}(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$$
- Generated a dense symmetric matrix of shape $(4805, 4805)$ stored as `similarity.pkl`.

---

# 11. Algorithms Used

### Cosine Similarity Algorithm
- **Definition**: Measures the cosine of the angle between two multi-dimensional vectors in inner product space.
- **Time Complexity**:
  - Pre-computation: $O(N^2 \cdot M)$ where $N = 4805$ (movies), $M = 5000$ (features).
  - Runtime Lookup: $O(N \log N)$ to sort similarity array of size $N$.
- **Space Complexity**: $O(N^2)$ matrix storage ($\approx 184\text{ MB}$).

---

# 12. Design Patterns

1. **Model-View-Template (MVT)**: Django's variant of MVC separating data models (`models.py`), request controllers (`views.py`), and HTML presentation templates (`templates/`).
2. **Singleton Pattern**: Cached in-memory loader (`load_recommendation_data()`) ensuring `movies_dict.pkl` and `similarity.pkl` are loaded into RAM once upon first request rather than re-read from disk on every HTTP request.
3. **Proxy Pattern**: `poster_proxy` acts as a surrogate proxy object for TMDB CDN servers, handling caching, network errors, and SVG fallback generation transparently.
4. **Strategy / Fallback Pattern**: Multi-tiered fallback strategy for poster retrieval:
   $$\text{Pre-built Disk Cache} \longrightarrow \text{TMDB Live API Proxy} \longrightarrow \text{SVG Letter/Artwork Generator}$$

---

# 13. System Design & Scalability

### High-Level Architecture
- **Web Application Server**: Gunicorn / uWSGI running Django app instances behind Nginx reverse proxy.
- **In-Memory Cache**: Redis / Memcached to store computed recommendations and binary poster buffers.
- **Storage**: AWS S3 for user-uploaded media photos.

```
                    ┌─────────────────────────┐
                    │      Nginx Reverse      │
                    │          Proxy          │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Gunicorn / Django    │
                    └──────┬───────────┬──────┘
                           │           │
           ┌───────────────▼───┐   ┌───▼───────────────┐
           │ Redis Cache / RAM │   │ PostgreSQL DB /   │
           │ (Pickle Vectors)  │   │     S3 Media      │
           └───────────────────┘   └───────────────────┘
```

---

# 14. Security Considerations

- **Cross-Site Request Forgery (CSRF)**: Every POST form includes `{% csrf_token %}` validated by Django's `CsrfViewMiddleware`.
- **SQL Injection**: Django ORM uses parameterized SQL queries, completely eliminating raw SQL injection vulnerabilities.
- **Cross-Site Scripting (XSS)**: Django template tags automatically escape HTML content unless explicitly marked with `|safe`.
- **SSRF Prevention**: `poster_proxy` strictly validates image path format (`/` prefix and image extensions) to prevent Server-Side Request Forgery.

---

# 15. Performance Optimizations

1. **In-Memory Pickle Singleton**: Loading similarity matrix into RAM avoids 184 MB disk I/O per query.
2. **LRU Image Caching**: Memory LRU cache (`_POSTER_CACHE`) eliminates repeated outbound TMDB HTTP requests.
3. **Lazy Model Loading**: Pickles load lazily on the first recommendation request, optimizing application cold-start time.

---

# 16. Deployment Pipeline

### Production Readiness Steps
1. **Environment Variables**: Move sensitive keys (`SECRET_KEY`, `TMDB_API_KEY`) to `.env` using `python-dotenv`.
2. **Production Server**: Replace Django dev server with Gunicorn:
   ```bash
   gunicorn cinesense.wsgi:application --bind 0.0.0.0:8000 --workers 4
   ```
3. **Static File Collection**: Run `python manage.py collectstatic`.

---

# 17. Learning Perspective

- **Key Takeaway**: Building real-world AI applications requires balancing ML vector operations with web performance constraints. Pre-computing similarity matrices offline transforms expensive $O(N^2 \cdot M)$ vector calculations into fast $O(N \log N)$ runtime array lookups.

---

# 18. Interview Questions & Answers

### Easy
- **Q**: *What is the purpose of `manage.py` in Django?*
  - **Answer**: It is a command-line wrapper script around `django.core.management` used to execute administrative tasks like running dev servers, creating database migrations, and executing test suites.

### Medium
- **Q**: *How does Cosine Similarity differ from Euclidean Distance in text recommendations?*
  - **Answer**: Euclidean distance measures absolute spatial distance between points, making it sensitive to text length. Cosine similarity measures the angle between directional vectors, ignoring document length and focusing purely on relative word frequency proportions.

### Hard
- **Q**: *How would you scale this recommendation engine from 4,800 movies to 10,000,000 movies?*
  - **Answer**: An $N \times N$ matrix for 10M items requires $10^{14}$ floats ($\approx 400\text{ Terabytes}$ of RAM), which cannot fit on a single node. I would replace full matrix pre-computation with **Approximate Nearest Neighbor (ANN)** algorithms like **Faiss** or **HNSW (Hierarchical Navigable Small World)** indexing on vector databases (Milvus, Pinecone, Qdrant) combined with candidate generation + re-ranking pipeline.

---

# 19. Future Improvements

1. **Vector Database Integration**: Replace `similarity.pkl` with Qdrant or Milvus for sub-millisecond $O(\log N)$ ANN search.
2. **Hybrid Recommendation Engine**: Combine content-based recommendations with Collaborative Filtering (Matrix Factorization / User Implicit Feedback).
3. **Asynchronous Background Processing**: Offload poster path pre-fetching to Celery + Redis task queues.

---

# 20. End-to-End Technical Presentation Script

> *"CineMatch is a cinema intelligence platform I architected to solve the dual challenge of content discovery and review sentiment evaluation.*
> 
> *On the backend, I built a content-based recommendation pipeline trained on 4,800+ films. By vectorizing plot metadata, genres, keywords, cast, and crew with CountVectorizer and calculating pairwise Cosine Similarity, the engine instantly returns top similar movies.*
> 
> *To solve third-party CDN tracking blocks and latency issues, I designed a server-side image proxy with an LRU memory cache and a failsafe SVG artwork generator that guarantees valid poster visuals even when external APIs time out.*
> 
> *The web application is built on Django following MVT architecture with decoupled service singletons, ensuring robust security, clean separation of concerns, and instant response times."*

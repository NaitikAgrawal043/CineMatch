from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
import pickle
import json
from tensorflow.keras.preprocessing.sequence import pad_sequences

from .models import Review
from .forms import ReviewForm, UserRegistrationForm
from services.recommendation_service import RecommendationService
from services.tmdb_service import get_poster_path, fetch_poster_binary, generate_fallback_svg

# Load Deep Learning Sentiment Analysis Model
model = None
tokenizer = None

def load_sentiment_model():
    global model, tokenizer
    if model is not None and tokenizer is not None:
        return
    model_path = os.path.join(settings.BASE_DIR, 'review/models/model.pkl')
    tokenizer_path = os.path.join(settings.BASE_DIR, 'review/models/tokenizer.pkl')
    try:
        with open(model_path, 'rb') as model_file:
            model = pickle.load(model_file)
        with open(tokenizer_path, 'rb') as token_file:
            tokenizer = pickle.load(token_file)
        print("[SentimentService] LSTM model & tokenizer loaded successfully.")
    except Exception as e:
        print(f"[SentimentService] Error loading sentiment model: {e}")

load_sentiment_model()

# ==============================================================================
# Landing Page vs. Recommender Views
# ==============================================================================

def landing(request):
    """
    Dedicated Home / Landing Page:
    - Welcome hero with platform value proposition & CTA buttons
    - Key performance & architecture statistics
    - Spotlight/Featured movies grid (linking directly to recommendations)
    - 3-step machine learning pipeline explanation
    - Recent community reviews
    """
    rec_service = RecommendationService.get_instance()
    movie_list = rec_service.get_all_titles()
    
    spotlight_titles = ["The Dark Knight", "Inception", "Avatar", "Interstellar", "The Avengers", "Pulp Fiction"]
    spotlight_movies = []
    
    if rec_service.movies is not None:
        for title in spotlight_titles:
            m = rec_service.movies[rec_service.movies['title'].str.lower() == title.lower()]
            if not m.empty:
                movie_row = m.iloc[0]
                poster_path = get_poster_path(movie_row.movie_id)
                if poster_path:
                    poster_url = f"/review/poster-proxy/?path={poster_path}&title={movie_row.title}&movie_id={movie_row.movie_id}"
                else:
                    poster_url = f"/review/poster-proxy/?title={movie_row.title}&movie_id={movie_row.movie_id}"
                
                spotlight_movies.append({
                    'movie_id': int(movie_row.movie_id),
                    'title': movie_row.title,
                    'poster_url': poster_url,
                })

    recent_reviews = Review.objects.all().order_by('-created_at')[:4]

    context = {
        'movie_list': movie_list,
        'spotlight_movies': spotlight_movies,
        'recent_reviews': recent_reviews,
    }
    return render(request, 'landing.html', context)


def recommend_view(request):
    """
    Dedicated Movie Recommender Workspace:
    - Interactive search input with autocomplete datalist
    - Top-5 cosine similarity recommendation cards with match scores
    - Quick category chips & similarity drill-down
    """
    rec_service = RecommendationService.get_instance()
    movie_list = rec_service.get_all_titles()
    
    query = request.GET.get('query', '').strip()
    recommendations = []
    selected_movie = query
    starter_movies = []

    if query:
        recs = rec_service.get_recommendations(query, top_n=5)
        for r in recs:
            poster_path = get_poster_path(r['movie_id'])
            if poster_path:
                proxy_url = f"/review/poster-proxy/?path={poster_path}&title={r['title']}&movie_id={r['movie_id']}"
            else:
                proxy_url = f"/review/poster-proxy/?title={r['title']}&movie_id={r['movie_id']}"
            
            r['poster_url'] = proxy_url
            recommendations.append(r)
    else:
        starter_titles = ["Inception", "The Dark Knight", "Avatar", "Interstellar", "The Avengers"]
        if rec_service.movies is not None:
            for title in starter_titles:
                m = rec_service.movies[rec_service.movies['title'].str.lower() == title.lower()]
                if not m.empty:
                    row = m.iloc[0]
                    p_path = get_poster_path(row.movie_id)
                    p_url = f"/review/poster-proxy/?path={p_path}&title={row.title}&movie_id={row.movie_id}" if p_path else f"/review/poster-proxy/?title={row.title}&movie_id={row.movie_id}"
                    starter_movies.append({
                        'movie_id': int(row.movie_id),
                        'title': row.title,
                        'poster_url': p_url
                    })

    context = {
        'movie_list': movie_list,
        'query': query,
        'selected_movie': selected_movie,
        'recommendations': recommendations,
        'starter_movies': starter_movies,
    }
    return render(request, 'recommender.html', context)


@csrf_exempt
def recommend_api(request):
    """AJAX JSON Endpoint for Movie Recommendations."""
    movie_name = request.GET.get('movie_name', '')
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            movie_name = body.get('movie_name', movie_name)
        except:
            movie_name = request.POST.get('movie_name', movie_name)

    if not movie_name:
        return JsonResponse({'error': 'No movie name provided', 'recommendations': []})

    rec_service = RecommendationService.get_instance()
    recs = rec_service.get_recommendations(movie_name, top_n=5)
    
    results = []
    for r in recs:
        poster_path = get_poster_path(r['movie_id'])
        if poster_path:
            proxy_url = f"/review/poster-proxy/?path={poster_path}&title={r['title']}&movie_id={r['movie_id']}"
        else:
            proxy_url = f"/review/poster-proxy/?title={r['title']}&movie_id={r['movie_id']}"
        
        results.append({
            'movie_id': r['movie_id'],
            'title': r['title'],
            'score': r['score'],
            'match_percentage': r['match_percentage'],
            'poster': proxy_url
        })

    return JsonResponse({'query': movie_name, 'recommendations': results})


def poster_proxy(request):
    """
    Resilient Server-side CDN Poster Proxy:
    - Fetches TMDB poster binaries with same-origin header safety
    - Falls back to dynamic stylized Cinema SVG Poster on network error or missing artwork
    """
    path = request.GET.get('path', '').strip()
    title = request.GET.get('title', 'Movie Poster').strip()
    movie_id = request.GET.get('movie_id')

    if not path and movie_id:
        try:
            path = get_poster_path(int(movie_id))
        except:
            path = None

    if path:
        binary_data, content_type = fetch_poster_binary(path)
        if binary_data:
            response = HttpResponse(binary_data, content_type=content_type)
            response['Cache-Control'] = 'public, max-age=86400'
            return response

    svg_data = generate_fallback_svg(title=title, movie_id=movie_id)
    response = HttpResponse(svg_data, content_type='image/svg+xml; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=86400'
    return response


# ==============================================================================
# Review CRUD & Dedicated Sentiment Analysis Views
# ==============================================================================

@csrf_exempt
def sentiment_analyzer_view(request):
    """
    Dedicated Interactive AI Sentiment Analyzer Tool:
    - Allows any user to input custom review text or choose sample reviews
    - Runs inference through the sequential LSTM neural network in real time
    - Returns sentiment polarity, confidence percentage, and classification report
    """
    review_text = request.POST.get('review_text', '').strip() or request.GET.get('review_text', '').strip()
    result = None

    if review_text:
        try:
            load_sentiment_model()
            if tokenizer is not None and model is not None:
                sequence = tokenizer.texts_to_sequences([review_text])
                padded_sequence = pad_sequences(sequence, maxlen=200)
                sentiment_prediction = model.predict(padded_sequence)
                confidence = float(sentiment_prediction[0][0])
                sentiment = "positive" if confidence > 0.5 else "negative"
                confidence_pct = round(confidence * 100 if sentiment == "positive" else (1 - confidence) * 100, 1)
                sentiment_color = "#059669" if sentiment == "positive" else "#e11d48"

                result = {
                    'text': review_text,
                    'sentiment': sentiment,
                    'confidence': confidence,
                    'confidence_percentage': confidence_pct,
                    'sentiment_color': sentiment_color
                }
        except Exception as e:
            print(f"[SentimentAnalyzer] Error: {e}")

    context = {
        'review_text': review_text,
        'result': result,
    }
    return render(request, 'sentiment_analyzer.html', context)


def review_list(request):
    reviews = Review.objects.all().order_by('-created_at')
    query = request.GET.get('q', '').strip()
    if query:
        reviews = reviews.filter(movie_name__icontains=query)
        return render(request, 'review_search.html', {'reviews': reviews, 'query': query})
    
    return render(request, 'review_list.html', {'reviews': reviews})


@login_required
def review_create(request):
    initial_movie = request.GET.get('movie_name', '')
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            return redirect('review_list')
    else:
        form = ReviewForm(initial={'movie_name': initial_movie} if initial_movie else None)
    return render(request, 'review_form.html', {'form': form, 'initial_movie': initial_movie})


@login_required
def review_edit(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            return redirect('review_list')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'review_form.html', {'form': form, 'is_edit': True})


@login_required
def review_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id, user=request.user)
    if request.method == 'POST':
        review.delete()
        return redirect('review_list')
    return render(request, 'review_confirm_delete.html', {'review': review})


def review_analyse(request, review_id):
    """Analyze sentiment of an existing database review (open to all users)."""
    review = get_object_or_404(Review, id=review_id)
    review_text = review.text

    try:
        load_sentiment_model()
        if tokenizer is None or model is None:
            return JsonResponse({'error': 'Sentiment model failed to initialize'}, status=500)

        sequence = tokenizer.texts_to_sequences([review_text])
        padded_sequence = pad_sequences(sequence, maxlen=200)
        sentiment_prediction = model.predict(padded_sequence)
        confidence = float(sentiment_prediction[0][0])
        sentiment = "positive" if confidence > 0.5 else "negative"
        confidence_pct = round(confidence * 100 if sentiment == "positive" else (1 - confidence) * 100, 1)

        sentiment_color = "#059669" if sentiment == "positive" else "#e11d48"

        context = {
            'review': review,
            'sentiment': sentiment,
            'confidence': confidence,
            'confidence_percentage': confidence_pct,
            'sentiment_color': sentiment_color
        }
        return render(request, 'review_analysis_result.html', context)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            return redirect('review_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})
"""
URL configuration for cinesense project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from review import views as review_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', review_views.landing, name='home'),
    path('recommend/', review_views.recommend_view, name='recommender'),
    path('sentiment/', review_views.sentiment_analyzer_view, name='sentiment_tool'),
    path('review/', include('review.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

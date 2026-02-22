function fetchRecommendations() {
    const movieInput = document.getElementById('movie-input');
    const movieName = movieInput.value.trim();
    const grid = document.getElementById('recommendations');
    const loading = document.getElementById('loading');

    // Validation
    if (!movieName) {
        showNotification("Please enter a movie name first!", "error");
        return;
    }

    // Clear previous results and show loader
    grid.innerHTML = '';
    loading.classList.remove('hidden');

    // Send POST request to Flask
    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ movie_name: movieName })
    })
    .then(response => response.json())
    .then(data => {
        // Hide loader
        loading.classList.add('hidden');

        // Handle movie not found
        if (data.length === 0) {
            grid.innerHTML = '<div class="no-results"><i class="fas fa-search"></i><p>No recommendations found. Please check your spelling or choose a movie from the dropdown.</p></div>';
            showNotification("No recommendations found. Try another movie!", "warning");
            return;
        }

        // Build Movie Cards dynamically
        data.forEach((movie, index) => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            card.style.animationDelay = `${index * 0.1}s`; // Stagger animation

            // onerror triggers if TMDB link breaks
            card.innerHTML = `
                <img src="${movie.poster}" alt="${movie.title}" class="movie-poster" onerror="this.src='https://via.placeholder.com/500x750?text=No+Poster'">
                <div class="movie-info">
                    <h3>${movie.title}</h3>
                </div>
            `;
            grid.appendChild(card);
        });

        showNotification(`Found ${data.length} great recommendations!`, "success");
    })
    .catch(error => {
        console.error('Error:', error);
        loading.classList.add('hidden');
        grid.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-triangle"></i><p>An error occurred while fetching recommendations. Please try again.</p></div>';
        showNotification("An error occurred. Please try again.", "error");
    });
}

function showNotification(message, type) {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'exclamation-circle'}"></i> ${message}`;

    document.body.appendChild(notification);

    // Show notification
    setTimeout(() => notification.classList.add('show'), 100);

    // Hide after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Enable pressing "Enter" key to trigger the search
document.getElementById("movie-input").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        document.getElementById("search-btn").click();
    }
});

// Clear input on focus if it has placeholder
document.getElementById("movie-input").addEventListener("focus", function() {
    if (this.value === this.placeholder) {
        this.value = '';
    }
});
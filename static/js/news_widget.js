document.addEventListener('DOMContentLoaded', function () {
    fetchNews();
    // Auto-refresh every 15 minutes (900,000 ms)
    setInterval(fetchNews, 900000);
});

function fetchNews() {
    const container = document.getElementById('news-container');
    if (!container) return;

    fetch('/api/news?limit=5')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.news.length > 0) {
                let html = '<div class="news-list" style="display: flex; flex-direction: column; gap: 10px;">';

                data.news.forEach(item => {
                    // Format date
                    const date = new Date(item.published);
                    const dateStr = date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

                    html += `
                        <a href="${item.link}" target="_blank" class="news-item" style="text-decoration: none; color: inherit; display: block; padding: 8px; background: rgba(0,0,0,0.03); border-radius: 8px; transition: background 0.2s;">
                            <div style="font-size: 0.85rem; font-weight: 600; color: #333; margin-bottom: 4px; line-height: 1.3;">
                                ${item.title}
                            </div>
                            <div style="font-size: 0.75rem; color: #888; display: flex; justify-content: space-between;">
                                <span>${dateStr}</span>
                                <span style="color: #ff385c;">Read More &rarr;</span>
                            </div>
                        </a>
                    `;
                });

                html += '</div>';
                container.innerHTML = html;

                // Add hover effect via JS since inline styles are limited
                const items = container.querySelectorAll('.news-item');
                items.forEach(item => {
                    item.addEventListener('mouseenter', () => item.style.background = 'rgba(0,0,0,0.06)');
                    item.addEventListener('mouseleave', () => item.style.background = 'rgba(0,0,0,0.03)');
                });

            } else {
                container.innerHTML = '<div style="font-size: 0.8rem; color: #888;">No news updates available.</div>';
            }
        })
        .catch(error => {
            console.error('Error fetching news:', error);
            container.innerHTML = '<div style="font-size: 0.8rem; color: #ff385c;">Failed to load news.</div>';
        });
}

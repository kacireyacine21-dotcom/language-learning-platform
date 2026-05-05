document.addEventListener('DOMContentLoaded', async () => {
    const grid = document.getElementById('languagesGrid');
    try {
        const res = await fetch(API_BASE_URL + '/api/languages');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const response = await res.json();
        const languages = Array.isArray(response) ? response : (response.data || []);
        if (!Array.isArray(languages)) throw new Error('Languages is not an array');
        grid.innerHTML = '';
        languages.forEach(lang => {
            const card = document.createElement('div');
            card.className = 'language-card';
            card.innerHTML = `
                <div class="flag">${lang.flag}</div>
                <h3>${lang.name}</h3>
                <p>${lang.description}</p>
                <p style="font-size:0.85rem;color:#999;">📚 ${lang.lesson_count} دروس | 📖 ${lang.vocab_count} كلمة</p>
                <a href="${isLoggedIn() ? 'dashboard.html?lang=' + lang.id : 'login.html'}" class="btn btn-primary" style="display:block;margin-top:1rem;">ابدأ التعلم</a>
            `;
            grid.appendChild(card);
        });
    } catch(e) { 
        console.error('Error loading languages:', e);
        grid.innerHTML = '<p>خطأ في التحميل</p>'; 
    }
});

// Fallback data in case API fails
const FALLBACK_LANGUAGES = [
    {id: 1, name: 'العربية', description: 'تعلم نطق اللغة العربية الفصحى', flag: '🇸🇦', lesson_count: 5, vocab_count: 3},
    {id: 2, name: 'الإنجليزية', description: 'تعلم نطق الإنجليزية الصحيح', flag: '🇺🇸', lesson_count: 5, vocab_count: 3},
    {id: 3, name: 'الفرنسية', description: 'تعلم نطق الفرنسية', flag: '🇫🇷', lesson_count: 5, vocab_count: 3},
    {id: 4, name: 'الألمانية', description: 'تعلم نطق الألمانية', flag: '🇩🇪', lesson_count: 5, vocab_count: 3},
    {id: 5, name: 'الإسبانية', description: 'تعلم نطق الإسبانية', flag: '🇪🇸', lesson_count: 5, vocab_count: 0},
    {id: 6, name: 'الإيطالية', description: 'تعلم نطق الإيطالية', flag: '🇮🇹', lesson_count: 5, vocab_count: 0},
    {id: 7, name: 'الصينية', description: 'تعلم نطق الماندرين', flag: '🇨🇳', lesson_count: 5, vocab_count: 0},
    {id: 8, name: 'اليابانية', description: 'تعلم نطق اليابانية', flag: '🇯🇵', lesson_count: 5, vocab_count: 0},
];

function displayLanguages(languages) {
    const grid = document.getElementById('languagesGrid');
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
}

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const res = await fetch(API_BASE_URL + '/api/languages');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const response = await res.json();
        const languages = Array.isArray(response) ? response : (response.data || []);
        if (!Array.isArray(languages) || languages.length === 0) throw new Error('No languages data');
        displayLanguages(languages);
    } catch(e) {
        console.error('Error loading languages from API:', e);
        console.log('Using fallback data...');
        displayLanguages(FALLBACK_LANGUAGES);
    }
});

let selectedLanguageId = null;
let allLessons = [];
let allVocab = [];

document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    selectedLanguageId = urlParams.get('lang');
    
    await loadProfile();
    await loadLanguages();
    
    if(selectedLanguageId) {
        await loadLessons(selectedLanguageId);
        await loadVocab(selectedLanguageId);
        await loadExercises(selectedLanguageId);
    }
});

async function loadProfile() {
    const res = await fetch(API_BASE_URL + '/api/user/profile', { headers: getHeaders() });
    if(res.ok) {
        const response = await res.json();
        const data = response.data || response;
        document.getElementById('lessonCount').textContent = (data.stats && data.stats.completed_lessons) || 0;
        document.getElementById('scoreAvg').textContent = ((data.stats && data.stats.average_score) || 0).toFixed(1) + '%';
    }
}

async function loadLanguages() {
    const res = await fetch(API_BASE_URL + '/api/languages');
    const response = await res.json();
    const languages = response.data || response;
    const grid = document.getElementById('languagesGrid');
    grid.innerHTML = '';
    
    languages.forEach(lang => {
        const card = document.createElement('div');
        card.className = 'language-card';
        card.style.cursor = 'pointer';
        card.innerHTML = `
            <div class="flag">${lang.flag}</div>
            <h3>${lang.name}</h3>
            <p style="font-size:0.85rem;color:#999;">📚 ${lang.lesson_count} دروس | 📖 ${lang.vocab_count} كلمة</p>
        `;
        card.onclick = () => selectLanguage(lang.id);
        grid.appendChild(card);
    });
}

async function selectLanguage(langId) {
    selectedLanguageId = langId;
    window.history.replaceState(null, '', 'dashboard.html?lang=' + langId);
    
    await loadLessons(langId);
    await loadVocab(langId);
    await loadExercises(langId);
    
    document.getElementById('lessonsTitle').style.display = 'block';
    document.getElementById('vocabTitle').style.display = 'block';
    document.getElementById('vocabControls').style.display = 'flex';
    document.getElementById('exTitle').style.display = 'block';
}

async function loadLessons(langId) {
    const res = await fetch(API_BASE_URL + '/api/lessons?language_id=' + langId);
    const response = await res.json();
    allLessons = response.data || response;
    
    const grid = document.getElementById('lessonsGrid');
    grid.innerHTML = '';
    grid.style.display = 'grid';
    
    allLessons.forEach(lesson => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <h3>${lesson.title}</h3>
            <p>${lesson.content ? lesson.content.substring(0, 100) : 'درس جديد'}</p>
            <a href="lesson.html?id=${lesson.id}" class="btn btn-primary">ابدأ الدرس</a>
        `;
        grid.appendChild(card);
    });
}

async function loadVocab(langId) {
    const res = await fetch(API_BASE_URL + '/api/vocabulary?language_id=' + langId);
    const response = await res.json();
    allVocab = response.data || response;
    
    const grid = document.getElementById('vocabGrid');
    grid.innerHTML = '';
    grid.style.display = 'grid';
    displayVocab(allVocab);
}

function displayVocab(items) {
    const grid = document.getElementById('vocabGrid');
    grid.innerHTML = '';
    
    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'vocab-card';
        card.innerHTML = `
            <div class="vocab-word">${item.word}</div>
            <div class="vocab-translation">🔤 ${item.translation}</div>
            <div style="font-size:0.8rem;opacity:0.9;">📢 ${item.pronunciation}</div>
            <div class="vocab-example">"${item.example_sentence}"</div>
            <div style="font-size:0.75rem;margin-top:0.5rem;opacity:0.8;">${item.category} • ${item.difficulty}</div>
        `;
        grid.appendChild(card);
    });
}

function filterVocab() {
    const category = document.getElementById('categoryFilter').value;
    const filtered = category ? allVocab.filter(v => v.category === category) : allVocab;
    displayVocab(filtered);
}

async function loadExercises(langId) {
    const res = await fetch(API_BASE_URL + '/api/exercises?language_id=' + langId);
    const response = await res.json();
    const exercises = response.data || response;
    
    const grid = document.getElementById('exGrid');
    grid.innerHTML = '';
    grid.style.display = 'grid';
    
    exercises.forEach((ex, idx) => {
        const card = document.createElement('div');
        card.className = 'exercise-card';
        card.innerHTML = `
            <div class="exercise-question">❓ ${ex.question}</div>
            <input type="text" class="exercise-input" id="answer${idx}" placeholder="اكتب الإجابة">
            <button onclick="submitExercise(${ex.id}, ${idx})" class="btn btn-primary" style="width:100%;">تحقق من الإجابة</button>
            <div id="result${idx}"></div>
        `;
        grid.appendChild(card);
    });
}

async function submitExercise(exId, idx) {
    const answer = document.getElementById('answer' + idx).value;
    const res = await fetch(API_BASE_URL + '/api/exercises/submit', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ exercise_id: exId, answer })
    });
    
    if(res.ok) {
        const response = await res.json();
        const data = response.data || response;
        const resultDiv = document.getElementById('result' + idx);
        resultDiv.className = data.correct ? 'result correct' : 'result incorrect';
        resultDiv.innerHTML = `
            <strong>${data.correct ? '✅ صحيح!' : '❌ خاطئ'}</strong><br>
            الإجابة الصحيحة: <strong>${data.correct_answer}</strong><br>
            ${data.explanation}
        `;
    }
}

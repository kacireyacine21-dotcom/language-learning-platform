// استخدم عنوان IP الفعلي بدلاً من localhost للسماح بالوصول من الأجهزة الأخرى
const API_BASE_URL = window.location.protocol + '//' + window.location.hostname + ':5000';

function getToken() { return localStorage.getItem('token'); }
function getUser() { return JSON.parse(localStorage.getItem('user') || '{}'); }
function isLoggedIn() { return !!getToken(); }
function getHeaders() { return { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' }; }
function logout() { localStorage.clear(); window.location.href = 'index.html'; }

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { checkAuth(); });
} else { 
    checkAuth(); 
}

function checkAuth() {
    const protectedPages = ['dashboard.html', 'lesson.html', 'vocabulary.html', 'exercises.html', 'quiz.html'];
    const currentPage = window.location.pathname.split('/').pop();
    if (protectedPages.includes(currentPage) && !isLoggedIn()) { 
        window.location.href = 'login.html'; 
    }
    const userElement = document.getElementById('userName');
    if (userElement && isLoggedIn()) {
        const user = getUser();
        userElement.textContent = user.name;
    }
}

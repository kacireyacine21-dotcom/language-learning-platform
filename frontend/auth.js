// استخدم عنوان الخادم الديناميكي - يعمل على localhost:5000، الشبكة المحلية، والـ Render
const hostname = window.location.hostname;
let API_BASE_URL;

if (hostname === 'localhost' || hostname === '127.0.0.1') {
    // Local development
    API_BASE_URL = 'http://localhost:5000';
} else if (hostname.includes('.onrender.com') || hostname.includes('.com')) {
    // Production (Render or external)
    API_BASE_URL = window.location.origin;
} else {
    // Local network access (e.g., 192.168.1.6)
    API_BASE_URL = `http://${hostname}:5000`;
}

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

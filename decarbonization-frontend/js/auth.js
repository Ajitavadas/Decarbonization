// Authentication Management
class AuthService {
    constructor() {
        this.token = localStorage.getItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
        this.userData = JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.USER_DATA) || 'null');
    }

    async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(buildUrl(CONFIG.ENDPOINTS.AUTH.LOGIN), {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        this.token = data.access_token;
        this.userData = data.user;

        localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, this.token);
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER_DATA, JSON.stringify(this.userData));

        return data;
    }

    async register(email, username, password, organizationName) {
        const response = await fetch(buildUrl(CONFIG.ENDPOINTS.AUTH.REGISTER), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                username,
                password,
                organization_name: organizationName
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }

        return await response.json();
    }

    logout() {
        this.token = null;
        this.userData = null;
        localStorage.removeItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
        localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_DATA);
        window.location.reload();
    }

    isAuthenticated() {
        return !!this.token;
    }

    getToken() {
        return this.token;
    }

    getUserData() {
        return this.userData;
    }
}

// Initialize auth service
const authService = new AuthService();

// Setup login form handler
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const authModal = document.getElementById('authModal');

    // Check if user is authenticated
    if (!authService.isAuthenticated()) {
        authModal.classList.add('active');
    } else {
        // Load user data
        const userData = authService.getUserData();
        if (userData) {
            document.getElementById('userName').textContent = userData.username || userData.email;
        }
    }

    // Login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            const loadingOverlay = document.getElementById('loadingOverlay');
            loadingOverlay.classList.add('active');

            try {
                await authService.login(username, password);
                authModal.classList.remove('active');
                loadingOverlay.classList.remove('active');

                // Reload dashboard data
                if (window.loadDashboardData) {
                    window.loadDashboardData();
                }

                // Update user name
                const userData = authService.getUserData();
                if (userData) {
                    document.getElementById('userName').textContent = userData.username || userData.email;
                }
            } catch (error) {
                loadingOverlay.classList.remove('active');
                alert('Login failed: ' + error.message);
            }
        });
    }

    // Registration form submission
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('regEmail').value;
            const username = document.getElementById('regUsername').value;
            const password = document.getElementById('regPassword').value;
            const organization = document.getElementById('regOrganization').value;

            const loadingOverlay = document.getElementById('loadingOverlay');
            loadingOverlay.classList.add('active');

            try {
                await authService.register(email, username, password, organization);

                // Auto-login after successful registration
                await authService.login(username, password);

                authModal.classList.remove('active');
                loadingOverlay.classList.remove('active');

                // Reload dashboard data
                if (window.loadDashboardData) {
                    window.loadDashboardData();
                }

                // Update user name
                const userData = authService.getUserData();
                if (userData) {
                    document.getElementById('userName').textContent = userData.username || userData.email;
                }

                alert('Account created successfully!');
            } catch (error) {
                loadingOverlay.classList.remove('active');
                alert('Registration failed: ' + error.message);
            }
        });
    }

    // Toggle between login and register views
    const showRegisterLink = document.getElementById('showRegister');
    const showLoginLink = document.getElementById('showLogin');
    const loginView = document.getElementById('loginView');
    const registerView = document.getElementById('registerView');

    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            loginView.style.display = 'none';
            registerView.style.display = 'block';
        });
    }

    if (showLoginLink) {
        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            registerView.style.display = 'none';
            loginView.style.display = 'block';
        });
    }
});

import { apiRequest, API_BASE_URL } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    const loginEmail = document.getElementById('login-email');
    const loginPassword = document.getElementById('login-password');
    const regName = document.getElementById('reg-name');
    const regEmail = document.getElementById('reg-email');
    const regPassword = document.getElementById('reg-password');
    const regConfirmPassword = document.getElementById('reg-confirm-password');

    const loginError = document.getElementById('login-error');
    const registerError = document.getElementById('register-error');

    const strengthBar = document.getElementById('password-strength');
    const strengthLabel = document.getElementById('strength-label');

    const passwordToggles = document.querySelectorAll('.password-toggle');

    // Icons
    const eyeOpen = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>`;
    const eyeClosed = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18"/></svg>`;

    // Utility: Robust JWT Decoding
    const decodeJWT = (token) => {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            return JSON.parse(window.atob(base64));
        } catch (e) {
            console.error("JWT Decode failed", e);
            return null;
        }
    };

    // Tab Switching
    function switchTab(mode) {
        if (mode === 'login') {
            tabLogin.classList.add('bg-blue-600', 'text-white', 'shadow-lg');
            tabLogin.classList.remove('text-slate-400');
            tabRegister.classList.remove('bg-blue-600', 'text-white', 'shadow-lg');
            tabRegister.classList.add('text-slate-400');

            loginForm.classList.remove('hidden-form');
            registerForm.classList.add('hidden-form');
            setTimeout(() => {
                loginForm.style.display = 'block';
                registerForm.style.display = 'none';
            }, 300);
        } else {
            tabRegister.classList.add('bg-blue-600', 'text-white', 'shadow-lg');
            tabRegister.classList.remove('text-slate-400');
            tabLogin.classList.remove('bg-blue-600', 'text-white', 'shadow-lg');
            tabLogin.classList.add('text-slate-400');

            registerForm.classList.remove('hidden-form');
            loginForm.classList.add('hidden-form');
            setTimeout(() => {
                registerForm.style.display = 'block';
                loginForm.style.display = 'none';
            }, 300);
        }
    }

    tabLogin.addEventListener('click', () => switchTab('login'));
    tabRegister.addEventListener('click', () => switchTab('register'));

    // Password Visibility Toggle
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.parentElement.querySelector('input');
            if (input.type === 'password') {
                input.type = 'text';
                toggle.innerHTML = eyeClosed;
            } else {
                input.type = 'password';
                toggle.innerHTML = eyeOpen;
            }
        });
    });

    // Email Validation (Regex)
    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    const handleEmailValidation = (input) => {
        const errorText = input.parentElement.querySelector('.error-text');
        if (input.value && !validateEmail(input.value)) {
            input.classList.add('border-red-500');
            if (errorText) {
                errorText.textContent = 'Please enter a valid clinical email address';
                errorText.classList.remove('hidden');
            }
        } else {
            input.classList.remove('border-red-500');
            if (errorText) errorText.classList.add('hidden');
        }
    };

    loginEmail.addEventListener('blur', () => handleEmailValidation(loginEmail));
    regEmail.addEventListener('blur', () => handleEmailValidation(regEmail));

    // Password Strength Meter
    regPassword.addEventListener('input', () => {
        const val = regPassword.value;
        let strength = 0;

        if (val.length > 0) strength += 20;
        if (val.length >= 8) strength += 20;
        if (/[A-Z]/.test(val)) strength += 20;
        if (/[0-9]/.test(val)) strength += 20;
        if (/[^A-Za-z0-9]/.test(val)) strength += 20;

        strengthBar.style.width = strength + '%';

        if (strength <= 40) {
            strengthBar.style.backgroundColor = '#DC2626';
            strengthLabel.textContent = 'Security Level: Low (Danger)';
            strengthLabel.style.color = '#DC2626';
        } else if (strength <= 80) {
            strengthBar.style.backgroundColor = '#F59E0B';
            strengthLabel.textContent = 'Security Level: Moderate';
            strengthLabel.style.color = '#F59E0B';
        } else {
            strengthBar.style.backgroundColor = '#16A34A';
            strengthLabel.textContent = 'Security Level: High (Secure)';
            strengthLabel.style.color = '#16A34A';
        }

        if (val.length === 0) {
            strengthLabel.textContent = 'Security Level: None';
            strengthLabel.style.color = '#94A3B8';
        }
    });

    // Utility: Show Loading
    function setLoading(form, isLoading) {
        const btn = form.querySelector('button[type="submit"]');
        const btnText = btn.querySelector('.btn-text');
        if (isLoading) {
            btn.disabled = true;
            btn.classList.add('opacity-70', 'cursor-not-allowed');
            if (!btn.querySelector('.spinner')) {
                btnText.insertAdjacentHTML('afterbegin', '<span class="spinner"></span>');
            }
        } else {
            btn.disabled = false;
            btn.classList.remove('opacity-70', 'cursor-not-allowed');
            const spinner = btn.querySelector('.spinner');
            if (spinner) spinner.remove();
        }
    }

    // Login Form Submit
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.classList.add('hidden');

        const email = loginEmail.value;
        const password = loginPassword.value;

        if (!validateEmail(email)) {
            loginEmail.classList.add('border-red-500');
            return;
        }

        setLoading(loginForm, true);

        try {
            // Match backend LoginRequest schema
            // Using API_BASE_URL explicitly as per user request to change URL calls
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Incorrect email or password');
            }

            const data = await response.json();

            if (data && data.access_token) {
                localStorage.setItem('token', data.access_token);

                // Decode JWT to get role and patient_id
                const payload = decodeJWT(data.access_token);
                if (!payload) throw new Error("Invalid token received from server");

                localStorage.setItem('role', payload.role);

                // Smart Redirection based on Backend response
                if (payload.role === 'admin') {
                    window.location.href = 'admin.html';
                } else {
                    // Patient role logic
                    if (data.patient_id || payload.patient_id) {
                        localStorage.setItem('patient_id', data.patient_id || payload.patient_id);
                        window.location.href = 'dashboard.html';
                    } else {
                        // Registration complete but profile missing
                        window.location.href = 'profile.html';
                    }
                }
            }
        } catch (error) {
            loginError.textContent = error.message || 'Incorrect email or password.';
            loginError.classList.remove('hidden');
            loginForm.classList.add('shake');
            setTimeout(() => loginForm.classList.remove('shake'), 400);
        } finally {
            setLoading(loginForm, false);
        }
    });

    // Register Form Submit
    registerForm.addEventListener('submit', async (e) => {
        // 1️⃣ Prevent Default Form Submission
        e.preventDefault();
        registerError.classList.add('hidden');

        // 2️⃣ Collect Required Fields
        const fullName = regName.value.trim();
        const email = regEmail.value.trim();
        const password = regPassword.value.trim();
        const confirmPassword = regConfirmPassword.value.trim();

        // Basic frontend validation
        if (!fullName || !email || !password) {
            registerError.textContent = "All fields are required";
            registerError.classList.remove('hidden');
            return;
        }

        if (password !== confirmPassword) {
            registerError.textContent = "Passwords do not match";
            registerError.classList.remove('hidden');
            return;
        }

        setLoading(registerForm, true);

        try {
            // 3️⃣ Send Correct POST Request
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    full_name: fullName,
                    email: email,
                    password: password,
                    role: "patient" // 🔥 Hardcoded to "patient" as requested
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Registration failed");
            }

            // 4️⃣ Auto Login After Registration
            await loginUser(email, password);

        } catch (error) {
            registerError.textContent = error.message;
            registerError.classList.remove('hidden');
            registerForm.classList.add('shake');
            setTimeout(() => registerForm.classList.remove('shake'), 400);
        } finally {
            setLoading(registerForm, false);
        }
    });

    // Login Helper Function (as requested)
    async function loginUser(email, password) {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email,
                    password
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Login failed");
            }

            const data = await response.json();

            localStorage.setItem("token", data.access_token);

            const payload = decodeJWT(data.access_token);
            if (!payload) throw new Error("Invalid token");

            localStorage.setItem('role', payload.role);
            if (data.patient_id || payload.patient_id) {
                localStorage.setItem('patient_id', data.patient_id || payload.patient_id);
            }

            const role = data.role || payload.role;
            const patientId = data.patient_id || payload.patient_id;

            if (role === "admin") {
                window.location.href = "admin.html";
            } else {
                if (!patientId) {
                    window.location.href = "profile.html";
                } else {
                    window.location.href = "dashboard.html";
                }
            }
        } catch (error) {
            console.error("Auto-login error", error);
            // Fallback if auto-login fails (shouldn't happen if reg succeeded)
            alert("Registration successful, but login failed. Please log in manually.");
            switchTab('login');
        }
    }
});

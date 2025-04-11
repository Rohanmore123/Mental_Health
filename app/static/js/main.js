// API Base URL
const API_BASE_URL = '/api/v1';

// Token Storage
function saveToken(token) {
    console.log('Saving token:', token ? token.substring(0, 10) + '...' : 'null');
    localStorage.setItem('token', token);
}

function getToken() {
    return localStorage.getItem('token');
}

function removeToken() {
    console.log('Removing token');
    localStorage.removeItem('token');
}

// Check if user is logged in
function isLoggedIn() {
    return !!getToken();
}

// Redirect if not logged in
function requireAuth() {
    console.log('Checking authentication...');
    if (!isLoggedIn()) {
        console.log('Not logged in, redirecting to login page');
        window.location.href = '/login';
    } else {
        console.log('User is authenticated');
    }
}

// API Calls with Fetch
async function apiCall(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json'
    };

    // Add auth token if available
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const options = {
        method,
        headers
    };

    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

        // Handle unauthorized
        if (response.status === 401) {
            console.log('Unauthorized access, redirecting to login');
            removeToken();
            window.location.href = '/login?error=session_expired';
            return null;
        }

        try {
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Non-JSON response:', await response.text());
                throw new Error('Server returned non-JSON response');
            }

            const result = await response.json();
            console.log(`API response for ${endpoint}:`, result);

            if (!response.ok) {
                throw new Error(result.detail || 'Something went wrong');
            }

            return result;
        } catch (parseError) {
            console.error('Error parsing API response:', parseError);
            if (response.status === 404) {
                console.error('404 Not Found error for endpoint:', endpoint);
                showError(`Resource not found: ${endpoint}`);
            } else {
                showError(`Error processing response: ${parseError.message}`);
            }
            return null;
        }
    } catch (error) {
        console.error(`API Error for ${endpoint}:`, error);
        showError(error.message);
        return null;
    }
}

// Login Function
async function login(email, password, userType) {
    try {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        console.log(`Attempting to login with email: ${email}`);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            body: formData
        });

        console.log('Login response status:', response.status);

        // Check if the response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text);
            throw new Error('Server returned non-JSON response');
        }

        const data = await response.json();
        console.log('Login response data:', data);

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        // Save token and user information
        saveToken(data.access_token);
        localStorage.setItem('userType', userType);
        localStorage.setItem('userId', data.user_id || '');
        localStorage.setItem('userEmail', data.email || '');
        localStorage.setItem('userName', data.name || '');
        localStorage.setItem('userRoles', data.roles || '');
        localStorage.setItem('loginTime', new Date().toISOString());

        // Show success message
        showSuccess('Login successful! Redirecting to dashboard...');

        // Redirect to dashboard after a short delay
        setTimeout(() => {
            if (userType === 'patient') {
                window.location.href = '/patient-dashboard';
            } else if (userType === 'doctor') {
                window.location.href = '/doctor-dashboard';
            } else {
                window.location.href = '/';
            }
        }, 1500);

    } catch (error) {
        console.error('Login Error:', error);
        showError(error.message);
    }
}

// Logout Function
function logout() {
    console.log('Logging out...');
    // Clear all user data
    removeToken();
    localStorage.removeItem('userType');
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userName');
    localStorage.removeItem('userRoles');
    localStorage.removeItem('loginTime');

    // Redirect to login page
    window.location.href = '/login';
}

// Show Error Message
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';

        // Hide after 5 seconds
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    } else {
        alert(message);
    }
}

// Show Success Message
function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';

        // Hide after 5 seconds
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 5000);
    }
}

// Get User Profile
async function getUserProfile() {
    return await apiCall('/users/me');
}

// Doctor Dashboard Functions
async function getDoctorAppointments() {
    return await apiCall('/doctors/appointments');
}

async function getPatientsList() {
    return await apiCall('/doctors/patients');
}

// Patient Dashboard Functions
async function getPatientAppointments() {
    return await apiCall('/patients/appointments');
}

async function getDoctorRecommendations(patientId) {
    return await apiCall('/doctors/recommend', 'POST', { patient_id: patientId });
}

async function getMoodAnalysis(patientId) {
    return await apiCall(`/analytics/mood`, 'POST', { patient_id: patientId });
}

// Initialize dashboard based on user type
function initializeDashboard() {
    console.log('Initializing dashboard...');

    // Check if user is logged in
    if (!isLoggedIn()) {
        console.log('Not logged in, redirecting to login page');
        window.location.href = '/login';
        return;
    }

    // Get user information from localStorage
    const userType = localStorage.getItem('userType');
    const userName = localStorage.getItem('userName');
    const userRoles = localStorage.getItem('userRoles');

    console.log('User type:', userType);
    console.log('User name:', userName);
    console.log('User roles:', userRoles);

    // Update user name in the UI if available
    if (userName) {
        const userNameElements = document.querySelectorAll('#user-name');
        userNameElements.forEach(element => {
            if (userType === 'doctor') {
                element.textContent = `Dr. ${userName}`;
            } else {
                element.textContent = userName;
            }
        });
    }

    // Initialize dashboard based on user type
    if (userType === 'patient') {
        console.log('Initializing patient dashboard...');
        initializePatientDashboard();
    } else if (userType === 'doctor') {
        console.log('Initializing doctor dashboard...');
        initializeDoctorDashboard();
    } else {
        console.log('Unknown user type, redirecting to login...');
        // Unknown user type, redirect to login
        window.location.href = '/login';
    }
}

// Initialize Patient Dashboard
async function initializePatientDashboard() {
    try {
        // Get user ID from localStorage
        const userId = localStorage.getItem('userId');
        if (!userId) {
            console.error('No user ID found in localStorage');
            showError('Session information missing. Please login again.');
            setTimeout(() => { window.location.href = '/login'; }, 2000);
            return;
        }

        console.log('Initializing patient dashboard for user ID:', userId);

        try {
            // Load appointments
            console.log('Loading appointments...');
            const appointments = await getPatientAppointments();
            console.log('Appointments:', appointments);
            displayAppointments(appointments);
        } catch (e) {
            console.error('Error loading appointments:', e);
        }

        try {
            // Get user profile to get patient ID
            console.log('Getting user profile for doctor recommendations...');
            const userProfile = await getUserProfile();
            console.log('User profile:', userProfile);

            if (userProfile && userProfile.patient_id) {
                // Load doctor recommendations using patient ID
                console.log('Loading doctor recommendations for patient ID:', userProfile.patient_id);
                const recommendations = await getDoctorRecommendations(userProfile.patient_id);
                console.log('Recommendations:', recommendations);
                displayDoctorRecommendations(recommendations);
            } else {
                console.error('No patient ID found in user profile');
                showError('Could not load doctor recommendations: Patient ID not found');
            }
        } catch (e) {
            console.error('Error loading recommendations:', e);
        }

        try {
            // Get user profile to get patient ID
            console.log('Getting user profile for mood analysis...');
            const userProfile = await getUserProfile();
            console.log('User profile:', userProfile);

            if (userProfile && userProfile.patient_id) {
                // Load mood analysis using patient ID
                console.log('Loading mood analysis for patient ID:', userProfile.patient_id);
                const moodAnalysis = await getMoodAnalysis(userProfile.patient_id);
                console.log('Mood analysis:', moodAnalysis);
                displayMoodAnalysis(moodAnalysis);
            } else {
                console.error('No patient ID found in user profile');
                showError('Could not load mood analysis: Patient ID not found');
            }
        } catch (e) {
            console.error('Error loading mood analysis:', e);
        }

    } catch (error) {
        console.error('Dashboard Error:', error);
        showError('Failed to load dashboard data');
    }
}

// Initialize Doctor Dashboard
async function initializeDoctorDashboard() {
    try {
        // Get user ID from localStorage
        const userId = localStorage.getItem('userId');
        if (!userId) {
            console.error('No user ID found in localStorage');
            showError('Session information missing. Please login again.');
            setTimeout(() => { window.location.href = '/login'; }, 2000);
            return;
        }

        console.log('Initializing doctor dashboard for user ID:', userId);

        try {
            // Load appointments
            console.log('Loading doctor appointments...');
            const appointments = await getDoctorAppointments();
            console.log('Doctor appointments:', appointments);
            displayAppointments(appointments);
        } catch (e) {
            console.error('Error loading doctor appointments:', e);
        }

        try {
            // Load patients list
            console.log('Loading patients list...');
            const patients = await getPatientsList();
            console.log('Patients list:', patients);
            displayPatientsList(patients);
        } catch (e) {
            console.error('Error loading patients list:', e);
        }

    } catch (error) {
        console.error('Dashboard Error:', error);
        showError('Failed to load dashboard data');
    }
}

// Display Appointments
function displayAppointments(appointments) {
    console.log('Displaying appointments...');
    const container = document.getElementById('appointments-list');
    if (!container) {
        console.error('Appointments container not found');
        return;
    }

    // Update appointment count if element exists
    const appointmentCount = document.getElementById('appointment-count');
    if (appointmentCount) {
        appointmentCount.textContent = appointments ? appointments.length : 0;
    }

    if (!appointments || appointments.length === 0) {
        console.log('No appointments to display');
        container.innerHTML = '<p>No appointments scheduled.</p>';
        return;
    }

    console.log(`Displaying ${appointments.length} appointments`);
    let html = '';

    appointments.forEach((appointment, index) => {
        try {
            console.log(`Processing appointment ${index}:`, appointment);
            const appointmentDate = appointment.appointment_date ? new Date(appointment.appointment_date).toLocaleDateString() : 'N/A';
            const appointmentTime = appointment.appointment_time || 'N/A';
            const name = appointment.doctor_name || appointment.patient_name || 'Unknown';
            const reason = appointment.visit_reason || appointment.reason || 'General consultation';
            const status = appointment.status || 'Scheduled';

            html += `
                <div class="appointment-item">
                    <div class="appointment-date">
                        <strong>${appointmentDate}</strong>
                        <span>${appointmentTime}</span>
                    </div>
                    <div class="appointment-details">
                        <h4>${name}</h4>
                        <p>${reason}</p>
                        <span class="badge ${getStatusBadgeClass(status)}">${status}</span>
                    </div>
                </div>
            `;
        } catch (e) {
            console.error(`Error processing appointment ${index}:`, e);
        }
    });

    container.innerHTML = html;
    console.log('Appointments displayed successfully');
}

// Get CSS class for status badge
function getStatusBadgeClass(status) {
    switch (status) {
        case 'Scheduled':
            return 'badge-primary';
        case 'Completed':
            return 'badge-success';
        case 'Cancelled':
            return 'badge-danger';
        default:
            return 'badge-secondary';
    }
}

// Display Doctor Recommendations
function displayDoctorRecommendations(recommendations) {
    const container = document.getElementById('doctor-recommendations');
    if (!container) return;

    if (!recommendations || !recommendations.doctors || recommendations.doctors.length === 0) {
        container.innerHTML = '<p>No doctor recommendations available.</p>';
        return;
    }

    let html = '';
    recommendations.doctors.forEach(doctor => {
        html += `
            <div class="doctor-card">
                <div class="doctor-info">
                    <h4>Dr. ${doctor.first_name} ${doctor.last_name}</h4>
                    <p>${doctor.specialization || 'General Practitioner'}</p>
                    <p><i class="fas fa-money-bill-wave"></i> $${doctor.consultation_fee}</p>
                </div>
                <div class="doctor-actions">
                    <button class="btn btn-sm btn-primary" onclick="bookAppointment('${doctor.doctor_id}')">
                        Book Appointment
                    </button>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Display Mood Analysis
function displayMoodAnalysis(moodData) {
    const container = document.getElementById('mood-analysis');
    if (!container) return;

    if (!moodData || !moodData.mood_scores) {
        container.innerHTML = '<p>No mood data available.</p>';
        return;
    }

    let html = `
        <div class="mood-summary">
            <h4>Mood Trend: ${moodData.trend}</h4>
        </div>
        <div class="mood-recommendations">
            <h5>Recommendations:</h5>
            <ul>
    `;

    if (moodData.recommendations && moodData.recommendations.length > 0) {
        moodData.recommendations.forEach(rec => {
            html += `<li>${rec}</li>`;
        });
    } else {
        html += `<li>No recommendations available.</li>`;
    }

    html += `
            </ul>
        </div>
    `;

    container.innerHTML = html;
}

// Display Patients List
function displayPatientsList(patients) {
    console.log('Displaying patients list...');
    const container = document.getElementById('patients-list');
    if (!container) {
        console.error('Patients list container not found');
        return;
    }

    if (!patients || patients.length === 0) {
        console.log('No patients to display');
        container.innerHTML = '<p>No patients assigned.</p>';
        return;
    }

    console.log(`Displaying ${patients.length} patients`);
    let html = '';

    patients.forEach((patient, index) => {
        try {
            console.log(`Processing patient ${index}:`, patient);
            const age = patient.age || 'N/A';
            const treatment = patient.treatment || 'N/A';

            html += `
                <div class="patient-card">
                    <div class="patient-info">
                        <h4>${patient.first_name} ${patient.last_name}</h4>
                        <p>Age: ${age}</p>
                        <p>Treatment: ${treatment}</p>
                    </div>
                    <div class="patient-actions">
                        <button class="btn btn-sm btn-primary" onclick="viewPatientDetails('${patient.patient_id}')">
                            View Details
                        </button>
                    </div>
                </div>
            `;
        } catch (e) {
            console.error(`Error processing patient ${index}:`, e);
        }
    });

    container.innerHTML = html;
    console.log('Patients list displayed successfully');
}

// Book Appointment Function
function bookAppointment(doctorId) {
    // Redirect to appointment booking page with doctor ID
    window.location.href = `/book_appointment.html?doctor=${doctorId}`;
}

// View Patient Details Function
function viewPatientDetails(patientId) {
    // Redirect to patient details page
    window.location.href = `/patient_details.html?id=${patientId}`;
}

// Document Ready Function
document.addEventListener('DOMContentLoaded', function() {
    // Check if logout button exists and attach event
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Check if on dashboard page
    const dashboardContainer = document.querySelector('.dashboard-container');
    if (dashboardContainer) {
        requireAuth();
        initializeDashboard();
    }

    // Check if on login page and attach form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const userType = document.querySelector('input[name="user-type"]:checked').value;

            login(email, password, userType);
        });
    }
});

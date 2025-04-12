// Doctor Filter Functionality

// Global variables
let patientId = null;
let currentFilters = {};

// Add event listener when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Doctor filters: DOM loaded, checking for filter button...');
    const filterBtn = document.getElementById('filter-doctors-btn');

    if (filterBtn) {
        console.log('Filter button found, attaching direct event listener');
        filterBtn.addEventListener('click', function() {
            toggleFilterPanel();
        });
    } else {
        console.error('Filter button not found on DOM load');
    }
});

// Toggle filter panel function
function toggleFilterPanel() {
    console.log('Toggle filter panel called');
    const filterPanel = document.getElementById('doctor-filter-panel');
    const filterBtn = document.getElementById('filter-doctors-btn');

    if (!filterPanel || !filterBtn) {
        console.error('Filter panel or button not found');
        return;
    }

    // Check computed style to handle both inline and CSS display properties
    const computedStyle = window.getComputedStyle(filterPanel);
    const isHidden = computedStyle.display === 'none';

    if (isHidden) {
        filterPanel.style.display = 'block';
        filterBtn.classList.add('active');
        console.log('Filter panel shown');
    } else {
        filterPanel.style.display = 'none';
        filterBtn.classList.remove('active');
        console.log('Filter panel hidden');
    }
}

// Initialize doctor filters
function initializeDoctorFilters() {
    console.log('Initializing doctor filters...');

    // Get filter elements
    const filterPanel = document.getElementById('doctor-filter-panel');
    const applyFiltersBtn = document.getElementById('apply-filters-btn');
    const resetFiltersBtn = document.getElementById('reset-filters-btn');

    if (!filterPanel || !applyFiltersBtn || !resetFiltersBtn) {
        console.error('Filter elements not found');
        return;
    }

    // Make sure filter panel is initially hidden with inline style
    filterPanel.style.display = 'none';

    // Apply filters - using onclick to avoid duplicate listeners
    applyFiltersBtn.onclick = function() {
        applyDoctorFilters();
    };

    // Reset filters - using onclick to avoid duplicate listeners
    resetFiltersBtn.onclick = function() {
        resetDoctorFilters();
    };

    console.log('Doctor filters initialized');
}

// Get filter values
function getFilterValues() {
    const specialization = document.getElementById('filter-specialization').value;
    const language = document.getElementById('filter-language').value;
    const gender = document.getElementById('filter-gender').value;
    const region = document.getElementById('filter-region').value;
    const day = document.getElementById('filter-day').value;
    const time = document.getElementById('filter-time').value;

    // Build filters object
    const filters = {};

    if (specialization) filters.specialization = specialization;
    if (language) filters.language = language;
    if (gender) filters.gender = gender;
    if (region) filters.region = region;

    // Add availability if day or time is specified
    if (day || time) {
        filters.availability = {};
        if (day) filters.availability.day = day;
        if (time) filters.availability.start_time = time;
    }

    return filters;
}

// Apply doctor filters
async function applyDoctorFilters() {
    try {
        if (!patientId) {
            console.error('Patient ID not available');
            showError('Unable to apply filters: Patient ID not available');
            return;
        }

        // Get filter values
        currentFilters = getFilterValues();
        console.log('Applying filters:', currentFilters);

        // Show loading state
        const container = document.getElementById('doctor-recommendations');
        if (container) {
            container.innerHTML = '<p class="text-center text-muted">Loading filtered recommendations...</p>';
        }

        // Call API with filters
        const recommendations = await getFilteredDoctorRecommendations(patientId, currentFilters);
        console.log('Filtered recommendations:', recommendations);

        // Display recommendations
        displayDoctorRecommendations(recommendations);

        // Hide filter panel
        const filterPanel = document.getElementById('doctor-filter-panel');
        if (filterPanel) {
            filterPanel.style.display = 'none';
        }

        // Update filter button to show active filters
        updateFilterButtonState();

    } catch (error) {
        console.error('Error applying filters:', error);
        showError('Failed to apply filters: ' + error.message);
    }
}

// Reset doctor filters
async function resetDoctorFilters() {
    try {
        // Reset filter form
        document.getElementById('filter-specialization').value = '';
        document.getElementById('filter-language').value = '';
        document.getElementById('filter-gender').value = '';
        document.getElementById('filter-region').value = '';
        document.getElementById('filter-day').value = '';
        document.getElementById('filter-time').value = '';

        // Clear current filters
        currentFilters = {};

        // Update recommendations without filters
        if (patientId) {
            const recommendations = await getFilteredDoctorRecommendations(patientId, null);
            displayDoctorRecommendations(recommendations);
        }

        // Update filter button state
        updateFilterButtonState();

    } catch (error) {
        console.error('Error resetting filters:', error);
        showError('Failed to reset filters: ' + error.message);
    }
}

// Update filter button state to show active filters
function updateFilterButtonState() {
    const filterBtn = document.getElementById('filter-doctors-btn');
    if (!filterBtn) return;

    const filterCount = Object.keys(currentFilters).length;

    if (filterCount > 0) {
        filterBtn.innerHTML = `<i class="fas fa-filter me-1"></i>Filters (${filterCount})`;
        filterBtn.classList.add('btn-primary');
        filterBtn.classList.remove('btn-outline-primary');
    } else {
        filterBtn.innerHTML = `<i class="fas fa-filter me-1"></i>Filter`;
        filterBtn.classList.add('btn-outline-primary');
        filterBtn.classList.remove('btn-primary');
    }
}

// Get filtered doctor recommendations
async function getFilteredDoctorRecommendations(patientId, filters) {
    try {
        // Prepare request body
        const requestBody = {
            patient_id: patientId,
            filters: filters
        };

        // Call the recommendations API
        return await apiCall('/recommendations/doctors', 'POST', requestBody);
    } catch (error) {
        console.error('Error getting filtered recommendations:', error);
        throw error;
    }
}

// Set patient ID for filters
function setPatientIdForFilters(id) {
    patientId = id;
    console.log('Patient ID set for filters:', patientId);
}

// Enhanced doctor recommendations display
function displayEnhancedDoctorRecommendations(recommendations) {
    const container = document.getElementById('doctor-recommendations');
    if (!container) return;

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="text-center">No doctor recommendations available.</p>';
        return;
    }

    console.log('Doctor recommendations:', recommendations);

    let html = '';
    recommendations.forEach((doctor, index) => {
        // Log each doctor object for debugging
        console.log(`Doctor ${index + 1}:`, doctor);
        console.log(`Doctor ${index + 1} availability:`, doctor.availability);
        // Ensure we have valid data for each field
        const doctorName = doctor.name ||
            (doctor.first_name && doctor.last_name ? `Dr. ${doctor.first_name} ${doctor.last_name}` : 'Doctor');
        const specialization = doctor.specialization || 'General Practitioner';
        const language = doctor.language || 'Not specified';
        const gender = doctor.gender || 'Not specified';
        const fee = doctor.consultation_fee ? `$${doctor.consultation_fee}` : 'Not specified';
        const rating = doctor.average_rating && doctor.average_rating !== 'N/A' ?
            `<div class="doctor-rating"><i class="fas fa-star me-1"></i>${doctor.average_rating}/5</div>` :
            '<div class="doctor-rating text-muted"><i class="far fa-star me-1"></i>No ratings yet</div>';

        // Format availability
        let availabilityHtml = '<div class="doctor-availability mt-2"><i class="fas fa-clock me-1"></i>';

        if (doctor.availability && doctor.availability.length > 0) {
            // Log availability data for debugging
            console.log('Doctor availability data:', doctor.availability);

            const availabilityItems = doctor.availability.map(a => {
                // Check if day_of_week exists, otherwise check for day
                const day = a.day_of_week || a.day || 'Any day';

                // Format the time strings properly
                let startTime = '00:00';
                let endTime = '00:00';

                if (a.start_time) {
                    // Handle both string and Date object formats
                    if (typeof a.start_time === 'string') {
                        // If it's already a string like "09:00", use it directly
                        startTime = a.start_time.includes('T') ?
                            a.start_time.split('T')[1].substring(0, 5) : a.start_time;
                    } else {
                        // If it's a Date object, format it
                        const date = new Date(a.start_time);
                        startTime = date.getHours().toString().padStart(2, '0') + ':' +
                                   date.getMinutes().toString().padStart(2, '0');
                    }
                }

                if (a.end_time) {
                    // Handle both string and Date object formats
                    if (typeof a.end_time === 'string') {
                        // If it's already a string like "17:00", use it directly
                        endTime = a.end_time.includes('T') ?
                            a.end_time.split('T')[1].substring(0, 5) : a.end_time;
                    } else {
                        // If it's a Date object, format it
                        const date = new Date(a.end_time);
                        endTime = date.getHours().toString().padStart(2, '0') + ':' +
                                 date.getMinutes().toString().padStart(2, '0');
                    }
                }

                return `${day} ${startTime}-${endTime}`;
            }).slice(0, 2);

            if (doctor.availability.length > 2) {
                availabilityHtml += availabilityItems.join(', ') + ' +' + (doctor.availability.length - 2) + ' more';
            } else {
                availabilityHtml += availabilityItems.join(', ');
            }
        } else {
            availabilityHtml += 'Schedule not available';
        }

        availabilityHtml += '</div>';

        // Format badges
        const badges = `
            <span class="badge bg-info">${language}</span>
            <span class="badge bg-secondary">${gender}</span>
        `;

        html += `
            <div class="doctor-card">
                <div class="doctor-info">
                    <h4>${doctorName}</h4>
                    <p>${specialization}</p>
                    <div class="mb-2">${badges}</div>
                    ${rating}
                    <p><i class="fas fa-money-bill-wave me-1"></i> ${fee}</p>
                    ${availabilityHtml}
                </div>
                <div class="doctor-actions">
                    <button class="btn btn-sm btn-primary mb-2" onclick="bookAppointment('${doctor.doctor_id}')">
                        Book Appointment
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="viewDoctorProfile('${doctor.doctor_id}')">
                        View Profile
                    </button>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Function to view doctor profile (placeholder)
function viewDoctorProfile(doctorId) {
    console.log('View doctor profile:', doctorId);
    showInfo('Doctor profile feature coming soon!');
}

// API endpoints
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const meetingForm = document.getElementById('meeting-form');
const summaryForm = document.getElementById('summary-form');
const scheduleResult = document.getElementById('schedule-result');
const summaryResult = document.getElementById('summary-result');

// Helper Functions
function showResult(element, message, isError = false, details = null) {
    let fullMessage = message;
    if (details) {
        if (details.event_link) {
            fullMessage += `\nView meeting: ${details.event_link}`;
        }
        if (details.attendees && details.attendees.length > 0) {
            fullMessage += `\nInvitations sent to: ${details.attendees.join(', ')}`;
        }
    }
    element.textContent = fullMessage;
    element.className = `result ${isError ? 'error' : 'success'}`;
    element.style.display = 'block';
    
    // Add show class after a small delay to trigger animation
    setTimeout(() => {
        element.classList.add('show');
    }, 10);
}

function clearResult(element) {
    element.textContent = '';
    element.className = 'result';
    element.style.display = 'none';
    element.classList.remove('show');
}

function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    return date.toISOString().slice(0, 16); // Format: YYYY-MM-DDTHH:mm
}

function setLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = '<span class="loading"></span>Processing...';
    } else {
        button.disabled = false;
        button.innerHTML = button.getAttribute('data-original-text') || 'Submit';
    }
}

// Event Listeners
meetingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearResult(scheduleResult);

    const submitButton = meetingForm.querySelector('button[type="submit"]');
    submitButton.setAttribute('data-original-text', submitButton.innerHTML);
    setLoading(submitButton, true);

    const formData = new FormData(meetingForm);
    const participants = formData.get('participants')
        .split('\n')
        .map(email => email.trim())
        .filter(email => email);

    const meetingData = {
        title: formData.get('title'),
        description: formData.get('description'),
        start_time: formData.get('start-time'),
        end_time: formData.get('end-time'),
        participants: participants
    };

    try {
        const response = await fetch(`${API_BASE_URL}/schedule-meeting`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(meetingData)
        });

        const data = await response.json();

        if (response.ok) {
            if (data.auth_required) {
                // Redirect to Google OAuth
                window.location.href = data.auth_url;
                return;
            }
            showResult(scheduleResult, data.message, false, data);
            meetingForm.reset();
        } else {
            showResult(scheduleResult, data.detail || 'Failed to schedule meeting', true);
        }
    } catch (error) {
        showResult(scheduleResult, 'Error connecting to the server', true);
        console.error('Error:', error);
    } finally {
        setLoading(submitButton, false);
    }
});

summaryForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearResult(summaryResult);

    const submitButton = summaryForm.querySelector('button[type="submit"]');
    submitButton.setAttribute('data-original-text', submitButton.innerHTML);
    setLoading(submitButton, true);

    const formData = new FormData(summaryForm);
    const transcript = formData.get('transcript');

    try {
        const response = await fetch(`${API_BASE_URL}/generate-summary`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ transcript })
        });

        const data = await response.json();

        if (response.ok) {
            showResult(summaryResult, data.summary);
        } else {
            showResult(summaryResult, data.detail || 'Failed to generate summary', true);
        }
    } catch (error) {
        showResult(summaryResult, 'Error connecting to the server', true);
        console.error('Error:', error);
    } finally {
        setLoading(submitButton, false);
    }
});

// Initialize datetime-local inputs with current time
document.addEventListener('DOMContentLoaded', () => {
    const now = new Date();
    const startTime = document.getElementById('start-time');
    const endTime = document.getElementById('end-time');

    // Set start time to current time
    startTime.value = formatDateTime(now);

    // Set end time to current time + 1 hour
    const endDateTime = new Date(now.getTime() + 60 * 60 * 1000);
    endTime.value = formatDateTime(endDateTime);
    
    // Add animation to form elements when they come into view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.form-group').forEach(el => {
        observer.observe(el);
    });
}); 
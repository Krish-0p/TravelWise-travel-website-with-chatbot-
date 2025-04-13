/**
 * Main JavaScript file for TravelWise website
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers with current date + 1 day and current date + 8 days
    initDatePickers();
    
    // Initialize any tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add event listeners to all search forms
    initSearchForms();
});

/**
 * Initialize date pickers with default dates
 */
function initDatePickers() {
    const today = new Date();
    
    // Tomorrow's date for check-in/departure
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    // Next week for check-out/return
    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 8);
    
    // Format dates to YYYY-MM-DD
    const tomorrowFormatted = formatDate(tomorrow);
    const nextWeekFormatted = formatDate(nextWeek);
    
    // Set default values for date inputs
    const checkInInputs = document.querySelectorAll('#check-in, #departure-date');
    const checkOutInputs = document.querySelectorAll('#check-out, #return-date');
    
    checkInInputs.forEach(input => {
        if (input) {
            input.value = tomorrowFormatted;
            input.min = tomorrowFormatted;
        }
    });
    
    checkOutInputs.forEach(input => {
        if (input) {
            input.value = nextWeekFormatted;
            input.min = tomorrowFormatted;
        }
    });
}

/**
 * Format date to YYYY-MM-DD string
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Initialize search form event listeners
 */
function initSearchForms() {
    const searchForms = document.querySelectorAll('form');
    
    searchForms.forEach(form => {
        const searchButton = form.querySelector('button[type="button"]');
        if (searchButton) {
            searchButton.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get search parameters
                const formData = new FormData(form);
                let searchParams = {};
                
                for (let [key, value] of formData.entries()) {
                    if (value) {
                        searchParams[key] = value;
                    }
                }
                
                // Here you would typically submit the form or redirect
                // For now, just show an alert with the search parameters
                alert('Search feature will be implemented in the next phase. Parameters: ' + JSON.stringify(searchParams));
            });
        }
    });
}

/**
 * Smooth scroll to element
 */
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

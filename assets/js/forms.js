// Form handling functionality

domReady(() => {
    const contactForm = document.getElementById('contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', handleFormSubmit);
    }
});

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    // Get form values
    const data = {
        name: formData.get('name'),
        email: formData.get('email'),
        role: formData.get('role'),
        message: formData.get('message')
    };
    
    // Set loading state
    window.DRIP.setButtonLoading(submitButton, true);
    
    try {
        // For now, we'll use a mailto link as a fallback
        // In production, this would send to a backend endpoint
        const subject = `DRIP Team Application - ${data.role}`;
        const body = `Name: ${data.name}
Email: ${data.email}
Position: ${data.role}

Message:
${data.message}`;
        
        // Create mailto link
        const mailtoLink = `mailto:drip-team@stanford.edu?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
        
        // Open email client
        window.location.href = mailtoLink;
        
        // Show success message
        showFormMessage('success', 'Thank you for your interest! Please complete sending the email in your email client.');
        
        // Reset form
        form.reset();
        
    } catch (error) {
        console.error('Form submission error:', error);
        showFormMessage('error', 'There was an error submitting the form. Please try again or email us directly.');
    } finally {
        // Reset button state
        window.DRIP.setButtonLoading(submitButton, false);
    }
}

function showFormMessage(type, message) {
    const form = document.getElementById('contact-form');
    
    // Remove existing messages
    const existingMessage = form.parentElement.querySelector('.form-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `form-message form-message--${type}`;
    messageDiv.textContent = message;
    
    // Insert after form
    form.parentElement.insertBefore(messageDiv, form.nextSibling);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 300);
    }, 5000);
}

// Add form message styles
const formStyles = `
<style>
.form-message {
    margin-top: var(--space-md);
    padding: var(--space-md);
    border-radius: var(--radius-md);
    text-align: center;
    transition: opacity var(--transition-base);
}

.form-message--success {
    background-color: rgba(39, 174, 96, 0.1);
    border: 1px solid var(--success-green);
    color: var(--success-green);
}

.form-message--error {
    background-color: rgba(231, 76, 60, 0.1);
    border: 1px solid var(--error-red);
    color: var(--error-red);
}

/* Loading state for buttons */
.btn.loading {
    opacity: 0.7;
    cursor: not-allowed;
}

/* Form validation styles */
.contact-form input:invalid:not(:focus),
.contact-form select:invalid:not(:focus),
.contact-form textarea:invalid:not(:focus) {
    border-color: var(--error-red);
}

.contact-form input:valid:not(:focus),
.contact-form select:valid:not(:focus),
.contact-form textarea:valid:not(:focus) {
    border-color: var(--success-green);
}

/* Optional: Add a floating label effect */
.contact-form input:focus::placeholder,
.contact-form select:focus::placeholder,
.contact-form textarea:focus::placeholder {
    opacity: 0.5;
}
</style>`;

// Inject form-specific styles
if (!document.querySelector('#form-styles')) {
    const styleTag = document.createElement('div');
    styleTag.id = 'form-styles';
    styleTag.innerHTML = formStyles;
    document.head.appendChild(styleTag.firstElementChild);
}

// Optional: Add form field validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Optional: Add real-time validation
const emailInput = document.querySelector('input[type="email"]');
if (emailInput) {
    emailInput.addEventListener('blur', function() {
        if (this.value && !validateEmail(this.value)) {
            this.setCustomValidity('Please enter a valid email address');
        } else {
            this.setCustomValidity('');
        }
    });
}
// Team page functionality

domReady(() => {
    const modal = document.getElementById('team-modal');
    const modalClose = modal.querySelector('.modal__close');
    const teamCards = document.querySelectorAll('.team-card');
    
    // Load team data
    loadTeamData();
    
    // Modal close functionality
    modalClose.addEventListener('click', closeModal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Close modal with escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('modal--open')) {
            closeModal();
        }
    });
    
    // Team card click handlers
    teamCards.forEach(card => {
        card.addEventListener('click', () => {
            const memberId = card.dataset.memberId;
            openModal(memberId);
        });
    });
});

// Load team data from JSON
async function loadTeamData() {
    const data = await window.DRIP.loadData('team.json');
    if (!data) return;
    
    // Update team grid with current members
    if (data.current && data.current.length > 0) {
        const teamGrid = document.getElementById('team-grid');
        const currentMembersHTML = data.current.map((member, index) => `
            <div class="team-card reveal stagger-${index + 1}" data-member-id="${member.id}">
                <div class="team-card__photo">
                    ${member.photo ? 
                        `<img src="${member.photo}" alt="${member.name}">` : 
                        `<div class="team-placeholder">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                        </div>`
                    }
                    <div class="role-badge">${member.badge || member.role}</div>
                </div>
                <div class="team-card__content">
                    <h3 class="team-card__name">${member.name}</h3>
                    <p class="team-card__title">${member.role}</p>
                </div>
            </div>
        `).join('');
        
        // Check if team grid already has content (from HTML)
        if (teamGrid.children.length === 0) {
            // Only add members if grid is empty
            teamGrid.innerHTML = currentMembersHTML;
        }
        
        // Re-attach click handlers to all cards
        document.querySelectorAll('.team-card').forEach(card => {
            card.addEventListener('click', () => {
                const memberId = card.dataset.memberId;
                openModal(memberId, data.current);
            });
        });
    }
}

// Open modal with member data
async function openModal(memberId, teamData = null) {
    const modal = document.getElementById('team-modal');
    
    // If we don't have team data, try to load it
    if (!teamData) {
        const data = await window.DRIP.loadData('team.json');
        teamData = data?.current || [];
    }
    
    // Find member data
    const member = teamData.find(m => m.id === memberId);
    
    if (member) {
        updateModal(member);
    }
    
    // Open modal
    modal.classList.add('modal--open');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

// Update modal content
function updateModal(member) {
    const modal = document.getElementById('team-modal');
    
    // Update photo
    const modalPhoto = modal.querySelector('.modal__photo');
    if (member.photo) {
        modalPhoto.src = member.photo;
        modalPhoto.alt = member.name;
        modalPhoto.style.display = 'block';
    } else {
        modalPhoto.style.display = 'none';
    }
    
    // Update basic info
    modal.querySelector('.modal__name').textContent = member.name;
    modal.querySelector('.modal__role').textContent = member.role;
    
    // Update bio
    const bioParagraph = modal.querySelector('.modal__bio');
    bioParagraph.textContent = member.bio?.full || 'No biography available.';
    
    // Update responsibilities
    const respList = modal.querySelector('.modal__responsibilities');
    if (member.bio?.responsibilities) {
        respList.innerHTML = member.bio.responsibilities
            .map(resp => `<li>${resp}</li>`)
            .join('');
    } else {
        respList.innerHTML = '<li>No responsibilities listed</li>';
    }
    
    // Update expertise
    const expertiseList = modal.querySelector('.modal__expertise');
    if (member.bio?.expertise) {
        expertiseList.innerHTML = member.bio.expertise
            .map(exp => `<li>${exp}</li>`)
            .join('');
    } else {
        expertiseList.innerHTML = '<li>No expertise listed</li>';
    }
    
    // Update contact link
    const contactBtn = modal.querySelector('.modal__contact');
    if (member.social?.email) {
        contactBtn.href = `mailto:${member.social.email}`;
        contactBtn.textContent = 'Contact';
        contactBtn.style.display = 'inline-flex';
        
        // Remove any existing click listeners
        contactBtn.replaceWith(contactBtn.cloneNode(true));
        const newContactBtn = modal.querySelector('.modal__contact');
        
        // Add click handler for better email client support
        newContactBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = `mailto:${member.social.email}`;
        });
    } else {
        contactBtn.style.display = 'none';
    }
}

// Close modal
function closeModal() {
    const modal = document.getElementById('team-modal');
    modal.classList.remove('modal--open');
    document.body.style.overflow = ''; // Restore scrolling
}
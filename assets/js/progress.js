// Progress page functionality

domReady(() => {
    // Phase accordion functionality
    const phases = document.querySelectorAll('.phase');
    
    phases.forEach(phase => {
        const header = phase.querySelector('.phase__header');
        const content = phase.querySelector('.phase__content');
        
        // Set initial state
        if (phase.classList.contains('phase--complete')) {
            phase.classList.add('phase--expanded');
        }
        
        header.addEventListener('click', () => {
            // Toggle expanded state
            phase.classList.toggle('phase--expanded');
            
            // Update aria attributes for accessibility
            const isExpanded = phase.classList.contains('phase--expanded');
            header.setAttribute('aria-expanded', isExpanded);
            content.setAttribute('aria-hidden', !isExpanded);
        });
    });
    
    // Load milestone data if available
    loadMilestoneData();
    
    // Animate progress bars when in viewport
    const progressBars = document.querySelectorAll('.progress-bar');
    const progressObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const fill = entry.target.querySelector('.progress-bar__fill');
                if (fill && fill.classList.contains('progress-bar__fill--animated')) {
                    // Trigger animation by adding a class
                    fill.style.width = fill.style.getPropertyValue('--progress-width');
                }
                progressObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    progressBars.forEach(bar => progressObserver.observe(bar));
});

// Load milestone data from JSON
async function loadMilestoneData() {
    const data = await window.DRIP.loadData('milestones.json');
    if (!data) return;
    
    // Update phases with loaded data
    if (data.phases) {
        data.phases.forEach(phaseData => {
            const phaseElement = document.querySelector(`[data-phase="${phaseData.id.split('-')[1]}"]`);
            if (!phaseElement) return;
            
            // Update phase status
            if (phaseData.status === 'complete') {
                phaseElement.classList.add('phase--complete');
                phaseElement.querySelector('.phase__icon').textContent = '✓';
            }
            
            // Update dates if available
            if (phaseData.startDate && phaseData.endDate) {
                const dateElement = phaseElement.querySelector('.phase__date');
                if (dateElement) {
                    const start = new Date(phaseData.startDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    const end = new Date(phaseData.endDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                    dateElement.textContent = `${start} - ${end}`;
                }
            }
            
            // Update milestones
            if (phaseData.milestones && phaseData.milestones.length > 0) {
                const milestonesContainer = phaseElement.querySelector('.phase__milestones');
                if (milestonesContainer) {
                    milestonesContainer.innerHTML = phaseData.milestones.map(milestone => `
                        <div class="milestone ${milestone.status === 'complete' ? 'milestone--complete' : ''}">
                            <h4>${milestone.title}</h4>
                            <p>${milestone.description}</p>
                        </div>
                    `).join('');
                }
            }
        });
    }
    
    // Update subsystem progress
    if (data.subsystems) {
        data.subsystems.forEach(subsystem => {
            const progressBar = Array.from(document.querySelectorAll('.progress-bar')).find(bar => 
                bar.querySelector('.progress-bar__label span').textContent === subsystem.name
            );
            
            if (progressBar) {
                const percentElement = progressBar.querySelector('.progress-bar__percent');
                const fillElement = progressBar.querySelector('.progress-bar__fill');
                
                if (percentElement) percentElement.textContent = `${subsystem.progress}%`;
                if (fillElement) {
                    fillElement.style.setProperty('--progress-width', `${subsystem.progress}%`);
                }
            }
        });
    }
    
    // Update last updated timestamp
    if (data.lastUpdated) {
        const lastUpdatedElement = document.querySelector('.text-muted');
        if (lastUpdatedElement) {
            const date = new Date(data.lastUpdated).toLocaleDateString('en-US', { 
                month: 'long', 
                day: 'numeric', 
                year: 'numeric' 
            });
            lastUpdatedElement.textContent = `Last updated: ${date}`;
        }
    }
}

// Add milestone card styles
const milestoneStyles = `
<style>
.milestone-card {
    background-color: white;
    border-radius: var(--radius-lg);
    padding: var(--space-xl);
    box-shadow: var(--shadow-sm);
    border-left: 4px solid var(--acoustic-blue);
    transition: all var(--transition-base);
    margin-bottom: var(--space-md);
}

.milestone-card:hover {
    transform: translateX(5px);
    box-shadow: var(--shadow-md);
}

.milestone-card__date {
    font-size: var(--text-sm);
    color: var(--acoustic-blue);
    font-weight: 600;
    margin-bottom: var(--space-xs);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.milestone-card h3 {
    font-size: var(--text-xl);
    margin-bottom: var(--space-sm);
    color: var(--steel-dark);
}

.milestone-card p {
    color: var(--aluminum-silver);
    margin: 0;
}

.text-muted {
    color: var(--aluminum-silver);
}

/* Enhance phase interactions */
.phase__header {
    user-select: none;
}

.phase__header::after {
    content: '▼';
    margin-left: auto;
    transition: transform var(--transition-base);
    opacity: 0.5;
}

.phase--expanded .phase__header::after {
    transform: rotate(180deg);
}

.phase__date {
    font-size: var(--text-sm);
    color: var(--aluminum-silver);
    margin-left: auto;
    margin-right: var(--space-md);
}
</style>`;

// Inject progress-specific styles
if (!document.querySelector('#progress-styles')) {
    const styleTag = document.createElement('div');
    styleTag.id = 'progress-styles';
    styleTag.innerHTML = milestoneStyles;
    document.head.appendChild(styleTag.firstElementChild);
}
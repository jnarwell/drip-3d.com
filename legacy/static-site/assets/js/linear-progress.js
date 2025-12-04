class LinearProgressManager {
    constructor() {
        this.progressData = null;
        this.teamData = null;
        this.initialized = false;
        this.emailToNameMap = {};
    }

    async init() {
        try {
            await this.loadTeamData();
            await this.loadProgressData();
            this.updateProgressPage();
            this.initialized = true;
        } catch (error) {
            console.error('Failed to initialize Linear progress:', error);
            // Fall back to static content
        }
    }

    async loadTeamData() {
        try {
            const response = await fetch('data/team.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.teamData = await response.json();
            
            // Create email-to-name mapping
            this.emailToNameMap = {};
            if (this.teamData && this.teamData.current) {
                this.teamData.current.forEach(member => {
                    if (member.social && member.social.email) {
                        this.emailToNameMap[member.social.email] = member.name;
                        // Also map the email without @drip-3d.com suffix for Linear data
                        const emailPrefix = member.social.email.replace('@drip-3d.com', '');
                        this.emailToNameMap[emailPrefix] = member.name;
                    }
                });
            }
            
            // Add specific mappings for Linear data
            this.emailToNameMap['ryos17@stanford.edu'] = 'Ryota Sato';
            this.emailToNameMap['pierce@drip-3d.com'] = 'Pierce Thompson';
            this.emailToNameMap['jamie@drip-3d.com'] = 'Jamie Marwell';
            
        } catch (error) {
            console.error('Failed to load team data:', error);
            // Continue without team data
        }
    }

    async loadProgressData() {
        try {
            const response = await fetch('assets/data/progress.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.progressData = await response.json();
        } catch (error) {
            console.error('Failed to load progress data:', error);
            throw error;
        }
    }

    updateProgressPage() {
        if (!this.progressData || !this.progressData.phases) {
            return;
        }

        this.updatePhases();
        this.updateLastUpdated();
        this.updateUpcomingMilestones();
    }

    updatePhases() {
        const phaseContainer = document.querySelector('.phase-checklist');
        if (!phaseContainer) return;

        // Clear existing phases (except the title and controls)
        const existingPhases = phaseContainer.querySelectorAll('.phase');
        existingPhases.forEach(phase => phase.remove());

        // Sort phases by phase number (Linear returns them in reverse order)
        const sortedPhases = [...this.progressData.phases].sort((a, b) => {
            const aNum = this.extractPhaseNumber(a.title);
            const bNum = this.extractPhaseNumber(b.title);
            return aNum - bNum;
        });

        sortedPhases.forEach((phase, index) => {
            const phaseElement = this.createPhaseElement(phase, index + 1);
            phaseElement.style.display = 'block';
            phaseElement.style.opacity = '1';
            phaseContainer.appendChild(phaseElement);
            
            // Re-add click functionality for expand/collapse
            const header = phaseElement.querySelector('.phase__header');
            const content = phaseElement.querySelector('.phase__content');
            
            if (header && content) {
                header.addEventListener('click', () => {
                    phaseElement.classList.toggle('phase--expanded');
                    const isExpanded = phaseElement.classList.contains('phase--expanded');
                    header.setAttribute('aria-expanded', isExpanded);
                    content.setAttribute('aria-hidden', !isExpanded);
                });
                
                // Start collapsed by default
                phaseElement.classList.remove('phase--expanded');
            }
        });
    }

    extractPhaseNumber(title) {
        const match = title.match(/Phase (\d+)/);
        return match ? parseInt(match[1]) : 999;
    }

    getFullName(nameOrEmail) {
        if (!nameOrEmail) return null;
        
        // If it's already a full name (contains space), return it
        if (nameOrEmail.includes(' ')) {
            return nameOrEmail;
        }
        
        // Try to map email to full name
        const fullName = this.emailToNameMap[nameOrEmail];
        if (fullName) {
            return fullName;
        }
        
        // If no mapping found, return the original
        return nameOrEmail;
    }

    addWeekToDate(dateString) {
        const date = new Date(dateString);
        date.setDate(date.getDate() + 7);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    createPhaseElement(phase, displayPhase) {
        const phaseDiv = document.createElement('div');
        phaseDiv.className = 'phase reveal';
        phaseDiv.setAttribute('data-phase', displayPhase);

        const phaseNumber = this.extractPhaseNumber(phase.title);
        const isActive = phase.projects.length > 0;
        const completedProjects = phase.projects.filter(p => p.progress >= 1).length;
        const totalProjects = phase.projects.length;

        phaseDiv.innerHTML = `
            <div class="phase__header" style="position: relative;">
                <div class="phase__title">
                    <span class="phase__icon">${phaseNumber}</span>
                    <span>${phase.title.replace(/^Phase \d+ - /, '')}</span>
                </div>
                <div class="phase__date" style="position: absolute; right: 3rem; top: 50%; transform: translateY(-50%);">Target: ${phase.targetDate}</div>
            </div>
            <div class="phase__content">
                ${phase.description ? `<p class="phase__description">${phase.description}</p>` : ''}
                ${totalProjects > 0 ? `
                    <div class="phase__progress">
                        <div class="progress-summary">
                            <span>Progress: ${completedProjects}/${totalProjects} projects completed</span>
                            <span class="progress-percent">${Math.round((completedProjects / totalProjects) * 100)}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-bar__track">
                                <div class="progress-bar__fill" style="width: ${(completedProjects / totalProjects) * 100}%"></div>
                            </div>
                        </div>
                    </div>
                    <div class="phase__projects">
                        <h4>Projects:</h4>
                        ${phase.projects.map(project => this.createProjectHtml(project)).join('')}
                    </div>
                ` : `
                    <div class="phase__status">
                        <p><em>Projects will be added to this phase soon.</em></p>
                    </div>
                `}
            </div>
        `;

        return phaseDiv;
    }

    createProjectHtml(project) {
        const progressPercent = Math.round(project.progress * 100);
        const isCompleted = project.progress >= 1;
        const statusClass = isCompleted ? 'project--completed' : 'project--in-progress';

        return `
            <div class="project ${statusClass}">
                <div class="project__header">
                    <h5>${project.name}</h5>
                    <span class="project__progress">${progressPercent}%</span>
                </div>
                <p class="project__description">${project.description || ''}</p>
                <div class="project__meta">
                    <span class="project__due">Due: ${project.targetDate}</span>
                    ${project.lead ? `<span class="project__lead">Lead: ${this.getFullName(project.lead.name)}</span>` : ''}
                </div>
                <div class="project__progress-bar">
                    <div class="progress-bar__track">
                        <div class="progress-bar__fill" style="width: ${progressPercent}%"></div>
                    </div>
                </div>
            </div>
        `;
    }

    updateUpcomingMilestones() {
        // Get next 3 upcoming project completion milestones (excluding Team Setup)
        const allProjects = this.progressData.phases
            .flatMap(phase => phase.projects)
            .filter(project => 
                project.progress < 1 && 
                !project.name.toLowerCase().includes('team setup')
            )
            .sort((a, b) => new Date(a.targetDate) - new Date(b.targetDate))
            .slice(0, 3);

        const milestonesContainer = document.querySelector('.grid--1');
        if (!milestonesContainer || !allProjects.length) return;

        milestonesContainer.innerHTML = allProjects.map(project => `
            <div class="milestone-card reveal" style="display: block; opacity: 1;">
                <div class="milestone-card__date">${this.addWeekToDate(project.targetDate)}</div>
                <h3>${project.name} Completion</h3>
                <p>Milestone celebrating the completion of ${project.name.toLowerCase()}</p>
                <div class="milestone-card__progress">
                    <span>Currently ${Math.round(project.progress * 100)}% complete</span>
                    ${project.lead ? `<span class="milestone-card__lead">Lead: ${this.getFullName(project.lead.name)}</span>` : ''}
                </div>
            </div>
        `).join('');
    }

    updateLastUpdated() {
        const lastUpdatedElement = document.querySelector('.text-muted');
        if (lastUpdatedElement && this.progressData.lastUpdated) {
            const date = new Date(this.progressData.lastUpdated);
            lastUpdatedElement.textContent = `Last updated: ${date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            })}`;
        }
    }

    // Method to refresh data (can be called periodically or on demand)
    async refresh() {
        await this.loadProgressData();
        this.updateProgressPage();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const progressManager = new LinearProgressManager();
    progressManager.init();
    
    // Auto-sync removed - data loads automatically on page load
    
    // Make it globally accessible for manual refresh
    window.linearProgress = progressManager;
});

// Add CSS for the new project styles
const style = document.createElement('style');
style.textContent = `
.phase-header {
    margin-bottom: 2rem;
}

.sync-controls {
    margin-top: 1rem;
}

.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
}

.btn--secondary {
    background: var(--color-background-light, #f8f9fa);
    color: var(--color-text, #333);
    border: 1px solid var(--color-border, #ddd);
}

.btn--secondary:hover {
    background: var(--color-background, #e9ecef);
}

.btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.sync-status {
    margin-left: 1rem;
    font-size: 0.85rem;
}

.sync-status--loading {
    color: var(--color-primary, #0066cc);
}

.sync-status--success {
    color: var(--color-success, #28a745);
}

.sync-status--error {
    color: var(--color-danger, #dc3545);
}
.phase__description {
    margin: 1rem 0;
    font-style: italic;
    color: var(--color-text-muted, #666);
}

.phase__content {
    padding-left: 2rem;
    padding-right: 2rem;
}

.phase--expanded .phase__content {
    padding-bottom: 2rem;
}

.phase__progress {
    margin: 1rem 0;
    padding: 1rem;
    background: var(--color-background-light, #f8f9fa);
    border-radius: 8px;
}

.progress-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.progress-percent {
    font-weight: 600;
    color: var(--color-primary, #0066cc);
}

.phase__projects {
    margin-top: 1rem;
}

.project {
    margin: 0.75rem 0;
    padding: 1rem;
    background: white;
    border: 1px solid var(--color-border, #e1e5e9);
    border-radius: 6px;
    transition: box-shadow 0.2s;
}

.project:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.project--completed {
    border-color: var(--color-success, #28a745);
    background: var(--color-success-light, #f8fff9);
}

.project__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.project__header h5 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
}

.project__progress {
    font-weight: 600;
    color: var(--color-primary, #0066cc);
}

.project__description {
    margin: 0.5rem 0;
    color: var(--color-text-muted, #666);
    font-size: 0.9rem;
}

.project__meta {
    display: flex;
    gap: 1rem;
    margin: 0.5rem 0;
    font-size: 0.85rem;
    color: var(--color-text-muted, #666);
}

.project__progress-bar {
    margin-top: 0.5rem;
}

.project__progress-bar .progress-bar__track {
    height: 4px;
    background: var(--color-background-light, #e1e5e9);
    border-radius: 2px;
    overflow: hidden;
}

.project__progress-bar .progress-bar__fill {
    height: 100%;
    background: var(--color-primary, #0066cc);
    transition: width 0.3s ease;
}

.phase__status {
    padding: 1rem;
    text-align: center;
    color: var(--color-text-muted, #666);
    font-style: italic;
}

.milestone-card__progress {
    margin-top: 0.5rem;
    font-size: 0.85rem;
    color: var(--color-text-muted, #666);
}

.milestone-card__lead {
    font-weight: 500;
}

.phase__date {
    margin-left: auto !important;
    margin-right: 1rem !important;
}
`;
document.head.appendChild(style);
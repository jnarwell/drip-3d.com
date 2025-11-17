const fs = require('fs');
const path = require('path');

const LINEAR_API_KEY = process.env.LINEAR_API_KEY || 'your-linear-api-key-here';
const LINEAR_API_URL = 'https://api.linear.app/graphql';

class LinearSync {
    constructor() {
        this.apiKey = LINEAR_API_KEY;
        this.apiUrl = LINEAR_API_URL;
    }

    async makeGraphQLRequest(query, variables = {}) {
        const response = await fetch(this.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': this.apiKey
            },
            body: JSON.stringify({
                query,
                variables
            })
        });

        const data = await response.json();
        
        if (data.errors) {
            throw new Error(`GraphQL Error: ${JSON.stringify(data.errors)}`);
        }
        
        return data.data;
    }

    async fetchInitiatives() {
        const query = `
            query {
                initiatives {
                    nodes {
                        id
                        name
                        description
                        targetDate
                        projects(first: 10) {
                            nodes {
                                id
                                name
                                description
                                progress
                                targetDate
                                health
                                lead {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        `;

        return await this.makeGraphQLRequest(query);
    }

    async fetchTeams() {
        const query = `
            query {
                teams {
                    nodes {
                        id
                        name
                        key
                        projects {
                            nodes {
                                id
                                name
                                status
                                progress
                                targetDate
                            }
                        }
                    }
                }
            }
        `;

        return await this.makeGraphQLRequest(query);
    }

    transformLinearDataToWebsiteFormat(initiatives) {
        return initiatives.nodes.map((initiative, index) => {
            const phaseNumber = index + 1;
            const projects = initiative.projects.nodes;
            
            // Calculate overall progress
            const totalProgress = projects.reduce((sum, project) => sum + (project.progress || 0), 0);
            const averageProgress = projects.length > 0 ? Math.round(totalProgress / projects.length) : 0;
            
            // Format target date
            const targetDate = initiative.targetDate ? new Date(initiative.targetDate).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            }) : 'TBD';

            return {
                phase: phaseNumber,
                title: initiative.name,
                description: initiative.description,
                targetDate: targetDate,
                progress: averageProgress,
                projects: projects.map(project => ({
                    id: project.id,
                    name: project.name,
                    description: project.description,
                    status: 'active',
                    progress: project.progress || 0,
                    targetDate: project.targetDate ? new Date(project.targetDate).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                    }) : 'TBD',
                    health: project.health,
                    lead: project.lead ? {
                        name: project.lead.name,
                        email: null
                    } : null
                }))
            };
        });
    }

    async updateProgressPage() {
        try {
            console.log('Fetching Linear data...');
            const data = await this.fetchInitiatives();
            const transformedData = this.transformLinearDataToWebsiteFormat(data.initiatives);
            
            // Save the data as JSON for the frontend
            const dataPath = path.join(__dirname, 'assets', 'data', 'progress.json');
            
            // Ensure directory exists
            const dataDir = path.dirname(dataPath);
            if (!fs.existsSync(dataDir)) {
                fs.mkdirSync(dataDir, { recursive: true });
            }
            
            const progressData = {
                lastUpdated: new Date().toISOString(),
                phases: transformedData
            };
            
            fs.writeFileSync(dataPath, JSON.stringify(progressData, null, 2));
            
            console.log('Progress data updated successfully!');
            console.log(`Found ${transformedData.length} phases with Linear data`);
            
            return progressData;
        } catch (error) {
            console.error('Error updating progress page:', error);
            throw error;
        }
    }

    async testConnection() {
        try {
            console.log('Testing Linear API connection...');
            const data = await this.fetchInitiatives();
            console.log('✅ Connection successful!');
            console.log(`Found ${data.initiatives.nodes.length} initiatives`);
            
            data.initiatives.nodes.forEach((initiative, index) => {
                console.log(`${index + 1}. ${initiative.name} (${initiative.projects.nodes.length} projects)`);
            });
            
            return true;
        } catch (error) {
            console.error('❌ Connection failed:', error.message);
            return false;
        }
    }
}

// CLI usage
if (require.main === module) {
    const sync = new LinearSync();
    
    const command = process.argv[2] || 'sync';
    
    switch (command) {
        case 'test':
            sync.testConnection();
            break;
        case 'sync':
            sync.updateProgressPage();
            break;
        default:
            console.log('Usage: node linear-sync.js [test|sync]');
    }
}

module.exports = LinearSync;
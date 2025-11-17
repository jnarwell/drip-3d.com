#!/usr/bin/env node

/**
 * Linear Sync Automation Script
 * 
 * This script can be used to:
 * 1. Set up automatic syncing with Linear on a schedule
 * 2. Handle webhook notifications from Linear for real-time updates
 * 3. Provide a simple HTTP endpoint to trigger syncs
 */

const http = require('http');
const url = require('url');
const LinearSync = require('./linear-sync');

class LinearSyncAutomation {
    constructor() {
        this.sync = new LinearSync();
        this.server = null;
        this.syncInterval = null;
    }

    // Start HTTP server for webhook handling and manual triggers
    startServer(port = 3001) {
        this.server = http.createServer(async (req, res) => {
            const parsedUrl = url.parse(req.url, true);
            
            // Set CORS headers
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
            res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
            
            if (req.method === 'OPTIONS') {
                res.writeHead(200);
                res.end();
                return;
            }

            try {
                switch (parsedUrl.pathname) {
                    case '/sync':
                        await this.handleSyncRequest(req, res);
                        break;
                    case '/webhook':
                        await this.handleWebhook(req, res);
                        break;
                    case '/status':
                        await this.handleStatusRequest(req, res);
                        break;
                    default:
                        res.writeHead(404, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({ error: 'Not found' }));
                }
            } catch (error) {
                console.error('Server error:', error);
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Internal server error' }));
            }
        });

        this.server.listen(port, () => {
            console.log(`Linear sync server running on port ${port}`);
            console.log(`Available endpoints:`);
            console.log(`  POST http://localhost:${port}/sync - Manual sync trigger`);
            console.log(`  POST http://localhost:${port}/webhook - Linear webhook endpoint`);
            console.log(`  GET http://localhost:${port}/status - Check sync status`);
        });
    }

    async handleSyncRequest(req, res) {
        try {
            console.log('Manual sync triggered');
            const result = await this.sync.updateProgressPage();
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: true,
                message: 'Sync completed successfully',
                timestamp: new Date().toISOString(),
                data: result
            }));
        } catch (error) {
            console.error('Sync failed:', error);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            }));
        }
    }

    async handleWebhook(req, res) {
        let body = '';
        
        req.on('data', chunk => {
            body += chunk.toString();
        });

        req.on('end', async () => {
            try {
                const webhookData = JSON.parse(body);
                console.log('Webhook received:', webhookData.type || 'unknown');
                
                // Check if this is a project or initiative update
                if (this.shouldTriggerSync(webhookData)) {
                    console.log('Triggering sync due to webhook');
                    await this.sync.updateProgressPage();
                }
                
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ received: true }));
            } catch (error) {
                console.error('Webhook processing failed:', error);
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Invalid webhook data' }));
            }
        });
    }

    async handleStatusRequest(req, res) {
        try {
            const connectionTest = await this.sync.testConnection();
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                status: 'running',
                linearConnection: connectionTest,
                lastSync: this.getLastSyncTime(),
                timestamp: new Date().toISOString()
            }));
        } catch (error) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                status: 'error',
                error: error.message,
                timestamp: new Date().toISOString()
            }));
        }
    }

    shouldTriggerSync(webhookData) {
        // Trigger sync for project and initiative updates
        const triggerTypes = [
            'Project',
            'Initiative',
            'ProjectUpdate',
            'Issue' // In case issues are used as milestones
        ];
        
        return triggerTypes.some(type => 
            webhookData.type && webhookData.type.includes(type)
        );
    }

    getLastSyncTime() {
        try {
            const fs = require('fs');
            const path = require('path');
            const dataPath = path.join(__dirname, 'assets', 'data', 'progress.json');
            
            if (fs.existsSync(dataPath)) {
                const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
                return data.lastUpdated;
            }
        } catch (error) {
            console.error('Error reading last sync time:', error);
        }
        return null;
    }

    // Start automatic syncing on an interval
    startPeriodicSync(intervalMinutes = 60) {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }

        this.syncInterval = setInterval(async () => {
            try {
                console.log('Performing scheduled sync...');
                await this.sync.updateProgressPage();
                console.log('Scheduled sync completed');
            } catch (error) {
                console.error('Scheduled sync failed:', error);
            }
        }, intervalMinutes * 60 * 1000);

        console.log(`Automatic sync scheduled every ${intervalMinutes} minutes`);
    }

    stop() {
        if (this.server) {
            this.server.close();
        }
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
        console.log('Linear sync automation stopped');
    }
}

// CLI usage
if (require.main === module) {
    const automation = new LinearSyncAutomation();
    const command = process.argv[2] || 'server';
    
    switch (command) {
        case 'server':
            const port = process.argv[3] || 3001;
            automation.startServer(port);
            automation.startPeriodicSync(30); // Sync every 30 minutes
            break;
        case 'sync':
            automation.sync.updateProgressPage().then(() => {
                console.log('One-time sync completed');
                process.exit(0);
            }).catch(error => {
                console.error('Sync failed:', error);
                process.exit(1);
            });
            break;
        default:
            console.log('Usage: node sync-automation.js [server|sync] [port]');
            console.log('  server - Start webhook server with periodic sync (default)');
            console.log('  sync   - Perform one-time sync and exit');
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\nShutting down...');
    if (module.exports && module.exports.stop) {
        module.exports.stop();
    }
    process.exit(0);
});

module.exports = LinearSyncAutomation;
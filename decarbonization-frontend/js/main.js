// Main Application Logic
class DecarbApp {
    constructor() {
        this.currentPage = 'overview';
        this.dashboardData = null;
        this.init();
    }

    init() {
        // Initialize navigation
        this.setupNavigation();

        // Initialize charts
        chartsManager.init();

        // Load initial data if authenticated
        if (authService.isAuthenticated()) {
            this.loadDashboardData();
        }

        // Setup event listeners
        this.setupEventListeners();
    }

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');

        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });
    }

    navigateTo(page) {
        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === page) {
                item.classList.add('active');
            }
        });

        // Update active page
        document.querySelectorAll('.page').forEach(p => {
            p.classList.remove('active');
        });

        const pageElement = document.getElementById(`${page}Page`);
        if (pageElement) {
            pageElement.classList.add('active');

            // Update header
            this.updateHeader(page);

            // Load page-specific data
            this.loadPageData(page);
        }

        this.currentPage = page;
    }

    updateHeader(page) {
        const titles = {
            overview: {
                title: 'Carbon Emissions Overview',
                subtitle: 'Real-time tracking and analysis of your carbon footprint'
            },
            emissions: {
                title: 'Emissions Data',
                subtitle: 'Detailed transaction-level emissions tracking'
            },
            targets: {
                title: 'Targets & Goals',
                subtitle: 'Track progress toward net-zero commitments'
            },
            copilot: {
                title: 'AI Copilot',
                subtitle: 'Get intelligent insights about your carbon data'
            },
            reports: {
                title: 'Reports & Exports',
                subtitle: 'Generate compliance and stakeholder reports'
            },
            insights: {
                title: 'Actionable Insights',
                subtitle: 'AI-powered recommendations and anomaly detection'
            }
        };

        const config = titles[page] || titles.overview;
        document.getElementById('pageTitle').textContent = config.title;
        document.getElementById('pageSubtitle').textContent = config.subtitle;
    }

    setupEventListeners() {
        // Export report button
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', async () => {
                try {
                    this.showLoading(true);
                    await DashboardAPI.exportReport();
                    this.showLoading(false);
                } catch (error) {
                    this.showLoading(false);
                    alert('Failed to export report: ' + error.message);
                }
            });
        }

        // Chart period buttons
        document.querySelectorAll('[data-period]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Update active state
                document.querySelectorAll('[data-period]').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');

                // Reload trend data
                const months = parseInt(e.target.dataset.period);
                this.loadTrendData(months);
            });
        });
    }

    async loadDashboardData() {
        try {
            this.showLoading(true);

            // Load dashboard overview
            const dashboard = await DashboardAPI.getOverview();
            this.dashboardData = dashboard;

            // Update UI with data
            this.updateMetrics(dashboard);
            this.updateCharts(dashboard);

            // Load anomalies
            this.loadAnomalies();

            this.showLoading(false);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.showLoading(false);

            // If no data available, show demo data
            this.loadDemoData();
        }
    }

    updateMetrics(data) {
        // Total emissions
        const totalEl = document.getElementById('totalEmissions');
        if (totalEl && data.total_emissions !== undefined) {
            totalEl.innerHTML = `
                <span class="metric-number">${data.total_emissions.toFixed(2)}</span>
                <span class="metric-unit">tCO2e</span>
            `;
        }

        // Scope breakdowns
        if (data.scope_breakdown) {
            const scope1El = document.getElementById('scope1Emissions');
            const scope2El = document.getElementById('scope2Emissions');
            const scope3El = document.getElementById('scope3Emissions');

            if (scope1El) {
                scope1El.innerHTML = `
                    <span class="metric-number">${(data.scope_breakdown[1] || 0).toFixed(2)}</span>
                    <span class="metric-unit">tCO2e</span>
                `;
            }

            if (scope2El) {
                scope2El.innerHTML = `
                    <span class="metric-number">${(data.scope_breakdown[2] || 0).toFixed(2)}</span>
                    <span class="metric-unit">tCO2e</span>
                `;
            }

            if (scope3El) {
                scope3El.innerHTML = `
                    <span class="metric-number">${(data.scope_breakdown[3] || 0).toFixed(2)}</span>
                    <span class="metric-unit">tCO2e</span>
                `;
            }
        }

        // Emissions change
        const changeEl = document.getElementById('emissionsChange');
        if (changeEl && data.period_change) {
            const change = data.period_change;
            const isPositive = change < 0; // Negative change is positive (reduction)
            changeEl.className = `metric-change ${isPositive ? 'positive' : 'negative'}`;
            changeEl.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                    <path d="${isPositive ? 'M6 10L2 6h8L6 10z' : 'M6 2L2 6h8L6 2z'}"/>
                </svg>
                <span>${Math.abs(change).toFixed(1)}% vs last period</span>
            `;
        }
    }

    updateCharts(data) {
        // Update scope chart
        if (data.scope_breakdown) {
            chartsManager.updateScopeChart(
                data.scope_breakdown[1] || 0,
                data.scope_breakdown[2] || 0,
                data.scope_breakdown[3] || 0
            );
        }

        // Update trend chart
        if (data.monthly_trend) {
            chartsManager.updateTrendChart(data.monthly_trend);
        }

        // Update category chart
        if (data.top_categories) {
            chartsManager.updateCategoryChart(data.top_categories);
        }
    }

    async loadTrendData(months = 12) {
        try {
            // This would call a specific endpoint for trend data
            // For now, we'll use the dashboard data
            if (this.dashboardData && this.dashboardData.monthly_trend) {
                const trendData = this.dashboardData.monthly_trend.slice(-months);
                chartsManager.updateTrendChart(trendData);
            }
        } catch (error) {
            console.error('Failed to load trend data:', error);
        }
    }

    async loadAnomalies() {
        try {
            const anomalies = await DashboardAPI.getAnomalies();

            if (anomalies && anomalies.length > 0) {
                const alertCard = document.getElementById('anomalyAlert');
                const messageEl = document.getElementById('anomalyMessage');

                if (alertCard && messageEl) {
                    messageEl.textContent = `${anomalies.length} anomalies detected in recent transactions. Review them to ensure data accuracy.`;
                    alertCard.style.display = 'flex';
                }
            }
        } catch (error) {
            console.error('Failed to load anomalies:', error);
        }
    }

    loadPageData(page) {
        switch (page) {
            case 'copilot':
                this.loadCopilotPage();
                break;
            case 'targets':
                this.loadTargetsPage();
                break;
            case 'emissions':
                this.loadEmissionsPage();
                break;
            case 'insights':
                this.loadInsightsPage();
                break;
            case 'reports':
                this.loadReportsPage();
                break;
        }
    }

    loadCopilotPage() {
        const pageEl = document.getElementById('copilotPage');
        if (!pageEl) return;

        pageEl.innerHTML = `
            <div class="copilot-container">
                <div class="chat-messages" id="chatMessages">
                    <div class="welcome-message">
                        <h3>👋 Welcome to Carbon Assistant</h3>
                        <p>Ask me anything about your emissions data, trends, or reduction strategies.</p>
                        <div class="suggested-questions">
                            <button class="suggestion-chip" data-question="What are my total emissions?">What are my total emissions?</button>
                            <button class="suggestion-chip" data-question="Show me Scope 2 trend">Show me Scope 2 trend</button>
                            <button class="suggestion-chip" data-question="What are my top emission categories?">Top categories?</button>
                        </div>
                    </div>
                </div>
                <div class="chat-input-container">
                    <input type="text" id="copilotInput" class="chat-input" placeholder="Ask about your carbon data...">
                    <button class="btn-primary" id="sendCopilotBtn">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M15.854.146a.5.5 0 01.11.54l-5.819 14.547a.75.75 0 01-1.329.124l-3.178-4.995L.643 7.184a.75.75 0 01.124-1.33L15.314.037a.5.5 0 01.54.11z"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        this.setupCopilot();
    }

    setupCopilot() {
        const input = document.getElementById('copilotInput');
        const sendBtn = document.getElementById('sendCopilotBtn');
        const messagesEl = document.getElementById('chatMessages');

        const sendMessage = async () => {
            const question = input.value.trim();
            if (!question) return;

            // Add user message
            this.addChatMessage(question, 'user');
            input.value = '';

            try {
                // Show typing indicator
                this.addChatMessage('...', 'assistant', true);

                const response = await CopilotAPI.query(question);

                // Remove typing indicator
                const typingIndicator = messagesEl.querySelector('.typing-indicator');
                if (typingIndicator) typingIndicator.remove();

                // Add assistant response
                this.addChatMessage(response.answer || 'Sorry, I could not process your question.', 'assistant');
            } catch (error) {
                const typingIndicator = messagesEl.querySelector('.typing-indicator');
                if (typingIndicator) typingIndicator.remove();

                this.addChatMessage('Sorry, there was an error processing your question.', 'assistant');
            }
        };

        if (sendBtn) {
            sendBtn.addEventListener('click', sendMessage);
        }

        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
        }

        // Suggestion chips
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                input.value = chip.dataset.question;
                sendMessage();
            });
        });
    }

    addChatMessage(text, role, isTyping = false) {
        const messagesEl = document.getElementById('chatMessages');
        if (!messagesEl) return;

        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${role} ${isTyping ? 'typing-indicator' : ''}`;
        messageEl.innerHTML = `
            <div class="message-content">${text}</div>
        `;

        messagesEl.appendChild(messageEl);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    loadTargetsPage() {
        const pageEl = document.getElementById('targetsPage');
        if (!pageEl) return;

        pageEl.innerHTML = `
            <div class="chart-card">
                <div class="chart-header">
                    <h3>Net Zero Progress</h3>
                    <button class="btn-primary">Set Target</button>
                </div>
                <p class="text-center" style="padding: 60px 0; color: #9ca3af;">
                    No targets set. Create your first net-zero target to start tracking progress.
                </p>
            </div>
        `;
    }

    loadEmissionsPage() {
        const pageEl = document.getElementById('emissionsPage');
        if (!pageEl) return;

        pageEl.innerHTML = `
            <div class="chart-card">
                <div class="chart-header">
                    <h3>Recent Transactions</h3>
                    <button class="btn-primary">Import CSV</button>
                </div>
                <p class="text-center" style="padding: 60px 0; color: #9ca3af;">
                    Emissions transaction data will appear here.
                </p>
            </div>
        `;
    }

    loadInsightsPage() {
        const pageEl = document.getElementById('insightsPage');
        if (!pageEl) return;

        pageEl.innerHTML = `
            <div class="chart-card">
                <div class="chart-header">
                    <h3>AI-Powered Insights</h3>
                </div>
                <p class="text-center" style="padding: 60px 0; color: #9ca3af;">
                    Loading insights and recommendations...
                </p>
            </div>
        `;
    }

    loadReportsPage() {
        const pageEl = document.getElementById('reportsPage');
        if (!pageEl) return;

        pageEl.innerHTML = `
            <div class="chart-card">
                <div class="chart-header">
                    <h3>Generate Reports</h3>
                </div>
                <div style="padding: 40px; text-align: center;">
                    <button class="btn-primary" style="font-size: 1.1rem; padding: 1rem 2rem;">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/><path fill-rule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5z"/>
                        </svg>
                        Download PDF Report
                    </button>
                </div>
            </div>
        `;
    }

    loadDemoData() {
        // Demo data for presentation
        const demoData = {
            total_emissions: 1245.67,
            scope_breakdown: {
                1: 345.23,
                2: 512.89,
                3: 387.55
            },
            period_change: -8.5,
            monthly_trend: [
                { month: '2024-06', emissions_tonnes: 98.5 },
                { month: '2024-07', emissions_tonnes: 105.2 },
                { month: '2024-08', emissions_tonnes: 112.8 },
                { month: '2024-09', emissions_tonnes: 108.3 },
                { month: '2024-10', emissions_tonnes: 95.7 },
                { month: '2024-11', emissions_tonnes: 103.4 }
            ],
            top_categories: [
                { category: 'Electricity', emissions_tonnes: 512.89 },
                { category: 'Natural Gas', emissions_tonnes: 245.12 },
                { category: 'Business Travel', emissions_tonnes: 187.34 },
                { category: 'Transportation', emissions_tonnes: 156.78 },
                { category: 'Waste', emissions_tonnes: 143.54 }
            ]
        };

        this.updateMetrics(demoData);
        this.updateCharts(demoData);
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.toggle('active', show);
        }
    }
}

// Initialize app when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    window.app = new DecarbApp();

    // Expose navigation function globally
    window.navigateTo = (page) => window.app.navigateTo(page);

    // Expose data loading function
    window.loadDashboardData = () => window.app.loadDashboardData();
});

// Add CSS for copilot page
const copilotStyles = document.createElement('style');
copilotStyles.textContent = `
.copilot-container {
    background: white;
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-md);
    border: 1px solid var(--gray-100);
    height: calc(100vh - 240px);
    display: flex;
    flex-direction: column;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-6);
}

.welcome-message {
    text-align: center;
    padding: var(--space-12) var(--space-6);
}

.welcome-message h3 {
    margin-bottom: var(--space-3);
    color: var(--gray-900);
}

.suggested-questions {
    display: flex;
    gap: var(--space-3);
    justify-content: center;
    flex-wrap: wrap;
    margin-top: var(--space-6);
}

.suggestion-chip {
    padding: var(--space-2) var(--space-4);
    background: var(--gray-50);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-full);
    color: var(--gray-700);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all var(--transition-base);
}

.suggestion-chip:hover {
    background: var(--primary-50);
    border-color: var(--primary-500);
    color: var(--primary-700);
}

.chat-message {
    margin-bottom: var(--space-4);
    display: flex;
    animation: slideIn 0.3s ease-out;
}

.chat-message.user {
    justify-content: flex-end;
}

.chat-message.user .message-content {
    background: var(--gradient-primary);
    color: white;
}

.chat-message.assistant .message-content {
    background: var(--gray-100);
    color: var(--gray-900);
}

.message-content {
    max-width: 70%;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-lg);
    line-height: 1.5;
}

.chat-input-container {
    padding: var(--space-6);
    border-top: 1px solid var(--gray-200);
    display: flex;
    gap: var(--space-3);
}

.chat-input {
    flex: 1;
    padding: var(--space-3) var(--space-4);
    border: 2px solid var(--gray-200);
    border-radius: var(--radius-lg);
    font-size: 1rem;
    font-family: var(--font-family);
}

.chat-input:focus {
    outline: none;
    border-color: var(--primary-500);
}
`;
document.head.appendChild(copilotStyles);

// Charts Configuration and Management
class ChartsManager {
    constructor() {
        this.charts = {};
        this.colors = {
            primary: 'rgb(16, 185, 129)',
            scope1: 'rgb(245, 158, 11)',
            scope2: 'rgb(59, 130, 246)',
            scope3: 'rgb(139, 92, 246)',
            gray: 'rgb(156, 163, 175)'
        };
    }

    // Initialize all charts
    init() {
        this.createTrendChart();
        this.createScopeChart();
        this.createCategoryChart();
    }

    // Trend Line Chart
    createTrendChart() {
        const ctx = document.getElementById('trendChart');
        if (!ctx) return;

        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Total Emissions (tCO2e)',
                    data: [],
                    borderColor: this.colors.primary,
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: this.colors.primary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        borderRadius: 8,
                        titleFont: { size: 14, weight: 'bold' },
                        bodyFont: { size: 13 },
                        callbacks: {
                            label: (context) => {
                                return `${context.parsed.y.toFixed(2)} tCO2e`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: (value) => value.toFixed(0) + ' t'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // Scope Breakdown Doughnut Chart
    createScopeChart() {
        const ctx = document.getElementById('scopeChart');
        if (!ctx) return;

        this.charts.scope = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Scope 1', 'Scope 2', 'Scope 3'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        this.colors.scope1,
                        this.colors.scope2,
                        this.colors.scope3
                    ],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: { size: 12, weight: '500' },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        borderRadius: 8,
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${value.toFixed(2)} tCO2e (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Category Bar Chart
    createCategoryChart() {
        const ctx = document.getElementById('categoryChart');
        if (!ctx) return;

        this.charts.category = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Emissions (tCO2e)',
                    data: [],
                    backgroundColor: this.colors.primary,
                    borderRadius: 8,
                    barThickness: 40
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        borderRadius: 8,
                        callbacks: {
                            label: (context) => {
                                return `${context.parsed.x.toFixed(2)} tCO2e`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // Update trend chart data
    updateTrendChart(data) {
        if (!this.charts.trend || !data) return;

        const labels = data.map(d => d.date || d.month);
        const values = data.map(d => d.emissions_tonnes || d.emissions || 0);

        this.charts.trend.data.labels = labels;
        this.charts.trend.data.datasets[0].data = values;
        this.charts.trend.update('none'); // Smooth update without animation
    }

    // Update scope chart data
    updateScopeChart(scope1, scope2, scope3) {
        if (!this.charts.scope) return;

        this.charts.scope.data.datasets[0].data = [
            scope1 || 0,
            scope2 || 0,
            scope3 || 0
        ];
        this.charts.scope.update('none');
    }

    // Update category chart data
    updateCategoryChart(categories) {
        if (!this.charts.category || !categories) return;

        const labels = categories.map(c => c.category);
        const values = categories.map(c => c.emissions_tonnes || c.total || 0);

        this.charts.category.data.labels = labels;
        this.charts.category.data.datasets[0].data = values;
        this.charts.category.update('none');
    }

    // Destroy all charts
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
    }
}

// Initialize charts manager
const chartsManager = new ChartsManager();

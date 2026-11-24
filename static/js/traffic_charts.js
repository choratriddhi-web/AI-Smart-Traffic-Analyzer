// AI Smart Traffic Analyzer - Chart.js Visualizations

document.addEventListener('DOMContentLoaded', async () => {
    const categoryCtx = document.getElementById('chart-category-distribution');
    const cameraCtx = document.getElementById('chart-camera-comparison');
    const trendCtx = document.getElementById('chart-density-trend');
    const laneCtx = document.getElementById('chart-lane-distribution');

    if (!categoryCtx && !cameraCtx && !trendCtx) return;

    try {
        const resp = await fetch('/analytics/api/data/');
        const data = await resp.json();

        // 1. Vehicle Category Doughnut Chart
        if (categoryCtx) {
            new Chart(categoryCtx, {
                type: 'doughnut',
                data: {
                    labels: data.categories.labels,
                    datasets: [{
                        data: data.categories.data,
                        backgroundColor: ['#c084fc', '#06b6d4', '#f59e0b', '#ec4899'],
                        borderColor: '#130a24',
                        borderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#cbd5e1', font: { size: 12 } } }
                    }
                }
            });
        }

        // 2. Camera Comparison Bar Chart
        if (cameraCtx) {
            new Chart(cameraCtx, {
                type: 'bar',
                data: {
                    labels: data.camera_comparison.labels,
                    datasets: [{
                        label: 'Total Crossings',
                        data: data.camera_comparison.data,
                        backgroundColor: ['#a855f7', '#ec4899', '#3b82f6', '#10b981'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: 'rgba(168, 85, 247, 0.1)' }, ticks: { color: '#94a3b8' } },
                        y: { grid: { color: 'rgba(168, 85, 247, 0.1)' }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

        // 3. Density Trend Line Chart
        if (trendCtx) {
            new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: data.density_trend.labels,
                    datasets: [{
                        label: 'Active Vehicles',
                        data: data.density_trend.data,
                        borderColor: '#22d3ee',
                        backgroundColor: 'rgba(6, 182, 212, 0.15)',
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#a855f7',
                        pointBorderColor: '#fff',
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: 'rgba(168, 85, 247, 0.1)' }, ticks: { color: '#94a3b8' } },
                        y: { grid: { color: 'rgba(168, 85, 247, 0.1)' }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: { legend: { labels: { color: '#cbd5e1' } } }
                }
            });
        }

        // 4. Lane Distribution Bar Chart
        if (laneCtx) {
            new Chart(laneCtx, {
                type: 'bar',
                data: {
                    labels: data.lane_distribution.labels,
                    datasets: [{
                        label: 'Vehicles in Lane',
                        data: data.lane_distribution.data,
                        backgroundColor: '#8b5cf6',
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: 'rgba(168, 85, 247, 0.1)' }, ticks: { color: '#94a3b8' } },
                        y: { grid: { color: 'rgba(168, 85, 247, 0.1)' }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }

    } catch (e) {
        console.error('Failed to load analytics data:', e);
    }
});

class NetworkLogComponent {
    constructor() {
        this.containerId = 'view-network-log';
        this.initialized = false;
        this.chart = null;
    }

    init() {
        if (this.initialized) return;
        this.render();
        this.initialized = true;
    }

    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="panel p-6 rounded-lg h-[calc(100vh-8rem)] flex flex-col animate-fade-in">
                <div class="flex justify-between items-center mb-6">
                    <div class="flex items-center gap-4">
                        <div class="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-500">
                            <i class="fas fa-network-wired text-xl"></i>
                        </div>
                        <div>
                            <h2 class="font-display font-bold text-2xl">Network Logs</h2>
                            <p class="text-sm font-mono opacity-60">Real-time Network Traffic Analysis</p>
                        </div>
                    </div>
                    <div class="flex gap-2">
                         <div class="relative">
                            <i class="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 opacity-40"></i>
                            <input type="text" placeholder="Search IP, Port, Protocol..." class="bg-black/20 border border-white/10 rounded-lg py-2 pl-10 pr-4 outline-none focus:border-purple-500/50 transition-all font-mono text-xs w-64">
                        </div>
                        <button onclick="window.networkLogComponent.refresh()" class="px-4 py-2 rounded bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-colors">
                            <i class="fas fa-sync mr-2"></i> Refresh
                        </button>
                    </div>
                </div>

                <!-- Stats & Graph Row -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                    <!-- Stats Grid -->
                    <div class="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="panel p-4 rounded bg-white/5 border border-white/5 flex flex-col gap-1">
                            <span class="text-[10px] font-mono uppercase opacity-60">Total Requests</span>
                            <span class="text-xl font-display font-bold" id="net-stat-total">0</span>
                        </div>
                        <div class="panel p-4 rounded bg-white/5 border border-white/5 flex flex-col gap-1">
                            <span class="text-[10px] font-mono uppercase opacity-60">Inbound Traffic</span>
                            <span class="text-xl font-display font-bold text-blue-400" id="net-stat-inbound">0 B</span>
                        </div>
                        <div class="panel p-4 rounded bg-white/5 border border-white/5 flex flex-col gap-1">
                            <span class="text-[10px] font-mono uppercase opacity-60">Outbound Traffic</span>
                            <span class="text-xl font-display font-bold text-green-400" id="net-stat-outbound">0 B</span>
                        </div>
                        <div class="panel p-4 rounded bg-white/5 border border-white/5 flex flex-col gap-1">
                            <span class="text-[10px] font-mono uppercase opacity-60">Unique IPs</span>
                            <span class="text-xl font-display font-bold text-purple-400" id="net-stat-unique">0</span>
                        </div>
                    </div>

                    <!-- Graph -->
                    <!--
                    <div class="panel p-4 rounded bg-white/5 border border-white/5 flex items-center justify-between relative overflow-hidden">
                        <div class="flex flex-col z-10">
                            <span class="text-[10px] font-mono uppercase opacity-60 mb-1">Protocol Distribution</span>
                            <h3 class="font-display font-bold text-lg">Traffic Overview</h3>
                        </div>
                        <div class="h-24 w-24 relative z-10">
                            <canvas id="networkProtocolChart"></canvas>
                        </div>
                        <div class="absolute right-0 top-0 w-32 h-full bg-gradient-to-l from-purple-500/10 to-transparent pointer-events-none"></div>
                    </div>
                    -->
                </div>

                <!-- Table -->
                <div class="flex-1 overflow-auto custom-scrollbar bg-black/20 rounded border border-white/5 relative">
                    <table class="w-full text-left text-xs font-mono">
                        <thead class="sticky top-0 z-10 bg-[#111] border-b border-white/10 uppercase tracking-wider text-white/40">
                            <tr>
                                <th class="p-3 w-32">Time</th>
                                <th class="p-3 w-32">Source</th>
                                <th class="p-3 w-32">Destination</th>
                                <th class="p-3 w-20">Protocol</th>
                                <th class="p-3 w-20">Service</th>
                                <th class="p-3 w-24 text-right">State</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-white/5 text-white/80" id="network-logs-body">
                            <!-- Logs will be injected here -->
                        </tbody>
                    </table>
                </div>
                
                <!-- Pagination -->
                 <div class="mt-4 flex justify-between items-center border-t border-white/10 pt-4">
                    <span class="text-xs opacity-60 font-mono" id="network-pagination-info">Showing 0-0 of 0</span>
                    <div class="flex gap-2">
                        <button class="px-3 py-1.5 rounded bg-white/5 hover:bg-white/10 text-xs font-bold transition disabled:opacity-30" disabled>Previous</button>
                        <button class="px-3 py-1.5 rounded bg-white/5 hover:bg-white/10 text-xs font-bold transition" disabled>Next</button>
                    </div>
                </div>
            </div>
        `;

        this.fetchData();
    }

    refresh() {
        this.fetchData();
    }

    async fetchData() {
        const tbody = document.getElementById('network-logs-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center opacity-40">Loading data...</td></tr>';
        }

        try {
            const response = await fetch('http://localhost:8000/network?limit=50&offset=0');
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            this.processData(data);
        } catch (error) {
            console.error('Error fetching network logs:', error);
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center text-red-400">Error loading data. Ensure backend is running.</td></tr>';
            }
        }
    }

    processData(data) {
        let logs = [];
        if (Array.isArray(data)) {
            logs = data;
        } else if (data && Array.isArray(data.connections)) {
            logs = data.connections;
        } else {
            console.error('Unexpected data format:', data);
            return;
        }

        // Update Stats
        let totalInbound = 0;
        let totalOutbound = 0;
        const uniqueIPs = new Set();
        const protocolCounts = {};

        logs.forEach(log => {
            totalInbound += (log.resp_ip_bytes || 0);
            totalOutbound += (log.orig_ip_bytes || 0);
            if (log.orig_h) uniqueIPs.add(log.orig_h);
            if (log.resp_h) uniqueIPs.add(log.resp_h);

            const proto = (log.proto || 'unknown').toUpperCase();
            protocolCounts[proto] = (protocolCounts[proto] || 0) + 1;
        });

        document.getElementById('net-stat-total').innerText = logs.length.toLocaleString();
        document.getElementById('net-stat-inbound').innerText = this.formatBytes(totalInbound);
        document.getElementById('net-stat-outbound').innerText = this.formatBytes(totalOutbound);
        document.getElementById('net-stat-unique').innerText = uniqueIPs.size.toLocaleString();

        // Update Table
        const tbody = document.getElementById('network-logs-body');
        if (tbody) {
            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="p-4 text-center opacity-40">No logs found</td></tr>';
            } else {
                tbody.innerHTML = logs.map(log => {
                    const time = new Date(log.recv_time || log.ts).toLocaleTimeString();

                    let stateColor = 'text-yellow-500';
                    if (log.conn_state === 'SF') stateColor = 'text-green-500';
                    else if (['REJ', 'RSTO', 'RSTR'].includes(log.conn_state)) stateColor = 'text-red-500';

                    return `
                    <tr class="hover:bg-white/5 transition-colors">
                        <td class="p-3 opacity-60 whitespace-nowrap">${time}</td>
                        <td class="p-3 text-blue-400 font-mono">${log.orig_h}:${log.orig_p}</td>
                        <td class="p-3 text-purple-400 font-mono">${log.resp_h}:${log.resp_p}</td>
                        <td class="p-3 opacity-80 font-bold">${(log.proto || '-').toUpperCase()}</td>
                        <td class="p-3 opacity-60 font-mono">${log.service || '-'}</td>
                        <td class="p-3 text-right font-bold ${stateColor}">${log.conn_state}</td>
                    </tr>
                    `;
                }).join('');
            }
        }

        // Update Pagination Info
        document.getElementById('network-pagination-info').innerText = `Showing 1-${logs.length} of ${logs.length}`;

        // Update Chart
        this.updateChart(protocolCounts);
    }

    updateChart(protocolCounts) {
        const ctx = document.getElementById('networkProtocolChart');
        if (!ctx) return;

        const labels = Object.keys(protocolCounts);
        const data = Object.values(protocolCounts);

        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#a855f7', // Purple
                        '#3b82f6', // Blue
                        '#22c55e', // Green
                        '#eab308', // Yellow
                        '#ef4444', // Red
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
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
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 10,
                        bodyFont: {
                            family: 'monospace'
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    formatBytes(bytes, decimals = 2) {
        if (!+bytes) return '0 B';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
    }
}

window.networkLogComponent = new NetworkLogComponent();

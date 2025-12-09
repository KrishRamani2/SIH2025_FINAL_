
class TTPLogsManager {
    constructor() {
        this.currentPage = 0;
        this.limit = 20;
        this.currentFilter = 'all';
        this.logsCache = [];
    }

    init() {
        this.fetchLogs();
    }

    async fetchLogs() {
        const tbody = document.getElementById('ttp-logs-table-body');
        if (!tbody) return;

        tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center opacity-50"><i class="fas fa-circle-notch fa-spin mr-2"></i> Loading TTP logs...</td></tr>';

        try {
            let url = `/api/alerts/?limit=${this.limit}&offset=${this.currentPage * this.limit}`;

            // We can reuse the severity filter logic if needed, but for now let's just fetch all
            // and assume "TTP Logs" are essentially all alerts that are rule-based.

            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                this.logsCache = data.alerts || [];
                this.renderTable(this.logsCache, data.total || 0);
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-red-500">Failed to load logs</td></tr>';
            }
        } catch (e) {
            console.error(e);
            tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-red-500">Error connecting to server</td></tr>';
        }
    }

    renderTable(logs, total) {
        const tbody = document.getElementById('ttp-logs-table-body');
        const paginationInfo = document.getElementById('ttp-logs-pagination-info');
        const btnPrev = document.getElementById('btn-prev-ttp-logs');
        const btnNext = document.getElementById('btn-next-ttp-logs');

        if (!tbody) return;

        if (!logs || logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center opacity-50">No TTP logs found</td></tr>';
            if (paginationInfo) paginationInfo.innerText = 'Showing 0-0 of 0';
            if (btnPrev) btnPrev.disabled = true;
            if (btnNext) btnNext.disabled = true;
            return;
        }

        tbody.innerHTML = logs.map(log => {
            const id = log.id || '-';
            const title = log.title || 'Untitled';
            let severity = log.severity ? log.severity.toLowerCase() : 'info';
            const hostname = log.server ? log.server.hostname : 'Unknown';
            const time = log.triggered_at ? new Date(log.triggered_at).toLocaleString() : '-';

            // Extract TTP info from metadata if available
            let ttpId = '-';
            let technique = '-';

            if (log.metadata) {
                if (log.metadata.tags) {
                    // Look for MITRE tags like Txxxx
                    const tags = Array.isArray(log.metadata.tags) ? log.metadata.tags : [log.metadata.tags];
                    const mitreTag = tags.find(t => /^T\d{4}$/.test(t));
                    if (mitreTag) ttpId = mitreTag;
                }
                // Sometimes technique name is in description or title, or metadata
            }

            // Styling
            let severityClass = 'text-blue-500';
            if (severity === 'critical' || severity === 'high') severityClass = 'text-red-500';
            else if (severity === 'medium' || severity === 'warning') severityClass = 'text-orange-500';

            return `
                <tr class="table-row transition-colors hover:bg-white/5 group">
                    <td class="p-4 border-b border-white/5 text-xs opacity-60">#${id}</td>
                    <td class="p-4 border-b border-white/5 font-bold text-sm">${title}</td>
                    <td class="p-4 border-b border-white/5">
                        <span class="font-bold uppercase text-xs ${severityClass}">
                            ${severity}
                        </span>
                    </td>
                    <td class="p-4 border-b border-white/5 text-xs font-mono text-yellow-500">${ttpId}</td>
                    <td class="p-4 border-b border-white/5 text-xs font-mono opacity-80">${hostname}</td>
                    <td class="p-4 border-b border-white/5 text-xs opacity-60">${time}</td>
                </tr>
            `;
        }).join('');

        // Pagination
        if (paginationInfo) {
            const start = this.currentPage * this.limit + 1;
            const end = Math.min((this.currentPage + 1) * this.limit, total);
            paginationInfo.innerText = `Showing ${start}-${end} of ${total}`;
        }

        if (btnPrev) btnPrev.disabled = this.currentPage === 0;
        if (btnNext) btnNext.disabled = (this.currentPage + 1) * this.limit >= total;
    }

    changePage(delta) {
        this.currentPage += delta;
        if (this.currentPage < 0) this.currentPage = 0;
        this.fetchLogs();
    }
}

const ttpLogsManager = new TTPLogsManager();

(function () {
    const page = document.body.dataset.page;
    const statusEl = document.getElementById('status');
    const refreshTimers = [];

    function escapeHtml(text) {
        return String(text == null ? '' : text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function fmtDate(value) {
        if (!value) {
            return '-';
        }
        const d = new Date(value);
        if (Number.isNaN(d.getTime())) {
            return String(value);
        }
        const p = (n) => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
    }

    function setStatus(message, isError) {
        if (!statusEl) {
            return;
        }
        statusEl.textContent = message || '';
        statusEl.className = isError ? 'status-bad' : 'status-good';
    }

    async function apiRequest(method, path, body) {
        const res = await fetch(path, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: body ? JSON.stringify(body) : undefined
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.message || `请求失败: ${path}`);
        }
        return data;
    }

    function qs(path, params) {
        const url = new URL(path, window.location.origin);
        Object.keys(params || {}).forEach((key) => {
            if (params[key] !== undefined && params[key] !== null) {
                url.searchParams.set(key, String(params[key]));
            }
        });
        return url.pathname + url.search;
    }

    async function apiGet(path, params) {
        const url = qs(path, params || {});
        const res = await fetch(url);
        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.message || `请求失败: ${path}`);
        }
        return data;
    }

    function activateMenu() {
        const links = document.querySelectorAll('.menu a');
        links.forEach((el) => {
            const key = el.getAttribute('data-key');
            if (key === page) {
                el.classList.add('active');
            }
        });
    }

    function setAutoRefresh(handler, intervalMs, checkboxId) {
        const cb = document.getElementById(checkboxId);
        const timer = setInterval(() => {
            if (!cb || cb.checked) {
                handler();
            }
        }, intervalMs);
        refreshTimers.push(timer);
    }

    async function initDashboard() {
        async function load() {
            const [summary, health] = await Promise.all([
                apiGet('/admin/summary'),
                apiGet('/admin/health')
            ]);

            document.getElementById('sumProxies').textContent = summary.status.sum_proxies_cnt || 0;
            document.getElementById('validatedProxies').textContent = summary.status.validated_proxies_cnt || 0;
            document.getElementById('pendingProxies').textContent = summary.status.pending_proxies_cnt || 0;
            document.getElementById('enabledFetchers').textContent = (summary.fetchers || []).filter((f) => f.enable).length;
            document.getElementById('healthText').textContent = `API=${health.api_ok ? 'OK' : 'FAIL'} / DB=${health.db_ok ? 'OK' : 'FAIL'}`;

            const protocolTbody = document.getElementById('protocolBody');
            protocolTbody.innerHTML = (summary.protocol_stats || []).map((row) => `
                <tr>
                    <td>${escapeHtml(row.protocol)}</td>
                    <td>${row.total || 0}</td>
                    <td>${row.validated || 0}</td>
                </tr>
            `).join('');

            const errorsTbody = document.getElementById('errorsBody');
            errorsTbody.innerHTML = (summary.recent_errors || []).map((row) => `
                <tr>
                    <td>${escapeHtml(row.fetcher_name)}</td>
                    <td>${escapeHtml(fmtDate(row.created_at))}</td>
                    <td>${escapeHtml(row.error_message)}</td>
                </tr>
            `).join('');

            setStatus('总览已更新', false);
        }

        document.getElementById('refreshBtn').addEventListener('click', load);
        await load();
        setAutoRefresh(load, 5000, 'autoRefresh');
    }

    async function initFetchers() {
        async function load() {
            const summary = await apiGet('/admin/summary');
            const rows = summary.fetchers || [];
            document.getElementById('fetcherCount').textContent = rows.length;
            document.getElementById('enabledCount').textContent = rows.filter((f) => f.enable).length;
            document.getElementById('fetchersBody').innerHTML = rows.map((row, index) => `
                <tr>
                    <td>${escapeHtml(row.name)}</td>
                    <td>${row.validated_cnt || 0}</td>
                    <td>${row.in_db_cnt || 0}</td>
                    <td>${row.sum_proxies_cnt || 0}</td>
                    <td>${row.last_proxies_cnt || 0}</td>
                    <td>${escapeHtml(fmtDate(row.last_fetch_date))}</td>
                    <td><input type="checkbox" data-index="${index}" ${row.enable ? 'checked' : ''} /></td>
                </tr>
            `).join('');
            const toggles = document.querySelectorAll('#fetchersBody input[type="checkbox"]');
            toggles.forEach((el) => {
                el.addEventListener('change', async () => {
                    const idx = Number(el.getAttribute('data-index'));
                    const item = rows[idx];
                    const enable = el.checked ? '1' : '0';
                    try {
                        await apiGet('/fetcher_enable', { name: item.name, enable });
                        setStatus(`已更新抓取器: ${item.name}`, false);
                    } catch (err) {
                        el.checked = !el.checked;
                        setStatus(err.message, true);
                    }
                });
            });
            document.getElementById('lastFetchersRefresh').textContent = fmtDate(new Date());
            setStatus('抓取器状态已更新', false);
        }

        document.getElementById('refreshBtn').addEventListener('click', load);
        document.getElementById('clearStatsBtn').addEventListener('click', async () => {
            const token = document.getElementById('clearStatsToken').value.trim();
            if (token !== 'CLEAR_FETCHERS_STATS') {
                setStatus('确认词错误：需要 CLEAR_FETCHERS_STATS', true);
                return;
            }
            if (!window.confirm('确认清空抓取器统计？此操作不可撤销。')) {
                return;
            }
            await apiRequest('POST', '/admin/maintenance/clear_fetchers_stats', { confirm_text: token });
            setStatus('抓取器统计已清空', false);
            await load();
        });

        await load();
        setAutoRefresh(load, 4000, 'autoRefresh');
    }

    async function initProxies() {
        const state = {
            page: 1,
            pageSize: 50,
            total: 0
        };

        async function loadFetchers() {
            const summary = await apiGet('/admin/summary');
            const select = document.getElementById('fetcherFilter');
            const items = summary.fetchers || [];
            items.forEach((f) => {
                const opt = document.createElement('option');
                opt.value = f.name;
                opt.textContent = f.name;
                select.appendChild(opt);
            });
        }

        function filters() {
            return {
                protocol: document.getElementById('protocolFilter').value,
                validated: document.getElementById('validatedFilter').value,
                fetcher_name: document.getElementById('fetcherFilter').value,
                keyword: document.getElementById('keywordFilter').value.trim(),
                page: state.page,
                page_size: state.pageSize
            };
        }

        async function load() {
            const data = await apiGet('/admin/proxies', filters());
            state.total = data.total || 0;
            const rows = data.items || [];
            document.getElementById('proxiesBody').innerHTML = rows.map((row) => `
                <tr>
                    <td>${escapeHtml(row.fetcher_name)}</td>
                    <td>${escapeHtml(row.protocol)}</td>
                    <td>${escapeHtml(row.ip)}</td>
                    <td>${row.port}</td>
                    <td class="${row.validated ? 'status-good' : 'status-bad'}">${row.validated ? '可用' : '不可用'}</td>
                    <td>${row.latency == null ? '-' : row.latency}</td>
                    <td>${escapeHtml(fmtDate(row.validate_date))}</td>
                </tr>
            `).join('');
            document.getElementById('totalCnt').textContent = state.total;
            document.getElementById('pageInfo').textContent = `第 ${state.page} 页`;
            setStatus('代理列表已更新', false);
        }

        function exportCsv() {
            const f = filters();
            delete f.page;
            delete f.page_size;
            window.open(qs('/admin/proxies/export.csv', f), '_blank');
        }

        document.getElementById('searchBtn').addEventListener('click', async () => {
            state.page = 1;
            await load();
        });
        document.getElementById('exportBtn').addEventListener('click', exportCsv);
        document.getElementById('refreshBtn').addEventListener('click', load);
        document.getElementById('prevPageBtn').addEventListener('click', async () => {
            if (state.page > 1) {
                state.page -= 1;
                await load();
            }
        });
        document.getElementById('nextPageBtn').addEventListener('click', async () => {
            const maxPage = Math.max(Math.ceil(state.total / state.pageSize), 1);
            if (state.page < maxPage) {
                state.page += 1;
                await load();
            }
        });
        document.getElementById('pageSize').addEventListener('change', async (e) => {
            state.pageSize = Number(e.target.value) || 50;
            state.page = 1;
            await load();
        });

        await loadFetchers();
        await load();
        setAutoRefresh(load, 5000, 'autoRefresh');
    }

    function validateSources(lines) {
        const invalid = [];
        const allowed = new Set(['http', 'https', 'socks4', 'socks5', 'auto']);
        let validCount = 0;

        lines.forEach((line, index) => {
            const lineNo = index + 1;
            const text = line.trim();
            if (!text || text.startsWith('#')) {
                return;
            }
            validCount += 1;
            let protocol = 'http';
            let url = text;
            if (text.includes(',')) {
                const parts = text.split(',');
                protocol = (parts.shift() || '').trim().toLowerCase();
                url = parts.join(',').trim();
                if (!allowed.has(protocol)) {
                    invalid.push({ line_no: lineNo, line, message: `协议不合法: ${protocol}` });
                    return;
                }
            }
            if (!/^https?:\/\//i.test(url)) {
                invalid.push({ line_no: lineNo, line, message: `URL必须以http(s)开头: ${url}` });
            }
        });
        return { invalid, validCount };
    }

    async function initSources() {
        async function load() {
            const data = await apiGet('/admin/sources');
            document.getElementById('sourcePath').textContent = data.file_path || '-';
            const text = (data.lines || []).join('\n');
            document.getElementById('sourceEditor').value = text;
            renderValidation();
            setStatus('代理源已加载', false);
        }

        function renderValidation() {
            const lines = document.getElementById('sourceEditor').value.replace(/\r\n/g, '\n').split('\n');
            const result = validateSources(lines);
            document.getElementById('validSourceCnt').textContent = result.validCount;
            document.getElementById('sourceInvalidBody').innerHTML = result.invalid.map((row) => `
                <tr>
                    <td>${row.line_no}</td>
                    <td>${escapeHtml(row.line)}</td>
                    <td>${escapeHtml(row.message)}</td>
                </tr>
            `).join('');
            return { lines, result };
        }

        document.getElementById('refreshBtn').addEventListener('click', load);
        document.getElementById('sourceEditor').addEventListener('input', renderValidation);
        document.getElementById('saveBtn').addEventListener('click', async () => {
            const { lines, result } = renderValidation();
            if (result.invalid.length > 0) {
                setStatus(`存在 ${result.invalid.length} 行错误，不能保存`, true);
                return;
            }
            await apiRequest('PUT', '/admin/sources', { lines });
            setStatus('代理源保存成功', false);
            await load();
        });

        await load();
    }

    async function initSystem() {
        async function load() {
            const [summary, health] = await Promise.all([
                apiGet('/admin/summary'),
                apiGet('/admin/health')
            ]);
            document.getElementById('apiHealth').textContent = health.api_ok ? 'OK' : 'FAIL';
            document.getElementById('dbHealth').textContent = health.db_ok ? 'OK' : 'FAIL';
            document.getElementById('registeredFetchers').textContent = health.fetchers_registered || 0;
            document.getElementById('runtimeConfig').textContent = JSON.stringify(summary.runtime_config || {}, null, 2);
            setStatus('系统信息已更新', false);
        }

        document.getElementById('refreshBtn').addEventListener('click', load);
        document.getElementById('clearStatsBtn').addEventListener('click', async () => {
            const token = document.getElementById('clearStatsToken').value.trim();
            if (token !== 'CLEAR_FETCHERS_STATS') {
                setStatus('确认词错误：需要 CLEAR_FETCHERS_STATS', true);
                return;
            }
            if (!window.confirm('确认清空抓取器统计？')) {
                return;
            }
            await apiRequest('POST', '/admin/maintenance/clear_fetchers_stats', { confirm_text: token });
            setStatus('抓取器统计已清空', false);
            await load();
        });
        document.getElementById('clearProxiesBtn').addEventListener('click', async () => {
            const token = document.getElementById('clearProxiesToken').value.trim();
            if (token !== 'CLEAR_PROXIES') {
                setStatus('确认词错误：需要 CLEAR_PROXIES', true);
                return;
            }
            if (!window.confirm('确认清空代理池？此操作不可撤销。')) {
                return;
            }
            await apiRequest('POST', '/admin/maintenance/clear_proxies', { confirm_text: token });
            setStatus('代理池已清空', false);
            await load();
        });

        await load();
        setAutoRefresh(load, 6000, 'autoRefresh');
    }

    async function boot() {
        activateMenu();
        try {
            if (page === 'dashboard') {
                await initDashboard();
            } else if (page === 'fetchers') {
                await initFetchers();
            } else if (page === 'proxies') {
                await initProxies();
            } else if (page === 'sources') {
                await initSources();
            } else if (page === 'system') {
                await initSystem();
            }
        } catch (err) {
            setStatus(err.message || String(err), true);
        }
    }

    window.addEventListener('beforeunload', () => {
        refreshTimers.forEach((id) => clearInterval(id));
    });

    boot();
})();

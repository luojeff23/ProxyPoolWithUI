<template>
    <div>
        <a-card :bordered="false">
            <a-row :gutter="12">
                <a-col :xs="24" :sm="12" :md="6">
                    <a-select v-model="filters.protocol" style="width: 100%" @change="onFilterChange">
                        <a-select-option value="all">全部协议</a-select-option>
                        <a-select-option value="http">http</a-select-option>
                        <a-select-option value="https">https</a-select-option>
                        <a-select-option value="socks4">socks4</a-select-option>
                        <a-select-option value="socks5">socks5</a-select-option>
                    </a-select>
                </a-col>
                <a-col :xs="24" :sm="12" :md="6">
                    <a-select v-model="filters.validated" style="width: 100%" @change="onFilterChange">
                        <a-select-option value="all">全部状态</a-select-option>
                        <a-select-option value="true">仅可用</a-select-option>
                        <a-select-option value="false">仅不可用</a-select-option>
                    </a-select>
                </a-col>
                <a-col :xs="24" :sm="12" :md="6">
                    <a-select v-model="filters.fetcher_name" style="width: 100%" @change="onFilterChange">
                        <a-select-option value="all">全部来源</a-select-option>
                        <a-select-option v-for="f in fetchers" :key="f.name" :value="f.name">
                            {{ f.name }}
                        </a-select-option>
                    </a-select>
                </a-col>
                <a-col :xs="24" :sm="12" :md="4">
                    <a-input
                        v-model="filters.keyword"
                        placeholder="搜索IP / 端口 / 来源"
                        allow-clear
                        @pressEnter="onFilterChange"
                    />
                </a-col>
                <a-col :xs="24" :sm="12" :md="8" style="text-align: right">
                    <a-button type="primary" icon="search" @click="onFilterChange">筛选</a-button>
                    <a-button style="margin-left: 8px" icon="download" @click="exportCsv">导出CSV</a-button>
                </a-col>
            </a-row>
        </a-card>
        <a-row :gutter="12" style="margin-top: 12px">
            <a-col :xs="24" :md="8">
                <a-card>
                    <a-statistic title="筛选结果总数" :value="total" />
                </a-card>
            </a-col>
            <a-col :xs="24" :md="8">
                <a-card>
                    <a-statistic title="当前页数量" :value="items.length" />
                </a-card>
            </a-col>
            <a-col :xs="24" :md="8">
                <a-card>
                    <a-statistic title="自动刷新" :value="autoupdate ? 'ON' : 'OFF'" />
                    <a-switch v-model="autoupdate" />
                </a-card>
            </a-col>
        </a-row>
        <a-table
            style="margin-top: 12px"
            :columns="columns"
            :data-source="items"
            :row-key="(r) => `${r.protocol}://${r.ip}:${r.port}`"
            :pagination="pagination"
            :loading="loading"
            :bordered="true"
            @change="onTableChange"
        >
            <span slot="validated" slot-scope="validated">
                <a-tag :color="validated ? 'green' : 'red'">{{ validated ? '可用' : '不可用' }}</a-tag>
            </span>
            <span slot="latency" slot-scope="latency">
                <a-tag v-if="latency !== null" :color="latency < 2000 ? 'green' : (latency < 4000 ? 'orange' : 'red')">
                    {{ latency }}
                </a-tag>
                <span v-else>-</span>
            </span>
        </a-table>
    </div>
</template>

<script>
import moment from 'moment';

const columns = [
    { title: '来源', dataIndex: 'fetcher_name', width: 180 },
    { title: '协议', dataIndex: 'protocol', width: 90 },
    { title: 'IP', dataIndex: 'ip', width: 150 },
    { title: '端口', dataIndex: 'port', width: 100 },
    { title: '状态', dataIndex: 'validated', width: 90, scopedSlots: { customRender: 'validated' } },
    { title: '延迟(ms)', dataIndex: 'latency', width: 110, scopedSlots: { customRender: 'latency' } },
    {
        title: '上次验证时间',
        dataIndex: 'validate_date',
        customRender: (value) => value ? moment(value).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    {
        title: '下次验证时间',
        dataIndex: 'to_validate_date',
        customRender: (value) => value ? moment(value).format('YYYY-MM-DD HH:mm:ss') : '-'
    }
];

export default {
    data () {
        return {
            columns,
            items: [],
            fetchers: [],
            loading: false,
            total: 0,
            page: 1,
            pageSize: 50,
            autoupdate: true,
            timer: null,
            filters: {
                protocol: 'all',
                validated: 'all',
                fetcher_name: 'all',
                keyword: ''
            }
        };
    },
    computed: {
        pagination () {
            return {
                current: this.page,
                pageSize: this.pageSize,
                total: this.total,
                showSizeChanger: true,
                showTotal: total => `总计 ${total} 条`
            };
        }
    },
    mounted () {
        this.loadFetchers();
        this.fetchData();
        this.timer = setInterval(() => {
            if (this.autoupdate) {
                this.fetchData();
            }
        }, 4000);
    },
    destroyed () {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    },
    methods: {
        buildApiUrl (path) {
            const base = (this.$http.baseURL || '').trim();
            if (base === '' || base === '/') {
                return path;
            }
            return `${base.replace(/\/+$/, '')}${path}`;
        },
        async loadFetchers () {
            const data = await this.$http.get('/admin/summary');
            this.fetchers = data.fetchers || [];
        },
        async fetchData () {
            this.loading = true;
            try {
                const data = await this.$http.get('/admin/proxies', {
                    protocol: this.filters.protocol,
                    validated: this.filters.validated,
                    fetcher_name: this.filters.fetcher_name,
                    keyword: this.filters.keyword,
                    page: this.page,
                    page_size: this.pageSize
                });
                this.items = data.items || [];
                this.total = data.total || 0;
            } finally {
                this.loading = false;
            }
        },
        onTableChange (pagination) {
            this.page = pagination.current;
            this.pageSize = pagination.pageSize;
            this.fetchData();
        },
        onFilterChange () {
            this.page = 1;
            this.fetchData();
        },
        exportCsv () {
            const params = new URLSearchParams({
                protocol: this.filters.protocol,
                validated: this.filters.validated,
                fetcher_name: this.filters.fetcher_name,
                keyword: this.filters.keyword
            });
            const url = this.buildApiUrl(`/admin/proxies/export.csv?${params.toString()}`);
            window.open(url, '_blank');
        }
    }
};
</script>

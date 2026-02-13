<template>
    <div>
        <a-row :gutter="12">
            <a-col :xs="24" :md="6">
                <a-card><a-statistic title="总代理数量" :value="status.sum_proxies_cnt || 0" /></a-card>
            </a-col>
            <a-col :xs="24" :md="6">
                <a-card><a-statistic title="可用代理数量" :value="status.validated_proxies_cnt || 0" /></a-card>
            </a-col>
            <a-col :xs="24" :md="6">
                <a-card><a-statistic title="待验证数量" :value="status.pending_proxies_cnt || 0" /></a-card>
            </a-col>
            <a-col :xs="24" :md="6">
                <a-card>
                    <a-statistic title="已启用抓取器" :value="enabledFetcherCount" />
                    <div style="margin-top: 8px">自动刷新 <a-switch v-model="autoupdate" /></div>
                </a-card>
            </a-col>
        </a-row>

        <a-row :gutter="12" style="margin-top: 12px">
            <a-col :xs="24" :md="12">
                <a-card title="协议分布">
                    <a-table
                        :columns="protocolColumns"
                        :data-source="protocolStats"
                        :pagination="false"
                        row-key="protocol"
                        size="small"
                    />
                </a-card>
            </a-col>
            <a-col :xs="24" :md="12">
                <a-card title="运行健康状态">
                    <a-descriptions :column="1" size="small">
                        <a-descriptions-item label="API状态">
                            <a-tag :color="health.api_ok ? 'green' : 'red'">{{ health.api_ok ? 'OK' : 'FAIL' }}</a-tag>
                        </a-descriptions-item>
                        <a-descriptions-item label="数据库状态">
                            <a-tag :color="health.db_ok ? 'green' : 'red'">{{ health.db_ok ? 'OK' : 'FAIL' }}</a-tag>
                        </a-descriptions-item>
                        <a-descriptions-item label="抓取器注册数">
                            {{ health.fetchers_registered || 0 }}
                        </a-descriptions-item>
                    </a-descriptions>
                    <a-alert
                        v-if="health.db_error"
                        :message="health.db_error"
                        type="error"
                        show-icon
                        style="margin-top: 8px"
                    />
                </a-card>
            </a-col>
        </a-row>

        <a-card title="最近抓取错误" style="margin-top: 12px">
            <a-table
                :columns="errorColumns"
                :data-source="recentErrors"
                :pagination="{ pageSize: 8 }"
                row-key="id"
                size="small"
            />
        </a-card>
    </div>
</template>

<script>
import moment from 'moment';

const protocolColumns = [
    { title: '协议', dataIndex: 'protocol' },
    { title: '总数', dataIndex: 'total' },
    { title: '可用数', dataIndex: 'validated' }
];

const errorColumns = [
    { title: '抓取器', dataIndex: 'fetcher_name', width: 180 },
    {
        title: '时间',
        dataIndex: 'created_at',
        width: 170,
        customRender: (value) => value ? moment(value).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    { title: '错误信息', dataIndex: 'error_message' }
];

export default {
    data () {
        return {
            protocolColumns,
            errorColumns,
            autoupdate: true,
            status: {},
            health: {},
            protocolStats: [],
            fetchers: [],
            recentErrors: [],
            timer: null
        };
    },
    computed: {
        enabledFetcherCount () {
            return (this.fetchers || []).filter(item => item.enable).length;
        }
    },
    mounted () {
        this.update();
        this.timer = setInterval(() => {
            if (this.autoupdate) {
                this.update();
            }
        }, 5000);
    },
    destroyed () {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    },
    methods: {
        async update () {
            const [summary, health] = await Promise.all([
                this.$http.get('/admin/summary'),
                this.$http.get('/admin/health')
            ]);
            this.status = summary.status || {};
            this.protocolStats = summary.protocol_stats || [];
            this.fetchers = summary.fetchers || [];
            this.recentErrors = summary.recent_errors || [];
            this.health = health || {};
        }
    }
};
</script>

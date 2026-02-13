<template>
    <div>
        <a-row :gutter="12">
            <a-col :xs="24" :md="6">
                <a-card>
                    <a-statistic title="API状态" :value="health.api_ok ? 'OK' : 'FAIL'" />
                    <a-tag :color="health.api_ok ? 'green' : 'red'">{{ health.api_ok ? '可访问' : '异常' }}</a-tag>
                </a-card>
            </a-col>
            <a-col :xs="24" :md="6">
                <a-card>
                    <a-statistic title="数据库状态" :value="health.db_ok ? 'OK' : 'FAIL'" />
                    <a-tag :color="health.db_ok ? 'green' : 'red'">{{ health.db_ok ? '正常' : '异常' }}</a-tag>
                </a-card>
            </a-col>
            <a-col :xs="24" :md="6">
                <a-card>
                    <a-statistic title="已注册抓取器" :value="health.fetchers_registered || 0" />
                </a-card>
            </a-col>
            <a-col :xs="24" :md="6">
                <a-card>
                    <a-statistic title="自动刷新" :value="autoupdate ? 'ON' : 'OFF'" />
                    <a-switch v-model="autoupdate" />
                </a-card>
            </a-col>
        </a-row>

        <a-alert
            v-if="health.db_error"
            type="error"
            show-icon
            :message="health.db_error"
            style="margin-top: 12px"
        />

        <a-card title="运行配置（只读）" style="margin-top: 12px">
            <a-descriptions size="small" :column="2" bordered>
                <a-descriptions-item label="数据库路径">{{ runtimeConfig.database_path || '-' }}</a-descriptions-item>
                <a-descriptions-item label="API监听">{{ runtimeConfig.api_host }}:{{ runtimeConfig.api_port }}</a-descriptions-item>
                <a-descriptions-item label="抓取轮询间隔">{{ runtimeConfig.proc_fetcher_sleep }}</a-descriptions-item>
                <a-descriptions-item label="验证轮询间隔">{{ runtimeConfig.proc_validator_sleep }}</a-descriptions-item>
                <a-descriptions-item label="验证线程数">{{ runtimeConfig.validate_thread_num }}</a-descriptions-item>
                <a-descriptions-item label="验证超时">{{ runtimeConfig.validate_timeout }}</a-descriptions-item>
                <a-descriptions-item label="验证URL">{{ runtimeConfig.validate_url || '-' }}</a-descriptions-item>
                <a-descriptions-item label="验证方法">{{ runtimeConfig.validate_method || '-' }}</a-descriptions-item>
                <a-descriptions-item label="RAW源文件">{{ runtimeConfig.raw_sources_file || '-' }}</a-descriptions-item>
                <a-descriptions-item label="RAW源请求超时">{{ runtimeConfig.raw_sources_timeout }}</a-descriptions-item>
            </a-descriptions>
        </a-card>

        <a-card title="危险操作（需要二次确认）" style="margin-top: 12px">
            <a-alert
                type="warning"
                show-icon
                message="危险操作会直接修改数据库。请先输入确认词，再点击按钮，并在弹窗中二次确认。"
                style="margin-bottom: 12px"
            />
            <a-row :gutter="12">
                <a-col :xs="24" :md="12">
                    <a-card size="small" title="清空抓取器统计">
                        <p>输入确认词：<code>CLEAR_FETCHERS_STATS</code></p>
                        <a-input
                            v-model="confirmFetchersStats"
                            placeholder="请输入确认词"
                            style="margin-bottom: 10px"
                        />
                        <a-popconfirm
                            title="确认清空抓取器统计？此操作不可撤销。"
                            ok-text="确认"
                            cancel-text="取消"
                            @confirm="clearFetchersStats"
                        >
                            <a-button type="danger" :disabled="confirmFetchersStats !== 'CLEAR_FETCHERS_STATS'">
                                清空抓取器统计
                            </a-button>
                        </a-popconfirm>
                    </a-card>
                </a-col>
                <a-col :xs="24" :md="12">
                    <a-card size="small" title="清空代理池">
                        <p>输入确认词：<code>CLEAR_PROXIES</code></p>
                        <a-input
                            v-model="confirmProxies"
                            placeholder="请输入确认词"
                            style="margin-bottom: 10px"
                        />
                        <a-popconfirm
                            title="确认清空全部代理？此操作不可撤销。"
                            ok-text="确认"
                            cancel-text="取消"
                            @confirm="clearProxies"
                        >
                            <a-button type="danger" :disabled="confirmProxies !== 'CLEAR_PROXIES'">
                                清空代理池
                            </a-button>
                        </a-popconfirm>
                    </a-card>
                </a-col>
            </a-row>
        </a-card>
    </div>
</template>

<script>
export default {
    data () {
        return {
            autoupdate: true,
            timer: null,
            health: {},
            runtimeConfig: {},
            confirmFetchersStats: '',
            confirmProxies: ''
        };
    },
    mounted () {
        this.refresh();
        this.timer = setInterval(() => {
            if (this.autoupdate) {
                this.refresh();
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
        async refresh () {
            const [health, summary] = await Promise.all([
                this.$http.get('/admin/health'),
                this.$http.get('/admin/summary')
            ]);
            this.health = health || {};
            this.runtimeConfig = (summary && summary.runtime_config) || {};
        },
        async clearFetchersStats () {
            await this.$http.post('/admin/maintenance/clear_fetchers_stats', {}, {
                confirm_text: this.confirmFetchersStats
            });
            this.$message.success('抓取器统计已清空');
            this.confirmFetchersStats = '';
            await this.refresh();
        },
        async clearProxies () {
            await this.$http.post('/admin/maintenance/clear_proxies', {}, {
                confirm_text: this.confirmProxies
            });
            this.$message.success('代理池已清空');
            this.confirmProxies = '';
            await this.refresh();
        }
    }
};
</script>

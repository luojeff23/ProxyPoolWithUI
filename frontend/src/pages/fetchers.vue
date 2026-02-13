<template>
    <div>
        <a-row :gutter="12">
            <a-col :xs="24" :md="6">
                <a-card>
                    <a-statistic title="抓取器总数" :value="fetchers.length" />
                </a-card>
            </a-col>
            <a-col :xs="24" :md="6">
                <a-card>
                    <a-statistic title="已启用抓取器" :value="enabledCount" />
                </a-card>
            </a-col>
            <a-col :xs="24" :md="6">
                <a-card>
                    <a-statistic title="自动刷新" :value="autoupdate ? 'ON' : 'OFF'" />
                    <a-switch v-model="autoupdate" />
                </a-card>
            </a-col>
            <a-col :xs="24" :md="6">
                <a-card>
                    <div>上次刷新：{{ lastupdate || '-' }}</div>
                    <div style="margin-top: 8px">
                        <a-input
                            v-model="confirmText"
                            placeholder="输入 CLEAR_FETCHERS_STATS"
                            size="small"
                            style="margin-bottom: 8px"
                        />
                        <a-popconfirm
                            title="确认清空抓取器统计？"
                            ok-text="确认"
                            cancel-text="取消"
                            @confirm="clearStatus"
                        >
                            <a-button
                                type="danger"
                                size="small"
                                :disabled="confirmText !== 'CLEAR_FETCHERS_STATS'"
                            >
                                清空统计
                            </a-button>
                        </a-popconfirm>
                    </div>
                </a-card>
            </a-col>
        </a-row>

        <a-table
            style="margin-top: 12px"
            :columns="columns"
            :data-source="fetchers"
            row-key="name"
            :pagination="false"
            :loading="loading"
            :bordered="true"
        >
            <span slot="enable" slot-scope="enable, record">
                <a-switch :checked="enable" @change="(checked) => enableChange(record, checked)" />
            </span>
        </a-table>
    </div>
</template>

<script>
import moment from 'moment';

const columns = [
    {
        title: '名称',
        dataIndex: 'name'
    },
    {
        title: '当前可用代理数量',
        dataIndex: 'validated_cnt',
        width: 140
    },
    {
        title: '数据库中的代理数量',
        dataIndex: 'in_db_cnt',
        width: 150
    },
    {
        title: '总共爬取代理数量',
        dataIndex: 'sum_proxies_cnt',
        width: 150
    },
    {
        title: '上次爬取代理数量',
        dataIndex: 'last_proxies_cnt',
        width: 150
    },
    {
        title: '上次爬取时间',
        dataIndex: 'last_fetch_date',
        width: 180,
        customRender: (date) => {
            return date ? moment(date).format('YYYY-MM-DD HH:mm:ss') : '-';
        }
    },
    {
        title: '启用',
        dataIndex: 'enable',
        width: 90,
        scopedSlots: { customRender: 'enable' }
    }
];

export default {
    data () {
        return {
            fetchers: [],
            columns,
            autoupdate: true,
            lastupdate: '',
            loading: false,
            confirmText: '',
            handle: null
        };
    },
    computed: {
        enabledCount () {
            return this.fetchers.filter(item => item.enable).length;
        }
    },
    mounted () {
        this.handle = setInterval(() => {
            if (this.autoupdate) {
                this.update();
            }
        }, 3000);
        this.update();
    },
    destroyed () {
        if (this.handle) {
            clearInterval(this.handle);
        }
        this.handle = null;
    },
    methods: {
        async update () {
            this.loading = true;
            try {
                const data = await this.$http.get('/admin/summary');
                this.fetchers = data.fetchers || [];
                this.lastupdate = moment().format('HH:mm:ss');
            } finally {
                this.loading = false;
            }
        },
        async clearStatus () {
            await this.$http.post('/admin/maintenance/clear_fetchers_stats', {}, {
                confirm_text: this.confirmText
            });
            this.$message.success('抓取器统计已清空');
            this.confirmText = '';
            await this.update();
        },
        async enableChange (fetcher, checked) {
            await this.$http.get('/fetcher_enable', {
                name: fetcher.name,
                enable: checked ? '1' : '0'
            });
            this.$message.success('修改成功');
            await this.update();
        }
    }
};
</script>

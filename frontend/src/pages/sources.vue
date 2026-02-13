<template>
    <div>
        <a-card :bordered="false" title="代理源配置">
            <a-alert
                type="info"
                show-icon
                message="每行一个源，支持“protocol,url”或“url”格式。空行和 # 注释会被忽略。"
                style="margin-bottom: 12px"
            />
            <a-row :gutter="12" style="margin-bottom: 12px">
                <a-col :xs="24" :md="12">
                    <a-descriptions size="small" :column="1">
                        <a-descriptions-item label="配置文件路径">
                            <code>{{ filePath || '-' }}</code>
                        </a-descriptions-item>
                        <a-descriptions-item label="有效源数量">
                            {{ validSourceCount }}
                        </a-descriptions-item>
                    </a-descriptions>
                </a-col>
                <a-col :xs="24" :md="12" style="text-align: right">
                    <a-button icon="reload" @click="loadSources">重新加载</a-button>
                    <a-button
                        type="primary"
                        icon="save"
                        :loading="saving"
                        style="margin-left: 8px"
                        @click="saveSources"
                    >
                        校验并保存
                    </a-button>
                </a-col>
            </a-row>
            <a-textarea
                v-model="editorText"
                :auto-size="{ minRows: 14, maxRows: 24 }"
                placeholder="例如：https://example.com/http.txt 或 socks5,https://example.com/socks5.txt"
                @input="revalidate"
            />
        </a-card>

        <a-card v-if="invalidLines.length > 0" title="本地校验发现的问题" style="margin-top: 12px">
            <a-table
                :columns="invalidColumns"
                :data-source="invalidLines"
                :pagination="{ pageSize: 8 }"
                row-key="line_no"
                size="small"
            />
        </a-card>
    </div>
</template>

<script>
const ALLOWED_PROTOCOLS = ['http', 'https', 'socks4', 'socks5', 'auto'];

const invalidColumns = [
    { title: '行号', dataIndex: 'line_no', width: 100 },
    { title: '内容', dataIndex: 'line' },
    { title: '问题', dataIndex: 'message', width: 260 }
];

export default {
    data () {
        return {
            invalidColumns,
            filePath: '',
            editorText: '',
            validSourceCount: 0,
            invalidLines: [],
            saving: false
        };
    },
    mounted () {
        this.loadSources();
    },
    methods: {
        parseLines () {
            const lines = this.editorText.replace(/\r\n/g, '\n').split('\n');
            const invalid = [];
            let validCount = 0;

            lines.forEach((line, index) => {
                const lineNo = index + 1;
                const text = line.trim();
                if (text === '' || text.startsWith('#')) {
                    return;
                }
                validCount += 1;

                let protocol = 'http';
                let url = text;
                if (text.includes(',')) {
                    const parts = text.split(',');
                    protocol = (parts.shift() || '').trim().toLowerCase();
                    url = parts.join(',').trim();
                    if (!ALLOWED_PROTOCOLS.includes(protocol)) {
                        invalid.push({
                            line_no: lineNo,
                            line,
                            message: `协议不合法: ${protocol}`
                        });
                        return;
                    }
                }

                if (!/^https?:\/\//i.test(url)) {
                    invalid.push({
                        line_no: lineNo,
                        line,
                        message: `URL必须以http(s)开头: ${url}`
                    });
                }
            });

            return {
                lines,
                validCount,
                invalid
            };
        },
        revalidate () {
            const data = this.parseLines();
            this.validSourceCount = data.validCount;
            this.invalidLines = data.invalid;
        },
        async loadSources () {
            const data = await this.$http.get('/admin/sources');
            this.filePath = data.file_path || '';
            this.editorText = (data.lines || []).join('\n');
            this.revalidate();
        },
        async saveSources () {
            const data = this.parseLines();
            this.validSourceCount = data.validCount;
            this.invalidLines = data.invalid;

            if (this.invalidLines.length > 0) {
                this.$message.error(`有 ${this.invalidLines.length} 行配置不合法，请先修正`);
                return;
            }

            this.saving = true;
            try {
                const resp = await this.$http.put('/admin/sources', {}, {
                    lines: data.lines
                });
                this.$message.success(`保存成功，有效源 ${resp.valid_count} 条`);
                await this.loadSources();
            } finally {
                this.saving = false;
            }
        }
    }
};
</script>

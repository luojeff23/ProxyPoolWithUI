<template>
    <a-config-provider :locale="locale">
        <a-layout class="layout-main">
            <a-layout-sider collapsible :width="224" class="sider-shell">
                <div class="logo">
                    <div class="logo-main">Proxy Console</div>
                    <div class="logo-sub">All-in-one 管理台</div>
                </div>
                <a-menu v-model="urlPath" theme="dark" mode="inline">
                    <a-menu-item key="/dashboard">
                        <NuxtLink to="/dashboard">
                            <a-icon type="dashboard" />
                            <span>控制台总览</span>
                        </NuxtLink>
                    </a-menu-item>
                    <a-menu-item key="/proxies">
                        <NuxtLink to="/proxies">
                            <a-icon type="database" />
                            <span>代理池管理</span>
                        </NuxtLink>
                    </a-menu-item>
                    <a-menu-item key="/sources">
                        <NuxtLink to="/sources">
                            <a-icon type="link" />
                            <span>代理源管理</span>
                        </NuxtLink>
                    </a-menu-item>
                    <a-menu-item key="/fetchers">
                        <NuxtLink to="/fetchers">
                            <a-icon type="retweet" />
                            <span>抓取器管理</span>
                        </NuxtLink>
                    </a-menu-item>
                    <a-menu-item key="/system">
                        <NuxtLink to="/system">
                            <a-icon type="setting" />
                            <span>系统与维护</span>
                        </NuxtLink>
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item key="github">
                        <a href="https://github.com/OxOOo/ProxyPoolWithUI" target="_blank">
                            <a-icon type="github" />
                            <span>Github主页</span>
                        </a>
                    </a-menu-item>
                </a-menu>
            </a-layout-sider>
            <a-layout>
                <a-layout-header class="header-shell">
                    <div class="header-title">{{ pageTitle }}</div>
                    <div class="header-sub">Web 控制台模式</div>
                </a-layout-header>
                <a-layout-content class="content-shell">
                    <Nuxt />
                </a-layout-content>
            </a-layout>
        </a-layout>
    </a-config-provider>
</template>

<script>
import zh_CN from 'ant-design-vue/lib/locale-provider/zh_CN';
import moment from 'moment';

moment.locale('zh-cn');

export default {
    data () {
        return {
            locale: zh_CN,
            urlPath: []
        };
    },
    computed: {
        pageTitle () {
            const map = {
                '/dashboard': '控制台总览',
                '/proxies': '代理池管理',
                '/sources': '代理源管理',
                '/fetchers': '抓取器管理',
                '/system': '系统与维护'
            };
            return map[this.urlPath[0]] || 'Proxy Console';
        }
    },
    watch: {
        $route () {
            this.updateNav();
        }
    },
    mounted () {
        this.updateNav();
    },
    methods: {
        updateNav () {
            const data = /^\/[^/]*/.exec(this.$route.path || '');
            if (data) {
                this.urlPath = [data[0]];
            } else {
                this.urlPath = [];
            }
        }
    }
};
</script>

<style scoped>
.layout-main {
    min-height: 100vh;
    background: #111827;
}
.logo {
    margin: 14px 14px 18px;
    padding: 12px 14px;
    border-radius: 8px;
    background: linear-gradient(135deg, #1f2937, #111827);
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.logo-main {
    color: #f9fafb;
    font-weight: 700;
    letter-spacing: 0.4px;
}
.logo-sub {
    color: #93c5fd;
    margin-top: 2px;
    font-size: 12px;
}
.sider-shell {
    box-shadow: 4px 0 14px rgba(0, 0, 0, 0.2);
}
.header-shell {
    background: #f9fafb;
    padding: 0 18px;
    height: 60px;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header-title {
    font-size: 17px;
    font-weight: 600;
    color: #111827;
}
.header-sub {
    color: #4b5563;
    font-size: 13px;
}
.content-shell {
    margin: 16px;
    padding: 16px;
    background: #ffffff;
    border-radius: 8px;
    min-height: calc(100vh - 92px);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
</style>

<style>
html {
  font-family:
    'Source Sans Pro',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    'Helvetica Neue',
    Arial,
    sans-serif;
  font-size: 16px;
  word-spacing: 1px;
  -ms-text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
  -moz-osx-font-smoothing: grayscale;
  -webkit-font-smoothing: antialiased;
  box-sizing: border-box;
}
</style>

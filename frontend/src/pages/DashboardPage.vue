<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { api } from "../api";
const data = ref(null); const error = ref(""); const loading = ref(true);
async function load() { loading.value = true; error.value = ""; try { data.value = await api("/dashboard"); } catch (e) { error.value = e.message; } finally { loading.value = false; } }
onMounted(() => { load(); window.addEventListener("demo-identity-changed", load); }); onUnmounted(() => window.removeEventListener("demo-identity-changed", load));
</script>

<template>
  <div class="page-stack">
    <section class="welcome-row"><div><div class="eyebrow">OPERATIONS OVERVIEW</div><h2>售后运营概览</h2><p>指标来自当前演示身份可访问的运行记录，不包含其他用户或租户数据。</p></div><button class="button button-secondary" @click="load">↻ 更新</button></section>
    <div v-if="loading" class="state-card">正在读取工作区数据…</div><div v-else-if="error" class="state-card state-error">{{ error }} <button @click="load">重试</button></div>
    <template v-else-if="data">
      <section class="metric-grid">
        <article class="metric-card"><span>Agent 执行</span><strong>{{ data.runs.total }}</strong><small>当前用户 · 当前租户</small></article>
        <article class="metric-card"><span>成功完成</span><strong>{{ data.runs.completed }}</strong><small>来自 SQLite 运行记录</small></article>
        <article class="metric-card"><span>执行失败</span><strong>{{ data.runs.failed }}</strong><small>仅计已记录失败</small></article>
        <article class="metric-card"><span>待审批</span><strong>{{ data.pending_approvals }}</strong><small>当前审批人被分配的任务</small></article>
      </section>
      <section class="content-card"><div class="section-heading"><div><h3>最近运行</h3><p>可在记录中区分一次运行 Trace 与跨步骤 Thread。</p></div><RouterLink class="text-link" to="/observability">查看运行 →</RouterLink></div>
        <div v-if="!data.recent_runs.length" class="empty-state"><span class="empty-mark">⌁</span><strong>还没有运行记录</strong><p>前往智能客服发起一次演示问题，这里会显示真实记录。</p><RouterLink class="button button-primary" to="/chat">打开智能客服</RouterLink></div>
        <div v-else class="table-wrap"><table><thead><tr><th>运行 ID</th><th>意图</th><th>状态</th><th>开始时间</th></tr></thead><tbody><tr v-for="run in data.recent_runs" :key="run.run_id"><td class="mono">{{ run.run_id.slice(0, 12) }}…</td><td>{{ run.intent || "待路由" }}</td><td><span class="status-pill" :class="`status-${run.status}`">{{ run.status }}</span></td><td>{{ new Date(run.started_at).toLocaleString() }}</td></tr></tbody></table></div>
      </section>
      <section class="metric-note"><span class="notice-icon">i</span><div><strong>未采集的指标不会显示估算值</strong><p>平均耗时、Token 用量和最近 Bad Case 尚未持久化到本地数据，因此暂不绘制图表。</p></div></section>
    </template>
  </div>
</template>

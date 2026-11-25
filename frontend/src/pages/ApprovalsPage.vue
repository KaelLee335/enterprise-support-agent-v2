<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { api } from "../api";
const tasks = ref([]), history = ref([]), details = ref({}), loading = ref(true), error = ref(""), busy = ref("");
async function load() { loading.value = true; error.value = ""; try { [tasks.value, history.value] = await Promise.all([api("/approvals"), api("/approvals/history")]); } catch (e) { error.value = e.message; } finally { loading.value = false; } }
async function decide(task, approved) { busy.value = task.thread_id; error.value = ""; try { await api(`/approvals/${encodeURIComponent(task.thread_id)}/decision`, { method: "POST", body: JSON.stringify({ approved }) }); await load(); } catch (e) { error.value = e.message; } finally { busy.value = ""; } }
async function showDetails(task) { if (details.value[task.thread_id]) { details.value[task.thread_id] = null; return; } busy.value = task.thread_id; try { details.value[task.thread_id] = await api(`/approvals/${encodeURIComponent(task.thread_id)}`); } catch (e) { error.value = e.message; } finally { busy.value = ""; } }
onMounted(() => { load(); window.addEventListener("demo-identity-changed", load); }); onUnmounted(() => window.removeEventListener("demo-identity-changed", load));
</script>
<template>
  <div class="page-stack">
    <section class="welcome-row"><div><div class="eyebrow">HUMAN IN THE LOOP</div><h2>人工审批中心</h2><p>任务从 SQLite 按当前审批人和租户读取；批准只记录演示决定，不执行退款。</p></div><button class="button button-secondary" @click="load">↻ 刷新</button></section>
    <div v-if="loading" class="state-card">正在读取审批任务…</div><div v-else-if="error" class="state-card state-error">{{error}}<p>此页面仅授权审批人访问任务。</p></div>
    <template v-else>
      <section class="content-card"><div class="section-heading"><div><h3>待处理任务 <span class="count-badge">{{tasks.length}}</span></h3><p>仅本人被分配且仍处于待审批状态的任务。</p></div></div>
        <div v-if="!tasks.length" class="empty-state"><span class="empty-mark">✓</span><strong>当前没有待处理任务</strong><p>新任务会由后端审批接口进行分配与授权。</p></div>
        <div v-else class="approval-list"><article v-for="task in tasks" :key="task.task_id" class="approval-card"><div class="approval-title"><div><span class="status-pill status-pending">待审批</span><h4>订单 {{task.order_id}} · 售后演示申请</h4></div><small>{{new Date(task.created_at).toLocaleString()}}</small></div>
          <dl class="approval-meta"><div><dt>请求人</dt><dd>{{task.requester_id}}</dd></div><div><dt>Thread ID</dt><dd class="mono">{{task.thread_id}}</dd></div></dl>
          <button class="text-button" :disabled="busy===task.thread_id" @click="showDetails(task)">{{details[task.thread_id]?'收起上下文':'查看请求与 Agent 依据'}}</button>
          <div v-if="details[task.thread_id]" class="approval-context"><p><b>请求内容</b><br>{{details[task.thread_id].question||'当前快照无请求文本'}}</p><p><b>Agent 当前答复</b><br>{{details[task.thread_id].answer}}</p><p v-if="details[task.thread_id].order"><b>订单状态</b><br>{{details[task.thread_id].order.status}} · {{details[task.thread_id].order.product}}</p><p v-for="ev in details[task.thread_id].evidence||[]" :key="ev.source_id"><b>{{ev.source_id}} · {{ev.title}}</b><br>{{ev.content}}</p></div>
          <p class="muted">审批决定由后端重新校验当前任务分配；批准只记为演示状态，不执行退款。</p><div class="button-row"><button class="button button-primary" :disabled="busy===task.thread_id" @click="decide(task,true)">演示批准</button><button class="button button-danger" :disabled="busy===task.thread_id" @click="decide(task,false)">拒绝</button></div>
        </article></div>
      </section>
      <section class="content-card"><div class="section-heading"><div><h3>本人审批历史</h3><p>同一审批人可见的已分配任务。</p></div></div><div v-if="!history.length" class="empty-inline">暂无审批历史。</div><div v-else class="table-wrap"><table><thead><tr><th>任务</th><th>订单</th><th>状态</th><th>决定</th><th>更新时间</th></tr></thead><tbody><tr v-for="t in history" :key="t.task_id"><td class="mono">{{t.task_id.slice(0,12)}}…</td><td>{{t.order_id}}</td><td>{{t.status}}</td><td>{{t.decision || "—"}}</td><td>{{new Date(t.updated_at).toLocaleString()}}</td></tr></tbody></table></div></section>
    </template>
  </div>
</template>

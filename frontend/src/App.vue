<script setup>
import { computed, ref } from "vue";

const token = ref(localStorage.getItem("demo-token") || "demo-a-local-token");
const role = ref(localStorage.getItem("demo-role") || "requester");
const activeRole = ref(role.value);
const question = ref("");
const loading = ref(false);
const error = ref("");
const conversations = ref({ requester: [], approver: [] });
const messages = ref(conversations.value[role.value] || []);
const pending = ref(null);
const suggestions = ["查询订单1001", "退款多久能到账？", "定制商品有质量问题怎么办？", "帮我申请订单1001退款"];
const ready = computed(() => Boolean(token.value.trim()) && !loading.value);

function authHeaders() {
  localStorage.setItem("demo-role", role.value);
  localStorage.setItem("demo-token", token.value.trim());
  return { Authorization: `Bearer ${token.value.trim()}`, "Content-Type": "application/json" };
}

async function ask(text = question.value) {
  const prompt = text.trim();
  if (!prompt || !ready.value) return;
  question.value = "";
  error.value = "";
  messages.value.push({ role: "user", text: prompt });
  loading.value = true;
  try {
    const response = await fetch("/api/chat", { method: "POST", headers: authHeaders(), body: JSON.stringify({ question: prompt }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `请求失败 (${response.status})`);
    messages.value.push({ role: "assistant", data });
    if (data.approval_status === "pending" && data.thread_id) pending.value = data;
  } catch (e) {
    error.value = `${e.message}。确认 FastAPI 服务已启动后重试。`;
  } finally {
    loading.value = false;
  }
}

async function decide(approved) {
  if (!pending.value) return;
  loading.value = true;
  error.value = "";
  try {
    const response = await fetch(`/api/approvals/${encodeURIComponent(pending.value.thread_id)}/decision`, {
      method: "POST", headers: authHeaders(), body: JSON.stringify({ approved }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `审批请求失败 (${response.status})`);
    const decisionMessage = { role: "assistant", data: { answer: data.answer, intent: "approval", approval_status: data.approval_status, thread_id: data.thread_id } };
    messages.value.push(decisionMessage);
    conversations.value.approver = messages.value;
    const requesterMessage = [...conversations.value.requester].reverse().find(
      (message) => message.role === "assistant" && message.data.thread_id === data.thread_id,
    );
    if (requesterMessage) {
      requesterMessage.data.answer = data.answer;
      requesterMessage.data.approval_status = data.approval_status;
    }
    pending.value = null;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function selectRole() {
  if (loading.value) {
    role.value = activeRole.value;
    return;
  }
  conversations.value[activeRole.value] = messages.value;
  activeRole.value = role.value;
  messages.value = conversations.value[activeRole.value] || [];
  token.value = role.value === "approver" ? "demo-a-approver-local-token" : "demo-a-local-token";
  localStorage.setItem("demo-role", role.value);
  localStorage.setItem("demo-token", token.value);
}
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <a class="brand" href="#"><span class="brand-mark">S</span><span>Support<span class="brand-light">Agent</span></span></a>
      <div class="demo-badge"><i></i> 本地演示环境</div>
    </header>

    <section class="hero">
      <div class="eyebrow">ENTERPRISE SUPPORT · V2</div>
      <h1>售后问题，交给智能助手</h1>
      <p>查询演示订单、了解售后政策，或提交一个仅供演示的退款审批请求。</p>
    </section>

    <section class="workspace">
      <div class="chat-panel">
        <div class="panel-heading"><div><strong>对话</strong><span>基于订单数据与政策知识库</span></div><span class="online"><i></i> API</span></div>
        <div class="conversation" aria-live="polite">
          <div v-if="messages.length === 0" class="welcome"><div class="sparkle">✳</div><h2>{{ role === 'approver' ? (pending ? '有一笔待审批任务' : '当前没有待审批任务') : '你好，需要什么帮助？' }}</h2><p>{{ role === 'approver' ? (pending ? '请查看下方任务卡并决定；批准只记录演示状态。' : '先切换到请求人，发送“帮我申请订单1001退款”，再切回审批人处理任务。') : '试试查询订单，或询问退货、退款和质量问题。' }}</p><div v-if="role === 'requester'" class="suggestions"><button v-for="item in suggestions" :key="item" @click="ask(item)">{{ item }} <span>↗</span></button></div></div>
          <template v-for="(message, index) in messages" :key="index">
            <div v-if="message.role === 'user'" class="user-message">{{ message.text }}</div>
            <article v-else class="assistant-message"><div class="assistant-avatar">S</div><div class="answer-card"><div class="answer-meta">Support Agent <span>{{ message.data.intent }}</span></div><p>{{ message.data.answer }}</p>
              <div v-if="message.data.order" class="order-card"><div class="order-title">订单 {{ message.data.order.order_id }} <span>{{ message.data.order.status }}</span></div><div>{{ message.data.order.product }} · {{ message.data.order.issue_description || '演示数据' }}</div></div>
              <div v-if="message.data.shipment" class="order-card"><div class="order-title">模拟物流 <span>{{ message.data.shipment.status }}</span></div><div>运单 {{ message.data.shipment.tracking_number }} · {{ message.data.shipment.demo_only ? '虚构数据' : '' }}</div><ul><li v-for="(event, eventIndex) in message.data.shipment.events" :key="eventIndex">{{ event.time }} · {{ event.status }} · {{ event.location }}</li></ul></div>
              <div v-if="message.data.citations?.length" class="citations">引用政策：<span v-for="cite in message.data.citations" :key="cite">{{ cite }}</span><small v-if="message.data.citations_valid === false">引用校验未通过</small></div>
              <details v-if="message.data.evidence?.length" class="evidence"><summary>查看政策依据（{{ message.data.evidence.length }}）</summary><div v-for="item in message.data.evidence" :key="item.source_id" class="evidence-item"><b>{{ item.source_id }} · {{ item.title }}</b><p>{{ item.content }}</p></div></details>
              <div v-if="message.data.approval_status" class="status-line">演示审批状态：{{ message.data.approval_status }}</div>
              <small class="trace">运行 {{ message.data.run_id || message.data.thread_id || '—' }} · 追踪 {{ message.data.trace_id || '—' }}</small>
            </div></article>
          </template>
          <div v-if="loading" class="typing"><i></i><i></i><i></i><span>正在处理</span></div>
          <div v-if="pending" class="approval-box"><strong>待处理演示审批</strong><p>订单 {{ pending.pending_action?.order_id || '—' }} 的退款申请。请求人与审批人的对话分开显示；这张待审批任务卡会保留给审批人处理。</p><div class="order-title">原订单状态：{{ pending.pending_action?.order_status || '—' }} <span>{{ pending.approval_status }}</span></div><div v-if="role === 'approver'"><button class="approve" :disabled="loading" @click="decide(true)">演示批准</button><button class="reject" :disabled="loading" @click="decide(false)">拒绝</button></div><small v-else>当前为请求人身份，不能审批自己的请求。</small></div>
        </div>
        <div v-if="error" class="error-banner">{{ error }}</div>
        <form class="composer" @submit.prevent="ask()"><textarea v-model="question" rows="1" maxlength="4000" placeholder="输入你的售后问题…" @keydown.enter.exact.prevent="ask()"></textarea><button class="send" :disabled="!question.trim() || loading" aria-label="发送">↑</button><small>Enter 发送 · 内容会发送至当前配置的模型服务</small></form>
      </div>

      <aside class="side-panel"><div class="side-card"><div class="side-icon">⌘</div><h3>演示身份</h3><p>固定映射的本地演示身份，不是真实认证。请求人与审批人为两个同租户虚构用户。</p><label for="role">当前角色</label><select id="role" v-model="role" :disabled="loading" @change="selectRole"><option value="requester">请求人（demo-a）</option><option value="approver">审批人（demo-a）</option></select><label for="token">Demo Token</label><input id="token" v-model="token" type="password" autocomplete="off" placeholder="本地演示令牌"/><small>两种角色各自保留独立对话；待审批任务会跨角色显示。仅发送给当前本地 API。物流信息来自本机模拟 HTTP 服务。</small></div><div class="side-card flow-card"><h3>处理流程</h3><ol><li>确定性规则识别意图</li><li>订单只读查询、政策 RAG 或模拟物流 API</li><li>返回答复、证据或轨迹</li><li>退款请求暂停，独立演示身份作出决定</li></ol></div><div class="demo-note">演示项目 · 使用虚构数据<br/>物流服务为本地 mock · 不调用商业快递 API</div></aside>
    </section>
    <footer>Enterprise Support Agent V2 <span>用于学习与本地演示</span></footer>
  </main>
</template>

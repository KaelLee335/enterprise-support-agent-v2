<script setup>
import { computed, ref } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

const route = useRoute();
const role = ref(localStorage.getItem("demo-role") || "requester");
const token = ref(localStorage.getItem("demo-token") || "demo-a-local-token");
const pageTitle = computed(() => ({ dashboard: "工作台", chat: "智能客服", orders: "订单管理", approvals: "人工审批", knowledge: "知识库", evaluation: "评估中心", observability: "可观测性" }[route.name] || "工作台"));
function switchRole() {
  token.value = role.value === "approver" ? "demo-a-approver-local-token" : role.value === "requester-b" ? "demo-b-local-token" : "demo-a-local-token";
  localStorage.setItem("demo-role", role.value);
  localStorage.setItem("demo-token", token.value);
  window.dispatchEvent(new CustomEvent("demo-identity-changed"));
}
</script>

<template>
  <div class="app-frame">
    <aside class="sidebar">
      <RouterLink class="brand" to="/dashboard"><span class="brand-mark">S</span><span>Support<span class="brand-light">Agent</span></span></RouterLink>
      <div class="nav-caption">工作区</div>
      <nav class="primary-nav">
        <RouterLink to="/dashboard"><span class="nav-icon">▦</span>工作台</RouterLink>
        <RouterLink to="/chat"><span class="nav-icon">◌</span>智能客服</RouterLink>
        <RouterLink to="/orders"><span class="nav-icon">▤</span>订单管理</RouterLink>
        <RouterLink to="/approvals"><span class="nav-icon">✓</span>人工审批</RouterLink>
        <RouterLink to="/knowledge"><span class="nav-icon">▱</span>RAG 知识库</RouterLink>
        <RouterLink to="/evaluation"><span class="nav-icon">⌁</span>评估中心</RouterLink>
        <RouterLink to="/observability"><span class="nav-icon">⌘</span>可观测性</RouterLink>
      </nav>
      <div class="sidebar-bottom"><span class="status-dot"></span><span>本地演示环境</span><small>V2 · 虚构业务数据</small></div>
    </aside>
    <main class="main-area">
      <header class="main-header"><div><div class="breadcrumbs">Enterprise Support Agent <span>/</span> {{ pageTitle }}</div><h1>{{ pageTitle }}</h1></div>
        <div class="identity-switch"><span class="identity-dot"></span><select v-model="role" aria-label="切换演示身份" @change="switchRole"><option value="requester">请求人 · demo-a</option><option value="requester-b">请求人 · demo-b</option><option value="approver">审批人 · demo-a</option></select><span class="demo-label">DEMO</span></div>
      </header>
      <div class="page-content"><RouterView :key="route.fullPath" /></div>
      <footer class="app-footer">Enterprise Support Agent V2 <span>用于学习与本地演示 · 不连接真实电商平台</span></footer>
    </main>
  </div>
</template>

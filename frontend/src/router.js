import { createRouter, createWebHistory } from "vue-router";
import DashboardPage from "./pages/DashboardPage.vue";
import ChatWorkspace from "./ChatWorkspace.vue";
import OrdersPage from "./pages/OrdersPage.vue";
import ApprovalsPage from "./pages/ApprovalsPage.vue";
import KnowledgePage from "./pages/KnowledgePage.vue";
import EvaluationPage from "./pages/EvaluationPage.vue";
import ObservabilityPage from "./pages/ObservabilityPage.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    { path: "/dashboard", name: "dashboard", component: DashboardPage },
    { path: "/chat", name: "chat", component: ChatWorkspace },
    { path: "/orders", name: "orders", component: OrdersPage },
    { path: "/approvals", name: "approvals", component: ApprovalsPage },
    { path: "/knowledge", name: "knowledge", component: KnowledgePage },
    { path: "/evaluation", name: "evaluation", component: EvaluationPage },
    { path: "/observability", name: "observability", component: ObservabilityPage },
  ],
  scrollBehavior: () => ({ top: 0 }),
});

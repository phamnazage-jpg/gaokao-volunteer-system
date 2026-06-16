const TOKEN_KEY = "gaokao_admin_dashboard_token";

const state = {
  charts: {},
  payload: null,
  range: "7d",
  loading: false,
};

function resolveApiBase() {
  const raw = document.getElementById("api-base").value.trim();
  return raw || window.location.origin;
}

function formatMoney(cents) {
  return `¥${(Number(cents || 0) / 100).toFixed(2)}`;
}

function setMessage(text, tone) {
  const el = document.getElementById("message");
  el.textContent = text;
  el.className = "message" + (tone ? " " + tone : "");
}

function setError(text) {
  const el = document.getElementById("error");
  el.textContent = text || "";
}

function setStatus(state_, title, meta) {
  const dot = document.getElementById("status-dot");
  const titleEl = document.getElementById("status-title");
  const metaEl = document.getElementById("status-meta");
  const wrap = document.getElementById("system-status");
  dot.className = "status-dot " + state_;
  titleEl.textContent = title;
  metaEl.textContent = meta;
  wrap.className = "system-status " + state_;
}

function markCardsLoading() {
  document.querySelectorAll("[data-card]").forEach((card) => {
    card.classList.remove("empty");
    card.classList.add("loading");
  });
}

function markCardsEmpty() {
  document.querySelectorAll("[data-card]").forEach((card) => {
    card.classList.remove("loading");
    card.classList.add("empty");
  });
}

function setChartEmpty(chartId, label) {
  const node = document.getElementById(chartId);
  if (!node) return;
  node.innerHTML = `<div class="chart-empty"><span class="label">${label || "等待加载数据"}</span></div>`;
  delete state.charts[chartId];
}

function getToken() {
  return document.getElementById("token").value.trim();
}

function setToken(token) {
  document.getElementById("token").value = token || "";
  if (token) {
    window.sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    window.sessionStorage.removeItem(TOKEN_KEY);
  }
}

async function loginAndStoreToken() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  if (!username || !password) {
    throw new Error("请输入用户名和密码，或直接粘贴 Bearer Token。");
  }

  const resp = await fetch(`${resolveApiBase()}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!resp.ok) {
    throw new Error(`登录失败: HTTP ${resp.status}`);
  }

  const body = await resp.json();
  if (!body.access_token) {
    throw new Error("登录响应缺少 access_token");
  }

  setToken(body.access_token);
  return body.access_token;
}

function renderSummary(summary) {
  const totalOrders = Number(summary.total_orders ?? 0);
  const totalRevenue = Number(summary.total_revenue_cents ?? 0);
  const totalUsers = Number(summary.total_users ?? 0);
  const ordersToday = Number(summary.orders_today ?? 0);
  const orders7d = Number(summary.orders_7d ?? 0);
  const orders30d = Number(summary.orders_30d ?? 0);

  document.getElementById("total-orders").textContent = String(totalOrders);
  document.getElementById("total-revenue").textContent =
    formatMoney(totalRevenue);
  document.getElementById("total-users").textContent = String(totalUsers);
  document.getElementById("orders-subtitle").textContent =
    `今日 ${ordersToday} / 7d ${orders7d} / 30d ${orders30d}`;
  document.getElementById("revenue-subtitle").textContent =
    `今日 ${formatMoney(summary.revenue_today_cents)} / 7d ${formatMoney(summary.revenue_7d_cents)} / 30d ${formatMoney(summary.revenue_30d_cents)}`;

  const pending = Number(summary.pending_orders ?? 0);
  document.getElementById("pending-orders").textContent = String(pending);
}

function clearCardEmptyStates() {
  document.querySelectorAll("[data-card]").forEach((card) => {
    card.classList.remove("empty");
    card.classList.remove("loading");
  });
}

function ensureChart(id) {
  const host = document.getElementById(id);
  if (!host) return null;
  if (!state.charts[id]) {
    state.charts[id] = echarts.init(host);
  }
  return state.charts[id];
}

function renderTrend(trends) {
  const points = Array.isArray(trends?.[state.range])
    ? trends?.[state.range]
    : [];
  if (points.length === 0) {
    setChartEmpty(
      "trend-chart",
      state.range === "30d" ? "近 30 天暂无订单活动" : "近 7 天暂无订单活动",
    );
    document.getElementById("trend-title").textContent =
      state.range === "30d" ? "30 天趋势" : "7 天趋势";
    return;
  }
  const chart = ensureChart("trend-chart");
  document.getElementById("trend-title").textContent =
    state.range === "30d" ? "30 天趋势" : "7 天趋势";
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["订单数", "收入(元)"] },
    grid: { left: 48, right: 48, top: 48, bottom: 32 },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: points.map((item) => item.date),
    },
    yAxis: [
      { type: "value", name: "订单数" },
      { type: "value", name: "收入(元)" },
    ],
    series: [
      {
        name: "订单数",
        type: "line",
        smooth: true,
        data: points.map((item) => item.orders ?? 0),
      },
      {
        name: "收入(元)",
        type: "line",
        smooth: true,
        yAxisIndex: 1,
        data: points.map((item) => Number(item.revenue_cents ?? 0) / 100),
      },
    ],
  });
}

function renderBarChart(chartId, emptyLabel, dataMap, color) {
  const entries = Object.entries(dataMap || {});
  if (
    entries.length === 0 ||
    entries.every(([, value]) => Number(value || 0) === 0)
  ) {
    setChartEmpty(chartId, emptyLabel);
    return;
  }
  const chart = ensureChart(chartId);
  chart.setOption({
    tooltip: { trigger: "axis" },
    grid: { left: 48, right: 24, top: 32, bottom: 48 },
    xAxis: {
      type: "category",
      axisLabel: { interval: 0, rotate: entries.length > 4 ? 20 : 0 },
      data: entries.map(([label]) => label),
    },
    yAxis: { type: "value", minInterval: 1 },
    series: [
      {
        name: chartId,
        type: "bar",
        data: entries.map(([, value]) => value ?? 0),
        itemStyle: { color },
        barMaxWidth: 48,
      },
    ],
  });
}

function renderDistributions(payload) {
  renderBarChart(
    "status-chart",
    "暂无订单状态分布",
    payload.by_status,
    "#2563eb",
  );
  renderBarChart("source-chart", "暂无来源分布", payload.by_source, "#7c3aed");
  renderBarChart(
    "service-chart",
    "暂无服务版本分布",
    payload.by_service_version,
    "#059669",
  );
}

function updateRangeButtons() {
  const isThirty = state.range === "30d";
  document.getElementById("range-7d").className = isThirty
    ? "range-btn secondary"
    : "range-btn active-range";
  document.getElementById("range-30d").className = isThirty
    ? "range-btn active-range"
    : "range-btn secondary";
}

async function fetchDashboard(token) {
  const resp = await fetch(`${resolveApiBase()}/api/stats/dashboard`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!resp.ok) {
    throw new Error(`数据加载失败：HTTP ${resp.status}`);
  }
  return resp.json();
}

function renderDashboard(payload) {
  state.payload = payload;
  clearCardEmptyStates();
  renderSummary(payload.summary || {});
  renderTrend(payload.trends || {});
  renderDistributions(payload);
  updateRangeButtons();
  const generatedAt = payload.generated_at || "刚刚";
  document.getElementById("generated-at-hint")?.remove();
  setStatus(
    "online",
    "已连接 · 数据已加载",
    `更新时间：${generatedAt} · 数据范围：${state.range === "30d" ? "30 天" : "7 天"}`,
  );
}

async function loadDashboard({ loginFirst = false } = {}) {
  if (state.loading) return;
  state.loading = true;
  setError("");
  setMessage(loginFirst ? "登录中..." : "加载中...", "loading");
  setStatus(
    "loading",
    "正在连接...",
    loginFirst ? "正在登录并拉取数据" : "正在拉取最新数据",
  );
  markCardsLoading();

  try {
    let token = getToken();
    if (!token && loginFirst) {
      token = await loginAndStoreToken();
      setMessage("登录成功，开始加载仪表盘...", "success");
    }
    if (!token) {
      throw new Error("缺少 JWT，请先登录或粘贴 Bearer Token。");
    }

    const payload = await fetchDashboard(token);
    renderDashboard(payload);
    setMessage("仪表盘加载成功", "success");
  } catch (error) {
    setError(error.message || String(error));
    setMessage("加载失败，请检查认证或服务状态。", "error");
    setStatus("error", "连接失败", error.message || "请检查登录状态或刷新");
    markCardsEmpty();
    setChartEmpty("trend-chart", "登录后展示订单与收入趋势");
    setChartEmpty("status-chart", "暂无订单状态分布");
    setChartEmpty("source-chart", "暂无来源分布");
    setChartEmpty("service-chart", "暂无服务版本分布");
  } finally {
    state.loading = false;
  }
}

function bindRangeButton(id, range) {
  document.getElementById(id).addEventListener("click", () => {
    state.range = range;
    updateRangeButtons();
    if (state.payload) {
      renderTrend(state.payload.trends || {});
    }
  });
}

function logout() {
  setToken("");
  state.payload = null;
  Object.keys(state.charts).forEach((id) => setChartEmpty(id, "等待加载数据"));
  markCardsEmpty();
  setStatus("loading", "尚未连接", "登录后查看核心经营指标");
  setMessage("已退出登录，请重新登录。", "");
}

function bootstrap() {
  const cachedToken = window.sessionStorage.getItem(TOKEN_KEY);
  if (cachedToken && !getToken()) {
    setToken(cachedToken);
  }

  window.addEventListener("resize", () => {
    Object.values(state.charts).forEach((chart) => chart && chart.resize());
  });

  document.getElementById("login-btn").addEventListener("click", () => {
    loadDashboard({ loginFirst: true });
  });
  document.getElementById("refresh-btn").addEventListener("click", () => {
    loadDashboard({ loginFirst: false });
  });
  document.getElementById("quick-refresh-btn").addEventListener("click", () => {
    loadDashboard({ loginFirst: false });
  });
  document.getElementById("quick-logout-btn").addEventListener("click", logout);
  bindRangeButton("range-7d", "7d");
  bindRangeButton("range-30d", "30d");
  updateRangeButtons();
  setStatus("loading", "尚未连接", "登录后查看核心经营指标");
}

window.addEventListener("DOMContentLoaded", bootstrap);

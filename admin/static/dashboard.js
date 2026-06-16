const TOKEN_KEY = "gaokao_admin_dashboard_token";

const state = {
  charts: {},
  payload: null,
  range: "7d",
};

function resolveApiBase() {
  const raw = document.getElementById("api-base").value.trim();
  return raw || window.location.origin;
}

function formatMoney(cents) {
  return `¥${(Number(cents || 0) / 100).toFixed(2)}`;
}

function setMessage(text, isSuccess = false) {
  const el = document.getElementById("message");
  el.textContent = text;
  el.className = isSuccess ? "hint success" : "hint";
}

function setError(text) {
  document.getElementById("error").textContent = text || "";
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
  document.getElementById("total-orders").textContent = String(
    summary.total_orders ?? 0,
  );
  document.getElementById("total-users").textContent = String(
    summary.total_users ?? 0,
  );
  document.getElementById("total-revenue").textContent = formatMoney(
    summary.total_revenue_cents ?? 0,
  );
  document.getElementById("orders-subtitle").textContent =
    `今日 ${summary.orders_today ?? 0} / 7d ${summary.orders_7d ?? 0} / 30d ${summary.orders_30d ?? 0}`;
  document.getElementById("revenue-subtitle").textContent =
    `今日 ${formatMoney(summary.revenue_today_cents)} / 7d ${formatMoney(summary.revenue_7d_cents)} / 30d ${formatMoney(summary.revenue_30d_cents)}`;
}

function ensureChart(id) {
  if (!state.charts[id]) {
    state.charts[id] = echarts.init(document.getElementById(id));
  }
  return state.charts[id];
}

function renderTrend(trends) {
  const points = Array.isArray(trends?.[state.range])
    ? trends?.[state.range]
    : [];
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

function renderBarChart(chartId, title, dataMap, color) {
  const entries = Object.entries(dataMap || {});
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
        name: title,
        type: "bar",
        data: entries.map(([, value]) => value ?? 0),
        itemStyle: { color },
        barMaxWidth: 48,
      },
    ],
  });
}

function renderDistributions(payload) {
  renderBarChart("status-chart", "状态分布", payload.by_status, "#2563eb");
  renderBarChart("source-chart", "来源分布", payload.by_source, "#7c3aed");
  renderBarChart(
    "service-chart",
    "服务版本分布",
    payload.by_service_version,
    "#059669",
  );
}

function updateRangeButtons() {
  const isThirty = state.range === "30d";
  document.getElementById("range-7d").className = isThirty
    ? "secondary"
    : "active-range";
  document.getElementById("range-30d").className = isThirty
    ? "active-range"
    : "secondary";
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
  renderSummary(payload.summary || {});
  renderTrend(payload.trends || {});
  renderDistributions(payload);
  updateRangeButtons();
  document.getElementById("generated-at").textContent =
    `更新时间: ${payload.generated_at || "unknown"}`;
}

async function loadDashboard({ loginFirst = false } = {}) {
  try {
    setError("");
    setMessage(loginFirst ? "登录中..." : "加载中...");

    let token = getToken();
    if (!token && loginFirst) {
      token = await loginAndStoreToken();
      setMessage("登录成功，开始加载仪表盘...", true);
    }
    if (!token) {
      throw new Error("缺少 JWT，请先登录或粘贴 Bearer Token。");
    }

    const payload = await fetchDashboard(token);
    renderDashboard(payload);
    setMessage("仪表盘加载成功", true);
  } catch (error) {
    setError(error.message || String(error));
    setMessage("加载失败，请检查认证或服务状态。");
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
  bindRangeButton("range-7d", "7d");
  bindRangeButton("range-30d", "30d");
  updateRangeButtons();
}

window.addEventListener("DOMContentLoaded", bootstrap);

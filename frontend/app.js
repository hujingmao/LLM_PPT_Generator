// 默认 API 地址：
// 1. 通过 FastAPI 托管前端时，window.location.origin 就是后端地址。
// 2. 直接双击打开 index.html 时，使用本地 8000 端口作为后端地址。
const defaultApiBase = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : window.location.origin;
const API_BASE = (localStorage.getItem("apiBase") || defaultApiBase).replace(/\/$/, "");

// 前端全局状态。这里只保存当前登录 token 和用户信息，页面刷新时会从 localStorage 恢复 token。
const state = {
  token: localStorage.getItem("accessToken") || "",
  user: null,
};

// 缓存常用 DOM 节点，避免每次切换视图时重复查询。
const authView = document.querySelector("#authView");
const dashboardView = document.querySelector("#dashboardView");
const toast = document.querySelector("#toast");

// 页面 DOM 加载完成后再绑定事件，确保所有按钮和表单节点都已存在。
document.addEventListener("DOMContentLoaded", () => {
  bindAuthTabs();
  bindAuthForms();
  bindDashboard();
  boot();
});

async function boot() {
  // 没有 token 说明用户未登录，直接显示登录页。
  if (!state.token) {
    showAuth();
    return;
  }

  try {
    // 有 token 时先请求 /me 验证 token 是否仍然有效。
    const user = await apiRequest("/api/users/me");
    setSession(state.token, user);
    showDashboard();
    await Promise.all([loadPackages(), loadOrders(), loadPptRecords()]);
  } catch (error) {
    // token 过期或用户被禁用时，清理本地登录态。
    clearSession();
    showAuth();
  }
}

function bindAuthTabs() {
  // 登录/注册两个表单共用一个卡片，通过 data-auth-tab 控制显示哪一个。
  document.querySelectorAll("[data-auth-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-auth-tab]").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      document.querySelector("#loginForm").classList.toggle("hidden", button.dataset.authTab !== "login");
      document.querySelector("#registerForm").classList.toggle("hidden", button.dataset.authTab !== "register");
    });
  });
}

function bindAuthForms() {
  // 登录表单提交：拿到 JWT 后进入工作台。
  document.querySelector("#loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const result = await apiRequest("/api/auth/login", {
        method: "POST",
        body: data,
        auth: false,
      });
      setSession(result.access_token, result.user);
      showDashboard();
      await Promise.all([loadPackages(), loadOrders(), loadPptRecords()]);
      showToast("登录成功");
    } catch (error) {
      showToast(error.message, true);
    }
  });

  // 注册表单提交：注册成功后后端会直接返回 JWT，体验上等同自动登录。
  document.querySelector("#registerForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    data.email = data.email || null;
    try {
      const result = await apiRequest("/api/auth/register", {
        method: "POST",
        body: data,
        auth: false,
      });
      setSession(result.access_token, result.user);
      showDashboard();
      await Promise.all([loadPackages(), loadOrders(), loadPptRecords()]);
      showToast("注册成功");
    } catch (error) {
      showToast(error.message, true);
    }
  });
}

function bindDashboard() {
  // 退出只清理前端 token；后端是无状态 JWT，不需要服务端 session。
  document.querySelector("#logoutBtn").addEventListener("click", () => {
    clearSession();
    showAuth();
  });

  // 左侧菜单切换工作区。
  document.querySelectorAll("[data-page]").forEach((button) => {
    button.addEventListener("click", () => switchPage(button.dataset.page, button.textContent.trim()));
  });

  document.querySelector("#refreshOrdersBtn").addEventListener("click", loadOrders);
  document.querySelector("#refreshRecordsBtn").addEventListener("click", loadPptRecords);

  // 套餐按钮是动态渲染的，所以在父容器上做事件委托。
  document.querySelector("#packageList").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-package-id]");
    if (!button) return;
    await recharge(button.dataset.packageId, button);
  });

  // 生成记录和生成结果中的下载按钮同样使用事件委托。
  document.querySelector("#pptRecordList").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-download-id]");
    if (!button) return;
    await downloadRecord(button.dataset.downloadId);
  });

  document.querySelector("#generationResult").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-download-id]");
    if (!button) return;
    await downloadRecord(button.dataset.downloadId);
  });

  // PPT 生成表单提交后调用后端同步生成接口。
  document.querySelector("#generateForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    await generatePpt(event.currentTarget);
  });
}

function switchPage(pageId, title) {
  // 同步更新导航高亮、页面显示状态和顶部标题。
  document.querySelectorAll("[data-page]").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === pageId);
  });
  document.querySelectorAll(".workspace").forEach((section) => {
    section.classList.toggle("active", section.id === pageId);
  });
  document.querySelector("#pageTitle").textContent = title;
}

async function loadPackages() {
  // 套餐由后端统一返回，前端不硬编码金额和积分，便于后续后台调整。
  const packages = await apiRequest("/api/recharge/packages");
  const list = document.querySelector("#packageList");
  list.innerHTML = packages
    .map(
      (item) => `
        <article class="package-card">
          <span>${escapeHtml(item.name)}</span>
          <strong>${Number(item.points).toLocaleString()} 积分</strong>
          <span>￥${formatMoney(item.amount)}</span>
          <button class="primary-btn" type="button" data-package-id="${escapeHtml(item.id)}">模拟支付</button>
        </article>
      `
    )
    .join("");
}

async function recharge(packageId, button) {
  // 防止用户连续点击同一个套餐造成重复请求。
  button.disabled = true;
  try {
    const order = await apiRequest("/api/recharge/simulate", {
      method: "POST",
      body: { package_id: packageId },
    });
    await refreshUser();
    await loadOrders();
    showToast(`充值成功，到账 ${order.points} 积分`);
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function loadOrders() {
  // 充值记录展示当前用户最近 50 条订单。
  const orders = await apiRequest("/api/recharge/orders");
  const list = document.querySelector("#orderList");
  if (!orders.length) {
    list.innerHTML = `<div class="record-row"><strong>暂无充值记录</strong><span></span><span></span><span></span></div>`;
    return;
  }

  list.innerHTML = orders
    .map(
      (order) => `
        <div class="record-row">
          <div>
            <strong>${escapeHtml(order.order_no)}</strong>
            <span>${formatDate(order.created_at)}</span>
          </div>
          <div>￥${formatMoney(order.amount)}</div>
          <div>${Number(order.points).toLocaleString()} 积分</div>
          <span class="status ${escapeHtml(order.status)}">${escapeHtml(order.status)}</span>
        </div>
      `
    )
    .join("");
}

async function generatePpt(form) {
  // 把表单字段转换成后端接口需要的 JSON payload。
  const button = document.querySelector("#generateBtn");
  const resultPanel = document.querySelector("#generationResult");
  const data = Object.fromEntries(new FormData(form));
  data.page_count = Number(data.page_count || 8);
  data.use_images = Boolean(data.use_images);
  data.template_path = data.template_path ? data.template_path.trim() : null;

  // 生成 PPT 可能需要等待大模型和图片接口，按钮进入 loading 状态避免重复提交。
  button.disabled = true;
  button.textContent = "生成中...";
  resultPanel.classList.add("hidden");

  try {
    const result = await apiRequest("/api/ppt/generate", {
      method: "POST",
      body: data,
    });
    await refreshUser();
    await loadPptRecords();
    const record = result.record;
    // 生成成功后在当前页面给出下载按钮，同时历史记录页也会刷新。
    resultPanel.innerHTML = `
      <strong>生成成功：${escapeHtml(record.ppt_topic)}</strong>
      <span>消耗 ${record.points_cost} 积分，文件已写入生成记录。</span>
      <button class="primary-btn" type="button" data-download-id="${record.id}">下载 PPT</button>
    `;
    resultPanel.classList.remove("hidden");
    showToast("PPT 生成成功");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "生成并扣积分";
  }
}

async function loadPptRecords() {
  // 生成记录包含 success/failed/generating，前端根据状态决定是否显示下载按钮。
  const records = await apiRequest("/api/ppt/records");
  const list = document.querySelector("#pptRecordList");
  if (!records.length) {
    list.innerHTML = `<div class="record-row"><strong>暂无生成记录</strong><span></span><span></span><span></span></div>`;
    return;
  }

  list.innerHTML = records
    .map((record) => {
      const action =
        record.status === "success"
          ? `<button type="button" data-download-id="${record.id}">下载</button>`
          : `<span>${escapeHtml(record.error_message || "")}</span>`;
      return `
        <div class="record-row">
          <div>
            <strong>${escapeHtml(record.ppt_topic)}</strong>
            <span>${formatDate(record.created_at)}</span>
          </div>
          <div>${record.points_cost} 积分</div>
          <div><span class="status ${escapeHtml(record.status)}">${escapeHtml(record.status)}</span></div>
          ${action}
        </div>
      `;
    })
    .join("");
}

async function downloadRecord(recordId) {
  // 文件下载需要带上 Bearer Token，否则后端无法判断文件归属。
  try {
    const response = await fetch(`${API_BASE}/api/ppt/download/${recordId}`, {
      headers: { Authorization: `Bearer ${state.token}` },
    });
    if (!response.ok) {
      const payload = await safeJson(response);
      throw new Error(payload.detail || "下载失败");
    }

    // 把二进制响应转成临时 URL，再用隐藏 a 标签触发浏览器下载。
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = parseFilename(response.headers.get("content-disposition")) || `ppt_${recordId}.pptx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    showToast(error.message, true);
  }
}

async function refreshUser() {
  // 充值或生成扣费后刷新用户余额。
  const user = await apiRequest("/api/users/me");
  setUser(user);
}

async function apiRequest(path, options = {}) {
  // 全站统一请求封装：自动拼接 API_BASE、序列化 JSON、附加 token、处理错误。
  const { method = "GET", body, auth = true } = options;
  const headers = { "Content-Type": "application/json" };
  if (auth && state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const payload = await safeJson(response);
  if (!response.ok) {
    // FastAPI 错误响应通常把信息放在 detail 字段。
    throw new Error(payload.detail || "请求失败");
  }
  return payload;
}

async function safeJson(response) {
  // 有些响应可能为空或不是 JSON，统一兜底为空对象，避免 JSON.parse 抛错打断流程。
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

function setSession(token, user) {
  // token 写入 localStorage，刷新页面后 boot() 可以恢复登录态。
  state.token = token;
  localStorage.setItem("accessToken", token);
  setUser(user);
}

function setUser(user) {
  // 更新内存状态和页面右上角账户信息。
  state.user = user;
  document.querySelector("#currentUser").textContent = user.username;
  document.querySelector("#currentPoints").textContent = Number(user.points_balance).toLocaleString();
}

function clearSession() {
  // 清理本地登录态，下一次 boot 会回到登录页。
  state.token = "";
  state.user = null;
  localStorage.removeItem("accessToken");
}

function showAuth() {
  // 显示未登录视图。
  authView.classList.remove("hidden");
  dashboardView.classList.add("hidden");
}

function showDashboard() {
  // 显示工作台，并默认定位到生成 PPT 页面。
  authView.classList.add("hidden");
  dashboardView.classList.remove("hidden");
  switchPage("generatePage", "生成 PPT");
}

function showToast(message, isError = false) {
  // 轻提示自动隐藏；连续调用时先清理上一次计时器。
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.add("hidden"), 2600);
}

function formatMoney(value) {
  // 金额统一保留两位小数。
  return Number(value).toFixed(2);
}

function formatDate(value) {
  // 后端返回 ISO 时间字符串，前端按中文环境显示。
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function parseFilename(disposition) {
  // 从 Content-Disposition 里解析文件名，兼容 filename* 和 filename 两种格式。
  if (!disposition) return "";
  const utf8Match = disposition.match(/filename\*=utf-8''([^;]+)/i);
  if (utf8Match) return decodeURIComponent(utf8Match[1]);
  const asciiMatch = disposition.match(/filename="?([^"]+)"?/i);
  return asciiMatch ? asciiMatch[1] : "";
}

function escapeHtml(value) {
  // 用户输入的主题会被插入 innerHTML，必须转义以避免 XSS。
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

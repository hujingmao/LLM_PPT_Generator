const defaultApiBase = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : window.location.origin;
const API_BASE = (localStorage.getItem("apiBase") || defaultApiBase).replace(/\/$/, "");

const state = {
  token: localStorage.getItem("accessToken") || "",
  user: null,
};

const authView = document.querySelector("#authView");
const dashboardView = document.querySelector("#dashboardView");
const toast = document.querySelector("#toast");

document.addEventListener("DOMContentLoaded", () => {
  bindAuthTabs();
  bindAuthForms();
  bindDashboard();
  boot();
});

async function boot() {
  if (!state.token) {
    showAuth();
    return;
  }

  try {
    const user = await apiRequest("/api/users/me");
    setSession(state.token, user);
    showDashboard();
    await Promise.all([loadPackages(), loadOrders(), loadPptRecords()]);
  } catch (error) {
    clearSession();
    showAuth();
  }
}

function bindAuthTabs() {
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
  document.querySelector("#logoutBtn").addEventListener("click", () => {
    clearSession();
    showAuth();
  });

  document.querySelectorAll("[data-page]").forEach((button) => {
    button.addEventListener("click", () => switchPage(button.dataset.page, button.textContent.trim()));
  });

  document.querySelector("#refreshOrdersBtn").addEventListener("click", loadOrders);
  document.querySelector("#refreshRecordsBtn").addEventListener("click", loadPptRecords);

  document.querySelector("#packageList").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-package-id]");
    if (!button) return;
    await recharge(button.dataset.packageId, button);
  });

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

  document.querySelector("#generateForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    await generatePpt(event.currentTarget);
  });
}

function switchPage(pageId, title) {
  document.querySelectorAll("[data-page]").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === pageId);
  });
  document.querySelectorAll(".workspace").forEach((section) => {
    section.classList.toggle("active", section.id === pageId);
  });
  document.querySelector("#pageTitle").textContent = title;
}

async function loadPackages() {
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
  const button = document.querySelector("#generateBtn");
  const resultPanel = document.querySelector("#generationResult");
  const data = Object.fromEntries(new FormData(form));
  data.page_count = Number(data.page_count || 8);
  data.use_images = Boolean(data.use_images);
  data.template_path = data.template_path ? data.template_path.trim() : null;

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
  try {
    const response = await fetch(`${API_BASE}/api/ppt/download/${recordId}`, {
      headers: { Authorization: `Bearer ${state.token}` },
    });
    if (!response.ok) {
      const payload = await safeJson(response);
      throw new Error(payload.detail || "下载失败");
    }

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
  const user = await apiRequest("/api/users/me");
  setUser(user);
}

async function apiRequest(path, options = {}) {
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
    throw new Error(payload.detail || "请求失败");
  }
  return payload;
}

async function safeJson(response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

function setSession(token, user) {
  state.token = token;
  localStorage.setItem("accessToken", token);
  setUser(user);
}

function setUser(user) {
  state.user = user;
  document.querySelector("#currentUser").textContent = user.username;
  document.querySelector("#currentPoints").textContent = Number(user.points_balance).toLocaleString();
}

function clearSession() {
  state.token = "";
  state.user = null;
  localStorage.removeItem("accessToken");
}

function showAuth() {
  authView.classList.remove("hidden");
  dashboardView.classList.add("hidden");
}

function showDashboard() {
  authView.classList.add("hidden");
  dashboardView.classList.remove("hidden");
  switchPage("generatePage", "生成 PPT");
}

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.add("hidden"), 2600);
}

function formatMoney(value) {
  return Number(value).toFixed(2);
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function parseFilename(disposition) {
  if (!disposition) return "";
  const utf8Match = disposition.match(/filename\*=utf-8''([^;]+)/i);
  if (utf8Match) return decodeURIComponent(utf8Match[1]);
  const asciiMatch = disposition.match(/filename="?([^"]+)"?/i);
  return asciiMatch ? asciiMatch[1] : "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

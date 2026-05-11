const defaultApiBase = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : window.location.origin;
const API_BASE = (localStorage.getItem("apiBase") || defaultApiBase).replace(/\/$/, "");

const progressSteps = [
  "正在解析上传资料……",
  "正在构建知识库……",
  "正在检索相关内容……",
  "正在生成 PPT 大纲……",
  "等待用户确认大纲……",
  "正在生成 PPT 页面……",
  "正在自动配图……",
  "正在导出 PPT 文件……",
  "生成完成",
  "生成失败",
];

const layoutOptions = [
  ["cover", "封面页"],
  ["agenda", "目录页"],
  ["section", "章节过渡页"],
  ["text", "普通文本页"],
  ["image_text", "图文页"],
  ["three_cards", "三栏卡片页"],
  ["timeline", "时间轴页"],
  ["comparison", "对比页"],
  ["process", "流程页"],
  ["summary", "总结页"],
  ["thanks", "致谢页"],
];

const state = {
  token: localStorage.getItem("accessToken") || "",
  user: null,
  templates: [],
  uploadedFiles: [],
  currentOutline: null,
  progress: Object.fromEntries(progressSteps.map((step) => [step, "pending"])),
};

const authView = document.querySelector("#authView");
const appView = document.querySelector("#appView");
const toast = document.querySelector("#toast");

document.addEventListener("DOMContentLoaded", () => {
  bindAuthTabs();
  bindAuthForms();
  bindAppEvents();
  renderProgress();
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
    showApp();
    await loadDashboardData();
  } catch {
    clearSession();
    showAuth();
  }
}

async function loadDashboardData() {
  await Promise.allSettled([
    loadTemplates(),
    loadUploadedFiles(),
    loadPackages(),
    loadOrders(),
    loadPptRecords(),
  ]);
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
      const result = await apiRequest("/api/auth/login", { method: "POST", body: data, auth: false });
      setSession(result.access_token, result.user);
      showApp();
      await loadDashboardData();
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
      const result = await apiRequest("/api/auth/register", { method: "POST", body: data, auth: false });
      setSession(result.access_token, result.user);
      showApp();
      await loadDashboardData();
      showToast("注册成功");
    } catch (error) {
      showToast(error.message, true);
    }
  });
}

function bindAppEvents() {
  document.querySelector("#logoutBtn").addEventListener("click", () => {
    clearSession();
    showAuth();
  });

  document.querySelectorAll("[data-page]").forEach((button) => {
    button.addEventListener("click", () => switchPage(button.dataset.page));
  });

  document.querySelector("#uploadFileBtn").addEventListener("click", uploadReferenceFiles);
  document.querySelector("#refreshFilesBtn").addEventListener("click", loadUploadedFiles);
  document.querySelector("#generateOutlineBtn").addEventListener("click", generateOutline);
  document.querySelector("#exportPptBtn").addEventListener("click", exportPpt);
  document.querySelector("#refreshRecordsBtn").addEventListener("click", loadPptRecords);
  document.querySelector("#refreshRecordsInlineBtn").addEventListener("click", loadPptRecords);
  document.querySelector("#refreshOrdersBtn").addEventListener("click", loadOrders);

  document.querySelector("#packageList").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-package-id]");
    if (button) await recharge(button.dataset.packageId, button);
  });

  ["#pptRecordList", "#historyList", "#downloadArea"].forEach((selector) => {
    document.querySelector(selector).addEventListener("click", async (event) => {
      const button = event.target.closest("[data-download-id]");
      if (button) await downloadRecord(button.dataset.downloadId);
    });
  });
}

function switchPage(pageId) {
  document.querySelectorAll("[data-page]").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === pageId);
  });
  document.querySelectorAll(".workspace").forEach((section) => {
    section.classList.toggle("active", section.id === pageId);
  });
}

async function loadTemplates() {
  const templates = await apiRequest("/api/templates", { auth: false });
  state.templates = templates;
  const select = document.querySelector("#templateSelect");
  select.innerHTML = templates
    .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}</option>`)
    .join("");
}

async function uploadReferenceFiles() {
  const input = document.querySelector("#referenceFileInput");
  const files = Array.from(input.files || []);
  if (!files.length) {
    showToast("请选择要上传的参考资料", true);
    return;
  }

  const button = document.querySelector("#uploadFileBtn");
  button.disabled = true;
  markProgress("正在解析上传资料……", "active");

  try {
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      const result = await apiRequest("/api/files/upload", { method: "POST", body: formData });
      if (result.parse_status === "success") {
        markProgress("正在解析上传资料……", "done");
        markProgress("正在构建知识库……", "done");
        showToast(`${result.original_filename} 上传并解析成功`);
      } else {
        markProgress("生成失败", "active");
        showToast(`${result.original_filename}：${result.parse_error || "解析失败"}`, true);
      }
    }
    input.value = "";
    await loadUploadedFiles();
  } catch (error) {
    markProgress("生成失败", "active");
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function loadUploadedFiles() {
  const files = await apiRequest("/api/files");
  state.uploadedFiles = files;
  renderUploadedFiles();
}

function renderUploadedFiles() {
  const list = document.querySelector("#uploadedFileList");
  if (!state.uploadedFiles.length) {
    list.innerHTML = `<div class="file-row"><div class="file-main"><strong>暂无上传资料</strong><span>支持 txt、md、pdf、docx、pptx</span></div><span></span></div>`;
    return;
  }

  list.innerHTML = state.uploadedFiles
    .map((file) => {
      const disabled = file.parse_status !== "success" ? "disabled" : "";
      const checked = file.parse_status === "success" ? "checked" : "";
      return `
        <div class="file-row">
          <label>
            <input type="checkbox" value="${file.id}" ${checked} ${disabled} data-uploaded-file />
            <span class="file-main">
              <strong>${escapeHtml(file.original_filename)}</strong>
              <span>${formatFileSize(file.file_size)} · ${escapeHtml(file.file_type)}</span>
            </span>
          </label>
          <span class="status ${escapeHtml(file.parse_status)}">${formatParseStatus(file)}</span>
        </div>
      `;
    })
    .join("");
}

async function generateOutline() {
  const topic = document.querySelector("#topicInput").value.trim();
  if (!topic) {
    showToast("请输入 PPT 主题", true);
    return;
  }

  const button = document.querySelector("#generateOutlineBtn");
  const selectedFileIds = getSelectedFileIds();
  button.disabled = true;
  document.querySelector("#exportPptBtn").disabled = true;
  document.querySelector("#downloadArea").classList.add("hidden");
  resetProgress();
  if (selectedFileIds.length) {
    markProgress("正在解析上传资料……", "done");
    markProgress("正在构建知识库……", "done");
  }
  markProgress("正在检索相关内容……", "active");
  markProgress("正在生成 PPT 大纲……", "active");

  const payload = {
    topic,
    scene: document.querySelector("#sceneSelect").value,
    page_count: Number(document.querySelector("#pageCountInput").value || 8),
    style: document.querySelector("#styleSelect").value,
    uploaded_file_ids: selectedFileIds,
    reference_context: document.querySelector("#referenceContextInput").value.trim(),
  };

  try {
    const outline = await apiRequest("/api/ppt/outline", { method: "POST", body: payload });
    state.currentOutline = outline;
    markProgress("正在检索相关内容……", "done");
    markProgress("正在生成 PPT 大纲……", "done");
    markProgress("等待用户确认大纲……", "active");
    renderOutline(outline);
    document.querySelector("#exportPptBtn").disabled = false;
    showToast("大纲生成成功");
  } catch (error) {
    markProgress("生成失败", "active");
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
}

function renderOutline(outline) {
  document.querySelector("#outlineMeta").classList.remove("hidden");
  document.querySelector("#outlineTitleInput").value = outline.title || document.querySelector("#topicInput").value.trim();
  document.querySelector("#outlineSubtitleInput").value = outline.subtitle || document.querySelector("#sceneSelect").value;

  const preview = document.querySelector("#outlinePreview");
  preview.classList.remove("empty-state");
  preview.innerHTML = (outline.slides || [])
    .map((slide, index) => {
      const layoutSelect = layoutOptions
        .map(([value, label]) => {
          const selected = (slide.layout_type || "text") === value ? "selected" : "";
          return `<option value="${value}" ${selected}>${label}</option>`;
        })
        .join("");
      return `
        <article class="slide-editor" data-slide-editor>
          <div class="slide-no">${String(index + 1).padStart(2, "0")}</div>
          <div class="slide-fields">
            <label>
              页面标题
              <input data-field="page_title" value="${escapeHtml(slide.page_title || "")}" />
            </label>
            <label>
              版式
              <select data-field="layout_type">${layoutSelect}</select>
            </label>
            <label>
              要点
              <textarea data-field="bullets">${escapeHtml((slide.bullets || []).join("\n"))}</textarea>
            </label>
            <label>
              讲稿备注
              <textarea data-field="speaker_notes">${escapeHtml(slide.speaker_notes || "")}</textarea>
            </label>
            <label>
              配图关键词
              <input data-field="image_keywords" value="${escapeHtml((slide.image_keywords || []).join(", "))}" />
            </label>
          </div>
        </article>
      `;
    })
    .join("");
}

async function exportPpt() {
  const outline = buildOutlineFromEditor();
  if (!outline.slides.length) {
    showToast("请先生成大纲", true);
    return;
  }

  const button = document.querySelector("#exportPptBtn");
  button.disabled = true;
  markProgress("等待用户确认大纲……", "done");
  markProgress("正在生成 PPT 页面……", "active");
  if (document.querySelector("#useImagesCheckbox").checked) {
    markProgress("正在自动配图……", "active");
  }
  markProgress("正在导出 PPT 文件……", "active");

  const payload = {
    outline_json: outline,
    template_id: document.querySelector("#templateSelect").value || "default",
    style: document.querySelector("#styleSelect").value,
    scene: document.querySelector("#sceneSelect").value,
    use_images: document.querySelector("#useImagesCheckbox").checked,
  };

  try {
    const result = await apiRequest("/api/ppt/export", { method: "POST", body: payload });
    markProgress("正在生成 PPT 页面……", "done");
    markProgress("正在自动配图……", "done");
    markProgress("正在导出 PPT 文件……", "done");
    markProgress("生成完成", "done");
    renderDownload(result);
    await Promise.allSettled([refreshUser(), loadPptRecords()]);
    showToast("PPT 生成完成");
  } catch (error) {
    markProgress("生成失败", "active");
    showToast(error.message, true);
  } finally {
    button.disabled = false;
  }
}

function buildOutlineFromEditor() {
  const slides = Array.from(document.querySelectorAll("[data-slide-editor]")).map((editor, index) => {
    const bullets = getFieldValue(editor, "bullets")
      .split(/\n+/)
      .map((item) => item.trim())
      .filter(Boolean);
    const imageKeywords = getFieldValue(editor, "image_keywords")
      .split(/[,\n，]+/)
      .map((item) => item.trim())
      .filter(Boolean);
    return {
      page_no: index + 1,
      page_title: getFieldValue(editor, "page_title") || `第 ${index + 1} 页`,
      layout_type: getFieldValue(editor, "layout_type") || "text",
      bullets,
      speaker_notes: getFieldValue(editor, "speaker_notes"),
      image_keywords: imageKeywords,
    };
  });

  return {
    title: document.querySelector("#outlineTitleInput").value.trim() || document.querySelector("#topicInput").value.trim(),
    subtitle: document.querySelector("#outlineSubtitleInput").value.trim(),
    slides,
  };
}

function getFieldValue(editor, field) {
  const element = editor.querySelector(`[data-field="${field}"]`);
  return element ? element.value.trim() : "";
}

function renderDownload(result) {
  const area = document.querySelector("#downloadArea");
  area.innerHTML = `
    <strong>生成完成：${escapeHtml(result.filename || "PPT 文件")}</strong>
    <div>
      <button class="primary-btn" type="button" data-download-id="${result.ppt_record_id}">下载 PPT</button>
    </div>
  `;
  area.classList.remove("hidden");
}

async function loadPackages() {
  const packages = await apiRequest("/api/recharge/packages", { auth: false });
  const list = document.querySelector("#packageList");
  list.innerHTML = packages
    .map(
      (item) => `
        <article class="package-card">
          <span>${escapeHtml(item.name)}</span>
          <strong>${Number(item.points).toLocaleString()} 积分</strong>
          <span>¥ ${formatMoney(item.amount)}</span>
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
    await Promise.allSettled([refreshUser(), loadOrders()]);
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
          <div>¥ ${formatMoney(order.amount)}</div>
          <div>${Number(order.points).toLocaleString()} 积分</div>
          <span class="status ${escapeHtml(order.status)}">${escapeHtml(order.status)}</span>
        </div>
      `
    )
    .join("");
}

async function loadPptRecords() {
  const records = await apiRequest("/api/ppt/records");
  renderRecords(records, document.querySelector("#pptRecordList"));
  renderRecords(records.slice(0, 5), document.querySelector("#historyList"));
}

function renderRecords(records, list) {
  if (!records.length) {
    list.innerHTML = `<div class="record-row"><strong>暂无生成记录</strong><span></span><span></span><span></span></div>`;
    return;
  }

  list.innerHTML = records
    .map((record) => {
      const action =
        record.status === "success"
          ? `<button type="button" data-download-id="${record.id}">下载</button>`
          : `<span>${escapeHtml(record.error_message || record.progress_step || "")}</span>`;
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
      throw new Error(normalizeErrorDetail(payload.detail) || "下载失败");
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
  const headers = {};
  const isFormData = body instanceof FormData;
  if (!isFormData) headers["Content-Type"] = "application/json";
  if (auth && state.token) headers.Authorization = `Bearer ${state.token}`;

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? (isFormData ? body : JSON.stringify(body)) : undefined,
  });
  const payload = await safeJson(response);

  if (!response.ok) {
    if (response.status === 401) {
      clearSession();
      showAuth();
      throw new Error("请先登录");
    }
    throw new Error(normalizeErrorDetail(payload.detail) || "请求失败");
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
  appView.classList.add("hidden");
}

function showApp() {
  authView.classList.add("hidden");
  appView.classList.remove("hidden");
  switchPage("generatePage");
}

function getSelectedFileIds() {
  return Array.from(document.querySelectorAll("[data-uploaded-file]:checked")).map((item) => Number(item.value));
}

function renderProgress() {
  const list = document.querySelector("#progressList");
  list.innerHTML = progressSteps
    .map((step) => {
      const status = state.progress[step] || "pending";
      return `
        <div class="progress-row ${status}">
          <strong>${escapeHtml(step)}</strong>
          <span>${formatProgressStatus(status)}</span>
        </div>
      `;
    })
    .join("");
}

function resetProgress() {
  state.progress = Object.fromEntries(progressSteps.map((step) => [step, "pending"]));
  renderProgress();
}

function markProgress(step, status) {
  state.progress[step] = status;
  if (step !== "生成失败" && status === "active") {
    state.progress["生成失败"] = "pending";
  }
  renderProgress();
}

function formatProgressStatus(status) {
  if (status === "done") return "完成";
  if (status === "active") return "进行中";
  return "待处理";
}

function formatParseStatus(file) {
  if (file.parse_status === "success") return "解析成功";
  if (file.parse_status === "failed") return "解析失败";
  return "解析中";
}

function formatMoney(value) {
  return Number(value).toFixed(2);
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function formatFileSize(size) {
  const value = Number(size || 0);
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function parseFilename(disposition) {
  if (!disposition) return "";
  const utf8Match = disposition.match(/filename\*=utf-8''([^;]+)/i);
  if (utf8Match) return decodeURIComponent(utf8Match[1]);
  const asciiMatch = disposition.match(/filename="?([^"]+)"?/i);
  return asciiMatch ? asciiMatch[1] : "";
}

function normalizeErrorDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg || JSON.stringify(item)).join("；");
  if (typeof detail === "object") return detail.message || JSON.stringify(detail);
  return String(detail);
}

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.add("hidden"), 2800);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


// app.js - Enhanced SPA for Health Management System
const API = "/api";
let userId = null;
let currentUser = null;
const main = document.getElementById("main");
const sidebar = document.getElementById("sidebar");
const nav = document.getElementById("nav");
const mobileNavToggle = document.getElementById("mobileNavToggle");
const modal = document.getElementById("modal");
const modalTitle = document.getElementById("modalTitle");
const modalMessage = document.getElementById("modalMessage");
const modalCancel = document.getElementById("modalCancel");
const modalConfirm = document.getElementById("modalConfirm");
const currentDate = document.getElementById("currentDate");
const userName = document.getElementById("userName");
const displayScale = document.getElementById("displayScale");
const pickerOverlay = document.getElementById("pickerOverlay");
const pickerTitle = document.getElementById("pickerTitle");
const pickerBody = document.getElementById("pickerBody");
const pickerClose = document.getElementById("pickerClose");

let currentPage = "dashboard";
let chartInstance = null;
let editingVitalId = null;
let editingPatientId = null;
let editingCheckupId = null;
let editingHospitalityId = null;
let editingBillId = null;
let activePickerInput = null;
let calendarCursor = null;

const ADMIN_PROFILE = {
  id: "ADM-1001",
  name: "Mohit Kumar Pradhan",
  role: "Admin Developer",
  email: "mohitkumarpradhan1234567@gmail.com",
  phone: "+91 7970880676",
  department: "HMS Backend Department",
  specialization: "Backend Developer",
  photo: "admin-photo.jpg?v=3"
};

const USER_PROFILE = {
  id: "USR-1001",
  name: "HMS User",
  role: "User Mode",
  email: "user@hms.local",
  phone: "Self service",
  department: "Patient Portal",
  specialization: "Health Tracking",
  photo: "admin-photo.jpg?v=3"
};

// Authentication
function initAuth() {
  const loginForm = document.getElementById("loginForm");
  const logoutBtn = document.getElementById("logoutBtn");
  const loginMessage = document.getElementById("loginMessage");

  if (currentDate) {
    currentDate.textContent = new Date().toLocaleString();
  }
  initDisplayScale();

  // Check if already logged in
  const storedUser = localStorage.getItem("currentUser");
  if (storedUser) {
    currentUser = JSON.parse(storedUser);
    userId = currentUser.id;
    showMainApp();
    loadPage("dashboard");
  } else {
    showLoginScreen();
  }

  // Login form handler
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(loginForm);
    const email = formData.get("email");
    const password = formData.get("password");

    try {
      const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();

      if (res.ok && data.status === "ok") {
        currentUser = data.user;
        userId = data.user.id;
        localStorage.setItem("currentUser", JSON.stringify(currentUser));
        showMainApp();
        loadPage("dashboard");
      } else {
        loginMessage.innerHTML = showError(data.message || "Login failed");
      }
    } catch (error) {
      loginMessage.innerHTML = showError("Network error. Please try again.");
    }
  });

  // Logout handler
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("currentUser");
    currentUser = null;
    userId = null;
    showLoginScreen();
  });
}

pickerClose.addEventListener("click", closePicker);
pickerOverlay.addEventListener("click", (event) => {
  if (event.target === pickerOverlay) closePicker();
});

document.addEventListener("mousedown", (event) => {
  const selectEl = event.target.closest("select");
  const dateEl = event.target.closest('input[type="date"]');
  if (selectEl) {
    event.preventDefault();
    renderSelectPicker(selectEl);
    return;
  }
  if (dateEl) {
    event.preventDefault();
    renderDatePicker(dateEl);
  }
});

function showLoginScreen() {
  document.getElementById("loginScreen").style.display = "flex";
  document.getElementById("mainApp").style.display = "none";
}

function showMainApp() {
  document.getElementById("loginScreen").style.display = "none";
  document.getElementById("mainApp").style.display = "flex";
  updateUserMode();
  if (currentDate) {
    currentDate.textContent = new Date().toLocaleString();
  }
  if (userName && currentUser) {
    userName.textContent = currentUser.name || getActiveProfile().name || currentUser.email || "User";
  }
  const headerPhoto = document.getElementById("adminPhotoHeader");
  if (headerPhoto) {
    headerPhoto.src = getActiveProfile().photo;
  }
}

function isAdminMode() {
  const email = String(currentUser?.email || "").toLowerCase();
  return email.includes("admin");
}

function getActiveProfile() {
  return isAdminMode() ? ADMIN_PROFILE : USER_PROFILE;
}

function updateUserMode() {
  const adminOnlyButtons = document.querySelectorAll("[data-admin-only='true']");
  adminOnlyButtons.forEach((button) => {
    button.style.display = isAdminMode() ? "flex" : "none";
  });
}

function quickLogin(role) {
  const loginEmail = document.getElementById("loginEmail");
  const loginPassword = document.getElementById("loginPassword");
  loginEmail.value = `${role}@hms.local`;
  loginPassword.value = "demo123";
  document.getElementById("loginForm").requestSubmit();
}

function refreshData() {
  loadPage(currentPage);
}

function escapeAttr(value) {
  return String(value ?? "").replace(/'/g, "\\'");
}

function getNumericValue(id, fallback = 1) {
  const el = document.getElementById(id);
  if (!el) return fallback;
  const value = Number.parseInt(el.value, 10);
  return Number.isNaN(value) ? fallback : value;
}

function prepareChartCanvas(canvasId) {
  const canvas = document.getElementById(canvasId);
  const container = canvas.parentElement;
  const width = Math.max(320, Math.floor(container.clientWidth - 24));
  const height = Math.max(280, Math.floor(container.clientHeight - 24));
  canvas.width = width;
  canvas.height = height;
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  return canvas.getContext("2d");
}

function formatDateValue(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function closePicker() {
  pickerOverlay.style.display = "none";
  pickerBody.innerHTML = "";
  activePickerInput = null;
}

function openPicker(title) {
  pickerTitle.textContent = title;
  pickerOverlay.style.display = "flex";
}

function renderSelectPicker(selectEl) {
  activePickerInput = selectEl;
  openPicker(selectEl.labels?.[0]?.textContent || "Select option");
  const options = [...selectEl.options].filter(option => option.value !== "");
  pickerBody.innerHTML = `
    <div class="picker-options">
      ${options.map(option => `
        <button type="button" class="picker-option ${option.value === selectEl.value ? "is-active" : ""}" data-value="${option.value}">
          ${option.textContent}
        </button>
      `).join("")}
    </div>
  `;

  pickerBody.querySelectorAll(".picker-option").forEach(button => {
    button.addEventListener("click", () => {
      selectEl.value = button.dataset.value;
      selectEl.dispatchEvent(new Event("change", { bubbles: true }));
      closePicker();
    });
  });
}

function renderDatePicker(inputEl) {
  activePickerInput = inputEl;
  const baseDate = inputEl.value ? new Date(`${inputEl.value}T00:00:00`) : new Date();
  calendarCursor = new Date(baseDate.getFullYear(), baseDate.getMonth(), 1);
  drawCalendar(inputEl);
  openPicker(inputEl.labels?.[0]?.textContent || "Select date");
}

function drawCalendar(inputEl) {
  const year = calendarCursor.getFullYear();
  const month = calendarCursor.getMonth();
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startWeekday = firstDay.getDay();
  const selectedValue = inputEl.value;
  const monthLabel = firstDay.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  const days = [];

  for (let i = 0; i < startWeekday; i += 1) {
    days.push('<div class="calendar-day is-muted"></div>');
  }

  for (let day = 1; day <= lastDay.getDate(); day += 1) {
    const date = new Date(year, month, day);
    const value = formatDateValue(date);
    const activeClass = value === selectedValue ? "is-selected" : "";
    days.push(`<button type="button" class="calendar-day ${activeClass}" data-date="${value}">${day}</button>`);
  }

  pickerBody.innerHTML = `
    <div class="calendar-toolbar">
      <button type="button" id="calendarPrev">Prev</button>
      <div class="calendar-title">${monthLabel}</div>
      <button type="button" id="calendarNext">Next</button>
    </div>
    <div class="calendar-grid">
      <div class="calendar-weekday">Sun</div>
      <div class="calendar-weekday">Mon</div>
      <div class="calendar-weekday">Tue</div>
      <div class="calendar-weekday">Wed</div>
      <div class="calendar-weekday">Thu</div>
      <div class="calendar-weekday">Fri</div>
      <div class="calendar-weekday">Sat</div>
      ${days.join("")}
    </div>
  `;

  document.getElementById("calendarPrev").addEventListener("click", () => {
    calendarCursor = new Date(year, month - 1, 1);
    drawCalendar(inputEl);
  });

  document.getElementById("calendarNext").addEventListener("click", () => {
    calendarCursor = new Date(year, month + 1, 1);
    drawCalendar(inputEl);
  });

  pickerBody.querySelectorAll(".calendar-day[data-date]").forEach(button => {
    button.addEventListener("click", () => {
      inputEl.value = button.dataset.date;
      inputEl.dispatchEvent(new Event("change", { bubbles: true }));
      closePicker();
    });
  });
}

function applyDisplayScale(scale) {
  const numericScale = Number(scale) || 1;
  document.body.style.zoom = String(numericScale);
  localStorage.setItem("hmsDisplayScale", String(numericScale));
  if (displayScale) {
    displayScale.value = String(numericScale);
  }
}

function initDisplayScale() {
  const savedScale = localStorage.getItem("hmsDisplayScale") || "1";
  applyDisplayScale(savedScale);
  if (displayScale) {
    displayScale.addEventListener("change", (event) => {
      applyDisplayScale(event.target.value);
    });
  }
}

// Navigation
nav.addEventListener("click", (e) => {
  const button = e.target.closest("button[data-page]");
  if (button) {
    loadPage(button.dataset.page);
  }
});

mobileNavToggle.addEventListener("click", () => {
  sidebar.classList.toggle("show");
  nav.classList.toggle("show");
});

// Modal functions
function showModal(title, message, onConfirm) {
  modalTitle.textContent = title;
  modalMessage.textContent = message;
  modal.style.display = "flex";

  const handleConfirm = () => {
    onConfirm();
    hideModal();
  };

  const handleCancel = () => hideModal();

  modalConfirm.onclick = handleConfirm;
  modalCancel.onclick = handleCancel;

  // Close on backdrop click
  modal.onclick = (e) => {
    if (e.target === modal) hideModal();
  };
}

function hideModal() {
  modal.style.display = "none";
}

// Utility functions
function showLoading(container) {
  container.innerHTML = '<div class="loading">Loading...</div>';
}

function showError(message) {
  return `<div class="error">${message}</div>`;
}

function showSuccess(message) {
  return `<div class="success">${message}</div>`;
}

function updateNavActive(page) {
  document.querySelectorAll(".nav button").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.page === page);
  });
}

function loadPage(page) {
  currentPage = page;
  updateNavActive(page);
  if (window.innerWidth <= 768) {
    sidebar.classList.remove("show");
    nav.classList.remove("show");
  }

  if (page === "dashboard") return renderDashboard();
  if (page === "patients") return renderPatients();
  if (page === "checkups") return renderCheckups();
  if (page === "hospitality") return renderHospitality();
  if (page === "bills") return renderBills();
  if (page === "vitals") return renderVitals();
  if (page === "symptoms") return renderSymptoms();
  if (page === "meds") return renderMeds();
  if (page === "appts") return renderAppts();
  if (page === "reports") return renderReports();
  if (page === "healthgraph") return renderHealthGraph();
}

// ---------- Dashboard ---------
async function renderDashboard(){
  const activeProfile = getActiveProfile();
  main.innerHTML = `
    <div class="dashboard-layout">
      <div class="admin-profile-card">
        <img class="admin-photo" src="${activeProfile.photo}" alt="${activeProfile.role} photo">
        <div class="admin-role">${activeProfile.role}</div>
        <h3>${activeProfile.name}</h3>
        <div class="small" style="color: rgba(255,255,255,0.82); font-size: 17px;">${isAdminMode() ? "Primary administrator for the HMS monitor and reporting system." : "Personal health tracking mode with self-service tools."}</div>
        <div class="admin-meta">
          <div class="admin-meta-item">
            <span class="admin-meta-label">${isAdminMode() ? "Admin ID" : "User ID"}</span>
            <span class="admin-meta-value">${activeProfile.id}</span>
          </div>
          <div class="admin-meta-item">
            <span class="admin-meta-label">Email</span>
            <span class="admin-meta-value">${currentUser?.email || activeProfile.email}</span>
          </div>
          <div class="admin-meta-item">
            <span class="admin-meta-label">Phone</span>
            <span class="admin-meta-value">${activeProfile.phone}</span>
          </div>
          <div class="admin-meta-item">
            <span class="admin-meta-label">Department</span>
            <span class="admin-meta-value">${activeProfile.department}</span>
          </div>
          <div class="admin-meta-item">
            <span class="admin-meta-label">Specialization</span>
            <span class="admin-meta-value">${activeProfile.specialization}</span>
          </div>
        </div>
      </div>
      <div class="card">
        <h2>Dashboard</h2>
        <div id="dash-summary"></div>
        <div class="chart-container" style="height: 340px;">
          <canvas id="vitalsChart"></canvas>
        </div>
        <div id="dash-recent"></div>
      </div>
    </div>`;

  const dashSummary = document.getElementById("dash-summary");
  const dashRecent = document.getElementById("dash-recent");

  try {
    // Fetch all data for summary
    const [vitalsRes, symptomsRes, medsRes, apptsRes] = await Promise.all([
      fetch(`${API}/vitals/${userId}`),
      fetch(`${API}/symptoms/${userId}`),
      fetch(`${API}/meds/${userId}`),
      fetch(`${API}/appointments/${userId}`)
    ]);

    const vitals = await vitalsRes.json();
    const symptoms = await symptomsRes.json();
    const meds = await medsRes.json();
    const appts = await apptsRes.json();

    // Summary
    dashSummary.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px;">
        <div style="text-align: center; padding: 16px; background: var(--bg); border-radius: 8px;">
          <div style="font-size: 24px; font-weight: bold; color: var(--primary);">${vitals.length}</div>
          <div class="small">Vitals Recorded</div>
        </div>
        <div style="text-align: center; padding: 16px; background: var(--bg); border-radius: 8px;">
          <div style="font-size: 24px; font-weight: bold; color: var(--secondary);">${symptoms.length}</div>
          <div class="small">Symptoms Logged</div>
        </div>
        <div style="text-align: center; padding: 16px; background: var(--bg); border-radius: 8px;">
          <div style="font-size: 24px; font-weight: bold; color: var(--success);">${meds.length}</div>
          <div class="small">Medications</div>
        </div>
        <div style="text-align: center; padding: 16px; background: var(--bg); border-radius: 8px;">
          <div style="font-size: 24px; font-weight: bold; color: var(--warning);">${appts.length}</div>
          <div class="small">Appointments</div>
        </div>
      </div>`;

    // Chart for vitals. Prefer BP trend, otherwise fall back to counts by type.
    const ctx = prepareChartCanvas('vitalsChart');
    const chartScale = Number(localStorage.getItem("hmsDisplayScale") || "1");
    const chartDpr = Math.max(2, (window.devicePixelRatio || 1) * chartScale);
    if (chartInstance) chartInstance.destroy();

    const bpData = vitals
      .filter(v => {
        const type = (v.type || '').toLowerCase();
        return type.includes('blood pressure') || type === 'bp' || type.includes('bp ');
      })
      .filter(v => String(v.value || '').includes('/'))
      .slice(-10);

    if (bpData.length > 0) {
      const labels = bpData.map(v => new Date(v.timestamp).toLocaleDateString());
      const values = bpData.map(v => parseFloat(String(v.value).split('/')[0]));

      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Blood Pressure (Systolic)',
            data: values,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.15)',
            tension: 0.25,
            fill: true
          }]
        },
        options: {
          responsive: false,
          maintainAspectRatio: false,
          devicePixelRatio: chartDpr,
          animation: false,
          transitions: {
            active: {
              animation: {
                duration: 0
              }
            }
          },
          plugins: {
            legend: { display: true }
          },
          scales: {
            y: { beginAtZero: false }
          }
        }
      });
    } else {
      const groupedVitals = vitals.reduce((acc, vital) => {
        const key = vital.type || 'Unknown';
        acc[key] = (acc[key] || 0) + 1;
        return acc;
      }, {});

      const labels = Object.keys(groupedVitals);
      const values = Object.values(groupedVitals);

      chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Vitals Logged',
            data: values,
            backgroundColor: [
              'rgba(37, 99, 235, 0.75)',
              'rgba(8, 145, 178, 0.75)',
              'rgba(16, 185, 129, 0.75)',
              'rgba(245, 158, 11, 0.75)',
              'rgba(239, 68, 68, 0.75)'
            ],
            borderRadius: 8
          }]
        },
        options: {
          responsive: false,
          maintainAspectRatio: false,
          devicePixelRatio: chartDpr,
          animation: false,
          transitions: {
            active: {
              animation: {
                duration: 0
              }
            }
          },
          plugins: {
            legend: { display: true }
          },
          scales: {
            y: { beginAtZero: true, ticks: { precision: 0 } }
          }
        }
      });
    }

    // Recent activity
    const recentVitals = vitals.slice(0, 5);
    const recentSymptoms = symptoms.slice(0, 3);
    const recentAppts = appts.slice(0, 3);

    dashRecent.innerHTML = `
      <h3>Recent Activity</h3>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
        <div>
          <h4>Latest Vitals</h4>
          ${recentVitals.map(v => `<div class="small">${v.timestamp} — <strong>${v.type}</strong>: ${v.value} ${v.unit}</div>`).join('') || '<div class="small">No vitals recorded</div>'}
        </div>
        <div>
          <h4>Recent Symptoms</h4>
          ${recentSymptoms.map(s => `<div class="small">${s.timestamp} — ${s.name} (${s.severity}/10)</div>`).join('') || '<div class="small">No symptoms logged</div>'}
        </div>
        <div>
          <h4>Upcoming Appointments</h4>
          ${recentAppts.map(a => `<div class="small">${a.datetime} — Dr. ${a.doctor}</div>`).join('') || '<div class="small">No appointments scheduled</div>'}
        </div>
      </div>`;

  } catch (error) {
    dashSummary.innerHTML = showError("Failed to load dashboard data. Please check if the backend is running.");
    console.error("Dashboard error:", error);
  }
}
// ---------- Vitals ---------
function renderVitals(){
  editingVitalId = null;
  main.innerHTML = `
    <div class="card">
      <h2>Vitals</h2>
      <form id="vitalForm">
        <div class="form-row">
          <div class="form-group">
            <label for="vitalType">Type</label>
            <select id="vitalType" name="type" required>
              <option value="">Select type</option>
              <option value="Blood Pressure">Blood Pressure</option>
              <option value="Heart Rate">Heart Rate</option>
              <option value="Temperature">Temperature</option>
              <option value="Weight">Weight</option>
              <option value="Height">Height</option>
              <option value="BMI">BMI</option>
            </select>
          </div>
          <div class="form-group">
            <label for="vitalValue">Value</label>
            <input id="vitalValue" name="value" placeholder="Enter value" required>
          </div>
          <div class="form-group">
            <label for="vitalUnit">Unit</label>
            <input id="vitalUnit" name="unit" placeholder="e.g., mmHg, bpm, °F">
          </div>
        </div>
        <div class="quick-actions">
          <button class="primary" type="submit" id="vitalSubmitBtn">Add Vital</button>
          <button class="secondary" type="button" id="vitalCancelBtn" style="display:none;">Cancel Edit</button>
        </div>
      </form>
      <div id="vitalsMessage"></div>
      <div id="vlist"></div>
    </div>`;

  document.getElementById("vitalForm").addEventListener("submit", async (e)=>{
    e.preventDefault();
    const f = e.target;
    const messageEl = document.getElementById("vitalsMessage");

    const body = {
      user_id: userId,
      type: f.type.value,
      value: f.value.value,
      unit: f.unit.value
    };

    try {
      const url = editingVitalId ? `${API}/vitals/${editingVitalId}` : `${API}/vitals`;
      const method = editingVitalId ? 'PUT' : 'POST';
      const res = await fetch(url, {method, headers:{'content-type':'application/json'}, body:JSON.stringify(body)});
      if (res.ok) {
        messageEl.innerHTML = showSuccess(editingVitalId ? "Vital updated successfully!" : "Vital added successfully!");
        f.reset();
        editingVitalId = null;
        document.getElementById("vitalSubmitBtn").textContent = "Add Vital";
        document.getElementById("vitalCancelBtn").style.display = "none";
        await loadVitalsList();
      } else {
        messageEl.innerHTML = showError("Failed to save vital.");
      }
    } catch (error) {
      messageEl.innerHTML = showError("Network error. Please try again.");
    }
  });

  document.getElementById("vitalCancelBtn").addEventListener("click", ()=>{
    editingVitalId = null;
    document.getElementById("vitalForm").reset();
    document.getElementById("vitalSubmitBtn").textContent = "Add Vital";
    document.getElementById("vitalCancelBtn").style.display = "none";
    document.getElementById("vitalsMessage").innerHTML = "";
  });

  loadVitalsList();
}

async function renderHealthGraph() {
  main.innerHTML = `
    <div class="card">
      <h2>Patient Health Graph</h2>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; margin-bottom: 24px;">
        <div class="stat-card error">
          <div class="stat-icon"><i class="fas fa-triangle-exclamation"></i></div>
          <div class="stat-info">
            <h4>Dangerous</h4>
            <div class="value" id="dangerCount">0</div>
          </div>
        </div>
        <div class="stat-card success">
          <div class="stat-icon"><i class="fas fa-heart-circle-check"></i></div>
          <div class="stat-info">
            <h4>Normal</h4>
            <div class="value" id="normalCount">0</div>
          </div>
        </div>
      </div>
      <div class="chart-container" style="height: 520px;">
        <canvas id="patientHealthChart"></canvas>
      </div>
      <div id="patientHealthList"></div>
    </div>
  `;

  const list = document.getElementById("patientHealthList");

  try {
    const res = await fetch(`${API}/patient-health-summary`);
    const data = await res.json();

    const dangerCount = data.filter(item => item.status === "danger").length;
    const normalCount = data.filter(item => item.status === "normal").length;
    document.getElementById("dangerCount").textContent = String(dangerCount);
    document.getElementById("normalCount").textContent = String(normalCount);

    const ctx = prepareChartCanvas("patientHealthChart");
    const chartScale = Number(localStorage.getItem("hmsDisplayScale") || "1");
    const chartDpr = Math.max(2, (window.devicePixelRatio || 1) * chartScale);
    if (chartInstance) chartInstance.destroy();
    chartInstance = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Dangerous", "Normal"],
        datasets: [{
          data: [dangerCount, normalCount],
          backgroundColor: ["#ef4444", "#10b981"],
          borderWidth: 0
        }]
      },
      options: {
        responsive: false,
        maintainAspectRatio: false,
        devicePixelRatio: chartDpr,
        animation: false,
        transitions: {
          active: {
            animation: {
              duration: 0
            }
          }
        },
        cutout: "52%",
        radius: "88%",
        layout: {
          padding: 18
        },
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              font: {
                size: 22,
                weight: "600"
              },
              padding: 24,
              boxWidth: 28,
              boxHeight: 28
            }
          }
        }
      }
    });

    list.innerHTML = `
      <div class="health-status-grid">
        ${data.map(patient => `
          <div class="health-status-card ${patient.status}">
            <div class="health-status-pill">${patient.status === "danger" ? "Danger" : "Normal"}</div>
            <h3>${patient.name}</h3>
            <div class="small">Patient ID: ${patient.patient_id}</div>
            <div class="small">Checkups: ${patient.checkup_count}</div>
            <p style="margin-top: 14px; font-size: 17px;">${patient.reason}</p>
          </div>
        `).join("") || '<div class="small">No patient health data available.</div>'}
      </div>
    `;
  } catch (error) {
    list.innerHTML = showError("Failed to load patient health graph.");
  }
}

async function loadVitalsList(){
  const container = document.getElementById("vlist");
  showLoading(container);

  try {
    const res = await fetch(`${API}/vitals/${userId}`);
    const data = await res.json();

    if (data.length === 0) {
      container.innerHTML = '<div class="small" style="text-align: center; padding: 24px;">No vitals recorded yet.</div>';
      return;
    }

    container.innerHTML = data.map(v => `
      <div class="list-item">
        <div class="content">
          <div><strong>${v.type}</strong> — ${v.value} ${v.unit || ''}</div>
          <div class="small">${new Date(v.timestamp).toLocaleString()}</div>
        </div>
        <div class="actions">
          <button class="btn-small btn-edit" onclick="editVital(${v.id}, '${escapeAttr(v.type)}', '${escapeAttr(v.value)}', '${escapeAttr(v.unit || '')}')">Edit</button>
          <button class="btn-small btn-delete" onclick="deleteVital(${v.id})">Delete</button>
        </div>
      </div>`).join("");
  } catch (error) {
    container.innerHTML = showError("Failed to load vitals.");
  }
}

function editVital(id, type, value, unit) {
  editingVitalId = id;
  const form = document.getElementById("vitalForm");
  form.type.value = type;
  form.value.value = value;
  form.unit.value = unit || "";
  document.getElementById("vitalSubmitBtn").textContent = "Update Vital";
  document.getElementById("vitalCancelBtn").style.display = "inline-flex";
  document.getElementById("vitalsMessage").innerHTML = showSuccess(`Editing vital record #${id}`);
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function deleteVital(id) {
  showModal("Delete Vital", "Are you sure you want to delete this vital record?", async () => {
    const res = await fetch(`${API}/vitals/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'ok') {
      document.getElementById("vitalsMessage").innerHTML = showSuccess("Vital deleted successfully!");
      await loadVitalsList();
    } else {
      document.getElementById("vitalsMessage").innerHTML = showError(result.message || "Failed to delete vital.");
    }
  });
}
// ---------- Symptoms ---------
function renderSymptoms(){
  main.innerHTML = `
    <div class="card">
      <h2>Symptoms</h2>
      <form id="symForm" class="form-row">
        <input name="name" placeholder="Symptom name" required>
        <select name="system">
          <option>Cardiovascular</option>
          <option>Respiratory</option>
          <option>Digestive</option>
          <option>Nervous</option>
        </select>
        <input name="severity" type="number" min="1" max="10" placeholder="severity 1-10" required>
        <input name="notes" placeholder="notes">
        <button class="primary">Log Symptom</button>
      </form>
      <div id="slist" class="small"></div>
    </div>`;
  document.getElementById("symForm").addEventListener("submit", async (e)=>{
    e.preventDefault();
    const f = e.target;
    const body = { user_id:userId, name:f.name.value, system:f.system.value, severity:Number(f.severity.value), notes: f.notes.value };
    await fetch(`${API}/symptoms`, {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify(body)});
    f.reset(); loadSymptomsList();
  });
  loadSymptomsList();
}
async function loadSymptomsList(){
  const res = await fetch(`${API}/symptoms/${userId}`);
  const data = await res.json();
  const container = document.getElementById("slist");
  container.innerHTML = data.map(s=>`<div class="list-item"><div><strong>${s.name}</strong> (${s.system}) severity:${s.severity}</div><div class="small">${s.timestamp}</div><div>${s.notes || ''}</div></div>`).join("");
}
// ---------- Medications ---------
function renderMeds(){
  main.innerHTML = `
    <div class="card">
      <h2>Medications</h2>
      <form id="medForm" class="form-row">
        <input name="name" placeholder="Medication name" required>
        <input name="dose" placeholder="Dose (e.g., 5mg)">
        <input name="schedule" placeholder="Schedule (e.g., once daily)">
        <input name="start_date" type="date">
        <button class="primary">Add Med</button>
      </form>
      <div id="medlist" class="small"></div>
    </div>`;
  document.getElementById("medForm").addEventListener("submit", async (e)=>{
    e.preventDefault();
    const f = e.target;
    const body = {
      user_id: userId,
      name: f.name.value,
      dose: f.dose.value,
      schedule: f.schedule.value,
      start_date: f.start_date.value
    };
    await fetch(`${API}/meds`, {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify(body)});
    f.reset(); loadMedsList();
  });
  loadMedsList();
}
async function loadMedsList(){
  const res = await fetch(`${API}/meds/${userId}`);
  const data = await res.json();
  document.getElementById("medlist").innerHTML = data.map(m=>`<div class="list-item"><strong>${m.name}</strong> ${m.dose} — ${m.schedule}<div class="small">start: ${m.start_date || '—'}</div></div>`).join("");
}
// ---------- Appointments ---------
function renderAppts(){
  main.innerHTML = `
    <div class="card">
      <h2>Appointments</h2>
      <form id="apptForm" class="form-row">
        <input name="doctor" placeholder="Doctor name" required>
        <input name="datetime" type="datetime-local" required>
        <select name="type"><option>in-person</option><option>telehealth</option></select>
        <input name="notes" placeholder="notes">
        <button class="primary">Book</button>
      </form>
      <div id="applist" class="small"></div>
    </div>`;
  document.getElementById("apptForm").addEventListener("submit", async (e)=>{
    e.preventDefault();
    const f = e.target;
    const body = {
      user_id: userId,
      doctor: f.doctor.value,
      datetime: f.datetime.value,
      type: f.type.value,
      notes: f.notes.value
    };
    await fetch(`${API}/appointments`, {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify(body)});
    f.reset(); loadApptsList();
  });
  loadApptsList();
}
async function loadApptsList(){
  const res = await fetch(`${API}/appointments/${userId}`);
  const data = await res.json();
  document.getElementById("applist").innerHTML = data.map(a=>`<div class="list-item"><strong>${a.doctor}</strong> — ${a.datetime} <div class="small">${a.type}</div></div>`).join("");
}
// ---------- Patients ---------
function renderPatients(){
  editingPatientId = null;
  main.innerHTML = `
    <div class="card">
      <h2>Patients</h2>
      <form id="patientForm">
        <div class="form-row">
          <div class="form-group">
            <label for="patientName">Name</label>
            <input id="patientName" name="name" placeholder="Full name" required>
          </div>
          <div class="form-group">
            <label for="patientDob">Date of Birth</label>
            <input id="patientDob" name="dob" type="date" required>
          </div>
          <div class="form-group">
            <label for="patientGender">Gender</label>
            <select id="patientGender" name="gender" required>
              <option value="">Select gender</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="patientPhone">Phone</label>
            <input id="patientPhone" name="phone" placeholder="Phone number" required>
          </div>
          <div class="form-group">
            <label for="patientEmail">Email</label>
            <input id="patientEmail" name="email" type="email" placeholder="Email address" required>
          </div>
          <div class="form-group">
            <label for="patientBloodType">Blood Type</label>
            <select id="patientBloodType" name="blood_type">
              <option value="">Select blood type</option>
              <option value="A+">A+</option>
              <option value="A-">A-</option>
              <option value="B+">B+</option>
              <option value="B-">B-</option>
              <option value="AB+">AB+</option>
              <option value="AB-">AB-</option>
              <option value="O+">O+</option>
              <option value="O-">O-</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="patientAddress">Address</label>
            <textarea id="patientAddress" name="address" placeholder="Full address"></textarea>
          </div>
          <div class="form-group">
            <label for="patientEmergencyContact">Emergency Contact</label>
            <input id="patientEmergencyContact" name="emergency_contact" placeholder="Emergency contact name">
          </div>
          <div class="form-group">
            <label for="patientEmergencyPhone">Emergency Phone</label>
            <input id="patientEmergencyPhone" name="emergency_phone" placeholder="Emergency phone">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="patientMedicalHistory">Medical History</label>
            <textarea id="patientMedicalHistory" name="medical_history" placeholder="Medical history"></textarea>
          </div>
          <div class="form-group">
            <label for="patientAllergies">Allergies</label>
            <textarea id="patientAllergies" name="allergies" placeholder="Known allergies"></textarea>
          </div>
        </div>
        <div class="quick-actions">
          <button class="primary" type="submit" id="patientSubmitBtn">Add Patient</button>
          <button class="secondary" type="button" id="patientCancelBtn" style="display:none;">Cancel Edit</button>
        </div>
      </form>
      <div id="patientMessage"></div>
      <div class="search-box">
        <i class="fas fa-search"></i>
        <input id="patientSearch" placeholder="Search by name, phone, email, or patient ID">
      </div>
      <div id="patientList"></div>
    </div>`;

  document.getElementById("patientForm").addEventListener("submit", async (e)=>{
    e.preventDefault();
    const f = e.target;
    const messageEl = document.getElementById("patientMessage");

    const body = {
      name: f.name.value,
      dob: f.dob.value,
      gender: f.gender.value,
      phone: f.phone.value,
      email: f.email.value,
      blood_type: f.blood_type.value,
      address: f.address.value,
      emergency_contact: f.emergency_contact.value,
      emergency_phone: f.emergency_phone.value,
      medical_history: f.medical_history.value,
      allergies: f.allergies.value
    };

    try {
      const url = editingPatientId ? `${API}/patients/${editingPatientId}` : `${API}/patients`;
      const method = editingPatientId ? 'PUT' : 'POST';
      const res = await fetch(url, {method, headers:{'content-type':'application/json'}, body:JSON.stringify(body)});
      if (res.ok) {
        messageEl.innerHTML = showSuccess(editingPatientId ? "Patient updated successfully!" : "Patient added successfully!");
        f.reset();
        editingPatientId = null;
        document.getElementById("patientSubmitBtn").textContent = "Add Patient";
        document.getElementById("patientCancelBtn").style.display = "none";
        await loadPatientsList();
      } else {
        messageEl.innerHTML = showError("Failed to save patient.");
      }
    } catch (error) {
      messageEl.innerHTML = showError("Network error. Please try again.");
    }
  });

  document.getElementById("patientCancelBtn").addEventListener("click", ()=>{
    editingPatientId = null;
    document.getElementById("patientForm").reset();
    document.getElementById("patientSubmitBtn").textContent = "Add Patient";
    document.getElementById("patientCancelBtn").style.display = "none";
    document.getElementById("patientMessage").innerHTML = "";
  });

  document.getElementById("patientSearch").addEventListener("input", (e) => {
    loadPatientsList(e.target.value);
  });

  loadPatientsList();
}

async function loadPatientsList(searchTerm = ""){
  const container = document.getElementById("patientList");
  showLoading(container);

  try {
    const res = await fetch(`${API}/patients`);
    const data = await res.json();
    const query = String(searchTerm).trim().toLowerCase();
    const filtered = query
      ? data.filter(p =>
          String(p.id).includes(query) ||
          String(p.name || "").toLowerCase().includes(query) ||
          String(p.phone || "").toLowerCase().includes(query) ||
          String(p.email || "").toLowerCase().includes(query)
        )
      : data;

    if (filtered.length === 0) {
      container.innerHTML = '<div class="small" style="text-align: center; padding: 24px;">No patients registered yet.</div>';
      return;
    }

    container.innerHTML = filtered.map(p => `
      <div class="list-item">
        <div class="content">
          <div><strong>${p.name}</strong> — ${p.email} | ${p.phone}</div>
          <div class="small">DOB: ${p.dob} | Gender: ${p.gender} | Blood Type: ${p.blood_type || 'N/A'}</div>
        </div>
        <div class="actions">
          <button class="btn-small btn-view" onclick="viewPatient(${p.id})">View Details</button>
          <button class="btn-small btn-edit" onclick="editPatient(${p.id})">Edit</button>
          <button class="btn-small btn-delete" onclick="deletePatient(${p.id})">Delete</button>
        </div>
      </div>`).join("");
  } catch (error) {
    container.innerHTML = showError("Failed to load patients.");
  }
}

function viewPatient(id) {
  // For now, just alert - can be expanded to show detailed view
  alert("View patient details functionality. ID: " + id);
}

function editPatient(id) {
  fetch(`${API}/patients/${id}`)
    .then(res => res.json())
    .then(patient => {
      editingPatientId = id;
      const form = document.getElementById("patientForm");
      form.name.value = patient.name || "";
      form.dob.value = patient.dob || "";
      form.gender.value = patient.gender || "";
      form.phone.value = patient.phone || "";
      form.email.value = patient.email || "";
      form.blood_type.value = patient.blood_type || "";
      form.address.value = patient.address || "";
      form.emergency_contact.value = patient.emergency_contact || "";
      form.emergency_phone.value = patient.emergency_phone || "";
      form.medical_history.value = patient.medical_history || "";
      form.allergies.value = patient.allergies || "";
      document.getElementById("patientSubmitBtn").textContent = "Update Patient";
      document.getElementById("patientCancelBtn").style.display = "inline-flex";
      document.getElementById("patientMessage").innerHTML = showSuccess(`Editing patient #${id}`);
      form.scrollIntoView({ behavior: "smooth", block: "start" });
    })
    .catch(error => {
      document.getElementById("patientMessage").innerHTML = showError("Failed to load patient for editing.");
      console.error("Edit patient error:", error);
    });
}

function deletePatient(id) {
  showModal("Delete Patient", "Are you sure you want to delete this patient?", async () => {
    const res = await fetch(`${API}/patients/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'ok') {
      document.getElementById("patientMessage").innerHTML = showSuccess("Patient deleted successfully!");
      await loadPatientsList(document.getElementById("patientSearch")?.value || "");
    } else {
      document.getElementById("patientMessage").innerHTML = showError(result.message || "Failed to delete patient.");
    }
  });
}

// ---------- Checkups ---------
function renderCheckups(){
  editingCheckupId = null;
  main.innerHTML = `
    <div class="card">
      <h2>Medical Checkups</h2>
      <form id="checkupForm">
        <div class="form-row">
          <div class="form-group">
            <label for="checkupPatientId">Patient ID</label>
            <input id="checkupPatientId" name="patient_id" type="number" placeholder="Patient ID" required>
          </div>
          <div class="form-group">
            <label for="checkupTestType">Test Type</label>
            <select id="checkupTestType" name="test_type" required>
              <option value="">Select test type</option>
              <option value="Blood Test">Blood Test</option>
              <option value="Urine Test">Urine Test</option>
              <option value="X-Ray">X-Ray</option>
              <option value="MRI">MRI</option>
              <option value="CT Scan">CT Scan</option>
              <option value="ECG">ECG</option>
              <option value="Ultrasound">Ultrasound</option>
            </select>
          </div>
          <div class="form-group">
            <label for="checkupTestName">Test Name</label>
            <input id="checkupTestName" name="test_name" placeholder="Specific test name" required>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="checkupValue">Value</label>
            <input id="checkupValue" name="value" placeholder="Test result value" required>
          </div>
          <div class="form-group">
            <label for="checkupUnit">Unit</label>
            <input id="checkupUnit" name="unit" placeholder="Unit (e.g., mg/dL, mmHg)" required>
          </div>
          <div class="form-group">
            <label for="checkupReferenceRange">Reference Range</label>
            <input id="checkupReferenceRange" name="reference_range" placeholder="Normal range">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="checkupResultStatus">Result Status</label>
            <select id="checkupResultStatus" name="result_status">
              <option value="Normal">Normal</option>
              <option value="Abnormal">Abnormal</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
          <div class="form-group">
            <label for="checkupPerformedBy">Performed By</label>
            <input id="checkupPerformedBy" name="performed_by" placeholder="Doctor/Lab technician name">
          </div>
        </div>
        <div class="quick-actions">
          <button class="primary" type="submit" id="checkupSubmitBtn">Add Checkup Result</button>
          <button class="secondary" type="button" id="checkupCancelBtn" style="display:none;">Cancel Edit</button>
        </div>
      </form>
      <div id="checkupMessage"></div>
      <div class="form-row">
        <div class="form-group">
          <label for="checkupFilterPatientId">View Patient ID</label>
          <input id="checkupFilterPatientId" type="number" value="1" placeholder="Patient ID">
        </div>
        <div class="form-group" style="align-self:end;">
          <button class="secondary" type="button" id="checkupFilterBtn">Load Checkups</button>
        </div>
      </div>
      <div id="checkupList"></div>
    </div>`;

  document.getElementById("checkupForm").addEventListener("submit", async (e)=>{
    e.preventDefault();
    const f = e.target;
    const messageEl = document.getElementById("checkupMessage");

    const body = {
      patient_id: parseInt(f.patient_id.value),
      test_type: f.test_type.value,
      test_name: f.test_name.value,
      value: f.value.value,
      unit: f.unit.value,
      reference_range: f.reference_range.value,
      result_status: f.result_status.value,
      performed_by: f.performed_by.value
    };

    try {
      const url = editingCheckupId ? `${API}/checkup-record/${editingCheckupId}` : `${API}/checkups`;
      const method = editingCheckupId ? 'PUT' : 'POST';
      const res = await fetch(url, {method, headers:{'content-type':'application/json'}, body:JSON.stringify(body)});
      if (res.ok) {
        messageEl.innerHTML = showSuccess(editingCheckupId ? "Checkup updated successfully!" : "Checkup result added successfully!");
        f.reset();
        editingCheckupId = null;
        document.getElementById("checkupSubmitBtn").textContent = "Add Checkup Result";
        document.getElementById("checkupCancelBtn").style.display = "none";
        await loadCheckupsList();
      } else {
        messageEl.innerHTML = showError("Failed to save checkup result.");
      }
    } catch (error) {
      messageEl.innerHTML = showError("Network error. Please try again.");
    }
  });

  document.getElementById("checkupCancelBtn").addEventListener("click", ()=>{
    editingCheckupId = null;
    document.getElementById("checkupForm").reset();
    document.getElementById("checkupSubmitBtn").textContent = "Add Checkup Result";
    document.getElementById("checkupCancelBtn").style.display = "none";
    document.getElementById("checkupMessage").innerHTML = "";
  });

  document.getElementById("checkupFilterBtn").addEventListener("click", ()=>{
    loadCheckupsList(getNumericValue("checkupFilterPatientId", 1));
  });

  loadCheckupsList();
}

async function loadCheckupsList(patientId = 1){
  const container = document.getElementById("checkupList");
  showLoading(container);

  try {
    const res = await fetch(`${API}/checkups/${patientId}`);
    const data = await res.json();

    if (data.length === 0) {
      container.innerHTML = '<div class="small" style="text-align: center; padding: 24px;">No checkup results recorded for this patient yet.</div>';
      return;
    }

    container.innerHTML = data.map(c => `
      <div class="list-item">
        <div class="content">
          <div><strong>${c.test_name}</strong> (${c.test_type}) — ${c.value} ${c.unit}</div>
          <div class="small">Date: ${c.timestamp} | Status: ${c.result_status} | Performed by: ${c.performed_by || 'N/A'}</div>
        </div>
        <div class="actions">
          <button class="btn-small btn-view" onclick="viewCheckup(${c.id})">View Details</button>
          <button class="btn-small btn-edit" onclick="editCheckup(${c.id}, ${c.patient_id}, '${escapeAttr(c.test_type)}', '${escapeAttr(c.test_name)}', '${escapeAttr(c.value)}', '${escapeAttr(c.unit)}', '${escapeAttr(c.reference_range || '')}', '${escapeAttr(c.result_status || 'Normal')}', '${escapeAttr(c.performed_by || '')}')">Edit</button>
          <button class="btn-small btn-delete" onclick="deleteCheckup(${c.id})">Delete</button>
        </div>
      </div>`).join("");
  } catch (error) {
    container.innerHTML = showError("Failed to load checkup results.");
  }
}

function viewCheckup(id) {
  alert("View checkup details functionality. ID: " + id);
}

function editCheckup(id, patientId, testType, testName, value, unit, referenceRange, resultStatus, performedBy) {
  editingCheckupId = id;
  const form = document.getElementById("checkupForm");
  form.patient_id.value = patientId;
  form.test_type.value = testType;
  form.test_name.value = testName;
  form.value.value = value;
  form.unit.value = unit || "";
  form.reference_range.value = referenceRange || "";
  form.result_status.value = resultStatus || "Normal";
  form.performed_by.value = performedBy || "";
  document.getElementById("checkupSubmitBtn").textContent = "Update Checkup";
  document.getElementById("checkupCancelBtn").style.display = "inline-flex";
  document.getElementById("checkupMessage").innerHTML = showSuccess(`Editing checkup #${id}`);
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function deleteCheckup(id) {
  showModal("Delete Checkup", "Are you sure you want to delete this checkup record?", async () => {
    const res = await fetch(`${API}/checkup-record/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'ok') {
      document.getElementById("checkupMessage").innerHTML = showSuccess("Checkup deleted successfully!");
      await loadCheckupsList(getNumericValue("checkupFilterPatientId", 1));
    } else {
      document.getElementById("checkupMessage").innerHTML = showError(result.message || "Failed to delete checkup.");
    }
  });
}

// ---------- Hospitality ---------
function renderHospitality(){
  editingHospitalityId = null;
  main.innerHTML = `
    <div class="card">
      <h2>Hospital Stay Information</h2>
      <form id="hospitalityForm">
        <div class="form-row">
          <div class="form-group">
            <label for="hospPatientId">Patient ID</label>
            <input id="hospPatientId" name="patient_id" type="number" placeholder="Patient ID" required>
          </div>
          <div class="form-group">
            <label for="hospAdmissionDate">Admission Date</label>
            <input id="hospAdmissionDate" name="admission_date" type="date" required>
          </div>
          <div class="form-group">
            <label for="hospDischargeDate">Discharge Date</label>
            <input id="hospDischargeDate" name="discharge_date" type="date">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="hospRoomNumber">Room Number</label>
            <input id="hospRoomNumber" name="room_number" placeholder="Room number" required>
          </div>
          <div class="form-group">
            <label for="hospRoomType">Room Type</label>
            <select id="hospRoomType" name="room_type" required>
              <option value="">Select room type</option>
              <option value="General">General</option>
              <option value="Private">Private</option>
              <option value="Semi-Private">Semi-Private</option>
              <option value="ICU">ICU</option>
              <option value="CCU">CCU</option>
            </select>
          </div>
          <div class="form-group">
            <label for="hospDailyRate">Daily Rate ($)</label>
            <input id="hospDailyRate" name="daily_rate" type="number" step="0.01" placeholder="Daily rate" required>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="hospServices">Services</label>
            <textarea id="hospServices" name="services" placeholder="Services provided during stay"></textarea>
          </div>
          <div class="form-group">
            <label for="hospStatus">Status</label>
            <select id="hospStatus" name="status">
              <option value="Active">Active</option>
              <option value="Discharged">Discharged</option>
              <option value="Transferred">Transferred</option>
            </select>
          </div>
        </div>
        <div class="quick-actions">
          <button class="primary" type="submit" id="hospitalitySubmitBtn">Add Hospital Stay</button>
          <button class="secondary" type="button" id="hospitalityCancelBtn" style="display:none;">Cancel Edit</button>
        </div>
      </form>
      <div id="hospitalityMessage"></div>
      <div class="form-row">
        <div class="form-group">
          <label for="hospitalityFilterPatientId">View Patient ID</label>
          <input id="hospitalityFilterPatientId" type="number" value="1" placeholder="Patient ID">
        </div>
        <div class="form-group" style="align-self:end;">
          <button class="secondary" type="button" id="hospitalityFilterBtn">Load Hospital Stays</button>
        </div>
      </div>
      <div id="hospitalityList"></div>
    </div>`;

  document.getElementById("hospitalityForm").addEventListener("submit", async (e)=>{
    e.preventDefault();
    const f = e.target;
    const messageEl = document.getElementById("hospitalityMessage");

    const body = {
      patient_id: parseInt(f.patient_id.value),
      admission_date: f.admission_date.value,
      discharge_date: f.discharge_date.value || null,
      room_number: f.room_number.value,
      room_type: f.room_type.value,
      daily_rate: parseFloat(f.daily_rate.value),
      services: f.services.value,
      status: f.status.value
    };

    try {
      const url = editingHospitalityId ? `${API}/hospitality-record/${editingHospitalityId}` : `${API}/hospitality`;
      const method = editingHospitalityId ? 'PUT' : 'POST';
      const res = await fetch(url, {method, headers:{'content-type':'application/json'}, body:JSON.stringify(body)});
      if (res.ok) {
        messageEl.innerHTML = showSuccess(editingHospitalityId ? "Hospital stay updated successfully!" : "Hospital stay added successfully!");
        f.reset();
        editingHospitalityId = null;
        document.getElementById("hospitalitySubmitBtn").textContent = "Add Hospital Stay";
        document.getElementById("hospitalityCancelBtn").style.display = "none";
        await loadHospitalityList();
      } else {
        messageEl.innerHTML = showError("Failed to save hospital stay.");
      }
    } catch (error) {
      messageEl.innerHTML = showError("Network error. Please try again.");
    }
  });

  document.getElementById("hospitalityCancelBtn").addEventListener("click", ()=>{
    editingHospitalityId = null;
    document.getElementById("hospitalityForm").reset();
    document.getElementById("hospitalitySubmitBtn").textContent = "Add Hospital Stay";
    document.getElementById("hospitalityCancelBtn").style.display = "none";
    document.getElementById("hospitalityMessage").innerHTML = "";
  });

  document.getElementById("hospitalityFilterBtn").addEventListener("click", ()=>{
    loadHospitalityList(getNumericValue("hospitalityFilterPatientId", 1));
  });

  loadHospitalityList();
}

async function loadHospitalityList(patientId = 1){
  const container = document.getElementById("hospitalityList");
  showLoading(container);

  try {
    const res = await fetch(`${API}/hospitality/${patientId}`);
    const data = await res.json();

    if (data.length === 0) {
      container.innerHTML = '<div class="small" style="text-align: center; padding: 24px;">No hospital stays recorded for this patient yet.</div>';
      return;
    }

    container.innerHTML = data.map(h => `
      <div class="list-item">
        <div class="content">
          <div><strong>Room ${h.room_number}</strong> (${h.room_type}) — $${h.daily_rate}/day</div>
          <div class="small">Admission: ${h.admission_date} | Discharge: ${h.discharge_date || 'Ongoing'} | Status: ${h.status}</div>
        </div>
        <div class="actions">
          <button class="btn-small btn-view" onclick="viewHospitality(${h.id})">View Details</button>
          <button class="btn-small btn-edit" onclick="editHospitality(${h.id}, ${h.patient_id}, '${escapeAttr(h.admission_date)}', '${escapeAttr(h.discharge_date || '')}', '${escapeAttr(h.room_number)}', '${escapeAttr(h.room_type)}', '${escapeAttr(String(h.daily_rate || ''))}', '${escapeAttr(h.services || '')}', '${escapeAttr(h.status || 'Active')}')">Edit</button>
          <button class="btn-small btn-delete" onclick="deleteHospitality(${h.id})">Delete</button>
        </div>
      </div>`).join("");
  } catch (error) {
    container.innerHTML = showError("Failed to load hospital stays.");
  }
}

function viewHospitality(id) {
  alert("View hospitality details functionality. ID: " + id);
}

function editHospitality(id, patientId, admissionDate, dischargeDate, roomNumber, roomType, dailyRate, services, status) {
  editingHospitalityId = id;
  const form = document.getElementById("hospitalityForm");
  form.patient_id.value = patientId;
  form.admission_date.value = admissionDate || "";
  form.discharge_date.value = dischargeDate || "";
  form.room_number.value = roomNumber || "";
  form.room_type.value = roomType || "";
  form.daily_rate.value = dailyRate || "";
  form.services.value = services || "";
  form.status.value = status || "Active";
  document.getElementById("hospitalitySubmitBtn").textContent = "Update Hospital Stay";
  document.getElementById("hospitalityCancelBtn").style.display = "inline-flex";
  document.getElementById("hospitalityMessage").innerHTML = showSuccess(`Editing hospital stay #${id}`);
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function deleteHospitality(id) {
  showModal("Delete Hospital Stay", "Are you sure you want to delete this hospital stay record?", async () => {
    const res = await fetch(`${API}/hospitality-record/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'ok') {
      document.getElementById("hospitalityMessage").innerHTML = showSuccess("Hospital stay deleted successfully!");
      await loadHospitalityList(getNumericValue("hospitalityFilterPatientId", 1));
    } else {
      document.getElementById("hospitalityMessage").innerHTML = showError(result.message || "Failed to delete hospital stay.");
    }
  });
}

// ---------- Bills ---------
function renderBills(){
  editingBillId = null;
  main.innerHTML = `
    <div class="card">
      <h2>Billing</h2>
      <form id="billForm">
        <div class="form-row">
          <div class="form-group">
            <label for="billPatientId">Patient ID</label>
            <input id="billPatientId" name="patient_id" type="number" placeholder="Patient ID" required>
          </div>
          <div class="form-group">
            <label for="billDate">Bill Date</label>
            <input id="billDate" name="bill_date" type="date" required>
          </div>
          <div class="form-group">
            <label for="billPaymentStatus">Payment Status</label>
            <select id="billPaymentStatus" name="payment_status">
              <option value="Pending">Pending</option>
              <option value="Paid">Paid</option>
              <option value="Overdue">Overdue</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="billSubtotal">Subtotal ($)</label>
            <input id="billSubtotal" name="subtotal" type="number" step="0.01" placeholder="Subtotal amount" required>
          </div>
          <div class="form-group">
            <label for="billTaxRate">Tax Rate (%)</label>
            <input id="billTaxRate" name="tax_rate" type="number" step="0.01" placeholder="Tax rate (e.g., 0.08 for 8%)" value="0.08">
          </div>
          <div class="form-group">
            <label for="billTaxAmount">Tax Amount ($)</label>
            <input id="billTaxAmount" name="tax_amount" type="number" step="0.01" placeholder="Tax amount">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="billTotalAmount">Total Amount ($)</label>
            <input id="billTotalAmount" name="total_amount" type="number" step="0.01" placeholder="Total amount" required>
          </div>
          <div class="form-group">
            <label for="billItemizedCharges">Itemized Charges (JSON)</label>
            <textarea id="billItemizedCharges" name="itemized_charges" placeholder='[{"description": "Consultation", "quantity": 1, "unit_price": 150.00, "total": 150.00}]' rows="3"></textarea>
          </div>
        </div>
        <div class="quick-actions">
          <button class="primary" type="submit" id="billSubmitBtn">Create Bill</button>
          <button class="secondary" type="button" id="billCancelBtn" style="display:none;">Cancel Edit</button>
        </div>
      </form>
      <div id="billMessage"></div>
      <div class="form-row">
        <div class="form-group">
          <label for="billFilterPatientId">View Patient ID</label>
          <input id="billFilterPatientId" type="number" value="1" placeholder="Patient ID">
        </div>
        <div class="form-group" style="align-self:end;">
          <button class="secondary" type="button" id="billFilterBtn">Load Bills</button>
        </div>
      </div>
      <div id="billList"></div>
    </div>`;

  document.getElementById("billForm").addEventListener("submit", async (e)=>{
    e.preventDefault();
    const f = e.target;
    const messageEl = document.getElementById("billMessage");

    const body = {
      patient_id: parseInt(f.patient_id.value),
      bill_date: f.bill_date.value,
      payment_status: f.payment_status.value,
      subtotal: parseFloat(f.subtotal.value),
      tax_rate: parseFloat(f.tax_rate.value),
      tax_amount: parseFloat(f.tax_amount.value) || 0,
      total_amount: parseFloat(f.total_amount.value),
      itemized_charges: f.itemized_charges.value || '[]'
    };

    try {
      const url = editingBillId ? `${API}/bill-record/${editingBillId}` : `${API}/bills`;
      const method = editingBillId ? 'PUT' : 'POST';
      const res = await fetch(url, {method, headers:{'content-type':'application/json'}, body:JSON.stringify(body)});
      if (res.ok) {
        messageEl.innerHTML = showSuccess(editingBillId ? "Bill updated successfully!" : "Bill created successfully!");
        f.reset();
        editingBillId = null;
        document.getElementById("billSubmitBtn").textContent = "Create Bill";
        document.getElementById("billCancelBtn").style.display = "none";
        await loadBillsList();
      } else {
        messageEl.innerHTML = showError("Failed to save bill.");
      }
    } catch (error) {
      messageEl.innerHTML = showError("Network error. Please try again.");
    }
  });

  document.getElementById("billCancelBtn").addEventListener("click", ()=>{
    editingBillId = null;
    document.getElementById("billForm").reset();
    document.getElementById("billSubmitBtn").textContent = "Create Bill";
    document.getElementById("billCancelBtn").style.display = "none";
    document.getElementById("billMessage").innerHTML = "";
  });

  document.getElementById("billFilterBtn").addEventListener("click", ()=>{
    loadBillsList(getNumericValue("billFilterPatientId", 1));
  });

  loadBillsList();
}

async function loadBillsList(patientId = 1){
  const container = document.getElementById("billList");
  showLoading(container);

  try {
    const res = await fetch(`${API}/bills/${patientId}`);
    const data = await res.json();

    if (data.length === 0) {
      container.innerHTML = '<div class="small" style="text-align: center; padding: 24px;">No bills recorded for this patient yet.</div>';
      return;
    }

    container.innerHTML = data.map(b => `
      <div class="list-item">
        <div class="content">
          <div><strong>Bill Date:</strong> ${b.bill_date} | <strong>Total:</strong> $${b.total_amount.toFixed(2)}</div>
          <div class="small">Status: ${b.payment_status} | Subtotal: $${b.subtotal.toFixed(2)} | Tax: $${b.tax_amount.toFixed(2)}</div>
        </div>
        <div class="actions">
          <button class="btn-small btn-view" onclick="viewBill(${b.id})">View Details</button>
          <button class="btn-small btn-edit" onclick="editBill(${b.id}, ${b.patient_id}, '${escapeAttr(b.bill_date || '')}', '${escapeAttr(b.payment_status || 'Pending')}', '${escapeAttr(String(b.subtotal || ''))}', '${escapeAttr(String(b.tax_rate || ''))}', '${escapeAttr(String(b.tax_amount || ''))}', '${escapeAttr(String(b.total_amount || ''))}', '${escapeAttr(b.itemized_charges || '[]')}')">Edit</button>
          <button class="btn-small btn-delete" onclick="deleteBill(${b.id})">Delete</button>
          <button class="btn-small btn-notify" onclick="sendBillNotification(${b.patient_id})">Send Notification</button>
        </div>
      </div>`).join("");
  } catch (error) {
    container.innerHTML = showError("Failed to load bills.");
  }
}

function viewBill(id) {
  alert("View bill details functionality. ID: " + id);
}

function editBill(id, patientId, billDate, paymentStatus, subtotal, taxRate, taxAmount, totalAmount, itemizedCharges) {
  editingBillId = id;
  const form = document.getElementById("billForm");
  form.patient_id.value = patientId;
  form.bill_date.value = billDate ? String(billDate).slice(0, 10) : "";
  form.payment_status.value = paymentStatus || "Pending";
  form.subtotal.value = subtotal || "";
  form.tax_rate.value = taxRate || "";
  form.tax_amount.value = taxAmount || "";
  form.total_amount.value = totalAmount || "";
  form.itemized_charges.value = itemizedCharges || "[]";
  document.getElementById("billSubmitBtn").textContent = "Update Bill";
  document.getElementById("billCancelBtn").style.display = "inline-flex";
  document.getElementById("billMessage").innerHTML = showSuccess(`Editing bill #${id}`);
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function deleteBill(id) {
  showModal("Delete Bill", "Are you sure you want to delete this bill?", async () => {
    const res = await fetch(`${API}/bill-record/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'ok') {
      document.getElementById("billMessage").innerHTML = showSuccess("Bill deleted successfully!");
      await loadBillsList(getNumericValue("billFilterPatientId", 1));
    } else {
      document.getElementById("billMessage").innerHTML = showError(result.message || "Failed to delete bill.");
    }
  });
}

async function sendBillNotification(patientId) {
  try {
    const res = await fetch(`${API}/send-bill-notification/${patientId}`, {method: 'POST'});
    const result = await res.json();
    if (result.status === 'success') {
      alert("Bill notification sent successfully!");
    } else {
      alert("Failed to send bill notification: " + result.message);
    }
  } catch (error) {
    alert("Error sending bill notification: " + error.message);
  }
}

// ---------- Reports ---------
function renderReports(){
  main.innerHTML = `
    <div class="card">
      <h2>Reports</h2>
      <div class="form-row">
        <div class="form-group">
          <label for="reportPatientId">Patient ID</label>
          <input id="reportPatientId" name="patient_id" type="number" placeholder="Patient ID" value="1">
        </div>
      </div>
      <div style="display: flex; gap: 16px; margin-bottom: 24px;">
        <button id="genHealthReport" class="primary">Generate Health Report</button>
        <button id="genPatientReport" class="primary">Generate Patient Bill Report</button>
        <button id="sendPatientReport" class="secondary">Send Patient Report Email</button>
        <button id="sendReportToAdmin" class="secondary">Send Report To Admin</button>
      </div>
      <div id="reportMessage"></div>
    </div>`;

  document.getElementById("genHealthReport").addEventListener("click", async ()=>{
    const patientId = document.getElementById("reportPatientId").value || 1;
    const url = `${API}/report/${patientId}`;
    const res = await fetch(url);
    if (!res.ok) return alert('Failed to generate health report');
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `health-report-patient${patientId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    document.getElementById("reportMessage").innerText = "Health report downloaded.";
  });

  document.getElementById("genPatientReport").addEventListener("click", async ()=>{
    const patientId = document.getElementById("reportPatientId").value || 1;
    const url = `${API}/patient-report/${patientId}`;
    const res = await fetch(url);
    if (!res.ok) return alert('Failed to generate patient bill report');
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `patient-bill-report-${patientId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    document.getElementById("reportMessage").innerText = "Patient bill report downloaded.";
  });

  document.getElementById("sendPatientReport").addEventListener("click", async ()=>{
    const patientId = document.getElementById("reportPatientId").value || 1;
    try {
      const res = await fetch(`${API}/send-patient-report/${patientId}`, {method: 'POST'});
      const result = await res.json();
      if (result.status === 'success') {
        document.getElementById("reportMessage").innerText = "Patient report email sent successfully!";
      } else {
        document.getElementById("reportMessage").innerText = "Failed to send patient report email: " + result.message;
      }
    } catch (error) {
      document.getElementById("reportMessage").innerText = "Error sending patient report email: " + error.message;
    }
  });

  document.getElementById("sendReportToAdmin").addEventListener("click", async ()=>{
    const patientId = document.getElementById("reportPatientId").value || 1;
    try {
      const res = await fetch(`${API}/send-report-to-admin/${patientId}`, {method: 'POST'});
      const result = await res.json();
      if (result.status === 'success') {
        document.getElementById("reportMessage").innerText = "Report sent to admin successfully.";
      } else {
        document.getElementById("reportMessage").innerText = "Failed to send report to admin: " + result.message;
      }
    } catch (error) {
      document.getElementById("reportMessage").innerText = "Error sending report to admin: " + error.message;
    }
  });
}

// Initialize the app
initAuth()

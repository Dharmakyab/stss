/**
 * Sambhota Tibetan Schools Society (STSS) Teaching Repository & Maths Hub Client
 */

// Application State
const state = {
  resources: [],
  schools: [],
  templates: [],
  users: [
    { name: "Tashi", role: "Teacher", school: "STSS Chauntra", designation: "Mathematics Teacher" },
    { name: "Dolma", role: "Teacher", school: "STSS Paonta Sahib", designation: "Senior Mathematics Teacher" },
    { name: "Tenzin", role: "Moderator", school: "STSS Dharamshala (Petoen)", designation: "Curriculum & Copyright Moderator" },
    { name: "Lhamo", role: "Admin", school: "STSS Central Education Council", designation: "School Administrator" }
  ],
  currentUser: { name: "Tashi", role: "Teacher", school: "STSS Chauntra", designation: "Mathematics Teacher" },
  userFavorites: new Set(),
  activeStage: "",
  activeSubject: "",
  activeGrade: "",
  activeRating: "",
  activeType: "",
  activeLanguage: "",
  activeSchool: "",
  searchQuery: "",
  currentSort: "newest",
  currentLang: "en", // 'en' or 'bo'
  currentPreviewResource: null,
  activeView: "browse"
};

// Bilingual Dictionary
const i18n = {
  en: {
    hero_title: "Empowering STSS Educators Across India",
    hero_subtitle: "Curated lesson plans, bilingual worksheets, assessment papers, and SEE Learning resources from Sambhota schools.",
    upload_btn: "Upload Resource",
    filter_title: "Filter Resources",
    reset_btn: "Reset All",
    stage_label: "Education Stage",
    subject_label: "Subject / སློབ་ཚན།",
    grade_label: "Specific Class",
    type_label: "Resource Type",
    language_label: "Medium / Language",
    school_label: "STSS School / Institution",
    tab_browse: "Browse Resources",
    tab_templates: "Lesson Plan Templates",
    tab_curriculum: "Curriculum Framework",
    tab_stats: "Repository Analytics",
    modal_upload_title: "Contribute Teaching Resource",
    preview_btn: "Read / Preview",
    download_btn: "Download"
  },
  bo: {
    hero_title: "རྒྱ་གར་ཁུལ་གྱི་སམ་བྷོ་ཊའི་དགེ་རྒན་རྣམས་ཀྱི་སློབ་ཁྲིད་མཛོད་ཁང་།",
    hero_subtitle: "སམ་བྷོ་ཊ་བོད་སློབ་ཁག་གི་ཉིན་རེའི་སློབ་ཚན་འཆར་གཞི་དང་། ལས་ཤོག རྒྱུགས་གཞི། བཟང་སྤྱོད་ཤེས་ཡོན་གྱི་སློབ་ཁྲིད་མཐུན་རྐྱེན་ཕྱོགས་བསྡུས།",
    upload_btn: "མཐུན་རྐྱེན་ཡར་འཇུག",
    filter_title: "འཚོལ་བསྡུ་དབྱེ་འབྱེད།",
    reset_btn: "སླར་གསོ།",
    stage_label: "སློབ་གྲྭའི་རིམ་པ།",
    subject_label: "སློབ་ཚན།",
    grade_label: "འཛིན་གྲྭ།",
    type_label: "རྣམ་གྲངས།",
    language_label: "སྐད་ཡིག",
    school_label: "སམ་བྷོ་ཊའི་སློབ་ཁག",
    tab_browse: "མཐུན་རྐྱེན་འཚོལ་བསྡུ།",
    tab_templates: "འཆར་གཞིའི་དཔེ་གཞི།",
    tab_curriculum: "བསླབ་གཞིའི་སྒྲོམ་གཞི།",
    tab_stats: "མཛོད་ཁང་གནས་སྡུད།",
    modal_upload_title: "སློབ་ཁྲིད་མཐུན་རྐྱེན་གསར་པ་འཇུག་པ།",
    preview_btn: "ལྟ་ཀློག",
    download_btn: "ཕབ་ལེན།"
  }
};

// Initialization on DOM Load
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  loadSchools();
  loadUserFavorites();
  loadResources();
  loadTemplates();
  loadStats();
  loadModerationQueue();
  updateFormDefaultsForCurrentUser();
});

// Event Listeners
function initEventListeners() {
  const searchInput = document.getElementById("searchInput");
  let debounceTimer;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    const val = e.target.value.trim();
    document.getElementById("searchClearBtn").style.display = val ? "block" : "none";
    debounceTimer = setTimeout(() => {
      state.searchQuery = val;
      loadResources();
    }, 250);
  });
}

function clearSearch() {
  const input = document.getElementById("searchInput");
  input.value = "";
  document.getElementById("searchClearBtn").style.display = "none";
  state.searchQuery = "";
  loadResources();
}

function toggleLanguage() {
  state.currentLang = state.currentLang === "en" ? "bo" : "en";
  document.getElementById("langLabel").textContent = state.currentLang === "en" ? "བོད་ཡིག" : "English";
  
  const dict = i18n[state.currentLang];
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });
}

// Persona Switcher (Module A & F)
function onPersonaChanged(userName) {
  if (userName === "Guest") {
    state.currentUser = { name: "Guest", role: "Guest", school: "", designation: "Guest Educator" };
  } else {
    const found = state.users.find(u => u.name === userName);
    if (found) {
      state.currentUser = found;
    } else {
      state.currentUser = { name: userName, role: "Teacher", school: "STSS Network", designation: "Educator" };
    }
  }

  // Update Moderation Tab visibility (Only visible to Moderator & Admin)
  const modTab = document.getElementById("tab-moderation");
  if (modTab) {
    const canModerate = state.currentUser.role === "Moderator" || state.currentUser.role === "Admin";
    modTab.style.display = canModerate ? "inline-flex" : "none";
    if (!canModerate && state.activeView === "moderation") {
      switchView("browse");
    }
  }

  const favUserEl = document.getElementById("favUserName");
  if (favUserEl) favUserEl.textContent = state.currentUser.name;

  updateFormDefaultsForCurrentUser();
  loadUserFavorites();

  // If on favorites tab, refresh
  if (state.activeView === "favorites") {
    loadFavoritesView();
  }
}

// STSS Single Sign-On Simulation (PRD Screen 01 & Module A)
function openLoginModal() {
  document.getElementById("loginModal").classList.add("active");
}

function closeLoginModal() {
  document.getElementById("loginModal").classList.remove("active");
}

function performSSOLogin() {
  const selected = document.getElementById("quickLoginSelect").value;
  document.getElementById("userPersonaSelect").value = selected;
  onPersonaChanged(selected);
  closeLoginModal();
  alert(`Signed in successfully via Microsoft Entra ID as ${selected} (${state.currentUser.designation})!`);
}

function updateFormDefaultsForCurrentUser() {
  const formAuthor = document.getElementById("formAuthor");
  const formRole = document.getElementById("formRole");
  const formSchool = document.getElementById("formSchool");

  if (formAuthor) formAuthor.value = state.currentUser.name;
  if (formRole) formRole.value = state.currentUser.designation;
  if (formSchool && state.currentUser.school) {
    for (let opt of formSchool.options) {
      if (opt.value === state.currentUser.school) {
        formSchool.value = opt.value;
        break;
      }
    }
  }
}

async function loadUserFavorites() {
  try {
    const res = await fetch(`/api/favorites?user_name=${encodeURIComponent(state.currentUser.name)}`);
    const data = await res.json();
    state.userFavorites = new Set(data.favorite_ids || []);
  } catch (err) {
    console.error("Error loading favorites:", err);
  }
}

// Stage Pill Filter
function setStageFilter(stage) {
  state.activeStage = stage;
  const container = document.getElementById("stagePillsContainer");
  container.querySelectorAll(".stage-pill").forEach((btn) => {
    if (btn.getAttribute("data-stage") === stage) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
  loadResources();
}

// Trigger Search from dropdowns
function triggerSearch() {
  state.activeSubject = document.getElementById("subjectSelect").value;
  state.activeGrade = document.getElementById("gradeSelect").value;
  state.activeRating = document.getElementById("ratingSelect") ? document.getElementById("ratingSelect").value : "";
  state.activeType = document.getElementById("typeSelect").value;
  state.activeLanguage = document.getElementById("languageSelect").value;
  state.activeSchool = document.getElementById("schoolSelect").value;
  state.currentSort = document.getElementById("sortSelect").value;
  loadResources();
}

function resetFilters() {
  document.getElementById("searchInput").value = "";
  document.getElementById("searchClearBtn").style.display = "none";
  document.getElementById("subjectSelect").value = "";
  document.getElementById("gradeSelect").value = "";
  if (document.getElementById("ratingSelect")) document.getElementById("ratingSelect").value = "";
  document.getElementById("typeSelect").value = "";
  document.getElementById("languageSelect").value = "";
  document.getElementById("schoolSelect").value = "";
  document.getElementById("sortSelect").value = "newest";

  state.searchQuery = "";
  state.activeSubject = "";
  state.activeGrade = "";
  state.activeRating = "";
  state.activeType = "";
  state.activeLanguage = "";
  state.activeSchool = "";
  state.currentSort = "newest";

  setStageFilter("");
}

// Navigation View Switcher
function switchView(viewName) {
  state.activeView = viewName;
  const views = ["browse", "favorites", "moderation", "templates", "curriculum", "stats"];
  views.forEach((v) => {
    const el = document.getElementById(`view-${v}`);
    const tab = document.getElementById(`tab-${v}`);
    if (el) el.style.display = v === viewName ? "block" : "none";
    if (tab) tab.classList.toggle("active", v === viewName);
  });

  if (viewName === "stats") {
    loadStats();
  } else if (viewName === "templates") {
    loadTemplates();
  } else if (viewName === "moderation") {
    loadModerationQueue();
  } else if (viewName === "favorites") {
    loadFavoritesView();
  }
}

// API Calls: Schools
async function loadSchools() {
  try {
    const res = await fetch("/api/schools");
    const data = await res.json();
    state.schools = data.schools || [];

    const schoolSelect = document.getElementById("schoolSelect");
    const formSchool = document.getElementById("formSchool");

    state.schools.forEach((s) => {
      const opt1 = document.createElement("option");
      opt1.value = s.name;
      opt1.textContent = `${s.name} (${s.state})`;
      schoolSelect.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = s.name;
      opt2.textContent = `${s.name} (${s.state})`;
      formSchool.appendChild(opt2);
    });
    updateFormDefaultsForCurrentUser();
  } catch (err) {
    console.error("Error loading schools:", err);
  }
}

// API Calls: Resources
async function loadResources() {
  try {
    const params = new URLSearchParams();
    params.append("status", "Published"); // Public library shows only Approved content (Module K)
    if (state.searchQuery) params.append("q", state.searchQuery);
    if (state.activeStage) params.append("grade_category", state.activeStage);
    if (state.activeSubject) params.append("subject", state.activeSubject);
    if (state.activeGrade) params.append("grade_level", state.activeGrade);
    if (state.activeRating) params.append("min_rating", state.activeRating);
    if (state.activeType) params.append("resource_type", state.activeType);
    if (state.activeLanguage) params.append("medium_language", state.activeLanguage);
    if (state.activeSchool) params.append("school", state.activeSchool);
    if (state.currentSort) params.append("sort", state.currentSort);

    const res = await fetch(`/api/resources?${params.toString()}`);
    const data = await res.json();
    state.resources = data.resources || [];

    document.getElementById("resourcesCount").textContent = data.count || 0;
    renderResources(state.resources, "resourceGrid");
  } catch (err) {
    console.error("Error loading resources:", err);
  }
}

async function loadFavoritesView() {
  try {
    const res = await fetch(`/api/resources?favorites_user=${encodeURIComponent(state.currentUser.name)}&status=All`);
    const data = await res.json();
    const favs = data.resources || [];
    const grid = document.getElementById("favoritesGrid");

    if (favs.length === 0) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="icon">⭐</div>
          <h3>No saved resources yet</h3>
          <p>Click the "Save to Favorites" or star button on any lesson plan or worksheet to bookmark it here.</p>
        </div>
      `;
      return;
    }
    renderResources(favs, "favoritesGrid");
  } catch (err) {
    console.error("Error loading favorites view:", err);
  }
}

function renderResources(items, targetContainerId = "resourceGrid") {
  const container = document.getElementById(targetContainerId);
  const emptyState = document.getElementById("emptyState");

  if (!items || items.length === 0) {
    container.innerHTML = "";
    if (targetContainerId === "resourceGrid" && emptyState) emptyState.style.display = "block";
    return;
  }

  if (targetContainerId === "resourceGrid" && emptyState) emptyState.style.display = "none";
  container.innerHTML = items.map((item) => createResourceCardHTML(item)).join("");
}

function getSubjectBadgeClass(subject) {
  switch (subject) {
    case "Tibetan": return "badge-tibetan";
    case "Science": return "badge-science";
    case "Mathematics": return "badge-mathematics";
    case "Social Science": return "badge-social";
    case "English": return "badge-english";
    case "Hindi": return "badge-hindi";
    case "SEE Learning / Dialectics": return "badge-see";
    default: return "badge-general";
  }
}

function createResourceCardHTML(item) {
  const badgeClass = getSubjectBadgeClass(item.subject);
  const fileExt = (item.file_type || "md").toUpperCase();
  const isFav = state.userFavorites.has(item.id);
  const avgRating = item.rating_avg ? Number(item.rating_avg).toFixed(1) : "5.0";
  const ratingCount = item.rating_count || 0;
  const views = item.views_count || 0;

  return `
    <div class="resource-card" id="card-${item.id}">
      <div class="card-top-badges">
        <span class="subject-badge ${badgeClass}">${escapeHTML(item.subject)}</span>
        <div style="display: flex; gap: 0.3rem;">
          <span class="grade-badge">${escapeHTML(item.grade_level)}</span>
          <span class="type-pill">${escapeHTML(item.resource_type)}</span>
        </div>
      </div>

      <!-- Rating and Views Pill (PRD Module C & D) -->
      <div class="card-stars-views">
        <span class="star-rating-pill" title="${ratingCount} peer teacher ratings">
          ★ ${avgRating} <span style="font-weight: normal; font-size: 0.72rem; color: #a16207;">(${ratingCount})</span>
        </span>
        <span class="card-views-pill" title="Total teacher views">
          👁️ ${views} views
        </span>
      </div>

      <h3 class="card-title" onclick="openPreviewModal(${item.id})" style="cursor: pointer;" title="Click to preview material">${escapeHTML(item.title)}</h3>
      ${item.title_en ? `<div class="card-title-en" onclick="openPreviewModal(${item.id})" style="cursor: pointer;" title="Click to preview material">${escapeHTML(item.title_en)}</div>` : ""}

      <div class="card-topic">
        <span>📖</span>
        <span style="font-weight: 500;">${escapeHTML(item.chapter_topic)}</span>
      </div>

      <p class="card-desc">${escapeHTML(item.description || "No description provided.")}</p>

      <div class="card-meta">
        <div class="card-meta-row">
          <span class="card-school">🏫 ${escapeHTML(item.school_name)}</span>
          <span>🌐 ${escapeHTML(item.medium_language)}</span>
        </div>
        <div class="card-meta-row" style="color: #64748b; font-size: 0.74rem;">
          <span>👤 <a href="javascript:void(0)" class="author-link" onclick="event.stopPropagation(); openTeacherProfile('${escapeHTML(item.author_name)}')" title="View ${escapeHTML(item.author_name)}'s Contributor Profile">${escapeHTML(item.author_name)}</a> (${escapeHTML(item.author_role || "Teacher")})</span>
          <span>📁 ${fileExt} • ${item.file_size_kb || 1} KB</span>
        </div>
      </div>

      <div class="card-actions">
        <div style="display: flex; gap: 0.4rem;">
          <button class="card-btn card-btn-preview" onclick="openPreviewModal(${item.id})">
            👁️ Preview
          </button>
          <a class="card-btn card-btn-download" href="/api/resources/${item.id}/download" onclick="return onDownloadClicked(${item.id}, event)">
            ⬇️ Download
          </a>
        </div>

        <div style="display: flex; gap: 0.3rem;">
          <!-- Favorite Bookmark Toggle (PRD Module H) -->
          <button class="card-fav-btn ${isFav ? 'active' : ''}" onclick="toggleFavorite(${item.id})" title="${isFav ? 'Remove from Favorites' : 'Save to Favorites'}">
            ${isFav ? '⭐' : '☆'}
          </button>
          <!-- Appreciate / Like -->
          <button class="card-like-btn" onclick="likeResource(${item.id})" title="Appreciate">
            ❤️ <span id="like-count-${item.id}">${item.likes_count || 0}</span>
          </button>
        </div>
      </div>
    </div>
  `;
}

// Favorite Toggle (PRD Module H)
async function toggleFavorite(id) {
  if (state.currentUser.role === "Guest") {
    openLoginModal();
    return;
  }
  try {
    const res = await fetch(`/api/resources/${id}/favorite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_name: state.currentUser.name })
    });
    const data = await res.json();
    if (data.favorited) {
      state.userFavorites.add(id);
    } else {
      state.userFavorites.delete(id);
    }

    // Update UI card buttons
    document.querySelectorAll(`#card-${id} .card-fav-btn`).forEach(btn => {
      btn.classList.toggle("active", data.favorited);
      btn.textContent = data.favorited ? "⭐" : "☆";
    });

    if (state.currentPreviewResource && state.currentPreviewResource.id === id) {
      updatePreviewFavoriteBtn(data.favorited);
    }

    if (state.activeView === "favorites") {
      loadFavoritesView();
    }
  } catch (err) {
    console.error("Error toggling favorite:", err);
  }
}

function updatePreviewFavoriteBtn(isFav) {
  const btnText = document.getElementById("previewFavBtnText");
  if (btnText) {
    btnText.textContent = isFav ? "Saved in Favorites" : "Save to Favorites";
  }
}

function toggleCurrentPreviewFavorite() {
  if (state.currentPreviewResource) {
    toggleFavorite(state.currentPreviewResource.id);
  }
}

// Like Resource
async function likeResource(id) {
  try {
    const res = await fetch(`/api/resources/${id}/like`, { method: "POST" });
    const data = await res.json();
    if (data.likes_count !== undefined) {
      const el = document.getElementById(`like-count-${id}`);
      if (el) el.textContent = data.likes_count;
    }
  } catch (err) {
    console.error("Error liking resource:", err);
  }
}

function onDownloadClicked(id, event) {
  if (state.currentUser.role === "Guest") {
    if (event) event.preventDefault();
    openLoginModal();
    return false;
  }
  setTimeout(() => {
    loadStats();
  }, 1000);
  return true;
}

// Preview Modal (Module D, E, K)
async function openPreviewModal(id) {
  try {
    const res = await fetch(`/api/resources/${id}?user=${encodeURIComponent(state.currentUser.name)}`);
    const data = await res.json();
    state.currentPreviewResource = data;

    document.getElementById("previewModalTitle").textContent = data.title;
    document.getElementById("previewModalMeta").innerHTML = `
      ${escapeHTML(data.subject)} • ${escapeHTML(data.grade_level)} • ${escapeHTML(data.school_name)} • 
      Author: <a href="javascript:void(0)" class="author-link" style="color: #fde68a; text-decoration: underline; font-weight: 700;" onclick="event.stopPropagation(); openTeacherProfile('${escapeHTML(data.author_name)}')" title="View ${escapeHTML(data.author_name)}'s Contributor Profile">${escapeHTML(data.author_name)}</a> • 
      👁️ ${data.views_count || 1} views
    `;

    // Teaching Notes (Module B)
    const notesBox = document.getElementById("previewTeachingNotesBox");
    const notesText = document.getElementById("previewTeachingNotesText");
    if (data.teaching_notes && data.teaching_notes.trim()) {
      notesText.textContent = data.teaching_notes;
      notesBox.style.display = "block";
    } else {
      notesBox.style.display = "none";
    }

    // Document Body Preview (Supports PDF iframe, Images, Office Docs, and Markdown)
    const contentDiv = document.getElementById("previewContent");
    const fileUrl = `/api/resources/${data.id}/file`;

    const extFromType = (data.file_type || "").toLowerCase().replace(/^\./, "").trim();
    const extFromName = (data.file_name || "").split(".").pop().toLowerCase().trim();
    const extFromPath = (data.file_path || "").split(".").pop().toLowerCase().trim();
    const isPDF = extFromType === "pdf" ||
                  extFromType === "application/pdf" ||
                  extFromName === "pdf" ||
                  extFromPath === "pdf";

    const isImage = ["png", "jpg", "jpeg", "webp", "gif", "svg"].includes(extFromType) ||
                    ["png", "jpg", "jpeg", "webp", "gif", "svg"].includes(extFromName);

    const isOfficeDoc = ["docx", "doc", "pptx", "ppt", "xlsx", "xls", "zip"].includes(extFromType) ||
                        ["docx", "doc", "pptx", "ppt", "xlsx", "xls", "zip"].includes(extFromName);

    if (isPDF) {
      contentDiv.innerHTML = `
        <div style="margin-bottom: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 0.75rem 1rem; border: 1px solid var(--border); border-radius: 8px 8px 0 0; border-bottom: none; flex-wrap: wrap; gap: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
              <span style="font-size: 1.4rem;">📄</span>
              <div>
                <div style="font-weight: 700; font-size: 0.92rem; color: #1e293b;">${escapeHTML(data.file_name || 'Attached PDF Document')}</div>
                <div style="font-size: 0.76rem; color: #64748b;">PDF Document • ${data.file_size_kb || 1} KB • Inline Document Reader</div>
              </div>
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
              <a href="${fileUrl}" target="_blank" class="nav-btn" style="font-size: 0.8rem; padding: 0.35rem 0.75rem; background: #ffffff; color: var(--primary-dark); border: 1px solid var(--border); text-decoration: none; border-radius: 6px; font-weight: 600;">
                ↗️ Open Fullscreen / New Tab
              </a>
              <a href="/api/resources/${data.id}/download" class="nav-btn btn-upload" style="font-size: 0.8rem; padding: 0.35rem 0.75rem; text-decoration: none; border-radius: 6px; font-weight: 600;" onclick="return onDownloadClicked(${data.id}, event)">
                ⬇️ Download PDF
              </a>
            </div>
          </div>
          <iframe src="${fileUrl}#view=FitH" style="width: 100%; height: 600px; border: 1px solid var(--border); border-radius: 0 0 8px 8px; background: #525659; display: block;" title="PDF Preview">
            <div style="padding: 2rem; text-align: center; background: #ffffff;">
              <p style="font-size: 0.95rem; color: #334155; margin-bottom: 1rem;">If the PDF preview does not display directly in your browser:</p>
              <a href="${fileUrl}" target="_blank" class="nav-btn btn-upload" style="display: inline-block;">Open PDF in Browser Tab</a>
            </div>
          </iframe>
        </div>
        ${data.description ? `<div style="margin-top: 1rem; padding: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border);"><strong style="color: var(--primary-dark);">Description & Objectives:</strong><p style="margin-top: 0.4rem; color: #334155; line-height: 1.5;">${escapeHTML(data.description)}</p></div>` : ''}
      `;
    } else if (isImage) {
      contentDiv.innerHTML = `
        <div style="text-align: center; margin-bottom: 1rem;">
          <img src="${fileUrl}" style="max-width: 100%; max-height: 520px; border-radius: 8px; border: 1px solid var(--border); object-fit: contain;">
        </div>
        ${data.description ? `<div style="padding: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border);"><p style="color: #475569; line-height: 1.5;">${escapeHTML(data.description)}</p></div>` : ''}
      `;
    } else if (isOfficeDoc) {
      contentDiv.innerHTML = `
        <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 1.8rem; text-align: center; margin-bottom: 1rem;">
          <div style="font-size: 3rem; margin-bottom: 0.5rem;">📁</div>
          <h4 style="color: #1e293b; font-size: 1.1rem; margin-bottom: 0.3rem;">${escapeHTML(data.file_name || 'Office Document')}</h4>
          <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;">${(extFromName || extFromType).toUpperCase()} Document • ${data.file_size_kb || 1} KB</p>
          <a class="nav-btn btn-upload" href="/api/resources/${data.id}/download" onclick="return onDownloadClicked(${data.id}, event)">
            ⬇️ Download to View in Microsoft Office / Google Docs
          </a>
        </div>
        ${data.description ? `<div style="padding: 1rem; background: #ffffff; border-radius: 8px; border: 1px solid var(--border);"><strong style="color: var(--primary-dark);">Description & Objectives:</strong><p style="margin-top: 0.4rem; color: #334155; line-height: 1.5;">${escapeHTML(data.description)}</p></div>` : ''}
      `;
    } else {
      contentDiv.innerHTML = renderSimpleMarkdown(data.content_text || data.description || "No text preview available.");
    }

    // Rating Widget (Module E)
    renderRatingWidget(data);

    // Reviews & Comments (Module E)
    renderComments(data.comments || []);

    // Favorite button status
    updatePreviewFavoriteBtn(data.is_favorited);

    // Download button link
    const dlBtn = document.getElementById("previewDownloadBtn");
    dlBtn.onclick = (e) => {
      if (state.currentUser.role === "Guest") {
        openLoginModal();
        return;
      }
      window.location.href = `/api/resources/${id}/download`;
      onDownloadClicked(id);
    };

    document.getElementById("previewModal").classList.add("active");
  } catch (err) {
    console.error("Error opening preview modal:", err);
  }
}

function closePreviewModal() {
  document.getElementById("previewModal").classList.remove("active");
  state.currentPreviewResource = null;
}

// Star Rating Submission (PRD Module E: 1-5 Stars, editable)
function renderRatingWidget(resource) {
  const avg = resource.rating_avg ? Number(resource.rating_avg).toFixed(1) : "5.0";
  const count = resource.rating_count || 0;
  const userRating = resource.user_rating;

  const summary = document.getElementById("previewRatingSummary");
  if (summary) {
    summary.textContent = userRating 
      ? `You rated this ${userRating}★ • Community Average: ★ ${avg} (${count} reviews)`
      : `Community Average: ★ ${avg} (${count} ratings) • Click a star to rate`;
  }

  // Update star highlights
  const stars = document.querySelectorAll("#interactiveStarContainer span");
  stars.forEach(s => {
    const starVal = Number(s.getAttribute("data-star"));
    if (userRating && starVal <= userRating) {
      s.classList.add("filled");
    } else {
      s.classList.remove("filled");
    }
  });
}

async function submitRating(stars) {
  if (state.currentUser.role === "Guest") {
    openLoginModal();
    return;
  }
  if (!state.currentPreviewResource) return;
  const resId = state.currentPreviewResource.id;

  try {
    const res = await fetch(`/api/resources/${resId}/rate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_name: state.currentUser.name,
        rating: stars
      })
    });
    const data = await res.json();

    state.currentPreviewResource.rating_avg = data.rating_avg;
    state.currentPreviewResource.rating_count = data.rating_count;
    state.currentPreviewResource.user_rating = data.user_rating;

    renderRatingWidget(state.currentPreviewResource);
    loadResources(); // update background card
  } catch (err) {
    console.error("Error submitting rating:", err);
  }
}

// Comments / Reviews (PRD Module E)
function renderComments(comments) {
  const list = document.getElementById("previewReviewsList");
  const countEl = document.getElementById("previewCommentsCount");
  if (countEl) countEl.textContent = comments.length;

  if (!comments || comments.length === 0) {
    list.innerHTML = `<div style="color: #94a3b8; font-style: italic; font-size: 0.85rem; padding: 0.5rem 0;">No reviews yet. Be the first teacher to leave feedback!</div>`;
    return;
  }

  list.innerHTML = comments.map(c => `
    <div class="review-item">
      <div class="review-header">
        <div>
          <span class="review-author">👤 <a href="javascript:void(0)" class="author-link" onclick="event.stopPropagation(); openTeacherProfile('${escapeHTML(c.user_name)}')" title="View ${escapeHTML(c.user_name)}'s Profile">${escapeHTML(c.user_name)}</a></span>
          <span class="review-school">• ${escapeHTML(c.user_school || 'STSS Teacher')} (${escapeHTML(c.user_role || 'Educator')})</span>
        </div>
        <span class="review-date">${formatDate(c.created_at)}</span>
      </div>
      <p class="review-body">${escapeHTML(c.comment_text)}</p>
    </div>
  `).join("");
}

async function handleCommentSubmit(e) {
  e.preventDefault();
  if (state.currentUser.role === "Guest") {
    openLoginModal();
    return;
  }
  if (!state.currentPreviewResource) return;
  const resId = state.currentPreviewResource.id;
  const input = document.getElementById("commentInput");
  const text = input.value.trim();
  if (!text) return;

  const submitBtn = document.getElementById("commentSubmitBtn");
  submitBtn.disabled = true;

  try {
    const res = await fetch(`/api/resources/${resId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_name: state.currentUser.name,
        user_school: state.currentUser.school,
        user_role: state.currentUser.designation,
        comment_text: text
      })
    });
    const newComment = await res.json();

    if (!state.currentPreviewResource.comments) state.currentPreviewResource.comments = [];
    state.currentPreviewResource.comments.unshift(newComment);
    renderComments(state.currentPreviewResource.comments);
    input.value = "";
    loadStats();
  } catch (err) {
    alert("Error posting review: " + err.message);
  } finally {
    submitBtn.disabled = false;
  }
}

// Report / Flag Resource (PRD Module K)
async function reportResource() {
  if (!state.currentPreviewResource) return;
  const resId = state.currentPreviewResource.id;
  const reason = prompt("Please describe the copyright or pedagogical concern regarding this resource:");
  if (!reason || !reason.trim()) return;

  try {
    const res = await fetch(`/api/resources/${resId}/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_name: state.currentUser.name,
        reason: reason.trim()
      })
    });
    alert("Thank you. This resource has been flagged and submitted to STSS Content Moderators for review.");
    loadModerationQueue();
  } catch (err) {
    alert("Error reporting resource: " + err.message);
  }
}

function copyPreviewText() {
  if (!state.currentPreviewResource) return;
  const text = state.currentPreviewResource.content_text || state.currentPreviewResource.description;
  navigator.clipboard.writeText(text).then(() => {
    alert("Resource content copied to clipboard!");
  });
}

// Upload Modal & PRD Module K Copyright Confirmation
function openUploadModal() {
  if (state.currentUser.role === "Guest") {
    openLoginModal();
    return;
  }
  updateFormDefaultsForCurrentUser();
  document.getElementById("uploadModal").classList.add("active");
}

function closeUploadModal() {
  document.getElementById("uploadModal").classList.remove("active");
  document.getElementById("uploadForm").reset();
  document.getElementById("selectedFileName").textContent = "";
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) {
    document.getElementById("selectedFileName").textContent = `Selected: ${file.name} (${Math.round(file.size / 1024)} KB)`;
  }
}

async function handleResourceSubmit(e) {
  e.preventDefault();

  // Module K: Mandatory Copyright Check
  const copyrightCheckbox = document.getElementById("formCopyright");
  if (copyrightCheckbox && !copyrightCheckbox.checked) {
    alert("Module K Requirement: You must verify that you hold copyright or sharing permissions before submitting.");
    return;
  }

  const submitBtn = document.getElementById("submitBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Submitting for Moderation...";

  const fileInput = document.getElementById("formFile");
  const formData = new FormData();

  formData.append("title", document.getElementById("formTitle").value.trim());
  formData.append("title_en", document.getElementById("formTitleEn").value.trim());
  formData.append("subject", document.getElementById("formSubject").value);
  formData.append("grade_level", document.getElementById("formGrade").value);
  formData.append("chapter_topic", document.getElementById("formTopic").value.trim());
  formData.append("resource_type", document.getElementById("formType").value);
  formData.append("medium_language", document.getElementById("formLanguage").value);
  formData.append("author_name", document.getElementById("formAuthor").value.trim());
  formData.append("author_role", document.getElementById("formRole").value.trim());
  formData.append("school_name", document.getElementById("formSchool").value);
  formData.append("tags", document.getElementById("formTags").value.trim());
  formData.append("description", document.getElementById("formDesc").value.trim());
  formData.append("teaching_notes", document.getElementById("formTeachingNotes").value.trim());
  formData.append("content_text", document.getElementById("formContentText").value);
  formData.append("copyright_confirmed", "1");

  // If Admin or Moderator is uploading, publish directly; teachers submit to Pending Review
  const initialStatus = (state.currentUser.role === "Admin" || state.currentUser.role === "Moderator") 
    ? "Published" 
    : "Pending Review";
  formData.append("status", initialStatus);

  if (fileInput.files.length > 0) {
    formData.append("file", fileInput.files[0]);
  }

  try {
    const res = await fetch("/api/resources", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Failed to submit resource");
    }

    closeUploadModal();
    if (initialStatus === "Pending Review") {
      alert("Success! Your teaching resource has entered the STSS Moderation Queue (Module K). Once approved by an STSS Subject Moderator, it will appear in the public library.");
    } else {
      alert("Resource published successfully!");
    }
    loadResources();
    loadStats();
    loadModerationQueue();
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit for Moderation";
  }
}

// Moderation Queue & Audit Log (PRD Module K)
async function loadModerationQueue() {
  try {
    const res = await fetch("/api/resources?status=Pending Review");
    const data = await res.json();
    const pendingItems = data.resources || [];

    // Update tab badge
    const badge = document.getElementById("moderationBadge");
    if (badge) {
      badge.textContent = pendingItems.length;
      badge.style.display = pendingItems.length > 0 ? "inline-block" : "none";
    }

    const tbody = document.getElementById("moderationQueueBody");
    if (tbody) {
      if (pendingItems.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #64748b; padding: 1.5rem;">🎉 No resources currently pending review. The moderation queue is clear.</td></tr>`;
      } else {
        tbody.innerHTML = pendingItems.map(item => `
          <tr>
            <td>
              <div style="font-weight: 700; color: #1e293b;">${escapeHTML(item.title)}</div>
              <div style="font-size: 0.78rem; color: #64748b;">📖 ${escapeHTML(item.chapter_topic)}</div>
            </td>
            <td>
              <span class="grade-badge">${escapeHTML(item.grade_level)}</span>
              <div style="font-size: 0.76rem; color: #475569; margin-top: 2px;">${escapeHTML(item.subject)}</div>
            </td>
            <td>
              <div style="font-weight: 500;">${escapeHTML(item.author_name)}</div>
              <div style="font-size: 0.74rem; color: #64748b;">${escapeHTML(item.school_name)}</div>
            </td>
            <td>
              <span style="color: #16a34a; font-weight: bold; font-size: 0.8rem;">✓ Verified</span>
            </td>
            <td>
              <span class="status-badge status-pending">Pending Review</span>
            </td>
            <td>
              <div class="moderation-btn-group">
                <button class="card-btn card-btn-preview" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="openPreviewModal(${item.id})">
                  👁️ Inspect
                </button>
                <button class="btn-approve" onclick="reviewResource(${item.id}, 'Approved')">
                  ✓ Approve
                </button>
                <button class="btn-reject" onclick="reviewResource(${item.id}, 'Rejected')">
                  ✕ Reject
                </button>
              </div>
            </td>
          </tr>
        `).join("");
      }
    }

    // Load Audit Log
    loadModerationAudit();
  } catch (err) {
    console.error("Error loading moderation queue:", err);
  }
}

async function reviewResource(id, action) {
  let reason = "";
  if (action === "Rejected") {
    reason = prompt("Please specify the feedback or rejection reason for the teacher:");
    if (!reason || !reason.trim()) return;
  }

  try {
    const res = await fetch(`/api/moderation/${id}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        moderator_name: state.currentUser.name,
        action: action,
        reason: reason
      })
    });

    if (!res.ok) throw new Error("Failed to submit moderation decision");

    alert(`Resource has been marked as ${action}.`);
    loadModerationQueue();
    loadResources();
    loadStats();
  } catch (err) {
    alert("Error updating status: " + err.message);
  }
}

async function loadModerationAudit() {
  try {
    const res = await fetch("/api/moderation/audit");
    const data = await res.json();
    const list = data.audit_logs || [];
    const container = document.getElementById("moderationAuditLog");
    if (!container) return;

    if (list.length === 0) {
      container.innerHTML = `<div style="color: #94a3b8; font-size: 0.85rem;">No moderation audit records logged yet.</div>`;
      return;
    }

    container.innerHTML = list.map(log => `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0; border-bottom: 1px solid #f1f5f9; font-size: 0.82rem;">
        <div>
          <span style="font-weight: 700; color: #1e293b;">[${log.action}]</span> 
          <span>${escapeHTML(log.resource_title || 'Resource #' + log.resource_id)}</span>
          ${log.reason ? `<span style="color: #64748b; font-style: italic;"> — "${escapeHTML(log.reason)}"</span>` : ''}
        </div>
        <div style="color: #94a3b8; font-size: 0.75rem;">
          By <strong>${escapeHTML(log.moderator_name)}</strong> • ${formatDate(log.created_at)}
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading moderation audit:", err);
  }
}

// Templates View
async function loadTemplates() {
  try {
    const res = await fetch("/api/templates");
    const data = await res.json();
    state.templates = data.templates || [];

    const container = document.getElementById("templatesList");
    if (!container) return;

    container.innerHTML = state.templates.map((tpl) => `
      <div class="resource-card" style="border-top: 4px solid var(--accent-gold);">
        <div class="card-top-badges">
          <span class="subject-badge badge-general">${escapeHTML(tpl.category)}</span>
          <span class="type-pill">Template</span>
        </div>
        <h3 class="card-title">${escapeHTML(tpl.title)}</h3>
        ${tpl.title_tibetan ? `<div class="card-title-en" style="color: var(--primary-dark); font-weight: 500;">${escapeHTML(tpl.title_tibetan)}</div>` : ""}
        <p class="card-desc">${escapeHTML(tpl.description)}</p>
        <div class="card-actions" style="margin-top: 1rem;">
          <button class="card-btn card-btn-preview" onclick="previewTemplate(${tpl.id})">
            👁️ View Template
          </button>
          <button class="card-btn card-btn-download" onclick="useTemplateInUpload(${tpl.id})">
            ✏️ Use this Format
          </button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading templates:", err);
  }
}

function previewTemplate(id) {
  const tpl = state.templates.find(t => t.id === id);
  if (!tpl) return;

  state.currentPreviewResource = {
    title: tpl.title,
    content_text: tpl.content,
    subject: tpl.category,
    grade_level: "Standard Format",
    school_name: "STSS Central Education Council",
    author_name: "CTA DoE & STSS Curriculum Dept"
  };

  document.getElementById("previewModalTitle").textContent = tpl.title;
  document.getElementById("previewModalMeta").textContent = `${tpl.category} • Official STSS Format`;
  document.getElementById("previewTeachingNotesBox").style.display = "none";
  document.getElementById("previewContent").innerHTML = renderSimpleMarkdown(tpl.content);
  
  const dlBtn = document.getElementById("previewDownloadBtn");
  dlBtn.onclick = () => {
    const blob = new Blob([tpl.content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${tpl.title.toLowerCase().replace(/[^a-z0-9]/g, "_")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  document.getElementById("previewModal").classList.add("active");
}

function useTemplateInUpload(id) {
  const tpl = state.templates.find(t => t.id === id);
  if (!tpl) return;
  openUploadModal();
  document.getElementById("formContentText").value = tpl.content;
  document.getElementById("formTitle").value = `Lesson Plan: [Topic] (${tpl.title})`;
  document.getElementById("formDesc").value = `Prepared using official STSS ${tpl.title}`;
}

// Stats View
async function loadStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();

    document.getElementById("statTotalResources").textContent = data.total_resources || 0;
    document.getElementById("statTotalDownloads").textContent = data.total_downloads || 0;
    if (document.getElementById("statTotalViews")) {
      document.getElementById("statTotalViews").textContent = data.total_views || 0;
    }
    if (document.getElementById("statTotalReviews")) {
      document.getElementById("statTotalReviews").textContent = data.total_reviews || 0;
    }

    const subjectList = document.getElementById("statsSubjectList");
    if (subjectList) {
      subjectList.innerHTML = (data.by_subject || []).map(item => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9;">
          <span style="font-weight: 500;">${escapeHTML(item.subject)}</span>
          <span style="background: #e2e8f0; padding: 0.2rem 0.6rem; border-radius: 12px; font-weight: bold; font-size: 0.85rem;">
            ${item.count} items
          </span>
        </div>
      `).join("");
    }

    const schoolsList = document.getElementById("statsSchoolsList");
    if (schoolsList) {
      schoolsList.innerHTML = (data.top_schools || []).map(item => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9;">
          <span style="font-weight: 500;">🏫 ${escapeHTML(item.school_name)}</span>
          <span style="background: #fef3c7; color: #92400e; padding: 0.2rem 0.6rem; border-radius: 12px; font-weight: bold; font-size: 0.85rem;">
            ${item.count} contributed
          </span>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading stats:", err);
  }
}

// Markdown Renderer
function renderSimpleMarkdown(md) {
  if (!md) return "";
  let html = md;

  html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  html = html.replace(/```([\s\S]*?)```/g, '<pre style="background: #1e293b; color: #f8fafc; padding: 1rem; border-radius: 6px; overflow-x: auto;"><code>$1</code></pre>');
  html = html.replace(/^### (.*$)/gim, '<h3 style="color: var(--primary); margin-top: 1rem;">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 style="color: var(--primary-dark); margin-top: 1.2rem;">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 style="color: var(--primary-dark); border-bottom: 2px solid var(--accent-gold); padding-bottom: 0.4rem;">$1</h1>');
  html = html.replace(/^---$/gim, '<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 1.2rem 0;">');
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
  html = html.replace(/`([^`]+)`/g, '<code style="background: #f1f5f9; padding: 0.15rem 0.35rem; border-radius: 4px; font-family: monospace;">$1</code>');

  const lines = html.split("\n");
  let inTable = false;
  let tableHTML = "";
  const processedLines = [];

  for (let line of lines) {
    line = line.trim();
    if (line.startsWith("|") && line.endsWith("|")) {
      if (!inTable) {
        inTable = true;
        tableHTML = '<table style="width: 100%; border-collapse: collapse; margin: 1rem 0;">';
      }
      const cells = line.split("|").slice(1, -1).map(c => c.trim());
      if (cells.some(c => c.match(/^:?-+:?$/))) {
        continue;
      }
      tableHTML += '<tr>' + cells.map(c => `<td style="border: 1px solid #cbd5e1; padding: 0.5rem 0.75rem;">${c}</td>`).join("") + '</tr>';
    } else {
      if (inTable) {
        inTable = false;
        tableHTML += '</table>';
        processedLines.push(tableHTML);
      }
      processedLines.push(line);
    }
  }
  if (inTable) {
    tableHTML += '</table>';
    processedLines.push(tableHTML);
  }

  return processedLines.map(line => {
    if (line.startsWith("- ")) {
      return `<li style="margin-left: 1.5rem; margin-bottom: 0.3rem;">${line.substring(2)}</li>`;
    } else if (line.match(/^\d+\.\s/)) {
      return `<li style="margin-left: 1.5rem; margin-bottom: 0.3rem;">${line.replace(/^\d+\.\s/, "")}</li>`;
    } else if (line.startsWith("<h") || line.startsWith("<table") || line.startsWith("<hr") || line.startsWith("<pre") || line === "") {
      return line;
    } else {
      return `<p style="margin-bottom: 0.6rem;">${line}</p>`;
    }
  }).join("\n");
}

function formatDate(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function escapeHTML(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Teacher Profile Modal (PRD Module F)
async function openTeacherProfile(teacherName) {
  if (!teacherName) return;

  try {
    const res = await fetch(`/api/profile?name=${encodeURIComponent(teacherName)}`);
    if (!res.ok) throw new Error("Failed to load profile");
    const profile = await res.json();

    document.getElementById("profileModalHeaderTitle").textContent = `${profile.name}'s Contributor Profile`;
    document.getElementById("profileNameDisplay").textContent = profile.name;
    document.getElementById("profileSchoolDisplay").textContent = `🏫 ${profile.school}`;
    document.getElementById("profileSpecDisplay").textContent = `${profile.role} • ${profile.specialization} (Joined: ${formatDate(profile.joined_date) || 'Active Member'})`;
    document.getElementById("profileAvatarLetter").textContent = (profile.name[0] || 'T').toUpperCase();

    // Stats
    document.getElementById("profileStatResources").textContent = profile.stats.total_resources || 0;
    document.getElementById("profileStatDownloads").textContent = profile.stats.total_downloads || 0;
    document.getElementById("profileStatViews").textContent = profile.stats.total_views || 0;
    document.getElementById("profileStatRating").textContent = `★ ${Number(profile.stats.avg_rating || 5.0).toFixed(1)}`;

    // Resources list
    const listEl = document.getElementById("profileResourcesList");
    const countEl = document.getElementById("profileResourcesCount");
    if (countEl) countEl.textContent = profile.resources.length;

    if (profile.resources.length === 0) {
      listEl.innerHTML = `<div style="color: #94a3b8; font-style: italic; padding: 1rem 0;">No resources uploaded yet.</div>`;
    } else {
      listEl.innerHTML = profile.resources.map(r => `
        <div class="profile-resource-row">
          <div style="min-width: 0; flex: 1;">
            <div style="display: flex; gap: 0.35rem; align-items: center; margin-bottom: 0.2rem;">
              <span class="subject-badge ${getSubjectBadgeClass(r.subject)}" style="font-size: 0.68rem; padding: 0.15rem 0.45rem;">${escapeHTML(r.subject)}</span>
              <span class="grade-badge" style="font-size: 0.68rem;">${escapeHTML(r.grade_level)}</span>
              <span style="font-size: 0.72rem; color: #64748b;">★ ${Number(r.rating_avg || 5.0).toFixed(1)}</span>
            </div>
            <div style="font-weight: 700; font-size: 0.92rem; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              ${escapeHTML(r.title)}
            </div>
            <div style="font-size: 0.74rem; color: #64748b;">
              ${escapeHTML(r.chapter_topic || 'General')} • ⬇️ ${r.downloads_count || 0} downloads • 👁️ ${r.views_count || 0} views
            </div>
          </div>
          <div style="display: flex; gap: 0.35rem; margin-left: 0.8rem; flex-shrink: 0;">
            <button class="card-btn card-btn-preview" style="padding: 0.35rem 0.6rem; font-size: 0.76rem;" onclick="closeTeacherProfile(); openPreviewModal(${r.id});">
              👁️ View
            </button>
            <a class="card-btn card-btn-download" style="padding: 0.35rem 0.6rem; font-size: 0.76rem;" href="/api/resources/${r.id}/download" onclick="return onDownloadClicked(${r.id}, event)">
              ⬇️ Get
            </a>
          </div>
        </div>
      `).join("");
    }

    document.getElementById("teacherProfileModal").classList.add("active");
  } catch (err) {
    alert("Error opening teacher profile: " + err.message);
  }
}

function closeTeacherProfile() {
  const modal = document.getElementById("teacherProfileModal");
  if (modal) modal.classList.remove("active");
}

function openMyProfile() {
  if (state.currentUser.role === "Guest") {
    openLoginModal();
    return;
  }
  openTeacherProfile(state.currentUser.name);
}

// Modal overlay click outside to dismiss & Escape key handling
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay") && e.target.classList.contains("active")) {
    e.target.classList.remove("active");
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    const profileModal = document.getElementById("teacherProfileModal");
    if (profileModal && profileModal.classList.contains("active")) {
      closeTeacherProfile();
      return;
    }
    const activeModals = document.querySelectorAll(".modal-overlay.active");
    activeModals.forEach(m => m.classList.remove("active"));
  }
});

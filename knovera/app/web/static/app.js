let currentChatId = null;
let currentView = 'chats';
let kbCache = [];
let activeTheme = 'light';
let currentUserName = 'User';
let currentAssistantName = 'Assistant';
let showInactiveChats = false;
let kbEditorMode = 'create';
let editingKbId = null;
let settingsChatId = null;
let currentCitationMode = true;
let currentTopK = 5;

function syncChatHeaderActions() {
  const hasChat = Boolean(currentChatId);
  const ids = ['openChatSettingsBtn', 'openAdditionalInfoBtn', 'reloadChatBtn'];
  for (const id of ids) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.classList.toggle('d-none', !hasChat);
  }
}

function syncChatWorkspace() {
  const hasChat = Boolean(currentChatId);
  const empty = document.getElementById('chatEmptyState');
  const convo = document.getElementById('chatConversation');
  const stage = document.getElementById('chatStage');
  if (empty) empty.classList.toggle('d-none', hasChat);
  if (convo) convo.classList.toggle('d-none', !hasChat);
  if (stage) stage.classList.toggle('is-empty', !hasChat);
  syncBrandPlacement();
  syncSendButtons();
}

function restartHeroTyping() {
  const title = document.querySelector('#heroBrandSection .brand-title-typed');
  if (!title) return;
  title.classList.remove('typing-active');
  void title.offsetWidth;
  title.classList.add('typing-active');
}

function syncBrandPlacement() {
  const sidebarBrand = document.getElementById('sidebarBrandSection');
  const heroBrand = document.getElementById('heroBrandSection');
  const showHero = currentView === 'chats' && !currentChatId;

  if (sidebarBrand) {
    sidebarBrand.classList.toggle('d-none', showHero);
  }
  if (heroBrand) {
    heroBrand.classList.toggle('d-none', !showHero);
    heroBrand.setAttribute('aria-hidden', showHero ? 'false' : 'true');
    if (showHero) restartHeroTyping();
  }
}

function syncSendButtons() {
  const quickInput = document.getElementById('quickQuestionInput');
  const quickSendBtn = document.getElementById('quickSendBtn');
  if (quickInput && quickSendBtn) {
    quickSendBtn.disabled = !quickInput.value.trim();
  }

  const chatInput = document.getElementById('question');
  const askBtn = document.getElementById('askBtn');
  if (chatInput && askBtn) {
    askBtn.disabled = !chatInput.value.trim();
  }
}

function syncQuickKbHint() {
  const select = document.getElementById('quickKbSelect');
  const wrap = document.getElementById('quickKbWrap');
  if (!select || !wrap) return;
  wrap.classList.toggle('has-value', Boolean(select.value));
}

function openCenteredNewChatInput() {
  currentChatId = null;
  document.getElementById('activeChatTitle').textContent = '';
  document.getElementById('chatMessages').innerHTML = '';
  closeNewChatModal();
  closeChatSettingsModal();
  closeAdditionalInfoModal();
  setView('chats');
  syncChatHeaderActions();
  syncChatWorkspace();
  const input = document.getElementById('quickQuestionInput');
  if (input) {
    input.value = '';
    input.focus();
  }
  const questionInput = document.getElementById('question');
  if (questionInput) questionInput.value = '';
  syncSendButtons();
}

function setNewChatModalOpen(isOpen) {
  const modal = document.getElementById('newChatModal');
  if (!modal) return;
  if (isOpen) {
    modal.classList.remove('d-none');
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
  } else {
    modal.classList.add('d-none');
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
  }
}

function setChatSettingsModalOpen(isOpen) {
  const modal = document.getElementById('chatSettingsModal');
  if (!modal) return;
  if (isOpen) {
    modal.classList.remove('d-none');
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
  } else {
    modal.classList.add('d-none');
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
  }
}

function setAdditionalInfoModalOpen(isOpen) {
  const modal = document.getElementById('additionalInfoModal');
  if (!modal) return;
  if (isOpen) {
    modal.classList.remove('d-none');
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
  } else {
    modal.classList.add('d-none');
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
  }
}

function normalizeTopK(value, fallback = 5) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(1, Math.min(20, Math.floor(parsed)));
}

function setView(view) {
  currentView = view;
  document.getElementById('chatsView').classList.toggle('d-none', view !== 'chats');
  document.getElementById('kbView').classList.toggle('d-none', view !== 'kb');
  document.getElementById('leftChatsPanel').classList.toggle('d-none', view !== 'chats');
  document.getElementById('leftKbPanel').classList.toggle('d-none', view !== 'kb');
  document.getElementById('menuChatsBtn').classList.toggle('btn-primary', view === 'chats');
  document.getElementById('menuChatsBtn').classList.toggle('btn-outline-primary', view !== 'chats');
  document.getElementById('menuKbBtn').classList.toggle('btn-primary', view === 'kb');
  document.getElementById('menuKbBtn').classList.toggle('btn-outline-primary', view !== 'kb');
  syncBrandPlacement();
}

function applyTheme(theme) {
  activeTheme = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', activeTheme);
  document.body.setAttribute('data-theme', activeTheme);
  document.documentElement.style.colorScheme = activeTheme;
  localStorage.setItem('rag_theme', activeTheme);
  const btn = document.getElementById('themeToggleBtn');
  btn.dataset.theme = activeTheme;
  btn.title = activeTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
  btn.setAttribute('aria-pressed', activeTheme === 'dark' ? 'true' : 'false');
  const label = document.getElementById('themeToggleLabel');
  if (label) label.textContent = activeTheme === 'dark' ? 'Dark' : 'Light';
}

function toggleTheme() {
  applyTheme(activeTheme === 'dark' ? 'light' : 'dark');
}

function selectedDocumentIds() {
  return Array.from(document.querySelectorAll('input[name="docSelect"]:checked')).map((el) => el.value);
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatMessageContent(raw) {
  const escaped = escapeHtml(raw || '');
  const withCode = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
  const withBold = withCode.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  const withSourceLine = withBold.replace(/(^|\n)(\[(?:Source|source):[^\]\n]+\])/g, '$1<span class="msg-source">$2</span>');
  const exactBlocks = [];
  const withPlaceholders = withSourceLine.replace(/\[\[KB_EXACT\]\]([\s\S]*?)\[\[\/KB_EXACT\]\]/gi, (_, block) => {
    const lines = String(block || '')
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);

    if (!lines.length) {
      return '';
    }

    const body = lines.map((line) => `<div class="kb-exact-line">${line}</div>`).join('');
    const detailsHtml = `<details class="kb-exact"><summary>Exact wording from knowledge base</summary><div class="kb-exact-body">${body}</div></details>`;
    const token = `__KB_EXACT_${exactBlocks.length}__`;
    exactBlocks.push({ token, detailsHtml });
    return `\n\n${token}\n\n`;
  });

  let paragraphs = withPlaceholders
    .split(/\n{2,}/)
    .map((p) => `<p>${p.replace(/\n/g, '<br/>')}</p>`)
    .join('');

  for (const block of exactBlocks) {
    paragraphs = paragraphs
      .replace(`<p>${block.token}</p>`, block.detailsHtml)
      .replace(block.token, block.detailsHtml);
  }
  return paragraphs || '<p></p>';
}

function makeMessageNode(msg) {
  const row = document.createElement('div');
  row.className = `message-row ${msg.role}`;
  const roleLabel = msg.role === 'user' ? currentUserName : currentAssistantName;
  const bubble = document.createElement('div');
  bubble.className = `message ${msg.role}`;
  bubble.innerHTML = `
    <div class="msg-role">${escapeHtml(roleLabel)}</div>
    <div class="msg-content">${formatMessageContent(msg.content || '')}</div>
  `;
  row.appendChild(bubble);
  return row;
}

function renderMessages(messages) {
  const box = document.getElementById('chatMessages');
  box.innerHTML = '';

  if (!messages || !messages.length) {
    return;
  }

  for (const msg of messages) {
    box.appendChild(makeMessageNode(msg));
  }
  box.scrollTop = box.scrollHeight;
}

function addTypingPlaceholder() {
  const box = document.getElementById('chatMessages');
  const row = document.createElement('div');
  row.className = 'message-row assistant';
  row.id = 'typingRow';
  row.innerHTML = `
    <div class="message assistant">
      <div class="msg-role">${escapeHtml(currentAssistantName)}</div>
      <div class="msg-content">
        <span class="typing-dots"><span></span><span></span><span></span></span>
      </div>
    </div>
  `;
  box.appendChild(row);
  box.scrollTop = box.scrollHeight;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function typeAssistantText(text) {
  const row = document.getElementById('typingRow');
  if (!row) return;

  const content = row.querySelector('.msg-content');
  const role = row.querySelector('.msg-role');
  role.textContent = currentAssistantName;

  let current = '';
  for (let i = 0; i < (text || '').length; i += 1) {
    current += text[i];
    content.innerHTML = formatMessageContent(current);
    document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
    const ch = text[i];
    if (ch === '.' || ch === '!' || ch === '?') {
      await sleep(90);
    } else if (ch === ',' || ch === ';' || ch === ':') {
      await sleep(45);
    } else {
      await sleep(14);
    }
  }
}

async function renderChatWithTyping(messages) {
  const box = document.getElementById('chatMessages');
  box.innerHTML = '';
  if (!messages || !messages.length) {
    renderMessages(messages);
    return;
  }

  const lastAssistantIndex = [...messages].map((m) => m.role).lastIndexOf('assistant');
  messages.forEach((msg, idx) => {
    if (idx !== lastAssistantIndex) {
      box.appendChild(makeMessageNode(msg));
    }
  });

  const lastMsg = messages[lastAssistantIndex];
  if (!lastMsg) {
    box.scrollTop = box.scrollHeight;
    return;
  }

  addTypingPlaceholder();
  await sleep(360);
  await typeAssistantText(lastMsg.content || '');
  box.scrollTop = box.scrollHeight;
}

function renderCitations(citations) {
  const ul = document.getElementById('citations');
  ul.innerHTML = '';
  if (!citations || !citations.length) {
    ul.innerHTML = '<li class="text-muted">No citations for last response.</li>';
    return;
  }
  for (const c of citations || []) {
    const li = document.createElement('li');
    li.textContent = `${c.doc_name} p.${c.page} (score=${c.score})`;
    ul.appendChild(li);
  }
}

async function refreshDocs(preselectedIds = null) {
  const res = await fetch('/api/documents');
  const data = await res.json();
  const wrap = document.getElementById('docsChecklist');
  const selectedNow = preselectedIds ? new Set(preselectedIds) : new Set(selectedDocumentIds());
  wrap.innerHTML = '';

  for (const doc of data.items || []) {
    const disabled = doc.status !== 'ready' ? 'disabled' : '';
    const checked = selectedNow.has(doc.id) ? 'checked' : '';
    const row = document.createElement('label');
    row.className = 'doc-row d-flex justify-content-between align-items-center gap-2';
    row.innerHTML = `
      <span class="small text-truncate">
        <input class="form-check-input me-2" type="checkbox" name="docSelect" value="${doc.id}" ${disabled} ${checked} />
        ${doc.name}
      </span>
      <span class="badge ${doc.status === 'ready' ? 'text-bg-success' : 'text-bg-secondary'}">${doc.status}</span>
    `;
    wrap.appendChild(row);
  }
}

function renderKbSelect() {
  const select = document.getElementById('chatKbSelect');
  if (select) {
    const current = select.value;
    select.innerHTML = '<option value=\"\">No KB (all indexed docs)</option>';
    for (const kb of kbCache) {
      const opt = document.createElement('option');
      opt.value = kb.id;
      opt.textContent = `${kb.name} (${kb.document_count})`;
      select.appendChild(opt);
    }
    select.value = current;
  }

  const quickSelect = document.getElementById('quickKbSelect');
  if (quickSelect) {
    const quickCurrent = quickSelect.value;
    quickSelect.innerHTML = '<option value=\"\">Choose Document</option>';
    for (const kb of kbCache) {
      const opt = document.createElement('option');
      opt.value = kb.id;
      opt.textContent = kb.name;
      quickSelect.appendChild(opt);
    }
    const addKbOpt = document.createElement('option');
    addKbOpt.value = '__add_kb__';
    addKbOpt.textContent = 'Add Knowledge Base';
    quickSelect.appendChild(addKbOpt);
    quickSelect.value = (quickCurrent && quickCurrent !== '__add_kb__') ? quickCurrent : '';
    syncQuickKbHint();
  }
}

function populateNewChatKbSelect(selectedKbId = '') {
  const select = document.getElementById('newChatKbSelect');
  select.innerHTML = '<option value=\"\">No KB (all indexed docs)</option>';
  for (const kb of kbCache) {
    const opt = document.createElement('option');
    opt.value = kb.id;
    opt.textContent = `${kb.name} (${kb.document_count})`;
    select.appendChild(opt);
  }
  select.value = selectedKbId || '';
}

async function setKbEditorMode(mode, kb = null) {
  kbEditorMode = mode;
  const panel = document.getElementById('kbEditorPanel');
  const chip = document.getElementById('kbModeChip');
  if (mode === 'create') {
    editingKbId = null;
    panel.dataset.mode = 'create';
    chip.textContent = 'Create mode';
    chip.classList.remove('text-bg-secondary');
    chip.classList.add('text-bg-primary');
    document.getElementById('kbEditorModeLabel').textContent = 'Create Knowledge Base';
    document.getElementById('saveKbBtn').textContent = 'Create KB';
    document.getElementById('kbName').value = '';
    await refreshDocs([]);
    return;
  }

  if (!kb) return;
  editingKbId = kb.id;
  panel.dataset.mode = 'edit';
  chip.textContent = 'Edit mode';
  chip.classList.remove('text-bg-primary');
  chip.classList.add('text-bg-secondary');
  document.getElementById('kbEditorModeLabel').textContent = 'Edit Knowledge Base';
  document.getElementById('saveKbBtn').textContent = 'Save Changes';
  document.getElementById('kbName').value = kb.name;
  await refreshDocs(kb.document_ids || []);
}

async function refreshKnowledgeBases() {
  const res = await fetch('/api/knowledge-bases');
  kbCache = await res.json();

  renderKbSelect();

  const list = document.getElementById('kbList');
  list.innerHTML = '';

  if (!kbCache.length) {
    list.innerHTML = '<p class="text-muted small">No knowledge bases yet.</p>';
    await setKbEditorMode('create');
    return;
  }

  for (const kb of kbCache) {
    const div = document.createElement('div');
    div.className = `kb-card ${editingKbId === kb.id ? 'active' : ''}`;
    div.dataset.kbId = kb.id;
    div.innerHTML = `
      <div class="d-flex justify-content-between align-items-start gap-2">
        <div>
          <div class="fw-semibold">${kb.name}</div>
          <div class="small text-muted">${kb.document_names.join(', ') || 'No docs'}</div>
        </div>
        <span class="badge text-bg-primary">${kb.document_count}</span>
      </div>
      <div class="d-flex gap-2 mt-2">
        <button class="btn btn-sm btn-outline-primary" data-action="use" data-kb-id="${kb.id}">Use in Chat</button>
      </div>
    `;
    list.appendChild(div);
  }

  for (const card of list.querySelectorAll('.kb-card')) {
    card.addEventListener('click', async () => {
      const kbId = card.dataset.kbId;
      if (!kbId) return;
      const kb = kbCache.find((x) => x.id === kbId);
      if (!kb) return;
      await setKbEditorMode('edit', kb);
      await refreshKnowledgeBases();
    });
  }

  for (const btn of list.querySelectorAll('button[data-action="use"]')) {
    btn.addEventListener('click', (event) => {
      event.stopPropagation();
      const quickSelect = document.getElementById('quickKbSelect');
      if (quickSelect) {
        quickSelect.value = btn.dataset.kbId || '';
        syncQuickKbHint();
      }
      const mainSelect = document.getElementById('chatKbSelect');
      if (mainSelect) mainSelect.value = btn.dataset.kbId || '';
      setView('chats');
    });
  }
}

function highlightActiveChat() {
  for (const el of document.querySelectorAll('.chat-item')) {
    el.classList.toggle('active', el.dataset.chatId === currentChatId);
  }
}

async function refreshChats() {
  const res = await fetch(`/api/chats?include_inactive=${showInactiveChats ? 'true' : 'false'}`);
  const chats = await res.json();
  const list = document.getElementById('chatList');
  list.innerHTML = '';

  if (currentChatId && !chats.some((c) => c.id === currentChatId)) {
    currentChatId = null;
    document.getElementById('activeChatTitle').textContent = '';
    document.getElementById('chatMessages').innerHTML = '';
    syncChatHeaderActions();
    syncChatWorkspace();
  }

  if (!chats.length) {
    list.innerHTML = '<li class="list-group-item text-muted small">No chats yet.</li>';
    return;
  }

  for (const chat of chats) {
    const li = document.createElement('li');
    li.className = `list-group-item chat-item ${chat.status === 'inactive' ? 'inactive' : ''}`;
    li.dataset.chatId = chat.id;
    const titleInitial = ((chat.title || 'C').trim()[0] || 'C').toUpperCase();
    li.innerHTML = `
      <div class="d-flex justify-content-between align-items-start gap-2 chat-item-wrap">
        <div class="chat-item-avatar" aria-hidden="true">${titleInitial}</div>
        <div class="flex-grow-1 chat-item-main">
          <div class="fw-semibold text-truncate">${chat.title}</div>
        </div>
      </div>
    `;
    li.addEventListener('click', () => loadChat(chat.id));
    list.appendChild(li);
  }

  highlightActiveChat();
}

async function loadChat(chatId) {
  const res = await fetch(`/api/chats/${chatId}`);
  if (!res.ok) return;

  const chat = await res.json();
  currentChatId = chat.id;
  currentUserName = chat.user_name || 'User';
  currentAssistantName = chat.assistant_name || 'Assistant';
  currentCitationMode = Boolean(chat.citation_mode);
  currentTopK = normalizeTopK(chat.top_k, 5);
  const sourceLabel = chat.knowledge_base_name
    ? `KB: ${chat.knowledge_base_name}`
    : (chat.document_names.join(', ') || 'All indexed docs');
  document.getElementById('activeChatTitle').textContent = `${chat.title} (${sourceLabel})`;
  renderMessages(chat.messages || []);
  highlightActiveChat();
  syncChatHeaderActions();
  syncChatWorkspace();
  syncSendButtons();
}

async function openChatSettingsModal(chatId) {
  const targetChatId = chatId || currentChatId;
  if (!targetChatId) {
    alert('Select a chat first.');
    return;
  }
  const res = await fetch(`/api/chats/${targetChatId}`);
  if (!res.ok) {
    alert('Unable to load chat settings.');
    return;
  }
  const chat = await res.json();
  settingsChatId = targetChatId;
  document.getElementById('chatSettingsTitle').value = chat.title || '';
  document.getElementById('chatSettingsUserName').value = chat.user_name || 'User';
  document.getElementById('chatSettingsAssistantName').value = chat.assistant_name || 'Assistant';
  document.getElementById('chatSettingsCitationMode').checked = Boolean(chat.citation_mode);
  document.getElementById('chatSettingsTopK').value = normalizeTopK(chat.top_k, 5);
  document.getElementById('chatSettingsStatus').value = chat.status || 'active';
  setChatSettingsModalOpen(true);
}

function closeChatSettingsModal() {
  settingsChatId = null;
  setChatSettingsModalOpen(false);
}

function closeAdditionalInfoModal() {
  setAdditionalInfoModalOpen(false);
}

async function saveChatSettings() {
  if (!settingsChatId) return;
  const title = document.getElementById('chatSettingsTitle').value.trim();
  const userName = document.getElementById('chatSettingsUserName').value.trim() || 'User';
  const assistantName = document.getElementById('chatSettingsAssistantName').value.trim() || 'Assistant';
  const citationMode = document.getElementById('chatSettingsCitationMode').checked;
  const topK = normalizeTopK(document.getElementById('chatSettingsTopK').value, 5);
  const status = document.getElementById('chatSettingsStatus').value === 'inactive' ? 'inactive' : 'active';

  let res = await fetch(`/api/chats/${settingsChatId}/settings`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title,
      user_name: userName,
      assistant_name: assistantName,
      citation_mode: citationMode,
      top_k: topK,
    }),
  });

  if (!res.ok) {
    alert('Failed to save chat settings.');
    return;
  }

  const updated = await res.json();
  if (status !== (updated.status || 'active')) {
    res = await fetch(`/api/chats/${settingsChatId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    if (!res.ok) {
      alert('Failed to update chat status.');
      return;
    }
  }

  if (currentChatId === updated.id) {
    currentUserName = updated.user_name || 'User';
    currentAssistantName = updated.assistant_name || 'Assistant';
    currentCitationMode = Boolean(updated.citation_mode);
    currentTopK = normalizeTopK(updated.top_k, 5);
  }

  closeChatSettingsModal();
  await refreshChats();
  if (currentChatId && (status === 'active' || showInactiveChats)) {
    await loadChat(currentChatId);
  } else if (currentChatId && status === 'inactive' && !showInactiveChats) {
    currentChatId = null;
    document.getElementById('activeChatTitle').textContent = '';
    document.getElementById('chatMessages').innerHTML = '';
    syncChatHeaderActions();
    syncChatWorkspace();
  }
}

async function deleteChatFromSettingsModal() {
  if (!settingsChatId) return;
  const chatId = settingsChatId;
  closeChatSettingsModal();
  await deleteChat(chatId);
}

function openCreateChatModal() {
  document.getElementById('newChatModalTitle').textContent = 'Create New Chat';
  document.getElementById('newChatModalSubtitle').textContent = 'All fields are optional.';
  document.getElementById('confirmNewChatBtn').textContent = 'Create Chat';
  document.getElementById('newChatKbGroup').classList.remove('d-none');
  const mainSelect = document.getElementById('chatKbSelect');
  const quickSelect = document.getElementById('quickKbSelect');
  const preselectedKb = (mainSelect && mainSelect.value) || (quickSelect && quickSelect.value) || '';
  populateNewChatKbSelect(preselectedKb);
  document.getElementById('newChatUserName').value = currentUserName || 'User';
  document.getElementById('newChatAssistantName').value = currentAssistantName || 'Assistant';
  setNewChatModalOpen(true);
  document.getElementById('newChatUserName').focus();
}

function closeNewChatModal() {
  setNewChatModalOpen(false);
}

async function createNewChatFromModal() {
  const kbId = document.getElementById('newChatKbSelect').value || null;
  const title = kbId ? 'New KB Chat' : 'New chat';
  const userName = document.getElementById('newChatUserName').value.trim() || 'User';
  const assistantName = document.getElementById('newChatAssistantName').value.trim() || 'Assistant';

  const res = await fetch('/api/chats', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title,
      knowledge_base_id: kbId,
      document_ids: [],
      user_name: userName,
      assistant_name: assistantName,
    }),
  });

  if (!res.ok) {
    alert('Could not create chat.');
    return;
  }

  const chat = await res.json();
  closeNewChatModal();
  try {
    await refreshChats();
    await loadChat(chat.id);
  } catch (_) {
    // Modal is intentionally closed even if follow-up refresh/load fails.
  }
}

async function startQuickChatFromLanding() {
  const input = document.getElementById('quickQuestionInput');
  const question = input.value.trim();
  if (!question) {
    syncSendButtons();
    return;
  }
  const kbSelect = document.getElementById('quickKbSelect');
  const kbId = kbSelect ? (kbSelect.value || null) : null;
  const title = kbId ? 'New KB Chat' : 'New chat';

  const createRes = await fetch('/api/chats', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title,
      knowledge_base_id: kbId,
      document_ids: [],
      user_name: currentUserName || 'User',
      assistant_name: currentAssistantName || 'Assistant',
    }),
  });
  if (!createRes.ok) {
    alert('Could not start chat.');
    return;
  }

  const chat = await createRes.json();
  input.value = '';
  syncSendButtons();
  await refreshChats();
  await loadChat(chat.id);
  document.getElementById('question').value = question;
  syncSendButtons();
  await askQuestion();
}

async function confirmChatModal() {
  await createNewChatFromModal();
}

async function askQuestion() {
  if (!currentChatId) {
    alert('Create or select a chat first.');
    return;
  }

  const questionInput = document.getElementById('question');
  const question = questionInput.value.trim();
  if (!question) return;

  const citation_mode = currentCitationMode;
  const top_k = currentTopK;
  questionInput.value = '';
  syncSendButtons();

  const box = document.getElementById('chatMessages');
  box.insertAdjacentHTML(
    'beforeend',
    `<div class="message-row user"><div class="message user"><div class="msg-role">${escapeHtml(currentUserName)}</div><div class="msg-content">${formatMessageContent(question)}</div></div></div>`,
  );
  addTypingPlaceholder();
  box.scrollTop = box.scrollHeight;

  const res = await fetch(`/api/chats/${currentChatId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, citation_mode, top_k }),
  });

  if (!res.ok) {
    const typingRow = document.getElementById('typingRow');
    if (typingRow) typingRow.remove();
    let detail = 'Failed to query chat.';
    try {
      const err = await res.json();
      if (err.detail) detail = err.detail;
    } catch (_) {}
    alert(detail);
    syncSendButtons();
    return;
  }

  const data = await res.json();
  await renderChatWithTyping(data.messages || []);
  renderCitations(data.citations || []);
  await refreshChats();
  syncSendButtons();
}

async function uploadPdfs() {
  const filesInput = document.getElementById('pdfFiles');
  const out = document.getElementById('uploadOutput');
  if (!filesInput.files.length) {
    out.innerHTML = `<div class="status-line error small">Select at least one PDF before uploading.</div>`;
    return;
  }

  const form = new FormData();
  for (const file of filesInput.files) form.append('files', file);

  out.innerHTML = `<div class="status-line info small">Uploading and queueing documents for indexing...</div>`;
  const res = await fetch('/api/ingest', { method: 'POST', body: form });
  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    data = null;
  }

  if (res.ok) {
    const items = (data && data.items) || [];
    const queued = items.length;
    const names = items.map((x) => x.name).filter(Boolean);
    const namesPreview = names.slice(0, 3).join(', ');
    const more = names.length > 3 ? ` +${names.length - 3} more` : '';
    out.innerHTML = `
      <div class="status-line success small">
        ${queued} PDF${queued === 1 ? '' : 's'} queued for indexing.
        ${namesPreview ? `<br/><span class="text-muted">${escapeHtml(namesPreview)}${escapeHtml(more)}</span>` : ''}
      </div>
    `;
  } else {
    const detail = (data && data.detail) ? String(data.detail) : `Upload failed (HTTP ${res.status}).`;
    out.innerHTML = `
      <div class="status-line error small">${escapeHtml(detail)}</div>
      <details>
        <summary>View technical log</summary>
        <pre class="log-block">${escapeHtml(JSON.stringify(data || { status: res.status, statusText: res.statusText }, null, 2))}</pre>
      </details>
    `;
  }

  setTimeout(async () => {
    await refreshDocs();
    await refreshKnowledgeBases();
  }, 1200);
}

async function saveKbEditor() {
  const name = document.getElementById('kbName').value.trim();
  const document_ids = selectedDocumentIds();
  if (!name) {
    alert('Enter knowledge base name.');
    return;
  }

  let res;
  if (kbEditorMode === 'create' || !editingKbId) {
    res = await fetch('/api/knowledge-bases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, document_ids }),
    });
  } else {
    res = await fetch(`/api/knowledge-bases/${editingKbId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, document_ids }),
    });
  }

  if (!res.ok) {
    alert('Failed to save knowledge base.');
    return;
  }

  const kb = await res.json();
  editingKbId = kb.id;
  kbEditorMode = 'edit';
  await refreshKnowledgeBases();
  await setKbEditorMode('edit', kb);
}

async function setChatStatus(chatId, status) {
  const res = await fetch(`/api/chats/${chatId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    alert('Failed to update chat status.');
    return;
  }
  if (currentChatId === chatId && status === 'inactive' && !showInactiveChats) {
    currentChatId = null;
    document.getElementById('activeChatTitle').textContent = '';
    document.getElementById('chatMessages').innerHTML = '';
    syncChatHeaderActions();
    syncChatWorkspace();
  }
  await refreshChats();
}

async function deleteChat(chatId) {
  const ok = window.confirm('Delete this chat permanently?');
  if (!ok) return;
  const res = await fetch(`/api/chats/${chatId}`, { method: 'DELETE' });
  if (!res.ok) {
    alert('Failed to delete chat.');
    return;
  }
  if (currentChatId === chatId) {
    currentChatId = null;
    document.getElementById('activeChatTitle').textContent = '';
    document.getElementById('chatMessages').innerHTML = '';
    syncChatHeaderActions();
    syncChatWorkspace();
  }
  await refreshChats();
}

document.getElementById('menuChatsBtn').addEventListener('click', () => setView('chats'));
document.getElementById('menuKbBtn').addEventListener('click', () => setView('kb'));
document.getElementById('themeToggleBtn').addEventListener('click', toggleTheme);

document.getElementById('newChatBtn').addEventListener('click', openCenteredNewChatInput);
document.getElementById('closeNewChatModalBtn').addEventListener('click', closeNewChatModal);
document.getElementById('cancelNewChatBtn').addEventListener('click', closeNewChatModal);
document.getElementById('confirmNewChatBtn').addEventListener('click', confirmChatModal);
document.getElementById('closeChatSettingsModalBtn').addEventListener('click', closeChatSettingsModal);
document.getElementById('cancelChatSettingsBtn').addEventListener('click', closeChatSettingsModal);
document.getElementById('saveChatSettingsBtn').addEventListener('click', saveChatSettings);
document.getElementById('deleteChatFromSettingsBtn').addEventListener('click', deleteChatFromSettingsModal);
document.getElementById('openChatSettingsBtn').addEventListener('click', () => openChatSettingsModal(currentChatId));
document.getElementById('openAdditionalInfoBtn').addEventListener('click', () => setAdditionalInfoModalOpen(true));
document.getElementById('quickSendBtn').addEventListener('click', startQuickChatFromLanding);
document.getElementById('quickKbSelect').addEventListener('change', (event) => {
  if (event.target.value === '__add_kb__') {
    event.target.value = '';
    syncQuickKbHint();
    setView('kb');
    const kbName = document.getElementById('kbName');
    if (kbName) kbName.focus();
    return;
  }
  const primaryKb = document.getElementById('chatKbSelect');
  if (primaryKb) primaryKb.value = event.target.value || '';
  syncQuickKbHint();
});
document.getElementById('closeAdditionalInfoModalBtn').addEventListener('click', closeAdditionalInfoModal);
document.getElementById('reloadChatBtn').addEventListener('click', () => currentChatId && loadChat(currentChatId));
document.getElementById('askBtn').addEventListener('click', askQuestion);

document.getElementById('uploadBtn').addEventListener('click', uploadPdfs);
document.getElementById('refreshDocsBtn').addEventListener('click', refreshDocs);
document.getElementById('saveKbBtn').addEventListener('click', saveKbEditor);
document.getElementById('kbCreateModeBtn').addEventListener('click', () => setKbEditorMode('create'));
document.getElementById('resetKbEditorBtn').addEventListener('click', () => {
  if (kbEditorMode === 'edit' && editingKbId) {
    const kb = kbCache.find((x) => x.id === editingKbId);
    if (kb) {
      setKbEditorMode('edit', kb);
      return;
    }
  }
  setKbEditorMode('create');
});
document.getElementById('refreshKbBtn').addEventListener('click', refreshKnowledgeBases);
document.getElementById('showInactiveChats').addEventListener('change', (event) => {
  showInactiveChats = Boolean(event.target.checked);
  refreshChats();
});
document.getElementById('question').addEventListener('input', syncSendButtons);
document.getElementById('question').addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    if (!document.getElementById('askBtn').disabled) {
      askQuestion();
    }
  }
});
document.getElementById('quickQuestionInput').addEventListener('input', syncSendButtons);
document.getElementById('quickQuestionInput').addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    if (!document.getElementById('quickSendBtn').disabled) {
      startQuickChatFromLanding();
    }
  }
});
document.getElementById('newChatModal').addEventListener('click', (event) => {
  if (event.target.id === 'newChatModal') {
    closeNewChatModal();
  }
});
document.getElementById('chatSettingsModal').addEventListener('click', (event) => {
  if (event.target.id === 'chatSettingsModal') {
    closeChatSettingsModal();
  }
});
document.getElementById('additionalInfoModal').addEventListener('click', (event) => {
  if (event.target.id === 'additionalInfoModal') {
    closeAdditionalInfoModal();
  }
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeNewChatModal();
    closeChatSettingsModal();
    closeAdditionalInfoModal();
  }
});

(async function init() {
  setNewChatModalOpen(false);
  setChatSettingsModalOpen(false);
  setAdditionalInfoModalOpen(false);
  applyTheme(localStorage.getItem('rag_theme') || 'light');
  setView(currentView);
  syncChatHeaderActions();
  syncChatWorkspace();
  syncSendButtons();
  syncQuickKbHint();
  await refreshDocs([]);
  await refreshKnowledgeBases();
  await setKbEditorMode('create');
  await refreshChats();
})();

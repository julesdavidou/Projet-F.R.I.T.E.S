(() => {
  const STORAGE_KEY = "frites-standalone-state-v3";
  const THEME_KEY = "frites-theme-mode";

  const SCENARIOS = [
    {
      id: "phishing",
      title: "Mission phishing — livraison suspecte",
      prompt: "Lance une mission guidée pour apprendre à repérer un phishing de livraison suspecte. Donne-moi les indices un par un.",
      action: "Préparer une mission phishing"
    },
    {
      id: "password",
      title: "Créer un mot de passe solide",
      prompt: "Explique-moi comment créer un mot de passe solide et mémorisable, avec une méthode simple et des erreurs à éviter.",
      action: "Préparer un exemple"
    },
    {
      id: "wifi",
      title: "Wi‑Fi public au café",
      prompt: "Je suis sur un Wi-Fi public dans un café. Quels réflexes dois-je avoir pour limiter les risques ?",
      action: "Préparer les réflexes Wi‑Fi"
    },
    {
      id: "sms",
      title: "Arnaque SMS bancaire",
      prompt: "Aide-moi à analyser un SMS bancaire suspect et à savoir quoi faire sans prendre de risque.",
      action: "Préparer l’analyse SMS"
    },
    {
      id: "attachment",
      title: "Pièce jointe inconnue",
      prompt: "J’ai reçu une pièce jointe inconnue. Donne-moi une procédure simple pour vérifier le risque avant de l’ouvrir.",
      action: "Préparer la procédure"
    },
    {
      id: "quiz",
      title: "Quiz réflexes cyber",
      prompt: "Lance un mini-quiz de 5 questions pour tester mes réflexes cybersécurité. Pose une question à la fois.",
      action: "Préparer le mini‑quiz"
    },
    {
      id: "privacy",
      title: "Réseaux sociaux et confidentialité",
      prompt: "Explique-moi les bons réglages de confidentialité à vérifier sur les réseaux sociaux.",
      action: "Préparer les réglages"
    },
    {
      id: "mfa",
      title: "MFA et double authentification",
      prompt: "Explique-moi la MFA simplement et aide-moi à choisir une bonne méthode de double authentification.",
      action: "Préparer l’explication MFA"
    }
  ];

  const $ = (selector) => document.querySelector(selector);
  const els = {
    sidebar: $("#sidebar"),
    backdrop: $("#mobileBackdrop"),
    mobileMenu: $("#mobileMenuBtn"),
    newBtn: $("#newConversationBtn"),
    search: $("#conversationSearch"),
    list: $("#conversationList"),
    title: $("#chatTitle"),
    subtitle: $("#chatSubtitle"),
    messages: $("#messages"),
    form: $("#composer"),
    input: $("#messageInput"),
    send: $("#sendBtn"),
    voice: $("#voiceBtn"),
    themeToggle: $("#themeToggleBtn"),
    emptyTemplate: $("#emptyStateTemplate")
  };

  let state = loadState();
  let draftConversation = makeDraftConversation();
  let isSending = false;
  let dotStep = 0;
  let titleTicker = null;
  let mediaRecorder = null;
  let mediaStream = null;
  let recordingChunks = [];
  let toastTimer = null;
  let currentSpeechButton = null;

  let manualTheme = readThemePreference();

  function readThemePreference() {
    try {
      const saved = localStorage.getItem(THEME_KEY);
      return saved === "light" || saved === "dark" ? saved : null;
    } catch (_) {
      return null;
    }
  }

  function systemTheme() {
    return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light";
  }

  function effectiveTheme() {
    return manualTheme || systemTheme();
  }

  function applyTheme() {
    const theme = effectiveTheme();
    document.documentElement.dataset.theme = theme;
    if (!els.themeToggle) return;
    const isDark = theme === "dark";
    els.themeToggle.querySelector(".theme-toggle-icon").textContent = isDark ? "☀" : "☾";
    els.themeToggle.setAttribute("aria-label", isDark ? "Passer en mode clair" : "Passer en mode sombre");
    els.themeToggle.title = manualTheme
      ? (isDark ? "Passer en mode clair" : "Passer en mode sombre")
      : (isDark ? "Thème système sombre — passer en clair" : "Thème système clair — passer en sombre");
  }

  function toggleTheme() {
    manualTheme = effectiveTheme() === "dark" ? "light" : "dark";
    try { localStorage.setItem(THEME_KEY, manualTheme); } catch (_) {}
    applyTheme();
  }

  window.matchMedia?.("(prefers-color-scheme: dark)")?.addEventListener?.("change", () => {
    if (!manualTheme) applyTheme();
  });


  function uid() {
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
  }

  function makeDraftConversation() {
    return {
      id: "draft",
      title: "Nouvelle conversation cyber",
      empty: true,
      transient: true,
      scenarioId: null,
      messages: []
    };
  }

  function createInitialState() {
    return { activeId: null, conversations: [] };
  }

  function normaliseState(candidate) {
    if (!candidate || !Array.isArray(candidate.conversations)) return createInitialState();
    return {
      activeId: candidate.activeId || null,
      conversations: candidate.conversations
        .filter((conversation) => Array.isArray(conversation.messages) && conversation.messages.length > 0)
        .map((conversation) => ({
          id: conversation.id || uid(),
          title: conversation.title || "Conversation cyber",
          messages: conversation.messages.map((message) => ({
            role: message.role === "user" ? "user" : "assistant",
            content: String(message.content || ""),
            pending: Boolean(message.pending),
            error: Boolean(message.error),
            steps: Array.isArray(message.steps) ? message.steps : [],
            sources: Array.isArray(message.sources) ? message.sources : []
          })),
          createdAt: conversation.createdAt || Date.now(),
          updatedAt: conversation.updatedAt || Date.now(),
          titlePending: Boolean(conversation.titlePending),
          scenarioId: conversation.scenarioId || null
        }))
    };
  }

  function loadState() {
    try {
      return normaliseState(JSON.parse(localStorage.getItem(STORAGE_KEY)));
    } catch (_) {
      return createInitialState();
    }
  }

  function saveState() {
    const persisted = {
      activeId: state.activeId,
      conversations: state.conversations.filter((conversation) => conversation.messages?.length)
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
  }

  function activeConversation() {
    return state.conversations.find((conversation) => conversation.id === state.activeId) || draftConversation;
  }

  function scenarioFor(conversation) {
    return SCENARIOS.find((scenario) => scenario.id === conversation.scenarioId);
  }

  function displayTitle(conversation) {
    if (conversation?.titlePending) return ".".repeat((dotStep % 3) + 1);
    return conversation?.title || "Nouvelle conversation cyber";
  }

  function startTitleTicker() {
    if (titleTicker) return;
    titleTicker = window.setInterval(() => {
      if (!state.conversations.some((conversation) => conversation.titlePending)) {
        window.clearInterval(titleTicker);
        titleTicker = null;
        return;
      }
      dotStep = (dotStep + 1) % 3;
      renderSidebar();
      renderHeader(activeConversation());
    }, 450);
  }

  function setActive(id) {
    state.activeId = id;
    draftConversation = makeDraftConversation();
    saveState();
    render();
    closeMobileMenu();
  }

  function newConversation() {
    state.activeId = null;
    draftConversation = makeDraftConversation();
    saveState();
    render();
    closeMobileMenu();
    requestAnimationFrame(() => els.input.focus());
  }

  function persistDraftIfNeeded(conversation) {
    if (!conversation.transient) return conversation;
    const persisted = {
      id: uid(),
      title: "...",
      titlePending: true,
      empty: false,
      transient: false,
      scenarioId: conversation.scenarioId || null,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    };
    state.conversations.unshift(persisted);
    state.activeId = persisted.id;
    draftConversation = makeDraftConversation();
    startTitleTicker();
    return persisted;
  }

  function deleteConversation(id) {
    const conversation = state.conversations.find((item) => item.id === id);
    if (!conversation) return;

    showConfirm(`Supprimer « ${displayTitle(conversation)} » de l’historique ?`, () => {
      state.conversations = state.conversations.filter((item) => item.id !== id);
      if (state.activeId === id) {
        state.activeId = state.conversations[0]?.id || null;
        if (!state.activeId) draftConversation = makeDraftConversation();
      }
      saveState();
      render();
    });
  }

  function ensureToastRoot() {
    let root = document.getElementById("toastRoot");
    if (!root) {
      root = document.createElement("div");
      root.id = "toastRoot";
      root.className = "toast-root";
      document.body.appendChild(root);
    }
    return root;
  }

  function showToast(message, tone = "warning") {
    const root = ensureToastRoot();
    root.innerHTML = "";
    const toast = document.createElement("div");
    toast.className = `frite-toast ${tone}`;
    toast.innerHTML = `<strong>${tone === "error" ? "Oups" : "Info"}</strong><span>${escapeHtml(message)}</span>`;
    root.appendChild(toast);
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.remove(), 5200);
  }

  function showConfirm(message, onConfirm) {
    const previous = document.querySelector(".frite-modal-backdrop");
    if (previous) previous.remove();

    const backdrop = document.createElement("div");
    backdrop.className = "frite-modal-backdrop";
    backdrop.innerHTML = `
      <div class="frite-modal" role="dialog" aria-modal="true" aria-label="Confirmation">
        <h2>Confirmer la suppression</h2>
        <p>${escapeHtml(message)}</p>
        <div class="frite-modal-actions">
          <button type="button" class="modal-btn secondary" data-action="cancel">Annuler</button>
          <button type="button" class="modal-btn danger" data-action="confirm">Supprimer</button>
        </div>
      </div>`;

    const close = () => backdrop.remove();
    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop || event.target?.dataset?.action === "cancel") close();
      if (event.target?.dataset?.action === "confirm") {
        close();
        onConfirm?.();
      }
    });
    document.body.appendChild(backdrop);
    backdrop.querySelector('[data-action="cancel"]')?.focus();
  }

  function renderSidebar() {
    const filter = els.search.value.trim().toLowerCase();
    const conversations = state.conversations.filter((item) => displayTitle(item).toLowerCase().includes(filter));
    els.list.innerHTML = "";

    if (!conversations.length) {
      const empty = document.createElement("div");
      empty.className = "conversation-empty";
      empty.textContent = filter ? "Aucune conversation trouvée." : "Aucune conversation pour le moment.";
      els.list.appendChild(empty);
      return;
    }

    conversations.forEach((item) => {
      const row = document.createElement("div");
      row.className = `conversation-row${item.id === state.activeId ? " active" : ""}`;

      const button = document.createElement("button");
      button.type = "button";
      button.className = "conversation-item";
      button.textContent = displayTitle(item);
      button.title = item.titlePending ? "Titre en cours de génération" : item.title;
      button.addEventListener("click", () => setActive(item.id));

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "delete-conversation";
      remove.setAttribute("aria-label", `Supprimer ${item.title}`);
      remove.title = "Supprimer la conversation";
      remove.textContent = "×";
      remove.addEventListener("click", (event) => {
        event.stopPropagation();
        deleteConversation(item.id);
      });

      row.appendChild(button);
      row.appendChild(remove);
      els.list.appendChild(row);
    });
  }

  function renderHeader(conversation) {
    els.title.textContent = displayTitle(conversation);
    els.subtitle.textContent = conversation.messages?.length ? "Mission guidée • réflexes cybersécurité" : "Dialogue guidé • éveil cybersécurité";
  }

  function renderMessages(conversation) {
    els.messages.innerHTML = "";
    if (!conversation.messages?.length) {
      const empty = els.emptyTemplate.content.cloneNode(true);
      empty.querySelectorAll("[data-starter]").forEach((button) => {
        button.addEventListener("click", () => prefillScenario(button.dataset.starter));
      });
      els.messages.appendChild(empty);
      return;
    }

    const card = document.createElement("div");
    card.className = "guidance-card";
    card.innerHTML = `<img class="guidance-icon" src="/assets/frite-logo.png" alt="" aria-hidden="true"><strong>F.R.I.T.E.S est là pour vous saucer.</strong>`;
    els.messages.appendChild(card);

    conversation.messages.forEach((message) => appendMessageNode(message));

    // Nettoyage de sécurité : les anciennes versions pouvaient laisser des propositions
    // dans une discussion déjà commencée.
    els.messages.querySelectorAll(".quick-actions").forEach((node) => node.remove());

    scrollToBottom(false);
  }

  function appendMessageNode(messageOrRole, content, pending = false, error = false) {
    const message = typeof messageOrRole === "object"
      ? messageOrRole
      : { role: messageOrRole, content, pending, error, steps: [], sources: [] };

    const row = document.createElement("div");
    row.className = `message-row ${message.role === "user" ? "user" : "assistant"}`;

    const stack = document.createElement("div");
    stack.className = "message-stack";

    if (message.role !== "user" && !message.pending && Array.isArray(message.steps) && message.steps.length) {
      stack.appendChild(renderSteps(message.steps, message.sources || []));
    }

    const bubble = document.createElement("div");
    bubble.className = `bubble${message.pending ? " typing" : ""}${message.error ? " error" : ""}`;
    if (message.pending || message.role === "user") {
      bubble.textContent = message.content;
    } else {
      bubble.innerHTML = renderMarkdown(message.content || "");
    }

    stack.appendChild(bubble);

    if (message.role !== "user" && !message.pending && !message.error) {
      const toolbar = document.createElement("div");
      toolbar.className = "message-toolbar";
      const speak = document.createElement("button");
      speak.type = "button";
      speak.className = "speak-btn";
      speak.setAttribute("aria-label", "Lire la réponse à voix haute");
      speak.title = "Lire la réponse à voix haute";
      speak.innerHTML = speakerIconSvg();
      speak.addEventListener("click", () => speakAnswer(message.content || "", speak));
      toolbar.appendChild(speak);
      stack.appendChild(toolbar);
    }

    row.appendChild(stack);
    els.messages.appendChild(row);
    return row;
  }

  function speakerIconSvg() {
    return `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M4 9v6h4l5 4V5L8 9H4Z"></path>
      <path d="M16 9.5a4 4 0 0 1 0 5"></path>
      <path d="M18.5 7a7 7 0 0 1 0 10"></path>
    </svg>`;
  }

  function stopIconSvg() {
    return `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7 7h10v10H7z"></path></svg>`;
  }

  function plainTextFromMarkdown(markdown) {
    return String(markdown || "")
      .replace(/\n\s*Sources?\s*:\s*[\s\S]*$/i, "")
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1")
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/^\s*[-*•]\s+/gm, "")
      .replace(/^\s*\d+\.\s+/gm, "")
      .replace(/[>*_~]/g, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function resetSpeechButton(button) {
    if (!button) return;
    button.classList.remove("speaking");
    button.setAttribute("aria-label", "Lire la réponse à voix haute");
    button.title = "Lire la réponse à voix haute";
    button.innerHTML = speakerIconSvg();
    if (currentSpeechButton === button) currentSpeechButton = null;
  }

  function speakAnswer(markdown, button) {
    if (!("speechSynthesis" in window) || !window.SpeechSynthesisUtterance) {
      showToast("La lecture vocale n’est pas disponible dans ce navigateur.", "warning");
      return;
    }

    if (window.speechSynthesis.speaking && currentSpeechButton === button) {
      window.speechSynthesis.cancel();
      resetSpeechButton(button);
      return;
    }

    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      resetSpeechButton(currentSpeechButton);
    }

    const text = plainTextFromMarkdown(markdown);
    if (!text) {
      showToast("Aucun texte lisible dans cette réponse.", "warning");
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "fr-FR";
    utterance.rate = 1;
    utterance.pitch = 1;
    currentSpeechButton = button;
    button.classList.add("speaking");
    button.setAttribute("aria-label", "Arrêter la lecture");
    button.title = "Arrêter la lecture";
    button.innerHTML = stopIconSvg();
    utterance.onend = () => resetSpeechButton(button);
    utterance.onerror = () => {
      resetSpeechButton(button);
      showToast("La lecture vocale a été interrompue.", "warning");
    };
    window.speechSynthesis.speak(utterance);
  }

  function renderSteps(steps, sources) {
    const details = document.createElement("details");
    details.className = "processing-steps";
    details.open = true;
    const summary = document.createElement("summary");
    summary.textContent = "Étapes de traitement";
    details.appendChild(summary);

    const list = document.createElement("ol");
    steps.forEach((step) => {
      const item = document.createElement("li");
      item.className = `step-${step.status || "done"}`;
      const title = document.createElement("strong");
      title.textContent = step.title || "Étape";
      item.appendChild(title);
      if (step.detail) {
        const detail = document.createElement("span");
        detail.textContent = ` — ${step.detail}`;
        item.appendChild(detail);
      }
      list.appendChild(item);
    });

    if (Array.isArray(sources) && sources.length) {
      const item = document.createElement("li");
      item.className = "step-sources";
      const strong = document.createElement("strong");
      strong.textContent = "PDF liés";
      item.appendChild(strong);
      const links = document.createElement("div");
      links.className = "step-source-links";
      sources.forEach((source) => {
        const a = document.createElement("a");
        a.href = source.url || sourceUrl(source.name, source.page);
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = source.page ? `${source.name}, page ${source.page}` : source.name;
        links.appendChild(a);
      });
      item.appendChild(links);
      list.appendChild(item);
    }

    details.appendChild(list);
    return details;
  }

  function render() {
    const conversation = activeConversation();
    renderSidebar();
    renderHeader(conversation);
    renderMessages(conversation);
  }

  function prefillText(text) {
    els.input.value = text;
    autosizeInput();
    closeMobileMenu();
    requestAnimationFrame(() => {
      els.input.focus();
      els.input.setSelectionRange(els.input.value.length, els.input.value.length);
    });
  }

  function prefillScenario(id) {
    const scenario = SCENARIOS.find((item) => item.id === id);
    if (!scenario) return;
    draftConversation.scenarioId = scenario.id;
    prefillText(scenario.prompt);
  }

  function fallbackTitle(text) {
    const words = text
      .replace(/[\n\r]+/g, " ")
      .replace(/["“”'’]/g, "")
      .replace(/\s+/g, " ")
      .trim()
      .split(" ")
      .filter(Boolean)
      .slice(0, 9);
    return words.join(" ") || "Conversation cyber";
  }

  async function generateTitle(conversationId, userText) {
    const conversation = state.conversations.find((item) => item.id === conversationId);
    if (!conversation || !conversation.titlePending) return;

    try {
      const response = await fetch("/api/title", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Erreur HTTP ${response.status}`);
      conversation.title = data.title || fallbackTitle(userText);
    } catch (_) {
      conversation.title = fallbackTitle(userText);
    } finally {
      conversation.titlePending = false;
      conversation.updatedAt = Date.now();
      saveState();
      render();
    }
  }

  async function sendMessage(forcedText) {
    const text = (forcedText ?? els.input.value).trim();
    if (!text || isSending) return;

    let conversation = persistDraftIfNeeded(activeConversation());
    const isFirstMessage = !conversation.messages?.length;
    conversation.messages = conversation.messages || [];
    conversation.messages.push({ role: "user", content: text });
    conversation.updatedAt = Date.now();
    els.input.value = "";
    autosizeInput();

    isSending = true;
    els.send.disabled = true;
    saveState();
    render();

    if (isFirstMessage) generateTitle(conversation.id, text);

    const pendingMessage = { role: "assistant", content: "F.R.I.T.E.S prépare une réponse croustillante…", pending: true, steps: [] };
    conversation.messages.push(pendingMessage);
    saveState();
    render();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: conversation.id, message: text })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Erreur HTTP ${response.status}`);
      pendingMessage.content = data.content || "Je n’ai pas reçu de réponse exploitable.";
      pendingMessage.steps = Array.isArray(data.steps) ? data.steps : [];
      pendingMessage.sources = Array.isArray(data.sources) ? data.sources : [];
      pendingMessage.pending = false;
    } catch (error) {
      pendingMessage.content = `Impossible de contacter l’agent : ${error.message || error}`;
      pendingMessage.pending = false;
      pendingMessage.error = true;
    } finally {
      isSending = false;
      els.send.disabled = false;
      conversation.updatedAt = Date.now();
      saveState();
      render();
      requestAnimationFrame(() => els.input.focus());
    }
  }

  function autosizeInput() {
    els.input.style.height = "auto";
    els.input.style.height = `${Math.min(els.input.scrollHeight, 128)}px`;
  }

  function scrollToBottom(smooth = true) {
    els.messages.scrollTo({ top: els.messages.scrollHeight, behavior: smooth ? "smooth" : "auto" });
  }

  function openMobileMenu() {
    els.sidebar.classList.add("open");
    els.backdrop.hidden = false;
  }

  function closeMobileMenu() {
    els.sidebar.classList.remove("open");
    els.backdrop.hidden = true;
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function inlineMarkdown(raw) {
    let html = escapeHtml(raw);
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+|\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/__([^_]+)__/g, "<strong>$1</strong>");
    html = html.replace(/(^|\s)\*([^*\n]+)\*(?=\s|$|[.,;:!?])/g, "$1<em>$2</em>");
    return html;
  }

  function sourceUrl(name, page) {
    const cleaned = String(name || "").replace(/\.pdf$/i, "").trim();
    let url = `/api/source/${encodeURIComponent(cleaned)}`;
    const pageMatch = String(page || "").match(/\d+/);
    if (pageMatch) url += `#page=${pageMatch[0]}`;
    return url;
  }

  function renderSourceLine(rawLine) {
    const cleaned = rawLine.replace(/^\s*[-*•]\s*/, "").trim();
    const match = cleaned.match(/^(.+?)(?:,\s*page\s*(.+))?$/i);
    if (!match) return inlineMarkdown(rawLine);
    const name = match[1].trim().replace(/\.pdf$/i, "");
    const page = match[2]?.trim();
    const label = page ? `${name}, page ${page}` : name;
    return `<a class="source-link" href="${sourceUrl(name, page)}" target="_blank" rel="noopener noreferrer">${inlineMarkdown(label)}</a>`;
  }

  function flushParagraph(blocks, paragraph) {
    if (!paragraph.length) return;
    blocks.push(`<p>${paragraph.map(inlineMarkdown).join("<br>")}</p>`);
    paragraph.length = 0;
  }

  function closeList(blocks, listState) {
    if (!listState.type) return;
    if (listState.type === "source-ul") {
      blocks.push("</ul></div>");
    } else {
      blocks.push(`</${listState.type}>`);
    }
    listState.type = null;
  }

  function openList(blocks, listState, type) {
    if (listState.type === type) return;
    closeList(blocks, listState);
    blocks.push(`<${type}>`);
    listState.type = type;
  }

  function renderMarkdown(markdown) {
    const lines = String(markdown || "").replace(/\r\n/g, "\n").split("\n");
    const blocks = [];
    const paragraph = [];
    const listState = { type: null };
    let inSources = false;

    for (const line of lines) {
      const trimmed = line.trim();

      if (!trimmed) {
        flushParagraph(blocks, paragraph);
        closeList(blocks, listState);
        continue;
      }

      if (/^(\*\s*){3,}$/.test(trimmed) || /^[-_]{3,}$/.test(trimmed)) {
        flushParagraph(blocks, paragraph);
        closeList(blocks, listState);
        blocks.push("<hr>");
        continue;
      }

      if (/^Sources?\s*:\s*$/i.test(trimmed)) {
        flushParagraph(blocks, paragraph);
        closeList(blocks, listState);
        inSources = true;
        blocks.push('<div class="sources-block"><strong>Sources :</strong><ul>');
        listState.type = "source-ul";
        continue;
      }

      if (inSources) {
        const sourceContent = renderSourceLine(trimmed);
        blocks.push(`<li>${sourceContent}</li>`);
        continue;
      }

      const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
      if (heading) {
        flushParagraph(blocks, paragraph);
        closeList(blocks, listState);
        const level = Math.min(heading[1].length + 2, 6);
        blocks.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
        continue;
      }

      const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
      if (ordered) {
        flushParagraph(blocks, paragraph);
        openList(blocks, listState, "ol");
        blocks.push(`<li>${inlineMarkdown(ordered[1])}</li>`);
        continue;
      }

      const unordered = trimmed.match(/^[-*•]\s+(.+)$/);
      if (unordered) {
        flushParagraph(blocks, paragraph);
        openList(blocks, listState, "ul");
        blocks.push(`<li>${inlineMarkdown(unordered[1])}</li>`);
        continue;
      }

      closeList(blocks, listState);
      paragraph.push(line);
    }

    flushParagraph(blocks, paragraph);
    closeList(blocks, listState);
    return blocks.join("\n");
  }

  function setVoiceState(recording, message) {
    els.voice.classList.toggle("recording", Boolean(recording));
    els.voice.setAttribute("aria-label", recording ? "Arrêter la dictée vocale" : "Démarrer la dictée vocale");
    els.voice.title = recording ? "Arrêter la dictée vocale" : "Démarrer la dictée vocale";
    if (message) els.input.placeholder = message;
    else els.input.placeholder = "Pose ta question...";
  }

  function supportedMimeType() {
    const candidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "audio/ogg",
      "audio/mp4"
    ];
    return candidates.find((candidate) => window.MediaRecorder?.isTypeSupported?.(candidate)) || "";
  }

  async function startServerDictation() {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      return startBrowserDictation();
    }

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = supportedMimeType();
      mediaRecorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined);
      recordingChunks = [];

      mediaRecorder.addEventListener("dataavailable", (event) => {
        if (event.data?.size) recordingChunks.push(event.data);
      });

      mediaRecorder.addEventListener("stop", async () => {
        const tracks = mediaStream?.getTracks?.() || [];
        tracks.forEach((track) => track.stop());
        const blob = new Blob(recordingChunks, { type: mediaRecorder?.mimeType || "audio/webm" });
        mediaRecorder = null;
        mediaStream = null;
        recordingChunks = [];
        setVoiceState(false);

        if (!blob.size) return;

        try {
          els.voice.disabled = true;
          setVoiceState(false, "Transcription en cours...");
          const formData = new FormData();
          const ext = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "m4a" : "webm";
          formData.append("file", blob, `dictation.${ext}`);
          const response = await fetch("/api/transcribe", { method: "POST", body: formData });
          const data = await response.json().catch(() => ({}));
          if (!response.ok) throw new Error(data.detail || `Erreur HTTP ${response.status}`);
          if (data.text) prefillText(data.text);
        } catch (error) {
          showToast(error.message || "La transcription vocale a échoué.", "error");
        } finally {
          els.voice.disabled = false;
          setVoiceState(false);
        }
      });

      mediaRecorder.start();
      setVoiceState(true, "Parle maintenant… clique de nouveau pour arrêter.");
    } catch (error) {
      console.warn("Dictée serveur indisponible, tentative SpeechRecognition.", error);
      startBrowserDictation();
    }
  }

  function startBrowserDictation() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      showToast("La dictée vocale n’est pas disponible ici. Vérifie l’autorisation micro, utilise Chrome/Edge ou saisis ton message au clavier.", "warning");
      return;
    }
    const recognition = new Recognition();
    recognition.lang = "fr-FR";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    setVoiceState(true, "Écoute en cours… parle maintenant.");
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      if (transcript) prefillText(transcript);
    };
    recognition.onend = () => setVoiceState(false);
    recognition.onerror = (event) => {
      setVoiceState(false);
      if (event.error === "no-speech") showToast("Aucun texte reconnu. Réessaie en parlant un peu plus près du micro.", "warning");
      else if (event.error) showToast(`Dictée vocale interrompue : ${event.error}`, "warning");
    };
    recognition.start();
  }

  function toggleDictation() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      setVoiceState(false, "Transcription en cours...");
      return;
    }
    startServerDictation();
  }

  els.newBtn.addEventListener("click", newConversation);
  els.search.addEventListener("input", renderSidebar);
  els.form.addEventListener("submit", (event) => { event.preventDefault(); sendMessage(); });
  els.input.addEventListener("input", autosizeInput);
  els.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });
  els.mobileMenu.addEventListener("click", openMobileMenu);
  els.backdrop.addEventListener("click", closeMobileMenu);
  els.voice.addEventListener("click", toggleDictation);
  els.themeToggle?.addEventListener("click", toggleTheme);

  applyTheme();
  render();
  autosizeInput();
  startTitleTicker();
})();

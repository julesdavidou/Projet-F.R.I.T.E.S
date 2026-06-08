(() => {
  /**
   * F.R.I.T.E.S. Chainlit shell
   * - Ne force pas le thème : s'adapte à la classe/attribut dark de Chainlit ou au système.
   * - Récupère la logique du prototype Figma/Vite : conversations, actif, localStorage.
   * - Branche les boutons de la sidebar sur le vrai composer Chainlit.
   */

  const LOGO = "/public/frite-logo.png";
  const STORAGE_KEY = "frites-conversations";

  // Passe à true si tu veux que les boutons récents envoient directement le prompt.
  // À false, le prompt est seulement écrit dans le champ : l'utilisateur valide lui-même.
  const AUTO_SEND_SCENARIO_PROMPTS = false;

  const INITIAL_CONVERSATIONS = [
    { title: "Mission phishing — livraison suspecte" },
    { title: "Créer un mot de passe solide" },
    { title: "Wi‑Fi public au café" },
    { title: "Arnaque SMS bancaire" },
    { title: "Pièce jointe inconnue" },
    { title: "Quiz réflexes cyber" },
    { title: "Réseaux sociaux et confidentialité" }
  ];

  const SCENARIO_PROMPTS = {
    "Mission phishing — livraison suspecte": "Lance une mission guidée de sensibilisation au phishing sur le thème d'une livraison suspecte. Pose-moi des questions simples, explique les indices à vérifier, puis propose un mini-quiz.",
    "Créer un mot de passe solide": "Aide-moi à créer un mot de passe solide et mémorisable. Explique les bons réflexes avec des exemples simples, sans me demander d'écrire un vrai mot de passe personnel.",
    "Wi‑Fi public au café": "Explique les risques d'un Wi‑Fi public au café et donne-moi les bons réflexes pour protéger mes comptes et mes données.",
    "Arnaque SMS bancaire": "Lance un scénario guidé sur une arnaque SMS bancaire. Aide-moi à repérer les signaux d'alerte et à savoir quoi faire sans cliquer.",
    "Pièce jointe inconnue": "Explique quoi faire face à une pièce jointe inconnue ou inattendue. Donne une méthode courte pour décider si je dois l'ouvrir ou non.",
    "Quiz réflexes cyber": "Lance un mini-quiz de 5 questions sur les réflexes cyber du quotidien, avec correction pédagogique après chaque réponse.",
    "Réseaux sociaux et confidentialité": "Aide-moi à améliorer ma confidentialité sur les réseaux sociaux avec une checklist simple et priorisée."
  };

  function isInsideShell(el) {
    return Boolean(el?.closest?.("#frite-sidebar, #frite-chat-header, #frite-empty-hero"));
  }

  function getDefaultState() {
    return {
      conversations: INITIAL_CONVERSATIONS,
      active: { title: "Nouvelle conversation cyber", empty: true }
    };
  }

  function loadState() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return getDefaultState();
      const parsed = JSON.parse(stored);
      if (!Array.isArray(parsed?.conversations) || !parsed?.active?.title) return getDefaultState();
      return parsed;
    } catch {
      return getDefaultState();
    }
  }

  function saveState(next) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch {}
  }

  let state = loadState();

  function setActive(conversation) {
    state = { ...state, active: conversation };
    saveState(state);
    renderShellState();
  }

  function createConversation() {
    const baseTitle = "Nouvelle conversation cyber";
    const count = state.conversations.filter((c) => c.title.startsWith(baseTitle)).length;
    const title = count ? `${baseTitle} ${count + 1}` : baseTitle;
    const nextConversation = { title, empty: true };
    state = {
      conversations: [nextConversation, ...state.conversations],
      active: nextConversation
    };
    saveState(state);
    renderShellState();
    startNativeNewChat();
  }

  function currentThemeIsDark() {
    const root = document.documentElement;
    const body = document.body;
    const attr = `${root.getAttribute("data-theme") || ""} ${body.getAttribute("data-theme") || ""}`.toLowerCase();
    const cls = `${root.className || ""} ${body.className || ""}`.toLowerCase();
    if (attr.includes("dark") || cls.includes("dark")) return true;
    if (attr.includes("light") || cls.includes("light")) return false;
    return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches || false;
  }

  function syncThemeClass() {
    document.body.classList.toggle("frite-system-dark", currentThemeIsDark());
  }

  function nativeNewChatButton() {
    const candidates = [...document.querySelectorAll("button, a")].filter((el) => !isInsideShell(el));
    const labels = [/new chat/i, /nouvelle conversation/i, /nouveau chat/i, /new conversation/i];
    return candidates.find((el) => {
      const text = `${el.textContent || ""} ${el.getAttribute("aria-label") || ""} ${el.getAttribute("title") || ""}`;
      return labels.some((rx) => rx.test(text));
    });
  }

  function startNativeNewChat() {
    const btn = nativeNewChatButton();
    if (btn) {
      btn.click();
      // Si confirm_new_chat=true, Chainlit peut ouvrir une modale. On ne force pas le clic de confirmation.
      return;
    }
    // Fallback stable : recharge la session en conservant l'état UI F.R.I.T.E.S.
    window.setTimeout(() => {
      const url = new URL(window.location.href);
      url.searchParams.set("frite_new", String(Date.now()));
      window.location.href = url.toString();
    }, 80);
  }

  function findComposer() {
    const selectors = [
      "textarea:not([readonly]):not([disabled])",
      "[contenteditable='true']",
      "input[type='text']:not([readonly]):not([disabled])"
    ];
    for (const selector of selectors) {
      const nodes = [...document.querySelectorAll(selector)].filter((el) => !isInsideShell(el));
      const visible = nodes.reverse().find((el) => {
        const r = el.getBoundingClientRect();
        return r.width > 80 && r.height > 10 && r.bottom > window.innerHeight * 0.45;
      });
      if (visible) return visible;
    }
    return null;
  }

  function setNativeValue(el, value) {
    if (!el) return false;
    el.focus();
    if (el.isContentEditable) {
      el.textContent = value;
      el.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: value }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    }
    const proto = Object.getPrototypeOf(el);
    const descriptor = Object.getOwnPropertyDescriptor(proto, "value") || Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value") || Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value");
    if (descriptor?.set) descriptor.set.call(el, value);
    else el.value = value;
    el.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: value }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function findSendButton(composer) {
    const form = composer?.closest?.("form");
    const formButtons = form ? [...form.querySelectorAll("button")].filter((el) => !isInsideShell(el)) : [];
    const allButtons = [...document.querySelectorAll("button")].filter((el) => !isInsideShell(el));
    const candidates = [...formButtons, ...allButtons].filter((btn) => {
      const r = btn.getBoundingClientRect();
      if (r.width < 16 || r.height < 16 || btn.disabled) return false;
      const label = `${btn.textContent || ""} ${btn.getAttribute("aria-label") || ""} ${btn.getAttribute("title") || ""}`.toLowerCase();
      return /send|envoyer|submit|arrow|message|soumettre/.test(label) || btn.type === "submit" || r.bottom > window.innerHeight * 0.72;
    });
    return candidates[candidates.length - 1] || null;
  }

  function sendPrompt(prompt, { autoSend = AUTO_SEND_SCENARIO_PROMPTS } = {}) {
    const composer = findComposer();
    if (!composer) {
      console.warn("[F.R.I.T.E.S UI] Composer Chainlit introuvable.");
      return false;
    }
    setNativeValue(composer, prompt);

    if (!autoSend) return true;

    window.setTimeout(() => {
      const send = findSendButton(composer);
      if (send) {
        send.click();
      } else {
        composer.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true, cancelable: true }));
        composer.dispatchEvent(new KeyboardEvent("keyup", { key: "Enter", code: "Enter", bubbles: true, cancelable: true }));
      }
    }, 140);
    return true;
  }

  function clickConversation(title) {
    const conversation = state.conversations.find((c) => c.title === title) || { title };
    setActive({ ...conversation, empty: false });
    const prompt = SCENARIO_PROMPTS[title];
    if (prompt) sendPrompt(prompt);
  }

  function filterConversations(query) {
    const q = query.trim().toLowerCase();
    document.querySelectorAll(".frite-recent-btn").forEach((btn) => {
      const title = btn.getAttribute("data-title") || "";
      btn.hidden = q && !title.toLowerCase().includes(q);
    });
  }

  function mountSidebar() {
    if (document.getElementById("frite-sidebar")) return;
    const aside = document.createElement("aside");
    aside.id = "frite-sidebar";
    aside.innerHTML = `
      <div class="frite-brand">
        <img class="frite-brand-logo" src="${LOGO}" alt="F.R.I.T.E.S." />
        <div>
          <strong>F.R.I.T.E.S</strong>
          <span>La cyber à toutes les sauces</span>
        </div>
      </div>
      <button type="button" class="frite-new-chat" id="frite-new-chat" aria-label="Nouvelle conversation">
        <span class="frite-pencil">✎</span><span>Nouvelle conversation</span><b>›</b>
      </button>
      <label class="frite-search" aria-label="Rechercher dans les discussions">
        <span>⌕</span>
        <input id="frite-search-input" type="search" placeholder="Rechercher dans les discussions..." />
      </label>
      <p class="frite-section-title">Récents</p>
      <nav class="frite-recents" id="frite-recents"></nav>
      <div class="frite-profile">
        <div class="frite-avatar">J</div>
        <div><strong>Jules Davidou</strong><span>Prototype</span></div>
      </div>
    `;
    document.body.prepend(aside);
    aside.querySelector("#frite-new-chat")?.addEventListener("click", createConversation);
    aside.querySelector("#frite-search-input")?.addEventListener("input", (event) => filterConversations(event.target.value));
  }

  function mountHeader() {
    if (document.getElementById("frite-chat-header")) return;
    const header = document.createElement("header");
    header.id = "frite-chat-header";
    header.innerHTML = `
      <button type="button" id="frite-mobile-menu" aria-label="Ouvrir le menu">☰</button>
      <div>
        <h1 id="frite-current-title"></h1>
        <p>Dialogue guidé • éveil cybersécurité</p>
      </div>
    `;
    document.body.prepend(header);
    header.querySelector("#frite-mobile-menu")?.addEventListener("click", () => document.body.classList.toggle("frite-sidebar-open"));
  }

  function mountHero() {
    if (document.getElementById("frite-empty-hero")) return;
    const hero = document.createElement("section");
    hero.id = "frite-empty-hero";
    hero.innerHTML = `
      <img class="frite-hero-logo" src="${LOGO}" alt="F.R.I.T.E.S." />
      <h2>Sur quel réflexe cyber<br />devons-nous nous concentrer&nbsp;?</h2>
      <p>Démarre une nouvelle conversation avec F.R.I.T.E.S pour apprendre la cyber à toutes les sauces.</p>
      <div class="frite-hero-actions">
        <button type="button" data-scenario="Mission phishing — livraison suspecte">Mission phishing</button>
        <button type="button" data-scenario="Créer un mot de passe solide">Mot de passe solide</button>
        <button type="button" data-scenario="Quiz réflexes cyber">Mini‑quiz</button>
      </div>
    `;
    document.body.prepend(hero);
    hero.querySelectorAll("[data-scenario]").forEach((btn) => {
      btn.addEventListener("click", () => clickConversation(btn.getAttribute("data-scenario")));
    });
  }

  function renderRecents() {
    const nav = document.getElementById("frite-recents");
    if (!nav) return;
    nav.innerHTML = state.conversations.map((item) => {
      const active = item.title === state.active?.title ? " active" : "";
      return `<button type="button" class="frite-recent-btn${active}" data-title="${escapeHtml(item.title)}" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</button>`;
    }).join("");
    nav.querySelectorAll(".frite-recent-btn").forEach((btn) => {
      btn.addEventListener("click", () => clickConversation(btn.getAttribute("data-title")));
    });
  }

  function renderShellState() {
    renderRecents();
    const title = state.active?.title || "Nouvelle conversation cyber";
    const titleEl = document.getElementById("frite-current-title");
    if (titleEl) titleEl.textContent = title;
    document.body.classList.toggle("frite-empty-state", Boolean(state.active?.empty));
    document.body.classList.toggle("frite-active-scenario", !state.active?.empty);
  }

  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function findTextNode(pattern) {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (pattern.test(node.nodeValue || "")) return node;
    }
    return null;
  }

  function closestMessageBlock(node) {
    let el = node?.parentElement;
    for (let i = 0; i < 8 && el; i += 1) {
      if (isInsideShell(el)) return null;
      const text = (el.textContent || "").trim();
      if (text.length > 20 && text.length < 1200) return el;
      el = el.parentElement;
    }
    return null;
  }

  function hideNativeWelcome() {
    const node = findTextNode(/Bienvenue sur F\.R\.I\.T\.E\.S\.|Pose-moi une question sur la cybersécurité/i);
    const block = closestMessageBlock(node);
    if (block) block.classList.add("frite-native-welcome-hidden");
  }

  function hasActualChainlitConversation() {
    const bodyText = document.body.innerText || "";
    if (/Détail technique\s*:/i.test(bodyText)) return true;
    const candidates = [...document.querySelectorAll('[data-testid*="message"], [class*="message"], [class*="Message"], article')]
      .filter((el) => !isInsideShell(el))
      .map((el) => (el.textContent || "").trim())
      .filter(Boolean)
      .filter((txt) => !/Bienvenue sur F\.R\.I\.T\.E\.S\.|Pose-moi une question sur la cybersécurité|Les LLMs peuvent se tromper/i.test(txt));
    return candidates.some((txt) => txt.length > 2);
  }

  function sync() {
    document.body.classList.add("frite-shell-mounted");
    syncThemeClass();
    hideNativeWelcome();
    document.body.classList.toggle("frite-chainlit-has-messages", hasActualChainlitConversation());
  }

  function boot() {
    mountSidebar();
    mountHeader();
    mountHero();
    renderShellState();
    sync();
    const observer = new MutationObserver(() => {
      sync();
      renderShellState();
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["class", "data-theme"] });
    window.matchMedia?.("(prefers-color-scheme: dark)")?.addEventListener?.("change", sync);
    window.addEventListener("resize", sync);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();

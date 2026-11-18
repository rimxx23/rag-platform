import { ApiError, request } from "./api.js";

const $ = (id) => document.getElementById(id);
const storageKey = "rag-platform-token";
const pageSize = 20;
const statusLabels = { processing: "Обрабатывается", ready: "Готов", failed: "Ошибка" };
let token = sessionStorage.getItem(storageKey) || "";
let registering = false;
let selected = null;
let collections = [];
let historyCount = 0;
let documentTimer;
let sessionVersion = 0;

function notice(message = "", error = false) {
  $("notice").textContent = message;
  $("notice").hidden = !message;
  $("notice").dataset.error = String(error);
}

function setToken(value) {
  token = value;
  if (value) sessionStorage.setItem(storageKey, value);
  else sessionStorage.removeItem(storageKey);
}

function activate(user) {
  sessionVersion++;
  clearTimeout(documentTimer);
  selected = null;
  collections = [];
  $("auth").hidden = Boolean(user);
  $("workspace").hidden = !user;
  $("account").hidden = !user;
  $("username").textContent = user?.username || "";
  $("collections").replaceChildren();
  $("documents").replaceChildren();
  $("history").replaceChildren();
  $("documents-panel").hidden = true;
  $("ask-form").hidden = true;
  $("older").hidden = true;
  $("chat-title").textContent = "Выберите коллекцию";
  $("empty").textContent = "Создайте коллекцию или откройте существующую.";
  $("empty").hidden = false;
  for (const id of ["collection-form", "upload-form", "ask-form"]) $(id).reset();
}

async function api(path, { authenticated = true, ...options } = {}) {
  const requestToken = authenticated ? token : "";
  try {
    return await request(path, { ...options, token: requestToken });
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;

    if (error.status === 401 && authenticated && requestToken === token) {
      setToken("");
      activate(null);
      notice("Сессия завершилась. Войдите снова.", true);
    }
    if (error.status === 429 && error.retryAfter) {
      throw new Error(`Слишком много запросов. Повторите через ${error.retryAfter} с.`);
    }
    const messages = {
      400: "Проверьте формат файла.",
      401: "Проверьте имя пользователя и пароль.",
      404: "Коллекция недоступна.",
      409: "Это имя пользователя уже занято.",
      413: "Файл слишком большой.",
      422: "Проверьте введённые данные.",
      429: "Слишком много запросов. Повторите позже.",
      503: "Сервис временно недоступен.",
    };
    throw new Error(messages[error.status] || `Ошибка запроса (${error.status}).`);
  }
}

function bindForm(id, submit) {
  const form = $(id);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    const version = sessionVersion;
    button.disabled = true;
    notice();
    try {
      await submit(new FormData(form));
    } catch (error) {
      if (version === sessionVersion) notice(error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}

function renderCollections() {
  $("collections").replaceChildren(...collections.map((collection) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary";
    button.textContent = collection.name;
    if (selected?.id === collection.id) button.setAttribute("aria-current", "true");
    button.addEventListener("click", () => selectCollection(collection));
    item.append(button);
    return item;
  }));
}

async function loadCollections(preferred) {
  const version = sessionVersion;
  const items = await api("/collections");
  if (version !== sessionVersion) return;
  collections = items;
  const collection = preferred || items[0];
  if (collection) await selectCollection(collection);
  else renderCollections();
}

function collectionPath(selection, suffix) {
  return `/collections/${encodeURIComponent(selection.id)}/${suffix}`;
}

async function refreshDocuments(selection, follow = true) {
  clearTimeout(documentTimer);
  try {
    const items = await api(collectionPath(selection, "documents"));
    if (selection !== selected) return;
    $("documents").replaceChildren(...items.map((doc) => {
      const item = document.createElement("li");
      const status = document.createElement("span");
      status.className = "document-status";
      status.dataset.status = doc.status;
      status.textContent = doc.error ? `${statusLabels[doc.status]} — ${doc.error}` : statusLabels[doc.status];
      item.append(doc.filename, status);
      return item;
    }));
    if (follow && items.some((doc) => doc.status === "processing")) {
      documentTimer = setTimeout(() => refreshDocuments(selection), 1800);
    }
  } catch (error) {
    if (selection === selected) notice(error.message, true);
  }
}

function messageItem(message) {
  const item = document.createElement("li");
  for (const type of ["question", "answer"]) {
    const bubble = document.createElement("p");
    bubble.className = `bubble ${type}`;
    bubble.textContent = message[type];
    item.append(bubble);
  }
  for (const source of message.sources) {
    const details = document.createElement("details");
    const title = document.createElement("summary");
    const excerpt = document.createElement("p");
    const page = source.page === null ? "" : ` · стр. ${source.page}`;
    title.textContent = `[${source.number}] ${source.filename}${page}`;
    excerpt.textContent = source.content;
    details.append(title, excerpt);
    item.append(details);
  }
  return item;
}

async function loadHistory(selection, older = false) {
  const offset = older ? historyCount : 0;
  const items = await api(collectionPath(selection, `history?limit=${pageSize + 1}&offset=${offset}`));
  if (selection !== selected || (older && offset !== historyCount)) return;
  const page = items.slice(0, pageSize);
  const nodes = page.reverse().map(messageItem);
  if (older) $("history").prepend(...nodes);
  else $("history").replaceChildren(...nodes);
  historyCount = offset + page.length;
  $("older").hidden = items.length <= pageSize;
  $("empty").textContent = "Загрузите документ и задайте первый вопрос.";
  $("empty").hidden = historyCount > 0;
}

async function selectCollection(collection) {
  const selection = { ...collection };
  selected = selection;
  historyCount = 0;
  notice();
  renderCollections();
  $("chat-title").textContent = collection.name;
  $("documents-panel").hidden = false;
  $("ask-form").hidden = false;
  $("older").hidden = true;
  $("empty").hidden = true;
  $("documents").replaceChildren();
  $("history").replaceChildren();
  $("upload-form").reset();
  $("ask-form").reset();
  try {
    await Promise.all([refreshDocuments(selection), loadHistory(selection)]);
  } catch (error) {
    if (selected === selection) notice(error.message, true);
  }
}

$("auth-toggle").addEventListener("click", () => {
  registering = !registering;
  $("auth-title").textContent = registering ? "Регистрация" : "Вход";
  $("auth-submit").textContent = registering ? "Зарегистрироваться" : "Войти";
  $("auth-toggle").textContent = registering ? "Уже есть аккаунт" : "Создать аккаунт";
  $("password").autocomplete = registering ? "new-password" : "current-password";
  notice();
});

bindForm("auth-form", async (data) => {
  const credentials = Object.fromEntries(data);
  if (registering) {
    await api("/auth/register", { method: "POST", json: credentials, authenticated: false });
  }
  const result = await api("/auth/login", {
    method: "POST", body: new URLSearchParams(data), authenticated: false,
  });
  setToken(result.access_token);
  $("auth-form").reset();
  await restoreSession();
});

$("logout").addEventListener("click", () => {
  setToken("");
  activate(null);
  if (registering) $("auth-toggle").click();
  notice();
});

bindForm("collection-form", async (data) => {
  const version = sessionVersion;
  const name = data.get("name").trim();
  if (!name) throw new Error("Введите название коллекции.");
  const collection = await api("/collections", { method: "POST", json: { name } });
  if (version !== sessionVersion) return;
  $("collection-form").reset();
  await loadCollections(collection);
});

bindForm("upload-form", async (data) => {
  const selection = selected;
  if (!selection) return;
  await api(collectionPath(selection, "documents"), { method: "POST", body: data });
  if (selection !== selected) return;
  $("upload-form").reset();
  await refreshDocuments(selection);
});

bindForm("ask-form", async (data) => {
  const selection = selected;
  if (!selection) return;
  const question = data.get("question").trim();
  if (!question) throw new Error("Введите вопрос.");
  notice("Ищу ответ в документах…");
  await api(collectionPath(selection, "ask"), { method: "POST", json: { question } });
  if (selection !== selected) return;
  $("ask-form").reset();
  notice();
  await loadHistory(selection);
});

$("older").addEventListener("click", async () => {
  const selection = selected;
  if (!selection) return;
  $("older").disabled = true;
  try {
    await loadHistory(selection, true);
  } catch (error) {
    if (selection === selected) notice(error.message, true);
  } finally {
    $("older").disabled = false;
  }
});

async function restoreSession() {
  try {
    const user = await api("/auth/me");
    activate(user);
    await loadCollections();
  } catch (error) {
    if (token) notice(error.message, true);
  }
}

if (token) restoreSession();

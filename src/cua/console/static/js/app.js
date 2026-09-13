// Console wiring: composer, recent runs, and which run is on screen (kept in the URL hash).

import { followRun, getRun, getStatus, listRuns, startRun } from "./api.js";
import { createRunView, h, renderUserMessage } from "./render.js";

const $ = (id) => document.getElementById(id);
const shell = $("shell");
const thread = $("thread");
const welcome = $("welcome");
const conversation = $("conversation");
const composer = $("composer");
const input = $("member-id");
const send = $("send");
const hint = $("composer-hint");
const defaultHint = hint.textContent;

let stopFollowing = () => {};
let busy = false;
let ready = true;
let stickToBottom = true; // follow new output unless the operator has scrolled up to read

function setHint(text, tone) {
  hint.textContent = text ?? defaultHint;
  if (tone) hint.dataset.tone = tone;
  else delete hint.dataset.tone;
}

function setBusy(value) {
  busy = value;
  send.disabled = busy || !ready;
  input.setAttribute("aria-busy", String(busy));
}

function scrollToEnd() {
  if (stickToBottom) thread.scrollTo({ top: thread.scrollHeight });
}

thread.addEventListener("scroll", () => {
  stickToBottom = thread.scrollHeight - thread.scrollTop - thread.clientHeight < 120;
});
thread.addEventListener("load", scrollToEnd, true); // screenshots change the height once loaded

function relativeTime(iso) {
  const minutes = Math.round((Date.now() - new Date(iso)) / 60000);
  if (minutes < 1) return "now";
  if (minutes < 60) return `${minutes}m`;
  return `${Math.round(minutes / 60)}h`;
}

async function refreshRunList() {
  const runs = await listRuns().catch(() => []);
  const current = location.hash.slice(1);
  $("run-list").replaceChildren(...runs.map((run) =>
    h("li", {}, h("button", {
      class: "run-link", type: "button", "aria-current": String(run.id === current),
      onclick: () => { location.hash = run.id; closeDrawer(); },
    },
      h("span", { class: "status-dot", "data-status": run.status, "aria-label": run.status }),
      h("span", { text: `Member ${run.member_id}` }),
      h("time", { dateTime: run.created_at, text: relativeTime(run.created_at) })))));
  $("run-list-empty").hidden = runs.length > 0;
}

function showWelcome() {
  stopFollowing();
  conversation.replaceChildren();
  welcome.hidden = false;
  setBusy(false);
  refreshRunList();
  input.focus();
}

async function showRun(runId) {
  stopFollowing();
  const run = await getRun(runId).catch(() => null);
  if (!run) {
    history.replaceState(null, "", location.pathname);
    showWelcome();
    return;
  }
  welcome.hidden = true;
  stickToBottom = true;
  const view = createRunView(run.member_id, {
    onSettled: () => { setBusy(false); refreshRunList(); },
  });
  conversation.replaceChildren(renderUserMessage(run.member_id), view.element);
  setBusy(run.status === "running");
  refreshRunList();
  stopFollowing = followRun(run.id, (event) => {
    view.handle(event);
    scrollToEnd();
  });
}

async function submitLookup(memberId) {
  const value = memberId.trim();
  if (!/^\d{1,10}$/.test(value)) {
    setHint("Member numbers are digits only, like 12345.", "error");
    input.focus();
    return;
  }
  setHint();
  setBusy(true);
  try {
    const run = await startRun(value);
    input.value = "";
    location.hash = run.id; // triggers showRun via hashchange
  } catch (error) {
    setBusy(false);
    setHint(error.message, "error");
  }
}

function openDrawer() {
  shell.dataset.drawer = "open";
  $("scrim").hidden = false;
  $("menu-button").setAttribute("aria-expanded", "true");
}

function closeDrawer() {
  delete shell.dataset.drawer;
  $("scrim").hidden = true;
  $("menu-button").setAttribute("aria-expanded", "false");
}

composer.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!busy) submitLookup(input.value);
});
input.addEventListener("input", () => setHint());
document.querySelectorAll(".suggestion").forEach((button) =>
  button.addEventListener("click", () => submitLookup(button.dataset.member)));
$("new-run").addEventListener("click", () => {
  closeDrawer();
  if (location.hash) location.hash = "";
  showWelcome();
});
$("menu-button").addEventListener("click", openDrawer);
$("scrim").addEventListener("click", closeDrawer);
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeDrawer(); });
window.addEventListener("hashchange", () => (location.hash ? showRun(location.hash.slice(1)) : showWelcome()));

getStatus().then((status) => {
  ready = status.ready;
  if (!ready) setHint("Runs are disabled: set CUA_USERNAME and CUA_PASSWORD, then restart.", "error");
  setBusy(busy);
}).catch(() => setHint("Can't reach the console server.", "error"));

if (location.hash) showRun(location.hash.slice(1));
else showWelcome();

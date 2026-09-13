// Builds the DOM for a run. All page-derived text goes through textContent, never innerHTML.

const ICONS = {
  check: "M5 10.5l3.2 3L15 7",
  cross: "M6 6l8 8M14 6l-8 8",
};

export function h(tag, props = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") element.className = value;
    else if (key === "text") element.textContent = value;
    else if (key.startsWith("data-") || key.startsWith("aria-") || key === "role") element.setAttribute(key, value);
    else element[key] = value;
  }
  element.append(...children.filter(Boolean));
  return element;
}

function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 20 20");
  svg.setAttribute("aria-hidden", "true");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", ICONS[name]);
  svg.append(path);
  return svg;
}

const OUTCOMES = {
  member_found: (id, steps) => ({
    title: `Member ${id}'s record is open.`,
    body: `Signed on, searched, and reached the member detail page in ${steps} steps.`,
  }),
  member_not_found: (id) => ({
    title: `There's no member with number ${id}.`,
    body: "The app answered “No member found.” That's a business outcome, not an automation failure.",
  }),
  unexpected_page: () => ({
    title: "The lookup ended on a page it didn't expect.",
    body: "Every step ran, but the final page is neither a member record nor a “not found” message.",
  }),
};

export function renderUserMessage(memberId) {
  return h("div", { class: "message-user", text: `Look up member ${memberId}` });
}

/** Returns { element, handle(event) } for one run's agent response. */
export function createRunView(memberId, { onSettled } = {}) {
  const status = h("div", { class: "agent-status", "data-state": "running", role: "status" },
    h("span", { class: "shimmer", text: "Starting a browser…" }));
  const url = h("span", { class: "live-url" });
  const image = h("img", { alt: "" });
  const imageLink = h("a", { target: "_blank", rel: "noopener", title: "Open full-size screenshot" }, image);
  const liveView = h("figure", { class: "live-view", hidden: true },
    h("div", { class: "live-chrome", "aria-hidden": "true" },
      h("span", { class: "live-dots" }, h("i"), h("i"), h("i")), url),
    imageLink,
    h("figcaption", { text: "Latest screen the agent saw. Select it to open full size." }));
  const steps = h("ol", { class: "steps", "aria-label": "Steps" });
  const body = h("div", { class: "agent-body" }, status, steps, liveView);
  const element = h("div", { class: "message-agent" },
    h("span", { class: "brand-mark agent-mark", "aria-hidden": "true" }), body);

  const stepItems = new Map();
  let completedSteps = 0;
  let lastTitle = null;

  function setStatus(text, state) {
    status.dataset.state = state;
    status.replaceChildren(h("span", { class: state === "running" ? "shimmer" : "", text }));
  }

  function settle() {
    onSettled?.();
  }

  const handlers = {
    "run.started": () => setStatus("Signing on to the member system…", "running"),

    "step.started": (event) => {
      const item = h("li", { class: "step", "data-state": "running" },
        h("span", { class: "step-icon" }),
        h("span", { class: "step-text", text: event.text }));
      stepItems.set(event.index, item);
      steps.append(item);
      setStatus(`${event.text}…`, "running");
    },

    "step.completed": (event) => {
      const item = stepItems.get(event.index);
      item.dataset.state = "done";
      item.querySelector(".step-icon").replaceChildren(icon("check"));
      if (event.title !== lastTitle) {
        const page = event.title.split(" - ")[0]; // drop the app-wide title suffix
        item.querySelector(".step-text").append(h("span", { class: "step-meta", text: `→ ${page}` }));
        lastTitle = event.title;
      }
      completedSteps += 1;
      url.textContent = event.url;
      image.src = event.screenshot;
      image.alt = `Screenshot after step ${event.index + 1}: ${event.title}`;
      imageLink.href = event.screenshot;
      liveView.hidden = false;
    },

    "run.completed": (event) => {
      const outcome = (OUTCOMES[event.outcome] ?? OUTCOMES.unexpected_page)(memberId, completedSteps);
      setStatus(event.outcome === "member_found" ? "Done" : "Finished", "done");
      body.append(
        h("section", { class: "result", "aria-live": "polite" },
          h("h3", { text: outcome.title }), h("p", { text: outcome.body })),
        h("details", { class: "disclosure" },
          h("summary", { text: "What the agent sees — accessibility snapshot" }),
          h("pre", { text: event.snapshot })));
      settle();
    },

    "run.failed": (event) => {
      const item = stepItems.get(event.index);
      if (item) {
        item.dataset.state = "failed";
        item.querySelector(".step-icon").replaceChildren(icon("cross"));
      }
      setStatus("Stopped", "failed");
      const where = item ? `Step ${event.index + 1} couldn't be completed.` : "The run stopped early.";
      body.append(h("section", { class: "result", "data-tone": "error", "aria-live": "assertive" },
        h("h3", { text: "The lookup couldn't finish." }),
        h("p", { text: `${where} Nothing was changed in the app.` }),
        h("div", { class: "error-detail", text: event.error })));
      settle();
    },

    "connection.lost": () => {
      setStatus("Lost connection to the console. Reload to see the latest.", "failed");
      settle();
    },
  };

  return { element, handle: (event) => handlers[event.type]?.(event) };
}

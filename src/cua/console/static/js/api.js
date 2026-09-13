// Thin client for the console API.

const TERMINAL = new Set(["run.completed", "run.failed"]);

async function readJson(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === "string" ? body.detail : "Enter a member number (digits only).";
    throw new Error(detail);
  }
  return body;
}

export async function getStatus() {
  return readJson(await fetch("/api/status"));
}

export async function listRuns() {
  return readJson(await fetch("/api/runs"));
}

export async function getRun(runId) {
  return readJson(await fetch(`/api/runs/${encodeURIComponent(runId)}`));
}

export async function startRun(memberId) {
  const response = await fetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ member_id: memberId }),
  });
  return readJson(response);
}

/** Replays a run's events from the start, then follows it live. Returns a function to stop. */
export function followRun(runId, onEvent) {
  const source = new EventSource(`/api/runs/${encodeURIComponent(runId)}/events`);
  let finished = false;
  source.onmessage = (message) => {
    const event = JSON.parse(message.data);
    if (TERMINAL.has(event.type)) {
      finished = true;
      source.close();
    }
    onEvent(event);
  };
  source.onerror = () => {
    source.close();
    if (!finished) onEvent({ type: "connection.lost" });
  };
  return () => source.close();
}

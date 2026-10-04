// The browser only talks to the web container. nginx forwards /api/ to the API container.
const $ = (id) => document.getElementById(id);

async function loadInfo() {
  try {
    const r = await fetch("/api/info");
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const i = await r.json();
    $("info").innerHTML =
      `<b>${i.greeting}</b><br>environment: <code>${i.app_env}</code> · ` +
      `answered by API container <code>${i.container_hostname}</code> · database host <code>${i.database_host}</code>`;
  } catch (e) {
    $("info").className = "card error";
    $("info").textContent = `The web container could not reach the API (${e.message}). Check: docker logs, docker network inspect.`;
  }
}

async function loadMessages() {
  const r = await fetch("/api/messages");
  if (!r.ok) {
    $("messages").innerHTML = `<li class="error">Could not load messages (HTTP ${r.status})</li>`;
    return;
  }
  const list = await r.json();
  $("messages").innerHTML = list.length ? "" : "<li>No messages yet</li>";
  for (const m of list) {
    const li = document.createElement("li");
    li.textContent = m.text + " ";
    const t = document.createElement("time");
    t.textContent = new Date(m.created_at).toLocaleString();
    li.appendChild(t);
    $("messages").appendChild(li);
  }
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  await fetch("/api/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: $("text").value }),
  });
  $("text").value = "";
  loadMessages();
});

loadInfo();
loadMessages();

(function () {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const log = document.getElementById("log");

  function add(cls, text) {
    const div = document.createElement("div");
    div.className = "msg " + cls;
    div.textContent = text;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
    return div;
  }

  function addCheckout(co) {
    const box = document.createElement("div");
    box.className = "msg checkout";
    const title = document.createElement("strong");
    title.textContent = "Your cart (priced by the shop)";
    box.appendChild(title);
    const ul = document.createElement("ul");
    co.lines.forEach(function (li) {
      const item = document.createElement("li");
      item.textContent = li.qty + " x " + li.name;
      ul.appendChild(item);
    });
    box.appendChild(ul);
    const total = document.createElement("p");
    total.textContent = "Total: $" + co.total + " " + co.currency;
    box.appendChild(total);
    const a = document.createElement("a");
    a.className = "button paypal";
    a.href = co.approve_url;
    a.textContent = "Review and pay with PayPal (Sandbox)";
    box.appendChild(a);
    log.appendChild(box);
    log.scrollTop = log.scrollHeight;
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    add("me", text);
    input.value = "";
    const button = form.querySelector("button");
    button.disabled = true;
    const waiting = add("bot pending", "Thinking...");
    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await r.json();
      waiting.remove();
      if (!r.ok) { add("bot error", "Sorry, something went wrong."); return; }
      if (data.notice) add("notice", data.notice);
      add("bot", data.text || "(no reply)");
      if (data.checkout) addCheckout(data.checkout);
    } catch (err) {
      waiting.remove();
      add("bot error", "Couldn't reach the shop. Check your connection and try again.");
    } finally {
      button.disabled = false;
      input.focus();
    }
  });
})();

export const dynamic = "force-dynamic";

export async function GET() {
  const script = `
(() => {
  const currentScript = document.currentScript;
  if (!currentScript) return;

  const origin = new URL(currentScript.src).origin;
  const company = currentScript.dataset.company || "startup-demo-001";
  const title = currentScript.dataset.title || "Website Assistant";
  const subtitle = currentScript.dataset.subtitle || "Ask us anything about our services.";
  const apiKey = currentScript.dataset.apiKey || "";
  const buttonLabel = currentScript.dataset.buttonLabel || "Chat with us";

  const wrapper = document.createElement("div");
  wrapper.style.position = "fixed";
  wrapper.style.right = "24px";
  wrapper.style.bottom = "24px";
  wrapper.style.zIndex = "2147483000";
  wrapper.style.fontFamily = "system-ui, sans-serif";

  const button = document.createElement("button");
  button.textContent = buttonLabel;
  button.style.border = "0";
  button.style.borderRadius = "999px";
  button.style.padding = "14px 18px";
  button.style.background = "linear-gradient(135deg, #58a6ff, #2f7df6)";
  button.style.color = "#fff";
  button.style.fontSize = "14px";
  button.style.fontWeight = "600";
  button.style.cursor = "pointer";
  button.style.boxShadow = "0 18px 45px rgba(47,125,246,0.32)";

  const frame = document.createElement("iframe");
  const frameUrl = new URL(origin + "/embed");
  frameUrl.searchParams.set("company", company);
  frameUrl.searchParams.set("title", title);
  frameUrl.searchParams.set("subtitle", subtitle);
  if (apiKey) {
    frameUrl.searchParams.set("apiKey", apiKey);
  }

  frame.src = frameUrl.toString();
  frame.title = title;
  frame.style.width = "380px";
  frame.style.maxWidth = "calc(100vw - 32px)";
  frame.style.height = "640px";
  frame.style.maxHeight = "calc(100vh - 96px)";
  frame.style.border = "0";
  frame.style.borderRadius = "28px";
  frame.style.boxShadow = "0 28px 80px rgba(2, 9, 22, 0.4)";
  frame.style.overflow = "hidden";
  frame.style.display = "none";
  frame.style.background = "#07111f";

  button.addEventListener("click", () => {
    const isOpen = frame.style.display === "block";
    frame.style.display = isOpen ? "none" : "block";
    button.textContent = isOpen ? buttonLabel : "Close chat";
  });

  wrapper.appendChild(frame);
  wrapper.appendChild(button);
  document.body.appendChild(wrapper);
})();
`;

  return new Response(script, {
    headers: {
      "Content-Type": "application/javascript; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "Content-Security-Policy": `default-src 'self'; script-src 'self' 'unsafe-inline'; frame-src 'self'; style-src 'unsafe-inline';`,
    },
  });
}

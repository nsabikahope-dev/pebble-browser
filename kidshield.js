/**
 * KidShield — Standalone content scanner for Pebble browser.
 * Injected by Python after each page load.
 * Settings pre-loaded via: window.__pebbleKidshield = {...}
 */
(async function () {
  "use strict";

  const settings = window.__pebbleKidshield;
  if (!settings || !settings.enabled) return;

  // Prevent double-scan within the same page context (SPA navigation guard)
  if (window.__kidshieldActive) return;
  window.__kidshieldActive = true;

  // ─── Shadow DOM ──────────────────────────────────────────────────────────────

  let shadowRoot = null;

  function ensureShadowRoot() {
    if (shadowRoot) return shadowRoot;
    let host = document.getElementById("kidshield-host");
    if (!host) {
      host = document.createElement("div");
      host.id = "kidshield-host";
      host.style.cssText = "all:unset;position:fixed;z-index:2147483647;top:0;left:0;width:0;height:0;";
      document.documentElement.appendChild(host);
    }
    shadowRoot = host.attachShadow({ mode: "closed" });
    return shadowRoot;
  }

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
  }

  function clearUI() {
    if (shadowRoot) {
      while (shadowRoot.firstChild) shadowRoot.removeChild(shadowRoot.firstChild);
    }
    if (window.__ksBlurStyle) {
      window.__ksBlurStyle.remove();
      window.__ksBlurStyle = null;
    }
  }

  // Python can call this to clear the UI (e.g. on navigation)
  window.__kidshieldClear = clearUI;

  // ─── UI: Overlay ─────────────────────────────────────────────────────────────

  function applyOverlay(findings) {
    clearUI();
    const sr = ensureShadowRoot();

    const style = document.createElement("style");
    style.textContent = `
      .ks-overlay {
        position:fixed;inset:0;z-index:9999;background:rgba(15,15,15,0.92);
        display:flex;align-items:center;justify-content:center;
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
      }
      .ks-card {
        background:#fff;border-radius:16px;padding:32px 28px;
        max-width:420px;width:calc(100vw - 48px);
        box-shadow:0 24px 80px rgba(0,0,0,0.5);text-align:center;
      }
      .ks-shield { font-size:52px;margin-bottom:12px;line-height:1; }
      .ks-title  { font-size:22px;font-weight:700;color:#111;margin-bottom:8px; }
      .ks-subtitle { font-size:14px;color:#555;margin-bottom:20px;line-height:1.5; }
      .ks-findings {
        background:#fef2f2;border:1px solid #fca5a5;border-radius:10px;
        padding:12px 16px;margin-bottom:20px;text-align:left;
      }
      .ks-findings-title { font-size:12px;font-weight:600;color:#991b1b;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px; }
      .ks-findings-list { list-style:none;padding:0;margin:0; }
      .ks-findings-list li { font-size:13px;color:#7f1d1d;padding:2px 0; }
      .ks-findings-list li::before { content:"⚠ "; }
      .ks-btn-group { display:flex;gap:10px;justify-content:center;flex-wrap:wrap; }
      .ks-btn-back {
        background:#dc2626;color:#fff;border:none;border-radius:8px;
        padding:10px 22px;font-size:14px;font-weight:600;cursor:pointer;
      }
      .ks-btn-back:hover { background:#b91c1c; }
      .ks-btn-dismiss {
        background:transparent;color:#6b7280;border:1px solid #d1d5db;
        border-radius:8px;padding:10px 22px;font-size:14px;cursor:pointer;
      }
      .ks-btn-dismiss:hover { background:#f9fafb; }
      .ks-branding { margin-top:16px;font-size:11px;color:#9ca3af; }
    `;
    sr.appendChild(style);

    const findingsHtml = findings.length > 0
      ? `<div class="ks-findings">
           <div class="ks-findings-title">Issues detected</div>
           <ul class="ks-findings-list">
             ${findings.map(f => `<li>${escapeHtml(f)}</li>`).join("")}
           </ul>
         </div>`
      : "";

    const overlay = document.createElement("div");
    overlay.className = "ks-overlay";
    overlay.setAttribute("role", "alertdialog");
    overlay.innerHTML = `
      <div class="ks-card">
        <div class="ks-shield">🛡️</div>
        <div class="ks-title">Content Blocked</div>
        <p class="ks-subtitle">KidShield detected content that may not be appropriate for children on this page.</p>
        ${findingsHtml}
        <div class="ks-btn-group">
          <button class="ks-btn-back">← Go Back</button>
          <button class="ks-btn-dismiss">Show Anyway</button>
        </div>
        <div class="ks-branding">Protected by KidShield · Pebble</div>
      </div>
    `;

    overlay.querySelector(".ks-btn-back").addEventListener("click", () => history.back());
    overlay.querySelector(".ks-btn-dismiss").addEventListener("click", clearUI);
    sr.appendChild(overlay);
  }

  // ─── UI: Blur ────────────────────────────────────────────────────────────────

  function applyBlur(findings) {
    clearUI();
    ensureShadowRoot();
    const style = document.createElement("style");
    style.textContent = "body > *:not(#kidshield-host) { filter:blur(8px) !important; pointer-events:none !important; }";
    document.head.appendChild(style);
    window.__ksBlurStyle = style;
    _banner(findings, false);
  }

  // ─── UI: Banner ──────────────────────────────────────────────────────────────

  function applyBanner(findings) { _banner(findings, true); }

  function _banner(findings, closeable) {
    const sr = ensureShadowRoot();
    const style = document.createElement("style");
    style.textContent = `
      .ks-banner {
        position:fixed;top:0;left:0;right:0;z-index:9999;
        background:#dc2626;color:#fff;
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
        font-size:14px;font-weight:500;
        display:flex;align-items:center;gap:10px;padding:10px 16px;
        box-shadow:0 2px 12px rgba(0,0,0,0.3);
      }
      .ks-banner-text { flex:1; }
      .ks-banner-close {
        background:rgba(255,255,255,0.2);border:none;color:#fff;
        border-radius:4px;padding:4px 10px;font-size:13px;cursor:pointer;flex-shrink:0;
      }
      .ks-banner-close:hover { background:rgba(255,255,255,0.35); }
    `;
    sr.appendChild(style);

    const summary = findings.length > 0
      ? findings.slice(0, 2).join(" • ") + (findings.length > 2 ? ` +${findings.length - 2} more` : "")
      : "Potentially harmful content detected";

    const banner = document.createElement("div");
    banner.className = "ks-banner";
    banner.setAttribute("role", "alert");
    banner.innerHTML = `
      <span>🛡️</span>
      <span class="ks-banner-text">KidShield: ${escapeHtml(summary)}</span>
      <button class="ks-banner-close">${closeable ? "Dismiss" : "Show Unblurred"}</button>
    `;
    if (closeable) {
      banner.querySelector(".ks-banner-close").addEventListener("click", clearUI);
    } else {
      banner.querySelector(".ks-banner-close").addEventListener("click", () => {
        if (window.__ksBlurStyle) { window.__ksBlurStyle.remove(); window.__ksBlurStyle = null; }
        clearUI();
      });
    }
    sr.appendChild(banner);
  }

  function applyResponse(mode, findings) {
    if (mode === "blur")   return applyBlur(findings);
    if (mode === "banner") return applyBanner(findings);
    applyOverlay(findings);
  }

  // ─── Content extraction ──────────────────────────────────────────────────────

  function extractContent() {
    const url      = window.location.href;
    const hostname = window.location.hostname;

    // YouTube
    if (hostname.includes("youtube.com") && window.location.pathname.startsWith("/watch")) {
      const titleEl   = document.querySelector("h1.ytd-watch-metadata yt-formatted-string, #title h1, h1#title");
      const channelEl = document.querySelector("ytd-channel-name a, #channel-name a");
      const descEl    = document.querySelector("ytd-text-inline-expander #snippet-text yt-formatted-string, #description-text");
      const title    = titleEl?.textContent?.trim()   || document.title;
      const channel  = channelEl?.textContent?.trim() || "";
      const descText = descEl?.textContent?.trim()    || "";
      const captions = Array.from(document.querySelectorAll(".ytp-caption-segment"))
                            .map(el => el.textContent).join(" ").slice(0, 800);
      return {
        url, title, type: "video",
        description: [channel && `Channel: ${channel}`, descText].filter(Boolean).join(" | ").slice(0, 600),
        text: [
          `Title: ${title}`,
          channel  && `Channel: ${channel}`,
          descText && `Description: ${descText}`,
          captions && `Captions: ${captions}`
        ].filter(Boolean).join("\n").slice(0, 2500)
      };
    }

    // Twitter / X
    if (hostname.includes("twitter.com") || hostname.includes("x.com")) {
      const tweets = Array.from(document.querySelectorAll('[data-testid="tweetText"]'))
        .map(el => el.textContent.trim()).slice(0, 10).join("\n");
      return { url, title: document.title, type: "social", text: tweets || document.body.innerText.slice(0, 2500) };
    }

    // General page
    const metaDesc = document.querySelector('meta[name="description"]')?.content || "";
    const source   = document.querySelector("main, article, [role=main], #content, .content, .post-content, .entry-content") || document.body;
    const SKIP     = new Set(["SCRIPT","STYLE","NAV","FOOTER","ASIDE","HEADER","NOSCRIPT","IFRAME","SELECT","BUTTON"]);
    const parts    = [];

    function walk(node) {
      if (SKIP.has(node.nodeName)) return;
      if (node.nodeType === Node.TEXT_NODE) {
        const t = node.textContent.trim();
        if (t.length > 20) parts.push(t);
      } else {
        node.childNodes.forEach(walk);
      }
    }
    walk(source);

    return {
      url,
      title:       document.title,
      type:        "page",
      description: metaDesc.slice(0, 300),
      text:        parts.join(" ").replace(/\s+/g, " ").slice(0, 2500)
    };
  }

  // ─── Keyword scan ────────────────────────────────────────────────────────────

  function escapeRegex(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

  function keywordScan(text, keywords) {
    if (!keywords?.length) return [];
    const lower = text.toLowerCase();
    const found = [];
    for (const kw of keywords) {
      if (new RegExp(`\\b${escapeRegex(kw.trim().toLowerCase())}\\b`).test(lower))
        found.push(`Keyword match: "${kw}"`);
    }
    return found;
  }

  const TITLE_SEXUAL_TERMS = [
    "sex","sexy","sexual","nude","nudity","naked","porn","porno","pornography",
    "xxx","adult content","adult video","explicit","nsfw","erotic","erotica","18+",
    "onlyfans","stripper","strip club","masturbat","orgasm","penis","vagina",
    "breast","boob","boobs","nudes","leaked nudes","sex tape"
  ];

  function titleKeywordScan(content) {
    const shortText = [content.title || "", content.description || ""].join(" ").toLowerCase();
    for (const term of TITLE_SEXUAL_TERMS) {
      const hit = term.includes(" ")
        ? shortText.includes(term)
        : new RegExp(`\\b${escapeRegex(term)}\\b`).test(shortText);
      if (hit) return [`Sexual Content: "${term}" found in title or caption`];
    }
    return [];
  }

  // ─── Claude API call ─────────────────────────────────────────────────────────

  const CATEGORY_LABELS = {
    violence:    "Violence & Gore",
    sexual:      "Sexual Content",
    profanity:   "Profanity & Strong Language",
    drugs:       "Drug & Alcohol Use",
    gambling:    "Gambling",
    horror:      "Horror & Frightening Content",
    selfHarm:    "Self-Harm & Suicide",
    hateSpeech:  "Hate Speech & Discrimination",
    adultThemes: "Adult Themes",
    weapons:     "Weapons & Explosives"
  };

  async function callClaude(content) {
    const enabledCategories = Object.entries(settings.categories || {})
      .filter(([, enabled]) => enabled)
      .map(([key]) => CATEGORY_LABELS[key] || key);

    if (!enabledCategories.length) return { safe: true, findings: [] };

    const systemPrompt = `You are a content safety classifier for KidShield, protecting children from harmful online content.

RULES:
1. HATE SPEECH disguised as education MUST be flagged: any content claiming a racial or ethnic group is less intelligent, less attractive, or genetically inferior — even if framed as "study", "research", "IQ", "science", or "statistics". This includes content targeting African, Black, or any other group. Flag it.
2. SEXUAL CONTENT: any page or video where the title, caption, or heading contains sexual language must be flagged, even if the body seems unrelated.
3. Legitimate civil rights history and anti-racism education is NOT hate speech.
4. Respond ONLY with a valid JSON object — no prose, no markdown, no code fences.

Categories to check:
${enabledCategories.map(c => `- ${c}`).join("\n")}

Format: {"safe": true/false, "findings": ["Category: specific reason"], "confidence": 0.0-1.0}`;

    const sample = [content.description, content.text].filter(Boolean).join("\n\n").slice(0, 3000);

    const resp = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type":  "application/json",
        "x-api-key":     settings.apiKey,
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true"
      },
      body: JSON.stringify({
        model:      "claude-haiku-4-5-20251001",
        max_tokens: 300,
        system:     systemPrompt,
        messages:   [{
          role:    "user",
          content: `Analyze this ${content.type} for children's safety.\nURL: ${content.url}\nTitle: ${content.title}\n\n---\n${sample}\n---\n\nReturn only the JSON.`
        }]
      })
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.error?.message || `API error ${resp.status}`);
    }

    const data = await resp.json();
    const raw  = data.content[0].text.trim()
      .replace(/^```json?\s*/i, "").replace(/\s*```$/, "").trim();
    return JSON.parse(raw);
  }

  // ─── Main scan ───────────────────────────────────────────────────────────────

  try {
    const content = extractContent();
    if (!content?.text && !content?.title) return;

    // 1. Title keyword scan (always runs if sexual category is on)
    const titleFindings = settings.categories?.sexual ? titleKeywordScan(content) : [];

    // 2. Custom keyword scan
    const kwFindings = keywordScan(content.text || "", settings.customKeywords || []);

    const allKeywordFindings = [...titleFindings, ...kwFindings];
    let safe = allKeywordFindings.length === 0;
    const findings = new Set(allKeywordFindings);

    // 3. AI scan if API key is set
    if (settings.apiKey) {
      try {
        const aiResult = await callClaude(content);
        if (!aiResult.safe) safe = false;
        (aiResult.findings || []).forEach(f => findings.add(f));
      } catch (e) {
        console.warn("[KidShield] API error:", e.message);
        // Fall back to keyword result only
      }
    }

    // 4. Apply response
    if (!safe) {
      applyResponse(settings.responseMode || "overlay", [...findings]);
    }
  } catch (e) {
    console.warn("[KidShield] Scan error:", e);
  }

})();

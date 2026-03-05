import { useState, useRef, useCallback } from "react";

const SYSTEM_PROMPT = `You are an expert QA engineer and BDD specialist. Your job is to analyze provided context (business requirements, user stories, API specs, or feature descriptions) and generate comprehensive Cucumber test scenarios using Gherkin syntax.

Follow these rules:
1. Generate Feature files with clear Feature descriptions
2. Write Scenario and Scenario Outline blocks with Given/When/Then/And/But steps
3. Use Background blocks when setup steps repeat across scenarios
4. Use Scenario Outline + Examples tables for data-driven tests
5. Cover: happy paths, edge cases, negative/error cases, boundary conditions
6. Use @tags to organize scenarios (e.g., @smoke, @regression, @negative, @boundary)
7. Keep steps atomic and reusable
8. Return ONLY valid Gherkin .feature file content, no extra explanation

Format your response as a single valid .feature file. Start with the Feature: keyword.`;

// ─── GitHub helpers ──────────────────────────────────────────────────────────

function parseRepoUrl(input) {
  // Accept "owner/repo", full https URL, or git URL
  const clean = input.trim().replace(/\.git$/, "");
  const m = clean.match(/github\.com[/:]([^/]+)\/([^/]+)/);
  if (m) return { owner: m[1], repo: m[2] };
  const parts = clean.split("/").filter(Boolean);
  if (parts.length >= 2) return { owner: parts[parts.length - 2], repo: parts[parts.length - 1] };
  return null;
}

async function ghFetch(path, token) {
  const res = await fetch(`https://api.github.com${path}`, {
    headers: {
      Accept: "application/vnd.github+json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    if (res.status === 404) {
      throw new Error(
        "Repository not found. If this is a private repo, enter a Personal Access Token with \"repo\" read scope and try again."
      );
    }
    if (res.status === 401) {
      throw new Error("Authentication failed. Check that your Personal Access Token is valid and has not expired.");
    }
    if (res.status === 403) {
      throw new Error("Access forbidden. Your token may lack the required \"repo\" scope, or you have hit the GitHub API rate limit.");
    }
    throw new Error(body.message || `GitHub API error ${res.status}`);
  }
  return res.json();
}

// Recursively fetch the full file tree (up to GitHub's 100k node limit)
async function fetchTree(owner, repo, branch, token) {
  const data = await ghFetch(
    `/repos/${owner}/${repo}/git/trees/${branch}?recursive=1`,
    token
  );
  return data.tree || [];
}

async function fetchFileContent(owner, repo, path, token) {
  const data = await ghFetch(`/repos/${owner}/${repo}/contents/${path}`, token);
  if (data.encoding === "base64") {
    return atob(data.content.replace(/\n/g, ""));
  }
  if (data.download_url) {
    const r = await fetch(data.download_url);
    return r.text();
  }
  return "";
}

// ─── File-tree node component ─────────────────────────────────────────────────

const CODE_EXTS = new Set([
  "js","jsx","ts","tsx","java","py","rb","go","cs","cpp","c","h","swift",
  "kt","rs","php","scala","vue","svelte",
  "feature","md","txt","json","yaml","yml","xml","html","htm","toml","ini","env",
  "sql","graphql","proto",
]);

function isCodeFile(path) {
  const ext = path.split(".").pop().toLowerCase();
  return CODE_EXTS.has(ext);
}

function buildTree(nodes) {
  const root = {};
  nodes.forEach((n) => {
    const parts = n.path.split("/");
    let cur = root;
    parts.forEach((part, i) => {
      if (!cur[part]) cur[part] = i === parts.length - 1 && n.type === "blob" ? null : {};
      cur = cur[part] ?? {};
    });
  });
  return root;
}

function FileTree({ tree, path = "", selectedPaths, onToggle, expandedDirs, onExpandDir }) {
  return (
    <div style={{ paddingLeft: path ? 14 : 0 }}>
      {Object.entries(tree).sort(([a, av], [b, bv]) => {
        const aDir = av !== null;
        const bDir = bv !== null;
        if (aDir !== bDir) return aDir ? -1 : 1;
        return a.localeCompare(b);
      }).map(([name, subtree]) => {
        const fullPath = path ? `${path}/${name}` : name;
        const isDir = subtree !== null && typeof subtree === "object";
        const isFile = subtree === null;
        const isSelectable = isFile && isCodeFile(name);
        const isSelected = selectedPaths.has(fullPath);
        const isExpanded = expandedDirs.has(fullPath);

        if (isDir) {
          return (
            <div key={fullPath}>
              <div
                onClick={() => onExpandDir(fullPath)}
                style={{
                  display: "flex", alignItems: "center", gap: 6, padding: "3px 6px",
                  cursor: "pointer", borderRadius: 4, fontSize: 12, color: "#c9d1d9",
                  userSelect: "none",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "#21262d"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                <span style={{ fontSize: 10 }}>{isExpanded ? "▼" : "▶"}</span>
                <span>📁</span>
                <span>{name}</span>
              </div>
              {isExpanded && (
                <FileTree
                  tree={subtree}
                  path={fullPath}
                  selectedPaths={selectedPaths}
                  onToggle={onToggle}
                  expandedDirs={expandedDirs}
                  onExpandDir={onExpandDir}
                />
              )}
            </div>
          );
        }

        if (isFile) {
          return (
            <div
              key={fullPath}
              onClick={() => isSelectable && onToggle(fullPath)}
              style={{
                display: "flex", alignItems: "center", gap: 6, padding: "3px 6px",
                cursor: isSelectable ? "pointer" : "default",
                borderRadius: 4, fontSize: 12,
                color: isSelected ? "#79c0ff" : isSelectable ? "#e6edf3" : "#484f58",
                background: isSelected ? "#1f6feb22" : "transparent",
                userSelect: "none",
              }}
              onMouseEnter={(e) => { if (isSelectable) e.currentTarget.style.background = isSelected ? "#1f6feb33" : "#21262d"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = isSelected ? "#1f6feb22" : "transparent"; }}
            >
              <span style={{ fontSize: 10, minWidth: 10 }}>{isSelected ? "✔" : " "}</span>
              <span>{isSelectable ? "📄" : "🔒"}</span>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{name}</span>
            </div>
          );
        }

        return null;
      })}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function App() {
  const [context, setContext] = useState("");
  const [scenarios, setScenarios] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [tab, setTab] = useState("input");
  const [chatHistory, setChatHistory] = useState([]);
  const [refineMsg, setRefineMsg] = useState("");
  const fileRef = useRef();

  // ── GitHub state ──
  const [ghToken, setGhToken] = useState(() => localStorage.getItem("gh_token") || "");
  const [ghRepo, setGhRepo] = useState("");
  const [ghBranch, setGhBranch] = useState("main");
  const [ghBranches, setGhBranches] = useState([]);
  const [ghTree, setGhTree] = useState(null);          // built tree object
  const [ghRawNodes, setGhRawNodes] = useState([]);    // flat list from API
  const [ghSelectedPaths, setGhSelectedPaths] = useState(new Set());
  const [ghExpandedDirs, setGhExpandedDirs] = useState(new Set());
  const [ghLoading, setGhLoading] = useState(false);
  const [ghError, setGhError] = useState("");
  const [ghImporting, setGhImporting] = useState(false);
  const [ghImported, setGhImported] = useState([]);   // {path, chars}
  const [showGhPanel, setShowGhPanel] = useState(false);

  // ── GitHub handlers ──

  const saveToken = (val) => {
    setGhToken(val);
    if (val) localStorage.setItem("gh_token", val);
    else localStorage.removeItem("gh_token");
  };

  const loadRepo = async () => {
    const parsed = parseRepoUrl(ghRepo);
    if (!parsed) { setGhError("Invalid repo. Use owner/repo or paste the GitHub URL."); return; }
    setGhError("");
    setGhLoading(true);
    setGhTree(null);
    setGhSelectedPaths(new Set());
    setGhExpandedDirs(new Set());
    setGhImported([]);
    try {
      const { owner, repo } = parsed;
      // fetch branches
      const branchData = await ghFetch(`/repos/${owner}/${repo}/branches?per_page=100`, ghToken);
      const names = branchData.map((b) => b.name);
      setGhBranches(names);
      const defaultBranch = names.includes(ghBranch) ? ghBranch : (names.includes("main") ? "main" : names[0] || "main");
      setGhBranch(defaultBranch);
      // fetch tree
      const nodes = await fetchTree(owner, repo, defaultBranch, ghToken);
      setGhRawNodes(nodes);
      setGhTree(buildTree(nodes));
    } catch (e) {
      setGhError(e.message);
    } finally {
      setGhLoading(false);
    }
  };

  const switchBranch = async (branch) => {
    const parsed = parseRepoUrl(ghRepo);
    if (!parsed) return;
    setGhBranch(branch);
    setGhLoading(true);
    setGhTree(null);
    setGhSelectedPaths(new Set());
    setGhExpandedDirs(new Set());
    try {
      const nodes = await fetchTree(parsed.owner, parsed.repo, branch, ghToken);
      setGhRawNodes(nodes);
      setGhTree(buildTree(nodes));
    } catch (e) {
      setGhError(e.message);
    } finally {
      setGhLoading(false);
    }
  };

  const togglePath = (path) => {
    setGhSelectedPaths((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const toggleDir = (dirPath) => {
    setGhExpandedDirs((prev) => {
      const next = new Set(prev);
      if (next.has(dirPath)) next.delete(dirPath);
      else next.add(dirPath);
      return next;
    });
  };

  const selectAllVisible = () => {
    const selectable = ghRawNodes.filter((n) => n.type === "blob" && isCodeFile(n.path)).map((n) => n.path);
    setGhSelectedPaths(new Set(selectable));
  };

  const importSelected = async () => {
    if (ghSelectedPaths.size === 0) return;
    const parsed = parseRepoUrl(ghRepo);
    if (!parsed) return;
    setGhImporting(true);
    setGhError("");
    const loaded = [];
    for (const path of ghSelectedPaths) {
      try {
        const content = await fetchFileContent(parsed.owner, parsed.repo, path, ghToken);
        loaded.push({ path, content, chars: content.length });
        setContext((prev) => prev + (prev ? "\n\n" : "") + `--- github:${parsed.owner}/${parsed.repo}/${path} ---\n${content}`);
      } catch (e) {
        loaded.push({ path, content: "", chars: 0, error: e.message });
      }
    }
    setGhImported((prev) => [...prev, ...loaded]);
    setGhSelectedPaths(new Set());
    setGhImporting(false);
  };

  // ── Local file handlers ──

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        const text = ev.target.result;
        setUploadedFiles((prev) => [...prev, { name: file.name, content: text }]);
        setContext((prev) => prev + (prev ? "\n\n" : "") + `--- ${file.name} ---\n${text}`);
      };
      reader.readAsText(file);
    });
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        const text = ev.target.result;
        setUploadedFiles((prev) => [...prev, { name: file.name, content: text }]);
        setContext((prev) => prev + (prev ? "\n\n" : "") + `--- ${file.name} ---\n${text}`);
      };
      reader.readAsText(file);
    });
  }, []);

  const generate = async () => {
    if (!context.trim()) {
      setError("Please provide some context before generating.");
      return;
    }
    setError("");
    setLoading(true);
    setTab("output");

    const messages = [
      {
        role: "user",
        content: `Here is the context for generating Cucumber test scenarios:\n\n${context}\n\nPlease generate comprehensive Cucumber feature file(s) with all relevant test scenarios.`,
      },
    ];
    setChatHistory(messages);

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: SYSTEM_PROMPT,
          messages,
        }),
      });
      const data = await res.json();
      const text = data.content?.map((b) => b.text || "").join("") || "";
      setScenarios(text);
      setChatHistory((prev) => [...prev, { role: "assistant", content: text }]);
    } catch (err) {
      setError("Failed to generate scenarios. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const refine = async () => {
    if (!refineMsg.trim() || !scenarios) return;
    setLoading(true);
    setError("");

    const newHistory = [
      ...chatHistory,
      { role: "user", content: refineMsg },
    ];
    setChatHistory(newHistory);
    setRefineMsg("");

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: SYSTEM_PROMPT,
          messages: newHistory,
        }),
      });
      const data = await res.json();
      const text = data.content?.map((b) => b.text || "").join("") || "";
      setScenarios(text);
      setChatHistory((prev) => [...prev, { role: "assistant", content: text }]);
    } catch (err) {
      setError("Failed to refine scenarios.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(scenarios);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const download = () => {
    const blob = new Blob([scenarios], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "generated.feature";
    a.click();
    URL.revokeObjectURL(url);
  };

  const highlight = (code) => {
    return code
      .replace(/(Feature:|Scenario:|Scenario Outline:|Background:|Examples:)/g, '<span class="kw-feature">$1</span>')
      .replace(/(^\s*)(Given |When |Then |And |But )(.+)/gm, '$1<span class="kw-step">$2</span>$3')
      .replace(/(@\w+)/g, '<span class="kw-tag">$1</span>')
      .replace(/(#.*$)/gm, '<span class="kw-comment">$1</span>')
      .replace(/(".*?")/g, '<span class="kw-string">$1</span>')
      .replace(/(\|[^|\n]+)/g, '<span class="kw-table">$1</span>');
  };

  return (
    <div style={{ fontFamily: "'JetBrains Mono', 'Fira Code', monospace", minHeight: "100vh", background: "#0d1117", color: "#e6edf3", display: "flex", flexDirection: "column" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: #161b22; } ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
        .kw-feature { color: #ff7b72; font-weight: 700; }
        .kw-step { color: #79c0ff; }
        .kw-tag { color: #f0883e; }
        .kw-comment { color: #8b949e; font-style: italic; }
        .kw-string { color: #a5d6ff; }
        .kw-table { color: #d2a8ff; }
        .tab-btn { background: none; border: none; cursor: pointer; font-family: inherit; font-size: 13px; padding: 8px 20px; color: #8b949e; border-bottom: 2px solid transparent; transition: all 0.2s; }
        .tab-btn.active { color: #79c0ff; border-bottom-color: #79c0ff; }
        .tab-btn:hover { color: #e6edf3; }
        .btn { font-family: inherit; font-size: 13px; font-weight: 600; border: none; border-radius: 6px; padding: 10px 20px; cursor: pointer; transition: all 0.2s; }
        .btn-primary { background: #238636; color: #fff; }
        .btn-primary:hover { background: #2ea043; }
        .btn-primary:disabled { background: #21262d; color: #484f58; cursor: not-allowed; }
        .btn-secondary { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
        .btn-secondary:hover { background: #30363d; }
        .btn-blue { background: #1f6feb; color: #fff; }
        .btn-blue:hover { background: #388bfd; }
        textarea { background: #161b22; border: 1px solid #30363d; color: #e6edf3; font-family: 'JetBrains Mono', monospace; font-size: 13px; border-radius: 8px; padding: 14px; resize: none; outline: none; width: 100%; transition: border-color 0.2s; }
        textarea:focus { border-color: #388bfd; }
        .drop-zone { border: 2px dashed #30363d; border-radius: 8px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.2s; }
        .drop-zone:hover { border-color: #388bfd; background: rgba(56,139,253,0.05); }
        .chip { background: #21262d; border: 1px solid #30363d; border-radius: 20px; padding: 4px 12px; font-size: 11px; color: #8b949e; display: inline-flex; align-items: center; gap: 6px; }
        .chip-remove { cursor: pointer; color: #6e7681; } .chip-remove:hover { color: #ff7b72; }
        .pulse { animation: pulse 1.5s ease-in-out infinite; }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        .slide-in { animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        pre { white-space: pre-wrap; word-break: break-word; line-height: 1.7; font-size: 13px; }
        .refine-bar { display: flex; gap: 8px; }
        .refine-input { flex: 1; background: #161b22; border: 1px solid #30363d; color: #e6edf3; font-family: 'JetBrains Mono', monospace; font-size: 13px; border-radius: 6px; padding: 10px 14px; outline: none; }
        .refine-input:focus { border-color: #388bfd; }
        .badge { display: inline-block; background: #1f6feb22; color: #79c0ff; border: 1px solid #1f6feb44; border-radius: 4px; font-size: 11px; padding: 2px 8px; margin-left: 8px; }
        .gh-input { background: #0d1117; border: 1px solid #30363d; color: #e6edf3; font-family: 'JetBrains Mono', monospace; font-size: 13px; border-radius: 6px; padding: 8px 12px; outline: none; width: 100%; transition: border-color 0.2s; }
        .gh-input:focus { border-color: #388bfd; }
        .gh-panel { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; overflow: hidden; }
        .gh-tree-scroll { overflow-y: auto; max-height: 360px; padding: 8px; }
        .gh-select { background: #0d1117; border: 1px solid #30363d; color: #e6edf3; font-family: 'JetBrains Mono', monospace; font-size: 12px; border-radius: 6px; padding: 6px 10px; outline: none; }
        .gh-select:focus { border-color: #388bfd; }
        .status-dot-green { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #3fb950; margin-right: 6px; }
        .status-dot-red { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #ff7b72; margin-right: 6px; }
      `}</style>

      {/* Header */}
      <div style={{ background: "#161b22", borderBottom: "1px solid #30363d", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: 32, height: 32, background: "linear-gradient(135deg, #238636, #1f6feb)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>🥒</div>
          <div>
            <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 18, letterSpacing: "-0.5px" }}>CucumberGen <span className="badge">RAG Agent</span></div>
            <div style={{ fontSize: 11, color: "#8b949e", marginTop: 2 }}>Context-aware Gherkin test scenario generator</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#ff5f57" }}></div>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#febc2e" }}></div>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#28c840" }}></div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ background: "#161b22", borderBottom: "1px solid #30363d", padding: "0 24px", display: "flex" }}>
        <button className={`tab-btn ${tab === "input" ? "active" : ""}`} onClick={() => setTab("input")}>📥 Context Input</button>
        <button className={`tab-btn ${tab === "github" ? "active" : ""}`} onClick={() => setTab("github")}>
          🐙 GitHub {ghImported.length > 0 && <span className="badge">{ghImported.length} imported</span>}
        </button>
        <button className={`tab-btn ${tab === "output" ? "active" : ""}`} onClick={() => setTab("output")} disabled={!scenarios && !loading}>📄 Feature File {scenarios && "✓"}</button>
      </div>

      <div style={{ flex: 1, padding: 24, maxWidth: 960, margin: "0 auto", width: "100%" }}>
        {tab === "github" && (
          <div className="slide-in" style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Token + Repo row */}
            <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ fontSize: 13, color: "#8b949e", fontWeight: 600 }}>🔑 GitHub Access</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <div style={{ fontSize: 11, color: "#8b949e", marginBottom: 6 }}>Personal Access Token (optional for public repos)</div>
                  <input
                    className="gh-input"
                    type="password"
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                    value={ghToken}
                    onChange={(e) => saveToken(e.target.value)}
                  />
                  <div style={{ fontSize: 10, color: "#484f58", marginTop: 4 }}>Token is saved in localStorage. Needs repo read scope for private repos.</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "#8b949e", marginBottom: 6 }}>Repository</div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      className="gh-input"
                      placeholder="owner/repo or https://github.com/owner/repo"
                      value={ghRepo}
                      onChange={(e) => setGhRepo(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && loadRepo()}
                      style={{ flex: 1 }}
                    />
                    <button className="btn btn-blue" onClick={loadRepo} disabled={ghLoading || !ghRepo.trim()} style={{ whiteSpace: "nowrap" }}>
                      {ghLoading ? "⏳" : "Load"}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {ghError && (
              <div style={{ background: "#ff7b7222", border: "1px solid #ff7b7244", borderRadius: 8, padding: "10px 14px", color: "#ff7b72", fontSize: 13 }}>⚠️ {ghError}</div>
            )}

            {/* Branch selector + tree */}
            {ghTree && (
              <div className="gh-panel">
                {/* Tree header */}
                <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderBottom: "1px solid #30363d", background: "#161b22", flexWrap: "wrap", gap: 8 }}>
                  <span style={{ fontSize: 12, color: "#8b949e" }}>Branch:</span>
                  <select
                    className="gh-select"
                    value={ghBranch}
                    onChange={(e) => switchBranch(e.target.value)}
                  >
                    {ghBranches.map((b) => <option key={b} value={b}>{b}</option>)}
                  </select>
                  <span style={{ fontSize: 11, color: "#484f58", flex: 1 }}>
                    {ghRawNodes.filter(n => n.type === "blob").length} files · {ghRawNodes.filter(n => n.type === "blob" && isCodeFile(n.path)).length} code files
                  </span>
                  <button className="btn btn-secondary" style={{ padding: "4px 12px", fontSize: 11 }} onClick={selectAllVisible}>Select all code</button>
                  <button className="btn btn-secondary" style={{ padding: "4px 12px", fontSize: 11 }} onClick={() => setGhSelectedPaths(new Set())}>Clear</button>
                </div>

                {/* File tree */}
                <div className="gh-tree-scroll">
                  {ghLoading ? (
                    <div style={{ color: "#8b949e", fontSize: 12, padding: 16, textAlign: "center" }} className="pulse">Loading file tree...</div>
                  ) : (
                    <FileTree
                      tree={ghTree}
                      selectedPaths={ghSelectedPaths}
                      onToggle={togglePath}
                      expandedDirs={ghExpandedDirs}
                      onExpandDir={toggleDir}
                    />
                  )}
                </div>

                {/* Import action bar */}
                <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderTop: "1px solid #30363d", background: "#161b22" }}>
                  <span style={{ fontSize: 12, color: ghSelectedPaths.size > 0 ? "#79c0ff" : "#484f58" }}>
                    {ghSelectedPaths.size} file{ghSelectedPaths.size !== 1 ? "s" : ""} selected
                  </span>
                  <button
                    className="btn btn-primary"
                    disabled={ghSelectedPaths.size === 0 || ghImporting}
                    onClick={importSelected}
                    style={{ marginLeft: "auto" }}
                  >
                    {ghImporting ? "⏳ Importing..." : `⬆️ Import ${ghSelectedPaths.size > 0 ? ghSelectedPaths.size + " file" + (ghSelectedPaths.size > 1 ? "s" : "") : "selected"} into context`}
                  </button>
                  <button className="btn btn-blue" onClick={() => setTab("input")} style={{ whiteSpace: "nowrap" }}>
                    ✏️ Edit context
                  </button>
                </div>
              </div>
            )}

            {/* Imported files list */}
            {ghImported.length > 0 && (
              <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 14 }}>
                <div style={{ fontSize: 12, color: "#8b949e", marginBottom: 10 }}>📦 Imported from GitHub</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {ghImported.map((f, i) => (
                    <span key={i} className="chip" style={{ borderColor: f.error ? "#ff7b7244" : "#30363d" }}>
                      {f.error ? <span className="status-dot-red" /> : <span className="status-dot-green" />}
                      {f.path.split("/").pop()}
                      {!f.error && <span style={{ color: "#484f58" }}> · {(f.chars / 1000).toFixed(1)}k</span>}
                      {f.error && <span style={{ color: "#ff7b72" }}> · {f.error}</span>}
                      <span className="chip-remove" onClick={() => setGhImported((prev) => prev.filter((_, idx) => idx !== i))}>✕</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {!ghTree && !ghLoading && (
              <div style={{ background: "#161b22", border: "1px dashed #30363d", borderRadius: 8, padding: 32, textAlign: "center", color: "#484f58", fontSize: 13 }}>
                🐙 Enter a GitHub repo above and click <strong style={{ color: "#8b949e" }}>Load</strong> to browse its file tree
              </div>
            )}
          </div>
        )}

        {tab === "input" && (
          <div className="slide-in" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* File Upload */}
            <div
              className="drop-zone"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileRef.current.click()}
            >
              <div style={{ fontSize: 28, marginBottom: 8 }}>📁</div>
              <div style={{ color: "#8b949e", fontSize: 13 }}>Drop files here or click to upload</div>
              <div style={{ color: "#484f58", fontSize: 11, marginTop: 4 }}>.txt, .md, .json, .yaml, .feature, .js, .ts, .java, .py</div>
              <input ref={fileRef} type="file" multiple accept=".txt,.md,.json,.yaml,.yml,.feature,.js,.ts,.java,.py,.xml,.html" style={{ display: "none" }} onChange={handleFileUpload} />
            </div>

            {(uploadedFiles.length > 0 || ghImported.length > 0) && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {uploadedFiles.map((f, i) => (
                  <span key={`local-${i}`} className="chip">
                    📄 {f.name}
                    <span className="chip-remove" onClick={() => setUploadedFiles((prev) => prev.filter((_, idx) => idx !== i))}>✕</span>
                  </span>
                ))}
                {ghImported.filter(f => !f.error).map((f, i) => (
                  <span key={`gh-${i}`} className="chip" style={{ borderColor: "#1f6feb44", color: "#79c0ff" }}>
                    🐙 {f.path.split("/").pop()}
                    <span style={{ color: "#484f58" }}> · {(f.chars/1000).toFixed(1)}k</span>
                    <span className="chip-remove" onClick={() => setGhImported((prev) => prev.filter((_, idx) => idx !== i))}>✕</span>
                  </span>
                ))}
              </div>
            )}

            {/* Context Textarea */}
            <div>
              <div style={{ fontSize: 12, color: "#8b949e", marginBottom: 8 }}>✏️ Or paste your context directly (requirements, user stories, API specs, feature descriptions...)</div>
              <textarea
                rows={16}
                placeholder={`Example:\nFeature: User authentication\n\nAs a registered user\nI want to log in to my account\nSo that I can access my dashboard\n\nAcceptance criteria:\n- User can log in with valid email and password\n- Show error for invalid credentials\n- Lock account after 5 failed attempts\n- Redirect to dashboard on success`}
                value={context}
                onChange={(e) => setContext(e.target.value)}
              />
            </div>

            {error && <div style={{ background: "#ff7b7222", border: "1px solid #ff7b7244", borderRadius: 8, padding: "10px 14px", color: "#ff7b72", fontSize: 13 }}>⚠️ {error}</div>}

            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <button className="btn btn-primary" onClick={generate} disabled={loading || !context.trim()}>
                {loading ? "⏳ Generating..." : "🚀 Generate Cucumber Scenarios"}
              </button>
              <button className="btn btn-secondary" onClick={() => { setContext(""); setUploadedFiles([]); setScenarios(""); setChatHistory([]); setGhImported([]); setGhSelectedPaths(new Set()); }}>🗑️ Clear All</button>
              <span style={{ fontSize: 12, color: "#484f58", marginLeft: "auto" }}>{context.length} chars · ~{Math.ceil(context.split(/\s+/).length / 750)} min read</span>
            </div>
          </div>
        )}

        {tab === "output" && (
          <div className="slide-in" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {loading && (
              <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 32, textAlign: "center" }}>
                <div className="pulse" style={{ fontSize: 32, marginBottom: 12 }}>🥒</div>
                <div style={{ color: "#8b949e", fontSize: 14 }}>Analyzing context and generating scenarios...</div>
                <div style={{ color: "#484f58", fontSize: 12, marginTop: 8 }}>RAG agent is reading your requirements</div>
              </div>
            )}

            {scenarios && !loading && (
              <>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <button className="btn btn-secondary" onClick={copyToClipboard}>{copied ? "✅ Copied!" : "📋 Copy"}</button>
                  <button className="btn btn-blue" onClick={download}>⬇️ Download .feature</button>
                  <button className="btn btn-secondary" onClick={() => setTab("input")}>← Back to Context</button>
                  <span style={{ fontSize: 12, color: "#484f58", marginLeft: "auto" }}>
                    {scenarios.split('\n').length} lines · {(scenarios.match(/Scenario|Scenario Outline/g) || []).length} scenarios
                  </span>
                </div>

                <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 20, overflow: "auto", maxHeight: "60vh" }}>
                  <pre dangerouslySetInnerHTML={{ __html: highlight(scenarios.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')) }} />
                </div>

                {/* Refine bar */}
                <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8, padding: 16 }}>
                  <div style={{ fontSize: 12, color: "#8b949e", marginBottom: 10 }}>🤖 Refine with AI — ask for changes, add edge cases, change tags, etc.</div>
                  <div className="refine-bar">
                    <input
                      className="refine-input"
                      placeholder="e.g. Add more edge cases for the login flow, use @smoke tags..."
                      value={refineMsg}
                      onChange={(e) => setRefineMsg(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") refine(); }}
                    />
                    <button className="btn btn-primary" onClick={refine} disabled={!refineMsg.trim() || loading}>Send</button>
                  </div>
                </div>

                {chatHistory.filter(m => m.role === "user").length > 1 && (
                  <div style={{ fontSize: 12, color: "#484f58" }}>
                    💬 {chatHistory.filter(m => m.role === "user").length - 1} refinement(s) applied
                  </div>
                )}
              </>
            )}

            {error && <div style={{ background: "#ff7b7222", border: "1px solid #ff7b7244", borderRadius: 8, padding: "10px 14px", color: "#ff7b72", fontSize: 13 }}>⚠️ {error}</div>}
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{ borderTop: "1px solid #21262d", padding: "12px 24px", display: "flex", justifyContent: "space-between", fontSize: 11, color: "#484f58" }}>
        <span>🥒 CucumberGen · Gherkin BDD Test Generator · 🐙 GitHub Source Integration</span>
        <span>Powered by Claude claude-sonnet-4-20250514 · RAG Pipeline · GitHub REST API v3</span>
      </div>
    </div>
  );
}

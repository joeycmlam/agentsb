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
        <button className={`tab-btn ${tab === "output" ? "active" : ""}`} onClick={() => setTab("output")} disabled={!scenarios && !loading}>📄 Feature File {scenarios && "✓"}</button>
      </div>

      <div style={{ flex: 1, padding: 24, maxWidth: 960, margin: "0 auto", width: "100%" }}>
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

            {uploadedFiles.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {uploadedFiles.map((f, i) => (
                  <span key={i} className="chip">
                    📄 {f.name}
                    <span className="chip-remove" onClick={() => {
                      setUploadedFiles((prev) => prev.filter((_, idx) => idx !== i));
                    }}>✕</span>
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
              <button className="btn btn-secondary" onClick={() => { setContext(""); setUploadedFiles([]); setScenarios(""); setChatHistory([]); }}>🗑️ Clear All</button>
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
        <span>🥒 CucumberGen · Gherkin BDD Test Generator</span>
        <span>Powered by Claude claude-sonnet-4-20250514 · RAG Pipeline</span>
      </div>
    </div>
  );
}

import { useState } from "react"
import UploadPanel from "./components/UploadPanel"
import ProgressBar from "./components/ProgressBar"
import ResultPanel from "./components/ResultPanel"
import QAPanel from "./components/QAPanel"
import "./App.css"

export default function App() {
  const [sessionId, setSessionId]   = useState(null)
  const [status, setStatus]         = useState(null)
  const [progress, setProgress]     = useState(0)
  const [results, setResults]       = useState(null)
  const [activeTab, setActiveTab]   = useState("checklist")

  const TABS = [
    { id: "checklist", icon: "📋", label: "Review Findings" },
    { id: "qa",        icon: "💬", label: "Ask a Question"  },
    { id: "download",  icon: "⬇️", label: "Download Memo"   },
  ]

  return (
    <div className="app" style={{ position: 'relative', minHeight: '100vh' }}>
      <header className="app-header">
        <div className="header-badge">
          <span>⚖️</span> AI-Powered Legal Due Diligence
        </div>
        <h1>Legal RAG System</h1>
        <p>Pakistani Law Firm Document Review — Powered by LlamaIndex & Groq</p>
        <div className="header-stats">
          <div className="header-stat">
            <span className="header-stat-value">15+</span>
            <span className="header-stat-label">Checklist Questions</span>
          </div>
          <div className="header-stat">
            <span className="header-stat-value">4</span>
            <span className="header-stat-label">Cities Supported</span>
          </div>
          <div className="header-stat">
            <span className="header-stat-value">2,510</span>
            <span className="header-stat-label">Statute Chunks</span>
          </div>
          <div className="header-stat">
            <span className="header-stat-value">&lt;5 min</span>
            <span className="header-stat-label">Review Time</span>
          </div>
        </div>
      </header>

      <main className="app-main">
        {!sessionId && (
          <UploadPanel
            onSessionStart={(id) => {
              setSessionId(id)
              setStatus("uploaded")
            }}
          />
        )}

        {sessionId && status !== "complete" && (
          <ProgressBar
            sessionId={sessionId}
            progress={progress}
            onComplete={(res) => {
              setResults(res)
              setStatus("complete")
            }}
            onStatusUpdate={(s, p) => {
              setStatus(s)
              setProgress(p)
            }}
          />
        )}

        {status === "complete" && results && (
          <>
            <div className="tab-bar">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </div>

            {activeTab === "checklist" && <ResultPanel results={results} />}
            {activeTab === "qa"        && <QAPanel sessionId={sessionId} />}
            {activeTab === "download"  && (
              <div className="panel download-panel">
                <div className="download-icon-wrap">📄</div>
                <h3>Your Due Diligence Memo Is Ready</h3>
                <p>
                  Structured review memorandum with clause-by-clause findings,
                  red flags, constitutional citations, and FBR compliance assessment.
                </p>
                <a
                  href={`http://localhost:8000/api/download/${sessionId}`}
                  className="download-btn"
                  download
                >
                  ⬇️ Download Word Memo (.docx)
                </a>
                <div className="download-meta">
                  <div className="download-meta-item">✅ Word format (.docx)</div>
                  <div className="download-meta-item">✅ Constitutional citations</div>
                  <div className="download-meta-item">✅ FBR compliance section</div>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
import { useState } from "react"
import axios from "axios"

const EXAMPLES = [
  "Does this agreement comply with Section 54 of the Transfer of Property Act?",
  "Is the vendor's title constitutionally protected under Article 23?",
  "Are there any AML obligations for this transaction?",
  "What are the stamp duty requirements under the Stamp Act 1899?",
]

export default function QAPanel({ sessionId }) {
  const [question, setQuestion] = useState("")
  const [answer, setAnswer]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  async function handleAsk() {
    if (!question.trim()) return
    setLoading(true)
    setError(null)
    setAnswer(null)
    try {
      const res = await axios.post("http://localhost:8000/api/query", {
        session_id: sessionId,
        question,
      })
      setAnswer(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || "Query failed. Please retry.")
    } finally {
      setLoading(false)
    }
  }

  const risk = answer ? (answer.risk_level || "LOW").toUpperCase() : null

  return (
    <div className="panel qa-panel">
      <h2>Ask a Legal Question</h2>
      <p className="panel-subtitle">
        Query both your uploaded documents and the Pakistani legal corpus simultaneously.
        The system will cite specific statutes and constitutional provisions.
      </p>

      <div className="qa-examples">
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            className="qa-example-chip"
            onClick={() => setQuestion(ex)}
          >
            {ex.length > 55 ? ex.slice(0, 55) + "…" : ex}
          </button>
        ))}
      </div>

      <div className="qa-input-row">
        <textarea
          className="qa-input"
          rows={3}
          placeholder="e.g. Does this agreement comply with Section 54 of the Transfer of Property Act 1882?"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && e.ctrlKey) handleAsk()
          }}
        />
        <button
          className="ask-btn"
          onClick={handleAsk}
          disabled={loading || !question.trim()}
        >
          {loading ? "⏳ Querying..." : "Ask ↵"}
        </button>
      </div>
      <p className="hint">Ctrl + Enter to submit · Searches both documents and Pakistani statutes</p>

      {error && <div className="error" style={{ marginTop: "1rem" }}>⚠️ {error}</div>}

      {answer && (
        <div className="qa-answer">
          <div className="qa-answer-header">
            <span className={`risk-badge ${risk}`}>{risk}</span>
            <span>Legal Analysis Result</span>
          </div>
          <div className="qa-answer-body">
            <div className="finding-row">
              <span className="finding-row-label">Finding</span>
              <span className="finding-row-value">{answer.finding}</span>
            </div>
            <div className="finding-row">
              <span className="finding-row-label">Reasoning</span>
              <span className="finding-row-value">{answer.reasoning}</span>
            </div>
            <div className="finding-row">
              <span className="finding-row-label">Citations</span>
              <span className="finding-row-value">
                {answer.document_citation && (
                  <span className="citation-chip">📄 {answer.document_citation}</span>
                )}
                {answer.statutory_citation && (
                  <span className="citation-chip">⚖️ {answer.statutory_citation}</span>
                )}
              </span>
            </div>
            <div className="finding-row">
              <span className="finding-row-label">Constitution</span>
              <span className="finding-row-value">
                {answer.constitutional_basis && (
                  <span className="citation-chip">🏛️ {answer.constitutional_basis}</span>
                )}
              </span>
            </div>
            <div className="finding-row">
              <span className="finding-row-label">Recommendation</span>
              <span className="finding-row-value">{answer.recommendation}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
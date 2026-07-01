import { useEffect, useRef, useState } from "react"
import axios from "axios"

const STAGES = [
  { key: "processing", label: "Extract",  short: "1" },
  { key: "indexing",   label: "Index",    short: "2" },
  { key: "querying",   label: "Analyse",  short: "3" },
  { key: "generating", label: "Generate", short: "4" },
  { key: "complete",   label: "Done",     short: "✓" },
]

const STAGE_LABELS = {
  uploaded   : "Documents received...",
  processing : "Extracting text, detecting Urdu content and legal flags...",
  indexing   : "Building multilingual vector index in ChromaDB...",
  querying   : "Running 15+ due diligence questions against Pakistani statutes...",
  generating : "Generating structured review memorandum...",
  complete   : "Review complete!",
}

export default function ProgressBar({ sessionId, progress, onComplete, onStatusUpdate }) {
  const intervalRef   = useRef(null)
  const [currentStatus, setCurrentStatus] = useState("uploaded")

  useEffect(() => {
    intervalRef.current = setInterval(async () => {
      try {
        const res = await axios.get(`http://localhost:8000/api/status/${sessionId}`)
        const { status, progress: p } = res.data
        setCurrentStatus(status)
        onStatusUpdate(status, p)

        if (status === "complete") {
          clearInterval(intervalRef.current)
          const r = await axios.get(`http://localhost:8000/api/results/${sessionId}`)
          onComplete(r.data)
        }
        if (status.startsWith("error")) clearInterval(intervalRef.current)
      } catch (e) {
        console.error("Status poll failed:", e)
      }
    }, 2000)
    return () => clearInterval(intervalRef.current)
  }, [sessionId])

  const stageIndex = STAGES.findIndex(s => s.key === currentStatus)

  return (
    <div className="panel progress-panel">
      <h2>Processing Documents</h2>
      <p className="panel-subtitle">
        Running full Pakistani legal due diligence analysis...
      </p>

      <div className="stage-steps">
        {STAGES.map((stage, i) => {
          const isDone   = i < stageIndex
          const isActive = i === stageIndex
          return (
            <div key={stage.key} className="stage-step">
              <div className={`stage-dot ${isDone ? "done" : isActive ? "active" : ""}`}>
                {isDone ? "✓" : stage.short}
              </div>
              <span className={`stage-label-text ${isDone ? "done" : isActive ? "active" : ""}`}>
                {stage.label}
              </span>
            </div>
          )
        })}
      </div>

      <div className="stage-label">
        {STAGE_LABELS[currentStatus] || "Working..."}
      </div>

      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>
      <div className="progress-pct">{progress}% complete</div>

      <p className="hint">
        ⏱ Typically 3–6 minutes · Groq auto-retries on rate limits
      </p>
    </div>
  )
}
import { useState, useRef } from "react"
import axios from "axios"

const CITIES = ["islamabad", "rawalpindi", "lahore", "karachi"]
const TYPES  = ["property", "loan", "acquisition"]
const SOCIETIES = ["None", "DHA Islamabad", "DHA Lahore",
                   "Bahria Town Rawalpindi", "Bahria Town Lahore"]

export default function UploadPanel({ onSessionStart }) {
  const [files, setFiles]          = useState([])
  const [transactionType, setType] = useState("property")
  const [city, setCity]            = useState("islamabad")
  const [society, setSociety]      = useState("None")
  const [loading, setLoading]      = useState(false)
  const [error, setError]          = useState(null)
  const [dragging, setDragging]    = useState(false)
  const inputRef                   = useRef(null)

  function handleFiles(fileList) {
    const pdfs = [...fileList].filter(f => f.name.toLowerCase().endsWith(".pdf"))
    if (pdfs.length !== fileList.length) {
      setError("Only PDF files are accepted.")
    } else {
      setError(null)
    }
    setFiles(pdfs)
  }

  async function handleSubmit() {
    if (!files.length) return setError("Please select at least one PDF.")
    setLoading(true)
    setError(null)
    const form = new FormData()
    files.forEach(f => form.append("files", f))
    form.append("transaction_type", transactionType)
    form.append("city", city)
    form.append("housing_society", society === "None" ? "" : society)
    try {
      const res = await axios.post("http://localhost:8000/api/upload", form)
      onSessionStart(res.data.session_id)
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed. Is the backend running?")
    } finally {
      setLoading(false)
    }
  }

  const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1)

  return (
    <div className="panel upload-panel">
      <h2>Upload Legal Documents</h2>
      <p className="panel-subtitle">
        Upload your PDF bundle and configure the review parameters below.
        The system will run a full due diligence analysis against Pakistani statutes.
      </p>

      <div className="field-row">
        <div className="field-group">
          <label className="field-label">Transaction Type</label>
          <select value={transactionType} onChange={e => setType(e.target.value)}>
            {TYPES.map(t => (
              <option key={t} value={t}>{capitalize(t)}</option>
            ))}
          </select>
        </div>
        <div className="field-group">
          <label className="field-label">City / Authority</label>
          <select value={city} onChange={e => setCity(e.target.value)}>
            {CITIES.map(c => (
              <option key={c} value={c}>{capitalize(c)}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="field-group">
        <label className="field-label">Housing Society (Optional)</label>
        <select value={society} onChange={e => setSociety(e.target.value)}>
          {SOCIETIES.map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className="field-group">
        <label className="field-label">PDF Documents</label>
        <div
          className={`upload-zone ${dragging ? "dragging" : ""}`}
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={e => {
            e.preventDefault()
            setDragging(false)
            handleFiles(e.dataTransfer.files)
          }}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            multiple
            style={{ display: "none" }}
            onChange={e => handleFiles(e.target.files)}
          />
          <div className="upload-icon">📎</div>
          <h3>
            {dragging
              ? "Drop files here"
              : <>Drag & drop PDFs or <span className="browse-link">browse</ span></>
            }
          </h3>
          <p>Supports text-based and scanned PDFs · Urdu + English · Multiple files</p>
        </div>

        {files.length > 0 && (
          <div className="file-list">
            {files.map((f, i) => (
              <div key={i} className="file-item">
                <span className="file-item-icon">📄</span>
                <span>{f.name}</span>
                <span style={{ marginLeft: "auto", color: "var(--gray-600)", fontSize: "0.78rem" }}>
                  {(f.size / 1024).toFixed(0)} KB
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && <div className="error">⚠️ {error}</div>}

      <button
        className="primary-btn"
        onClick={handleSubmit}
        disabled={loading || !files.length}
      >
        {loading
          ? <><span>⏳</span> Uploading...</>
          : <><span>🔍</span> Run Due Diligence Review</>
        }
      </button>
    </div>
  )
}
export default function ResultPanel({ results }) {
  const {
    findings = [], red_flags = [],
    high_risk_count: high = 0,
    medium_risk_count: medium = 0,
    low_risk_count: low = 0,
  } = results

  return (
    <div className="panel result-panel">
      <h2>Due Diligence Findings</h2>
      <p className="panel-subtitle">
        {findings.length} questions assessed · {red_flags.length} red flag(s) detected
      </p>

      {/* Risk summary */}
      <div className="risk-summary">
        <div className="risk-box high">
          <div className="risk-box-count">{high}</div>
          <div className="risk-box-label">🔴 High Risk</div>
        </div>
        <div className="risk-box medium">
          <div className="risk-box-count">{medium}</div>
          <div className="risk-box-label">🟡 Medium Risk</div>
        </div>
        <div className="risk-box low">
          <div className="risk-box-count">{low}</div>
          <div className="risk-box-label">🟢 Low Risk</div>
        </div>
      </div>

      {/* Red flags */}
      {red_flags.length > 0 ? (
        <div className="red-flags-section">
          <div className="red-flags-header">
            <span>🚨</span>
            <h3>Red Flags Requiring Immediate Attention</h3>
          </div>
          {red_flags.map(flag => (
            <div key={flag.id} className="flag-item">
              <div className="flag-dot" />
              <div className="flag-content">
                <div className="flag-label">[{flag.id}] {flag.label}</div>
                <div className="flag-statute">
                  {flag.statute} · {flag.article}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-issues">
          ✅ No critical red flags detected in this document bundle.
        </div>
      )}

      {/* Findings */}
      <div className="section-heading">
        📝 Clause-by-Clause Findings
      </div>

      <div className="findings-list">
        {findings.map(f => {
          const risk = (f.risk_level || "LOW").toUpperCase()
          return (
            <div key={f.question_id} className="finding-card">
              <div className={`finding-card-header ${risk.toLowerCase()}`}>
                <div className="q-number">Q{f.question_id}</div>
                <div className="question-text">{f.question}</div>
                <span className={`risk-badge ${risk}`}>{risk}</span>
              </div>
              <div className="finding-card-body">
                <div className="finding-row">
                  <span className="finding-row-label">Finding</span>
                  <span className="finding-row-value">{f.finding}</span>
                </div>
                <div className="finding-row">
                  <span className="finding-row-label">Reasoning</span>
                  <span className="finding-row-value">{f.reasoning}</span>
                </div>
                <div className="finding-row">
                  <span className="finding-row-label">Citations</span>
                  <span className="finding-row-value">
                    {f.document_citation && (
                      <span className="citation-chip">📄 {f.document_citation}</span>
                    )}
                    {f.statutory_citation && (
                      <span className="citation-chip">⚖️ {f.statutory_citation}</span>
                    )}
                  </span>
                </div>
                <div className="finding-row">
                  <span className="finding-row-label">Constitution</span>
                  <span className="finding-row-value">
                    {f.constitutional_basis && (
                      <span className="citation-chip">🏛️ {f.constitutional_basis}</span>
                    )}
                  </span>
                </div>
                <div className="finding-row">
                  <span className="finding-row-label">Recommendation</span>
                  <span className="finding-row-value">{f.recommendation}</span>
                </div>
                {f.missing_documents?.length > 0 && (
                  <div className="finding-row">
                    <span className="finding-row-label">Missing</span>
                    <span className="finding-row-value">
                      {f.missing_documents.map((d, i) => (
                        <span key={i} className="missing-tag">⚠️ {d}</span>
                      ))}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
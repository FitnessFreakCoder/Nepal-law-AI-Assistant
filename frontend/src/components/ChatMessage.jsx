import { useState } from 'react'
import api from '../api/axios'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const [nepaliSummary, setNepaliSummary] = useState(null)
  const [nepaliRefs, setNepaliRefs] = useState(null)
  const [translating, setTranslating] = useState(false)
  const [showNepali, setShowNepali] = useState(false)

  const handleTranslate = async () => {
    if (nepaliSummary) {
      setShowNepali(!showNepali)
      return
    }
    setTranslating(true)
    try {
      const [summaryRes, refsRes] = await Promise.all([
        api.post('/translate', { text: message.summary }),
        message.legal_references
          ? api.post('/translate', { text: message.legal_references })
          : Promise.resolve({ data: { translated: '' } })
      ])
      setNepaliSummary(summaryRes.data.translated || 'Translation failed.')
      setNepaliRefs(refsRes.data.translated || '')
      setShowNepali(true)
    } catch {
      setNepaliSummary('Translation failed.')
      setNepaliRefs('')
      setShowNepali(true)
    } finally {
      setTranslating(false)
    }
  }

  if (isUser) {
    return (
      <div className="message user">
        <div className="message-bubble user-bubble">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="message assistant">
      <div className="message-bubble assistant-bubble">
        <SummaryBlock
          summary={message.summary}
          nepali={nepaliSummary}
          showNepali={showNepali}
          translating={translating}
          onTranslate={handleTranslate}
        />
        {message.legal_references && (
          <LegalReferences refs={message.legal_references} nepali={nepaliRefs} showNepali={showNepali} />
        )}
        <div className="message-actions">
          <CopyButton summary={message.summary} refs={message.legal_references} />
        </div>
      </div>
    </div>
  )
}

function SummaryBlock({ summary, nepali, showNepali, translating, onTranslate }) {
  return (
    <div className="summary-block">
      <div className="summary-header">
        <h4>📝 Summary</h4>
        <button className="translate-btn" onClick={onTranslate} disabled={translating}>
          {translating ? 'Translating…' : showNepali ? '🇬🇧 English' : '🇳🇵 नेपालीमा'}
        </button>
      </div>
      <p>{showNepali && nepali ? nepali : summary}</p>
    </div>
  )
}

function LegalReferences({ refs, nepali, showNepali }) {
  const [expanded, setExpanded] = useState(false)
  const displayRefs = showNepali && nepali ? nepali : refs

  return (
    <div className="legal-refs">
      <button className="refs-toggle" onClick={() => setExpanded(!expanded)}>
        📜 Legal Provisions {expanded ? '▲' : '▼'}
      </button>
      {expanded && (
        <div className="refs-content">
          {displayRefs.split('\n').map((line, i) => (
            line.trim() ? <p key={i}>{line}</p> : null
          ))}
        </div>
      )}
    </div>
  )
}

function CopyButton({ summary, refs }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    const text = `Summary:\n${summary}\n\nLegal Provisions:\n${refs || 'N/A'}`
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <button className={`copy-btn${copied ? ' copied' : ''}`} onClick={handleCopy}>
      {copied ? '✓ Copied' : '📋 Copy'}
    </button>
  )
}

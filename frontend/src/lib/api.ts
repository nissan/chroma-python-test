const API_BASE = (import.meta.env.VITE_API_URL as string) ?? 'http://localhost:8000'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface DocumentRecord {
  doc_id: string
  source_file: string
  file_type: string
  chunk_count: number
}

export async function* streamChat(
  message: string,
  history: Message[]
): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ message, history }),
  })

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6)
      if (data === '[DONE]') return
      try {
        const parsed = JSON.parse(data)
        if (parsed.content) yield parsed.content as string
        if (parsed.error) throw new Error(parsed.error as string)
      } catch (e) {
        if (e instanceof SyntaxError) continue
        throw e
      }
    }
  }
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  const res = await fetch(`${API_BASE}/documents`)
  if (!res.ok) throw new Error('Failed to list documents')
  return res.json() as Promise<DocumentRecord[]>
}

export async function uploadFile(
  file: File
): Promise<{ doc_id: string; chunks_ingested: number; source_file: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/documents/upload`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = (await res.json()) as { detail?: string }
    throw new Error(err.detail ?? 'Upload failed')
  }
  return res.json()
}

export async function ingestUrl(
  url: string
): Promise<{ doc_id: string; chunks_ingested: number; source_file: string }> {
  const res = await fetch(`${API_BASE}/documents/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (!res.ok) {
    const err = (await res.json()) as { detail?: string }
    throw new Error(err.detail ?? 'URL ingestion failed')
  }
  return res.json()
}

export async function deleteDocument(doc_id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/${doc_id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Delete failed')
}

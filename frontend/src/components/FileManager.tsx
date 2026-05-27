import { useState, useEffect, useRef, type DragEvent, type ChangeEvent } from 'react'
import { Upload, Link, Trash2, FileText, Globe, FileType, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { listDocuments, uploadFile, ingestUrl, deleteDocument, type DocumentRecord } from '@/lib/api'

const FILE_TYPE_ICONS: Record<string, typeof FileText> = {
  pdf: FileType,
  docx: FileText,
  md: FileText,
  txt: FileText,
  url: Globe,
}

const ACCEPTED_TYPES = '.pdf,.docx,.doc,.md,.txt,.markdown'

export function FileManager() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [urlInput, setUrlInput] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function refresh() {
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch {
      setStatusMessage({ text: 'Failed to load documents', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  function showStatus(text: string, type: 'success' | 'error') {
    setStatusMessage({ text, type })
    setTimeout(() => setStatusMessage(null), 4000)
  }

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return
    setUploading(true)
    for (const file of Array.from(files)) {
      try {
        const result = await uploadFile(file)
        showStatus(`✓ "${file.name}" ingested — ${result.chunks_ingested} chunks`, 'success')
      } catch (err) {
        showStatus(`✗ "${file.name}": ${err instanceof Error ? err.message : 'Upload failed'}`, 'error')
      }
    }
    setUploading(false)
    void refresh()
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragOver(false)
    void handleFiles(e.dataTransfer.files)
  }

  async function handleIngestUrl() {
    const url = urlInput.trim()
    if (!url) return
    setUploading(true)
    try {
      const result = await ingestUrl(url)
      showStatus(`✓ URL ingested — ${result.chunks_ingested} chunks`, 'success')
      setUrlInput('')
    } catch (err) {
      showStatus(`✗ ${err instanceof Error ? err.message : 'Ingestion failed'}`, 'error')
    } finally {
      setUploading(false)
      void refresh()
    }
  }

  async function handleDelete(doc_id: string, source: string) {
    try {
      await deleteDocument(doc_id)
      showStatus(`✓ Deleted "${source}"`, 'success')
      void refresh()
    } catch {
      showStatus('Delete failed', 'error')
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Status toast */}
      {statusMessage && (
        <div
          className={cn(
            'fixed top-4 right-4 z-50 rounded-md px-4 py-3 text-sm shadow-lg',
            statusMessage.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          )}
        >
          {statusMessage.text}
        </div>
      )}

      {/* Upload zone */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Upload className="h-4 w-4" /> Add Documents
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drag-drop area */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
              dragOver
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50 hover:bg-muted/30'
            )}
          >
            {uploading ? (
              <div className="flex flex-col items-center gap-2 text-muted-foreground">
                <Loader2 className="h-8 w-8 animate-spin" />
                <p className="text-sm">Processing…</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-muted-foreground">
                <Upload className="h-8 w-8 opacity-50" />
                <p className="text-sm font-medium">Drop files here or click to browse</p>
                <p className="text-xs">Supports PDF, DOCX, MD, TXT</p>
              </div>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES}
            multiple
            className="hidden"
            onChange={(e: ChangeEvent<HTMLInputElement>) => void handleFiles(e.target.files)}
          />

          <Separator />

          {/* URL ingest */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') void handleIngestUrl() }}
                placeholder="https://example.com/article"
                className="pl-9"
                disabled={uploading}
              />
            </div>
            <Button onClick={() => void handleIngestUrl()} disabled={uploading || !urlInput.trim()}>
              <Link className="h-4 w-4 mr-1" />
              Ingest URL
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Document list */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Ingested Documents
            <Badge variant="secondary" className="ml-auto">
              {documents.length}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : documents.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No documents ingested yet. Upload files or ingest a URL above.
            </p>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => {
                const Icon = FILE_TYPE_ICONS[doc.file_type] ?? FileText
                return (
                  <div
                    key={doc.doc_id}
                    className="flex items-center gap-3 p-3 rounded-md border bg-card hover:bg-muted/30 transition-colors"
                  >
                    <Icon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate" title={doc.source_file}>
                        {doc.source_file}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {doc.chunk_count} chunk{doc.chunk_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <Badge variant="outline" className="text-xs flex-shrink-0">
                      {doc.file_type}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive flex-shrink-0"
                      onClick={() => void handleDelete(doc.doc_id, doc.source_file)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

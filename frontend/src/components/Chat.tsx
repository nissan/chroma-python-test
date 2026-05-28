import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, Bot, User, ChevronDown, ChevronUp, Link } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import { streamChat, type Message, type Source, type TechLevel } from '@/lib/api'

interface AssistantMessage extends Message {
  role: 'assistant'
  sources?: Source[]
}

type ChatMessage = Message | AssistantMessage

interface Props {
  techLevel: TechLevel
}

function SourcesPanel({ sources }: { sources: Source[] }) {
  const [open, setOpen] = useState(false)
  if (sources.length === 0) return null

  return (
    <div className="mt-2 border rounded-md text-xs overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-3 py-1.5 bg-muted/50 hover:bg-muted transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="font-medium text-muted-foreground">
          {sources.length} source{sources.length !== 1 ? 's' : ''}
        </span>
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>
      {open && (
        <div className="divide-y">
          {sources.map((src, i) => (
            <div key={i} className="px-3 py-2 space-y-1">
              <div className="flex items-center gap-1.5 font-medium">
                <Link className="h-3 w-3 flex-shrink-0 text-muted-foreground" />
                {src.url ? (
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary hover:underline truncate"
                  >
                    {src.title || src.url}
                  </a>
                ) : (
                  <span className="text-foreground">{src.title}</span>
                )}
              </div>
              {src.chunk && (
                <p className="text-muted-foreground line-clamp-3 pl-4">{src.chunk}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function Chat({ techLevel }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSubmit() {
    const text = input.trim()
    if (!text || isStreaming) return

    const userMessage: Message = { role: 'user', content: text }
    const history = messages.slice(-10)

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsStreaming(true)

    const assistantMessage: AssistantMessage = { role: 'assistant', content: '', sources: [] }
    setMessages((prev) => [...prev, assistantMessage])

    try {
      for await (const chunk of streamChat(text, history, techLevel, (sources) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1] as AssistantMessage
          updated[updated.length - 1] = { ...last, sources }
          return updated
        })
      })) {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1] as AssistantMessage
          updated[updated.length - 1] = { ...last, content: last.content + chunk }
          return updated
        })
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`,
        }
        return updated
      })
    } finally {
      setIsStreaming(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSubmit()
    }
  }

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground gap-3">
            <Bot className="h-12 w-12 opacity-30" />
            <p className="text-sm">Ask me anything about your documents</p>
            <p className="text-xs opacity-60">Upload documents in the Documents tab first</p>
          </div>
        ) : (
          <div className="space-y-4 max-w-3xl mx-auto">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}
              >
                {msg.role === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                )}
                <div
                  className={cn(
                    'rounded-lg px-4 py-2 max-w-[80%] text-sm',
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground'
                  )}
                >
                  {msg.role === 'assistant' ? (
                    <div>
                      <div className="prose prose-sm max-w-none dark:prose-invert">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                        {isStreaming && i === messages.length - 1 && msg.content === '' && (
                          <span className="inline-flex gap-1">
                            <span className="animate-bounce">.</span>
                            <span className="animate-bounce [animation-delay:0.1s]">.</span>
                            <span className="animate-bounce [animation-delay:0.2s]">.</span>
                          </span>
                        )}
                      </div>
                      {'sources' in msg && msg.sources && msg.sources.length > 0 && (
                        <SourcesPanel sources={msg.sources} />
                      )}
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </ScrollArea>

      <div className="border-t p-4">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
            disabled={isStreaming}
            rows={2}
            className="resize-none"
          />
          <Button
            onClick={() => void handleSubmit()}
            disabled={isStreaming || !input.trim()}
            size="icon"
            className="h-auto"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

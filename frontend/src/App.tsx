import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Chat } from '@/components/Chat'
import { FileManager } from '@/components/FileManager'
import { MessageSquare, FolderOpen, Sparkles } from 'lucide-react'

export default function App() {
  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b px-6 py-3 flex items-center gap-2 bg-card">
        <Sparkles className="h-5 w-5 text-primary" />
        <h1 className="text-base font-semibold">RAG Assistant</h1>
        <span className="text-xs text-muted-foreground ml-auto">mistral · Ollama · ChromaDB</span>
      </header>

      <Tabs defaultValue="chat" className="flex-1 overflow-hidden flex flex-col">
        <div className="border-b px-6 pt-2">
          <TabsList className="h-9">
            <TabsTrigger value="chat" className="gap-1.5 text-xs">
              <MessageSquare className="h-3.5 w-3.5" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="documents" className="gap-1.5 text-xs">
              <FolderOpen className="h-3.5 w-3.5" />
              Documents
            </TabsTrigger>
          </TabsList>
        </div>
        <TabsContent value="chat" className="flex-1 overflow-hidden mt-0 data-[state=active]:flex data-[state=active]:flex-col">
          <Chat />
        </TabsContent>
        <TabsContent value="documents" className="flex-1 overflow-auto mt-0 p-6">
          <FileManager />
        </TabsContent>
      </Tabs>
    </div>
  )
}

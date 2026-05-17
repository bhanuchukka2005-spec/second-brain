import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, FileText, Bot, User } from 'lucide-react'
import { clsx } from 'clsx'
import { chatApi } from '../../api/client'
import { useChatStore, useProviderStore } from '../../store'
import type { ChatMessage } from '../../types'

interface Props {
  sessionId: number
}

export function ChatPanel({ sessionId }: Props) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streamingMsg, setStreamingMsg] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const { addMessage, getMessages } = useChatStore()
  const { provider, apiKey, ollamaModel } = useProviderStore()
  const messages = getMessages(sessionId)

  // Scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMsg])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const question = input.trim()
    setInput('')
    setLoading(true)

    // Add user message immediately
    const userMsg: ChatMessage = { role: 'user', content: question }
    addMessage(sessionId, userMsg)

    try {
      if (provider === 'ollama') {
        // Streaming for Ollama
        setStreamingMsg('')
        let fullResponse = ''

        chatApi.askStream(
          question,
          sessionId,
          ollamaModel,
          (token) => {
            fullResponse += token
            setStreamingMsg(fullResponse)
          },
          () => {
            addMessage(sessionId, { role: 'assistant', content: fullResponse, sources: [] })
            setStreamingMsg('')
            setLoading(false)
          },
          (err) => {
            addMessage(sessionId, {
              role: 'assistant',
              content: `⚠️ Error: ${err}`,
              sources: [],
            })
            setStreamingMsg('')
            setLoading(false)
          }
        )
      } else {
        // Cloud provider — full response
        const res = await chatApi.ask(question, sessionId, provider, apiKey, ollamaModel)
        addMessage(sessionId, {
          role: 'assistant',
          content: res.data.answer,
          sources: res.data.sources,
        })
        setLoading(false)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      addMessage(sessionId, { role: 'assistant', content: `⚠️ ${msg}`, sources: [] })
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className="w-12 h-12 text-brand-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-1">Ready to chat!</h3>
            <p className="text-sm text-gray-400 max-w-sm">
              Ask anything about your indexed notes. The AI answers only from your material.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {/* Streaming message */}
        {streamingMsg && (
          <MessageBubble
            message={{ role: 'assistant', content: streamingMsg }}
            streaming
          />
        )}

        {/* Thinking indicator */}
        {loading && !streamingMsg && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-2 h-2 rounded-full bg-gray-500 animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-4 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask anything about your notes..."
            disabled={loading}
            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 disabled:opacity-50 transition-colors"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-4 py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white transition-colors"
            aria-label="Send message"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message, streaming }: { message: ChatMessage; streaming?: boolean }) {
  const isUser = message.role === 'user'
  return (
    <div className={clsx('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={clsx(
        'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
        isUser ? 'bg-gray-700' : 'bg-brand-600'
      )}>
        {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
      </div>

      {/* Bubble */}
      <div className={clsx(
        'max-w-[75%] rounded-2xl px-4 py-3 text-sm',
        isUser
          ? 'bg-brand-600 text-white rounded-tr-sm'
          : 'bg-gray-800 text-gray-100 rounded-tl-sm'
      )}>
        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        {streaming && (
          <span className="inline-block w-1 h-4 bg-brand-400 animate-pulse ml-0.5 align-middle" />
        )}

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-700">
            <p className="text-xs text-gray-400 mb-1 flex items-center gap-1">
              <FileText className="w-3 h-3" /> Sources
            </p>
            {message.sources.map((s, i) => (
              <p key={i} className="text-xs text-gray-500 truncate">• {s}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

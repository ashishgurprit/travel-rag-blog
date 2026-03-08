"use client"

interface StreamedAnswerProps {
  text: string
  isStreaming: boolean
}

export function StreamedAnswer({ text, isStreaming }: StreamedAnswerProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
        {text}
        {isStreaming && (
          <span className="inline-block w-0.5 h-4 bg-blue-600 ml-0.5 animate-pulse align-middle" />
        )}
      </p>
    </div>
  )
}

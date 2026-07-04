import AIChat from '@/components/ai/AIChat'

export default function AIAssistantPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-text-primary">AI Assistant</h1>
        <p className="text-sm text-text-secondary">
          Ask about findings, get remediation guidance, or draft report language
        </p>
      </div>
      <AIChat />
    </div>
  )
}

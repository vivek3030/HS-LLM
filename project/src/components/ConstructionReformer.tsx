import React, { useState, useRef, useEffect } from 'react';
import { 
  HardHat, 
  Send, 
  Copy, 
  Check, 
  Loader2, 
  AlertCircle, 
  Sparkles,
  Languages,
  Clock,
  Zap
} from 'lucide-react';

interface StreamingState {
  isStreaming: boolean;
  response: string;
  error: string | null;
  language: string;
  processingTime: number;
}

export const ConstructionReformer: React.FC = () => {
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState<StreamingState>({
    isStreaming: false,
    response: '',
    error: null,
    language: '',
    processingTime: 0
  });
  const [copied, setCopied] = useState(false);
  const responseRef = useRef<HTMLDivElement>(null);
  const startTimeRef = useRef<number>(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || input.length < 5) {
      setStreaming(prev => ({ ...prev, error: 'Please enter at least 5 characters' }));
      return;
    }

    if (input.length > 2000) {
      setStreaming(prev => ({ ...prev, error: 'Input exceeds 2000 character limit' }));
      return;
    }

    startTimeRef.current = Date.now();
    setStreaming({
      isStreaming: true,
      response: '',
      error: null,
      language: '',
      processingTime: 0
    });

    try {
      // Simulate API call to your Python backend
      // Replace this with actual API endpoint
      const response = await fetch('/api/reform-description', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          prompt: input,
          use_streaming: true 
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response stream available');
      }

      let accumulatedResponse = '';
      let detectedLanguage = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = new TextDecoder().decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.content) {
                accumulatedResponse += data.content;
                setStreaming(prev => ({
                  ...prev,
                  response: accumulatedResponse
                }));
              }
              
              if (data.language && !detectedLanguage) {
                detectedLanguage = data.language;
                setStreaming(prev => ({
                  ...prev,
                  language: data.language
                }));
              }
            } catch (e) {
              // Skip invalid JSON lines
            }
          }
        }
      }

      const processingTime = Date.now() - startTimeRef.current;
      setStreaming(prev => ({
        ...prev,
        isStreaming: false,
        processingTime
      }));

    } catch (error) {
      setStreaming(prev => ({
        ...prev,
        isStreaming: false,
        error: error instanceof Error ? error.message : 'An unexpected error occurred'
      }));
    }
  };

  const handleCopy = async () => {
    if (streaming.response) {
      await navigator.clipboard.writeText(streaming.response);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  useEffect(() => {
    if (responseRef.current) {
      responseRef.current.scrollTop = responseRef.current.scrollHeight;
    }
  }, [streaming.response]);

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="bg-blue-600 p-3 rounded-full">
              <HardHat className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-800">
              Construction Description Reformer
            </h1>
          </div>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Transform unstructured construction descriptions into clear, professional documentation with AI-powered language processing.
          </p>
        </div>

        {/* Main Interface */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Input Section */}
          <div className="p-6 md:p-8 border-b border-gray-100">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="description" className="block text-sm font-semibold text-gray-700 mb-2">
                  Construction Description
                </label>
                <textarea
                  id="description"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Enter your construction work description here... (e.g., 'Needs painting wall in bedroom, fix broken tiles kitchen floor, replace old sink bathroom')"
                  className="w-full h-32 p-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 resize-none text-gray-700 placeholder-gray-400"
                  disabled={streaming.isStreaming}
                />
                <div className="flex justify-between items-center mt-2">
                  <span className={`text-sm ${
                    input.length > 2000 ? 'text-red-500' : 
                    input.length > 1500 ? 'text-orange-500' : 'text-gray-500'
                  }`}>
                    {input.length}/2000 characters
                  </span>
                  {streaming.error && (
                    <div className="flex items-center gap-1 text-red-500 text-sm">
                      <AlertCircle className="w-4 h-4" />
                      {streaming.error}
                    </div>
                  )}
                </div>
              </div>
              
              <button
                type="submit"
                disabled={streaming.isStreaming || !input.trim() || input.length < 5}
                className="w-full md:w-auto px-8 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2"
              >
                {streaming.isStreaming ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    Reform Description
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Status Bar */}
          {(streaming.isStreaming || streaming.response || streaming.language) && (
            <div className="px-6 md:px-8 py-4 bg-gray-50 border-b border-gray-100">
              <div className="flex flex-wrap items-center gap-4 text-sm">
                {streaming.language && (
                  <div className="flex items-center gap-2 text-blue-600">
                    <Languages className="w-4 h-4" />
                    <span>Language: {streaming.language.toUpperCase()}</span>
                  </div>
                )}
                {streaming.processingTime > 0 && (
                  <div className="flex items-center gap-2 text-green-600">
                    <Clock className="w-4 h-4" />
                    <span>Processed in {(streaming.processingTime / 1000).toFixed(1)}s</span>
                  </div>
                )}
                {streaming.isStreaming && (
                  <div className="flex items-center gap-2 text-orange-600">
                    <Zap className="w-4 h-4" />
                    <span>Streaming response...</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Response Section */}
          {(streaming.response || streaming.isStreaming) && (
            <div className="p-6 md:p-8">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-blue-600" />
                  <h3 className="text-lg font-semibold text-gray-800">
                    Improved Description
                  </h3>
                </div>
                {streaming.response && (
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors duration-200"
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4 text-green-500" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy
                      </>
                    )}
                  </button>
                )}
              </div>
              
              <div
                ref={responseRef}
                className="bg-gray-50 rounded-xl p-6 max-h-96 overflow-y-auto"
              >
                {streaming.response ? (
                  <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {streaming.response}
                    {streaming.isStreaming && (
                      <span className="inline-block w-2 h-5 bg-blue-500 ml-1 animate-pulse" />
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-3 text-gray-500">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Generating improved description...</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-gray-500 text-sm">
          <p>Powered by AI language processing • Optimized for construction industry terminology</p>
        </div>
      </div>
    </div>
  );
};
'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  Upload,
  FileText,
  Send,
  Sparkles,
  Compass,
  Highlighter,
  BookOpen,
  ArrowLeft,
  CheckCircle2,
  Loader2,
  ExternalLink,
  ChevronRight,
  Trash2,
  Menu,
  Scale,
  CheckSquare,
  Square,
  Check,
  X,
  Layers,
  HelpCircle
} from 'lucide-react';
import ResearchCards, { ResearchPaper } from '@/components/ResearchCards';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

interface DocumentMeta {
  doc_id: string;
  filename: string;
  total_pages: number;
  total_chunks: number;
  language_code?: string;
  language_name?: string;
}

interface Citation {
  citation_id: number;
  doc_id: string;
  filename: string;
  page: number;
  snippet: string;
  start_char: number;
  end_char: number;
}

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  citations?: Citation[];
  research_papers?: ResearchPaper[];
  research_mode?: boolean;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';

function sanitizeMarkdown(content: string): string {
  if (!content) return '';
  let text = content;
  // 1. Fix double pipes separating multiple table rows concatenated on the same line
  text = text.replace(/\|\s*\|\s*/g, '|\n| ');
  // 2. Fix empty blank lines between table header and table separator
  text = text.replace(/(\|.+?\|)\n\s*\n+(\|[-:\s|]+\|)/g, '$1\n$2');
  // 3. Ensure double newline before table starts so GFM block parser triggers
  text = text.replace(/([^\n])\n*(\|.+?\|\n\|[-:\s|]+\|)/g, '$1\n\n$2');
  // 4. Ensure double newline after table ends
  text = text.replace(/(\|[^\n]+\|)\n(?=[^\n|#])/g, '$1\n\n');
  // 5. Remove empty row artifacts like | |
  text = text.replace(/\n\|\s*\|\s*\n/g, '\n');
  return text;
}

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentMeta[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState<string>('');
  const [loadingAnswer, setLoadingAnswer] = useState<boolean>(false);
  const [researchMode, setResearchMode] = useState<boolean>(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Computed selected documents
  const selectedDocs = documents.filter((d) => selectedDocIds.includes(d.doc_id));
  const selectedDoc = selectedDocs[0] || null;
  const isMultiCompare = selectedDocIds.length >= 2;

  // Fetch documents on load
  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loadingAnswer]);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/documents`);
      if (res.ok) {
        const data: DocumentMeta[] = await res.json();
        setDocuments(data);
        if (data.length > 0 && selectedDocIds.length === 0) {
          setSelectedDocIds([data[0].doc_id]);
        }
      }
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  const toggleDocSelection = (docId: string) => {
    setSelectedDocIds((prev) => {
      if (prev.includes(docId)) {
        return prev.filter((id) => id !== docId);
      } else {
        return [...prev, docId];
      }
    });
  };

  const selectAllDocs = () => {
    setSelectedDocIds(documents.map((d) => d.doc_id));
  };

  const clearDocSelection = () => {
    setSelectedDocIds([]);
  };

  const [isDragging, setIsDragging] = useState<boolean>(false);

  const processFile = async (file: File) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadStatus('Error: Please upload or drop a valid PDF document (.pdf)');
      return;
    }

    setUploading(true);
    setUploadStatus('Processing & chunking PDF document...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${BACKEND_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setUploadStatus('Document successfully indexed!');
        await fetchDocuments();
        setSelectedDocIds((prev) => [...prev, data.document.doc_id]);
        setIsSidebarOpen(false);
      } else {
        const errData = await res.json();
        setUploadStatus(`Error: ${errData.detail || 'Failed to upload document.'}`);
      }
    } catch (err) {
      setUploadStatus('Upload failed. Please ensure FastAPI server is running on port 8000.');
    } finally {
      setUploading(false);
      setTimeout(() => setUploadStatus(null), 5000);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  };

  const handleSendMessage = async (customQuery?: string) => {
    const query = (typeof customQuery === 'string' ? customQuery : inputQuery).trim();
    if (!query || loadingAnswer) return;

    const userMsgId = Date.now().toString();
    const newMsg: Message = {
      id: userMsgId,
      sender: 'user',
      text: query,
    };

    setMessages((prev) => [...prev, newMsg]);
    if (!customQuery) setInputQuery('');
    setLoadingAnswer(true);

    try {
      const res = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          doc_ids: selectedDocIds,
          doc_id: selectedDocIds[0] || null,
          research_mode: researchMode,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const aiMsg: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: data.answer,
          citations: data.citations || [],
          research_papers: data.research_papers || [],
          research_mode: data.research_mode,
        };
        setMessages((prev) => [...prev, aiMsg]);
      } else {
        const aiMsg: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'ai',
          text: 'Sorry, an error occurred while processing your question.',
        };
        setMessages((prev) => [...prev, aiMsg]);
      }
    } catch (err) {
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: 'Failed to connect to backend server. Please verify FastAPI server is running at http://localhost:8000.',
      };
      setMessages((prev) => [...prev, aiMsg]);
    } finally {
      setLoadingAnswer(false);
    }
  };

  // Open PDF in a NEW TAB with target page & highlighted snippet
  const handleCitationClick = (citation: Citation) => {
    const docId = citation.doc_id || selectedDocIds[0];
    if (!docId) return;

    const targetUrl = `/pdf-viewer?doc_id=${docId}&page=${citation.page}&snippet=${encodeURIComponent(citation.snippet)}`;
    window.open(targetUrl, '_blank');
  };

  const handleDeleteDocument = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this research paper? This will also remove all its indexed vector chunks.')) {
      return;
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/documents/${docId}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
        setSelectedDocIds((prev) => prev.filter((id) => id !== docId));
      } else {
        alert('Failed to delete paper.');
      }
    } catch (e) {
      alert('Network error deleting document.');
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans overflow-hidden">
      {/* Mobile Drawer Overlay */}
      {isSidebarOpen && (
        <div
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm md:hidden transition-opacity"
        />
      )}

      {/* Left Sidebar: Multi-Document Paper Manager */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-80 bg-white/90 backdrop-blur-xl border-r border-slate-200/80 flex flex-col transition-transform duration-300 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Sidebar Header & Brand */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-100">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-black bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
                Alethia.ai
              </h1>
              <p className="text-[10px] text-slate-400 font-medium tracking-tight">Academic Explainer & Multi-Paper RAG</p>
            </div>
          </Link>
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 md:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Upload Drop Zone */}
        <div className="p-4 border-b border-slate-100">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-4 text-center transition-all ${
              isDragging
                ? 'border-indigo-500 bg-indigo-50/70 scale-[1.02]'
                : 'border-slate-200 hover:border-indigo-400 bg-slate-50/50 hover:bg-slate-50'
            }`}
          >
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="hidden"
              id="pdf-upload"
              disabled={uploading}
            />
            <label
              htmlFor="pdf-upload"
              className="cursor-pointer flex flex-col items-center justify-center space-y-2"
            >
              <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100/80">
                {uploading ? (
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
              </div>
              <div>
                <span className="text-xs font-bold text-slate-700 block">
                  {uploading ? 'Analyzing Paper...' : 'Upload or Drop PDF'}
                </span>
                <span className="text-[10px] text-slate-400 block mt-0.5">
                  Academic papers, preprints, patents
                </span>
              </div>
            </label>
          </div>

          {uploadStatus && (
            <div
              className={`mt-2.5 p-2.5 rounded-xl text-[11px] flex items-center gap-2 ${
                uploadStatus.startsWith('Error')
                  ? 'bg-red-50 text-red-700 border border-red-100'
                  : 'bg-emerald-50 text-emerald-700 border border-emerald-100'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">{uploadStatus}</span>
            </div>
          )}
        </div>

        {/* Web Research Mode (Tavily) Sidebar Toggle Switch */}
        <div className="px-4 py-3 border-b border-slate-100 bg-white">
          <div
            onClick={() => setResearchMode(!researchMode)}
            className={`p-2.5 rounded-2xl border transition-all flex items-center justify-between cursor-pointer select-none group ${
              researchMode
                ? 'bg-indigo-50/80 border-indigo-200 text-indigo-950 shadow-xs'
                : 'bg-slate-50/80 border-slate-200/80 text-slate-700 hover:border-indigo-200 hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div
                className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 transition-all ${
                  researchMode
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'bg-white border border-slate-200 text-slate-400 group-hover:text-indigo-600 group-hover:border-indigo-200'
                }`}
              >
                <Compass className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-slate-800 truncate">Web Research Mode</span>
                  {researchMode && (
                    <span className="px-1.5 py-0.2 rounded-full text-[9px] font-bold bg-indigo-600 text-white leading-tight">
                      ON
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-slate-400 truncate mt-0.5">
                  Discover research papers
                </p>
              </div>
            </div>

            {/* Apple / Tailwind Style Switch Pill */}
            <div
              className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors duration-200 ease-in-out ml-2 ${
                researchMode ? 'bg-indigo-600' : 'bg-slate-300'
              }`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition duration-200 ease-in-out ${
                  researchMode ? 'translate-x-4' : 'translate-x-0.75'
                }`}
              />
            </div>
          </div>
        </div>

        {/* Multi-Paper Selection Status Banner */}
        <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/60">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Paper Context ({documents.length})
            </span>
            {documents.length >= 2 && (
              <div className="flex items-center gap-2">
                <button
                  onClick={selectAllDocs}
                  className="text-[10px] text-indigo-600 hover:text-indigo-800 font-semibold"
                >
                  Select All
                </button>
                <span className="text-slate-300">•</span>
                <button
                  onClick={clearDocSelection}
                  className="text-[10px] text-slate-400 hover:text-slate-600"
                >
                  Clear
                </button>
              </div>
            )}
          </div>

          {isMultiCompare ? (
            <div className="p-2.5 rounded-xl bg-gradient-to-r from-purple-50 via-indigo-50 to-purple-50 border border-purple-200/70 text-purple-950">
              <div className="flex items-center gap-2 font-bold text-xs">
                <Scale className="w-3.5 h-3.5 text-purple-600 shrink-0" />
                <span>Comparative Mode ({selectedDocIds.length} Papers)</span>
              </div>
              <p className="text-[10px] text-purple-700/90 mt-0.5 leading-tight">
                Ask questions in chat to compare both papers, contrast features, or explore trade-offs.
              </p>
            </div>
          ) : selectedDoc ? (
            <div className="p-2.5 rounded-xl bg-indigo-50/70 border border-indigo-100 text-indigo-950">
              <div className="flex items-center gap-1.5 font-bold text-xs">
                <FileText className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                <span>1 Paper Active</span>
              </div>
              <p className="text-[10px] text-indigo-700/90 mt-0.5 leading-tight">
                Check another paper below to compare between them directly in chat.
              </p>
            </div>
          ) : (
            <div className="p-2.5 rounded-xl bg-slate-100/80 border border-slate-200 text-slate-600 text-[11px]">
              🌐 Global Research Mode (0 papers selected)
            </div>
          )}
        </div>

        {/* Uploaded Documents List with Checkboxes */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {documents.length === 0 ? (
            <div className="text-center p-6 bg-slate-50 rounded-2xl border border-dashed border-slate-200 text-slate-400 text-xs">
              No documents uploaded yet. Upload a PDF paper above to start analyzing!
            </div>
          ) : (
            documents.map((doc) => {
              const isSelected = selectedDocIds.includes(doc.doc_id);
              return (
                <div
                  key={doc.doc_id}
                  onClick={() => toggleDocSelection(doc.doc_id)}
                  className={`p-3 rounded-2xl border transition-all flex items-center justify-between cursor-pointer group select-none ${
                    isSelected
                      ? 'bg-indigo-50/90 border-indigo-300 text-indigo-950 shadow-sm'
                      : 'bg-white border-slate-200/70 text-slate-600 hover:border-indigo-300 hover:bg-slate-50/80'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate flex-1 min-w-0">
                    <div className="shrink-0 text-indigo-600">
                      {isSelected ? (
                        <CheckSquare className="w-4 h-4 text-indigo-600" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-300 group-hover:text-slate-400" />
                      )}
                    </div>
                    <div className="truncate flex-1">
                      <p className={`text-xs font-semibold truncate ${isSelected ? 'text-indigo-950 font-bold' : 'text-slate-800'}`}>
                        {doc.filename}
                      </p>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="text-[10px] text-slate-400 font-mono">
                          {doc.total_pages}p • {doc.total_chunks} chunks
                        </span>
                        {doc.language_name && (
                          <span className="text-[9px] bg-white text-slate-600 border border-slate-200/80 px-1.5 py-0.2 rounded font-medium">
                            {doc.language_name.split(' ')[0]}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1 ml-2 shrink-0">
                    {/* Open in PDF Viewer in new tab */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(`/pdf-viewer?doc_id=${doc.doc_id}`, '_blank');
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-white transition-all"
                      title="Open full PDF viewer"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                    {/* Delete Paper */}
                    <button
                      onClick={(e) => handleDeleteDocument(e, doc.doc_id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
                      title="Delete paper"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-slate-100 text-center text-[10px] text-slate-400 bg-slate-50/50">
          ResearchSync AI Engine • Dual & Multi-Paper RAG
        </div>
      </aside>

      {/* Main Chat Interface */}
      <main className="flex-1 flex flex-col bg-slate-50/30 overflow-hidden">
        {/* Top Header */}
        <header className="px-4 md:px-6 py-3.5 border-b border-slate-200/60 bg-white/80 backdrop-blur-md flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            {/* Mobile Sidebar Toggle */}
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-500 hover:text-indigo-600 md:hidden transition-all shadow-sm shrink-0"
              title="Open papers drawer"
            >
              <Menu className="w-4 h-4" />
            </button>

            <div className="hidden xs:flex w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600 items-center justify-center shadow-sm shrink-0">
              {isMultiCompare ? (
                <Scale className="w-4 h-4 text-purple-600" />
              ) : (
                <Sparkles className="w-4 h-4 text-indigo-600" />
              )}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900 truncate">Research Assistant Chat</h2>
                {isMultiCompare && (
                  <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-750 font-bold text-[10px] border border-purple-200">
                    ⚖️ {selectedDocIds.length} Papers Active
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 truncate max-w-sm md:max-w-xl">
                {isMultiCompare
                  ? `Comparative Context: ${selectedDocs.map((d) => d.filename).join(' & ')}`
                  : selectedDoc
                  ? `Active Paper: ${selectedDoc.filename}`
                  : 'No paper selected (Global Academic Research Mode)'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Research Mode Active Indicator Badge */}
            {researchMode && (
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 shadow-2xs">
                <Compass className="w-3.5 h-3.5 animate-pulse text-indigo-600" />
                <span>Web Research ON</span>
              </span>
            )}

            {/* View PDF if single doc */}
            {selectedDocs.length === 1 && (
              <button
                onClick={() => window.open(`/pdf-viewer?doc_id=${selectedDocs[0].doc_id}`, '_blank')}
                className="hidden sm:flex px-3 py-1.5 rounded-full bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 items-center gap-1.5 border border-slate-200 shadow-xs transition-all hover:border-indigo-400 hover:text-indigo-600"
              >
                <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                <span>Open PDF</span>
              </button>
            )}
          </div>
        </header>

        {/* Chat Feed Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 max-w-5xl mx-auto w-full">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center max-w-2xl mx-auto space-y-5">
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-indigo-500 via-indigo-600 to-purple-600 text-white flex items-center justify-center shadow-xl shadow-indigo-100">
                {isMultiCompare ? (
                  <Scale className="w-8 h-8" />
                ) : (
                  <Sparkles className="w-8 h-8" />
                )}
              </div>

              <div>
                <h3 className="text-xl font-black text-slate-900">
                  {isMultiCompare
                    ? 'Comparative Multi-Paper Chat'
                    : selectedDoc
                    ? 'AI Academic Explainer Ready'
                    : 'Alethia.ai Academic Research'}
                </h3>
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed max-w-lg">
                  {isMultiCompare
                    ? `You have ${selectedDocIds.length} papers active in the sidebar. Ask normal human questions to compare them, contrast features, or synthesize cross-paper findings.`
                    : selectedDoc
                    ? `Active paper: ${selectedDoc.filename}. Ask questions in English, Hindi, Spanish, or any language, or check another paper on the left to compare both in chat.`
                    : 'Upload research PDFs from the left sidebar or ask any general literature question.'}
                </p>
              </div>

              {/* Quick Prompt Suggestion Chips */}
              <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
                {isMultiCompare ? (
                  <>
                    <button
                      onClick={() => handleSendMessage('Compare both papers in a detailed structured table with key differences, datasets, and results')}
                      className="px-3.5 py-2 rounded-xl bg-white hover:bg-purple-50 hover:border-purple-300 border border-slate-200 text-slate-700 text-xs font-medium shadow-sm transition-all text-left flex items-center gap-1.5"
                    >
                      <span>📊 Compare both papers in a table</span>
                    </button>
                    <button
                      onClick={() => handleSendMessage('What are the key methodology differences and trade-offs between both papers?')}
                      className="px-3.5 py-2 rounded-xl bg-white hover:bg-purple-50 hover:border-purple-300 border border-slate-200 text-slate-700 text-xs font-medium shadow-sm transition-all text-left flex items-center gap-1.5"
                    >
                      <span>⚖️ Compare methodologies & trade-offs</span>
                    </button>
                    <button
                      onClick={() => handleSendMessage('Compare the empirical results, benchmarks, and accuracy of both papers')}
                      className="px-3.5 py-2 rounded-xl bg-white hover:bg-purple-50 hover:border-purple-300 border border-slate-200 text-slate-700 text-xs font-medium shadow-sm transition-all text-left flex items-center gap-1.5"
                    >
                      <span>📈 Compare empirical benchmarks</span>
                    </button>
                    <button
                      onClick={() => handleSendMessage('दोनों शोध पत्रों की तुलना करें और मुख्य अंतर हिंदी में समझाएं')}
                      className="px-3.5 py-2 rounded-xl bg-white hover:bg-purple-50 hover:border-purple-300 border border-slate-200 text-slate-700 text-xs font-medium shadow-sm transition-all text-left flex items-center gap-1.5"
                    >
                      <span>🇮🇳 दोनों पेपर्स की तुलना (Hindi)</span>
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => handleSendMessage('What are the core contributions and key takeaways of this paper?')}
                      className="px-3.5 py-2 rounded-xl bg-white hover:bg-indigo-50 hover:border-indigo-300 border border-slate-200 text-slate-700 text-xs font-medium shadow-sm transition-all text-left"
                    >
                      📋 Summarize key contributions
                    </button>
                    <button
                      onClick={() => handleSendMessage('Explain the model architecture and training methodology in simple terms')}
                      className="px-3.5 py-2 rounded-xl bg-white hover:bg-indigo-50 hover:border-indigo-300 border border-slate-200 text-slate-700 text-xs font-medium shadow-sm transition-all text-left"
                    >
                      🔬 Explain architecture & methodology
                    </button>
                    <button
                      onClick={() => handleSendMessage('What are the limitations, computational bottlenecks, and future work?')}
                      className="px-3.5 py-2 rounded-xl bg-white hover:bg-indigo-50 hover:border-indigo-300 border border-slate-200 text-slate-700 text-xs font-medium shadow-sm transition-all text-left"
                    >
                      ⚠️ Limitations & computational bottlenecks
                    </button>
                  </>
                )}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'ai' && (
                  <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shrink-0 mt-1 shadow-sm">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}

                {msg.sender === 'user' ? (
                  <div className="max-w-2xl rounded-2xl px-5 py-3.5 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-sm text-sm font-medium leading-relaxed whitespace-pre-wrap">
                    {msg.text}
                  </div>
                ) : (
                  <div className="max-w-3xl rounded-2xl p-5 shadow-sm leading-relaxed bg-white border border-slate-200/80 text-slate-800 flex-1">
                    {/* Message Content with GFM Markdown Table & HTML raw breaks support */}
                    <div className="markdown-content text-sm space-y-2 overflow-x-auto text-slate-800">
                      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                        {sanitizeMarkdown(msg.text)}
                      </ReactMarkdown>
                    </div>

                    {/* Direct Document Citations with Exact Paper attribution */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-100">
                        <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                          <Highlighter className="w-3.5 h-3.5 text-yellow-600" />
                          <span>Source Citations ({msg.citations.length})</span>
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {msg.citations.map((c, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleCitationClick(c)}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-yellow-50/90 hover:bg-yellow-100 text-yellow-950 border border-yellow-200/80 transition-all font-mono font-medium text-xs hover:shadow-sm text-left max-w-full group"
                              title="Click to open source PDF on exact page"
                            >
                              <span className="font-bold text-yellow-800 truncate max-w-[120px]">
                                {c.filename ? c.filename : 'Paper'}
                              </span>
                              <span className="text-yellow-700">• [Page {c.page}]</span>
                              <span className="truncate max-w-[180px] text-[11px] opacity-75 font-sans">
                                &quot;{c.snippet}&quot;
                              </span>
                              <ExternalLink className="w-3 h-3 text-yellow-700 shrink-0 group-hover:translate-x-0.5 transition-transform" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Research Paper Suggestions */}
                    {msg.research_papers && msg.research_papers.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-100">
                        <ResearchCards papers={msg.research_papers} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}

          {loadingAnswer && (
            <div className="flex items-center gap-3 text-slate-500 text-xs bg-white p-4 rounded-2xl border border-slate-200 w-fit shadow-sm">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
              <span>
                {isMultiCompare
                  ? `Analyzing & comparing ${selectedDocIds.length} papers...`
                  : 'Analyzing paper & generating answer...'}
              </span>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Bottom Input Bar */}
        <div className="p-4 border-t border-slate-200/60 bg-white/80 backdrop-blur-md">
          <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="max-w-4xl mx-auto flex items-center gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder={
                  isMultiCompare
                    ? `Ask anything or compare these ${selectedDocIds.length} papers (e.g. "compare both papers on accuracy")...`
                    : selectedDoc
                    ? `Ask about ${selectedDoc.filename} (or select another paper to compare)...`
                    : 'Upload a PDF paper or ask any research question...'
                }
                className="w-full bg-white border border-slate-200 rounded-full px-5 py-3.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:shadow-sm focus:shadow-indigo-50/50 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loadingAnswer || !inputQuery.trim()}
              className="px-6 py-3.5 rounded-full bg-slate-900 hover:bg-indigo-600 text-white font-semibold text-sm transition-all hover:scale-[1.03] active:scale-[0.97] disabled:opacity-40 disabled:hover:scale-100 flex items-center gap-2 shadow-sm"
            >
              <span>Ask</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

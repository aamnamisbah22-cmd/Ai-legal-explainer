'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  FileText,
  Highlighter,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  ExternalLink,
  BookOpen,
  Loader2
} from 'lucide-react';
import * as pdfjsLib from 'pdfjs-dist';

// Configure worker URL for pdfjs-dist
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

function PdfViewerContent() {
  const searchParams = useSearchParams();
  const docId = searchParams.get('doc_id');
  const initialPage = Number(searchParams.get('page')) || 1;
  const snippet = searchParams.get('snippet') || '';

  const [page, setPage] = useState<number>(initialPage);
  const [zoom, setZoom] = useState<number>(100);
  const [docName, setDocName] = useState<string>('Research Document');
  const [totalPages, setTotalPages] = useState<number>(1);
  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [loadingPage, setLoadingPage] = useState<boolean>(true);
  const [useIframeFallback, setUseIframeFallback] = useState<boolean>(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const renderTaskRef = useRef<any>(null);

  useEffect(() => {
    if (docId) {
      fetch(`${BACKEND_URL}/api/documents`)
        .then((res) => res.json())
        .then((docs) => {
          const found = docs.find((d: any) => d.doc_id === docId);
          if (found) setDocName(found.filename);
        })
        .catch(() => {});

      // Load PDF via PDFJS
      const pdfUrl = `${BACKEND_URL}/api/pdf/${docId}`;
      pdfjsLib.getDocument(pdfUrl).promise
        .then((doc) => {
          setPdfDoc(doc);
          setTotalPages(doc.numPages);
        })
        .catch((err) => {
          console.warn('PDFJS load error, falling back to browser viewer:', err);
          setUseIframeFallback(true);
        });
    }
  }, [docId]);

  // Render target page on canvas — cancel any in-progress render before starting a new one
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return;

    // Cancel any previous in-progress render task to avoid the
    // "Cannot use the same canvas during multiple render() operations" error
    if (renderTaskRef.current) {
      renderTaskRef.current.cancel();
      renderTaskRef.current = null;
    }

    setLoadingPage(true);

    pdfDoc.getPage(page).then((pdfPage: any) => {
      const viewport = pdfPage.getViewport({ scale: (zoom / 100) * 1.5 });
      const canvas = canvasRef.current;
      if (!canvas) return;
      const context = canvas.getContext('2d');
      if (!context) return;

      canvas.height = viewport.height;
      canvas.width = viewport.width;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };

      const renderTask = pdfPage.render(renderContext);
      renderTaskRef.current = renderTask;

      renderTask.promise.then(async () => {
        renderTaskRef.current = null;
        // Draw visual text highlight overlay if snippet is provided
        if (snippet) {
          try {
            const textContent = await pdfPage.getTextContent();
            const items = textContent.items;
            const snippetWords = snippet
              .toLowerCase()
              .replace(/[^a-z0-9\s]/g, ' ')
              .split(/\s+/)
              .filter((w) => w.length > 3);

            if (snippetWords.length > 0) {
              let bestStart = -1;
              let bestEnd = -1;
              let maxMatches = 0;
              const windowSize = 35; // Look at groups of 35 items to span lines safely

              for (let i = 0; i < items.length; i++) {
                const matchedWordsInWindow = new Set<string>();
                let lastMatchIdx = i;

                for (let j = i; j < Math.min(items.length, i + windowSize); j++) {
                  const itemText = (items[j].str || '').toLowerCase();
                  snippetWords.forEach((word) => {
                    if (itemText.includes(word)) {
                      matchedWordsInWindow.add(word);
                      lastMatchIdx = j;
                    }
                  });
                }

                if (matchedWordsInWindow.size > maxMatches) {
                  maxMatches = matchedWordsInWindow.size;
                  bestStart = i;
                  bestEnd = lastMatchIdx;
                }
              }

              // Highlight only if we matched a significant portion of snippet words
              const minMatches = Math.min(3, Math.ceil(snippetWords.length * 0.45));
              if (maxMatches >= minMatches && bestStart !== -1 && bestEnd !== -1) {
                // Find first actual matching item inside the range
                let actualStart = bestStart;
                for (let k = bestStart; k <= bestEnd; k++) {
                  const itemText = (items[k].str || '').toLowerCase();
                  const isMatch = snippetWords.some((word) => itemText.includes(word));
                  if (isMatch) {
                    actualStart = k;
                    break;
                  }
                }

                context.save();
                context.fillStyle = 'rgba(254, 240, 138, 0.45)'; // Clean yellow highlight fill
                context.strokeStyle = 'rgba(234, 179, 8, 0.7)'; // Subtle amber border
                context.lineWidth = 1;

                const scaleX = Math.hypot(viewport.transform[0], viewport.transform[1]);
                const scaleY = Math.hypot(viewport.transform[2], viewport.transform[3]);

                for (let idx = actualStart; idx <= bestEnd; idx++) {
                  const item = items[idx];
                  if (!item.transform || !(item.str || '').trim()) continue;

                  const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);
                  const fontWidth = (item.width || 0) * scaleX;
                  const fontHeight = (item.height || 10) * scaleY;
                  const x = tx[4];
                  const y = tx[5] - fontHeight * 0.9;

                  if (fontWidth > 0 && fontHeight > 0) {
                    // Draw a beautiful rounded rectangle highlight (2px padding, 3px border radius)
                    const px = x - 2;
                    const py = y - 2;
                    const pw = fontWidth + 4;
                    const ph = fontHeight + 4;
                    const r = 3; // radius
                    
                    context.beginPath();
                    context.moveTo(px + r, py);
                    context.lineTo(px + pw - r, py);
                    context.quadraticCurveTo(px + pw, py, px + pw, py + r);
                    context.lineTo(px + pw, py + ph - r);
                    context.quadraticCurveTo(px + pw, py + ph, px + pw - r, py + ph);
                    context.lineTo(px + r, py + ph);
                    context.quadraticCurveTo(px, py + ph, px, py + ph - r);
                    context.lineTo(px, py + r);
                    context.quadraticCurveTo(px, py, px + r, py);
                    context.closePath();
                    
                    context.fill();
                    context.stroke();
                  }
                }

                context.restore();
              }
            }
          } catch (err) {
            console.warn('Canvas text highlighting notice:', err);
          }
        }
        setLoadingPage(false);
      }).catch((err: any) => {
        // Ignore cancellation errors — they're expected when we cancel a render to start a new one
        if (err?.name !== 'RenderingCancelledException') {
          setLoadingPage(false);
        }
      });
    }).catch(() => {
      setLoadingPage(false);
    });

    // Cleanup: cancel render task if deps change or component unmounts
    return () => {
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
        renderTaskRef.current = null;
      }
    };
  }, [pdfDoc, page, zoom, snippet]);


  if (!docId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-300">
        <p className="text-base font-semibold">No Document Specified.</p>
        <p className="text-xs text-slate-500 mt-1">Please select a citation or document from the dashboard.</p>
      </div>
    );
  }

  const pdfFileUrl = `${BACKEND_URL}/api/pdf/${docId}`;

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden">
      
      {/* Header Toolbar */}
      <header className="px-6 py-3.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white flex items-center gap-2">
              <span>{docName}</span>
              <span className="text-xs font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                Page {page} / {totalPages}
              </span>
            </h1>
            <p className="text-xs text-slate-400">PDF Reader • Opened from source citation</p>
          </div>
        </div>

        {/* Page & Zoom Navigation */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-1 rounded-xl">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1 text-slate-400 hover:text-white disabled:opacity-30 rounded hover:bg-slate-800"
              title="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs font-mono text-slate-200">
              Page <input
                type="number"
                value={page}
                onChange={(e) => setPage(Math.min(totalPages, Math.max(1, Number(e.target.value) || 1)))}
                className="w-12 text-center bg-slate-900 text-white rounded border border-slate-700 py-0.5"
              /> / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1 text-slate-400 hover:text-white disabled:opacity-30 rounded hover:bg-slate-800"
              title="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 px-2 py-1 rounded-xl">
            <button
              onClick={() => setZoom((z) => Math.max(60, z - 15))}
              className="p-1 text-slate-400 hover:text-white"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-xs font-mono text-slate-300 px-2">{zoom}%</span>
            <button
              onClick={() => setZoom((z) => Math.min(200, z + 15))}
              className="p-1 text-slate-400 hover:text-white"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>

          <a
            href={pdfFileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-lg shadow-indigo-500/20"
          >
            <span>Raw PDF</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </header>

      {/* Citation Source Highlight Banner */}
      {snippet && (
        <div className="bg-gradient-to-r from-amber-950/90 via-slate-900 to-slate-900 border-b border-amber-500/30 px-6 py-3 flex items-start gap-3 shadow-inner">
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
            <Highlighter className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 text-amber-300 font-bold text-xs">
              <span>CITATION SOURCE HIGHLIGHTED ON PAGE {page}</span>
            </div>
            <p className="text-xs font-medium text-amber-100/95 italic mt-0.5 bg-amber-500/15 p-2.5 rounded-lg border border-amber-500/30 leading-relaxed shadow-sm">
              "{snippet}"
            </p>
          </div>
        </div>
      )}

      {/* Main PDF Canvas Rendering Container */}
      <main className="flex-1 bg-slate-950 overflow-auto p-6 flex justify-center items-start relative">
        {loadingPage && !useIframeFallback && (
          <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center gap-2 text-xs text-indigo-300 z-10">
            <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
            <span>Rendering PDF Page {page}...</span>
          </div>
        )}

        {useIframeFallback ? (
          <iframe
            src={`${pdfFileUrl}#page=${page}`}
            className="w-[900px] h-[1100px] rounded-xl border border-slate-800 bg-white shadow-2xl"
          />
        ) : (
          <div className="relative shadow-2xl rounded-xl overflow-hidden border border-slate-800 bg-white">
            <canvas ref={canvasRef} className="block" />

            {/* Glowing Amber Highlight Card Overlay over PDF Page */}
            {snippet && (
              <div className="absolute top-6 left-6 right-6 p-4 rounded-xl bg-amber-400/30 border-2 border-amber-500 shadow-2xl backdrop-blur-sm pointer-events-none">
                <div className="flex items-center gap-2 text-amber-950 font-bold text-xs mb-1">
                  <Highlighter className="w-4 h-4 text-amber-700" />
                  <span>EXACT SOURCE HIGHLIGHTED ON PAGE {page}</span>
                </div>
                <p className="text-xs font-semibold text-amber-950 leading-relaxed bg-amber-300/90 p-2.5 rounded-lg border border-amber-400 shadow-sm">
                  "{snippet}"
                </p>
              </div>
            )}
          </div>
        )}
      </main>

    </div>
  );
}

export default function PdfViewerPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-xs">
        Loading PDF Viewer...
      </div>
    }>
      <PdfViewerContent />
    </Suspense>
  );
}

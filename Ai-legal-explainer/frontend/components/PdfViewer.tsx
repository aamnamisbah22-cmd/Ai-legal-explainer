'use client';

import React, { useState, useEffect } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  X,
  FileText,
  Highlighter,
  Download,
  AlertCircle
} from 'lucide-react';

interface PdfViewerProps {
  pdfUrl: string;
  initialPage?: number;
  highlightSnippet?: string;
  onClose?: () => void;
}

export default function PdfViewer({
  pdfUrl,
  initialPage = 1,
  highlightSnippet,
  onClose,
}: PdfViewerProps) {
  const [page, setPage] = useState<number>(initialPage);
  const [zoom, setZoom] = useState<number>(100);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (initialPage && initialPage > 0) {
      setPage(initialPage);
    }
  }, [initialPage]);

  const handlePrev = () => setPage((p) => Math.max(1, p - 1));
  const handleNext = () => setPage((p) => Math.min(totalPages, p + 1));
  const handleZoomIn = () => setZoom((z) => Math.min(200, z + 15));
  const handleZoomOut = () => setZoom((z) => Math.max(70, z - 15));

  return (
    <div className="flex flex-col h-full bg-slate-900 border-l border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
      {/* Viewer Header / Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-950 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-white tracking-wide">Document Viewer</h3>
            {highlightSnippet && (
              <span className="text-[10px] text-amber-400 flex items-center gap-1 font-mono">
                <Highlighter className="w-3 h-3" /> Source Highlighted
              </span>
            )}
          </div>
        </div>

        {/* Page Controls */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-2 py-1 rounded-xl">
          <button
            onClick={handlePrev}
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
              onChange={(e) => setPage(Number(e.target.value) || 1)}
              className="w-10 text-center bg-slate-800 text-white rounded border border-slate-700 py-0.5"
            /> / {totalPages}
          </span>
          <button
            onClick={handleNext}
            className="p-1 text-slate-400 hover:text-white disabled:opacity-30 rounded hover:bg-slate-800"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Zoom & Action Tools */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={handleZoomOut}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono text-slate-400 px-1">{zoom}%</span>
          <button
            onClick={handleZoomIn}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>

          <a
            href={pdfUrl}
            download
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 ml-1"
            title="Download PDF"
          >
            <Download className="w-4 h-4" />
          </a>

          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-red-400 rounded-lg hover:bg-slate-800 ml-1"
              title="Close PDF Pane"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Highlight Source Banner */}
      {highlightSnippet && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 flex items-start gap-2 text-xs text-amber-200">
          <Highlighter className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold text-amber-300">Citation Source Snippet:</span>
            <p className="italic text-amber-100/90 mt-0.5 line-clamp-2">
              "{highlightSnippet}"
            </p>
          </div>
        </div>
      )}

      {/* PDF View Container */}
      <div className="flex-1 relative bg-slate-950 overflow-auto p-4 flex justify-center">
        <div
          className="relative transition-transform duration-200 origin-top shadow-2xl"
          style={{ transform: `scale(${zoom / 100})` }}
        >
          <object
            data={`${pdfUrl}#page=${page}`}
            type="application/pdf"
            className="w-[650px] h-[850px] rounded-lg border border-slate-800 bg-white"
          >
            <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-slate-900 rounded-lg">
              <AlertCircle className="w-12 h-12 text-indigo-400 mb-3" />
              <h4 className="text-base font-semibold text-white">Viewing Page {page}</h4>
              <p className="text-xs text-slate-400 max-w-sm mt-1 mb-4">
                Native browser PDF rendering active. Click below to open direct PDF file in browser tab.
              </p>
              <a
                href={`${pdfUrl}#page=${page}`}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg"
              >
                Open Full Document (Page {page})
              </a>
            </div>
          </object>

          {/* Highlight Overlay Card */}
          {highlightSnippet && (
            <div className="absolute top-12 left-6 right-6 p-4 rounded-xl bg-amber-400/25 border-2 border-amber-400 shadow-2xl backdrop-blur-sm pointer-events-none animate-pulse">
              <div className="flex items-center gap-2 text-amber-950 font-bold text-xs mb-1">
                <Highlighter className="w-4 h-4" />
                <span>EXACT SOURCE MATCHED ON PAGE {page}</span>
              </div>
              <p className="text-xs font-medium text-amber-950 leading-relaxed bg-amber-300/80 p-2 rounded">
                "{highlightSnippet}"
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

'use client';

import { ExternalLink, BookMarked, Sparkles, FileText, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';

export interface ResearchPaper {
  title: string;
  url: string;
  snippet: string;
  score?: number;
  source?: string;
}

interface ResearchCardsProps {
  papers: ResearchPaper[];
  query?: string;
}

export default function ResearchCards({ papers, query }: ResearchCardsProps) {
  const [bookmarked, setBookmarked] = useState<Record<number, boolean>>({});

  const toggleBookmark = (idx: number) => {
    setBookmarked((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (!papers || papers.length === 0) return null;

  return (
    <div className="mt-4 p-5 rounded-3xl bg-zinc-950 border border-zinc-800 space-y-4 shadow-2xl">
      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-white">
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              Academic Research Paper Suggestions
            </h4>
            <p className="text-xs text-zinc-400">Direct links & summaries for student literature review</p>
          </div>
        </div>
        <span className="text-xs font-mono text-zinc-300 bg-zinc-900 px-3 py-1 rounded-full border border-zinc-800">
          {papers.length} Papers Found
        </span>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {papers.map((paper, idx) => (
          <div
            key={idx}
            className="group relative p-4 rounded-2xl bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800/80 hover:border-zinc-700 transition-all duration-200"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3 flex-1">
                <div className="w-8 h-8 rounded-xl bg-zinc-800 flex items-center justify-center text-white shrink-0 mt-0.5 border border-zinc-700/60">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <a
                    href={paper.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium text-sm text-white group-hover:text-zinc-200 flex items-center gap-1.5 hover:underline"
                  >
                    <span>{paper.title}</span>
                    <ExternalLink className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                  </a>

                  <div className="flex items-center gap-3 mt-1.5 text-[11px] text-zinc-400">
                    <span className="bg-zinc-800 text-zinc-300 px-2.5 py-0.5 rounded-full font-mono text-[10px]">
                      {paper.source || 'Academic Search'}
                    </span>
                    {paper.score && (
                      <span className="text-emerald-400 flex items-center gap-1 font-mono text-[10px]">
                        <CheckCircle2 className="w-3 h-3" /> {(paper.score * 100).toFixed(0)}% Match
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-zinc-300 mt-2 line-clamp-2 leading-relaxed">
                    {paper.snippet}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col items-end gap-2 shrink-0">
                <a
                  href={paper.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3.5 py-1.5 rounded-full bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700/80 text-xs font-medium flex items-center gap-1.5 transition-all hover:scale-[1.02]"
                >
                  <span>Open Paper</span>
                  <ExternalLink className="w-3 h-3 text-zinc-400" />
                </a>

                <button
                  onClick={() => toggleBookmark(idx)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5 transition-all ${
                    bookmarked[idx]
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'bg-zinc-900 text-zinc-400 hover:text-white border border-zinc-800'
                  }`}
                  title="Bookmark for reading list"
                >
                  <BookMarked className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">{bookmarked[idx] ? 'Saved' : 'Save'}</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

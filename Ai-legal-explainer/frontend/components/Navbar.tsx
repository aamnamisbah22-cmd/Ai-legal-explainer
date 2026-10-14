'use me';
'use client';

import Link from 'next/link';
import { BookOpen, Sparkles, LayoutDashboard, Compass } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 bg-black/80 backdrop-blur-md border-b border-zinc-800/80 px-6 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-zinc-900 border border-zinc-700/60 flex items-center justify-center shadow-lg group-hover:border-zinc-500 transition-colors">
            <BookOpen className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-white tracking-tight group-hover:text-zinc-300 transition-colors">
                Alethia.ai
              </span>
              <span className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles className="w-2.5 h-2.5 text-amber-400" /> Pro
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-normal">AI Academic Explainer</p>
          </div>
        </Link>

        {/* Center Nav Items */}
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-400">
          <Link href="/#products" className="hover:text-white transition-colors">
            Products
          </Link>
          <Link href="/#features" className="hover:text-white transition-colors">
            Source Highlighting
          </Link>
          <Link href="/#use-cases" className="hover:text-white transition-colors flex items-center gap-1.5">
            <Compass className="w-4 h-4 text-indigo-400" />
            Deep Research Mode
          </Link>
        </div>

        {/* Right CTA Button */}
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-zinc-800 to-zinc-900 hover:from-zinc-700 hover:to-zinc-800 text-white font-medium text-sm border border-zinc-700/80 shadow-xl transition-all hover:scale-[1.03] active:scale-[0.97]"
          >
            <LayoutDashboard className="w-4 h-4 text-white" />
            <span>Dashboard</span>
          </Link>
        </div>

      </div>
    </nav>
  );
}

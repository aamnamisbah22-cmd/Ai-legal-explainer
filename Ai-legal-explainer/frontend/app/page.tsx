'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  Play, 
  Search, 
  Plus, 
  MoreHorizontal, 
  Check, 
  ChevronDown, 
  Home, 
  Folder, 
  BookOpen, 
  ListTodo, 
  Settings, 
  FileText, 
  Share2,
  Sparkles,
  Globe,
  Bell,
  Cpu as CpuIcon
} from 'lucide-react';
import { Button } from '@/components/ui/button';

// Framer Motion Animation Variants
const fadeInUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { 
    opacity: 1, 
    y: 0, 
    transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } 
  }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.1
    }
  }
};

const hoverCard = {
  initial: { y: 0, scale: 1, borderColor: "rgba(226, 232, 240, 0.5)", boxShadow: "0 1px 3px 0 rgba(0,0,0,0.05)" },
  hover: {
    y: -8,
    scale: 1.025,
    borderColor: "rgba(99, 102, 241, 0.35)",
    boxShadow: "0 20px 40px -15px rgba(99, 102, 241, 0.12), 0 10px 20px -10px rgba(0,0,0,0.04)",
    transition: { duration: 0.4, ease: "easeOut" }
  }
};

// Custom Typewriter Hook
function useTypewriter(words: string[], speed: number = 80, delay: number = 1800) {
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [currentText, setCurrentText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    const targetWord = words[currentWordIndex];

    if (isDeleting) {
      timer = setTimeout(() => {
        setCurrentText(targetWord.substring(0, currentText.length - 1));
      }, speed / 2);
    } else {
      timer = setTimeout(() => {
        setCurrentText(targetWord.substring(0, currentText.length + 1));
      }, speed);
    }

    if (!isDeleting && currentText === targetWord) {
      timer = setTimeout(() => setIsDeleting(true), delay);
    } else if (isDeleting && currentText === '') {
      setIsDeleting(false);
      setCurrentWordIndex((prev) => (prev + 1) % words.length);
    }

    return () => clearTimeout(timer);
  }, [currentText, isDeleting, currentWordIndex, words, speed, delay]);

  return currentText;
}

export default function LandingPage() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const dynamicWord = useTypewriter([
    'Academic Literature',
    'Scientific Journals',
    'Research Discovery',
    'Conference Preprints',
    'Complex Citations'
  ], 75, 2000);

  return (
    <div className="min-h-screen w-full bg-background text-foreground font-sans overflow-x-hidden relative selection:bg-accent selection:text-accent-foreground">
      
      {/* 1. Fullscreen Video (Restricted to Hero segment) */}
      <div className="absolute top-0 left-0 w-full h-[100vh] overflow-hidden pointer-events-none z-0">
        <video 
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260319_015952_e1deeb12-8fb7-4071-a42a-60779fc64ab6.mp4"
          autoPlay 
          muted 
          loop 
          playsInline
          className="absolute inset-0 w-full h-full object-cover opacity-[0.25] pointer-events-none"
        />
        {/* Soft gradient fade mask transitioning background video into solid page background */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/70 to-background" />
      </div>

      {/* Floating Navigation Header */}
      <header className="relative z-30 flex items-center justify-between px-6 md:px-12 lg:px-20 py-5 font-body border-b border-border/10 bg-background/30 backdrop-blur-md">
        {/* Left: Logo */}
        <Link href="/" className="flex items-center space-x-2">
          <span className="text-xl font-semibold tracking-tight text-foreground flex items-center gap-1.5">
            <span className="text-accent">✦</span> Alethia.ai
          </span>
        </Link>

        {/* Center: Nav links */}
        <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-muted-foreground">
          <Link href="#features" className="hover:text-foreground transition-colors">Features</Link>
          <Link href="#how-it-works" className="hover:text-foreground transition-colors">How It Works</Link>
          <Link href="/dashboard" className="hover:text-foreground transition-colors">Dashboard</Link>
        </nav>

        {/* Right: CTA */}
        <div>
          <Link href="/dashboard">
            <Button className="rounded-full px-5 text-sm font-medium">
              Launch Platform
            </Button>
          </Link>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section className="relative z-10 max-w-6xl mx-auto flex flex-col items-center justify-between pt-16 md:pt-24 px-6 overflow-hidden">
        
        {/* Top Hero text block */}
        <div className="flex flex-col items-center text-center w-full max-w-3xl">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-4 py-1.5 text-xs text-muted-foreground font-body mb-6 shadow-sm"
          >
            <span>Powered by Gemini 2.5 & Deep Research ✨</span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display text-4xl sm:text-5xl md:text-6xl lg:text-[4.75rem] leading-[0.95] tracking-tight text-foreground max-w-2xl"
          >
            The Future of
            <br />
            <span className="font-display italic font-light text-accent">{dynamicWord}</span>
            <span className="text-accent animate-blink ml-1">|</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-5 text-center text-sm md:text-base text-muted-foreground max-w-[620px] leading-relaxed font-body"
          >
            Automate your literature review with intelligent agents that read, search, and extract citations—so your team can focus on what matters most.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-6 flex items-center gap-3"
          >
            <Link href="/dashboard">
              <Button className="rounded-full px-6 py-5 text-sm font-medium font-body shadow-lg shadow-accent/20">
                Book a demo
              </Button>
            </Link>

            <button className="h-11 w-11 rounded-full border-0 bg-background shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:bg-background/80 flex items-center justify-center transition-colors">
              <Play className="h-4 w-4 fill-foreground stroke-none text-foreground ml-0.5" />
            </button>
          </motion.div>
        </div>

        {/* 3. Custom Coded AI Research Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="w-full mt-10"
        >
          {/* Frosted Glass Wrapper */}
          <div 
            style={{
              background: 'rgba(255, 255, 255, 0.45)',
              border: '1px solid rgba(255, 255, 255, 0.6)',
              boxShadow: '0 25px 80px -12px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.06)'
            }}
            className="rounded-2xl overflow-hidden p-3 md:p-4 backdrop-blur-xl border-b-0 max-h-[520px] flex flex-col relative"
          >
            {/* Dashboard Internals */}
            <div className="flex-1 bg-background rounded-xl border border-border/40 shadow-sm flex overflow-hidden text-[11px] select-none pointer-events-none">
              
              {/* Sidebar */}
              <aside className="hidden sm:flex w-40 border-r border-border/40 p-3 flex-col justify-between shrink-0 bg-secondary/10">
                <div className="space-y-4">
                  {/* Brand logo */}
                  <div className="flex items-center space-x-2 px-1">
                    <div className="w-5 h-5 rounded bg-foreground flex items-center justify-center text-background font-bold text-[10px]">
                      A
                    </div>
                    <span className="font-semibold text-foreground tracking-tight text-[11px]">Alethia.ai</span>
                    <ChevronDown className="w-3 h-3 text-muted-foreground/80" />
                  </div>

                  {/* Nav links */}
                  <nav className="space-y-0.5">
                    <div className="flex items-center justify-between px-2 py-1.5 rounded bg-secondary text-foreground font-medium">
                      <div className="flex items-center space-x-2">
                        <Home className="w-3.5 h-3.5" />
                        <span>Home</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between px-2 py-1.5 rounded text-muted-foreground hover:text-foreground">
                      <div className="flex items-center space-x-2">
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>Library</span>
                      </div>
                      <span className="bg-secondary px-1.5 py-0.2 rounded-full text-[9px] font-semibold text-muted-foreground">10</span>
                    </div>
                    <div className="flex items-center space-x-2 px-2 py-1.5 rounded text-muted-foreground hover:text-foreground">
                      <FileText className="w-3.5 h-3.5" />
                      <span>Publications</span>
                    </div>
                    <div className="flex items-center justify-between px-2 py-1.5 rounded text-muted-foreground hover:text-foreground">
                      <div className="flex items-center space-x-2">
                        <Folder className="w-3.5 h-3.5" />
                        <span>Collections</span>
                      </div>
                      <ChevronDown className="w-2.5 h-2.5" />
                    </div>
                    <div className="flex items-center space-x-2 px-2 py-1.5 rounded text-muted-foreground hover:text-foreground">
                      <ListTodo className="w-3.5 h-3.5" />
                      <span>Saved</span>
                    </div>
                    <div className="flex items-center space-x-2 px-2 py-1.5 rounded text-muted-foreground hover:text-foreground">
                      <Share2 className="w-3.5 h-3.5" />
                      <span>Citations</span>
                    </div>
                    <div className="flex items-center space-x-2 px-2 py-1.5 rounded text-muted-foreground hover:text-foreground">
                      <Settings className="w-3.5 h-3.5" />
                      <span>Settings</span>
                    </div>
                  </nav>

                  {/* Section Workflows */}
                  <div className="pt-2">
                    <span className="text-[9px] uppercase font-bold tracking-wider text-muted-foreground/70 px-2 block mb-1">Workflows</span>
                    <nav className="space-y-0.5">
                      <div className="flex items-center space-x-2 px-2 py-1 rounded text-muted-foreground hover:text-foreground">
                        <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                        <span>PDF Ingestion</span>
                      </div>
                      <div className="flex items-center space-x-2 px-2 py-1 rounded text-muted-foreground hover:text-foreground">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                        <span>Literature RAG</span>
                      </div>
                      <div className="flex items-center space-x-2 px-2 py-1 rounded text-muted-foreground hover:text-foreground">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                        <span>Extracts</span>
                      </div>
                      <div className="flex items-center space-x-2 px-2 py-1 rounded text-muted-foreground hover:text-foreground">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                        <span>Exporter</span>
                      </div>
                    </nav>
                  </div>
                </div>
              </aside>

              {/* Main Content Area */}
              <main className="flex-1 flex flex-col bg-secondary/20 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                {/* Topbar */}
                <div className="h-10 border-b border-border/40 px-4 flex items-center justify-between shrink-0 bg-background/50 backdrop-blur-sm">
                  {/* Search Bar */}
                  <div className="hidden sm:flex w-56 h-6 rounded-md bg-secondary items-center justify-between px-2 text-muted-foreground/60">
                    <div className="flex items-center space-x-1.5">
                      <Search className="w-3 h-3" />
                      <span>Search literature index...</span>
                    </div>
                    <span className="text-[8px] bg-background border border-border/40 px-1 rounded text-muted-foreground">⌘K</span>
                  </div>

                  {/* Actions / User */}
                  <div className="flex items-center space-x-3">
                    <Button variant="default" className="h-6 rounded-md px-2.5 text-[9px] font-medium flex items-center space-x-1">
                      <Plus className="w-3 h-3" />
                      <span>Upload Paper</span>
                    </Button>
                    <Bell className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
                    <div className="w-5 h-5 rounded-full bg-accent flex items-center justify-center text-accent-foreground font-bold text-[9px]">
                      JB
                    </div>
                  </div>
                </div>

                {/* Dashboard body */}
                <div className="p-4 space-y-4">
                  {/* Greeting */}
                  <div>
                    <h2 className="text-sm font-semibold text-foreground">Welcome, Jane</h2>
                  </div>

                  {/* Action Buttons Row */}
                  <div className="flex flex-wrap gap-1.5">
                    <button className="bg-accent text-accent-foreground rounded-full px-3 py-1 font-semibold text-[9px] hover:opacity-90">Upload PDF</button>
                    <button className="bg-secondary border border-border/50 text-foreground rounded-full px-3 py-1 font-semibold text-[9px] hover:bg-secondary/80">Request RAG</button>
                    <button className="bg-secondary border border-border/50 text-foreground rounded-full px-3 py-1 font-semibold text-[9px] hover:bg-secondary/80">Find Similar</button>
                    <button className="bg-secondary border border-border/50 text-foreground rounded-full px-3 py-1 font-semibold text-[9px] hover:bg-secondary/80">Export Citations</button>
                    <button className="bg-secondary border border-border/50 text-foreground rounded-full px-3 py-1 font-semibold text-[9px] hover:bg-secondary/80">Print Log</button>
                    <button className="bg-secondary border border-border/50 text-foreground rounded-full px-3 py-1 font-semibold text-[9px] hover:bg-secondary/80">Create Folder</button>
                    <span className="text-muted-foreground text-[9px] self-center ml-1 cursor-pointer">+ Customize</span>
                  </div>

                  {/* Two equal-width cards */}
                  <div className="flex flex-col sm:flex-row gap-4 items-stretch">
                    
                    {/* Citations Indexed Card */}
                    <div className="bg-background border border-border/40 rounded-xl p-4 flex flex-col justify-between space-y-3 relative overflow-hidden shadow-sm sm:flex-1 sm:basis-0">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-1.5 text-muted-foreground">
                          <span>Citations Indexed</span>
                          <div className="w-3.5 h-3.5 rounded-full bg-green-500/10 text-green-600 flex items-center justify-center">
                            <Check className="w-2.5 h-2.5" />
                          </div>
                        </div>
                        <div className="flex items-baseline space-x-0.5">
                          <span className="text-base font-bold text-foreground">8,450,190</span>
                          <span className="text-xs text-muted-foreground">.32</span>
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="flex items-center space-x-3 text-[9px] font-semibold">
                        <span className="text-muted-foreground">Last 30 Days</span>
                        <span className="text-green-500 flex items-center space-x-0.5">
                          <span>+1.8M parsed</span>
                        </span>
                        <span className="text-destructive flex items-center space-x-0.5">
                          <span>-900K duplicates</span>
                        </span>
                      </div>

                      {/* Smooth Area Chart SVG */}
                      <div className="h-16 w-full pt-2">
                        <svg className="w-full h-full" viewBox="0 0 100 40" preserveAspectRatio="none">
                          <defs>
                            <linearGradient id="chart-grad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity="0.18" />
                              <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity="0" />
                            </linearGradient>
                          </defs>
                          <path d="M 0 35 C 15 25, 25 15, 40 28 C 55 38, 65 5, 80 12 C 90 15, 95 3, 100 5 L 100 40 L 0 40 Z" fill="url(#chart-grad)" />
                          <path d="M 0 35 C 15 25, 25 15, 40 28 C 55 38, 65 5, 80 12 C 90 15, 95 3, 100 5" fill="none" stroke="hsl(var(--accent))" strokeWidth="1.5" />
                        </svg>
                      </div>
                    </div>

                    {/* Academic Repositories Card */}
                    <div className="bg-background border border-border/40 rounded-xl p-4 flex flex-col justify-between shadow-sm sm:flex-1 sm:basis-0">
                      <div className="flex justify-between items-center pb-2 border-b border-border/20">
                        <span className="font-semibold text-foreground">Connected Libraries</span>
                        <div className="flex items-center space-x-1.5 text-muted-foreground">
                          <Plus className="w-3.5 h-3.5 hover:text-foreground cursor-pointer" />
                          <MoreHorizontal className="w-3.5 h-3.5 hover:text-foreground cursor-pointer" />
                        </div>
                      </div>

                      <div className="flex-1 flex flex-col justify-center space-y-1.5 py-2">
                        <div className="flex justify-between items-center py-1">
                          <span className="text-muted-foreground">BioRxiv / MedRxiv</span>
                          <span className="font-medium text-foreground">98,125 docs</span>
                        </div>
                        <div className="flex justify-between items-center py-1">
                          <span className="text-muted-foreground">IEEE / ACM Portal</span>
                          <span className="font-medium text-foreground">6,750,200 docs</span>
                        </div>
                        <div className="flex justify-between items-center py-1">
                          <span className="text-muted-foreground">Local PDF Uploads</span>
                          <span className="font-medium text-foreground">1,592,864 docs</span>
                        </div>
                      </div>
                    </div>

                  </div>

                  {/* Transactions Table */}
                  <div className="bg-background border border-border/40 rounded-xl p-4 shadow-sm space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-foreground">Recent Literature Indexing</span>
                    </div>

                    <div className="overflow-x-auto w-full [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                      <table className="w-full min-w-[500px] text-left border-collapse">
                      <thead>
                        <tr className="border-b border-border/20 text-muted-foreground text-[9px] font-bold">
                          <th className="pb-2">Date</th>
                          <th className="pb-2">Document Name</th>
                          <th className="pb-2">File Size</th>
                          <th className="pb-2 text-right">RAG Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/10 font-medium text-foreground">
                        <tr className="hover:bg-secondary/10 transition-colors">
                          <td className="py-2 text-muted-foreground">Aug 21</td>
                          <td className="py-2 flex items-center space-x-1.5">
                            <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                            <span>attention_is_all_you_need.pdf</span>
                          </td>
                          <td className="py-2 text-muted-foreground">5.2 MB</td>
                          <td className="py-2 text-right">
                            <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-200/50 text-[9px]">Indexing</span>
                          </td>
                        </tr>
                        <tr className="hover:bg-secondary/10 transition-colors">
                          <td className="py-2 text-muted-foreground">Aug 20</td>
                          <td className="py-2 flex items-center space-x-1.5">
                            <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                            <span>llama_3_evaluation_report.pdf</span>
                          </td>
                          <td className="py-2 text-muted-foreground">125.0 MB</td>
                          <td className="py-2 text-right">
                            <span className="px-2 py-0.5 rounded-full bg-green-50 text-green-600 border border-green-200/50 text-[9px]">Completed</span>
                          </td>
                        </tr>
                        <tr className="hover:bg-secondary/10 transition-colors">
                          <td className="py-2 text-muted-foreground">Aug 19</td>
                          <td className="py-2 flex items-center space-x-1.5">
                            <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                            <span>resnet_deep_learning_theory.pdf</span>
                          </td>
                          <td className="py-2 text-muted-foreground">85.4 MB</td>
                          <td className="py-2 text-right">
                            <span className="px-2 py-0.5 rounded-full bg-green-50 text-green-600 border border-green-200/50 text-[9px]">Completed</span>
                          </td>
                        </tr>
                        <tr className="hover:bg-secondary/10 transition-colors">
                          <td className="py-2 text-muted-foreground">Aug 18</td>
                          <td className="py-2 flex items-center space-x-1.5">
                            <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                            <span>bert_pretraining_transformers.pdf</span>
                          </td>
                          <td className="py-2 text-muted-foreground">1.2 MB</td>
                          <td className="py-2 text-right">
                            <span className="px-2 py-0.5 rounded-full bg-green-50 text-green-600 border border-green-200/50 text-[9px]">Completed</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    </div>
                  </div>

                </div>
              </main>

            </div>
          </div>
        </motion.div>
      </section>

      {/* 4. Features Grid Section */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-24 relative z-10 space-y-16">
        <div className="text-center max-w-2xl mx-auto space-y-4">
          <span className="text-accent text-xs font-bold uppercase tracking-wider">Features Grid</span>
          <h2 className="text-3xl md:text-5xl font-display font-medium text-foreground tracking-tight">
            Built for High-Velocity Literature Review
          </h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Eliminate hours of manual citations and reference searching. Understand and map academic papers in seconds.
          </p>
        </div>

        <motion.div 
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
        >
          {/* Card 1 */}
          <motion.div variants={hoverCard} initial="initial" whileHover="hover" className="bg-background p-6 rounded-2xl border border-border/60 shadow-sm space-y-4 cursor-pointer card-glow-wrapper relative overflow-hidden">
            <div className="card-glow-inner" />
            <div className="relative z-10 space-y-4">
              <div className="w-10 h-10 rounded-xl bg-secondary text-accent flex items-center justify-center">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-foreground text-base">Advanced Semantic Search</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Query papers based on conceptual meaning. Local vector embeddings capture deep connections across your literature library.
              </p>
            </div>
          </motion.div>

          {/* Card 2 */}
          <motion.div variants={hoverCard} initial="initial" whileHover="hover" className="bg-background p-6 rounded-2xl border border-border/60 shadow-sm space-y-4 cursor-pointer card-glow-wrapper relative overflow-hidden">
            <div className="card-glow-inner" />
            <div className="relative z-10 space-y-4">
              <div className="w-10 h-10 rounded-xl bg-secondary text-accent flex items-center justify-center">
                <Globe className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-foreground text-base">Deep Research Mode</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Search external paper catalogs dynamically. Discover and ingest associated preprints and research results in real-time.
              </p>
            </div>
          </motion.div>

          {/* Card 3 */}
          <motion.div variants={hoverCard} initial="initial" whileHover="hover" className="bg-background p-6 rounded-2xl border border-border/60 shadow-sm space-y-4 cursor-pointer card-glow-wrapper relative overflow-hidden">
            <div className="card-glow-inner" />
            <div className="relative z-10 space-y-4">
              <div className="w-10 h-10 rounded-xl bg-secondary text-accent flex items-center justify-center">
                <CpuIcon className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-foreground text-base">Intelligent RAG Summaries</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Retrieve accurate source highlights instantly. Get contextual answers mapped directly to exact pages on the PDF viewer.
              </p>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* 5. Ingestion & Workflow View Section */}
      <section id="how-it-works" className="max-w-6xl mx-auto px-6 py-16 relative z-10 space-y-12">
        <div className="flex flex-col lg:flex-row items-center gap-16">
          <div className="w-full lg:w-1/2 space-y-6">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-secondary border border-border/40 text-accent text-xs font-bold uppercase">
              <span>Ingestion Pipeline</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-display font-medium text-foreground tracking-tight">
              Intelligent Literature Ingestion Pipeline
            </h2>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Track your documents through automatic extraction, semantic chunking, and index mapping stages to prepare them for instantly-cited RAG queries.
            </p>

            <ul className="space-y-4 pt-2">
              <li className="flex items-start space-x-3">
                <div className="w-5 h-5 rounded-full bg-green-500/10 flex items-center justify-center text-green-600 shrink-0 mt-0.5">✓</div>
                <p className="text-xs text-foreground font-semibold">Automatic exact-source text highlighting inside Next.js reader.</p>
              </li>
              <li className="flex items-start space-x-3">
                <div className="w-5 h-5 rounded-full bg-green-500/10 flex items-center justify-center text-green-600 shrink-0 mt-0.5">✓</div>
                <p className="text-xs text-foreground font-semibold">Flexible context window memory to retain chat histories.</p>
              </li>
              <li className="flex items-start space-x-3">
                <div className="w-5 h-5 rounded-full bg-green-500/10 flex items-center justify-center text-green-600 shrink-0 mt-0.5">✓</div>
                <p className="text-xs text-foreground font-semibold">Deep research modes to search external paper databases.</p>
              </li>
            </ul>
          </div>
          
          <div className="w-full lg:w-1/2 flex flex-col space-y-4">
            {/* Screen Container */}
            <div className="bg-background rounded-2xl border border-border/40 shadow-xl overflow-hidden h-[420px] flex items-center justify-center relative">
              <div className="w-full h-full p-8 flex flex-col justify-center space-y-8 bg-secondary/5">
                <div className="space-y-4">
                  <span className="text-[10px] uppercase tracking-wider text-accent font-bold">Step 1 — Ingestion</span>
                  <h3 className="font-semibold text-foreground text-sm">Upload literature PDF</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">Fast OCR extracts text structures while mapping pages and columns accurately.</p>
                </div>
                <div className="space-y-4 border-t border-border/20 pt-6">
                  <span className="text-[10px] uppercase tracking-wider text-green-600 font-bold">Step 2 — Semantic Chunking</span>
                  <h3 className="font-semibold text-foreground text-sm">Local vector storage index</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">Splits documents into overlapping semantic blocks and stores them in Pinecone.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Student Accelerator Tools Section */}
      <section id="students" className="max-w-6xl mx-auto px-6 py-24 relative z-10 space-y-16">
        <div className="text-center max-w-2xl mx-auto space-y-4">
          <span className="text-accent text-xs font-bold uppercase tracking-wider">Student Accelerator</span>
          <h2 className="text-3xl md:text-5xl font-display font-medium text-foreground tracking-tight">
            Designed for Student Success
          </h2>
          <p className="text-muted-foreground text-sm">
            Supercharge your studying, thesis preparation, and reading speed with tools tailor-made for academia.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto items-stretch">
          {/* Card 1: Jargon Translator */}
          <div className="bg-background p-8 rounded-2xl border border-border/50 shadow-sm flex flex-col justify-between space-y-6 relative overflow-hidden card-glow-wrapper">
            <div className="card-glow-inner" />
            <div className="relative z-10 space-y-4">
              <div className="w-10 h-10 rounded-xl bg-secondary text-accent flex items-center justify-center">
                <BookOpen className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-foreground text-lg">Smart Jargon Translator</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Struggling with complex mathematical notation or dense PhD-level terminology? Toggle explanation levels instantly (e.g. "Explain like I'm a freshman" or "Explain like I'm a PhD student") to break down complex papers into plain English.
              </p>
            </div>
            <div className="bg-secondary/40 rounded-xl p-4 border border-border/20 text-[10px] font-mono text-muted-foreground leading-relaxed space-y-2">
              <p className="text-foreground font-semibold">Original Paper snippet:</p>
              <p className="italic">"We employ a cross-attention layer parameterizing query matrices alongside sinusoidal positional encodings..."</p>
              <div className="border-t border-border/20 pt-2 text-accent font-semibold flex items-center gap-1">
                <span>✦ Translated (Freshman level):</span>
              </div>
              <p>"The model matches new input questions with stored text blocks by checking how they align, using coordinate markers."</p>
            </div>
          </div>

          {/* Card 2: Thesis Gap Finder */}
          <div className="bg-background p-8 rounded-2xl border border-border/50 shadow-sm flex flex-col justify-between space-y-6 relative overflow-hidden card-glow-wrapper">
            <div className="card-glow-inner" />
            <div className="relative z-10 space-y-4">
              <div className="w-10 h-10 rounded-xl bg-secondary text-accent flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-foreground text-lg">Thesis Gap & Literature Synthesizer</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Connect multiple papers together to find research gaps. Generate bibliography summaries, compare conflicting methodologies, and discover open research questions automatically to draft your thesis outline.
              </p>
            </div>
            <div className="bg-secondary/40 rounded-xl p-4 border border-border/20 text-[10px] font-mono text-muted-foreground space-y-2">
              <div className="flex justify-between text-[9px] text-accent font-bold uppercase tracking-wider">
                <span>Methodology comparison</span>
                <span className="text-green-500">2 Papers</span>
              </div>
              <div className="space-y-1">
                <p className="text-foreground font-semibold">Paper A (Vaswani et al.):</p>
                <p className="text-muted-foreground">Uses absolute sinusoidal values for token indexes.</p>
                <p className="text-foreground font-semibold pt-1">Paper B (Su et al.):</p>
                <p className="text-muted-foreground">Introduces rotary position embeddings for relative distance.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Global Footer */}
      <footer className="bg-secondary/40 border-t border-border/30 py-16 px-6 relative z-10 font-body">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12 text-sm">
          
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <span className="font-bold tracking-tight text-foreground">✦ Alethia.ai</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-sm">
              An intelligent academic literature review assistant. Streamlining text vectorization, semantic RAG extraction, and source highlighting.
            </p>
            <span className="text-[10px] text-muted-foreground/60 block pt-4">
              © {new Date().getFullYear()} Alethia.ai. All rights reserved.
            </span>
          </div>

          <div className="space-y-3">
            <h4 className="font-bold text-foreground uppercase tracking-widest text-[10px]">Product</h4>
            <ul className="space-y-2 text-muted-foreground text-xs">
              <li><Link href="/dashboard" className="hover:text-foreground">RAG Explorer</Link></li>
              <li><Link href="#features" className="hover:text-foreground">Core Engine</Link></li>
              <li><Link href="#how-it-works" className="hover:text-foreground">How It Works</Link></li>
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="font-bold text-foreground uppercase tracking-widest text-[10px]">Resources</h4>
            <ul className="space-y-2 text-muted-foreground text-xs">
              <li><Link href="https://github.com" className="hover:text-foreground">Documentation</Link></li>
              <li><Link href="https://github.com" className="hover:text-foreground">GitHub Portal</Link></li>
              <li><Link href="#how-it-works" className="hover:text-foreground">Walkthrough</Link></li>
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="font-bold text-foreground uppercase tracking-widest text-[10px]">Contact</h4>
            <button className="text-muted-foreground hover:text-foreground text-xs text-left">
              hello@alethia.ai
            </button>
            <span className="text-[10px] text-muted-foreground/60 block pt-4">
              Designed with precision.
            </span>
          </div>

        </div>
      </footer>

    </div>
  );
}

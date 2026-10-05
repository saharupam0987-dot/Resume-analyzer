import React, { useMemo, useState } from 'react';
import { 
  X, FileText, Sparkles, Download, CheckCircle2, 
  HelpCircle, Compass, BookOpen, Layers, Clock, Award
} from 'lucide-react';
import { Button, Badge, TypeBadge, DifficultyBadge, EditorialCallout, SegmentedTabs } from './ui';
import { Donut } from './charts';

export default function ExamPaper({ exam, onClose }) {
  const [questions, setQuestions] = useState(exam.questions || []);
  const [activeSection, setActiveSection] = useState('all');
  const [gen, setGen] = useState(false);

  const sorted = useMemo(
    () => [...questions].sort((a, b) => a.question_number - b.question_number),
    [questions]
  );

  const totalMarks = sorted.reduce((s, q) => s + (q.marks || 0), 0);

  // Group into sections/parts for the tabs
  const mcqs = sorted.filter((q) => q.question_type === 'mcq');
  const fills = sorted.filter((q) => q.question_type === 'fill_blanks');
  const subjs = sorted.filter((q) => q.question_type === 'subjective' || q.question_type === 'long');

  const filteredQuestions = useMemo(() => {
    if (activeSection === 'mcq') return mcqs;
    if (activeSection === 'fill') return fills;
    if (activeSection === 'subj') return subjs;
    return sorted;
  }, [activeSection, sorted, mcqs, fills, subjs]);

  const tabs = [
    { id: 'all', label: 'All Items', sublabel: `${sorted.length} questions` },
    { id: 'mcq', label: 'Part 1', sublabel: `${mcqs.length} multiple choice` },
    { id: 'fill', label: 'Part 2', sublabel: `${fills.length} fill-in-blanks` },
    { id: 'subj', label: 'Part 3', sublabel: `${subjs.length} subjective` },
  ];

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[#FAF8F5] text-[#1C2421] overflow-y-auto" aria-modal="true">
      {/* Top Header - Mirrors Screenshot 1 */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-[#E7E4DC]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          {/* Breadcrumb / Title */}
          <div className="flex items-center gap-3">
            <span className="font-serif text-xl sm:text-2xl font-normal text-[#1C2421]">
              {exam.subject || 'Computer Science'}
            </span>
            <span className="text-xs uppercase tracking-wider text-[#969E99] font-mono">
              {exam.semester ? `SEM ${exam.semester}` : 'EXAM'}
            </span>
            <span className="text-sm text-[#969E99] px-1">/</span>
            <span className="font-serif text-xl sm:text-2xl font-normal text-[#1C2421] truncate max-w-[280px] sm:max-w-md">
              {exam.title}
            </span>
          </div>

          {/* Badges & Action CTA */}
          <div className="flex items-center gap-2 sm:gap-3">
            <Badge tone="neutral" className="hidden sm:inline-flex gap-1.5">
              <Clock size={13} className="text-[#616B66]" />
              {exam.duration || 45} mins
            </Badge>
            <Badge tone="neutral" className="hidden md:inline-flex">
              {totalMarks} marks
            </Badge>
            <Badge tone="sage" className="hidden lg:inline-flex">
              AI Evaluated
            </Badge>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => window.print()}
              icon={Download}
            >
              Print Paper
            </Button>
            <button 
              onClick={onClose} 
              className="p-1.5 rounded-lg text-[#616B66] hover:text-[#1C2421] hover:bg-[#F5F2EA] transition-colors"
              aria-label="Close"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Segmented Horizontal Tabs - Exactly like Screenshot 1 */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-3">
          <SegmentedTabs 
            tabs={tabs} 
            activeTab={activeSection} 
            onChange={setActiveSection} 
          />
        </div>
      </header>

      {/* Main Split Layout - Mirrors Screenshot 1 */}
      <main className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 flex-1">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Column: Atmospheric Editorial Visual Card */}
          <div className="lg:col-span-5 lg:sticky lg:top-36">
            <div className="relative rounded-3xl overflow-hidden aspect-[3/4] max-h-[580px] w-full bg-[#16382C] text-white shadow-xl flex flex-col justify-between p-7 sm:p-8">
              {/* Background atmospheric image with subtle overlay */}
              <img 
                src="https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1200&q=80" 
                alt="Editorial architecture" 
                className="absolute inset-0 w-full h-full object-cover opacity-35 mix-blend-luminosity hover:scale-105 transition-transform duration-700 ease-out"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#16382C] via-[#16382C]/60 to-transparent" />

              {/* Top Big Serif Number - Exactly like "01" in Screenshot 1 */}
              <div className="relative z-10">
                <span className="font-serif text-6xl sm:text-7xl font-bold tracking-tight text-white/95">
                  01
                </span>
              </div>

              {/* Bottom Editorial Caption */}
              <div className="relative z-10 space-y-2">
                <div className="flex items-center gap-1.5 text-xs tracking-wider uppercase text-emerald-200/90 font-medium">
                  <Compass size={13} />
                  <span>{exam.subject || 'Academics'} · Paper Overview</span>
                </div>
                <h3 className="font-serif text-2xl sm:text-3xl font-normal leading-snug text-white">
                  Rigorous conceptual assessment.
                </h3>
                <p className="text-xs text-white/70 leading-relaxed pt-1 font-sans">
                  Synthesized question blueprint with model answer rubrics designed to evaluate understanding and application.
                </p>
              </div>
            </div>

            {/* Quick summary stats beneath the card */}
            <div className="mt-4 p-4 rounded-2xl bg-white border border-[#E7E4DC] flex items-center justify-between text-xs text-[#616B66]">
              <div>
                <span className="text-[#1C2421] font-semibold">{sorted.length}</span> Total Questions
              </div>
              <div className="h-3 w-px bg-[#E7E4DC]" />
              <div>
                <span className="text-[#1C2421] font-semibold">{totalMarks}</span> Total Marks
              </div>
              <div className="h-3 w-px bg-[#E7E4DC]" />
              <div>
                Strictness: <span className="capitalize text-[#16382C] font-semibold">{exam.evaluation_strictness || 'Medium'}</span>
              </div>
            </div>
          </div>

          {/* Right Column: Editorial Timeline Flow */}
          <div className="lg:col-span-7 space-y-6">
            <div>
              <span className="text-xs uppercase tracking-widest text-[#969E99] font-medium font-sans">
                Take it slow
              </span>
              <h2 className="font-serif text-3xl sm:text-4xl font-normal text-[#1C2421] mt-1 mb-2 leading-tight">
                A soft landing. A lovely first wander.
              </h2>
              <p className="text-sm text-[#616B66] leading-relaxed">
                Review and inspect each question, rubric model answers, and semantic scoring criteria below.
              </p>
            </div>

            {/* Question Timeline with Connecting Line */}
            <div className="relative pl-6 sm:pl-8 space-y-8 before:absolute before:left-2 sm:before:left-3 before:top-3 before:bottom-3 before:w-px before:bg-[#E7E4DC]">
              {filteredQuestions.map((q, idx) => {
                const questionNum = q.question_number || idx + 1;
                return (
                  <div key={q.id || idx} className="relative group">
                    {/* Node Dot on Timeline */}
                    <div className="absolute -left-6 sm:-left-8 top-1 w-5 h-5 rounded-full bg-white border-2 border-[#16382C] flex items-center justify-center text-[10px] font-bold text-[#16382C] group-hover:bg-[#16382C] group-hover:text-white transition-colors">
                      {questionNum}
                    </div>

                    {/* Question Content */}
                    <div className="bg-white border border-[#E7E4DC] rounded-2xl p-5 hover:border-[#D8D4C8] transition-all">
                      <div className="flex items-center justify-between gap-2 mb-2 flex-wrap">
                        <span className="text-xs uppercase tracking-wider text-[#969E99] font-medium">
                          Question {questionNum} · {q.question_type?.toUpperCase()}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <DifficultyBadge level={q.difficulty || 'medium'} />
                          <Badge tone="primary">{q.marks} marks</Badge>
                        </div>
                      </div>

                      <h4 className="font-serif text-lg font-medium text-[#1C2421] leading-snug mb-3">
                        {q.question_text}
                      </h4>

                      {/* Options for MCQ */}
                      {q.question_type === 'mcq' && q.options?.length > 0 && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3 pt-3 border-t border-[#F5F2EA]">
                          {q.options.map((opt, i) => {
                            const isCorrect = opt === q.correct_answer;
                            return (
                              <div 
                                key={i}
                                className={`flex items-start gap-2.5 p-2.5 rounded-xl text-xs font-sans border transition-all ${
                                  isCorrect 
                                    ? 'bg-[#E8EFE9] border-[#D0DDD2] text-[#16382C] font-medium' 
                                    : 'bg-[#FAF8F5] border-[#E7E4DC] text-[#616B66]'
                                }`}
                              >
                                <span className="font-mono font-bold shrink-0">{String.fromCharCode(65 + i)}.</span>
                                <span>{opt}</span>
                                {isCorrect && <CheckCircle2 size={13} className="ml-auto text-[#16382C] shrink-0" />}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {/* Model answer for Fill/Subjective */}
                      {q.correct_answer && q.question_type !== 'mcq' && (
                        <div className="mt-3 p-3.5 rounded-xl bg-[#FAF8F5] border border-[#E7E4DC] text-xs leading-relaxed">
                          <span className="font-semibold text-[#16382C] uppercase tracking-wider text-[11px] block mb-1">
                            Model Answer
                          </span>
                          <p className="text-[#616B66]">{q.correct_answer}</p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* "Good to know" Callout - Exactly matching Screenshot 1 */}
            <EditorialCallout title="Good to know" icon={Compass} className="mt-8">
              This examination is automatically evaluated using hybrid semantic AI. Multiple choice and fill-in-the-blanks are scored instantaneously against calibrated answer keys. Subjective responses are analyzed through multidimensional rubrics assessing factual accuracy, conceptual depth, and analytical clarity.
            </EditorialCallout>

            {/* End of paper note */}
            <div className="text-center py-4 text-xs uppercase tracking-widest text-[#969E99] font-sans">
              — End of Examination Paper —
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
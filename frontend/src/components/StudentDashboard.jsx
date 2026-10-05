import React, { useMemo } from 'react';
import { Play, ClipboardCheck, Clock, Target, BookOpen, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Card, Badge, Button, SectionTitle, Skeleton, EmptyState } from './ui';
import { ExamCard } from './Exams';

export default function StudentDashboard({ exams, submissions, loading, onStart, onResults, practiceOnly }) {
  const list = exams || [];
  const subs = submissions || [];

  const stats = useMemo(() => {
    const completed = subs.filter((s) => s.status === 'evaluated').length;
    const pending = subs.filter((s) => s.status !== 'evaluated').length;
    const evaluatedSubs = subs.filter((s) => s.status === 'evaluated' && s.total_score != null);
    const avgScore = evaluatedSubs.length
      ? Math.round(evaluatedSubs.reduce((acc, s) => acc + Number(s.total_score || 0), 0) / evaluatedSubs.length)
      : 0;

    return { 
      available: list.length, 
      completed, 
      pending, 
      avgScore 
    };
  }, [list, subs]);

  const recommended = list.slice(0, 4);

  return (
    <div className="space-y-10 font-sans">
      {/* Editorial Student Hero */}
      <div className="relative rounded-3xl overflow-hidden bg-[#16382C] text-white shadow-xl p-8 sm:p-12">
        <img 
          src="https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=1600&q=80" 
          alt="Study space" 
          className="absolute inset-0 w-full h-full object-cover opacity-20 mix-blend-luminosity"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#16382C] via-[#16382C]/90 to-transparent" />

        <div className="relative z-10 max-w-2xl space-y-3">
          <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-emerald-200/90 font-medium">
            <span className="w-2 h-2 rounded-full bg-[#E05D38]" />
            Student Examination Portal
          </div>
          <h1 className="font-serif text-3xl sm:text-5xl font-normal tracking-tight text-white">
            Active Examinations & Results
          </h1>
          <p className="text-sm sm:text-base text-white/80 leading-relaxed font-sans pt-1">
            Attempt scheduled exams, track semantic rubric scores, and review detailed question-wise feedback.
          </p>
          <div className="pt-3 flex items-center gap-3">
            <Button variant="primary" onClick={onResults} icon={ClipboardCheck}>
              My Results & Submissions
            </Button>
          </div>
        </div>
      </div>

      {/* Stat Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatPill label="Available Exams" value={stats.available} index="01" />
        <StatPill label="Completed Tests" value={stats.completed} index="02" />
        <StatPill label="Pending Review" value={stats.pending} index="03" />
        <StatPill label="Average Score" value={stats.avgScore ? `${stats.avgScore} pts` : 'N/A'} index="04" />
      </div>

      {/* Available Examinations */}
      <div>
        <SectionTitle 
          title="Assigned Examinations" 
          subtitle="Select an exam below to enter distraction-free test taking mode"
        />

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {[0, 1].map((i) => <Skeleton key={i} className="h-44 rounded-2xl" />)}
          </div>
        ) : recommended.length === 0 ? (
          <EmptyState 
            icon={BookOpen} 
            title="No exams assigned yet" 
            description="When your teacher assigns an exam, it will appear right here." 
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {recommended.map((exam, idx) => (
              <ExamCard 
                key={exam.id || idx} 
                exam={exam} 
                index={String(idx + 1).padStart(2, '0')} 
                role="student" 
                onStart={() => onStart(exam)} 
              />
            ))}
          </div>
        )}
      </div>

      {/* Recent Submissions list if any */}
      {subs.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-[#E7E4DC]">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-2xl text-[#1C2421]">Your Recent Submissions</h2>
            <button 
              onClick={onResults} 
              className="text-xs font-semibold text-[#16382C] hover:underline cursor-pointer"
            >
              View all results →
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {subs.slice(0, 4).map((sub, i) => {
              const exam = list.find((e) => e.id === sub.exam_id);
              return (
                <div key={sub.id || i} className="p-4 rounded-2xl border border-[#E7E4DC] bg-white flex items-center justify-between">
                  <div>
                    <div className="text-xs font-semibold text-[#1C2421]">
                      {exam?.title || `Exam #${sub.exam_id}`}
                    </div>
                    <div className="text-[11px] text-[#969E99] mt-0.5">
                      {sub.status === 'evaluated' ? 'AI Evaluated' : 'Submitted'} · {new Date(sub.submitted_at || Date.now()).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-serif text-lg font-bold text-[#16382C]">
                      {sub.total_score} pts
                    </div>
                    <button 
                      onClick={onResults} 
                      className="text-[11px] font-medium text-[#E05D38] hover:underline cursor-pointer"
                    >
                      Inspect Feedback
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function StatPill({ label, value, index }) {
  return (
    <div className="bg-white border border-[#E7E4DC] rounded-2xl p-5 transition-all duration-200 hover:border-[#D8D4C8] flex flex-col justify-between">
      <div className="flex items-center justify-between text-[#969E99] font-mono text-xs mb-3">
        <span>{index}</span>
        <span className="w-1.5 h-1.5 rounded-full bg-[#E8EFE9]" />
      </div>
      <div>
        <div className="font-serif text-3xl font-normal text-[#16382C]">
          {value}
        </div>
        <div className="text-xs font-medium text-[#1C2421] mt-1 font-sans">
          {label}
        </div>
      </div>
    </div>
  );
}
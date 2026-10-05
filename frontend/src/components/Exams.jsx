import React, { useMemo, useState } from 'react';
import { Plus, Eye, Play, FileText, Clock, ListChecks, Sparkles, Search, ArrowRight } from 'lucide-react';
import { Card, Badge, Button, Skeleton, EmptyState, DifficultyBadge, SectionTitle } from './ui';

export function ExamsGrid({ exams, role, loading, onView, onStart, onCreate }) {
  const [q, setQ] = useState('');
  const filtered = useMemo(() => {
    return (exams || []).filter((e) => e.title.toLowerCase().includes(q.toLowerCase()));
  }, [exams, q]);

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-[#969E99] font-medium font-sans">
            Catalog
          </span>
          <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[#1C2421] mt-1">
            {role === 'teacher' ? 'Examinations & Papers' : 'Your Assessments'}
          </h1>
          <p className="text-xs sm:text-sm text-[#616B66] mt-1 font-sans">
            {role === 'teacher' ? `${exams?.length || 0} active papers ready for evaluation` : 'Your assigned tests with instant AI rubric scoring'}
          </p>
        </div>
        {role === 'teacher' && (
          <Button variant="primary" onClick={onCreate} icon={Plus}>Create Exam</Button>
        )}
      </div>

      <div className="relative max-w-md">
        <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#969E99]" />
        <input 
          className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E7E4DC] text-sm bg-white focus:border-[#16382C] outline-none transition-colors" 
          placeholder="Search by title or subject…" 
          value={q} 
          onChange={(e) => setQ(e.target.value)} 
        />
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {[0, 1, 2].map((i) => <Skeleton key={i} className="h-48 rounded-2xl" />)}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <EmptyState
            icon={FileText}
            title={exams?.length ? 'No exams match your search' : role === 'teacher' ? 'No exams created yet' : 'No exams assigned'}
            description={exams?.length ? 'Try a different keyword or subject.' : role === 'teacher' ? 'Create your first AI-generated exam from course notes.' : 'Check back later for teacher assignments.'}
            action={role === 'teacher' && exams?.length === 0 ? <Button variant="primary" onClick={onCreate} icon={Plus}>Create Exam</Button> : null}
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filtered.map((exam, idx) => (
            <ExamCard 
              key={exam.id || idx} 
              index={String(idx + 1).padStart(2, '0')} 
              exam={exam} 
              role={role} 
              onView={() => onView(exam)} 
              onStart={() => onStart(exam)} 
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function ExamCard({ exam, index = '01', role, onView, onStart }) {
  const n = exam.questions?.length || 0;
  return (
    <div 
      className="bg-white border border-[#E7E4DC] hover:border-[#D8D4C8] rounded-2xl p-6 transition-all duration-200 hover:shadow-sm flex flex-col justify-between group"
    >
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="font-serif text-2xl font-bold text-[#16382C]">
            {index}
          </span>
          <div className="flex items-center gap-1.5">
            <Badge tone="sage">{n} Questions</Badge>
            <Badge tone="neutral">{exam.total_marks || 20} Marks</Badge>
          </div>
        </div>

        <h3 className="font-serif text-lg font-medium text-[#1C2421] leading-snug line-clamp-2 group-hover:text-[#16382C] transition-colors">
          {exam.title}
        </h3>

        <div className="flex items-center gap-3 mt-3 text-xs text-[#616B66]">
          <span>{exam.subject || 'Academics'}</span>
          <span className="text-[#E7E4DC]">·</span>
          <span>{exam.duration || 45} mins</span>
        </div>
      </div>

      <div className="pt-4 mt-6 border-t border-[#F5F2EA] flex items-center justify-between">
        <span className="text-xs text-[#969E99]">
          Strictness: <span className="capitalize font-medium text-[#1C2421]">{exam.evaluation_strictness || 'Medium'}</span>
        </span>
        {role === 'student' ? (
          <button 
            onClick={onStart}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#E05D38] hover:text-[#C94B27] group-hover:translate-x-0.5 transition-all cursor-pointer"
          >
            <span>Take Exam</span>
            <ArrowRight size={13} />
          </button>
        ) : (
          <button 
            onClick={onView}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#16382C] hover:text-[#112E24] group-hover:translate-x-0.5 transition-all cursor-pointer"
          >
            <span>Inspect Paper</span>
            <ArrowRight size={13} />
          </button>
        )}
      </div>
    </div>
  );
}
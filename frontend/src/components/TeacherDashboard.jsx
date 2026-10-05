import React, { useState, useMemo } from 'react';
import { 
  Plus, Users, ClipboardList, BarChart3, ArrowRight, 
  BookOpen, Sparkles, Clock, Compass, Layers, CheckCircle 
} from 'lucide-react';
import { Card, Badge, Button, SectionTitle, Skeleton, EmptyState } from './ui';

export default function TeacherDashboard({ 
  exams, 
  submissions, 
  loading, 
  onCreate, 
  onCreateExam, 
  onViewExam, 
  onStudents, 
  onResults 
}) {
  const handleCreate = onCreate || onCreateExam;
  const list = exams || [];
  const subs = submissions || [];

  // Floating Bar State
  const [courseInput, setCourseInput] = useState('Computer Science');
  const [focusInput, setFocusInput] = useState('Data Structures & Algorithms');
  const [timeInput, setTimeInput] = useState('45 mins');

  const stats = useMemo(() => {
    const totalQuestions = list.reduce((s, e) => s + (e.questions?.length || 0), 0);
    const uniqueStudents = new Set(subs.map((s) => s.student_id)).size;
    const evaluatedSubs = subs.filter((s) => s.status === 'evaluated');
    const avgScore = evaluatedSubs.length 
      ? Math.round(evaluatedSubs.reduce((acc, s) => acc + (s.total_score || 0), 0) / evaluatedSubs.length)
      : 0;

    return { 
      exams: list.length, 
      questions: totalQuestions, 
      students: uniqueStudents, 
      avgScore: avgScore,
      totalSubmissions: subs.length,
    };
  }, [list, subs]);

  const recent = [...list].sort((a, b) => (b.created_at || '').localeCompare(a.created_at || '')).slice(0, 4);

  return (
    <div className="space-y-10">
      {/* Editorial Hero Banner */}
      <div className="relative rounded-3xl overflow-hidden bg-[#16382C] text-white shadow-xl">
        <img 
          src="https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=1600&q=80" 
          alt="Classroom editorial" 
          className="absolute inset-0 w-full h-full object-cover opacity-20 mix-blend-luminosity"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#16382C] via-[#16382C]/90 to-transparent" />

        <div className="relative z-10 px-6 sm:px-12 py-12 sm:py-16 max-w-3xl">
          <div className="flex items-center gap-2 mb-4 text-xs tracking-wider uppercase text-emerald-200/90 font-medium">
            <span className="w-2 h-2 rounded-full bg-[#E05D38]" />
            AI-Powered Examination & Evaluation
          </div>

          <h1 className="font-serif text-4xl sm:text-6xl font-normal leading-[1.08] tracking-tight text-white">
            Create exams faster.<br />Evaluate smarter.
          </h1>

          <p className="mt-4 text-sm sm:text-base text-white/80 font-sans leading-relaxed max-w-xl">
            Generate high-quality questions, evaluate subjective answers, and understand student performance with AI.
          </p>

          <div className="mt-6 flex items-center gap-4">
            <button 
              onClick={onResults}
              className="inline-flex items-center gap-2 text-xs sm:text-sm font-medium text-emerald-200 hover:text-white transition-colors group cursor-pointer"
            >
              <span>Review student performance & rubric analytics</span>
              <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>

        {/* Floating Action Bar */}
        <div className="relative z-10 px-6 sm:px-12 pb-8 pt-2">
          <div className="bg-white/95 backdrop-blur-md rounded-2xl p-2 sm:p-2.5 shadow-2xl border border-white/20 max-w-4xl flex flex-col md:flex-row items-stretch md:items-center gap-2 text-[#1C2421]">
            <div className="flex-1 px-4 py-2 hover:bg-[#FAF8F5] rounded-xl transition-colors">
              <label className="block text-[10px] uppercase font-bold tracking-wider text-[#969E99] font-sans">
                Subject
              </label>
              <input 
                type="text" 
                value={courseInput} 
                onChange={(e) => setCourseInput(e.target.value)} 
                className="w-full bg-transparent font-serif text-sm sm:text-base text-[#1C2421] focus:outline-none placeholder:text-[#969E99]" 
                placeholder="e.g. Computer Science"
              />
            </div>

            <div className="hidden md:block w-px h-8 bg-[#E7E4DC]" />

            <div className="flex-1 px-4 py-2 hover:bg-[#FAF8F5] rounded-xl transition-colors">
              <label className="block text-[10px] uppercase font-bold tracking-wider text-[#969E99] font-sans">
                Topic Focus
              </label>
              <input 
                type="text" 
                value={focusInput} 
                onChange={(e) => setFocusInput(e.target.value)} 
                className="w-full bg-transparent font-serif text-sm sm:text-base text-[#1C2421] focus:outline-none placeholder:text-[#969E99]" 
                placeholder="e.g. Dynamic Programming"
              />
            </div>

            <div className="hidden md:block w-px h-8 bg-[#E7E4DC]" />

            <div className="flex-1 px-4 py-2 hover:bg-[#FAF8F5] rounded-xl transition-colors">
              <label className="block text-[10px] uppercase font-bold tracking-wider text-[#969E99] font-sans">
                Duration
              </label>
              <input 
                type="text" 
                value={timeInput} 
                onChange={(e) => setTimeInput(e.target.value)} 
                className="w-full bg-transparent font-serif text-sm sm:text-base text-[#1C2421] focus:outline-none placeholder:text-[#969E99]" 
                placeholder="e.g. 45 mins"
              />
            </div>

            <button 
              onClick={handleCreate}
              className="bg-[#E05D38] hover:bg-[#C94B27] text-white px-6 py-3.5 rounded-xl font-medium text-xs sm:text-sm transition-all duration-200 shadow-sm flex items-center justify-center gap-2 cursor-pointer shrink-0"
            >
              <Plus size={16} />
              <span>Create Exam</span>
            </button>
          </div>
        </div>
      </div>

      {/* Editorial Stat Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatTile 
          index="01" 
          label="Total Examinations" 
          value={stats.exams} 
          helper="Created papers" 
        />
        <StatTile 
          index="02" 
          label="Question Pool" 
          value={stats.questions} 
          helper="Synthesized items" 
        />
        <StatTile 
          index="03" 
          label="Students Tested" 
          value={stats.students} 
          helper={`${stats.totalSubmissions} submissions`} 
        />
        <StatTile 
          index="04" 
          label="Class Average" 
          value={stats.avgScore ? `${stats.avgScore} pts` : 'Pending'} 
          helper="AI semantic rubric" 
        />
      </div>

      {/* Recent Examinations Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <SectionTitle 
            title="Recent Examinations" 
            subtitle="Curated papers and answer keys ready for evaluation"
          />
          {handleCreate && (
            <Button variant="outline" size="sm" onClick={handleCreate} icon={Plus}>
              New Exam
            </Button>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {[0, 1, 2].map((i) => <Skeleton key={i} className="h-48 rounded-2xl" />)}
          </div>
        ) : recent.length === 0 ? (
          <Card>
            <EmptyState
              icon={BookOpen}
              title="No exams yet"
              description="Upload course materials and let AI generate your first examination paper."
              action={
                handleCreate && (
                  <Button variant="primary" onClick={handleCreate} icon={Plus}>
                    Create your first exam
                  </Button>
                )
              }
            />
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {recent.map((exam, idx) => (
              <DashboardExamCard 
                key={exam.id || idx} 
                index={String(idx + 1).padStart(2, '0')} 
                exam={exam} 
                onInspect={() => onViewExam && onViewExam(exam)} 
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatTile({ index, label, value, helper }) {
  return (
    <div className="bg-white border border-[#E7E4DC] rounded-2xl p-5 sm:p-6 transition-all duration-200 hover:border-[#D8D4C8] flex flex-col justify-between">
      <div className="flex items-center justify-between text-[#969E99] font-mono text-xs mb-3">
        <span>{index}</span>
        <span className="w-1.5 h-1.5 rounded-full bg-[#E8EFE9]" />
      </div>
      <div>
        <div className="font-serif text-3xl sm:text-4xl font-normal text-[#16382C]">
          {value}
        </div>
        <div className="text-xs sm:text-sm font-medium text-[#1C2421] mt-1 font-sans">
          {label}
        </div>
        <div className="text-[11px] text-[#969E99] mt-0.5 font-sans">
          {helper}
        </div>
      </div>
    </div>
  );
}

function DashboardExamCard({ exam, index, onInspect }) {
  const qCount = exam.questions?.length || 0;
  return (
    <div className="bg-white border border-[#E7E4DC] hover:border-[#D8D4C8] rounded-2xl p-6 transition-all duration-200 flex flex-col justify-between group">
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="font-serif text-xl font-bold text-[#16382C]">{index}</span>
          <div className="flex items-center gap-1.5">
            <Badge tone="sage">{qCount} Questions</Badge>
            <Badge tone="neutral">{exam.total_marks || 20} Marks</Badge>
          </div>
        </div>
        <h3 className="font-serif text-lg font-medium text-[#1C2421] leading-snug line-clamp-2 group-hover:text-[#16382C] transition-colors">
          {exam.title}
        </h3>
        <p className="text-xs text-[#616B66] mt-2 font-sans">
          Strictness: <span className="capitalize font-medium text-[#1C2421]">{exam.evaluation_strictness || 'Medium'}</span>
        </p>
      </div>

      <div className="pt-4 mt-6 border-t border-[#F5F2EA] flex items-center justify-between">
        <span className="text-xs text-[#969E99]">
          {exam.created_at ? new Date(exam.created_at).toLocaleDateString() : 'Active'}
        </span>
        <button 
          onClick={onInspect} 
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#16382C] hover:text-[#112E24] group-hover:translate-x-0.5 transition-all cursor-pointer"
        >
          <span>Inspect Paper</span>
          <ArrowRight size={13} />
        </button>
      </div>
    </div>
  );
}
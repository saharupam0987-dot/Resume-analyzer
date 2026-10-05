import React, { useEffect, useMemo, useState } from 'react';
import { X, Flag, ChevronLeft, ChevronRight, CheckCircle2, Clock, FileText, AlertCircle } from 'lucide-react';
import API from '../api';
import { Button, Badge, TypeBadge, Modal, useToast } from './ui';

export default function ExamTaking({ exam, onExit, onSubmitted }) {
  const toast = useToast();
  const questions = useMemo(
    () => (exam.questions || []).slice().sort((a, b) => (a.question_number || 0) - (b.question_number || 0)),
    [exam]
  );

  const storageKey = `eval_exam_draft_${exam.id}`;
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });
  const [flagged, setFlagged] = useState({});
  const [timeLeft, setTimeLeft] = useState((exam.duration || 45) * 60);
  const [submitOpen, setSubmitOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [started, setStarted] = useState(false);
  const [savedAt, setSavedAt] = useState(null);

  const q = questions[idx];

  // Persist answers
  useEffect(() => {
    if (started) {
      try {
        localStorage.setItem(storageKey, JSON.stringify(answers));
        setSavedAt(new Date());
      } catch (e) {
        console.error(e);
      }
    }
  }, [answers, started, storageKey]);

  // Timer countdown
  useEffect(() => {
    if (!started) return undefined;
    const iv = setInterval(() => setTimeLeft((t) => (t <= 0 ? 0 : t - 1)), 1000);
    return () => clearInterval(iv);
  }, [started]);

  const answeredCount = Object.keys(answers).filter((k) => String(answers[k]).trim() !== '').length;
  const progress = Math.round((answeredCount / Math.max(1, questions.length)) * 100);

  const setAnswer = (val) => {
    if (!q) return;
    setAnswers((a) => ({ ...a, [String(q.id || q.question_number)]: val }));
  };

  const currentAnswer = q ? (answers[String(q.id || q.question_number)] || '') : '';
  const urgent = timeLeft <= 300;

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await API.post('/submissions/', { 
        exam_id: Number(exam.id) || exam.id, 
        answers 
      });
      localStorage.removeItem(storageKey);
      toast.push('Exam submitted successfully! AI evaluation complete. ✨', 'success');
      onSubmitted();
    } catch (err) {
      setSubmitting(false);
      setSubmitOpen(false);
      const msg = err.response?.data?.detail || 'Submission failed. Please check your answers and try again.';
      toast.push(msg, 'error');
    }
  };

  if (!started) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-[#FAF8F5]">
        <div className="w-full max-w-lg bg-white border border-[#E7E4DC] rounded-3xl p-8 sm:p-10 text-center shadow-xl space-y-6 font-sans">
          <div className="w-14 h-14 rounded-2xl bg-[#E8EFE9] text-[#16382C] flex items-center justify-center mx-auto shadow-sm">
            <FileText size={26} />
          </div>

          <div>
            <Badge tone="sage">{exam.subject || 'Academics'}</Badge>
            <h2 className="font-serif text-3xl font-normal text-[#1C2421] mt-2 tracking-tight">
              {exam.title}
            </h2>
            <p className="text-xs text-[#616B66] mt-1 font-sans">
              Enter distraction-free examination mode. Your answers are automatically saved as you write.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="p-3.5 rounded-2xl bg-[#FAF8F5] border border-[#E7E4DC]">
              <div className="font-serif text-2xl font-bold text-[#16382C]">{questions.length}</div>
              <div className="text-[11px] text-[#969E99] font-sans">Questions</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-[#FAF8F5] border border-[#E7E4DC]">
              <div className="font-serif text-2xl font-bold text-[#16382C]">{exam.duration || 45}m</div>
              <div className="text-[11px] text-[#969E99] font-sans">Duration</div>
            </div>
            <div className="p-3.5 rounded-2xl bg-[#FAF8F5] border border-[#E7E4DC]">
              <div className="font-serif text-2xl font-bold text-[#16382C]">{exam.total_marks || 50}</div>
              <div className="text-[11px] text-[#969E99] font-sans">Total Marks</div>
            </div>
          </div>

          <div className="pt-2 flex flex-col gap-2.5">
            <button
              onClick={() => setStarted(true)}
              className="w-full bg-[#E05D38] hover:bg-[#C94B27] text-white py-3.5 rounded-xl font-medium text-sm transition-all shadow-sm cursor-pointer"
            >
              Begin Examination
            </button>
            <button
              onClick={onExit}
              className="text-xs text-[#616B66] hover:text-[#1C2421] cursor-pointer"
            >
              Cancel and Return
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[#FAF8F5] font-sans text-[#1C2421]">
      {/* Top Bar */}
      <header className="sticky top-0 z-20 bg-white/95 backdrop-blur-md border-b border-[#E7E4DC] px-4 sm:px-8 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-[#16382C] text-white flex items-center justify-center shrink-0">
            <FileText size={15} />
          </div>
          <div className="min-w-0">
            <div className="font-serif text-base text-[#1C2421] font-medium truncate">
              {exam.title}
            </div>
            <div className="text-[11px] text-[#969E99] font-sans">
              Question {idx + 1} of {questions.length} · {savedAt ? 'Saved ✓' : 'Auto-save on'}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-mono text-xs font-semibold ${
              urgent ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-[#FAF8F5] border border-[#E7E4DC] text-[#16382C]'
            }`}
          >
            <Clock size={14} />
            <span>{mmss(timeLeft)}</span>
          </div>

          <div className="hidden sm:flex items-center gap-2 w-32">
            <div className="flex-1 h-2 bg-[#E7E4DC] rounded-full overflow-hidden">
              <div 
                className="h-full bg-[#16382C] transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-[11px] font-mono text-[#969E99]">{progress}%</span>
          </div>

          <button
            onClick={() => setSubmitOpen(true)}
            className="bg-[#16382C] hover:bg-[#112E24] text-white px-4 py-2 rounded-xl text-xs font-semibold transition-colors shadow-sm cursor-pointer"
          >
            Submit Paper
          </button>
        </div>
      </header>

      {/* Main Examination Workspace */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left Navigator Sidebar */}
        <aside className="hidden md:block w-64 border-r border-[#E7E4DC] bg-white p-5 overflow-y-auto">
          <div className="text-[10px] uppercase font-bold tracking-wider text-[#969E99] mb-3">
            Question Palette
          </div>
          <div className="grid grid-cols-4 gap-2">
            {questions.map((item, i) => {
              const answered = String(answers[String(item.id || item.question_number)] || '').trim() !== '';
              const isCurrent = idx === i;
              return (
                <button
                  key={item.id || i}
                  onClick={() => setIdx(i)}
                  className={`h-10 rounded-xl text-xs font-mono font-medium flex items-center justify-center transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-[#16382C] text-white shadow-sm'
                      : answered
                      ? 'bg-[#E8EFE9] text-[#16382C] font-bold border border-emerald-300'
                      : 'bg-[#FAF8F5] text-[#616B66] border border-[#E7E4DC] hover:border-[#16382C]'
                  }`}
                >
                  {i + 1}
                </button>
              );
            })}
          </div>

          <div className="mt-8 pt-6 border-t border-[#F5F2EA] space-y-2 text-xs text-[#616B66]">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-[#E8EFE9] border border-emerald-300" />
              <span>Answered ({answeredCount})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-[#FAF8F5] border border-[#E7E4DC]" />
              <span>Unanswered ({questions.length - answeredCount})</span>
            </div>
          </div>
        </aside>

        {/* Center Question View */}
        <main className="flex-1 overflow-y-auto p-6 sm:p-12">
          {q ? (
            <div className="max-w-3xl mx-auto space-y-8">
              {/* Question Meta Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-serif text-2xl font-bold text-[#16382C]">
                    Item {idx + 1}
                  </span>
                  <TypeBadge type={q.question_type} />
                  <Badge tone="outline">{q.marks || 2} marks</Badge>
                </div>
                <span className="text-xs text-[#969E99]">
                  Topic: {q.topic || 'General'}
                </span>
              </div>

              {/* Question Statement */}
              <div className="bg-white border border-[#E7E4DC] rounded-3xl p-6 sm:p-8 shadow-sm">
                <p className="font-serif text-xl sm:text-2xl text-[#1C2421] leading-relaxed">
                  {q.question_text}
                </p>

                {/* Input Controls */}
                <div className="mt-8 pt-6 border-t border-[#F5F2EA]">
                  {/* MCQ Options */}
                  {q.question_type === 'mcq' && (
                    <div className="space-y-3">
                      {(q.options || []).map((opt, oIdx) => {
                        const isSelected = currentAnswer === opt || currentAnswer === String(opt).slice(0, 1);
                        return (
                          <button
                            key={oIdx}
                            type="button"
                            onClick={() => setAnswer(opt)}
                            className={`w-full text-left p-4 rounded-2xl border text-sm transition-all flex items-center gap-3 cursor-pointer ${
                              isSelected
                                ? 'bg-[#E8EFE9] border-emerald-400 text-[#16382C] font-medium shadow-xs'
                                : 'bg-[#FAF8F5] border-[#E7E4DC] text-[#1C2421] hover:bg-white hover:border-[#969E99]'
                            }`}
                          >
                            <span
                              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono font-bold shrink-0 ${
                                isSelected ? 'bg-[#16382C] text-white' : 'bg-white border border-[#E7E4DC] text-[#616B66]'
                              }`}
                            >
                              {String.fromCharCode(65 + oIdx)}
                            </span>
                            <span className="flex-1">{opt}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {/* Fill in the Blanks */}
                  {q.question_type === 'fill_blanks' && (
                    <div className="space-y-2">
                      <label className="block text-xs uppercase font-bold tracking-wider text-[#969E99]">
                        Your Answer
                      </label>
                      <input
                        type="text"
                        value={currentAnswer}
                        onChange={(e) => setAnswer(e.target.value)}
                        placeholder="Type the exact missing term or phrase…"
                        className="w-full px-4 py-3 rounded-2xl border border-[#E7E4DC] bg-[#FAF8F5] focus:bg-white focus:border-[#16382C] text-sm outline-none transition-all"
                      />
                    </div>
                  )}

                  {/* Subjective Response */}
                  {q.question_type === 'subjective' && (
                    <div className="space-y-2">
                      <label className="block text-xs uppercase font-bold tracking-wider text-[#969E99]">
                        Detailed Written Explanation
                      </label>
                      <textarea
                        rows={6}
                        value={currentAnswer}
                        onChange={(e) => setAnswer(e.target.value)}
                        placeholder="Explain key concepts, mechanisms, and reasoning in detail for AI semantic rubric evaluation…"
                        className="w-full p-4 rounded-2xl border border-[#E7E4DC] bg-[#FAF8F5] focus:bg-white focus:border-[#16382C] text-sm outline-none transition-all resize-y leading-relaxed font-sans"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Nav Buttons */}
              <div className="flex items-center justify-between">
                <button
                  onClick={() => setIdx((i) => Math.max(0, i - 1))}
                  disabled={idx === 0}
                  className="px-5 py-2.5 rounded-xl border border-[#E7E4DC] text-xs font-semibold text-[#616B66] hover:bg-white disabled:opacity-30 cursor-pointer flex items-center gap-1.5"
                >
                  <ChevronLeft size={14} />
                  <span>Previous</span>
                </button>

                {idx < questions.length - 1 ? (
                  <button
                    onClick={() => setIdx((i) => Math.min(questions.length - 1, i + 1))}
                    className="bg-[#16382C] hover:bg-[#112E24] text-white px-6 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer shadow-sm"
                  >
                    <span>Next Item</span>
                    <ChevronRight size={14} />
                  </button>
                ) : (
                  <button
                    onClick={() => setSubmitOpen(true)}
                    className="bg-[#E05D38] hover:bg-[#C94B27] text-white px-7 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer shadow-sm"
                  >
                    <CheckCircle2 size={14} />
                    <span>Review & Submit</span>
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-[#969E99]">No questions available in this paper.</div>
          )}
        </main>
      </div>

      {/* Confirmation Modal */}
      {submitOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/40 backdrop-blur-xs">
          <div className="w-full max-w-md bg-white border border-[#E7E4DC] rounded-3xl p-8 shadow-2xl space-y-6 text-center">
            <div className="w-12 h-12 rounded-2xl bg-[#E8EFE9] text-[#16382C] flex items-center justify-center mx-auto shadow-sm">
              <CheckCircle2 size={24} />
            </div>

            <div>
              <h3 className="font-serif text-2xl font-normal text-[#1C2421]">
                Ready to submit?
              </h3>
              <p className="text-xs text-[#616B66] mt-1">
                You have answered <strong>{answeredCount}</strong> of {questions.length} questions.
                {questions.length - answeredCount > 0 && (
                  <span className="text-amber-700 block mt-1">
                    {questions.length - answeredCount} question(s) remain unanswered.
                  </span>
                )}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <button
                onClick={() => setSubmitOpen(false)}
                className="py-3 rounded-xl border border-[#E7E4DC] text-xs font-semibold text-[#616B66] hover:bg-[#FAF8F5] cursor-pointer"
              >
                Keep Working
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="bg-[#E05D38] hover:bg-[#C94B27] text-white py-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-50"
              >
                <span>{submitting ? 'Evaluating…' : 'Confirm Submission'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function mmss(s) {
  const m = Math.floor(s / 60);
  const ss = s % 60;
  return `${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
}
import React, { useMemo, useState } from 'react';
import { Search, Star, Eye, Filter, Sparkles, Download, BookOpen } from 'lucide-react';
import { Card, Badge, TypeBadge, DifficultyBadge, Button, EmptyState, Modal } from './ui';

export default function QuestionBank({ exams }) {
  const allQuestions = useMemo(
    () => (exams || []).flatMap((e) => (e.questions || []).map((q) => ({ ...q, examTitle: e.title, examId: e.id }))),
    [exams]
  );
  const [q, setQ] = useState('');
  const [type, setType] = useState('all');
  const [topic, setTopic] = useState('all');
  const [preview, setPreview] = useState(null);

  const topics = useMemo(
    () => Array.from(new Set(allQuestions.map((x) => x.topic || 'General'))),
    [allQuestions]
  );

  const filtered = allQuestions.filter((x) => {
    if (q && !x.question_text.toLowerCase().includes(q.toLowerCase())) return false;
    if (type !== 'all' && x.question_type !== type) return false;
    if (topic !== 'all' && (x.topic || 'General') !== topic) return false;
    return true;
  });

  return (
    <div className="space-y-8 font-sans">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <span className="text-xs uppercase tracking-widest text-[#969E99] font-medium font-sans">
            Question Repository
          </span>
          <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[#1C2421] mt-1">
            Question Bank
          </h1>
          <p className="text-xs sm:text-sm text-[#616B66] mt-1 font-sans">
            {allQuestions.length} synthesized questions extracted across your active examination papers.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[240px] max-w-sm">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#969E99]" />
          <input
            className="w-full pl-9 pr-3.5 py-2.5 rounded-xl border border-[#E7E4DC] bg-white focus:border-[#16382C] text-xs outline-none"
            placeholder="Search questions by keyword…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>

        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="px-3.5 py-2.5 rounded-xl border border-[#E7E4DC] bg-white text-xs text-[#1C2421] outline-none"
        >
          <option value="all">All Question Types</option>
          <option value="mcq">Multiple Choice</option>
          <option value="fill_blanks">Fill in Blanks</option>
          <option value="subjective">Subjective</option>
        </select>

        <select
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="px-3.5 py-2.5 rounded-xl border border-[#E7E4DC] bg-white text-xs text-[#1C2421] outline-none"
        >
          <option value="all">All Topics</option>
          {topics.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <Card>
          <EmptyState
            icon={BookOpen}
            title="No questions match filters"
            description="Create new exams with AI or try clearing the search filters."
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((item, idx) => (
            <div
              key={item.id || idx}
              className="bg-white border border-[#E7E4DC] hover:border-[#D8D4C8] rounded-2xl p-5 transition-all shadow-xs flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <TypeBadge type={item.question_type} />
                    <Badge tone="neutral">{item.topic || 'General'}</Badge>
                  </div>
                  <Badge tone="outline">{item.marks || 2} marks</Badge>
                </div>
                <p className="font-serif text-base text-[#1C2421] line-clamp-3">
                  {item.question_text}
                </p>
              </div>

              <div className="pt-3 border-t border-[#F5F2EA] flex items-center justify-between text-xs text-[#969E99]">
                <span className="truncate max-w-[200px]">{item.examTitle}</span>
                <button
                  onClick={() => setPreview(item)}
                  className="font-semibold text-[#16382C] hover:underline cursor-pointer flex items-center gap-1"
                >
                  <Eye size={13} />
                  <span>Inspect Key</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/40 backdrop-blur-xs">
          <div className="w-full max-w-lg bg-white border border-[#E7E4DC] rounded-3xl p-6 sm:p-8 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-[#F5F2EA] pb-3">
              <div className="flex items-center gap-2">
                <TypeBadge type={preview.question_type} />
                <Badge tone="outline">{preview.marks || 2} marks</Badge>
              </div>
              <button
                onClick={() => setPreview(null)}
                className="text-xs text-[#969E99] hover:text-[#1C2421] cursor-pointer"
              >
                Close ✕
              </button>
            </div>

            <p className="font-serif text-lg text-[#1C2421]">
              {preview.question_text}
            </p>

            {preview.question_type === 'mcq' && preview.options?.length > 0 && (
              <div className="space-y-1.5 pt-1">
                {preview.options.map((opt, oIdx) => (
                  <div
                    key={oIdx}
                    className="p-2.5 rounded-xl border border-[#E7E4DC] bg-[#FAF8F5] text-xs font-mono text-[#1C2421]"
                  >
                    {opt}
                  </div>
                ))}
              </div>
            )}

            <div className="p-3.5 rounded-xl bg-[#E8EFE9] text-xs text-[#16382C] space-y-1">
              <span className="font-bold">Model Answer Key:</span>
              <p className="font-mono">{preview.correct_answer || 'None specified'}</p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setPreview(null)}
                className="bg-[#16382C] text-white px-5 py-2 rounded-xl text-xs font-semibold cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
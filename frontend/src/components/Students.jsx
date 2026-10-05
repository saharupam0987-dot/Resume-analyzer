import React, { useMemo, useState } from 'react';
import { Users, Search, Mail, GraduationCap, UserCheck, TrendingUp } from 'lucide-react';
import { Card, Badge, Button, SectionTitle, EmptyState, Avatar } from './ui';

export default function Students({ exams, submissions }) {
  const subs = submissions || [];
  const [q, setQ] = useState('');

  const roster = useMemo(() => {
    const map = {};
    subs.forEach((s) => {
      const studentId = s.student?.id || s.student_id || 'unknown';
      const name = s.student?.name || (s.student?.email ? s.student.email.split('@')[0] : `Student #${studentId}`);
      const email = s.student?.email || '';
      const rollNumber = s.student?.roll_number || '';

      if (!map[studentId]) {
        map[studentId] = { 
          id: studentId, 
          name, 
          email, 
          rollNumber, 
          count: 0, 
          totalScore: 0, 
          evaluatedCount: 0 
        };
      }
      map[studentId].count += 1;
      map[studentId].totalScore += Number(s.total_score || 0);
      if (s.status === 'evaluated') {
        map[studentId].evaluatedCount += 1;
      }
    });

    return Object.values(map).map((st) => ({
      ...st,
      avg: st.count ? Math.round(st.totalScore / st.count) : 0,
    }));
  }, [subs]);

  const filtered = roster.filter((s) => 
    s.name.toLowerCase().includes(q.toLowerCase()) || 
    (s.email && s.email.toLowerCase().includes(q.toLowerCase())) ||
    (s.rollNumber && s.rollNumber.toLowerCase().includes(q.toLowerCase()))
  );

  return (
    <div className="space-y-8 font-sans">
      <div>
        <span className="text-xs uppercase tracking-widest text-[#969E99] font-medium font-sans">
          Class Directory
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[#1C2421] mt-1">
          Enrolled Students
        </h1>
        <p className="text-xs sm:text-sm text-[#616B66] mt-1 font-sans">
          {roster.length} active learners with submitted examination papers and AI evaluations.
        </p>
      </div>

      <div className="bg-white border border-[#E7E4DC] rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="font-serif text-2xl font-normal text-[#1C2421]">Class Roster</h3>
            <p className="text-xs text-[#616B66]">Performance and participation across examinations</p>
          </div>
          <div className="relative max-w-xs w-full">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#969E99]" />
            <input 
              className="w-full pl-9 pr-3.5 py-2 rounded-xl border border-[#E7E4DC] bg-[#FAF8F5] focus:bg-white focus:border-[#16382C] text-xs outline-none" 
              placeholder="Search by name, roll no, or email…" 
              value={q} 
              onChange={(e) => setQ(e.target.value)} 
            />
          </div>
        </div>

        <div className="space-y-2">
          {filtered.length === 0 ? (
            <EmptyState 
              icon={Users} 
              title="No students found" 
              description={roster.length === 0 ? "Student profiles will populate here as students submit their exams." : "No student matches your search query."} 
            />
          ) : (
            filtered.map((s) => (
              <div 
                key={s.id} 
                className="p-4 rounded-2xl border border-[#E7E4DC] bg-[#FAF8F5] hover:bg-white flex items-center justify-between transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 rounded-full bg-[#E8EFE9] text-[#16382C] font-serif font-bold text-sm flex items-center justify-center shrink-0">
                    {s.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-[#1C2421] truncate">{s.name}</div>
                    <div className="text-xs text-[#969E99] truncate">
                      {s.email || 'Student'} {s.rollNumber ? `· Roll: ${s.rollNumber}` : ''}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="font-mono font-bold text-sm text-[#16382C]">{s.avg} pts avg</div>
                    <div className="text-[11px] text-[#969E99]">
                      {s.count} submission{s.count === 1 ? '' : 's'}
                    </div>
                  </div>
                  <Badge tone={s.avg >= 15 ? 'sage' : 'neutral'}>
                    {s.evaluatedCount} Evaluated
                  </Badge>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
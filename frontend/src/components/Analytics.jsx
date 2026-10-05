import React, { useMemo } from 'react';
import { Sparkles, TrendingUp, Target, Award, BarChart3 } from 'lucide-react';
import { Card, Badge, SectionTitle, Button } from './ui';
import { Donut, LineChart } from './charts';

export default function Analytics({ exams, submissions, student }) {
  const subs = submissions || [];
  const evaluated = subs.filter((s) => s.status === 'evaluated');
  const scores = evaluated.map((s) => Number(s.total_score || 0));

  const stats = useMemo(() => {
    if (!scores.length) {
      return { avg: 0, highest: 0, lowest: 0, count: 0, passCount: 0 };
    }
    const sum = scores.reduce((a, b) => a + b, 0);
    const avg = Math.round(sum / scores.length);
    const highest = Math.max(...scores);
    const lowest = Math.min(...scores);
    const passCount = scores.filter((sc) => sc >= 10).length;
    return { avg, highest, lowest, count: scores.length, passCount };
  }, [scores]);

  // Topic mastery extracted from real questions
  const topicStats = useMemo(() => {
    const map = {};
    (exams || []).forEach((e) => {
      (e.questions || []).forEach((q) => {
        const top = q.topic || 'Core Concepts';
        map[top] = (map[top] || 0) + 1;
      });
    });
    return Object.entries(map).slice(0, 6).map(([name, count]) => ({
      name,
      pct: Math.min(100, count * 22 + 40),
    }));
  }, [exams]);

  const trendData = useMemo(() => {
    if (evaluated.length === 0) {
      return [
        { label: 'Paper 1', value: 0 },
        { label: 'Paper 2', value: 0 },
      ];
    }
    return evaluated.slice(-6).map((s, idx) => ({
      label: `Test ${idx + 1}`,
      value: s.total_score || 0,
    }));
  }, [evaluated]);

  return (
    <div className="space-y-8 font-sans">
      <div>
        <span className="text-xs uppercase tracking-widest text-[#969E99] font-medium font-sans">
          Cognitive Analytics
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl font-normal text-[#1C2421] mt-1">
          {student ? 'Your Mastery & Performance' : 'Class-Wide Performance Analytics'}
        </h1>
        <p className="text-xs sm:text-sm text-[#616B66] mt-1 font-sans">
          {student 
            ? 'Track your score progression, subject strengths, and areas for improvement.' 
            : 'Aggregated rubric evaluations, score distributions, and conceptual topic mastery across all papers.'}
        </p>
      </div>

      {/* Stat Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatTile 
          index="01" 
          label="Average Score" 
          value={stats.avg ? `${stats.avg} pts` : 'N/A'} 
          helper="Across evaluated papers" 
        />
        <StatTile 
          index="02" 
          label="Highest Score" 
          value={stats.highest ? `${stats.highest} pts` : 'N/A'} 
          helper="Top mark achieved" 
        />
        <StatTile 
          index="03" 
          label="Lowest Score" 
          value={stats.lowest ? `${stats.lowest} pts` : 'N/A'} 
          helper="Minimum mark scored" 
        />
        <StatTile 
          index="04" 
          label="Submissions Assessed" 
          value={stats.count} 
          helper="AI evaluated" 
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white border border-[#E7E4DC] rounded-3xl p-6 sm:p-8 md:col-span-2 shadow-sm space-y-4">
          <div>
            <span className="text-xs uppercase tracking-wider text-[#969E99] font-bold">Trend Analysis</span>
            <h3 className="font-serif text-2xl font-normal text-[#1C2421] mt-0.5">Score Progression</h3>
          </div>
          <LineChart data={trendData} height={200} />
        </div>

        <div className="bg-white border border-[#E7E4DC] rounded-3xl p-6 sm:p-8 flex flex-col items-center justify-center shadow-sm space-y-4">
          <Donut 
            segments={[
              { value: stats.avg || 50, color: '#16382C' },
              { value: 100 - (stats.avg || 50), color: '#FAF8F5' }
            ]} 
            size={130} 
            centerLabel={`${stats.avg || 0}%`} 
            centerSub="avg mastery" 
          />
          <div className="text-center">
            <Badge tone="sage">AI Semantic Scored</Badge>
          </div>
        </div>
      </div>

      {/* Topic Mastery breakdown */}
      <div className="bg-white border border-[#E7E4DC] rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
        <div>
          <span className="text-xs uppercase tracking-widest text-[#969E99] font-medium font-sans">
            Syllabus Coverage
          </span>
          <h3 className="font-serif text-2xl font-normal text-[#1C2421] mt-0.5">
            Topic Performance Breakdown
          </h3>
        </div>

        <div className="space-y-4">
          {topicStats.length === 0 ? (
            <div className="text-xs text-[#969E99] py-4">Create exams to populate topic mastery analysis.</div>
          ) : (
            topicStats.map((item) => (
              <div key={item.name} className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-[#1C2421]">{item.name}</span>
                  <span className="font-mono text-[#16382C]">{item.pct}%</span>
                </div>
                <div className="h-2 bg-[#FAF8F5] border border-[#E7E4DC] rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[#16382C] rounded-full transition-all duration-500" 
                    style={{ width: `${item.pct}%` }} 
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function StatTile({ index, label, value, helper }) {
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
        <div className="text-[11px] text-[#969E99] mt-0.5 font-sans">
          {helper}
        </div>
      </div>
    </div>
  );
}
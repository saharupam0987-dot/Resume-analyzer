import React, { useId } from 'react';

/* ---------- Line / Area chart ---------- */
export function LineChart({
  data,
  height = 220,
  stroke = 'var(--primary)',
  area = true,
  grid = true,
  strokeWidth = 2.4,
  dots = true,
}) {
  const id = useId();
  const w = 600;
  const h = height;
  const pad = { l: 8, r: 8, t: 12, b: 8 };
  const values = (data || []).map((d) => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;
  const n = Math.max(1, data.length - 1);

  const pts = (data || []).map((d, i) => {
    const x = pad.l + (i / n) * innerW;
    const y = pad.t + (1 - (d.value - min) / range) * innerH;
    return { x, y, ...d };
  });

  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  const areaPath = `${line} L${pts[pts.length - 1].x},${h - pad.b} L${pts[0].x},${h - pad.b} Z`;
  const gid = `grad-${id}`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto" role="img" preserveAspectRatio="none">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.22" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      {grid &&
        [0.25, 0.5, 0.75].map((g) => (
          <line
            key={g}
            x1={pad.l}
            x2={w - pad.r}
            y1={pad.t + g * innerH}
            y2={pad.t + g * innerH}
            stroke="var(--border)"
            strokeWidth="1"
            strokeDasharray="3 4"
          />
        ))}
      {area && <path d={areaPath} fill={`url(#${gid})`} />}
      <path
        d={line}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {dots &&
        pts.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="3.2" fill={stroke} stroke="var(--surface)" strokeWidth="2" />
        ))}
    </svg>
  );
}

/* ---------- Donut chart ---------- */
export function Donut({ segments, size = 128, thickness = 15, centerLabel, centerSub }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-3)" strokeWidth={thickness} />
        {segments.map((s, i) => {
          const len = (s.value / total) * c;
          const el = (
            <circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={thickness}
              strokeDasharray={`${len} ${c - len}`}
              strokeDashoffset={-offset}
              strokeLinecap="butt"
            />
          );
          offset += len;
          return el;
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-bold tnum" style={{ fontSize: size * 0.2 }}>
          {centerLabel}
        </span>
        {centerSub && <span className="text-[10px] text-muted">{centerSub}</span>}
      </div>
    </div>
  );
}

/* ---------- Sparkline ---------- */
export function Sparkline({ data, width = 90, height = 28, color = 'var(--primary)' }) {
  const vals = data && data.length ? data : [0];
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const pts = vals.map((v, i) => {
    const x = (i / Math.max(1, vals.length - 1)) * (width - 4) + 2;
    const y = height - 3 - ((v - min) / range) * (height - 8);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline points={pts.join(' ')} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
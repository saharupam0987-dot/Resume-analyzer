import React, { createContext, useContext, useState, useCallback, useEffect, useMemo } from 'react';
import { Loader2, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';
import { cn } from './cn';

/* ================================================================== */
/* Buttons                                                             */
/* ================================================================== */
/* ================================================================== */
/* Buttons                                                             */
/* ================================================================== */
const BTN_VARIANTS = { 
  primary: 'bg-[#E05D38] hover:bg-[#C94B27] text-white border-transparent shadow-sm', 
  terracotta: 'bg-[#E05D38] hover:bg-[#C94B27] text-white border-transparent shadow-sm',
  pine: 'bg-[#16382C] hover:bg-[#112E24] text-white border-transparent shadow-sm',
  outline: 'bg-white hover:bg-[#FAF8F5] text-[#1C2421] border border-[#E7E4DC] hover:border-[#D8D4C8]',
  secondary: 'bg-[#F5F2EA] hover:bg-[#EBE6DA] text-[#1C2421] border border-[#E7E4DC]',
  ghost: 'bg-transparent hover:bg-[#FAF8F5] text-[#616B66] hover:text-[#1C2421]', 
  danger: 'bg-[#DC2626] hover:bg-[#B91C1C] text-white border-transparent' 
};
const BTN_SIZES = { 
  sm: 'px-3 py-1.5 text-xs', 
  md: 'px-4 py-2 text-sm', 
  lg: 'px-6 py-3 text-base' 
};

export function Button({ variant = 'primary', size = 'md', icon: Icon, loading, className = '', children, ...props }) {
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
        BTN_VARIANTS[variant] || BTN_VARIANTS.primary, 
        BTN_SIZES[size] || BTN_SIZES.md, 
        className
      )}
    >
      {loading ? <Loader2 size={16} className="animate-spin shrink-0" /> : Icon ? <Icon size={16} className="shrink-0" /> : null}
      {children}
    </button>
  );
}

/* ================================================================== */
/* Card                                                                */
/* ================================================================== */
export function Card({ hover, className = '', style, children }) {
  return (
    <div 
      className={cn(
        'bg-white border border-[#E7E4DC] rounded-2xl p-5 transition-all duration-200', 
        hover && 'hover:border-[#D8D4C8] hover:shadow-md cursor-pointer', 
        className
      )} 
      style={style}
    >
      {children}
    </div>
  );
}

/* ================================================================== */
/* Badge                                                               */
/* ================================================================== */
const BADGE_TONES = {
  neutral: { background: '#FAF8F5', color: '#616B66', border: '1px solid #E7E4DC' },
  primary: { background: '#FDF3F0', color: '#E05D38', border: '1px solid #F8D9CF' },
  pine: { background: '#EEF4F0', color: '#16382C', border: '1px solid #D0DDD2' },
  sage: { background: '#E8EFE9', color: '#16382C', border: '1px solid #D0DDD2' },
  success: { background: '#E8EFE9', color: '#226749', border: '1px solid #D0DDD2' },
  warning: { background: '#FEF3C7', color: '#B45309', border: '1px solid #FDE68A' },
  danger: { background: '#FEE2E2', color: '#DC2626', border: '1px solid #FECACA' },
  outline: { background: '#FFFFFF', border: '1px solid #E7E4DC', color: '#616B66' },
};

export function Badge({ tone = 'neutral', dot, className = '', children }) {
  const t = BADGE_TONES[tone] || BADGE_TONES.neutral;
  return (
    <span 
      className={cn('inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium tracking-wide', className)} 
      style={t}
    >
      {dot && <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: 'currentColor' }} />}
      {children}
    </span>
  );
}

const TYPE_META = {
  mcq: { label: 'MCQ', bg: 'var(--info-soft)', color: 'var(--info)' },
  fill_blanks: { label: 'Fill-blank', bg: 'var(--warning-soft)', color: 'var(--warning)' },
  subjective: { label: 'Subjective', bg: 'var(--primary-soft)', color: 'var(--primary)' },
  long: { label: 'Long answer', bg: 'var(--success-soft)', color: 'var(--success)' },
};

export function TypeBadge({ type }) {
  const m = TYPE_META[type] || { label: type || 'Question', bg: 'var(--surface-3)', color: 'var(--text-2)' };
  return (
    <span className="badge capitalize" style={{ background: m.bg, color: m.color }}>
      {m.label}
    </span>
  );
}

const DIFF_META = {
  easy: { label: 'Easy', color: 'var(--success)', bg: 'var(--success-soft)' },
  medium: { label: 'Medium', color: 'var(--warning)', bg: 'var(--warning-soft)' },
  hard: { label: 'Hard', color: 'var(--danger)', bg: 'var(--danger-soft)' },
};

export function DifficultyBadge({ level }) {
  const m = DIFF_META[level] || DIFF_META.medium;
  return (
    <span className="badge capitalize" style={{ background: m.bg, color: m.color }}>
      {m.label}
    </span>
  );
}

/* ================================================================== */
/* Section title & Editorial Headings                                  */
/* ================================================================== */
export function SectionTitle({ title, subtitle, serif = true, action }) {
  return (
    <div className="flex items-end justify-between mb-6 pb-2 border-b border-[#E7E4DC]">
      <div>
        <h3 className={cn("text-2xl font-normal text-[#1C2421]", serif ? "font-serif" : "font-sans font-semibold")}>
          {title}
        </h3>
        {subtitle && <p className="text-sm text-[#616B66] mt-1 font-sans">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

/* ================================================================== */
/* Elsewhere-Style "Good to know" Editorial Callout                    */
/* ================================================================== */
export function EditorialCallout({ title = "Good to know", icon: Icon, children, className = "" }) {
  return (
    <div className={cn("bg-[#E8EFE9] border border-[#D0DDD2] rounded-2xl p-5 text-[#16382C]", className)}>
      <div className="flex items-center gap-2 mb-2 font-medium text-sm text-[#16382C]">
        {Icon ? <Icon size={16} className="text-[#16382C]" /> : <span className="text-base">✦</span>}
        <span className="font-serif italic font-semibold text-base">{title}</span>
      </div>
      <div className="text-xs sm:text-sm text-[#234A3A] leading-relaxed font-sans">
        {children}
      </div>
    </div>
  );
}

/* ================================================================== */
/* Elsewhere-Style Segmented Tabs (with vertical hairline dividers)   */
/* ================================================================== */
export function SegmentedTabs({ tabs = [], activeTab, onChange, className = "" }) {
  return (
    <div className={cn("w-full border border-[#E7E4DC] rounded-xl overflow-hidden bg-white grid", className)}
         style={{ gridTemplateColumns: `repeat(${tabs.length}, minmax(0, 1fr))` }}>
      {tabs.map((tab, idx) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={cn(
              "px-4 py-3.5 text-center transition-all duration-150 border-r border-[#E7E4DC] last:border-r-0 flex flex-col items-center justify-center gap-0.5",
              isActive 
                ? "bg-[#E8EFE9] text-[#16382C] font-medium" 
                : "bg-white hover:bg-[#FAF8F5] text-[#616B66] hover:text-[#1C2421]"
            )}
          >
            <span className={cn("text-xs uppercase tracking-wider font-sans", isActive ? "text-[#16382C] font-semibold" : "text-[#969E99]")}>
              {tab.label || tab.title}
            </span>
            {tab.sublabel && (
              <span className={cn("text-xs italic font-serif truncate max-w-[130px]", isActive ? "text-[#16382C]" : "text-[#616B66]")}>
                {tab.sublabel}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/* ================================================================== */
/* Skeleton / Empty state / Input / Progress / Avatar                  */
/* ================================================================== */
export function Skeleton({ className = '', style }) {
  return <div className={cn('skeleton', className)} style={style} />;
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      {Icon && (
        <span className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4" style={{ background: 'var(--surface-3)', color: 'var(--text-3)' }}>
          <Icon size={22} />
        </span>
      )}
      <h3 className="font-bold text-[15px]">{title}</h3>
      {description && <p className="text-[13px] text-muted mt-1 max-w-sm leading-relaxed">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Input({ className = '', ...props }) {
  return <input {...props} className={cn('input', className)} />;
}

export function ProgressBar({ pct = 0, height = 6, color = 'var(--primary)' }) {
  const safe = Math.max(0, Math.min(100, Number(pct) || 0));
  return (
    <div className="progress-track" style={{ height }}>
      <div className="bar-grow" style={{ height: '100%', width: `${safe}%`, background: color, borderRadius: 999, ['--target']: `${safe}%` }} />
    </div>
  );
}

export function Avatar({ name = '', size = 34 }) {
  const initials = String(name || '?')
    .split(' ')
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();
  return (
    <span
      className="inline-flex items-center justify-center rounded-full font-bold shrink-0"
      style={{ width: size, height: size, fontSize: Math.round(size * 0.36), background: 'var(--primary-soft)', color: 'var(--primary)' }}
    >
      {initials || '?'}
    </span>
  );
}

export function Tooltip({ content, children }) {
  return <span title={content}>{children}</span>;
}

/* ================================================================== */
/* Modal                                                               */
/* ================================================================== */
export function Modal({ open, onClose, title, footer, width = 480, children }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[70] modal-backdrop anim-fade-in flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="card shadow-2xl anim-scale-in w-full max-h-[90vh] overflow-y-auto"
        style={{ maxWidth: width, background: 'var(--surface)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b hairline">
          <h3 className="font-bold text-[15px]">{title}</h3>
          {onClose && (
            <button className="btn-ghost btn btn-sm p-1.5 text-muted" onClick={onClose} aria-label="Close">
              <X size={16} />
            </button>
          )}
        </div>
        <div className="p-5">{children}</div>
        {footer && <div className="px-5 py-4 border-t hairline">{footer}</div>}
      </div>
    </div>
  );
}

/* ================================================================== */
/* Toasts                                                              */
/* ================================================================== */
const ToastCtx = createContext(null);

export function useToast() {
  return useContext(ToastCtx);
}

const TONE_META = {
  success: { color: 'var(--success)', icon: CheckCircle2 },
  error: { color: 'var(--danger)', icon: AlertTriangle },
  info: { color: 'var(--info)', icon: Info },
  warning: { color: 'var(--warning)', icon: AlertTriangle },
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const push = useCallback((message, tone = 'success') => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, message, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3600);
  }, []);

  const value = useMemo(() => ({ push }), [push]);

  return (
    <ToastCtx.Provider value={value}>
      {children}
      <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 items-end pointer-events-none">
        {toasts.map((t) => {
          const m = TONE_META[t.tone] || TONE_META.success;
          const Icon = m.icon;
          return (
            <div
              key={t.id}
              className="anim-toast card px-4 py-3 shadow-lg flex items-center gap-2.5 pointer-events-auto"
              style={{ background: 'var(--surface)', borderLeft: `3px solid ${m.color}`, maxWidth: 340 }}
            >
              <Icon size={17} style={{ color: m.color, flexShrink: 0 }} />
              <span className="text-[13px] font-medium leading-snug">{t.message}</span>
            </div>
          );
        })}
      </div>
    </ToastCtx.Provider>
  );
}
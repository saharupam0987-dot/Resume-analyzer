import React, { useState, useEffect, useCallback, useMemo } from 'react';
import API from '../api';
import {
  LayoutDashboard, FileText, Library, Plus, BarChart3, Users,
  Settings, LogOut, Search, Bell, HelpCircle, GraduationCap,
  Menu, PanelLeft, PanelLeftOpen, ClipboardCheck, Target, Moon, Compass, 
} from 'lucide-react';
import { cn } from './cn';
import { Avatar, useToast } from './ui';
import TeacherDashboard from './TeacherDashboard';
import StudentDashboard from './StudentDashboard';
import CreateExam from './CreateExam';
import ExamPaper from './ExamPaper';
import ExamTaking from './ExamTaking';
import QuestionBank from './QuestionBank';
import Results from './Results';
import Analytics from './Analytics';
import Students from './Students';
import ClassManagement from './ClassManagement';
import { Settings as SettingsPage } from './Settings';
import { ExamsGrid } from './Exams';
import { DefaultView } from './DefaultView';

const TEACHER_NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'classes', label: 'Classes', icon: GraduationCap },
  { id: 'exams', label: 'Exams', icon: FileText },
  { id: 'question-bank', label: 'Question Bank', icon: Library },
  { id: 'create-exam', label: 'Create Exam', icon: Plus, accent: true },
  { id: 'results', label: 'Results', icon: ClipboardCheck },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'students', label: 'Students', icon: Users },
];

const STUDENT_NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'my-classes', label: 'My Classes', icon: GraduationCap },
  { id: 'my-exams', label: 'My Exams', icon: FileText },
  { id: 'practice', label: 'Practice', icon: Target },
  { id: 'performance', label: 'Performance', icon: BarChart3 },
  { id: 'results', label: 'Results', icon: ClipboardCheck },
];

const VIEW_TITLES = {
  dashboard: 'Dashboard',
  classes: 'Classrooms & Cohorts',
  'my-classes': 'My Classes',
  exams: 'Exams',
  'my-exams': 'My Exams',
  'create-exam': 'Create Exam',
  'question-bank': 'Question Bank',
  results: 'Results',
  analytics: 'Analytics',
  performance: 'Performance',
  students: 'Students',
  practice: 'Practice',
  settings: 'Settings',
};

export function AppShell({ token, setToken, role, setRole }) {
  const toast = useToast();
  const [view, setView] = useState('dashboard');
  const [exams, setExams] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('eval_theme') || 'light');
  const [compact, setCompact] = useState(() => localStorage.getItem('eval_compact') === '1');
  const [cmdOpen, setCmdOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [previewExam, setPreviewExam] = useState(null);
  const [takingExam, setTakingExam] = useState(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('eval_theme', theme);
  }, [theme]);
  useEffect(() => {
    localStorage.setItem('eval_compact', compact ? '1' : '0');
  }, [compact]);

  const fetchExams = useCallback(async () => {
    try {
      const endpoint = role === 'student' ? '/student/exams' : '/exams/';
      const res = await API.get(endpoint);
      setExams(res.data || []);
    } catch (e) {
      toast.push('Could not load exams', 'error');
    }
  }, [role]);

  const fetchSubmissions = useCallback(async () => {
    try {
      const endpoint = role === 'teacher' ? '/submissions/' : '/submissions/student';
      const res = await API.get(endpoint);
      setSubmissions(res.data || []);
    } catch (e) {
      console.error(e);
    }
  }, [role]);

  useEffect(() => {
    if (!token) return;
    (async () => {
      setLoading(true);
      await Promise.all([fetchExams(), fetchSubmissions()]);
      setLoading(false);
    })();
  }, [token, role, fetchExams, fetchSubmissions]);

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCmdOpen((v) => !v);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const nav = role === 'teacher' ? TEACHER_NAV : STUDENT_NAV;
  const navIds = nav.map((n) => n.id);

  const go = (id) => {
    if (id === 'settings' || navIds.includes(id)) {
      setView(id);
      setDrawerOpen(false);
      setProfileOpen(false);
    }
  };

  const [profile, setProfile] = useState(null);

  useEffect(() => {
    if (!token) return;
    API.get('/auth/me')
      .then((res) => {
        setProfile(res.data);
        if (res.data?.name) {
          localStorage.setItem('eval_user_name', res.data.name);
        }
      })
      .catch((e) => console.log('Profile load:', e.message));
  }, [token]);

  const logout = () => {
    localStorage.removeItem('eval_token');
    localStorage.removeItem('eval_role');
    localStorage.removeItem('eval_user_id');
    localStorage.removeItem('eval_user_name');
    setToken(null);
  };

  const user = useMemo(
    () => ({
      name: profile?.name || localStorage.getItem('eval_user_name') || (role === 'teacher' ? 'Educator' : 'Student'),
      role: profile?.role || role,
      email: profile?.email || '',
    }),
    [profile, role]
  );

  // Main view router
  const page = (() => {
    if (view === 'dashboard') {
      return role === 'teacher' ? (
        <TeacherDashboard 
          exams={exams} 
          submissions={submissions}
          loading={loading} 
          onCreate={() => go('create-exam')} 
          onViewExam={openExam} 
          onStudents={() => go('classes')} 
          onResults={() => go('results')} 
        />
      ) : (
        <StudentDashboard 
          exams={exams} 
          submissions={submissions} 
          loading={loading} 
          onStart={setTakingExam} 
          onResults={() => go('results')} 
        />
      );
    }
    if (view === 'classes' || view === 'my-classes') {
      return (
        <ClassManagement 
          role={role} 
          exams={exams} 
          onStartExam={setTakingExam} 
          onViewExam={openExam}
          onRefreshExams={fetchExams}
        />
      );
    }
    if (view === 'create-exam') {
      return (
        <CreateExam 
          onRefreshExams={fetchExams}
          onGenerated={() => { 
            fetchExams(); 
            go('exams'); 
          }} 
        />
      );
    }
    if (view === 'exams' || view === 'my-exams') {
      return <ExamsGrid exams={exams} role={role} loading={loading} onView={openExam} onStart={setTakingExam} onCreate={() => go('create-exam')} />;
    }
    if (view === 'question-bank') return <QuestionBank exams={exams} />;
    if (view === 'results') return <Results exams={exams} submissions={submissions} role={role} />;
    if (view === 'analytics') return <Analytics exams={exams} submissions={submissions} />;
    if (view === 'performance') return <Analytics exams={exams} submissions={submissions} student />;
    if (view === 'students') return <Students exams={exams} submissions={submissions} />;
    if (view === 'practice') return <StudentDashboard exams={exams} submissions={submissions} loading={loading} onStart={setTakingExam} onResults={() => go('results')} practiceOnly />;
    if (view === 'settings') return <SettingsPage theme={theme} setTheme={setTheme} compact={compact} setCompact={setCompact} />;
    return <DefaultView />;
  })();

  function openExam(e) {
    setPreviewExam(e);
  }

  return (
    <div
      className="min-h-screen flex"
      style={{ background: "var(--bg)", color: "var(--text)" }}
    >
      {takingExam && (
        <ExamTaking
          exam={takingExam}
          onExit={() => setTakingExam(null)}
          onSubmitted={() => {
            setTakingExam(null);
            fetchExams();
            fetchSubmissions();
            go("results");
          }}
        />
      )}
      {!takingExam && previewExam && (
        <ExamPaper exam={previewExam} onClose={() => setPreviewExam(null)} />
      )}

      {!takingExam && (
        <aside
          className="hidden lg:flex flex-col fixed left-0 top-0 bottom-0 z-40 border-r hairline transition-[width] duration-200"
          style={{
            width: sidebarCollapsed ? 76 : 256,
            background: "var(--surface)",
          }}
        >
          <SidebarContent
            nav={nav}
            view={view}
            role={role}
            collapsed={sidebarCollapsed}
            onGo={go}
            onLogout={logout}
            user={user}
          />
        </aside>
      )}

      {!takingExam && drawerOpen && (
        <div
          className="fixed inset-0 z-50 lg:hidden modal-backdrop anim-fade-in"
          onClick={() => setDrawerOpen(false)}
        >
          <div
            className="h-full w-[280px] border-r hairline anim-slide-in"
            style={{ background: "var(--surface)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <SidebarContent
              nav={nav}
              view={view}
              role={role}
              collapsed={false}
              onGo={go}
              onLogout={logout}
              user={user}
            />
          </div>
        </div>
      )}

      <div
        className="flex-1 flex flex-col min-w-0 transition-[margin] duration-200"
        style={{
          marginLeft: sidebarCollapsed ? 76 : 256,
        }}
      >
        <header className="sticky top-0 z-20 backdrop-blur-md border-b border-[#E7E4DC] bg-[#FAF8F5]/90">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16 gap-3">
            <div className="flex items-center gap-3">
              <button
                className="p-2 rounded-lg text-[#616B66] hover:text-[#1C2421] hover:bg-white lg:hidden"
                onClick={() => setDrawerOpen(true)}
                aria-label="Open menu"
              >
                <Menu size={18} />
              </button>
              <button
                className="p-2 rounded-lg text-[#616B66] hover:text-[#1C2421] hover:bg-white hidden lg:inline-flex"
                onClick={() => setSidebarCollapsed((v) => !v)}
                aria-label="Collapse sidebar"
              >
                {sidebarCollapsed ? (
                  <PanelLeftOpen size={17} />
                ) : (
                  <PanelLeft size={17} />
                )}
              </button>
              <Breadcrumb role={role} view={view} />
            </div>

            <div className="flex items-center gap-2 sm:gap-3">
              {/* Role Toggle Pill in Header */}
              <div className="hidden sm:inline-flex items-center border border-[#E7E4DC] rounded-xl overflow-hidden p-0.5 bg-white text-xs">
                <button
                  onClick={() => {
                    setRole("teacher");
                    localStorage.setItem("eval_role", "teacher");
                  }}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    role === "teacher"
                      ? "bg-[#E8EFE9] text-[#16382C] font-semibold"
                      : "text-[#616B66] hover:text-[#1C2421]"
                  }`}
                >
                  Teacher
                </button>
                <button
                  onClick={() => {
                    setRole("student");
                    localStorage.setItem("eval_role", "student");
                  }}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    role === "student"
                      ? "bg-[#E8EFE9] text-[#16382C] font-semibold"
                      : "text-[#616B66] hover:text-[#1C2421]"
                  }`}
                >
                  Student
                </button>
              </div>

              <button
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border border-[#E7E4DC] bg-white text-xs text-[#616B66] hover:border-[#D8D4C8] hover:text-[#1C2421] transition-colors"
                onClick={() => setCmdOpen(true)}
                aria-label="Search"
              >
                <Search size={14} />
                <span className="hidden md:inline">Search…</span>
                <kbd className="hidden md:inline px-1 py-0.2 rounded border border-[#E7E4DC] text-[10px] text-[#969E99]">
                  ⌘K
                </kbd>
              </button>

              <NotifMenu role={role} open={notifOpen} setOpen={setNotifOpen} />
              <ProfileMenu
                user={user}
                open={profileOpen}
                setOpen={setProfileOpen}
                onGo={go}
                onLogout={logout}
              />
            </div>
          </div>
        </header>

        <main className="app-container flex-1 py-6 pb-16 w-full min-w-0">
          <div key={view} className="anim-fade-up">
            {page}
          </div>
        </main>
      </div>

      {cmdOpen && (
        <CommandPalette
          nav={nav}
          view={view}
          onGo={go}
          onClose={() => setCmdOpen(false)}
          exams={exams}
          onOpenExam={(e) => {
            openExam(e);
            setCmdOpen(false);
          }}
        />
      )}
    </div>
  );
}

/* ---------- Breadcrumb ---------- */
function Breadcrumb({ role, view }) {
  return (
    <div className="flex items-center gap-2 text-[13px] font-medium">
      <span className="text-faint">{role === 'teacher' ? 'Teacher' : 'Student'}</span>
      <span className="text-faint">/</span>
      <span className="font-semibold">{VIEW_TITLES[view] || 'Dashboard'}</span>
    </div>
  );
}

/* ---------- Sidebar ---------- */
function SidebarContent({ nav, view, role, collapsed, onGo, onLogout, user }) {
  return (
    <div className="flex flex-col h-full bg-[#FAF8F5] border-r border-[#E7E4DC]">
      <div className={cn('flex items-center gap-2.5 px-5 h-16 shrink-0 border-b border-[#E7E4DC]', collapsed && 'justify-center px-0')}>
        <div className="w-8 h-8 rounded-full bg-[#16382C] text-white flex items-center justify-center shrink-0">
          <Compass size={16} />
        </div>
        {!collapsed && (
          <div className="leading-tight">
            <div className="font-serif text-xl font-normal tracking-normal text-[#1C2421]">evaluate.</div>
            <div className="text-[10px] font-medium text-[#969E99] uppercase tracking-widest font-sans">Examination AI</div>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3.5 py-4 space-y-1">
        {!collapsed && (
          <div className="px-3 pt-1 pb-2 text-[11px] font-medium uppercase tracking-wider text-[#969E99] font-sans">
            {role === 'teacher' ? 'Teaching & Rubrics' : 'Focus Space'}
          </div>
        )}
        {nav.map((item) => {
          const active = view === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onGo(item.id)}
              className={cn(
                'flex items-center gap-3 w-full rounded-xl px-3.5 py-2.5 text-xs sm:text-[13px] transition-all duration-150',
                collapsed && 'justify-center px-0',
                active
                  ? 'bg-[#E8EFE9] text-[#16382C] font-semibold shadow-xs'
                  : 'text-[#616B66] hover:bg-white hover:text-[#1C2421]'
              )}
              aria-current={active ? 'page' : undefined}
            >
              <Icon size={16} strokeWidth={active ? 2.2 : 1.8} className="shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
              {item.accent && !collapsed && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[#E05D38]" />
              )}
            </button>
          );
        })}

        {!collapsed && (
          <div className="px-3 pt-5 pb-2 text-[11px] font-medium uppercase tracking-wider text-[#969E99] font-sans">
            Workspace
          </div>
        )}
        <button 
          onClick={() => onGo('settings')} 
          className={cn(
            'flex items-center gap-3 w-full rounded-xl px-3.5 py-2.5 text-xs sm:text-[13px] font-medium transition-colors',
            collapsed && 'justify-center px-0',
            view === 'settings' ? 'bg-[#E8EFE9] text-[#16382C] font-semibold' : 'text-[#616B66] hover:bg-white'
          )}
        >
          <Settings size={16} className="shrink-0" />
          {!collapsed && <span>Settings</span>}
        </button>
        <button 
          onClick={onLogout} 
          className={cn(
            'flex items-center gap-3 w-full rounded-xl px-3.5 py-2.5 text-xs sm:text-[13px] font-medium text-[#616B66] hover:bg-rose-50 hover:text-rose-700 transition-colors',
            collapsed && 'justify-center px-0'
          )}
        >
          <LogOut size={16} className="shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </nav>

      <div className={cn('px-4 py-3.5 border-t border-[#E7E4DC] bg-white', collapsed && 'flex justify-center px-0')}>
        <div className={cn('flex items-center gap-2.5', collapsed && 'flex-col')}>
          <div className="w-8 h-8 rounded-full bg-[#E8EFE9] text-[#16382C] font-serif font-bold text-xs flex items-center justify-center shrink-0">
            {user.name?.charAt(0) || 'U'}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0 leading-tight">
              <div className="text-xs font-semibold text-[#1C2421] truncate">{user.name}</div>
              <div className="text-[11px] text-[#969E99] capitalize font-sans">{user.role}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------- Notifications ---------- */
function NotifMenu({ role, open, setOpen }) {
  const items =
    role === 'teacher'
      ? [
          { id: 1, title: 'AI pending review', sub: '5 subjective answers waiting', time: '2m', tone: 'var(--warning)' },
          { id: 2, title: 'Exam published', sub: '"Midterm — Data Structures"', time: '1h', tone: 'var(--success)' },
          { id: 3, title: 'Questions generated', sub: '20 questions added to bank', time: '3h', tone: 'var(--primary)' },
        ]
      : [
          { id: 1, title: 'Your result is ready', sub: 'Data Structures Midterm', time: '1h', tone: 'var(--success)' },
          { id: 2, title: 'New exam assigned', sub: 'Algorithms Quiz', time: '5h', tone: 'var(--primary)' },
          { id: 3, title: '7-day streak!', sub: 'Keep it up 🎉', time: '1d', tone: 'var(--warning)' },
        ];
  return (
    <div className="relative">
      <button className="btn-ghost btn btn-sm relative" onClick={() => setOpen((v) => !v)} aria-label="Notifications">
        <Bell size={17} />
        <span className="absolute top-1 right-1 w-2 h-2 rounded-full" style={{ background: 'var(--danger)' }} />
      </button>
      {open && (
        <div className="absolute right-0 top-11 w-80 card shadow-lg anim-scale-in p-2 z-50" style={{ background: 'var(--surface)' }}>
          <div className="px-2 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-faint">Notifications</div>
          {items.map((n) => (
            <button key={n.id} className="flex items-start gap-2.5 w-full text-left px-2 py-2 rounded-lg hover:bg-[color:var(--surface-3)]">
              <span className="mt-1.5 w-2 h-2 rounded-full shrink-0" style={{ background: n.tone }} />
              <div className="min-w-0">
                <div className="text-[13px] font-medium">{n.title}</div>
                <div className="text-[11px] text-faint">{n.sub}</div>
              </div>
              <span className="ml-auto text-[11px] text-faint shrink-0">{n.time}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- Profile menu ---------- */
function ProfileMenu({ user, open, setOpen, onGo, onLogout }) {
  return (
    <div className="relative">
      <button onClick={() => setOpen((v) => !v)} className="rounded-full focus-ring" aria-label="Profile menu">
        <Avatar name={user.name} size={32} />
      </button>
      {open && (
        <div className="absolute right-0 top-11 w-56 card shadow-lg anim-scale-in p-1.5 z-50" style={{ background: 'var(--surface)' }}>
          <div className="px-3 py-2.5 border-b hairline">
            <div className="text-[13.5px] font-semibold">{user.name}</div>
            <div className="text-[11.5px] text-faint capitalize">{user.role}</div>
          </div>
          <button onClick={() => { onGo('settings'); setOpen(false); }} className="flex items-center gap-2.5 w-full px-3 py-2 text-[13px] font-medium rounded-lg hover:bg-[color:var(--surface-3)]">
            <Settings size={15} /> Settings
          </button>
          <button onClick={onLogout} className="flex items-center gap-2.5 w-full px-3 py-2 text-[13px] font-medium text-[color:var(--danger)] rounded-lg hover:bg-[color:var(--danger-soft)]">
            <LogOut size={15} /> Logout
          </button>
        </div>
      )}
    </div>
  );
}

/* ---------- Command palette ---------- */
function CommandPalette({ nav, view, onGo, onClose, exams, onOpenExam }) {
  const [q, setQ] = useState('');
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
  const filtered = nav.filter((n) => n.label.toLowerCase().includes(q.toLowerCase())).slice(0, 6);
  const filteredExams = exams.filter((e) => e.title.toLowerCase().includes(q.toLowerCase())).slice(0, 4);
  return (
    <div className="fixed inset-0 z-[60] modal-backdrop anim-fade-in flex items-start justify-center p-4 pt-[12vh]" onClick={onClose}>
      <div className="card w-full max-w-lg shadow-2xl anim-scale-in overflow-hidden" style={{ background: 'var(--surface)' }} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 px-4 py-3 border-b hairline">
          <Search size={16} style={{ color: 'var(--text-3)' }} />
          <input autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Jump to a page or exam…" className="flex-1 bg-transparent outline-none text-[14px]" />
          <kbd className="px-1.5 py-0.5 text-[10px] rounded-md border hairline text-faint">ESC</kbd>
        </div>
        <div className="p-2 max-h-80 overflow-y-auto">
          {filtered.length === 0 && filteredExams.length === 0 && <div className="px-3 py-6 text-center text-[13px] text-faint">No results for “{q}”</div>}
          {filtered.map((n) => (
            <button key={n.id} onClick={() => { onGo(n.id); onClose(); }} className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-[13.5px] font-medium hover:bg-[color:var(--surface-3)]">
              <n.icon size={16} style={{ color: 'var(--text-2)' }} /> {n.label}
            </button>
          ))}
          {filteredExams.length > 0 && <div className="px-3 pt-2 pb-1 text-[10.5px] font-semibold uppercase text-faint">Exams</div>}
          {filteredExams.map((e) => (
            <button key={e.id} onClick={() => onOpenExam(e)} className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-[13.5px] font-medium hover:bg-[color:var(--surface-3)]">
              <FileText size={16} style={{ color: 'var(--text-2)' }} /> {e.title}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* storage helper for session fields */
export function store(k, v) {
  if (v === undefined) return localStorage.getItem(k);
  localStorage.setItem(k, v);
}

export default AppShell;
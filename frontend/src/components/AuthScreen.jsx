import React, { useState } from 'react';
import { Compass, ArrowRight, ShieldCheck, Sparkles, BookOpenCheck, Check, User, BookOpen } from 'lucide-react';
import API from '../api';
import { Button, useToast, Badge } from './ui';

export default function AuthScreen({ setToken, setRole }) {
  const toast = useToast();
  const [role, setLocalRole] = useState('teacher');
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '', extra: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') {
        const res = await API.post('/auth/login', { email: form.email, password: form.password, role });
        localStorage.setItem('eval_token', res.data.access_token);
        localStorage.setItem('eval_role', res.data.role);
        localStorage.setItem('eval_user_id', res.data.user_id);
        if (res.data.name) {
          localStorage.setItem('eval_user_name', res.data.name);
        }
        setToken(res.data.access_token);
        setRole(res.data.role);
      } else {
        const endpoint = role === 'teacher' ? '/auth/register/teacher' : '/auth/register/student';
        const payload =
          role === 'teacher'
            ? { name: form.name, email: form.email, password: form.password, subject: form.extra }
            : { name: form.name, email: form.email, password: form.password, roll_number: form.extra };
        await API.post(endpoint, payload);
        toast.push('Account registered successfully! Please sign in.', 'success');
        setMode('login');
        setForm((prev) => ({ ...prev, password: '' }));
      }
    } catch (err) {
      const msg = err.response?.data?.detail || (err.message === 'Network Error' ? 'Cannot connect to backend server. Please check connection.' : 'Authentication failed');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-[#FAF8F5]">
      {/* Left brand panel - Editorial Dark Pine Aesthetic */}
      <div className="hidden lg:flex w-[48%] flex-col justify-between p-12 lg:p-16 relative overflow-hidden bg-[#16382C] text-white">
        <img 
          src="https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1400&q=80" 
          alt="Editorial Architecture" 
          className="absolute inset-0 w-full h-full object-cover opacity-25 mix-blend-luminosity"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#16382C] via-[#16382C]/75 to-[#16382C]/90" />

        {/* Brand Header */}
        <div className="relative z-10 flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full border border-emerald-400/30 flex items-center justify-center text-emerald-200">
            <Compass size={16} />
          </div>
          <span className="font-serif text-2xl tracking-normal text-white">
            evaluate.
          </span>
        </div>

        {/* Center Editorial Typography */}
        <div className="relative z-10 space-y-6 max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-emerald-200 text-xs font-medium backdrop-blur">
            <span className="w-2 h-2 rounded-full bg-[#E05D38]" />
            AI-Powered Examination & Evaluation
          </div>

          <h1 className="font-serif text-5xl xl:text-6xl font-normal leading-[1.08] tracking-tight text-white">
            Create exams faster.<br />
            Evaluate smarter.
          </h1>

          <p className="text-white/80 text-base font-sans leading-relaxed">
            Generate high-quality questions, evaluate subjective answers, and understand student performance with AI.
          </p>

          <div className="pt-2 flex items-center gap-2 text-xs text-emerald-200 font-sans tracking-wide">
            <span>✦ Semantic Rubric Grading</span>
            <span className="text-white/40">·</span>
            <span>✦ Bloom's Taxonomy Alignment</span>
            <span className="text-white/40">·</span>
            <span>✦ RAG Question Synthesizer</span>
          </div>
        </div>

        {/* Footer Quote */}
        <div className="relative z-10 text-xs text-white/50 font-sans">
          © Evaluate · AI-Powered Examination & Semantic Evaluation Platform
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md bg-white border border-[#E7E4DC] rounded-3xl p-8 sm:p-10 shadow-sm">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center gap-2 mb-6 justify-center">
            <div className="w-8 h-8 rounded-full bg-[#16382C] text-white flex items-center justify-center">
              <Compass size={16} />
            </div>
            <span className="font-serif text-2xl text-[#1C2421]">evaluate.</span>
          </div>

          <div className="text-center sm:text-left mb-6">
            <span className="text-xs uppercase tracking-widest text-[#969E99] font-medium font-sans">
              Authentication
            </span>
            <h2 className="font-serif text-3xl font-normal text-[#1C2421] mt-1">
              {mode === 'login' ? 'Welcome back.' : 'Create your account.'}
            </h2>
            <p className="text-xs text-[#616B66] mt-1 font-sans">
              {mode === 'login' ? 'Sign in to access your examinations and rubrics' : 'Register to begin evaluating with AI'}
            </p>
          </div>

          {/* Role Toggle */}
          <div className="grid grid-cols-2 border border-[#E7E4DC] rounded-xl overflow-hidden mb-4 p-0.5 bg-[#FAF8F5]">
            <button
              type="button"
              onClick={() => setLocalRole('teacher')}
              className={`py-2 text-xs font-medium rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                role === 'teacher' ? 'bg-[#E8EFE9] text-[#16382C] font-semibold shadow-xs' : 'text-[#616B66] hover:text-[#1C2421]'
              }`}
            >
              <User size={13} /> Teacher
            </button>
            <button
              type="button"
              onClick={() => setLocalRole('student')}
              className={`py-2 text-xs font-medium rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                role === 'student' ? 'bg-[#E8EFE9] text-[#16382C] font-semibold shadow-xs' : 'text-[#616B66] hover:text-[#1C2421]'
              }`}
            >
              <BookOpen size={13} /> Student
            </button>
          </div>

          {mode === 'login' && (
            <div className="mb-5 p-2.5 rounded-xl bg-[#FAF8F5] border border-[#E7E4DC] flex items-center justify-between text-xs">
              <span className="text-[#969E99] font-sans">Quick fill:</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setLocalRole('teacher');
                    setForm({ ...form, email: 'sarah@university.com', password: 'password123' });
                  }}
                  className="px-2.5 py-1 rounded-lg bg-white border border-[#E7E4DC] hover:border-[#16382C] text-[#16382C] font-medium transition-colors cursor-pointer"
                >
                  Teacher (Sarah)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setLocalRole('student');
                    setForm({ ...form, email: 'alex@student.com', password: 'password123' });
                  }}
                  className="px-2.5 py-1 rounded-lg bg-white border border-[#E7E4DC] hover:border-[#16382C] text-[#16382C] font-medium transition-colors cursor-pointer"
                >
                  Student (Alex)
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 font-sans">
            {mode === 'register' && (
              <>
                <Field label="Full name">
                  <input 
                    required 
                    className="w-full px-3.5 py-2.5 rounded-xl border border-[#E7E4DC] text-sm bg-[#FAF8F5] focus:bg-white focus:border-[#16382C] outline-none transition-colors" 
                    placeholder={role === 'teacher' ? 'Prof. Sarah Mitchell' : 'Alex Morgan'} 
                    value={form.name} 
                    onChange={(e) => setForm({ ...form, name: e.target.value })} 
                  />
                </Field>
                <Field label={role === 'teacher' ? 'Subject Specialization' : 'Roll Number'}>
                  <input 
                    required 
                    className="w-full px-3.5 py-2.5 rounded-xl border border-[#E7E4DC] text-sm bg-[#FAF8F5] focus:bg-white focus:border-[#16382C] outline-none transition-colors" 
                    placeholder={role === 'teacher' ? 'Computer Science' : 'CS2026001'} 
                    value={form.extra} 
                    onChange={(e) => setForm({ ...form, extra: e.target.value })} 
                  />
                </Field>
              </>
            )}

            <Field label="Email Address">
              <input 
                required 
                type="email" 
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#E7E4DC] text-sm bg-[#FAF8F5] focus:bg-white focus:border-[#16382C] outline-none transition-colors" 
                placeholder="you@university.edu" 
                value={form.email} 
                onChange={(e) => setForm({ ...form, email: e.target.value })} 
              />
            </Field>

            <Field label="Password">
              <input 
                required 
                type="password" 
                className="w-full px-3.5 py-2.5 rounded-xl border border-[#E7E4DC] text-sm bg-[#FAF8F5] focus:bg-white focus:border-[#16382C] outline-none transition-colors" 
                placeholder="••••••••" 
                value={form.password} 
                onChange={(e) => setForm({ ...form, password: e.target.value })} 
              />
            </Field>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 bg-[#E05D38] hover:bg-[#C94B27] text-white py-3 rounded-xl font-medium text-sm transition-colors shadow-sm flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <span>{loading ? 'Processing…' : mode === 'login' ? 'Sign in' : 'Create Account'}</span>
              <ArrowRight size={15} />
            </button>
          </form>

          <p className="text-xs text-[#616B66] mt-6 text-center font-sans">
            {mode === 'login' ? "Don't have an account? " : 'Already registered? '}
            <button 
              onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }} 
              className="font-semibold text-[#16382C] underline decoration-[#E05D38] underline-offset-4 hover:text-[#E05D38] transition-colors cursor-pointer"
            >
              {mode === 'login' ? 'Create an account' : 'Sign in here'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-wider text-[#969E99] font-medium mb-1 font-sans">
        {label}
      </label>
      {children}
    </div>
  );
}
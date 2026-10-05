import React, { useState } from 'react';
import { Moon, Sun, Shrink, Bell, User as UserIcon, ShieldCheck, Palette } from 'lucide-react';
import { Card, Badge, Button, SectionTitle } from './ui';

export function Settings({ theme, setTheme, compact, setCompact }) {
  const [email, setEmail] = useState('sarah.mitchell@school.edu');
  const [notify, setNotify] = useState(true);

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h1 className="text-[26px] font-extrabold tracking-tight">Settings</h1>
        <p className="text-[14px] text-muted mt-1">Manage your account preferences and appearance.</p>
      </div>

      <Card className="p-6 mb-5">
        <div className="flex items-center gap-2 mb-5"><span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--primary-soft)', color: 'var(--primary)' }}><Palette size={16} /></span><SectionTitle title="Appearance" /></div>

        <SettingRow
          icon={theme === 'dark' ? Moon : Sun}
          label="Theme"
          detail="Switch between light and dark mode."
          control={
            <div className="flex gap-1.5 p-1 rounded-xl" style={{ background: 'var(--surface-3)' }}>
              {['light', 'dark'].map((t) => (
                <button key={t} onClick={() => setTheme(t)} className="px-3 py-1.5 rounded-lg text-[12.5px] font-semibold capitalize transition-colors" style={theme === t ? { background: 'var(--surface)', boxShadow: 'var(--shadow-sm)', color: 'var(--text)' } : { color: 'var(--text-2)' }}>
                  {t}
                </button>
              ))}
            </div>
          }
        />

        <div className="h-px hairline my-4" />

        <div
          className="flex items-center justify-between gap-4 cursor-pointer"
          onClick={() => setCompact((c) => !c)}
        >
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: 'var(--surface-3)', color: 'var(--text-2)' }}><User size={16} /></span>
            <div>
              <div className="text-[13.5px] font-semibold">Compact mode</div>
              <div className="text-[12px] text-muted">Reduce spacing for a denser layout.</div>
            </div>
          </div>
          <Switch checked={compact} onChange={setCompact} />
        </div>
      </Card>

      <Card className="p-6 mb-5">
        <div className="flex items-center gap-3 mb-4"><span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--primary-soft)', color: 'var(--primary)' }}><Bell size={16} /></span><SectionTitle title="Notifications" /></div>
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-[13.5px] font-semibold">Email notifications</div>
            <div className="text-[12px] text-muted">Get notified when submissions are evaluated.</div>
          </div>
          <Switch checked={notify} onChange={setNotify} />
        </div>
      </Card>

      <Card className="p-6 mb-5">
        <div className="flex items-center gap-3 mb-4"><span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--primary-soft)', color: 'var(--primary)' }}><User size={16} /></span><SectionTitle title="Profile" /></div>
        <div className="space-y-3.5">
          <Field label="Display name"><input className="input" defaultValue="Sarah Mitchell" /></Field>
          <Field label="Email address"><input className="input" value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
          <Field label="Role"><Badge tone="primary">Teacher</Badge></Field>
          <Button variant="primary">Save changes</Button>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center gap-3 mb-3"><span className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--success-soft)', color: 'var(--success)' }}><ShieldCheck size={16} /></span><SectionTitle title="Security" /></div>
        <div className="text-[13px] text-muted leading-relaxed">
          Your account is protected with JWT-based authentication. Sessions stay active until you sign out.
        </div>
        <div className="flex gap-2 mt-4">
          <Button variant="secondary">Change password</Button>
          <Button variant="danger">Sign out everywhere</Button>
        </div>
      </Card>
    </div>
  );
}

function Switch({ checked, onChange }) {
  return (
    <button
      onClick={(e) => { e.stopPropagation(); onChange(!checked); }}
      className="relative w-11 h-6 rounded-full transition-colors shrink-0"
      style={{ background: checked ? 'var(--primary)' : 'var(--surface-3)' }}
      aria-pressed={checked}
    >
      <span className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-all" style={{ left: checked ? 22 : 2 }} />
    </button>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  );
}

export default Settings;
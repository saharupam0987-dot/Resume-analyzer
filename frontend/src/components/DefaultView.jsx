import React from 'react';
import { GraduationCap } from 'lucide-react';

export function DefaultView() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <span className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4" style={{ background: 'var(--primary-soft)', color: 'var(--primary)' }}>
        <GraduationCap size={28} />
      </span>
      <h2 className="font-bold text-[18px]">Select a section</h2>
      <p className="text-[13px] text-muted mt-1">Choose a destination from the sidebar to get started.</p>
    </div>
  );
}

export default DefaultView;
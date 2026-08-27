import React from 'react';
import { Finding } from '../types';
import { AlertTriangle, AlertCircle, Info, Code2, Sparkles } from 'lucide-react';

interface Props {
  finding: Finding;
  source?: 'static' | 'ai';
}

export const FindingCard: React.FC<Props> = ({ finding, source = 'static' }) => {
  const sev = (finding.severity || 'LOW').toUpperCase();
  const confidencePct = Math.round((finding.confidence ?? 1.0) * 100);

  const getStyle = () => {
    switch (sev) {
      case 'HIGH':
        return {
          border: 'border-red-500/30 border-l-red-500',
          bg: 'bg-red-500/5 hover:bg-red-500/10',
          badge: 'bg-red-500/20 text-red-300 border-red-500/30',
          icon: <AlertTriangle className="w-4 h-4 text-red-400" />
        };
      case 'MEDIUM':
        return {
          border: 'border-amber-500/30 border-l-amber-500',
          bg: 'bg-amber-500/5 hover:bg-amber-500/10',
          badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
          icon: <AlertCircle className="w-4 h-4 text-amber-400" />
        };
      default:
        return {
          border: 'border-emerald-500/30 border-l-emerald-500',
          bg: 'bg-emerald-500/5 hover:bg-emerald-500/10',
          badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
          icon: <Info className="w-4 h-4 text-emerald-400" />
        };
    }
  };

  const style = getStyle();
  const lineDisplay = finding.line
    ? `Line ${finding.line}`
    : finding.line_range
    ? `Lines ${finding.line_range}`
    : 'Genel';

  return (
    <div className={`border border-l-4 ${style.border} ${style.bg} rounded-xl p-4 transition-all duration-200 shadow-sm mb-3`}>
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          {style.icon}
          <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-md border ${style.badge}`}>
            [{sev}] {finding.category}
          </span>
          <span className="text-xs font-mono text-slate-400 bg-slate-900/60 border border-slate-800 px-2 py-0.5 rounded">
            {lineDisplay}
          </span>
          {source === 'ai' && (
            <span className="text-[10px] flex items-center gap-1 font-mono text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded">
              <Sparkles className="w-3 h-3" /> AI Insight
            </span>
          )}
        </div>
        <span className="text-xs text-slate-500 font-mono">
          güven: {confidencePct}%
        </span>
      </div>

      <p className="text-sm text-slate-200 leading-relaxed font-normal">
        {finding.message}
      </p>

      {finding.suggestion && (
        <div className="mt-3 bg-slate-950/80 border border-slate-800/80 rounded-lg p-3 text-xs font-mono text-sky-300 flex items-start gap-2">
          <Code2 className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-slate-400 font-bold block mb-1">Öneri / Çözüm:</span>
            {finding.suggestion}
          </div>
        </div>
      )}
    </div>
  );
};

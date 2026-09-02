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
          border: 'border-red-500/40 border-l-red-500',
          bg: 'bg-red-500/10 hover:bg-red-500/15',
          badge: 'bg-red-500/20 text-red-300 border-red-500/40',
          icon: <AlertTriangle className="w-5 h-5 text-red-400" />
        };
      case 'MEDIUM':
        return {
          border: 'border-amber-500/40 border-l-amber-500',
          bg: 'bg-amber-500/10 hover:bg-amber-500/15',
          badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          icon: <AlertCircle className="w-5 h-5 text-amber-400" />
        };
      default:
        return {
          border: 'border-emerald-500/40 border-l-emerald-500',
          bg: 'bg-emerald-500/10 hover:bg-emerald-500/15',
          badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          icon: <Info className="w-5 h-5 text-emerald-400" />
        };
    }
  };

  const style = getStyle();
  
  const hasMultipleLines = finding.lines && finding.lines.length > 1;
  const lineDisplay = hasMultipleLines
    ? `Satırlar: ${finding.lines!.join(', ')} (${finding.lines!.length} Yerde)`
    : finding.line
    ? `Line ${finding.line}`
    : finding.line_range
    ? `Lines ${finding.line_range}`
    : 'Genel';


  return (
    <div className={`border border-l-4 ${style.border} ${style.bg} rounded-xl p-5 transition-all duration-200 shadow-md mb-3.5`}>
      <div className="flex items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2.5">
          {style.icon}
          <span className={`text-xs font-bold px-3 py-1 rounded-md border uppercase font-mono ${style.badge}`}>
            [{sev}] {finding.category}
          </span>
          <span className="text-xs font-mono text-slate-300 bg-slate-900 border border-slate-700 px-2.5 py-1 rounded-md font-bold">
            {lineDisplay}
          </span>
          {source === 'ai' && (
            <span className="text-xs flex items-center gap-1 font-mono text-purple-300 bg-purple-500/20 border border-purple-500/40 px-2.5 py-1 rounded-md font-bold">
              <Sparkles className="w-3.5 h-3.5" /> AI Insight
            </span>
          )}
        </div>
        <span className="text-xs text-slate-400 font-mono font-semibold">
          güven: {confidencePct}%
        </span>
      </div>

      <p className="text-base text-slate-100 font-medium leading-relaxed my-2">
        {finding.message}
      </p>

      {finding.suggestion && (
        <div className="mt-3.5 bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono text-sky-300 flex items-start gap-3">
          <Code2 className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-slate-400 font-bold block mb-1">Öneri / Çözüm:</span>
            <span className="text-sm font-sans text-sky-200">{finding.suggestion}</span>
          </div>
        </div>
      )}
    </div>
  );
};

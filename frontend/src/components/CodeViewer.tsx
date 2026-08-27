import React, { useState } from 'react';
import { Copy, Check, FileCode } from 'lucide-react';

interface Props {
  code: string;
  filename: string;
}

export const CodeViewer: React.FC<Props> = ({ code, filename }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = code.split('\n');

  return (
    <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950">
      <div className="bg-slate-900/80 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
          <FileCode className="w-4 h-4 text-sky-400" />
          <span>{filename}</span>
          <span className="text-slate-500">({lines.length} satır)</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800/60 px-2.5 py-1 rounded-lg border border-slate-700/50 transition"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Kopyalandı!' : 'Kopyala'}</span>
        </button>
      </div>

      <div className="p-4 overflow-x-auto max-h-[550px] font-mono text-xs leading-6 text-slate-200">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, idx) => (
              <tr key={idx} className="hover:bg-slate-900/40">
                <td className="w-10 select-none text-right pr-4 text-slate-600 text-[11px]">
                  {idx + 1}
                </td>
                <td className="whitespace-pre">
                  {line || ' '}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

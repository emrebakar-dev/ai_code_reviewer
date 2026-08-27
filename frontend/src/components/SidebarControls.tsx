import React from 'react';
import { FileCode2, FolderTree, FileArchive, Settings2, Bot, Sliders } from 'lucide-react';

export type Mode = 'single' | 'directory' | 'zip';

interface Props {
  mode: Mode;
  setMode: (m: Mode) => void;
  enableAi: boolean;
  setEnableAi: (b: boolean) => void;
  selectedModel: string;
  setSelectedModel: (s: string) => void;
  confidenceThreshold: number;
  setConfidenceThreshold: (n: number) => void;
}

export const SidebarControls: React.FC<Props> = ({
  mode,
  setMode,
  enableAi,
  setEnableAi,
  selectedModel,
  setSelectedModel,
  confidenceThreshold,
  setConfidenceThreshold,
}) => {
  return (
    <aside className="w-80 border-r border-slate-800/80 bg-slate-950/40 p-6 flex flex-col gap-6 shrink-0 min-h-[calc(100vh-4rem)]">
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          <Settings2 className="w-4 h-4 text-slate-400" />
          <span>Analiz Modu</span>
        </div>
        <div className="grid grid-cols-1 gap-2">
          <button
            onClick={() => setMode('single')}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl border text-sm font-medium transition ${
              mode === 'single'
                ? 'bg-indigo-600/10 border-indigo-500/50 text-indigo-300'
                : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <FileCode2 className="w-4 h-4" />
            <span>Tek Dosya / Kod</span>
          </button>
          <button
            onClick={() => setMode('directory')}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl border text-sm font-medium transition ${
              mode === 'directory'
                ? 'bg-indigo-600/10 border-indigo-500/50 text-indigo-300'
                : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <FolderTree className="w-4 h-4" />
            <span>Yerel Klasör Yolu</span>
          </button>
          <button
            onClick={() => setMode('zip')}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl border text-sm font-medium transition ${
              mode === 'zip'
                ? 'bg-indigo-600/10 border-indigo-500/50 text-indigo-300'
                : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <FileArchive className="w-4 h-4" />
            <span>Proje (ZIP) Yükle</span>
          </button>
        </div>
      </div>

      <div className="h-px bg-slate-800/80" />

      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <Bot className="w-4 h-4 text-slate-400" />
            <span>Yapay Zekâ</span>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={enableAi}
              onChange={(e) => setEnableAi(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-300 after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
          </label>
        </div>

        {enableAi && (
          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">AI Model:</label>
              <input
                type="text"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                placeholder="qwen/qwen3.6-27b"
              />
            </div>
          </div>
        )}
      </div>

      <div className="h-px bg-slate-800/80" />

      <div>
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-slate-400" />
            <span>Güven Eşiği</span>
          </div>
          <span className="font-mono text-indigo-400 text-xs">{confidenceThreshold.toFixed(2)}</span>
        </div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={confidenceThreshold}
          onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
          className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
        />
        <p className="text-[11px] text-slate-500 mt-1">
          Bu eşiğin altındaki bulgular gizlenir (0 = hepsini göster).
        </p>
      </div>
    </aside>
  );
};

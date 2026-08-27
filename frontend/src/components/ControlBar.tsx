import React from 'react';
import { Mode } from './SidebarControls';
import { FileCode2, FolderTree, FileArchive, Bot, Sliders } from 'lucide-react';

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

export const ControlBar: React.FC<Props> = ({
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
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-md mb-6 shadow-xl shadow-black/20">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* MODE SELECTOR (Segmented Control) */}
        <div className="flex items-center gap-1.5 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800">
          <button
            onClick={() => setMode('single')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mode === 'single'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <FileCode2 className="w-3.5 h-3.5" />
            <span>Tek Dosya / Kod</span>
          </button>
          <button
            onClick={() => setMode('directory')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mode === 'directory'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <FolderTree className="w-3.5 h-3.5" />
            <span>Yerel Klasör Yolu</span>
          </button>
          <button
            onClick={() => setMode('zip')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mode === 'zip'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
            }`}
          >
            <FileArchive className="w-3.5 h-3.5" />
            <span>Proje (ZIP) Yükle</span>
          </button>
        </div>

        {/* AI & CONFIDENCE CONTROLS */}
        <div className="flex items-center gap-6 bg-slate-950/80 px-4 py-2 rounded-xl border border-slate-800">
          {/* AI TOGGLE */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300">
              <Bot className="w-4 h-4 text-purple-400" />
              <span>Yapay Zekâ</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={enableAi}
                onChange={(e) => setEnableAi(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-8 h-4 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-300 after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          {enableAi && (
            <div className="h-4 w-px bg-slate-800" />
          )}

          {enableAi && (
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-slate-400">Model:</span>
              <input
                type="text"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-slate-200 font-mono w-40 focus:outline-none focus:border-purple-500"
                placeholder="qwen/qwen3.6-27b"
              />
            </div>
          )}

          <div className="h-4 w-px bg-slate-800" />

          {/* CONFIDENCE SLIDER */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-300">
              <Sliders className="w-3.5 h-3.5 text-indigo-400" />
              <span>Güven Eşiği:</span>
              <span className="font-mono text-indigo-400 text-xs font-bold">{confidenceThreshold.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
              className="w-24 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

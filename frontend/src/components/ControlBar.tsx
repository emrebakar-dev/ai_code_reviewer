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
  availableModels?: string[];
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
  availableModels = [
    "qwen/qwen3.6-27b",
    "groq/compound-mini",
    "groq/compound",
    "openai/gpt-oss-20b"
  ],
  confidenceThreshold,
  setConfidenceThreshold,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-700/80 rounded-2xl p-5 backdrop-blur-2xl shadow-2xl shadow-slate-950/50">
      <div className="flex flex-wrap items-center justify-between gap-6">
        {/* MODE SELECTOR (Segmented Control) */}
        <div className="flex items-center gap-2 bg-slate-950/80 p-2 rounded-xl border border-slate-700/80">
          <button
            onClick={() => setMode('single')}
            className={`flex items-center gap-2.5 px-5 py-3 rounded-lg text-sm font-bold transition-all ${
              mode === 'single'
                ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-600/40'
                : 'text-slate-300 hover:text-white'
            }`}
          >
            <FileCode2 className="w-4 h-4" />
            <span>Tek Dosya / Kod</span>
          </button>
          <button
            onClick={() => setMode('directory')}
            className={`flex items-center gap-2.5 px-5 py-3 rounded-lg text-sm font-bold transition-all ${
              mode === 'directory'
                ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-600/40'
                : 'text-slate-300 hover:text-white'
            }`}
          >
            <FolderTree className="w-4 h-4" />
            <span>Yerel Klasör Yolu</span>
          </button>
          <button
            onClick={() => setMode('zip')}
            className={`flex items-center gap-2.5 px-5 py-3 rounded-lg text-sm font-bold transition-all ${
              mode === 'zip'
                ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-600/40'
                : 'text-slate-300 hover:text-white'
            }`}
          >
            <FileArchive className="w-4 h-4" />
            <span>Proje ZIP</span>
          </button>
        </div>

        {/* AI & CONFIDENCE CONTROLS */}
        <div className="flex items-center gap-6 bg-slate-950/80 px-5 py-2.5 rounded-xl border border-slate-700/80">
          {/* AI TOGGLE */}
          <div className="flex items-center gap-3">
            <Bot className="w-5 h-5 text-purple-400" />
            <span className="text-sm text-slate-200 font-semibold">Yapay Zekâ:</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={enableAi}
                onChange={(e) => setEnableAi(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-300 after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          {enableAi && <div className="w-px h-5 bg-slate-700" />}

          {/* AI MODEL SELECTOR DROPDOWN */}
          {enableAi && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Model:</span>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-slate-900 text-sm text-purple-300 font-mono border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:border-purple-500 font-bold cursor-pointer"
              >
                {availableModels.map((m) => (
                  <option key={m} value={m} className="bg-slate-900 text-slate-200 font-mono">
                    {m}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="w-px h-5 bg-slate-700" />

          {/* CONFIDENCE SLIDER */}
          <div className="flex items-center gap-3">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <span className="text-xs text-slate-400 font-medium">Güven:</span>
            <span className="text-sm font-mono font-bold text-indigo-400">{confidenceThreshold.toFixed(2)}</span>
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

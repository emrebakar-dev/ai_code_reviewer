'use client';

import React, { useState } from 'react';
import { Header } from '../components/Header';
import { FindingCard } from '../components/FindingCard';
import { CodeViewer } from '../components/CodeViewer';
import { Mode } from '../components/SidebarControls';
import { SingleAnalyzeResponse, DirectoryAnalyzeResponse } from '../types';
import {
  Play,
  Upload,
  FolderSearch,
  FileText,
  Shield,
  Sparkles,
  Download,
  CheckCircle2,
  AlertOctagon,
  ChevronRight,
  Code2,
  FileCode2,
  FolderTree,
  FileArchive,
  Bot,
  Sliders,
  AlertTriangle
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function Home() {
  const [mode, setMode] = useState<Mode>('single');
  const [enableAi, setEnableAi] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string>('qwen/qwen3.6-27b');
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.0);

  // Inputs
  const [singleInputType, setSingleInputType] = useState<'upload' | 'paste'>('upload');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [pastedCode, setPastedCode] = useState<string>('def calculate_sum(a, b):\n    return a + b\n');

  const [dirPathInput, setDirPathInput] = useState<string>('');
  const [zipFile, setZipFile] = useState<File | null>(null);

  // States
  const [loading, setLoading] = useState<boolean>(false);
  const [statusText, setStatusText] = useState<string>('Analiz ediliyor...');
  const [progressPct, setProgressPct] = useState<number>(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [singleResult, setSingleResult] = useState<SingleAnalyzeResponse | null>(null);
  const [dirResult, setDirResult] = useState<DirectoryAnalyzeResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'static' | 'ai' | 'code' | 'report'>('static');
  const [activeExpanderFile, setActiveExpanderFile] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setErrorMsg(null);
    setSingleResult(null);
    setDirResult(null);
    setProgressPct(25);

    try {
      if (mode === 'single') {
        let codeToSend = '';
        let fileNameToSend = 'snippet.py';

        if (singleInputType === 'upload') {
          if (!uploadedFile) {
            throw new Error('Lütfen analiz edilecek bir dosya seçin.');
          }
          codeToSend = await uploadedFile.text();
          fileNameToSend = uploadedFile.name;
        } else {
          codeToSend = pastedCode;
        }

        setStatusText(`${fileNameToSend} analiz ediliyor...`);
        setProgressPct(55);

        const res = await fetch(`${API_BASE}/analyze/code`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            code: codeToSend,
            filename: fileNameToSend,
            enable_ai: enableAi,
            model: selectedModel,
            confidence_threshold: confidenceThreshold
          })
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || 'Analiz sırasında hata oluştu.');
        }

        setProgressPct(90);
        const data: SingleAnalyzeResponse = await res.json();
        setSingleResult(data);
      } else if (mode === 'directory') {
        if (!dirPathInput.trim()) {
          throw new Error('Lütfen taranacak klasör yolunu girin.');
        }

        setStatusText(`"${dirPathInput.trim()}" projesi taranıyor...`);
        setProgressPct(45);

        const res = await fetch(`${API_BASE}/analyze/directory`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            directory_path: dirPathInput.trim(),
            enable_ai: enableAi,
            model: selectedModel,
            confidence_threshold: confidenceThreshold
          })
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || 'Klasör tarama hatası.');
        }

        setProgressPct(90);
        const data: DirectoryAnalyzeResponse = await res.json();
        setDirResult(data);
      } else if (mode === 'zip') {
        if (!zipFile) {
          throw new Error('Lütfen bir .zip dosyası yükleyin.');
        }

        setStatusText(`${zipFile.name} ZIP arşivi taranıyor...`);
        setProgressPct(35);

        const formData = new FormData();
        formData.append('file', zipFile);
        formData.append('enable_ai', String(enableAi));
        if (selectedModel) formData.append('model', selectedModel);
        formData.append('confidence_threshold', String(confidenceThreshold));

        const res = await fetch(`${API_BASE}/analyze/zip`, {
          method: 'POST',
          body: formData
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || 'ZIP analiz hatası.');
        }

        setProgressPct(90);
        const data: DirectoryAnalyzeResponse = await res.json();
        setDirResult(data);
      }
      setProgressPct(100);
    } catch (err: any) {
      setErrorMsg(err.message || 'Bilinmeyen bir hata oluştu.');
    } finally {
      setLoading(false);
      setTimeout(() => setProgressPct(0), 1000);
    }
  };

  const downloadReport = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans text-base">
      {/* HEADER */}
      <Header />

      {/* PROMINENT ANIMATED NEON PROGRESS BAR */}
      {loading && (
        <div className="w-full bg-slate-800 h-2.5 relative overflow-hidden shadow-xl">
          <div
            className="h-full bg-gradient-to-r from-cyan-400 via-indigo-500 to-purple-500 transition-all duration-300 ease-out shadow-lg shadow-indigo-500/80"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      )}

      {/* MAIN HERO CANVAS (WIDE MAX-W-7XL) */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-10 flex flex-col gap-8">
        {/* HERO COMMAND CENTER BAR (SLATE-800 / BRIGHT BLUE ACCENT) */}
        <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 backdrop-blur-2xl shadow-2xl shadow-slate-950/50">
          <div className="flex flex-wrap items-center justify-between gap-6">
            {/* MODE SELECTION TABS */}
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

            {/* INLINE CONFIGURATION PILLS */}
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

              {enableAi && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-medium">Model:</span>
                  <input
                    type="text"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="bg-transparent text-sm text-purple-300 font-mono w-44 border-none focus:outline-none focus:ring-0 font-bold"
                    placeholder="qwen/qwen3.6-27b"
                  />
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

        {/* INPUT STUDIO CANVAS (BRIGHTER SLATE) */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-8 shadow-2xl relative">
          {mode === 'single' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-slate-700 pb-4">
                <div className="flex gap-3">
                  <button
                    onClick={() => setSingleInputType('upload')}
                    className={`text-sm font-bold px-4 py-2.5 rounded-lg border transition ${
                      singleInputType === 'upload'
                        ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Dosya Yükle (.py, .cpp, .java)
                  </button>
                  <button
                    onClick={() => setSingleInputType('paste')}
                    className={`text-sm font-bold px-4 py-2.5 rounded-lg border transition ${
                      singleInputType === 'paste'
                        ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Kod Yapıştır
                  </button>
                </div>
              </div>

              {singleInputType === 'upload' ? (
                <div className="border-2 border-dashed border-slate-700 hover:border-indigo-400 rounded-xl p-12 text-center transition bg-slate-950/80">
                  <input
                    type="file"
                    onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="single-file-input"
                  />
                  <label htmlFor="single-file-input" className="cursor-pointer flex flex-col items-center gap-4">
                    <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-300 shadow-xl">
                      <Upload className="w-8 h-8" />
                    </div>
                    <span className="text-base font-bold text-slate-100">
                      {uploadedFile ? uploadedFile.name : 'Dosyanızı Buraya Bırakın veya Seçin'}
                    </span>
                    <span className="text-xs text-slate-400">Desteklenen diller: Python (.py), C/C++ (.cpp), Java (.java), Web (.css, .html, .js, .ts)</span>
                  </label>
                </div>
              ) : (
                <div>
                  <textarea
                    value={pastedCode}
                    onChange={(e) => setPastedCode(e.target.value)}
                    rows={10}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl p-5 font-mono text-sm text-slate-100 focus:outline-none focus:border-indigo-500 leading-relaxed"
                    placeholder="Analiz edilecek kaynak kodu buraya yapıştırın..."
                  />
                </div>
              )}
            </div>
          )}

          {mode === 'directory' && (
            <div className="py-4">
              <label className="text-sm text-slate-200 block mb-3 font-semibold">Bilgisayarınızdaki Yerel Klasör Yolu:</label>
              <input
                type="text"
                value={dirPathInput}
                onChange={(e) => setDirPathInput(e.target.value)}
                placeholder="./examples veya /Users/kullanici/Desktop/proje"
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-5 py-4 text-sm text-slate-100 font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          {mode === 'zip' && (
            <div className="border-2 border-dashed border-slate-700 hover:border-indigo-400 rounded-xl p-12 text-center transition bg-slate-950/80">
              <input
                type="file"
                accept=".zip"
                onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                className="hidden"
                id="zip-file-input"
              />
              <label htmlFor="zip-file-input" className="cursor-pointer flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-300 shadow-xl">
                  <Upload className="w-8 h-8" />
                </div>
                <span className="text-base font-bold text-slate-100">
                  {zipFile ? zipFile.name : 'ZIP Arşivini Buraya Bırakın veya Seçin'}
                </span>
                <span className="text-xs text-slate-400">Tüm proje otomatik taranır ve raporlanır</span>
              </label>
            </div>
          )}

          {errorMsg && (
            <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-400 flex items-center gap-3">
              <AlertOctagon className="w-5 h-5 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* STATUS & PROGRESS BAR DISPLAY WHEN LOADING */}
          {loading && (
            <div className="mt-6 bg-indigo-600/15 border border-indigo-500/40 rounded-xl p-5 text-sm text-indigo-200 space-y-3">
              <div className="flex items-center justify-between font-mono">
                <span className="flex items-center gap-3 font-semibold">
                  <div className="w-4 h-4 border-2 border-indigo-300 border-t-transparent rounded-full animate-spin shrink-0" />
                  {statusText}
                </span>
                <span className="font-bold text-base text-indigo-300">{progressPct}%</span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-3 overflow-hidden border border-slate-700">
                <div
                  className="bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 h-full transition-all duration-300 rounded-full"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </div>
          )}

          {/* DEVA ACTION BUTTON */}
          <div className="mt-8 flex justify-end">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="flex items-center gap-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-sm px-10 py-4 rounded-xl shadow-xl shadow-indigo-600/30 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Taranıyor...</span>
                </>
              ) : (
                <>
                  <Play className="w-5 h-5 fill-current" />
                  <span>🔍 Analiz Et</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* RESULTS SECTION (SINGLE FILE) */}
        {singleResult && (
          <div className="space-y-6 mt-4">
            {/* METRICS ROW */}
            <div className="grid grid-cols-4 gap-5">
              <div className="bg-slate-800/90 border border-slate-700 rounded-xl p-5">
                <span className="text-xs text-slate-400 block mb-1 font-semibold">Dil / Language</span>
                <span className="text-xl font-bold text-slate-100 uppercase">{singleResult.static.language}</span>
              </div>
              <div className="bg-slate-800/90 border border-slate-700 rounded-xl p-5">
                <span className="text-xs text-slate-400 block mb-1 font-semibold">Statik Bulgular</span>
                <span className="text-xl font-bold text-indigo-400">{singleResult.static.findings.length}</span>
              </div>
              <div className="bg-slate-800/90 border border-slate-700 rounded-xl p-5">
                <span className="text-xs text-slate-400 block mb-1 font-semibold">AI Insights</span>
                <span className="text-xl font-bold text-purple-400">{singleResult.ai.findings?.length || 0}</span>
              </div>
              <div className="bg-slate-800/90 border border-slate-700 rounded-xl p-5">
                <span className="text-xs text-slate-400 block mb-1 font-semibold">AI Durumu</span>
                <span className="text-sm font-bold text-emerald-400">
                  {singleResult.ai.skipped ? 'Atlandı' : 'Tamamlandı'}
                </span>
              </div>
            </div>

            {/* TABS */}
            <div className="border-b border-slate-700 flex gap-8">
              <button
                onClick={() => setActiveTab('static')}
                className={`pb-4 text-base font-bold flex items-center gap-2 border-b-2 transition ${
                  activeTab === 'static'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Shield className="w-5 h-5" />
                <span>Statik Analiz ({singleResult.static.findings.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('ai')}
                className={`pb-4 text-base font-bold flex items-center gap-2 border-b-2 transition ${
                  activeTab === 'ai'
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Sparkles className="w-5 h-5" />
                <span>AI Insights ({singleResult.ai.findings?.length || 0})</span>
              </button>
              <button
                onClick={() => setActiveTab('code')}
                className={`pb-4 text-base font-bold flex items-center gap-2 border-b-2 transition ${
                  activeTab === 'code'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Code2 className="w-5 h-5" />
                <span>Kaynak Kod</span>
              </button>
              <button
                onClick={() => setActiveTab('report')}
                className={`pb-4 text-base font-bold flex items-center gap-2 border-b-2 transition ${
                  activeTab === 'report'
                    ? 'border-emerald-500 text-emerald-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <FileText className="w-5 h-5" />
                <span>Rapor</span>
              </button>
            </div>

            {/* TAB CONTENTS */}
            {activeTab === 'static' && (
              <div className="space-y-4">
                {singleResult.static.syntax_error && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-400">
                    Syntax Hatası: {singleResult.static.syntax_error}
                  </div>
                )}
                {singleResult.static.findings.length === 0 ? (
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-8 text-center text-base text-emerald-400 flex items-center justify-center gap-3">
                    <CheckCircle2 className="w-6 h-6" />
                    <span>Statik analiz herhangi bir ihlal tespit etmedi.</span>
                  </div>
                ) : (
                  singleResult.static.findings.map((f, i) => (
                    <FindingCard key={i} finding={f} source="static" />
                  ))
                )}
              </div>
            )}

            {activeTab === 'ai' && (
              <div className="space-y-4">
                {singleResult.ai.skipped ? (
                  <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5 text-sm text-amber-300 flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 shrink-0" />
                    <span>⚠️ AI İncelemesi Atlandı (Token/API Sınırı): {singleResult.ai.error || 'API anahtarı eksik veya kota aşımı.'}</span>
                  </div>
                ) : singleResult.ai.error ? (
                  <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5 text-sm text-amber-300 flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 shrink-0" />
                    <span>⚠️ AI İncelemesi Hatası: {singleResult.ai.error}</span>
                  </div>
                ) : !singleResult.ai.findings || singleResult.ai.findings.length === 0 ? (
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-8 text-center text-base text-emerald-400 flex items-center justify-center gap-3">
                    <CheckCircle2 className="w-6 h-6" />
                    <span>✅ AI modeli bu dosyayı inceledi ve herhangi bir hata/risk bulamadı.</span>
                  </div>
                ) : (
                  singleResult.ai.findings.map((f, i) => (
                    <FindingCard key={i} finding={f} source="ai" />
                  ))
                )}
              </div>
            )}

            {activeTab === 'code' && (
              <CodeViewer
                code={singleInputType === 'upload' ? 'yüklenen dosya içeriği' : pastedCode}
                filename={singleResult.filename}
              />
            )}

            {activeTab === 'report' && (
              <div className="space-y-4">
                <div className="flex justify-end">
                  <button
                    onClick={() => downloadReport(singleResult.report, `report_${singleResult.filename}.txt`)}
                    className="flex items-center gap-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm px-5 py-2.5 rounded-lg font-bold transition"
                  >
                    <Download className="w-4 h-4" />
                    <span>TXT Raporu İndir</span>
                  </button>
                </div>
                <pre className="bg-slate-950 border border-slate-800 rounded-xl p-6 font-mono text-xs text-slate-300 overflow-x-auto max-h-[500px]">
                  {singleResult.report}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* DIRECTORY / ZIP RESULT VIEW */}
        {dirResult && (
          <div className="space-y-6 mt-4">
            <div className="flex items-center justify-between bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl">
              <div>
                <h3 className="text-xl font-bold text-slate-100 mb-1">
                  Proje: {dirResult.directory}
                </h3>
                <p className="text-sm text-slate-300">
                  Toplam {dirResult.total_files} dosya taranarak analiz edildi.
                </p>
              </div>
              <button
                onClick={() => downloadReport(dirResult.report, `project_review_${dirResult.directory}.txt`)}
                className="flex items-center gap-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm px-6 py-3 rounded-xl font-bold transition shadow-lg shadow-emerald-600/20"
              >
                <Download className="w-5 h-5" />
                <span>Proje Raporunu İndir (TXT)</span>
              </button>
            </div>

            <div className="space-y-4">
              {dirResult.results.map((item, idx) => {
                const isOpen = activeExpanderFile === item.filepath;
                return (
                  <div key={idx} className="border border-slate-700 rounded-xl overflow-hidden bg-slate-800/90">
                    <button
                      onClick={() => setActiveExpanderFile(isOpen ? null : item.filepath)}
                      className="w-full px-6 py-5 flex items-center justify-between hover:bg-slate-700/80 transition text-left"
                    >
                      <div className="flex items-center gap-4">
                        <ChevronRight className={`w-5 h-5 text-slate-400 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
                        <span className="font-mono text-sm font-bold text-slate-100">{item.filepath}</span>
                        <span className="text-xs uppercase font-mono px-3 py-1 rounded-md bg-slate-900 text-slate-200 border border-slate-700 font-bold">
                          {item.language}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 font-mono text-sm">
                        <span className="text-red-400 bg-red-500/20 px-3 py-1 rounded-lg border border-red-500/30 font-bold">
                          H:{item.high_count}
                        </span>
                        <span className="text-amber-400 bg-amber-500/20 px-3 py-1 rounded-lg border border-amber-500/30 font-bold">
                          M:{item.medium_count}
                        </span>
                        <span className="text-emerald-400 bg-emerald-500/20 px-3 py-1 rounded-lg border border-emerald-500/30 font-bold">
                          L:{item.low_count}
                        </span>
                      </div>
                    </button>

                    {isOpen && (
                      <div className="p-6 border-t border-slate-700 space-y-6 bg-slate-950">
                        {/* STATİK ANALİZ BULGULARI */}
                        <div>
                          <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <Shield className="w-5 h-5 text-indigo-400" />
                            <span>Statik Analiz Bulguları ({item.static.findings.length})</span>
                          </h4>
                          {item.static.findings.length === 0 ? (
                            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 text-sm text-emerald-400 flex items-center gap-2">
                              <CheckCircle2 className="w-5 h-5" />
                              <span>Statik analiz herhangi bir hata tespit etmedi.</span>
                            </div>
                          ) : (
                            item.static.findings.map((f, i) => (
                              <FindingCard key={i} finding={f} source="static" />
                            ))
                          )}
                        </div>

                        {/* AI REVIEW BULGULARI */}
                        <div>
                          <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-purple-400" />
                            <span>AI Review Bulguları ({item.ai.findings?.length || 0})</span>
                          </h4>
                          {item.ai.skipped ? (
                            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-sm text-amber-300 flex items-center gap-3 font-mono">
                              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                              <span>⚠️ AI İncelemesi Atlandı (Token/Rate Sınırı): {item.ai.error || 'Kota sınırı.'}</span>
                            </div>
                          ) : item.ai.error ? (
                            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-sm text-amber-300 flex items-center gap-3 font-mono">
                              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                              <span>⚠️ AI Hatası: {item.ai.error}</span>
                            </div>
                          ) : !item.ai.findings || item.ai.findings.length === 0 ? (
                            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 text-sm text-emerald-400 flex items-center gap-3 font-mono">
                              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                              <span>✅ AI modeli bu dosyayı başarıyla inceledi ve herhangi bir hata bulamadı.</span>
                            </div>
                          ) : (
                            item.ai.findings.map((f, i) => (
                              <FindingCard key={i} finding={f} source="ai" />
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>

      {/* FOOTER STATUS BAR */}
      <footer className="bg-slate-950 border-t border-slate-800 px-8 py-3.5 flex items-center justify-between text-xs font-mono text-slate-300">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-2 text-emerald-400 font-bold">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            FastAPI Server (Port 8000)
          </span>
          <span className="text-slate-700">|</span>
          <span>Next.js Frontend (Port 3000)</span>
        </div>
        <div>
          <span>AI Code Reviewer Engine v2.0</span>
        </div>
      </footer>
    </div>
  );
}

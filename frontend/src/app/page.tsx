'use client';

import React, { useState } from 'react';
import { Header } from '../components/Header';
import { ControlBar } from '../components/ControlBar';
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
  Terminal
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
  const [pastedCode, setPastedCode] = useState<string>('def hello():\n    eval("print(123)")\n');
  const [dirPathInput, setDirPathInput] = useState<string>('');
  const [zipFile, setZipFile] = useState<File | null>(null);

  // States
  const [loading, setLoading] = useState<boolean>(false);
  const [statusText, setStatusText] = useState<string>('Analiz ediliyor...');
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

        setStatusText(`${fileNameToSend} statik analiz & AI incelemesi yapılıyor...`);

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

        const data: SingleAnalyzeResponse = await res.json();
        setSingleResult(data);
      } else if (mode === 'directory') {
        if (!dirPathInput.trim()) {
          throw new Error('Lütfen taranacak klasör yolunu girin.');
        }

        setStatusText(`"${dirPathInput.trim()}" projesi taranıyor ve analiz ediliyor...`);

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

        const data: DirectoryAnalyzeResponse = await res.json();
        setDirResult(data);
      } else if (mode === 'zip') {
        if (!zipFile) {
          throw new Error('Lütfen bir .zip dosyası yükleyin.');
        }

        setStatusText(`${zipFile.name} ZIP arşivi çıkarılıyor ve taranıyor...`);

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

        const data: DirectoryAnalyzeResponse = await res.json();
        setDirResult(data);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Bilinmeyen bir hata oluştu.');
    } finally {
      setLoading(false);
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header />

      {/* TOP NEON PROGRESS BAR */}
      {loading && (
        <div className="w-full h-1 bg-slate-900 overflow-hidden relative">
          <div className="w-full h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 animate-pulse" />
        </div>
      )}

      <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
        {/* CONTROL HUB BAR */}
        <ControlBar
          mode={mode}
          setMode={setMode}
          enableAi={enableAi}
          setEnableAi={setEnableAi}
          selectedModel={selectedModel}
          setSelectedModel={setSelectedModel}
          confidenceThreshold={confidenceThreshold}
          setConfidenceThreshold={setConfidenceThreshold}
        />

        {/* INPUT PANEL */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 mb-8 backdrop-blur-sm shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              {mode === 'single' && <FileText className="w-4 h-4 text-indigo-400" />}
              {mode === 'directory' && <FolderSearch className="w-4 h-4 text-indigo-400" />}
              {mode === 'zip' && <Upload className="w-4 h-4 text-indigo-400" />}
              <span>
                {mode === 'single' && 'Tek Dosya / Kod İnceleme Girdisi'}
                {mode === 'directory' && 'Yerel Klasör Yolu İle Tarama'}
                {mode === 'zip' && 'ZIP Proje Arşivi Yükleme'}
              </span>
            </h2>
          </div>

          {mode === 'single' && (
            <div className="space-y-4">
              <div className="flex gap-3 border-b border-slate-800/80 pb-3">
                <button
                  onClick={() => setSingleInputType('upload')}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition ${
                    singleInputType === 'upload'
                      ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Dosya Yükle (.py, .cpp, .java)
                </button>
                <button
                  onClick={() => setSingleInputType('paste')}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition ${
                    singleInputType === 'paste'
                      ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Kod Yapıştır
                </button>
              </div>

              {singleInputType === 'upload' ? (
                <div className="border-2 border-dashed border-slate-800 hover:border-indigo-500/50 rounded-xl p-8 text-center transition bg-slate-950/40">
                  <input
                    type="file"
                    onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="single-file-input"
                  />
                  <label htmlFor="single-file-input" className="cursor-pointer flex flex-col items-center gap-2">
                    <Upload className="w-8 h-8 text-slate-500" />
                    <span className="text-sm font-medium text-slate-300">
                      {uploadedFile ? uploadedFile.name : 'Dosya Seçin veya Sürükleyin'}
                    </span>
                    <span className="text-xs text-slate-500">Desteklenen diller: .py, .c, .cpp, .java</span>
                  </label>
                </div>
              ) : (
                <div>
                  <textarea
                    value={pastedCode}
                    onChange={(e) => setPastedCode(e.target.value)}
                    rows={7}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                    placeholder="Analiz edilecek kodu buraya yapıştırın..."
                  />
                </div>
              )}
            </div>
          )}

          {mode === 'directory' && (
            <div>
              <label className="text-xs text-slate-400 block mb-2 font-medium">Bilgisayarınızdaki Klasör Yolu:</label>
              <input
                type="text"
                value={dirPathInput}
                onChange={(e) => setDirPathInput(e.target.value)}
                placeholder="./examples veya /Users/kullanici/Desktop/proje"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          {mode === 'zip' && (
            <div className="border-2 border-dashed border-slate-800 hover:border-indigo-500/50 rounded-xl p-8 text-center transition bg-slate-950/40">
              <input
                type="file"
                accept=".zip"
                onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                className="hidden"
                id="zip-file-input"
              />
              <label htmlFor="zip-file-input" className="cursor-pointer flex flex-col items-center gap-2">
                <Upload className="w-8 h-8 text-slate-500" />
                <span className="text-sm font-medium text-slate-300">
                  {zipFile ? zipFile.name : 'ZIP Arşivi Seçin veya Bırakın'}
                </span>
                <span className="text-xs text-slate-500">Tüm proje dosyaları taranır</span>
              </label>
            </div>
          )}

          {errorMsg && (
            <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-xl p-3.5 text-xs text-red-400 flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* STATUS DISPLAY WHEN LOADING */}
          {loading && (
            <div className="mt-4 bg-indigo-500/10 border border-indigo-500/30 rounded-xl p-3.5 text-xs text-indigo-300 flex items-center gap-3">
              <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin shrink-0" />
              <span className="font-mono">{statusText}</span>
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="flex items-center gap-2 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold text-xs px-7 py-3 rounded-xl shadow-lg shadow-indigo-600/25 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Analiz Sürüyor...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>🔍 Analizi Başlat</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* SINGLE RESULT VIEW */}
        {singleResult && (
          <div className="space-y-6">
            {/* METRICS ROW */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1 font-medium">Dil / Language</span>
                <span className="text-lg font-bold text-slate-100 uppercase">{singleResult.static.language}</span>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1 font-medium">Statik Bulgular</span>
                <span className="text-lg font-bold text-indigo-400">{singleResult.static.findings.length}</span>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1 font-medium font-medium">AI Insights</span>
                <span className="text-lg font-bold text-purple-400">{singleResult.ai.findings?.length || 0}</span>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1 font-medium">AI Durumu</span>
                <span className="text-xs font-semibold text-emerald-400">
                  {singleResult.ai.skipped ? 'Atlandı' : 'Tamamlandı'}
                </span>
              </div>
            </div>

            {/* TABS */}
            <div className="border-b border-slate-800 flex gap-6">
              <button
                onClick={() => setActiveTab('static')}
                className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                  activeTab === 'static'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Shield className="w-4 h-4" />
                <span>Statik Analiz ({singleResult.static.findings.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('ai')}
                className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                  activeTab === 'ai'
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                <span>AI Insights ({singleResult.ai.findings?.length || 0})</span>
              </button>
              <button
                onClick={() => setActiveTab('code')}
                className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                  activeTab === 'code'
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Code2 className="w-4 h-4" />
                <span>Kaynak Kod</span>
              </button>
              <button
                onClick={() => setActiveTab('report')}
                className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
                  activeTab === 'report'
                    ? 'border-emerald-500 text-emerald-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <FileText className="w-4 h-4" />
                <span>Rapor</span>
              </button>
            </div>

            {/* TAB CONTENTS */}
            {activeTab === 'static' && (
              <div className="space-y-3">
                {singleResult.static.syntax_error && (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-xs text-red-400">
                    Syntax Hatası: {singleResult.static.syntax_error}
                  </div>
                )}
                {singleResult.static.findings.length === 0 ? (
                  <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-6 text-center text-sm text-emerald-400 flex items-center justify-center gap-2">
                    <CheckCircle2 className="w-5 h-5" />
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
              <div className="space-y-3">
                {singleResult.ai.skipped ? (
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-xs text-slate-400">
                    ℹ️ {singleResult.ai.error || 'AI İncelemesi atlandı.'}
                  </div>
                ) : singleResult.ai.error ? (
                  <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-xs text-red-400">
                    ❌ {singleResult.ai.error}
                  </div>
                ) : !singleResult.ai.findings || singleResult.ai.findings.length === 0 ? (
                  <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-6 text-center text-sm text-emerald-400 flex items-center justify-center gap-2">
                    <CheckCircle2 className="w-5 h-5" />
                    <span>AI modeli herhangi bir potansiyel problem tespit etmedi.</span>
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
                    className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-4 py-2 rounded-lg font-medium transition"
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
          <div className="space-y-6">
            <div className="flex items-center justify-between bg-slate-900/60 border border-slate-800 rounded-xl p-6">
              <div>
                <h3 className="text-lg font-bold text-slate-100 mb-1">
                  Proje: {dirResult.directory}
                </h3>
                <p className="text-xs text-slate-400">
                  Toplam {dirResult.total_files} dosya taranarak analiz edildi.
                </p>
              </div>
              <button
                onClick={() => downloadReport(dirResult.report, `project_review_${dirResult.directory}.txt`)}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-4 py-2.5 rounded-xl font-medium transition shadow-lg shadow-emerald-600/20"
              >
                <Download className="w-4 h-4" />
                <span>Proje Raporunu İndir (TXT)</span>
              </button>
            </div>

            <div className="space-y-3">
              {dirResult.results.map((item, idx) => {
                const isOpen = activeExpanderFile === item.filepath;
                return (
                  <div key={idx} className="border border-slate-800/80 rounded-xl overflow-hidden bg-slate-900/40">
                    <button
                      onClick={() => setActiveExpanderFile(isOpen ? null : item.filepath)}
                      className="w-full px-5 py-4 flex items-center justify-between hover:bg-slate-900/80 transition text-left"
                    >
                      <div className="flex items-center gap-3">
                        <ChevronRight className={`w-4 h-4 text-slate-500 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
                        <span className="font-mono text-xs font-semibold text-slate-200">{item.filepath}</span>
                        <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                          {item.language}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 font-mono text-xs">
                        <span className="text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                          H:{item.high_count}
                        </span>
                        <span className="text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                          M:{item.medium_count}
                        </span>
                        <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          L:{item.low_count}
                        </span>
                      </div>
                    </button>

                    {isOpen && (
                      <div className="p-5 border-t border-slate-800/80 space-y-4 bg-slate-950/60">
                        <div>
                          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                            Statik Analiz Bulguları ({item.static.findings.length})
                          </h4>
                          {item.static.findings.length === 0 ? (
                            <p className="text-xs text-emerald-400">Statik analiz bulgusu yok.</p>
                          ) : (
                            item.static.findings.map((f, i) => (
                              <FindingCard key={i} finding={f} source="static" />
                            ))
                          )}
                        </div>

                        <div>
                          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                            AI Review Bulguları ({item.ai.findings?.length || 0})
                          </h4>
                          {item.ai.skipped ? (
                            <p className="text-xs text-slate-500">ℹ️ {item.ai.error}</p>
                          ) : item.ai.error ? (
                            <p className="text-xs text-red-400">❌ AI Hatası: {item.ai.error}</p>
                          ) : !item.ai.findings || item.ai.findings.length === 0 ? (
                            <p className="text-xs text-emerald-400">AI inceleme bulgusu yok.</p>
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

        {/* WELCOME DASHBOARD (No results yet) */}
        {!singleResult && !dirResult && !loading && (
          <div className="border border-slate-800/80 bg-slate-900/30 rounded-2xl p-12 text-center my-6 backdrop-blur-sm">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-4 text-indigo-400">
              <Shield className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-slate-100 mb-2">Analize Başlamaya Hazır Mısınız?</h3>
            <p className="text-sm text-slate-400 max-w-lg mx-auto mb-8 leading-relaxed">
              Üst bardan modunuzu seçin (Tek Dosya, Yerel Klasör veya ZIP) ve <b>🔍 Analizi Başlat</b> butonuna tıklayın.
            </p>
            <div className="grid grid-cols-4 gap-4 max-w-2xl mx-auto">
              <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl text-center">
                <div className="text-2xl mb-1">🐍</div>
                <div className="text-xs font-semibold text-slate-200">Python</div>
                <div className="text-[10px] text-slate-500 mt-1">AST & Güvenlik</div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl text-center">
                <div className="text-2xl mb-1">⚡</div>
                <div className="text-xs font-semibold text-slate-200">C / C++</div>
                <div className="text-[10px] text-slate-500 mt-1">Bellek & Buffer</div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl text-center">
                <div className="text-2xl mb-1">☕</div>
                <div className="text-xs font-semibold text-slate-200">Java</div>
                <div className="text-[10px] text-slate-500 mt-1">SQLi & Inj.</div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl text-center">
                <div className="text-2xl mb-1">🤖</div>
                <div className="text-xs font-semibold text-slate-200">Qwen AI</div>
                <div className="text-[10px] text-slate-500 mt-1">Derin Kod İnceleme</div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

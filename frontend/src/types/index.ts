export interface Finding {
  severity: "HIGH" | "MEDIUM" | "LOW" | string;
  category: string;
  line: number | null;
  line_range?: string | null;
  message: string;
  suggestion?: string | null;
  confidence: number;
}

export interface StaticResult {
  language: string;
  syntax_error?: string | null;
  findings: Finding[];
}

export interface AIResult {
  skipped: boolean;
  error?: string | null;
  findings: Finding[];
  raw_response?: string;
  model_used?: string;
  parse_failed?: boolean;
}

export interface SingleAnalyzeResponse {
  filename: string;
  static: StaticResult;
  ai: AIResult;
  report: string;
  report_path?: string;
}

export interface FileScanItem {
  filepath: string;
  abs_path?: string;
  language: string;
  total_findings: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  static: StaticResult;
  ai: AIResult;
}

export interface DirectoryAnalyzeResponse {
  directory: string;
  total_files: number;
  results: FileScanItem[];
  report: string;
  report_path?: string;
}

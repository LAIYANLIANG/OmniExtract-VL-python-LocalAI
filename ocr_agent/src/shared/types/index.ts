// User types
export interface User {
  id: string;
  email: string;
  username: string;
  fullName: string;
  role: UserRole;
  department?: string;
  status: UserStatus;
  createdAt: Date;
  updatedAt: Date;
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user',
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
}

// File types
export interface FileMetadata {
  id: string;
  originalName: string;
  storedName: string;
  mimeType: string;
  size: number;
  uploadedBy: string;
  department?: string;
  status: FileStatus;
  processedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export enum FileStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum FileType {
  EXCEL = 'excel',
  PDF = 'pdf',
  WORD = 'word',
  POWERPOINT = 'powerpoint',
}

// Task types
export interface Task {
  id: string;
  type: TaskType;
  fileId: string;
  userId: string;
  status: TaskStatus;
  progress: number;
  result?: any;
  error?: string;
  startedAt?: Date;
  completedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export enum TaskType {
  FILE_PARSE = 'file_parse',
  OCR_PROCESS = 'ocr_process',
  AI_CLASSIFY = 'ai_classify',
  DATA_EXTRACT = 'data_extract',
}

export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Audit log types
export interface AuditLog {
  id: string;
  userId: string;
  action: string;
  resource: string;
  resourceId?: string;
  details?: any;
  ipAddress?: string;
  userAgent?: string;
  timestamp: Date;
}

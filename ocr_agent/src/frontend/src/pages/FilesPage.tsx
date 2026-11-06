import React from 'react';
import {
  DocumentArrowUpIcon,
  DocumentTextIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';

export default function FilesPage() {
  // 模拟文件列表数据
  const files = [
    {
      id: '1',
      name: '财务报表_2023Q4.xlsx',
      type: 'Excel',
      size: '2.5 MB',
      status: '已完成',
      uploadedAt: '2026-03-28 14:30',
      statusColor: 'text-green-600 bg-green-50',
    },
    {
      id: '2',
      name: '采购订单汇总.pdf',
      type: 'PDF',
      size: '5.2 MB',
      status: '处理中',
      uploadedAt: '2026-03-29 10:15',
      statusColor: 'text-yellow-600 bg-yellow-50',
    },
    {
      id: '3',
      name: '员工考勤统计.xlsx',
      type: 'Excel',
      size: '1.8 MB',
      status: '等待中',
      uploadedAt: '2026-03-29 09:45',
      statusColor: 'text-gray-600 bg-gray-50',
    },
  ];

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">文件管理</h1>
        <button className="btn btn-primary flex items-center">
          <DocumentArrowUpIcon className="h-5 w-5 mr-2" />
          上传文件
        </button>
      </div>

      {/* 搜索和筛选 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="搜索文件名..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <select className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
            <option>所有类型</option>
            <option>Excel</option>
            <option>PDF</option>
            <option>Word</option>
          </select>
          <select className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
            <option>所有状态</option>
            <option>已完成</option>
            <option>处理中</option>
            <option>等待中</option>
          </select>
        </div>
      </div>

      {/* 上传区域 */}
      <div className="bg-white rounded-lg shadow p-8">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-primary-500 hover:bg-primary-50/50 transition-colors cursor-pointer">
          <DocumentArrowUpIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">
            点击上传或拖拽文件到此处
          </p>
          <p className="text-sm text-gray-500">
            支持 Excel (.xlsx, .xls)、PDF、Word (.docx)、PowerPoint (.pptx)
          </p>
          <p className="text-xs text-gray-400 mt-2">
            最大文件大小：Excel 100MB, PDF 50MB
          </p>
        </div>
      </div>

      {/* 文件列表 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            最近文件 ({files.length})
          </h2>
        </div>
        <div className="divide-y divide-gray-200">
          {files.map((file) => (
            <div
              key={file.id}
              className="px-6 py-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 flex-1">
                  <DocumentTextIcon className="h-10 w-10 text-primary-600" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {file.type} · {file.size} · {file.uploadedAt}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${file.statusColor}`}
                  >
                    {file.status}
                  </span>
                  <div className="flex space-x-2">
                    <button
                      className="p-2 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-primary-50"
                      title="下载"
                    >
                      <ArrowDownTrayIcon className="h-5 w-5" />
                    </button>
                    <button
                      className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                      title="删除"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 空状态提示（当没有文件时显示） */}
      {files.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <DocumentTextIcon className="h-16 w-16 mx-auto text-gray-300 mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">
            还没有上传任何文件
          </p>
          <p className="text-sm text-gray-500 mb-6">
            开始上传文件进行处理
          </p>
          <button className="btn btn-primary">
            上传第一个文件
          </button>
        </div>
      )}
    </div>
  );
}

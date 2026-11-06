import React from 'react';
import {
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

export default function TasksPage() {
  // 模拟任务数据
  const tasks = [
    {
      id: '1',
      fileName: '财务报表_2023Q4.xlsx',
      type: 'Excel 解析',
      status: 'completed',
      statusText: '已完成',
      progress: 100,
      startTime: '2026-03-29 14:30:00',
      endTime: '2026-03-29 14:31:25',
      duration: '1分25秒',
    },
    {
      id: '2',
      fileName: '采购订单汇总.pdf',
      type: 'PDF OCR 识别',
      status: 'running',
      statusText: '处理中',
      progress: 65,
      startTime: '2026-03-29 15:20:00',
      endTime: '-',
      duration: '进行中',
    },
    {
      id: '3',
      fileName: '员工考勤统计.xlsx',
      type: '数据提取',
      status: 'pending',
      statusText: '等待中',
      progress: 0,
      startTime: '-',
      endTime: '-',
      duration: '-',
    },
    {
      id: '4',
      fileName: '发票扫描件.pdf',
      type: 'PDF OCR 识别',
      status: 'failed',
      statusText: '失败',
      progress: 45,
      startTime: '2026-03-29 13:15:00',
      endTime: '2026-03-29 13:16:30',
      duration: '1分30秒',
      error: '文件格式不支持或损坏',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-6 w-6 text-green-600" />;
      case 'running':
        return <ArrowPathIcon className="h-6 w-6 text-blue-600 animate-spin" />;
      case 'pending':
        return <ClockIcon className="h-6 w-6 text-gray-400" />;
      case 'failed':
        return <XCircleIcon className="h-6 w-6 text-red-600" />;
      default:
        return <ClockIcon className="h-6 w-6 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'running':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'pending':
        return 'bg-gray-50 text-gray-700 border-gray-200';
      case 'failed':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const stats = [
    { label: '总任务', value: tasks.length, color: 'text-gray-900' },
    {
      label: '已完成',
      value: tasks.filter((t) => t.status === 'completed').length,
      color: 'text-green-600',
    },
    {
      label: '处理中',
      value: tasks.filter((t) => t.status === 'running').length,
      color: 'text-blue-600',
    },
    {
      label: '失败',
      value: tasks.filter((t) => t.status === 'failed').length,
      color: 'text-red-600',
    },
  ];

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">任务监控</h1>
        <p className="text-gray-600 mt-2">实时追踪文件处理进度</p>
      </div>

      {/* 统计概览 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
            <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* 任务列表 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">任务列表</h2>
            <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              刷新
            </button>
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {tasks.map((task) => (
            <div key={task.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-start space-x-4">
                {/* 状态图标 */}
                <div className="flex-shrink-0 mt-1">
                  {getStatusIcon(task.status)}
                </div>

                {/* 任务信息 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-base font-medium text-gray-900 truncate">
                      {task.fileName}
                    </h3>
                    <span
                      className={`ml-4 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                        task.status
                      )}`}
                    >
                      {task.statusText}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mb-3">{task.type}</p>

                  {/* 进度条 */}
                  {task.status === 'running' && (
                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>处理进度</span>
                        <span>{task.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${task.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}

                  {/* 错误信息 */}
                  {task.status === 'failed' && task.error && (
                    <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-700">
                        <span className="font-medium">错误：</span>
                        {task.error}
                      </p>
                    </div>
                  )}

                  {/* 时间信息 */}
                  <div className="flex items-center space-x-6 text-xs text-gray-500">
                    <span>开始：{task.startTime}</span>
                    <span>结束：{task.endTime}</span>
                    <span>耗时：{task.duration}</span>
                  </div>
                </div>

                {/* 操作按钮 */}
                <div className="flex-shrink-0">
                  {task.status === 'running' && (
                    <button className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded border border-red-200">
                      取消
                    </button>
                  )}
                  {task.status === 'failed' && (
                    <button className="px-3 py-1 text-sm text-primary-600 hover:bg-primary-50 rounded border border-primary-200">
                      重试
                    </button>
                  )}
                  {task.status === 'completed' && (
                    <button className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded border border-gray-200">
                      查看结果
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 空状态 */}
      {tasks.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <ClockIcon className="h-16 w-16 mx-auto text-gray-300 mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">暂无任务</p>
          <p className="text-sm text-gray-500">上传文件后任务将显示在此处</p>
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import {
  ChartBarIcon,
  LightBulbIcon,
  PaperAirplaneIcon,
  BookmarkIcon,
  ArrowDownTrayIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  charts?: Chart[];
  insights?: string[];
}

interface Chart {
  id: string;
  type: 'bar' | 'line' | 'pie';
  title: string;
  data: { label: string; value: number; color?: string }[];
}

export default function AnalysisPage() {
  const [inputMessage, setInputMessage] = useState('');
  const [savedNotes, setSavedNotes] = useState<string[]>([]);

  // 引导式快捷问题
  const quickQuestions = [
    '本期的营收和上期比较如何？',
    '帮我分析费用结构占比',
    '应收帐款周转率趋势如何？',
    '帮我做一个获利能力分析',
    '流动比率和速动比率各是多少？',
    '与去年同期相比，哪些科目变动最大？',
  ];

  // 模拟对话记录
  const [messages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: '您好！我是 OCR 智能分析助手。\n\n我可以帮您分析财务报表、计算财务比率、找出异常变动，并生成图表。\n\n您可以直接提问，或选择下方的快捷问题开始分析。',
      timestamp: '15:30',
    },
    {
      id: '2',
      role: 'user',
      content: '帮我分析本期的费用结构',
      timestamp: '15:31',
    },
    {
      id: '3',
      role: 'assistant',
      content: '好的，以下是 **2025年12月** 费用结构分析：\n\n### 📊 费用结构概览\n\n本期总费用为 **26,300,000 元**，依各费用占比分析如下：',
      timestamp: '15:31',
      charts: [
        {
          id: 'c1',
          type: 'bar',
          title: '费用结构分析 (2025-12)',
          data: [
            { label: '管理费用', value: 12500000, color: '#3B82F6' },
            { label: '销售费用', value: 8200000, color: '#10B981' },
            { label: '研发费用', value: 5600000, color: '#F59E0B' },
          ],
        },
      ],
      insights: [
        '管理费用占比最高 (47.5%)，建议检视各项管理支出明细',
        '研发费用占 21.3%，低于同业平均 25%，可能影响长期竞争力',
        '销售费用较上期增长 12%，需确认是否有对应的营收增长',
      ],
    },
    {
      id: '4',
      role: 'user',
      content: '营收对应的增长情况呢？',
      timestamp: '15:32',
    },
    {
      id: '5',
      role: 'assistant',
      content: '让我帮您对比营收和费用的增长趋势：\n\n### 📈 营收 vs 费用增长对比',
      timestamp: '15:32',
      charts: [
        {
          id: 'c2',
          type: 'bar',
          title: '营收与费用月趋势',
          data: [
            { label: '10月营收', value: 88500, color: '#3B82F6' },
            { label: '10月费用', value: 24800, color: '#EF4444' },
            { label: '11月营收', value: 91200, color: '#3B82F6' },
            { label: '11月费用', value: 25100, color: '#EF4444' },
            { label: '12月营收', value: 96500, color: '#3B82F6' },
            { label: '12月费用', value: 26300, color: '#EF4444' },
          ],
        },
      ],
      insights: [
        '✅ 12月营收较10月成长 9.04%，费用成长 6.05%，营收增速高于费用，正面趋势',
        '📌 营业利益率从 10月 71.98% → 12月 72.75%，小幅改善',
        '⚠️ 销售费用增长 12% 但营收只增 5.8%（月对月），销售效率需关注',
      ],
    },
  ]);

  const formatChartBar = (value: number, maxValue: number, color: string) => {
    const percentage = (value / maxValue) * 100;
    return (
      <div className="flex items-center space-x-3">
        <div className="w-full bg-gray-100 rounded-full h-6 relative">
          <div
            className="h-6 rounded-full transition-all duration-500 flex items-center justify-end pr-2"
            style={{ width: `${Math.max(percentage, 8)}%`, backgroundColor: color }}
          >
            <span className="text-xs font-medium text-white">
              {new Intl.NumberFormat('zh-TW').format(value)}
            </span>
          </div>
        </div>
      </div>
    );
  };

  const saveInsight = (text: string) => {
    if (!savedNotes.includes(text)) {
      setSavedNotes([...savedNotes, text]);
    }
  };

  return (
    <div className="flex h-[calc(100vh-180px)] space-x-6">
      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col bg-white rounded-lg shadow">
        {/* 标题 */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <SparklesIcon className="h-6 w-6 text-primary-600" />
              <h1 className="text-xl font-bold text-gray-900">AI 财报分析</h1>
            </div>
            <div className="flex space-x-2">
              <button className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 rounded border hover:bg-gray-50">
                清除对话
              </button>
              <button className="text-sm text-primary-600 flex items-center px-3 py-1 rounded border border-primary-200 hover:bg-primary-50">
                <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                导出分析
              </button>
            </div>
          </div>
        </div>

        {/* 消息区域 */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] ${
                msg.role === 'user'
                  ? 'bg-primary-600 text-white rounded-2xl rounded-br-md px-5 py-3'
                  : 'bg-gray-50 text-gray-900 rounded-2xl rounded-bl-md px-5 py-4'
              }`}>
                {/* 消息文字 */}
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.content.split('\n').map((line, i) => {
                    if (line.startsWith('### ')) {
                      return <h3 key={i} className="text-base font-bold mt-2 mb-2">{line.replace('### ', '')}</h3>;
                    }
                    if (line.startsWith('**') && line.endsWith('**')) {
                      return <p key={i} className="font-bold">{line.replace(/\*\*/g, '')}</p>;
                    }
                    return <p key={i}>{line.replace(/\*\*/g, '')}</p>;
                  })}
                </div>

                {/* 图表 */}
                {msg.charts && msg.charts.map((chart) => (
                  <div key={chart.id} className="mt-4 bg-white rounded-lg p-4 border">
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">{chart.title}</h4>
                    <div className="space-y-3">
                      {chart.data.map((d, i) => {
                        const maxVal = Math.max(...chart.data.map((x) => x.value));
                        return (
                          <div key={i}>
                            <div className="flex justify-between text-xs text-gray-600 mb-1">
                              <span>{d.label}</span>
                            </div>
                            {formatChartBar(d.value, maxVal, d.color || '#3B82F6')}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}

                {/* 洞察 */}
                {msg.insights && (
                  <div className="mt-4 space-y-2">
                    <h4 className="text-sm font-semibold text-gray-700 flex items-center">
                      <LightBulbIcon className="h-4 w-4 mr-1 text-yellow-500" />
                      分析洞察
                    </h4>
                    {msg.insights.map((insight, i) => (
                      <div key={i} className="flex items-start justify-between bg-yellow-50 rounded-lg p-3 border border-yellow-100 group">
                        <p className="text-sm text-gray-700 flex-1">{insight}</p>
                        <button
                          onClick={() => saveInsight(insight)}
                          className="ml-3 text-gray-400 hover:text-primary-600 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                          title="保存为笔记"
                        >
                          <BookmarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <span className={`text-xs mt-2 block ${
                  msg.role === 'user' ? 'text-primary-200' : 'text-gray-400'
                }`}>{msg.timestamp}</span>
              </div>
            </div>
          ))}
        </div>

        {/* 快捷问题 */}
        <div className="px-6 py-3 border-t border-gray-100">
          <div className="flex items-center space-x-2 overflow-x-auto pb-2">
            <span className="text-xs text-gray-500 flex-shrink-0">引导：</span>
            {quickQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => setInputMessage(q)}
                className="flex-shrink-0 px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-primary-100 hover:text-primary-700 transition-colors whitespace-nowrap"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* 输入框 */}
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex space-x-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="输入您的分析问题...例如「帮我分析获利能力」"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              onKeyDown={(e) => e.key === 'Enter' && inputMessage.trim() && setInputMessage('')}
            />
            <button
              className="btn btn-primary flex items-center px-5"
              onClick={() => inputMessage.trim() && setInputMessage('')}
            >
              <PaperAirplaneIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* 右侧笔记面板 */}
      <div className="w-80 bg-white rounded-lg shadow flex flex-col">
        <div className="px-4 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <BookmarkIcon className="h-5 w-5 mr-2 text-primary-600" />
            分析笔记
          </h2>
          <p className="text-xs text-gray-500 mt-1">保存的重点与发现</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {savedNotes.length === 0 ? (
            <div className="text-center py-8">
              <BookmarkIcon className="h-10 w-10 mx-auto text-gray-300 mb-3" />
              <p className="text-sm text-gray-500">还没有保存任何笔记</p>
              <p className="text-xs text-gray-400 mt-1">
                点击分析洞察旁的 <BookmarkIcon className="h-3 w-3 inline" /> 保存为笔记
              </p>
            </div>
          ) : (
            savedNotes.map((note, i) => (
              <div key={i} className="bg-primary-50 rounded-lg p-3 border border-primary-100">
                <p className="text-sm text-gray-700">{note}</p>
                <div className="flex justify-between items-center mt-2">
                  <span className="text-xs text-gray-400">刚刚保存</span>
                  <button
                    onClick={() => setSavedNotes(savedNotes.filter((_, idx) => idx !== i))}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    删除
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* 手动添加笔记 */}
        <div className="p-4 border-t border-gray-200">
          <textarea
            placeholder="手动添加笔记..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none h-20 focus:ring-2 focus:ring-primary-500"
          />
          <div className="flex justify-between mt-2">
            <button className="text-xs text-primary-600 hover:text-primary-700 font-medium">
              组成报表
            </button>
            <button className="btn btn-primary text-xs px-3 py-1">
              保存笔记
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

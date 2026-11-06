import React, { useState } from 'react';
import {
  BookmarkIcon,
  PencilSquareIcon,
  TrashIcon,
  PlusIcon,
  DocumentTextIcon,
  TagIcon,
  ArrowDownTrayIcon,
  FolderIcon,
  ChevronRightIcon,
  MagnifyingGlassIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  linkedAccount?: string;
  linkedReport?: string;
  createdAt: string;
  updatedAt: string;
  isImportant: boolean;
}

export default function NotesPage() {
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [activeTag, setActiveTag] = useState('all');

  const notes: Note[] = [
    {
      id: '1',
      title: '2025 Q4 费用分析重点',
      content: '## 费用结构分析\n\n### 关键发现\n- 管理费用占比 47.5%，为所有费用最高项目\n- 研发费用占 21.3%，低于同业平均 25%\n- 销售费用较上期增长 12%\n\n### 需进一步确认\n- [ ] 管理费用明细中的「顾问费」异常增加 2M，需要向管理部确认\n- [ ] 销售费用增长是否与新市场开拓计划有关\n- [x] 研发费用下降已确认是因为专案完结\n\n### 建议\n1. 管理费用应控制在总费用的 40% 以内\n2. 研发投入需要重新评估，以维持竞争力\n3. 销售费用需要与营收增长做对比分析',
      tags: ['费用分析', 'Q4', '重点'],
      linkedReport: '损益表',
      createdAt: '2026-03-29 15:35',
      updatedAt: '2026-03-29 16:20',
      isImportant: true,
    },
    {
      id: '2',
      title: '应收帐款异常提醒',
      content: '## 应收帐款\n\n### 异常项目\n- 客户 A 帐龄超过 90 天，金额 3,500,000\n- 客户 F 本月新增 5,800,000 未收\n\n### 追踪事项\n- [ ] 联络客户 A 确认付款时间\n- [ ] 客户 F 信用额度审核',
      tags: ['应收帐款', '异常', '追踪'],
      linkedAccount: '1150 应收帐款',
      createdAt: '2026-03-29 14:20',
      updatedAt: '2026-03-29 14:20',
      isImportant: true,
    },
    {
      id: '3',
      title: '现金流量备注',
      content: '## 现金流量\n\n本月现金增加 2,400,000，主要来自：\n- 营业活动：净流入 4,500,000\n- 投资活动：净流出 -1,200,000\n- 融资活动：净流出 -900,000\n\n整体现金部位健康。',
      tags: ['现金流量', '月结'],
      linkedReport: '现金流量表',
      createdAt: '2026-03-28 10:15',
      updatedAt: '2026-03-28 10:15',
      isImportant: false,
    },
    {
      id: '4',
      title: '获利能力指标追踪',
      content: '## 获利能力\n\n| 指标 | 本期 | 上期 | 变动 |\n|------|------|------|------|\n| 毛利率 | 34.9% | 33.2% | +1.7% |\n| 营业利益率 | 7.9% | 7.1% | +0.8% |\n| 税前净利率 | 6.5% | 5.8% | +0.7% |\n| ROE | 5.3% | 4.8% | +0.5% |\n\n### 备注\n- 毛利率改善主要来自原物料成本下降\n- ROE 仍低于目标 8%，需加强',
      tags: ['获利能力', '指标', 'KPI'],
      createdAt: '2026-03-27 09:30',
      updatedAt: '2026-03-29 11:45',
      isImportant: false,
    },
    {
      id: '5',
      title: '年度财报组成笔记',
      content: '## 年度报告要点\n\n### 需要纳入的内容\n1. 营收成长趋势（含图表）\n2. 费用结构分析\n3. 获利能力与同业比较\n4. 现金流量分析\n5. 资产品质评估（应收帐款帐龄）\n6. 负债与偿债能力\n\n### 附注事项\n- 2025年新增长期投资 1,130,000 需要在附注揭露\n- 关系人交易说明\n- 或有负债检视',
      tags: ['年度报告', '组成', '附注'],
      createdAt: '2026-03-25 16:00',
      updatedAt: '2026-03-29 14:30',
      isImportant: true,
    },
  ];

  const allTags = Array.from(new Set(notes.flatMap((n) => n.tags)));

  const filteredNotes = notes.filter((n) => {
    const matchSearch = searchQuery === '' ||
      n.title.includes(searchQuery) ||
      n.content.includes(searchQuery) ||
      n.tags.some((t) => t.includes(searchQuery));
    const matchTag = activeTag === 'all' || n.tags.includes(activeTag);
    return matchSearch && matchTag;
  });

  const renderMarkdown = (content: string) => {
    return content.split('\n').map((line, i) => {
      if (line.startsWith('## ')) {
        return <h2 key={i} className="text-xl font-bold text-gray-900 mt-4 mb-2">{line.replace('## ', '')}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={i} className="text-lg font-semibold text-gray-800 mt-3 mb-1">{line.replace('### ', '')}</h3>;
      }
      if (line.startsWith('- [x] ')) {
        return (
          <div key={i} className="flex items-center space-x-2 ml-4 py-0.5">
            <input type="checkbox" checked readOnly className="rounded text-primary-600" />
            <span className="text-sm text-gray-500 line-through">{line.replace('- [x] ', '')}</span>
          </div>
        );
      }
      if (line.startsWith('- [ ] ')) {
        return (
          <div key={i} className="flex items-center space-x-2 ml-4 py-0.5">
            <input type="checkbox" readOnly className="rounded" />
            <span className="text-sm text-gray-700">{line.replace('- [ ] ', '')}</span>
          </div>
        );
      }
      if (line.startsWith('- ')) {
        return <li key={i} className="text-sm text-gray-700 ml-6 py-0.5">{line.replace('- ', '')}</li>;
      }
      if (line.match(/^\d+\. /)) {
        return <li key={i} className="text-sm text-gray-700 ml-6 py-0.5 list-decimal">{line.replace(/^\d+\. /, '')}</li>;
      }
      if (line.startsWith('| ')) {
        const cells = line.split('|').filter(Boolean).map((c) => c.trim());
        if (cells.every((c) => c.match(/^-+$/))) return null;
        const isHeader = i > 0 && content.split('\n')[i + 1]?.match(/^\|[\s-|]+\|$/);
        return (
          <tr key={i} className={isHeader ? 'bg-gray-100' : 'hover:bg-gray-50'}>
            {cells.map((cell, j) => (
              isHeader
                ? <th key={j} className="px-3 py-2 text-left text-xs font-semibold text-gray-700 border">{cell}</th>
                : <td key={j} className="px-3 py-2 text-sm text-gray-700 border">{cell}</td>
            ))}
          </tr>
        );
      }
      if (line === '') return <br key={i} />;
      return <p key={i} className="text-sm text-gray-700 leading-relaxed">{line}</p>;
    });
  };

  return (
    <div className="flex h-[calc(100vh-180px)] space-x-6">
      {/* 左侧笔记列表 */}
      <div className="w-96 bg-white rounded-lg shadow flex flex-col">
        <div className="px-4 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center mb-3">
            <h1 className="text-xl font-bold text-gray-900">笔记与附注</h1>
            <button className="btn btn-primary text-sm flex items-center">
              <PlusIcon className="h-4 w-4 mr-1" />
              新增
            </button>
          </div>
          {/* 搜索 */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜索笔记..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
            />
          </div>
          {/* 标签筛选 */}
          <div className="flex flex-wrap gap-1.5 mt-3">
            <button
              onClick={() => setActiveTag('all')}
              className={`px-2 py-0.5 rounded-full text-xs ${
                activeTag === 'all' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              全部
            </button>
            {allTags.map((tag) => (
              <button
                key={tag}
                onClick={() => setActiveTag(tag)}
                className={`px-2 py-0.5 rounded-full text-xs ${
                  activeTag === tag ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>

        {/* 笔记列表 */}
        <div className="flex-1 overflow-y-auto">
          {filteredNotes.map((note) => (
            <div
              key={note.id}
              onClick={() => { setSelectedNote(note); setEditMode(false); }}
              className={`px-4 py-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
                selectedNote?.id === note.id ? 'bg-primary-50 border-l-4 border-l-primary-500' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <h3 className="text-sm font-semibold text-gray-900 flex items-center">
                  {note.isImportant && <span className="text-yellow-500 mr-1">★</span>}
                  {note.title}
                </h3>
                <ChevronRightIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
              </div>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                {note.content.replace(/[#\-\[\]|*]/g, '').substring(0, 80)}...
              </p>
              <div className="flex items-center justify-between mt-2">
                <div className="flex space-x-1">
                  {note.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-[10px]">
                      {tag}
                    </span>
                  ))}
                </div>
                <span className="text-[10px] text-gray-400 flex items-center">
                  <ClockIcon className="h-3 w-3 mr-0.5" />
                  {note.updatedAt.split(' ')[0]}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* 底部操作 */}
        <div className="px-4 py-3 border-t border-gray-200">
          <button className="w-full btn bg-green-600 text-white hover:bg-green-700 text-sm flex items-center justify-center">
            <DocumentTextIcon className="h-4 w-4 mr-2" />
            汇出笔记组成财报
          </button>
        </div>
      </div>

      {/* 右侧笔记内容 */}
      <div className="flex-1 bg-white rounded-lg shadow flex flex-col">
        {selectedNote ? (
          <>
            {/* 笔记标题栏 */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    {selectedNote.isImportant && <span className="text-yellow-500 mr-1">★</span>}
                    {selectedNote.title}
                  </h2>
                  <div className="flex items-center space-x-4 text-xs text-gray-500 mt-2">
                    <span className="flex items-center">
                      <ClockIcon className="h-3 w-3 mr-1" />
                      更新：{selectedNote.updatedAt}
                    </span>
                    {selectedNote.linkedReport && (
                      <span className="flex items-center text-primary-600">
                        <FolderIcon className="h-3 w-3 mr-1" />
                        关联：{selectedNote.linkedReport}
                      </span>
                    )}
                    {selectedNote.linkedAccount && (
                      <span className="flex items-center text-primary-600">
                        <TagIcon className="h-3 w-3 mr-1" />
                        关联：{selectedNote.linkedAccount}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setEditMode(!editMode)}
                    className={`px-3 py-1.5 text-sm rounded-lg border flex items-center ${
                      editMode ? 'bg-primary-600 text-white border-primary-600' : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <PencilSquareIcon className="h-4 w-4 mr-1" />
                    {editMode ? '预览' : '编辑'}
                  </button>
                  <button className="px-3 py-1.5 text-sm text-gray-600 rounded-lg border hover:bg-gray-100 flex items-center">
                    <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                    导出
                  </button>
                  <button className="px-3 py-1.5 text-sm text-red-600 rounded-lg border border-red-200 hover:bg-red-50 flex items-center">
                    <TrashIcon className="h-4 w-4 mr-1" />
                    删除
                  </button>
                </div>
              </div>
              {/* 标签 */}
              <div className="flex items-center space-x-2 mt-3">
                <TagIcon className="h-4 w-4 text-gray-400" />
                {selectedNote.tags.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                    {tag}
                  </span>
                ))}
                <button className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs hover:bg-gray-200">
                  + 标签
                </button>
              </div>
            </div>

            {/* 笔记正文 */}
            <div className="flex-1 overflow-y-auto p-6">
              {editMode ? (
                <textarea
                  className="w-full h-full border border-gray-300 rounded-lg p-4 font-mono text-sm resize-none focus:ring-2 focus:ring-primary-500"
                  defaultValue={selectedNote.content}
                />
              ) : (
                <div className="prose max-w-none">
                  {renderMarkdown(selectedNote.content)}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <BookmarkIcon className="h-16 w-16 mx-auto text-gray-300 mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">选择一则笔记</p>
              <p className="text-sm text-gray-500">从左侧列表中选择笔记，或创建新笔记</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

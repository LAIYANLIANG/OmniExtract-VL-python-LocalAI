import React from 'react';
import { Link } from 'react-router-dom';
import {
  DocumentTextIcon,
  TableCellsIcon,
  ChartBarIcon,
  BookmarkIcon,
  SparklesIcon,
  ArrowTrendingUpIcon,
  BanknotesIcon,
  CalculatorIcon,
} from '@heroicons/react/24/outline';

export default function HomePage() {
  // 统计数据
  const stats = [
    { name: '本期营收', value: '96,500K', icon: BanknotesIcon, color: 'bg-blue-500', change: '+5.8%', positive: true },
    { name: '营业利益', value: '7,400K', icon: ArrowTrendingUpIcon, color: 'bg-green-500', change: '+12.1%', positive: true },
    { name: '总资产', value: '125,680K', icon: CalculatorIcon, color: 'bg-purple-500', change: '+6.2%', positive: true },
    { name: '笔记数', value: '5', icon: BookmarkIcon, color: 'bg-yellow-500', change: '+2 本周', positive: true },
  ];

  const quickActions = [
    {
      name: '财报查询',
      description: '查询资产负债表、损益表、现金流量表',
      to: '/reports',
      icon: DocumentTextIcon,
      color: 'bg-primary-600 hover:bg-primary-700',
    },
    {
      name: '科目查询',
      description: '按科目代码、属性查询，可钻取明细',
      to: '/accounts',
      icon: TableCellsIcon,
      color: 'bg-blue-600 hover:bg-blue-700',
    },
    {
      name: 'AI 财报分析',
      description: '引导式分析，生成图表与分析洞察',
      to: '/analysis',
      icon: ChartBarIcon,
      color: 'bg-green-600 hover:bg-green-700',
    },
    {
      name: '笔记附注',
      description: '记录重点发现，组成财务报表',
      to: '/notes',
      icon: BookmarkIcon,
      color: 'bg-yellow-600 hover:bg-yellow-700',
    },
  ];

  return (
    <div className="space-y-8">
      {/* 页面标题 */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          OmniExtract-VL
        </h1>
        <p className="text-lg text-gray-600">
          次世代智慧文件抽取與 AI 視覺中台
        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center">
              <div className={`${stat.color} rounded-lg p-3`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
            <div className="mt-2">
              <span className={`text-xs font-medium ${stat.positive ? 'text-green-600' : 'text-red-600'}`}>
                {stat.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* 快速操作 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">快速操作</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              to={action.to}
              className={`${action.color} text-white rounded-lg p-6 transition-all hover:scale-105 shadow-md`}
            >
              <action.icon className="h-8 w-8 mb-3" />
              <h3 className="text-lg font-semibold mb-1">{action.name}</h3>
              <p className="text-sm text-white/90">{action.description}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* 最近活动 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 近期笔记 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">近期笔记</h3>
            <Link to="/notes" className="text-sm text-primary-600 hover:text-primary-700">查看全部</Link>
          </div>
          <div className="divide-y divide-gray-100">
            {[
              { title: '2025 Q4 费用分析重点', tag: '费用分析', time: '今天 16:20', important: true },
              { title: '应收帐款异常提醒', tag: '追踪', time: '今天 14:20', important: true },
              { title: '获利能力指标追踪', tag: 'KPI', time: '昨天 11:45', important: false },
            ].map((n, i) => (
              <Link to="/notes" key={i} className="flex items-center justify-between px-6 py-3 hover:bg-gray-50">
                <div className="flex items-center">
                  {n.important && <span className="text-yellow-500 mr-2 text-sm">★</span>}
                  <span className="text-sm text-gray-900">{n.title}</span>
                  <span className="ml-2 px-2 py-0.5 text-[10px] bg-gray-100 text-gray-600 rounded-full">{n.tag}</span>
                </div>
                <span className="text-xs text-gray-400">{n.time}</span>
              </Link>
            ))}
          </div>
        </div>

        {/* 快速 AI 提问 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <SparklesIcon className="h-5 w-5 mr-2 text-primary-600" />
              快速分析
            </h3>
            <Link to="/analysis" className="text-sm text-primary-600 hover:text-primary-700">进入分析</Link>
          </div>
          <div className="p-6 space-y-3">
            <p className="text-sm text-gray-600 mb-3">点击下方问题快速启动 AI 分析：</p>
            {[
              '本期营收与上期相比如何？',
              '帮我分析费用结构占比',
              '应收帐款周转率趋势',
              '获利能力综合分析',
            ].map((q, i) => (
              <Link
                key={i}
                to="/analysis"
                className="block w-full text-left px-4 py-3 bg-gray-50 text-sm text-gray-700 rounded-lg hover:bg-primary-50 hover:text-primary-700 transition-colors"
              >
                💬 {q}
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* 系统状态 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-3">系统状态</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-600">前端界面</span>
            <span className="flex items-center text-green-600 text-sm">
              <span className="h-2 w-2 bg-green-600 rounded-full mr-2"></span>
              运行中
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-600">后端 API</span>
            <span className="flex items-center text-gray-400 text-sm">
              <span className="h-2 w-2 bg-gray-400 rounded-full mr-2"></span>
              未连接
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-600">财报数据库</span>
            <span className="flex items-center text-gray-400 text-sm">
              <span className="h-2 w-2 bg-gray-400 rounded-full mr-2"></span>
              未连接
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

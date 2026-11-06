import React, { useState } from 'react';
import {
  DocumentTextIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';

type ReportType = 'balance_sheet' | 'income_statement' | 'cash_flow';

interface ReportRow {
  id: string;
  code: string;
  name: string;
  currentPeriod: number;
  previousPeriod: number;
  change: number;
  changePercent: number;
  level: number;
  children?: ReportRow[];
  hasDetail?: boolean;
}

export default function FinancialReportPage() {
  const [reportType, setReportType] = useState<ReportType>('balance_sheet');
  const [period, setPeriod] = useState('2025-12');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set(['1', '2', '5']));
  const [showDetail, setShowDetail] = useState<string | null>(null);

  const reportTypes = [
    { key: 'balance_sheet' as ReportType, label: '资产负债表' },
    { key: 'income_statement' as ReportType, label: '损益表' },
    { key: 'cash_flow' as ReportType, label: '现金流量表' },
  ];

  // 模拟资产负债表数据
  const balanceSheetData: ReportRow[] = [
    {
      id: '1', code: '1', name: '资产', level: 0,
      currentPeriod: 125680000, previousPeriod: 118350000,
      change: 7330000, changePercent: 6.19,
      children: [
        {
          id: '1-1', code: '11', name: '流动资产', level: 1,
          currentPeriod: 68500000, previousPeriod: 62100000,
          change: 6400000, changePercent: 10.31,
          children: [
            { id: '1-1-1', code: '1100', name: '现金及约当现金', level: 2, currentPeriod: 15200000, previousPeriod: 12800000, change: 2400000, changePercent: 18.75, hasDetail: true },
            { id: '1-1-2', code: '1150', name: '应收帐款净额', level: 2, currentPeriod: 22300000, previousPeriod: 20500000, change: 1800000, changePercent: 8.78, hasDetail: true },
            { id: '1-1-3', code: '1200', name: '存货', level: 2, currentPeriod: 18500000, previousPeriod: 17200000, change: 1300000, changePercent: 7.56, hasDetail: true },
            { id: '1-1-4', code: '1210', name: '预付款项', level: 2, currentPeriod: 8200000, previousPeriod: 7800000, change: 400000, changePercent: 5.13, hasDetail: true },
            { id: '1-1-5', code: '1280', name: '其他流动资产', level: 2, currentPeriod: 4300000, previousPeriod: 3800000, change: 500000, changePercent: 13.16, hasDetail: true },
          ],
        },
        {
          id: '1-2', code: '15', name: '非流动资产', level: 1,
          currentPeriod: 57180000, previousPeriod: 56250000,
          change: 930000, changePercent: 1.65,
          children: [
            { id: '1-2-1', code: '1500', name: '不动产、厂房及设备', level: 2, currentPeriod: 35200000, previousPeriod: 36100000, change: -900000, changePercent: -2.49, hasDetail: true },
            { id: '1-2-2', code: '1550', name: '无形资产', level: 2, currentPeriod: 8500000, previousPeriod: 7800000, change: 700000, changePercent: 8.97, hasDetail: true },
            { id: '1-2-3', code: '1600', name: '长期投资', level: 2, currentPeriod: 13480000, previousPeriod: 12350000, change: 1130000, changePercent: 9.15, hasDetail: true },
          ],
        },
      ],
    },
    {
      id: '2', code: '2', name: '负债', level: 0,
      currentPeriod: 45230000, previousPeriod: 42180000,
      change: 3050000, changePercent: 7.23,
      children: [
        {
          id: '2-1', code: '21', name: '流动负债', level: 1,
          currentPeriod: 28500000, previousPeriod: 26200000,
          change: 2300000, changePercent: 8.78,
          children: [
            { id: '2-1-1', code: '2100', name: '应付帐款', level: 2, currentPeriod: 12800000, previousPeriod: 11500000, change: 1300000, changePercent: 11.30, hasDetail: true },
            { id: '2-1-2', code: '2150', name: '应付薪资', level: 2, currentPeriod: 3200000, previousPeriod: 2800000, change: 400000, changePercent: 14.29, hasDetail: true },
            { id: '2-1-3', code: '2200', name: '短期借款', level: 2, currentPeriod: 8500000, previousPeriod: 8200000, change: 300000, changePercent: 3.66, hasDetail: true },
            { id: '2-1-4', code: '2280', name: '其他流动负债', level: 2, currentPeriod: 4000000, previousPeriod: 3700000, change: 300000, changePercent: 8.11, hasDetail: true },
          ],
        },
        {
          id: '2-2', code: '25', name: '非流动负债', level: 1,
          currentPeriod: 16730000, previousPeriod: 15980000,
          change: 750000, changePercent: 4.69,
          children: [
            { id: '2-2-1', code: '2500', name: '长期借款', level: 2, currentPeriod: 12500000, previousPeriod: 12000000, change: 500000, changePercent: 4.17, hasDetail: true },
            { id: '2-2-2', code: '2580', name: '其他非流动负债', level: 2, currentPeriod: 4230000, previousPeriod: 3980000, change: 250000, changePercent: 6.28, hasDetail: true },
          ],
        },
      ],
    },
    {
      id: '5', code: '3', name: '股东权益', level: 0,
      currentPeriod: 80450000, previousPeriod: 76170000,
      change: 4280000, changePercent: 5.62,
      children: [
        { id: '5-1', code: '3100', name: '股本', level: 1, currentPeriod: 30000000, previousPeriod: 30000000, change: 0, changePercent: 0, hasDetail: true },
        { id: '5-2', code: '3200', name: '资本公积', level: 1, currentPeriod: 15000000, previousPeriod: 15000000, change: 0, changePercent: 0, hasDetail: true },
        { id: '5-3', code: '3300', name: '保留盈余', level: 1, currentPeriod: 35450000, previousPeriod: 31170000, change: 4280000, changePercent: 13.73, hasDetail: true },
      ],
    },
  ];

  // 模拟明细数据
  const detailData = [
    { date: '2025-12-28', voucherNo: 'JV-2025-1285', description: '客户 A 货款入帐', debit: 3500000, credit: 0, balance: 15200000 },
    { date: '2025-12-25', voucherNo: 'JV-2025-1274', description: '办公室租金支付', debit: 0, credit: 850000, balance: 11700000 },
    { date: '2025-12-22', voucherNo: 'JV-2025-1260', description: '客户 B 预收款', debit: 2200000, credit: 0, balance: 12550000 },
    { date: '2025-12-20', voucherNo: 'JV-2025-1248', description: '供应商付款', debit: 0, credit: 1500000, balance: 10350000 },
    { date: '2025-12-18', voucherNo: 'JV-2025-1235', description: '银行利息收入', debit: 45000, credit: 0, balance: 11850000 },
  ];

  const toggleRow = (id: string) => {
    const next = new Set(expandedRows);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedRows(next);
  };

  const formatNumber = (n: number) =>
    new Intl.NumberFormat('zh-TW').format(n);

  const renderRows = (rows: ReportRow[]): React.ReactNode => {
    return rows.map((row) => {
      const isExpanded = expandedRows.has(row.id);
      const hasChildren = row.children && row.children.length > 0;

      return (
        <React.Fragment key={row.id}>
          <tr
            className={`hover:bg-blue-50 transition-colors cursor-pointer ${
              row.level === 0 ? 'bg-gray-50 font-bold' : ''
            } ${row.level === 1 ? 'font-semibold' : ''}`}
            onClick={() => hasChildren ? toggleRow(row.id) : row.hasDetail ? setShowDetail(row.id) : null}
          >
            <td className="px-4 py-3 whitespace-nowrap">
              <div className="flex items-center" style={{ paddingLeft: `${row.level * 24}px` }}>
                {hasChildren ? (
                  isExpanded
                    ? <ChevronDownIcon className="h-4 w-4 mr-2 text-gray-500 flex-shrink-0" />
                    : <ChevronRightIcon className="h-4 w-4 mr-2 text-gray-500 flex-shrink-0" />
                ) : row.hasDetail ? (
                  <span className="w-4 mr-2 flex-shrink-0 text-center text-gray-300">•</span>
                ) : (
                  <span className="w-6 mr-2" />
                )}
                <span className="text-gray-500 text-xs mr-3 w-10">{row.code}</span>
                <span className={row.level === 0 ? 'text-gray-900' : 'text-gray-800'}>
                  {row.name}
                </span>
                {row.hasDetail && (
                  <span className="ml-2 text-xs text-primary-500 hover:text-primary-700">
                    查看明细
                  </span>
                )}
              </div>
            </td>
            <td className="px-4 py-3 text-right whitespace-nowrap font-mono">
              {formatNumber(row.currentPeriod)}
            </td>
            <td className="px-4 py-3 text-right whitespace-nowrap font-mono text-gray-500">
              {formatNumber(row.previousPeriod)}
            </td>
            <td className={`px-4 py-3 text-right whitespace-nowrap font-mono ${
              row.change > 0 ? 'text-red-600' : row.change < 0 ? 'text-green-600' : 'text-gray-500'
            }`}>
              {row.change > 0 ? '+' : ''}{formatNumber(row.change)}
            </td>
            <td className={`px-4 py-3 text-right whitespace-nowrap font-mono ${
              row.changePercent > 0 ? 'text-red-600' : row.changePercent < 0 ? 'text-green-600' : 'text-gray-500'
            }`}>
              {row.changePercent > 0 ? '+' : ''}{row.changePercent.toFixed(2)}%
            </td>
          </tr>
          {isExpanded && hasChildren && renderRows(row.children!)}
        </React.Fragment>
      );
    });
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">财务报表查询</h1>
          <p className="text-gray-600 mt-1">查询资产负债表、损益表、现金流量表，可展开细项查看明细</p>
        </div>
        <button className="btn btn-primary flex items-center">
          <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
          下载报表
        </button>
      </div>

      {/* 报表类型切换 */}
      <div className="bg-white rounded-lg shadow">
        <div className="flex border-b border-gray-200">
          {reportTypes.map((rt) => (
            <button
              key={rt.key}
              onClick={() => setReportType(rt.key)}
              className={`flex-1 py-4 text-center font-medium transition-colors relative ${
                reportType === rt.key
                  ? 'text-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {rt.label}
              {reportType === rt.key && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600" />
              )}
            </button>
          ))}
        </div>

        {/* 筛选条件 */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
              <span className="text-sm text-gray-600">筛选：</span>
            </div>
            <div>
              <label className="text-sm text-gray-600 mr-2">期别</label>
              <input
                type="month"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 mr-2">比较期间</label>
              <select className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500">
                <option>上期 (2025-11)</option>
                <option>去年同期 (2024-12)</option>
                <option>自定义期间</option>
              </select>
            </div>
            <div className="flex-1" />
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索科目..."
                className="pl-9 pr-4 py-1.5 border border-gray-300 rounded-lg text-sm w-48 focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </div>

        {/* 报表数据表格 */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 w-2/5">
                  科目
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">
                  本期金额
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">
                  上期金额
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">
                  增减金额
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">
                  增减 %
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {renderRows(balanceSheetData)}
            </tbody>
          </table>
        </div>

        {/* 报表合计 */}
        <div className="px-4 py-3 bg-gray-100 border-t border-gray-200">
          <div className="flex justify-between text-sm text-gray-600">
            <span>资产总计 = 负债 + 股东权益</span>
            <span className="font-mono font-semibold">
              {formatNumber(125680000)} = {formatNumber(45230000)} + {formatNumber(80450000)}
            </span>
          </div>
        </div>
      </div>

      {/* 明细弹窗/面板 */}
      {showDetail && (
        <div className="bg-white rounded-lg shadow border-2 border-primary-200">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-primary-50">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                科目明细 - 现金及约当现金 (1100)
              </h3>
              <p className="text-sm text-gray-500">2025年12月 传票明细</p>
            </div>
            <div className="flex items-center space-x-3">
              <button className="btn btn-primary text-sm flex items-center">
                <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                下载明细
              </button>
              <button
                onClick={() => setShowDetail(null)}
                className="text-gray-500 hover:text-gray-700 text-lg font-bold"
              >
                ✕
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">日期</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">传票号码</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">摘要</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">借方</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">贷方</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">余额</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {detailData.map((d, i) => (
                  <tr key={i} className="hover:bg-blue-50">
                    <td className="px-4 py-3 text-sm">{d.date}</td>
                    <td className="px-4 py-3 text-sm text-primary-600 hover:underline cursor-pointer">
                      {d.voucherNo}
                    </td>
                    <td className="px-4 py-3 text-sm">{d.description}</td>
                    <td className="px-4 py-3 text-sm text-right font-mono">
                      {d.debit > 0 ? formatNumber(d.debit) : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-mono">
                      {d.credit > 0 ? formatNumber(d.credit) : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-mono font-semibold">
                      {formatNumber(d.balance)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-3 bg-gray-50 border-t text-sm text-gray-500">
            显示 5 笔 / 共 128 笔 ·
            <button className="text-primary-600 hover:underline ml-1">查看全部</button>
          </div>
        </div>
      )}
    </div>
  );
}

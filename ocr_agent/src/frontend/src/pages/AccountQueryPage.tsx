import React, { useState } from 'react';
import {
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  ChevronRightIcon,
  AdjustmentsHorizontalIcon,
  TableCellsIcon,
} from '@heroicons/react/24/outline';

interface Account {
  code: string;
  name: string;
  attribute: string;
  category: string;
  balance: number;
  debitTotal: number;
  creditTotal: number;
  hasDetail: boolean;
}

interface DetailRecord {
  date: string;
  voucherNo: string;
  description: string;
  debit: number;
  credit: number;
  balance: number;
}

export default function AccountQueryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [attributeFilter, setAttributeFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  const accounts: Account[] = [
    { code: '1100', name: '现金及约当现金', attribute: '资产', category: '流动资产', balance: 15200000, debitTotal: 28500000, creditTotal: 13300000, hasDetail: true },
    { code: '1150', name: '应收帐款', attribute: '资产', category: '流动资产', balance: 22300000, debitTotal: 45200000, creditTotal: 22900000, hasDetail: true },
    { code: '1160', name: '备抵呆帐', attribute: '资产', category: '流动资产', balance: -850000, debitTotal: 200000, creditTotal: 1050000, hasDetail: true },
    { code: '1200', name: '存货', attribute: '资产', category: '流动资产', balance: 18500000, debitTotal: 32100000, creditTotal: 13600000, hasDetail: true },
    { code: '1500', name: '不动产、厂房及设备', attribute: '资产', category: '非流动资产', balance: 35200000, debitTotal: 5800000, creditTotal: 6700000, hasDetail: true },
    { code: '1550', name: '无形资产', attribute: '资产', category: '非流动资产', balance: 8500000, debitTotal: 1200000, creditTotal: 500000, hasDetail: true },
    { code: '2100', name: '应付帐款', attribute: '负债', category: '流动负债', balance: 12800000, debitTotal: 18500000, creditTotal: 31300000, hasDetail: true },
    { code: '2150', name: '应付薪资', attribute: '负债', category: '流动负债', balance: 3200000, debitTotal: 35600000, creditTotal: 38800000, hasDetail: true },
    { code: '2200', name: '短期借款', attribute: '负债', category: '流动负债', balance: 8500000, debitTotal: 5000000, creditTotal: 13500000, hasDetail: true },
    { code: '2500', name: '长期借款', attribute: '负债', category: '非流动负债', balance: 12500000, debitTotal: 2000000, creditTotal: 14500000, hasDetail: true },
    { code: '3100', name: '股本', attribute: '权益', category: '股东权益', balance: 30000000, debitTotal: 0, creditTotal: 30000000, hasDetail: true },
    { code: '3300', name: '保留盈余', attribute: '权益', category: '股东权益', balance: 35450000, debitTotal: 8200000, creditTotal: 43650000, hasDetail: true },
    { code: '4100', name: '营业收入', attribute: '收入', category: '营业收入', balance: 96500000, debitTotal: 1200000, creditTotal: 97700000, hasDetail: true },
    { code: '4200', name: '营业成本', attribute: '费用', category: '营业成本', balance: 62800000, debitTotal: 62800000, creditTotal: 0, hasDetail: true },
    { code: '5100', name: '管理费用', attribute: '费用', category: '营业费用', balance: 12500000, debitTotal: 12500000, creditTotal: 0, hasDetail: true },
    { code: '5200', name: '销售费用', attribute: '费用', category: '营业费用', balance: 8200000, debitTotal: 8200000, creditTotal: 0, hasDetail: true },
    { code: '5300', name: '研发费用', attribute: '费用', category: '营业费用', balance: 5600000, debitTotal: 5600000, creditTotal: 0, hasDetail: true },
    { code: '6100', name: '利息收入', attribute: '收入', category: '营业外收入', balance: 320000, debitTotal: 0, creditTotal: 320000, hasDetail: true },
    { code: '6200', name: '利息费用', attribute: '费用', category: '营业外费用', balance: 1850000, debitTotal: 1850000, creditTotal: 0, hasDetail: true },
  ];

  const detailRecords: DetailRecord[] = [
    { date: '2025-12-28', voucherNo: 'JV-2025-1285', description: '客户 A 公司出货', debit: 3500000, credit: 0, balance: 22300000 },
    { date: '2025-12-25', voucherNo: 'JV-2025-1272', description: '客户 B 公司收款沖帐', debit: 0, credit: 2800000, balance: 18800000 },
    { date: '2025-12-22', voucherNo: 'JV-2025-1258', description: '客户 C 公司出货', debit: 4200000, credit: 0, balance: 21600000 },
    { date: '2025-12-20', voucherNo: 'JV-2025-1245', description: '折让处理 - 客户 A', debit: 0, credit: 150000, balance: 17400000 },
    { date: '2025-12-18', voucherNo: 'JV-2025-1232', description: '客户 D 公司收款沖帐', debit: 0, credit: 3200000, balance: 17550000 },
    { date: '2025-12-15', voucherNo: 'JV-2025-1218', description: '客户 E 公司出货', debit: 5800000, credit: 0, balance: 20750000 },
    { date: '2025-12-12', voucherNo: 'JV-2025-1205', description: '坏帐回收 - 客户 F', debit: 500000, credit: 0, balance: 14950000 },
    { date: '2025-12-10', voucherNo: 'JV-2025-1198', description: '客户 G 公司收款沖帐', debit: 0, credit: 1800000, balance: 14450000 },
  ];

  const attributes = ['all', '资产', '负债', '权益', '收入', '费用'];
  const categories = ['all', '流动资产', '非流动资产', '流动负债', '非流动负债', '股东权益', '营业收入', '营业成本', '营业费用', '营业外收入', '营业外费用'];

  const filteredAccounts = accounts.filter((a) => {
    const matchSearch =
      searchQuery === '' ||
      a.code.includes(searchQuery) ||
      a.name.includes(searchQuery);
    const matchAttr = attributeFilter === 'all' || a.attribute === attributeFilter;
    const matchCat = categoryFilter === 'all' || a.category === categoryFilter;
    return matchSearch && matchAttr && matchCat;
  });

  const formatNumber = (n: number) => new Intl.NumberFormat('zh-TW').format(n);

  const getAttrColor = (attr: string) => {
    switch (attr) {
      case '资产': return 'bg-blue-100 text-blue-700';
      case '负债': return 'bg-red-100 text-red-700';
      case '权益': return 'bg-purple-100 text-purple-700';
      case '收入': return 'bg-green-100 text-green-700';
      case '费用': return 'bg-orange-100 text-orange-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">科目查询</h1>
        <p className="text-gray-600 mt-1">按科目代码、名称或属性查询，点击任一科目可查看传票明细</p>
      </div>

      {/* 搜索与筛选 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="输入科目代码或名称搜索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <select
            value={attributeFilter}
            onChange={(e) => setAttributeFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">所有属性</option>
            {attributes.filter((a) => a !== 'all').map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">所有分类</option>
            {categories.filter((c) => c !== 'all').map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {/* 快捷属性标签 */}
        <div className="flex items-center mt-3 space-x-2">
          <AdjustmentsHorizontalIcon className="h-4 w-4 text-gray-400" />
          <span className="text-sm text-gray-500">快捷：</span>
          {attributes.map((attr) => (
            <button
              key={attr}
              onClick={() => setAttributeFilter(attr)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                attributeFilter === attr
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {attr === 'all' ? '全部' : attr}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 科目列表 */}
        <div className={`bg-white rounded-lg shadow ${selectedAccount ? 'lg:col-span-1' : 'lg:col-span-3'}`}>
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">
              科目列表 ({filteredAccounts.length})
            </h2>
            <button className="text-sm text-primary-600 flex items-center">
              <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
              下载
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">科目代码</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">科目名称</th>
                  {!selectedAccount && (
                    <>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">属性</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600">借方累计</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600">贷方累计</th>
                    </>
                  )}
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600">余额</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredAccounts.map((account) => (
                  <tr
                    key={account.code}
                    onClick={() => setSelectedAccount(account)}
                    className={`hover:bg-blue-50 cursor-pointer transition-colors ${
                      selectedAccount?.code === account.code ? 'bg-primary-50 border-l-4 border-primary-500' : ''
                    }`}
                  >
                    <td className="px-4 py-3 text-sm font-mono text-gray-700">{account.code}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      <div className="flex items-center">
                        {account.name}
                        <ChevronRightIcon className="h-3 w-3 ml-1 text-gray-400" />
                      </div>
                    </td>
                    {!selectedAccount && (
                      <>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getAttrColor(account.attribute)}`}>
                            {account.attribute}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-right font-mono">{formatNumber(account.debitTotal)}</td>
                        <td className="px-4 py-3 text-sm text-right font-mono">{formatNumber(account.creditTotal)}</td>
                      </>
                    )}
                    <td className="px-4 py-3 text-sm text-right font-mono font-semibold">{formatNumber(account.balance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 科目明细面板 */}
        {selectedAccount && (
          <div className="lg:col-span-2 bg-white rounded-lg shadow">
            {/* 明细标题 */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <div>
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {selectedAccount.code} {selectedAccount.name}
                    </h3>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getAttrColor(selectedAccount.attribute)}`}>
                      {selectedAccount.attribute}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                      {selectedAccount.category}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">2025年12月 传票明细</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="btn btn-primary text-sm flex items-center">
                    <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                    下载明细
                  </button>
                  <button
                    onClick={() => setSelectedAccount(null)}
                    className="text-gray-400 hover:text-gray-600 text-xl font-bold px-2"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* 科目摘要 */}
              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-blue-600 mb-1">借方累计</p>
                  <p className="text-lg font-bold text-blue-900 font-mono">{formatNumber(selectedAccount.debitTotal)}</p>
                </div>
                <div className="bg-red-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-red-600 mb-1">贷方累计</p>
                  <p className="text-lg font-bold text-red-900 font-mono">{formatNumber(selectedAccount.creditTotal)}</p>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-green-600 mb-1">期末余额</p>
                  <p className="text-lg font-bold text-green-900 font-mono">{formatNumber(selectedAccount.balance)}</p>
                </div>
              </div>
            </div>

            {/* 明细表格 */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">日期</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">传票号码</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">摘要</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600">借方</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600">贷方</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600">余额</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {detailRecords.map((r, i) => (
                    <tr key={i} className="hover:bg-blue-50 transition-colors">
                      <td className="px-4 py-3 text-sm text-gray-600">{r.date}</td>
                      <td className="px-4 py-3 text-sm text-primary-600 hover:underline cursor-pointer">{r.voucherNo}</td>
                      <td className="px-4 py-3 text-sm">{r.description}</td>
                      <td className="px-4 py-3 text-sm text-right font-mono">{r.debit > 0 ? formatNumber(r.debit) : '-'}</td>
                      <td className="px-4 py-3 text-sm text-right font-mono">{r.credit > 0 ? formatNumber(r.credit) : '-'}</td>
                      <td className="px-4 py-3 text-sm text-right font-mono font-semibold">{formatNumber(r.balance)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-6 py-3 border-t bg-gray-50 flex justify-between text-sm text-gray-500">
              <span>显示 {detailRecords.length} 笔 / 共 256 笔</span>
              <div className="flex space-x-2">
                <button className="px-3 py-1 bg-white border rounded hover:bg-gray-100">上一页</button>
                <span className="px-3 py-1">1 / 32</span>
                <button className="px-3 py-1 bg-white border rounded hover:bg-gray-100">下一页</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

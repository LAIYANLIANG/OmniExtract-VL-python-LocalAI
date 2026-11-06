import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import FinancialReportPage from './pages/FinancialReportPage';
import AccountQueryPage from './pages/AccountQueryPage';
import AnalysisPage from './pages/AnalysisPage';
import NotesPage from './pages/NotesPage';
import NotFoundPage from './pages/NotFoundPage';

function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="reports" element={<FinancialReportPage />} />
          <Route path="accounts" element={<AccountQueryPage />} />
          <Route path="analysis" element={<AnalysisPage />} />
          <Route path="notes" element={<NotesPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
      <Toaster position="top-right" />
    </>
  );
}

export default App;

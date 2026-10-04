import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { PlannerProvider } from './context/PlannerContext';
import { Sidebar } from './components/layout/Sidebar';
import { MobileNav } from './components/layout/MobileNav';
import { Dashboard } from './pages/Dashboard';
import { Schedule } from './pages/Schedule';
import { Tasks } from './pages/Tasks';
import { AIAssistant } from './pages/AIAssistant';

export const App: React.FC = () => {
  return (
    <PlannerProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-[#FAF6F0] flex flex-col md:flex-row text-stone-800 antialiased selection:bg-[#F2DEC0] selection:text-[#7A5918]">
          {/* Desktop Left Sidebar */}
          <Sidebar />

          {/* Main Content Area */}
          <main className="flex-1 min-w-0 flex flex-col min-h-screen">
            <div className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto pb-24 md:pb-12">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/schedule" element={<Schedule />} />
                <Route path="/tasks" element={<Tasks />} />
                <Route path="/assistant" element={<AIAssistant />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </div>
          </main>

          {/* Mobile Bottom Navigation */}
          <MobileNav />
        </div>
      </BrowserRouter>
    </PlannerProvider>
  );
};

export default App;

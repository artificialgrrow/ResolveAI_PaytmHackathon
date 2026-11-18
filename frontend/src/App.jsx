import React, { useState } from 'react';
import Navbar from './Navbar';
import HeroMeshBanner from './HeroMeshBanner';
import QRProvenanceStudio from './QRProvenanceStudio';
import { resetDemoData } from './api';

export default function App() {
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [resetKey, setResetKey] = useState(0);

  const handleResetDemo = async () => {
    try {
      await resetDemoData();
      setResetKey(prev => prev + 1);
    } catch (e) {
      console.error('Reset failed:', e);
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-canvas text-ink flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar
        selectedLanguage={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
        onResetDemo={handleResetDemo}
      />

      {/* Hero Banner with Geist Mesh Gradient */}
      <HeroMeshBanner />

      {/* Main Studio Viewport (Fits 100% of remaining screen, zero vertical scroll on desktop) */}
      <main className="flex-1 min-h-0 overflow-hidden" key={resetKey}>
        <QRProvenanceStudio
          selectedLanguage={selectedLanguage}
          onLanguageChange={setSelectedLanguage}
        />
      </main>
    </div>
  );
}

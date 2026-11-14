import React, { useState, useEffect } from 'react';
import Navbar from './Navbar';
import HeroMeshBanner from './HeroMeshBanner';
import LoginView from './LoginView';
import MerchantChatPane from './MerchantChatPane';
import OpsCenterPane from './OpsCenterPane';
import { getMerchantData, streamIncident, approveIncident, resetDemoData } from './api';
import { SCENARIO_PROMPTS, MERCHANT_GREETINGS } from './languages';

export default function App() {
  const [currentMerchant, setCurrentMerchant] = useState(null);
  const [merchantData, setMerchantData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [events, setEvents] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentIncidentId, setCurrentIncidentId] = useState(null);
  const [pendingApproval, setPendingApproval] = useState(null);
  const [isApproving, setIsApproving] = useState(false);
  const [verifiedUtr, setVerifiedUtr] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('en');

  // Load merchant live transactions & settlement batches
  const refreshMerchantData = async (merchantId) => {
    const id = merchantId || currentMerchant?.id;
    if (!id) return;
    try {
      const data = await getMerchantData(id);
      setMerchantData(data);
    } catch (err) {
      console.error('Failed to load merchant data:', err);
    }
  };

  // Initialize or update merchant view
  useEffect(() => {
    if (currentMerchant) {
      refreshMerchantData(currentMerchant.id);
      const greeting = MERCHANT_GREETINGS[selectedLanguage]?.(currentMerchant.name) || MERCHANT_GREETINGS.en(currentMerchant.name);
      setMessages([
        {
          sender: 'ai',
          text: greeting
        }
      ]);
      setEvents([]);
      setVerifiedUtr(null);
      setPendingApproval(null);
    }
  }, [currentMerchant]);

  // Handle dynamic language change
  const handleLanguageChange = (newLang) => {
    setSelectedLanguage(newLang);
    if (currentMerchant && messages.length <= 1) {
      const greeting = MERCHANT_GREETINGS[newLang]?.(currentMerchant.name) || MERCHANT_GREETINGS.en(currentMerchant.name);
      setMessages([
        {
          sender: 'ai',
          text: greeting
        }
      ]);
    }
  };

  // Handle sending merchant query (supports any of the 10 Indian languages)
  const handleSendMessage = (messageText) => {
    if (!currentMerchant || isStreaming) return;

    setMessages((prev) => [...prev, { sender: 'merchant', text: messageText }]);
    setIsStreaming(true);
    setVerifiedUtr(null);
    setPendingApproval(null);

    streamIncident(
      currentMerchant.id,
      messageText,
      // onEvent callback
      (event) => {
        setEvents((prev) => [...prev, event]);

        if (event.details?.incident_id) {
          setCurrentIncidentId(event.details.incident_id);
        }

        // Check if supervisor approval is required (Scenario 2: > ₹25,000)
        if (event.status === 'AWAITING_APPROVAL') {
          setPendingApproval({
            incident_id: event.details.incident_id,
            amount: event.details.amount,
            batch_code: event.details.batch_code,
            hold_reason: event.details.hold_reason
          });

          const warningText = event.details?.merchant_warning ||
            `Safety Threshold Checkpoint: This transaction of ₹${event.details.amount.toLocaleString()} exceeds the ₹25,000 autonomous limit. I have verified the payment ledger and paused the batch for human supervisor approval.`;

          setMessages((prev) => [
            ...prev,
            {
              sender: 'ai',
              text: warningText
            }
          ]);
        }

        // Check if resolved
        if (event.status === 'RESOLVED') {
          if (event.details?.utr_number) {
            setVerifiedUtr(event.details.utr_number);
          }
          setMessages((prev) => [
            ...prev,
            {
              sender: 'ai',
              text: event.message
            }
          ]);
        }
      },
      // onDone callback
      () => {
        setIsStreaming(false);
        refreshMerchantData(currentMerchant.id);
      },
      // onError callback
      (err) => {
        setIsStreaming(false);
        setMessages((prev) => [
          ...prev,
          {
            sender: 'ai',
            text: `An operational error occurred while connecting to rails: ${err.message}`
          }
        ]);
      },
      selectedLanguage
    );
  };

  // Handle supervisor approval
  const handleApprove = (incidentId, notes) => {
    setIsApproving(true);
    approveIncident(
      incidentId,
      true,
      notes,
      (event) => {
        setEvents((prev) => [...prev, event]);
        if (event.status === 'RESOLVED') {
          if (event.details?.utr_number) {
            setVerifiedUtr(event.details.utr_number);
          }
          setMessages((prev) => [
            ...prev,
            {
              sender: 'ai',
              text: `${event.message}`
            }
          ]);
        }
      },
      () => {
        setIsApproving(false);
        setPendingApproval(null);
        refreshMerchantData(currentMerchant.id);
      },
      (err) => {
        setIsApproving(false);
        console.error('Approval failed:', err);
      },
      selectedLanguage
    );
  };

  const handleReject = (incidentId, notes) => {
    setIsApproving(true);
    approveIncident(
      incidentId,
      false,
      notes,
      (event) => {
        setEvents((prev) => [...prev, event]);
        setMessages((prev) => [
          ...prev,
          { sender: 'ai', text: `${event.message}` }
        ]);
      },
      () => {
        setIsApproving(false);
        setPendingApproval(null);
        refreshMerchantData(currentMerchant.id);
      },
      () => setIsApproving(false),
      selectedLanguage
    );
  };

  // Reset demo scenarios to initial held/stuck state for repeated presentations
  const handleResetScenarios = async () => {
    try {
      await resetDemoData();
      if (currentMerchant) {
        await refreshMerchantData(currentMerchant.id);
      }
      setEvents([]);
      setVerifiedUtr(null);
      setPendingApproval(null);
      setMessages([
        {
          sender: 'ai',
          text: `Demo reset complete! All 5 merchant failure scenarios have been restored to their initial state. You can now replay any scenario.`
        }
      ]);
    } catch (e) {
      console.error('Reset failed:', e);
    }
  };

  // Localized suggested scenario prompt for current merchant
  const localizedPrompt = currentMerchant
    ? (SCENARIO_PROMPTS[currentMerchant.id]?.[selectedLanguage] || SCENARIO_PROMPTS[currentMerchant.id]?.en)
    : '';

  return (
    <div className="h-screen w-screen overflow-hidden bg-canvas text-ink flex flex-col font-sans">
      {/* Top Navigation */}
      <Navbar
        merchant={currentMerchant}
        onLogout={() => setCurrentMerchant(null)}
        onRefreshData={() => refreshMerchantData(currentMerchant?.id)}
        onResetScenarios={handleResetScenarios}
        selectedLanguage={selectedLanguage}
        onLanguageChange={handleLanguageChange}
      />

      {/* Main View Area: Strict Viewport Bound */}
      {!currentMerchant ? (
        <LoginView onLoginSuccess={(m) => setCurrentMerchant(m)} />
      ) : (
        <main className="flex-1 min-h-0 flex flex-col overflow-hidden">
          {/* Compact Hero Banner with Geist Mesh Gradient */}
          <HeroMeshBanner />

          {/* Two-Pane Workspace Layout (Fits 100% into remaining screen) */}
          <div className="flex-1 min-h-0 px-3 sm:px-6 py-2.5 max-w-[1600px] mx-auto w-full">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 h-full min-h-0">
              {/* Left Pane: Merchant Conversational Experience (42% width) */}
              <div className="lg:col-span-5 h-full min-h-0">
                <MerchantChatPane
                  merchant={currentMerchant}
                  messages={messages}
                  onSendMessage={handleSendMessage}
                  isStreaming={isStreaming}
                  verifiedUtr={verifiedUtr}
                  suggestedPrompt={localizedPrompt}
                  selectedLanguage={selectedLanguage}
                />
              </div>

              {/* Right Pane: Autonomous Operations Center (58% width) */}
              <div className="lg:col-span-7 h-full min-h-0">
                <OpsCenterPane
                  events={events}
                  isStreaming={isStreaming}
                  currentIncidentId={currentIncidentId}
                  pendingApproval={pendingApproval}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  isApproving={isApproving}
                  merchantData={merchantData}
                  onSoundboxUpdated={() => refreshMerchantData(currentMerchant.id)}
                  onClearTrace={() => setEvents([])}
                />
              </div>
            </div>
          </div>
        </main>
      )}
    </div>
  );
}

const API_BASE = '/api';

export async function loginMerchant(username, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Login failed');
  }
  return res.json();
}

export async function getMerchants() {
  const res = await fetch(`${API_BASE}/merchants`);
  if (!res.ok) throw new Error('Failed to fetch demo merchants');
  return res.json();
}

export async function getMerchantData(merchantId) {
  const res = await fetch(`${API_BASE}/merchants/${merchantId}/data`);
  if (!res.ok) throw new Error('Failed to fetch merchant data');
  return res.json();
}

export async function streamIncident(merchantId, message, onEvent, onDone, onError, language = 'en') {
  try {
    const response = await fetch(`${API_BASE}/incident/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ merchant_id: merchantId, message, language })
    });

    if (!response.ok) {
      throw new Error(`Incident stream error: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep last incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const parsed = JSON.parse(line.substring(6));
            onEvent(parsed);
          } catch (e) {
            console.error('Failed to parse SSE line:', line, e);
          }
        }
      }
    }
    if (onDone) onDone();
  } catch (err) {
    console.error('Stream incident failure:', err);
    if (onError) onError(err);
  }
}

export async function approveIncident(incidentId, approved, notes, onEvent, onDone, onError, language = 'en') {
  try {
    const response = await fetch(`${API_BASE}/incident/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ incident_id: incidentId, approved, notes, language })
    });

    if (!response.ok) throw new Error('Approval request failed');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const parsed = JSON.parse(line.substring(6));
            onEvent(parsed);
          } catch (e) {
            console.error('Failed to parse approval SSE line:', line, e);
          }
        }
      }
    }
    if (onDone) onDone();
  } catch (err) {
    if (onError) onError(err);
  }
}

export async function pingSoundbox(deviceId, amount = 60.0) {
  const res = await fetch(`${API_BASE}/soundbox/test-chime?device_id=${deviceId}&amount=${amount}`, {
    method: 'POST'
  });
  return res.json();
}

export async function fetchTTSAudio(text, language = 'en') {
  const res = await fetch(`${API_BASE}/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language })
  });
  if (!res.ok) {
    throw new Error('TTS synthesis failed');
  }
  return res.blob();
}

export async function resetDemoData() {
  const res = await fetch(`${API_BASE}/admin/reset-demo`, {
    method: 'POST'
  });
  return res.json();
}


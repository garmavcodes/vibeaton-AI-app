const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

import AsyncStorage from '@react-native-async-storage/async-storage';

export async function apiCall(endpoint: string, options: RequestInit = {}) {
  const token = await AsyncStorage.getItem('auth_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${API_URL}/api${endpoint}`, {
    ...options,
    headers: { ...headers, ...(options.headers as Record<string, string>) },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    let msg = 'API Error';
    if (typeof detail === 'string') msg = detail;
    else if (Array.isArray(detail)) msg = detail.map((e: any) => e.msg || JSON.stringify(e)).join(' ');
    throw new Error(msg);
  }
  return res.json();
}

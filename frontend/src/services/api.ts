import axios from 'axios';

// Base URL for API client
const API_BASE = '/api/v1';

export const authStorage = {
  getToken: () => localStorage.getItem("mcuverse_token"),
  setToken: (token: string) => localStorage.setItem("mcuverse_token", token),
  clear: () => localStorage.removeItem("mcuverse_token"),
};

axios.interceptors.request.use((config) => {
  const token = authStorage.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface ChatSettings {
  theme: string;
  llm_provider: string;
  preferred_model: string | null;
  temperature: number;
  top_k: number;
  spoiler_preference: string;
  watched_up_to_movie: string | null;
  watched_up_to_series: string | null;
  language: string;
}

export interface Citation {
  source: string;
  score: number | null;
  category: string | null;
  title: string | null;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[] | null;
  confidence_score: number;
  provider_used: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  settings?: ChatSettings;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  role: "admin" | "user" | "guest";
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user: UserProfile;
}

export interface DocumentResponse {
  id: string;
  title: string;
  category: string;
  file_path: string | null;
  metadata_json: Record<string, any> | null;
  created_at: string;
}

export interface IngestionStats {
  documents: number;
  entities: number;
  relationships: number;
}

export interface AnalyticsSummary {
  total_conversations: number;
  total_messages: number;
  average_confidence: number;
  average_retrieval_time_ms: number;
  average_llm_time_ms: number;
  cache_hit_rate: number;
  embedding_count: number;
  document_count: number;
  entity_count: number;
  index_loaded: boolean;
  index_chunks: number;
  llm_provider: string;
  cache_provider: string;
}

export type ChatMessage = Message;

export const defaultSettings: ChatSettings = {
  theme: "jarvis-blue",
  llm_provider: "retrieval_only",
  preferred_model: null,
  temperature: 0.7,
  top_k: 5,
  spoiler_preference: "full",
  watched_up_to_movie: null,
  watched_up_to_series: null,
  language: "en",
};

export const api = {
  register: async (payload: {
    email: string;
    password: string;
    full_name?: string;
  }): Promise<AuthResponse> => {
    const res = await axios.post(`${API_BASE}/auth/register`, payload);
    authStorage.setToken(res.data.access_token);
    return res.data;
  },

  login: async (payload: { email: string; password: string }): Promise<AuthResponse> => {
    const res = await axios.post(`${API_BASE}/auth/login`, payload);
    authStorage.setToken(res.data.access_token);
    return res.data;
  },

  createGuest: async (): Promise<AuthResponse> => {
    const res = await axios.post(`${API_BASE}/auth/guest`);
    authStorage.setToken(res.data.access_token);
    return res.data;
  },

  me: async (): Promise<UserProfile> => {
    const res = await axios.get(`${API_BASE}/auth/me`);
    return res.data;
  },

  // Chat APIs
  listConversations: async (): Promise<Conversation[]> => {
    const res = await axios.get(`${API_BASE}/chat/conversations`);
    return res.data;
  },

  getConversations: async (): Promise<Conversation[]> => {
    const res = await axios.get(`${API_BASE}/chat/conversations`);
    return res.data;
  },

  createConversation: async (
    title = "New Conversation",
    settings?: Partial<ChatSettings>
  ): Promise<Conversation> => {
    const res = await axios.post(`${API_BASE}/chat/conversations`, { title, settings });
    return res.data;
  },

  deleteConversation: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE}/chat/conversations/${id}`);
  },

  getMessages: async (id: string): Promise<Message[]> => {
    const res = await axios.get(`${API_BASE}/chat/conversations/${id}/messages`);
    return res.data;
  },

  sendMessage: async (id: string, content: string, settings?: ChatSettings): Promise<Message> => {
    const res = await axios.post(`${API_BASE}/chat/conversations/${id}/messages`, {
      content,
      settings
    });
    return res.data;
  },

  // Knowledge / Admin APIs
  triggerIngestion: async (): Promise<IngestionStats> => {
    const res = await axios.post(`${API_BASE}/knowledge/ingest`);
    return res.data;
  },

  reindexKnowledge: async (): Promise<{ status: string; chunks: number }> => {
    const res = await axios.post(`${API_BASE}/knowledge/reindex`);
    return res.data;
  },

  getDocuments: async (): Promise<DocumentResponse[]> => {
    const res = await axios.get(`${API_BASE}/knowledge/documents`);
    return res.data;
  },

  getEntities: async (): Promise<any[]> => {
    const res = await axios.get(`${API_BASE}/knowledge/entities`);
    return res.data;
  },

  getRelationships: async (): Promise<any[]> => {
    const res = await axios.get(`${API_BASE}/knowledge/relationships`);
    return res.data;
  },

  getHealth: async (): Promise<{ status: string }> => {
    const res = await axios.get(`${API_BASE}/health`);
    return res.data;
  },

  getAnalytics: async (): Promise<AnalyticsSummary> => {
    const res = await axios.get(`${API_BASE}/analytics`);
    return res.data;
  }
};

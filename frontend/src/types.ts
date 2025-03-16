// src/types.ts

export interface Feedback {
  rating: number | null; // 1-10 rating
  comment: string;       // User's comment about the message
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  feedback: Feedback | null;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string | Date;
  updatedAt: string | Date;
  user_id?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;  // "user" or "admin"
  avatar?: string;
  admin: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Admin types
export interface UserStats {
  id: string;
  username: string;
  email: string;
  role: string;
  conversation_count: number;
  message_count: number;
}

export interface FeedbackStats {
  total_feedback_count: number;
  average_rating: number;
  rating_distribution: Record<string, number>;
}

export interface DashboardData {
  total_users: number;
  total_conversations: number;
  total_messages: number;
  feedback_stats: FeedbackStats;
  user_stats: UserStats[];
}
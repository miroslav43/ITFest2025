import { Conversation, DashboardData, FeedbackStats, User, UserStats } from '../types';

// API base URL
const API_URL = 'http://localhost:8000';

// Helper function to handle API responses
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'An error occurred');
  }
  
  // Check if the response has content
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await response.json() as T;
  }
  
  return {} as T;
}

// Get the stored token
function getToken(): string | null {
  return localStorage.getItem('token');
}

// Admin API calls
export const adminApi = {
  // Get all users
  async getAllUsers(): Promise<User[]> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/users`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<User[]>(response);
  },
  
  // Get all conversations
  async getAllConversations(): Promise<Conversation[]> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/conversations`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<Conversation[]>(response);
  },
  
  // Get user statistics
  async getUserStats(): Promise<UserStats[]> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/stats/users`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<UserStats[]>(response);
  },
  
  // Get feedback statistics
  async getFeedbackStats(): Promise<FeedbackStats> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/stats/feedback`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<FeedbackStats>(response);
  },
  
  // Get dashboard data
  async getDashboardData(): Promise<DashboardData> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/dashboard`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<DashboardData>(response);
  },
  
  async getQuestions(): Promise<any[]> {
    const token = getToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${API_URL}/admin/questions`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return handleResponse<any[]>(response);
  },
  // Check if user is admin
  async isAdmin(): Promise<boolean> {
    try {
      const token = getToken();
      if (!token) {
        return false;
      }
      
      const response = await fetch(`${API_URL}/users/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      
      const user = await handleResponse<User>(response);
      return user.role === 'admin';
    } catch {
      return false;
    }
  }
};

export default adminApi;
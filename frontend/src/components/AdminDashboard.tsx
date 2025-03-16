import { useEffect, useState } from "react";
import { adminApi } from "../services/adminApi";
import "../styles/admin.css";
import { DashboardData, UserStats } from "../types";

// Reusable component to display truncated text with "See More" functionality
function TruncatedCell({
  text,
  threshold = 50,
}: {
  text: string;
  threshold?: number;
}) {
  const [expanded, setExpanded] = useState(false);

  if (!text) {
    return <span>-</span>;
  }

  if (text.length <= threshold) {
    return <span>{text}</span>;
  }

  return (
    <span>
      {expanded ? text : text.slice(0, threshold) + "..."}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{ marginLeft: "5px", fontSize: "0.8em" }}
      >
        {expanded ? "See Less" : "See More"}
      </button>
    </span>
  );
}

export default function AdminDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );
  const [questions, setQuestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "users" | "feedback" | "questions"
  >("overview");

  // Fetch dashboard data (overview, users, feedback, etc.)
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const data = await adminApi.getDashboardData();
        setDashboardData(data);
        setError(null);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error";
        setError(
          `Failed to load dashboard data: ${errorMessage}. Make sure you have admin privileges and the backend server is running.`
        );
        console.error("Error fetching dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Fetch questions when the "questions" tab is active
  useEffect(() => {
    if (activeTab === "questions") {
      const fetchQuestions = async () => {
        try {
          const data = await adminApi.getQuestions();
          setQuestions(data);
        } catch (err) {
          console.error("Error fetching questions:", err);
        }
      };

      fetchQuestions();
    }
  }, [activeTab]);

  if (loading) {
    return (
      <div className="admin-loading">
        <div className="spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => (window.location.href = "/")}>
          Return to Chat
        </button>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="admin-error">
        <h2>No Data Available</h2>
        <p>Could not retrieve dashboard data.</p>
        <button onClick={() => (window.location.href = "/")}>
          Return to Chat
        </button>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <header className="admin-header">
        <h1>Admin Dashboard</h1>
        <button
          onClick={() => (window.location.href = "/")}
          className="back-button"
        >
          Return to Chat
        </button>
      </header>

      <nav className="admin-tabs">
        <button
          className={activeTab === "overview" ? "active" : ""}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={activeTab === "users" ? "active" : ""}
          onClick={() => setActiveTab("users")}
        >
          Users
        </button>
        <button
          className={activeTab === "feedback" ? "active" : ""}
          onClick={() => setActiveTab("feedback")}
        >
          Feedback
        </button>
        <button
          className={activeTab === "questions" ? "active" : ""}
          onClick={() => setActiveTab("questions")}
        >
          Questions
        </button>
      </nav>

      <div className="admin-content">
        {activeTab === "overview" && (
          <div className="overview-tab">
            <div className="stats-cards">
              <div className="stat-card">
                <h3>Total Users</h3>
                <div className="stat-value">{dashboardData.total_users}</div>
              </div>
              <div className="stat-card">
                <h3>Total Conversations</h3>
                <div className="stat-value">
                  {dashboardData.total_conversations}
                </div>
              </div>
              <div className="stat-card">
                <h3>Total Messages</h3>
                <div className="stat-value">{dashboardData.total_messages}</div>
              </div>
              <div className="stat-card">
                <h3>Average Rating</h3>
                <div className="stat-value">
                  {dashboardData.feedback_stats.average_rating.toFixed(1)}
                  <span className="stat-unit">/10</span>
                </div>
              </div>
            </div>

            <div className="summary-section">
              <h3>System Summary</h3>
              <p>
                The chat system currently has {dashboardData.total_users}{" "}
                registered users who have created a total of{" "}
                {dashboardData.total_conversations} conversations. These
                conversations contain {dashboardData.total_messages} messages in
                total.
              </p>
              <p>
                Users have provided feedback on{" "}
                {dashboardData.feedback_stats.total_feedback_count} messages,
                with an average rating of{" "}
                {dashboardData.feedback_stats.average_rating.toFixed(1)}/10.
              </p>
            </div>
          </div>
        )}

        {activeTab === "users" && (
          <div className="users-tab">
            <h2>User Statistics</h2>
            <table className="users-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Conversations</th>
                  <th>Messages</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.user_stats.map((user: UserStats) => (
                  <tr key={user.id}>
                    <td>{user.username}</td>
                    <td>{user.email}</td>
                    <td>
                      <span className={`role-badge ${user.role}`}>
                        {user.role}
                      </span>
                    </td>
                    <td>{user.conversation_count}</td>
                    <td>{user.message_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "feedback" && (
          <div className="feedback-tab">
            <h2>Feedback Statistics</h2>

            <div className="feedback-summary">
              <div className="feedback-stat">
                <h3>Total Feedback</h3>
                <div className="stat-value">
                  {dashboardData.feedback_stats.total_feedback_count}
                </div>
              </div>
              <div className="feedback-stat">
                <h3>Average Rating</h3>
                <div className="stat-value">
                  {dashboardData.feedback_stats.average_rating.toFixed(1)}/10
                </div>
              </div>
            </div>

            <h3>Rating Distribution</h3>
            <div className="rating-distribution">
              {Object.entries(dashboardData.feedback_stats.rating_distribution)
                .sort(([a], [b]) => Number(a) - Number(b))
                .map(([rating, count]) => (
                  <div key={rating} className="rating-bar">
                    <div className="rating-label">{rating}</div>
                    <div
                      className="rating-value-bar"
                      style={{
                        width: `${Math.min(
                          100,
                          (count /
                            dashboardData.feedback_stats.total_feedback_count) *
                            100
                        )}%`,
                      }}
                    ></div>
                    <div className="rating-count">{count}</div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {activeTab === "questions" && (
          <div className="questions-tab">
            <h2>Questions with Feedback</h2>
            <table className="questions-table">
              <thead>
                <tr>
                  <th>Conversation ID</th>
                  <th>Question</th>
                  <th>Response</th>
                  <th>Rating</th>
                  <th>Note</th>
                  <th>Asked At</th>
                </tr>
              </thead>
              <tbody>
                {questions.map((q) => (
                  <tr key={q.conversation_id}>
                    <td>{q.conversation_id}</td>
                    <td>
                      <TruncatedCell text={q.question} threshold={50} />
                    </td>
                    <td>
                      <TruncatedCell text={q.response} threshold={50} />
                    </td>
                    <td>{q.rating}</td>
                    <td>
                      <TruncatedCell text={q.note} threshold={50} />
                    </td>
                    <td>{new Date(q.asked_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

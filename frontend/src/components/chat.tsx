import React, { useState, useRef, useEffect } from "react";
import { Message, Feedback } from "../types";
import { chatApi, feedbackApi } from "../services/api";
import '../styles/chat.css';

interface ChatProps {
  conversationId?: string;
  initialMessages?: Message[];
  onSaveConversation?: (messages: Message[]) => void;
}

export default function Chat({ 
  conversationId, 
  initialMessages = [], 
  onSaveConversation 
}: ChatProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState<string>("");
  const [feedbackRating, setFeedbackRating] = useState<number | null>(null);
  const [feedbackComment, setFeedbackComment] = useState<string>("");
  const [activeFeedbackId, setActiveFeedbackId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Re-initialize local messages if conversation changes
  useEffect(() => {
    setMessages(initialMessages);
  }, [conversationId, initialMessages]);

  // Handle sending a new user message
  const handleSend = async (): Promise<void> => {
    if (!input.trim() || isLoading) return;

    // 1. Add the user's message to the chat list
    const userMessage: Message = {
      id: `${Date.now()}-user`,
      role: "user",
      content: input,
      feedback: null,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // 2. Send message to API
      const response = await chatApi.sendMessage(input, conversationId);

      // 3. Add the AI's response to the chat list
      const aiMessage: Message = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        content: response.message,
        feedback: null,
      };
      setMessages((prev) => {
         const updatedMessages = [...prev, aiMessage];
         if (onSaveConversation) {
            onSaveConversation(updatedMessages);
         }
         return updatedMessages;
      });

    } catch (error) {
      console.error("Error fetching AI response:", error);
      // Optionally add an error message to the chat
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle feedback form for a specific message
  const toggleFeedbackForm = (messageId: string): void => {
    if (activeFeedbackId === messageId) {
      // Close the form if it's already open
      setActiveFeedbackId(null);
      setFeedbackRating(null);
      setFeedbackComment("");
    } else {
      // Open the form for this message
      setActiveFeedbackId(messageId);
      
      // Pre-fill with existing feedback if any
      const message = messages.find(msg => msg.id === messageId);
      if (message?.feedback) {
        setFeedbackRating(message.feedback.rating);
        setFeedbackComment(message.feedback.comment);
      } else {
        setFeedbackRating(null);
        setFeedbackComment("");
      }
    }
  };

  // Submit feedback for a message
  const submitFeedback = async (messageId: string): Promise<void> => {
    if (feedbackRating === null) {
      alert("Please provide a rating from 1 to 10");
      return;
    }

    const newFeedback: Feedback = {
      rating: feedbackRating,
      comment: feedbackComment
    };

    // Update local state
    setMessages((prevMessages) =>
      prevMessages.map((msg) => {
        if (msg.id === messageId) {
          return { ...msg, feedback: newFeedback };
        }
        return msg;
      })
    );

    // Submit feedback to API if we have a conversation ID
    if (conversationId) {
      try {
        await feedbackApi.submitFeedback(
          messageId,
          conversationId,
          feedbackRating,
          feedbackComment
        );
      } catch (error) {
        console.error("Error submitting feedback:", error);
        // Optionally show an error message
      }
    }

    // Reset and close feedback form
    setActiveFeedbackId(null);
    setFeedbackRating(null);
    setFeedbackComment("");
  };

  // Generate rating buttons (1-10)
  const renderRatingButtons = () => {
    const buttons = [];
    for (let i = 1; i <= 10; i++) {
      buttons.push(
        <button
          key={i}
          className={`rating-button ${feedbackRating === i ? 'rating-button-selected' : 'rating-button-unselected'}`}
          onClick={() => setFeedbackRating(i)}
        >
          {i}
        </button>
      );
    }
    return buttons;
  };

  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message ${msg.role === "user" ? "user-message" : "assistant-message"}`}
          >
            <div className="message-content">
              <div className="message-role">
                {msg.role === "user" ? "You" : "Assistant"}
              </div>
              <p className="message-text">{msg.content}</p>
            </div>
            
            {/* Feedback section only for AI (assistant) messages */}
            {msg.role === "assistant" && (
              <div className="feedback-section">
                {/* Show feedback if it exists */}
                {msg.feedback && activeFeedbackId !== msg.id && (
                  <div className="existing-feedback">
                    <div className="feedback-rating">
                      Rating: <span className="rating-value">{msg.feedback.rating}/10</span>
                    </div>
                    {msg.feedback.comment && (
                      <div className="feedback-comment">
                        "{msg.feedback.comment}"
                      </div>
                    )}
                    <button 
                      className="edit-feedback-button"
                      onClick={() => toggleFeedbackForm(msg.id)}
                    >
                      Edit Feedback
                    </button>
                  </div>
                )}
                
                {/* Feedback button if no feedback exists */}
                {!msg.feedback && activeFeedbackId !== msg.id && (
                  <button 
                    className="give-feedback-button"
                    onClick={() => toggleFeedbackForm(msg.id)}
                  >
                    Give Feedback
                  </button>
                )}
                
                {/* Feedback form */}
                {activeFeedbackId === msg.id && (
                  <div className="feedback-form">
                    <div className="feedback-form-title">Rate this response (1-10):</div>
                    <div className="rating-buttons-container">
                      {renderRatingButtons()}
                    </div>
                    <textarea
                      className="comment-input"
                      placeholder="Add a comment (optional)"
                      value={feedbackComment}
                      onChange={(e) => setFeedbackComment(e.target.value)}
                    />
                    <div className="feedback-form-buttons">
                      <button 
                        className="cancel-button"
                        onClick={() => setActiveFeedbackId(null)}
                      >
                        Cancel
                      </button>
                      <button 
                        className="submit-button"
                        onClick={() => submitFeedback(msg.id)}
                      >
                        Submit Feedback
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="message assistant-message">
            <div className="message-content">
              <div className="message-role">Assistant</div>
              <p className="message-text">Thinking...</p>
            </div>
          </div>
        )}
        
        {/* Invisible element to scroll to */}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <input
          className="input-field"
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            // Send on Enter key
            if (e.key === "Enter") handleSend();
          }}
          disabled={isLoading}
        />
        <button 
          className="send-button"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}
/**
 * @file CreateGoal.jsx
 * @description Goal creation page with LLM-powered category detection,
 * follow-up questions, and toast notifications.
 *
 * API: POST /goals/category
 */

import React, { useState } from "react";
import { useToast } from "../components/Toast";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/* ─── Follow-Up Questions Panel ─── */
function FollowUpPanel({ questions, answers, onAnswer, onSubmit, loading }) {
  const allAnswered = questions.every((_, i) => answers[i]?.trim());

  return (
    <div
      style={{
        marginTop: 20,
        padding: 20,
        borderRadius: 16,
        background: "rgba(99, 102, 241, 0.04)",
        border: "1px solid rgba(99, 102, 241, 0.15)",
        animation: "fadeSlideIn 0.35s ease",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 16,
        }}
      >
        <span
          style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            background: "rgba(99, 102, 241, 0.12)",
            display: "grid",
            placeItems: "center",
            fontSize: 14,
          }}
        >
          ?
        </span>
        <span
          style={{
            fontSize: 15,
            fontWeight: 600,
            color: "var(--Text)",
          }}
        >
          We need a bit more detail
        </span>
      </div>

      <div style={{ display: "grid", gap: 14 }}>
        {questions.map((q, i) => (
          <div key={i} className="Field">
            <label
              className="FieldLabel"
              style={{ fontSize: 13, color: "var(--Muted)" }}
            >
              {q}
            </label>
            <input
              className="Input"
              type="text"
              placeholder="Your answer..."
              value={answers[i] || ""}
              onChange={(e) => onAnswer(i, e.target.value)}
            />
          </div>
        ))}
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginTop: 16,
        }}
      >
        <button
          className="Button"
          onClick={onSubmit}
          disabled={!allAnswered || loading}
          style={{ fontSize: 13, padding: "10px 20px" }}
        >
          {loading ? "Processing..." : "Submit & Create Goal"}
        </button>
      </div>
    </div>
  );
}

/* ─── Category Badge ─── */
function CategoryBadge({ category }) {
  const labels = {
    career_and_learning: { text: "Career & Learning", color: "#6366F1" },
    fitness: { text: "Fitness", color: "#059669" },
    immigration: { text: "Immigration", color: "#D97706" },
  };

  const info = labels[category] || {
    text: category,
    color: "var(--Muted)",
  };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: 12,
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.5px",
        padding: "5px 12px",
        borderRadius: 99,
        color: info.color,
        background: `${info.color}12`,
        border: `1px solid ${info.color}25`,
        animation: "fadeSlideIn 0.3s ease",
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: info.color,
        }}
      />
      {info.text}
    </span>
  );
}

/* ─── Main Component ─── */
const CreateGoal = () => {
  const toast = useToast();

  const [form, setForm] = useState({
    goal: "",
    startDate: "",
    endDate: "",
    note: "",
  });

  const [loading, setLoading] = useState(false);
  const [detectedCategory, setDetectedCategory] = useState(null);
  const [followUpQuestions, setFollowUpQuestions] = useState([]);
  const [followUpAnswers, setFollowUpAnswers] = useState({});
  const [goalCreated, setGoalCreated] = useState(null);

  const token = localStorage.getItem("agp_auth_token");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  /* Reset follow-up state */
  const resetFollowUp = () => {
    setDetectedCategory(null);
    setFollowUpQuestions([]);
    setFollowUpAnswers({});
    setGoalCreated(null);
  };

  /* Validate form before submit */
  const validate = () => {
    if (!form.goal.trim()) {
      toast.error("Please describe your goal.");
      return false;
    }
    if (!form.startDate || !form.endDate) {
      toast.error("Please select both start and end dates.");
      return false;
    }
    if (new Date(form.endDate) <= new Date(form.startDate)) {
      toast.error("End date must be after start date.");
      return false;
    }
    return true;
  };

  /* Build API payload */
  const buildPayload = (extraNote = "") => {
    const userId = localStorage.getItem("agp_user_id");
    return {
      goal_text: form.goal,
      start_date: form.startDate,
      end_date: form.endDate,
      note: [form.note, extraNote].filter(Boolean).join("\n") || null,
      ...(userId && { user_id: parseInt(userId) }),
    };
  };

  /* Call the category API */
  const callCategoryAPI = async (payload) => {
    const res = await fetch(`${API_BASE}/goals/category`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed (${res.status})`);
    }

    return res.json();
  };

  /* Initial submit */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    resetFollowUp();
    setLoading(true);

    try {
      const data = await callCategoryAPI(buildPayload());

      setDetectedCategory(data.category);

      if (data.status === "accepted" && data.goal_id) {
        setGoalCreated(data.goal_id);
        toast.success(data.message || "Goal created successfully!");
      } else if (data.status === "needs_more_info") {
        setFollowUpQuestions(data.follow_up_questions || []);
        toast.info("Almost there — please answer a few follow-up questions.");
      }
    } catch (err) {
      toast.error(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  /* Submit with follow-up answers */
  const handleFollowUpSubmit = async () => {
    setLoading(true);

    try {
      // Append follow-up answers to the note
      const extraNote = followUpQuestions
        .map((q, i) => `${q}: ${followUpAnswers[i] || ""}`)
        .join("\n");

      const data = await callCategoryAPI(buildPayload(extraNote));

      setDetectedCategory(data.category);

      if (data.status === "accepted" && data.goal_id) {
        setGoalCreated(data.goal_id);
        setFollowUpQuestions([]);
        toast.success(data.message || "Goal created successfully!");
      } else if (data.status === "needs_more_info") {
        setFollowUpQuestions(data.follow_up_questions || []);
        setFollowUpAnswers({});
        toast.info("A few more details needed.");
      }
    } catch (err) {
      toast.error(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  /* Reset everything for a new goal */
  const handleCreateAnother = () => {
    setForm({ goal: "", startDate: "", endDate: "", note: "" });
    resetFollowUp();
  };

  return (
    <div className="Container" style={{ maxWidth: 640, margin: "0 auto" }}>
      {/* Inline keyframes */}
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Page Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ margin: "0 0 4px", fontSize: 26, fontWeight: 800 }}>
          Create Goal
        </h1>
        <p style={{ color: "var(--Muted)", margin: 0, fontSize: 15 }}>
          Clearly define what you want to achieve and when.
        </p>
      </div>

      {/* ─── Success State ─── */}
      {goalCreated && (
        <div
          className="Panel"
          style={{
            textAlign: "center",
            padding: "40px 24px",
            animation: "fadeSlideIn 0.4s ease",
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: "rgba(5, 150, 105, 0.1)",
              display: "grid",
              placeItems: "center",
              margin: "0 auto 16px",
              fontSize: 24,
              color: "#059669",
            }}
          >
            ✓
          </div>
          <h2 style={{ margin: "0 0 8px", fontSize: 20, fontWeight: 700 }}>
            Goal Created!
          </h2>
          {detectedCategory && (
            <div style={{ marginBottom: 12 }}>
              <CategoryBadge category={detectedCategory} />
            </div>
          )}
          <p
            style={{
              color: "var(--Muted)",
              fontSize: 14,
              margin: "0 0 24px",
              lineHeight: 1.6,
            }}
          >
            Your goal has been created and tasks are being generated.
            <br />
            Check your dashboard to track progress.
          </p>
          <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
            <button className="Button" onClick={handleCreateAnother}>
              Create Another
            </button>
            <button
              className="Button ButtonGhost"
              onClick={() => (window.location.href = "/dashboard")}
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      )}

      {/* ─── Form ─── */}
      {!goalCreated && (
        <div className="Panel">
          {/* Detected category badge */}
          {detectedCategory && (
            <div style={{ marginBottom: 16 }}>
              <span
                style={{
                  fontSize: 12,
                  color: "var(--Muted)",
                  marginRight: 8,
                }}
              >
                Detected:
              </span>
              <CategoryBadge category={detectedCategory} />
            </div>
          )}

          <form className="Form" onSubmit={handleSubmit}>
            {/* Goal */}
            <div className="Field">
              <label className="FieldLabel">Goal</label>
              <textarea
                className="Input"
                name="goal"
                rows="3"
                placeholder="e.g., Lose 10kg through gym and diet control"
                value={form.goal}
                onChange={handleChange}
                required
                disabled={followUpQuestions.length > 0}
                style={{ resize: "vertical" }}
              />
            </div>

            {/* Dates */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: 12,
              }}
            >
              <div className="Field">
                <label className="FieldLabel">Start Date</label>
                <input
                  className="Input"
                  type="date"
                  name="startDate"
                  value={form.startDate}
                  onChange={handleChange}
                  required
                  disabled={followUpQuestions.length > 0}
                />
              </div>
              <div className="Field">
                <label className="FieldLabel">End Date</label>
                <input
                  className="Input"
                  type="date"
                  name="endDate"
                  value={form.endDate}
                  onChange={handleChange}
                  required
                  disabled={followUpQuestions.length > 0}
                />
              </div>
            </div>

            {/* Note */}
            <div className="Field">
              <label className="FieldLabel">Note (optional)</label>
              <textarea
                className="Input"
                name="note"
                rows="2"
                placeholder="Optional context, constraints, or motivation"
                value={form.note}
                onChange={handleChange}
                disabled={followUpQuestions.length > 0}
                style={{ resize: "vertical" }}
              />
            </div>

            {/* Submit — only show when no follow-ups */}
            {followUpQuestions.length === 0 && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  marginTop: 12,
                }}
              >
                <button
                  className="Button"
                  type="submit"
                  disabled={loading}
                >
                  {loading ? "Analyzing..." : "Create Goal"}
                </button>
              </div>
            )}
          </form>

          {/* ─── Follow-Up Questions ─── */}
          {followUpQuestions.length > 0 && (
            <FollowUpPanel
              questions={followUpQuestions}
              answers={followUpAnswers}
              onAnswer={(i, val) =>
                setFollowUpAnswers((prev) => ({ ...prev, [i]: val }))
              }
              onSubmit={handleFollowUpSubmit}
              loading={loading}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default CreateGoal;
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";

const API = "http://localhost:8000";

const INTERESTS = [
  { value: "coding", label: "💻 Coding / Software" },
  { value: "fitness", label: "🏋️ Fitness / Health" },
  { value: "immigration", label: "✈️ Immigration / Visa" },
  { value: "career", label: "💼 Career Development" },
];

const LEVELS = [
  { value: "beginner",     label: "Beginner",     desc: "Just starting out" },
  { value: "intermediate", label: "Intermediate", desc: "Some experience" },
  { value: "advanced",     label: "Advanced",     desc: "Highly experienced" },
];

const HOURS = [5, 10, 15, 20];

export default function Onboarding() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const email = params.get("email") || "";

  const [step, setStep]     = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");

  const [form, setForm] = useState({
    interest: "",
    experience_level: "",
    hours_per_week: 10,
    target_goal: "",
  });

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  // ── Step guards ────────────────────────────────────────────────────────────
  const canNext = [
    form.interest !== "",
    form.experience_level !== "",
    form.hours_per_week > 0,
    form.target_goal.trim().length >= 5,
  ];

  const handleSubmit = async () => {
    setError(""); setLoading(true);
    try {
      // Get user_id from URL param (set during registration response)
      // or fall back to reading from localStorage
      const params = new URLSearchParams(window.location.search);
      const userId = localStorage.getItem("pending_user_id") || 1;

      await axios.post("http://localhost:8000/onboarding/preferences", {
        user_id:          parseInt(userId),
        interest:         form.interest,
        experience_level: form.experience_level,
        hours_per_week:   form.hours_per_week,
        target_goal:      form.target_goal,
      });

      // Clear pending id and redirect to login with success message
      localStorage.removeItem("pending_user_id");
      navigate("/login?registered=true");
    } catch (err) {
      console.error("Failed to save preferences:", err);
      setError("Failed to generate your roadmap. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ── Step definitions ───────────────────────────────────────────────────────
  const steps = [
    {
      title: "What are you interested in?",
      subtitle: "We'll build your roadmap around this.",
      content: (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          {INTERESTS.map((i) => (
            <button
              key={i.value}
              onClick={() => set("interest", i.value)}
              style={{
                padding: "16px",
                borderRadius: "10px",
                border: `2px solid ${form.interest === i.value ? "#4F46E5" : "#E5E7EB"}`,
                background: form.interest === i.value ? "#EEF2FF" : "white",
                color: form.interest === i.value ? "#4F46E5" : "#374151",
                fontWeight: 600,
                fontSize: "15px",
                cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              {i.label}
            </button>
          ))}
        </div>
      ),
    },
    {
      title: "What's your experience level?",
      subtitle: "Be honest — we'll tailor the pace accordingly.",
      content: (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {LEVELS.map((l) => (
            <button
              key={l.value}
              onClick={() => set("experience_level", l.value)}
              style={{
                padding: "16px 20px",
                borderRadius: "10px",
                border: `2px solid ${form.experience_level === l.value ? "#4F46E5" : "#E5E7EB"}`,
                background: form.experience_level === l.value ? "#EEF2FF" : "white",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              <span style={{
                fontWeight: 700, fontSize: "15px",
                color: form.experience_level === l.value ? "#4F46E5" : "#111827",
              }}>
                {l.label}
              </span>
              <span style={{ fontSize: "13px", color: "#6B7280" }}>{l.desc}</span>
            </button>
          ))}
        </div>
      ),
    },
    {
      title: "How many hours per week can you dedicate?",
      subtitle: "We'll make sure the plan is realistic for your schedule.",
      content: (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          {HOURS.map((h) => (
            <button
              key={h}
              onClick={() => set("hours_per_week", h)}
              style={{
                padding: "20px",
                borderRadius: "10px",
                border: `2px solid ${form.hours_per_week === h ? "#4F46E5" : "#E5E7EB"}`,
                background: form.hours_per_week === h ? "#EEF2FF" : "white",
                color: form.hours_per_week === h ? "#4F46E5" : "#374151",
                fontWeight: 700,
                fontSize: "18px",
                cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              {h}h / week
            </button>
          ))}
        </div>
      ),
    },
    {
      title: "What's your main goal?",
      subtitle: "In one sentence, what do you want to achieve?",
      content: (
        <textarea
          value={form.target_goal}
          onChange={(e) => set("target_goal", e.target.value)}
          placeholder="e.g. Get a junior developer job within 6 months"
          rows={4}
          style={{
            width: "100%",
            padding: "14px",
            borderRadius: "10px",
            border: "2px solid #E5E7EB",
            fontSize: "15px",
            fontFamily: "inherit",
            resize: "none",
            outline: "none",
            boxSizing: "border-box",
            transition: "border-color 0.15s",
          }}
          onFocus={(e) => (e.target.style.borderColor = "#4F46E5")}
          onBlur={(e) => (e.target.style.borderColor = "#E5E7EB")}
        />
      ),
    },
  ];

  const currentStep = steps[step];
  const isLast = step === steps.length - 1;

  return (
    <div style={{
      minHeight: "100vh",
      background: "#F9FAFB",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px",
    }}>
      <div style={{
        background: "white",
        borderRadius: "16px",
        boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
        padding: "40px",
        width: "100%",
        maxWidth: "520px",
      }}>

        {/* Progress bar */}
        <div style={{ marginBottom: "32px" }}>
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "8px",
          }}>
            <span style={{ fontSize: "13px", color: "#6B7280", fontWeight: 600 }}>
              Step {step + 1} of {steps.length}
            </span>
            <span style={{ fontSize: "13px", color: "#4F46E5", fontWeight: 600 }}>
              {Math.round(((step + 1) / steps.length) * 100)}%
            </span>
          </div>
          <div style={{
            height: "6px", background: "#E5E7EB", borderRadius: "999px", overflow: "hidden",
          }}>
            <div style={{
              height: "100%",
              width: `${((step + 1) / steps.length) * 100}%`,
              background: "#4F46E5",
              borderRadius: "999px",
              transition: "width 0.3s ease",
            }} />
          </div>
        </div>

        {/* Step content */}
        <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#111827", marginBottom: "6px" }}>
          {currentStep.title}
        </h2>
        <p style={{ fontSize: "14px", color: "#6B7280", marginBottom: "24px" }}>
          {currentStep.subtitle}
        </p>

        {currentStep.content}

        {error && (
          <div style={{
            marginTop: "16px", padding: "12px", background: "#FEF2F2",
            border: "1px solid #FECACA", borderRadius: "8px",
            color: "#DC2626", fontSize: "14px",
          }}>
            {error}
          </div>
        )}

        {/* Navigation buttons */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: "32px",
          gap: "12px",
        }}>
          {step > 0 && (
            <button
              onClick={() => setStep((s) => s - 1)}
              style={{
                flex: 1, padding: "12px", borderRadius: "8px",
                border: "2px solid #E5E7EB", background: "white",
                color: "#374151", fontWeight: 600, cursor: "pointer",
                fontSize: "15px",
              }}
            >
              Back
            </button>
          )}

          <button
            onClick={isLast ? handleSubmit : () => setStep((s) => s + 1)}
            disabled={!canNext[step] || loading}
            style={{
              flex: 1, padding: "12px", borderRadius: "8px",
              background: canNext[step] && !loading ? "#4F46E5" : "#E5E7EB",
              color: canNext[step] && !loading ? "white" : "#9CA3AF",
              fontWeight: 700, cursor: canNext[step] && !loading ? "pointer" : "not-allowed",
              border: "none", fontSize: "15px", transition: "all 0.15s",
            }}
          >
            {loading ? "Generating..." : isLast ? "Generate My Roadmap 🚀" : "Next →"}
          </button>
        </div>
      </div>
    </div>
  );
}
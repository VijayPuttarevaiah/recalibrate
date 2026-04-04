/**
 * @file Onboarding.jsx
 * @description Multi-step onboarding wizard — professional UI.
 * Collects user preferences (interest, level, hours, goal) and submits
 * them to generate a personalized roadmap.
 */

import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// ── Data ──────────────────────────────────────────────────────────────────────
const INTERESTS = [
  { value: "coding",       icon: "💻", label: "Coding / Software" },
  { value: "fitness",      icon: "🏋️", label: "Fitness / Health" },
  { value: "immigration",  icon: "✈️",  label: "Immigration / Visa" },
  { value: "career",       icon: "💼", label: "Career Development" },
];

const LEVELS = [
  { value: "beginner",     icon: "🌱", label: "Beginner",     desc: "Just starting out" },
  { value: "intermediate", icon: "🌿", label: "Intermediate", desc: "Some experience" },
  { value: "advanced",     icon: "🌳", label: "Advanced",     desc: "Highly experienced" },
];

const HOURS = [
  { value: 5,  icon: "⚡", label: "5h / week" },
  { value: 10, icon: "🔥", label: "10h / week" },
  { value: 15, icon: "💪", label: "15h / week" },
  { value: 20, icon: "🚀", label: "20h / week" },
];

const STEP_META = [
  { key: "interest",         label: "Interest", emoji: "🎯" },
  { key: "experience_level", label: "Level",    emoji: "📊" },
  { key: "hours_per_week",   label: "Schedule", emoji: "⏰" },
  { key: "target_goal",      label: "Goal",     emoji: "🏆" },
];

// ── Component ─────────────────────────────────────────────────────────────────
export default function Onboarding() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const email = params.get("email") || "";

  const [step, setStep]       = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const [form, setForm] = useState({
    interest: "",
    experience_level: "",
    hours_per_week: 10,
    target_goal: "",
  });

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  // ── Step guards ───────────────────────────────────────────────────────────
  const canNext = [
    form.interest !== "",
    form.experience_level !== "",
    form.hours_per_week > 0,
    form.target_goal.trim().length >= 5,
  ];

  const handleSubmit = async () => {
    setError(""); setLoading(true);
    try {
      const userId = localStorage.getItem("pending_user_id") || 1;

      await axios.post(`${API}/onboarding/preferences`, {
        user_id:          parseInt(userId),
        interest:         form.interest,
        experience_level: form.experience_level,
        hours_per_week:   form.hours_per_week,
        target_goal:      form.target_goal,
      });

      localStorage.removeItem("pending_user_id");
      navigate("/login?registered=true");
    } catch (err) {
      console.error("Failed to save preferences:", err);
      setError("Failed to generate your roadmap. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const isLast = step === STEP_META.length - 1;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="OnboardShell">
      <div className="OnboardCard">

        {/* Badge */}
        <div className="OnboardBadge">🎯 Personalize Your Journey</div>

        {/* ── Progress indicator ── */}
        <div className="OnboardProgress">
          {STEP_META.map((s, i) => (
            <ProgressNode key={s.key} index={i} current={step} label={s.label} />
          ))}
        </div>

        {/* ── Step content (animated) ── */}
        <div className="OnboardStepContent" key={step}>
          <span className="OnboardStepEmoji">{STEP_META[step].emoji}</span>

          {/* Step 0 — Interest */}
          {step === 0 && (
            <>
              <h2 className="OnboardTitle">What are you interested in?</h2>
              <p className="OnboardSubtitle">We'll build your roadmap around this.</p>
              <div className="OnboardGrid">
                {INTERESTS.map((i) => (
                  <button
                    key={i.value}
                    className={`OnboardOption ${form.interest === i.value ? "OnboardOption--active" : ""}`}
                    onClick={() => set("interest", i.value)}
                    type="button"
                  >
                    <span className="OnboardOptionIcon">{i.icon}</span>
                    <span className="OnboardOptionLabel">{i.label}</span>
                  </button>
                ))}
              </div>
            </>
          )}

          {/* Step 1 — Experience Level */}
          {step === 1 && (
            <>
              <h2 className="OnboardTitle">What's your experience level?</h2>
              <p className="OnboardSubtitle">Be honest — we'll tailor the pace accordingly.</p>
              <div className="OnboardLevels">
                {LEVELS.map((l) => (
                  <button
                    key={l.value}
                    className={`OnboardLevel ${form.experience_level === l.value ? "OnboardLevel--active" : ""}`}
                    onClick={() => set("experience_level", l.value)}
                    type="button"
                  >
                    <div>
                      <span className="OnboardLevelName">{l.icon} {l.label}</span>
                      <div className="OnboardLevelDesc">{l.desc}</div>
                    </div>
                    <span className="OnboardLevelCheck">
                      {form.experience_level === l.value ? "✓" : ""}
                    </span>
                  </button>
                ))}
              </div>
            </>
          )}

          {/* Step 2 — Hours per Week */}
          {step === 2 && (
            <>
              <h2 className="OnboardTitle">How many hours per week can you dedicate?</h2>
              <p className="OnboardSubtitle">We'll make sure the plan is realistic for your schedule.</p>
              <div className="OnboardGrid">
                {HOURS.map((h) => (
                  <button
                    key={h.value}
                    className={`OnboardOption OnboardOption--hours ${form.hours_per_week === h.value ? "OnboardOption--active" : ""}`}
                    onClick={() => set("hours_per_week", h.value)}
                    type="button"
                  >
                    <span className="OnboardOptionIcon">{h.icon}</span>
                    <span className="OnboardOptionLabel">{h.label}</span>
                  </button>
                ))}
              </div>
            </>
          )}

          {/* Step 3 — Target Goal */}
          {step === 3 && (
            <>
              <h2 className="OnboardTitle">What's your main goal?</h2>
              <p className="OnboardSubtitle">In one sentence, what do you want to achieve?</p>
              <textarea
                className="OnboardTextarea"
                value={form.target_goal}
                onChange={(e) => set("target_goal", e.target.value)}
                placeholder="e.g. Get a junior developer job within 6 months"
                rows={4}
              />
            </>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="OnboardAlert">
            <span>⚠️</span> {error}
          </div>
        )}

        {/* ── Navigation ── */}
        <div className="OnboardNav">
          {step > 0 && (
            <button
              className="OnboardBtnGhost"
              onClick={() => setStep((s) => s - 1)}
              type="button"
            >
              ← Back
            </button>
          )}

          <button
            className="OnboardBtnPrimary"
            onClick={isLast ? handleSubmit : () => setStep((s) => s + 1)}
            disabled={!canNext[step] || loading}
            type="button"
          >
            {loading ? (
              <>
                <span className="OnboardSpinner" />
                Generating…
              </>
            ) : isLast ? (
              "Generate My Roadmap 🚀"
            ) : (
              "Next →"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Progress Node sub-component ─────────────────────────────────────────────
function ProgressNode({ index, current, label }) {
  const isDone   = index < current;
  const isActive = index === current;
  const total    = STEP_META.length;

  const dotClass = [
    "OnboardProgressDot",
    isActive ? "OnboardProgressDot--active" : "",
    isDone   ? "OnboardProgressDot--done"   : "",
  ].join(" ");

  const labelClass = [
    "OnboardProgressLabel",
    isActive ? "OnboardProgressLabel--active" : "",
    isDone   ? "OnboardProgressLabel--done"   : "",
  ].join(" ");

  return (
    <>
      <div className="OnboardProgressStep">
        <div className={dotClass}>
          {isDone ? "✓" : index + 1}
        </div>
        <span className={labelClass}>{label}</span>
      </div>
      {index < total - 1 && (
        <div
          className={`OnboardProgressConnector ${isDone ? "OnboardProgressConnector--done" : ""}`}
        />
      )}
    </>
  );
}
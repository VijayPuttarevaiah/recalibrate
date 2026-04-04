import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function Roadmap() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [roadmap, setRoadmap] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    axios
      .get(`${API}/roadmap/${userId}`)
      .then((res) => {
        setRoadmap(res.data.roadmap);
        setLoading(false);
      })
      .catch((err) => {
        setError(
          err.response?.status === 404
            ? "No roadmap found. Please complete onboarding first."
            : "Failed to load your roadmap. Please try again."
        );
        setLoading(false);
      });
  }, [userId]);

  if (loading) {
    return (
      <div style={{
        minHeight: "100vh", display: "flex", alignItems: "center",
        justifyContent: "center", flexDirection: "column", gap: "16px",
        background: "#F9FAFB",
      }}>
        <div style={{
          width: "40px", height: "40px", border: "4px solid #E5E7EB",
          borderTop: "4px solid #4F46E5", borderRadius: "50%",
          animation: "spin 0.8s linear infinite",
        }} />
        <p style={{ color: "#6B7280", fontWeight: 600 }}>Generating your personalized roadmap...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        minHeight: "100vh", display: "flex", alignItems: "center",
        justifyContent: "center", background: "#F9FAFB",
      }}>
        <div style={{
          background: "white", borderRadius: "12px", padding: "40px",
          textAlign: "center", maxWidth: "400px",
          boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
        }}>
          <div style={{ fontSize: "40px", marginBottom: "16px" }}>⚠️</div>
          <p style={{ color: "#374151", marginBottom: "20px" }}>{error}</p>
          <button
            onClick={() => navigate("/onboarding")}
            style={{
              background: "#4F46E5", color: "white", border: "none",
              borderRadius: "8px", padding: "12px 24px",
              fontWeight: 700, cursor: "pointer", fontSize: "15px",
            }}
          >
            Start Onboarding
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "#F9FAFB", padding: "32px 24px" }}>
      <div style={{ maxWidth: "720px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{ marginBottom: "40px" }}>
          <h1 style={{
            fontSize: "30px", fontWeight: 800, color: "#111827", marginBottom: "8px",
          }}>
            🗺️ Your Personalized Roadmap
          </h1>
          <p style={{ color: "#6B7280", fontSize: "15px" }}>
            Follow these phases to reach your goal. Each phase builds on the previous one.
          </p>
        </div>

        {/* Timeline */}
        <div style={{ position: "relative" }}>
          {/* Vertical line */}
          <div style={{
            position: "absolute", left: "19px", top: "24px",
            bottom: "24px", width: "2px", background: "#E5E7EB",
          }} />

          {roadmap.map((phase, index) => (
            <div
              key={index}
              style={{
                display: "flex", gap: "20px", marginBottom: "28px",
                position: "relative",
              }}
            >
              {/* Timeline dot */}
              <div style={{
                width: "40px", height: "40px", borderRadius: "50%",
                background: "#4F46E5", color: "white",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontWeight: 800, fontSize: "14px", flexShrink: 0,
                boxShadow: "0 0 0 4px #EEF2FF",
                zIndex: 1,
              }}>
                {index + 1}
              </div>

              {/* Phase card */}
              <div style={{
                flex: 1, background: "white", borderRadius: "12px",
                padding: "20px 24px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                border: "1px solid #F3F4F6",
              }}>
                <h2 style={{
                  fontSize: "17px", fontWeight: 700,
                  color: "#4F46E5", marginBottom: "12px",
                }}>
                  {phase.phase}
                </h2>
                <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
                  {phase.steps.map((step, i) => (
                    <li key={i} style={{
                      display: "flex", alignItems: "flex-start",
                      gap: "10px", marginBottom: "8px",
                      fontSize: "14px", color: "#374151", lineHeight: 1.5,
                    }}>
                      <span style={{ color: "#10B981", fontWeight: 700, marginTop: "1px" }}>✓</span>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div style={{
          marginTop: "48px", padding: "24px",
          background: "#EFF6FF", borderRadius: "12px",
          border: "1px solid #BFDBFE", textAlign: "center",
        }}>
          <h3 style={{ fontSize: "17px", fontWeight: 700, color: "#1E40AF", marginBottom: "8px" }}>
            Ready to start working on your goals?
          </h3>
          <p style={{ color: "#3B82F6", fontSize: "14px", marginBottom: "16px" }}>
            Create your first goal on the dashboard and track your progress step by step.
          </p>
          <a href="/dashboard" style={{
            display: "inline-block", background: "#2563EB", color: "white",
            padding: "12px 24px", borderRadius: "8px", fontWeight: 600,
            textDecoration: "none", fontSize: "15px",
          }}>
            Go to Dashboard →
          </a>
        </div>
      </div>
    </div>
  );
}
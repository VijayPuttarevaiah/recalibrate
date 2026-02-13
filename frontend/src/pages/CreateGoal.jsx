import React, { useState } from "react";

const CreateGoal = () => {
  const [form, setForm] = useState({
    goal: "",
    startDate: "",
    endDate: "",
    note: "",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("Create Goal Payload:", form);
  };

  return (
    <div className="Container">
      {/* Page Header */}
      <div style={{ marginBottom: "20px" }}>
        <h1>Create Goal</h1>
        <p style={{ color: "var(--Muted)", marginTop: "4px" }}>
          Clearly define what you want to achieve and when.
        </p>
      </div>

      <div className="Panel">
        <form className="Form" onSubmit={handleSubmit}>
          {/* Goal */}
          <div className="Field">
            <label className="FieldLabel">Goal</label>
            <textarea
              className="Input"
              name="goal"
              rows="3"
              placeholder="Describe your goal in one or two clear sentences"
              value={form.goal}
              onChange={handleChange}
              required
              style={{ resize: "vertical" }}
            />
          </div>

          {/* Dates */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "12px",
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
              />
            </div>
          </div>

          {/* Note */}
          <div className="Field">
            <label className="FieldLabel">Note</label>
            <textarea
              className="Input"
              name="note"
              rows="3"
              placeholder="Optional context, constraints, or motivation"
              value={form.note}
              onChange={handleChange}
              style={{ resize: "vertical" }}
            />
          </div>

          {/* Action */}
          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginTop: "12px",
            }}
          >
            <button className="Button" type="submit">
              Create Goal
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateGoal;

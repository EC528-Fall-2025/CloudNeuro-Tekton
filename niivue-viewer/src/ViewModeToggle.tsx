import React from "react";

export type Mode = "neurological" | "radiological";

type ViewModeToggleProps = {
  mode: Mode;
  onChange: (m: Mode) => void;
};

export default function ViewModeToggle({ mode, onChange }: ViewModeToggleProps) {
  return (
    <div
      style={{
        display: "inline-flex",
        border: "1px solid #4a5568",
        borderRadius: "6px",
        overflow: "hidden",
        fontSize: "14px",
        lineHeight: 1.2,
        fontFamily:
          "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      <button
        onClick={() => onChange("neurological")}
        style={{
          backgroundColor:
            mode === "neurological" ? "#2563eb" : "#1f2937",
          color: "#ffffff",
          padding: "8px 12px",
          borderRight: "1px solid #4a5568",
          cursor: "pointer",
          fontWeight: 500,
        }}
      >
        Neurological
      </button>

      <button
        onClick={() => onChange("radiological")}
        style={{
          backgroundColor:
            mode === "radiological" ? "#2563eb" : "#1f2937",
          color: "#ffffff",
          padding: "8px 12px",
          cursor: "pointer",
          fontWeight: 500,
        }}
      >
        Radiological
      </button>
    </div>
  );
}

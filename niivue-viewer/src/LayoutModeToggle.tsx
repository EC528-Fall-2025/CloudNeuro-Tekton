import React from "react";

export type LayoutMode =
  | "multi"
  | "multi+3d"
  | "axial"
  | "coronal"
  | "sagittal"
  | "render3d";

type LayoutModeToggleProps = {
  mode: LayoutMode;
  onChange: (m: LayoutMode) => void;
};

export default function LayoutModeToggle({ mode, onChange }: LayoutModeToggleProps) {
  // tiny helper so we don't repeat styles
  const btnStyle = (active: boolean, extraRightBorder = true): React.CSSProperties => ({
    backgroundColor: active ? "#3a3f46" : "transparent",
    color: "#fff",
    padding: "10px 14px",
    cursor: "pointer",
    fontWeight: 500,
    borderRight: extraRightBorder ? "1px solid #4a5568" : "none",
    whiteSpace: "nowrap",
    lineHeight: 1.2,
    textAlign: "center",
  });

  return (
    <div
      style={{
        display: "inline-flex",
        border: "1px solid #4a5568",
        borderRadius: "8px",
        overflow: "hidden",
        fontSize: "14px",
        fontFamily:
          "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        backgroundColor: "#1f242b", // dark bar background
      }}
    >
      <button
        style={btnStyle(mode === "multi")}
        onClick={() => onChange("multi")}
      >
        A+C+S
      </button>

      <button
        style={btnStyle(mode === "multi+3d")}
        onClick={() => onChange("multi+3d")}
      >
        A+C+S+3D
      </button>

      <button
        style={btnStyle(mode === "axial")}
        onClick={() => onChange("axial")}
      >
        Axial
      </button>

      <button
        style={btnStyle(mode === "coronal")}
        onClick={() => onChange("coronal")}
      >
        Coronal
      </button>

      <button
        style={btnStyle(mode === "sagittal")}
        onClick={() => onChange("sagittal")}
      >
        Sagittal
      </button>

      <button
        style={btnStyle(mode === "render3d", false)}
        onClick={() => onChange("render3d")}
      >
        3D<br />render
      </button>
    </div>
  );
}

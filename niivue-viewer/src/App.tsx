import React, { useRef, useState } from "react";
import NiiVueViewer, { type NiiVueViewerHandle } from "./NiiVueViewer";
import { SLICE_TYPE } from "@niivue/niivue";
import ViewModeToggle, {type Mode} from "./ViewModeToggle";
import LayoutModeToggle, {type LayoutMode} from "./LayoutModeToggle";

export default function App() {
  const viewerRef = useRef<NiiVueViewerHandle>(null);

  // Neurological vs Radiological
  const [mode, setMode] = useState<Mode>("neurological");
  
  // Layout mode (multiplanar vs axial vs 3D, etc.)
  const [layoutMode, setLayoutMode] = useState<LayoutMode>("multi");

  const onPick = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      await viewerRef.current?.loadFile(f);
    }
    // allow re-selecting the same file later
    e.currentTarget.value = "";
  };

  // when the user clicks Neurological / Radiological
  const handleModeChange = (newMode: "neurological" | "radiological") => {
    setMode(newMode);
    // radiological = true means flip L/R
    const isRadiological = newMode === "radiological";
    viewerRef.current?.setRadiological(isRadiological);
  };

  return (
    <>
      <div className="toolbar">
        <label className="btn" style={{ cursor: "pointer" }}>
          Open file
          <input
            style={{ display: "none" }}
            type="file"
            onChange={onPick}
            accept=".nii,.nii.gz"
          />
        </label>

        <button
          onClick={() =>
            viewerRef.current?.setSliceType(SLICE_TYPE.MULTIPLANAR)
          }
        >
          Multiplanar
        </button>

        <button
          onClick={() => viewerRef.current?.setSliceType(SLICE_TYPE.RENDER)}
        >
          3D Render
        </button>

        <ViewModeToggle mode={mode} onChange={handleModeChange} />

        <span style={{ opacity: 0.7, marginLeft: "auto" }}>
          Supports drag-drop and paste (Ctrl/Cmd-V)
        </span>
      </div>

      <div className="viewer-shell">
        {/* DPR is capped at 2 to avoid giant canvases on 4k/retina displays */}
        <NiiVueViewer ref={viewerRef} maxDevicePixelRatio={2} />
      </div>
    </>
  );
}

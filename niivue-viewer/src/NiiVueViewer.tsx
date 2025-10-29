import React, {
  useEffect, useRef, forwardRef, useImperativeHandle,
} from "react";
import { Niivue, SLICE_TYPE, type NVConfigOptions } from "@niivue/niivue";

export type NiiVueViewerHandle = {
  loadFile: (file: File) => Promise<void>;
  setSliceType: (sliceType: number) => void;
  setRadiological: (isRadiological: boolean) => void;
  setMultiplanarShowRender: (show: boolean) => void;
};

type Props = {
  className?: string;
  maxDevicePixelRatio?: number; // default 2
  alwaysShowRender?: boolean;
};

const NiiVueViewer = forwardRef<NiiVueViewerHandle, Props>(function NiiVueViewer(
  { className, maxDevicePixelRatio = 2, alwaysShowRender = false }, ref
) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef    = useRef<HTMLCanvasElement>(null);
  const nvRef        = useRef<Niivue | null>(null);

  // 1) Create & attach NiiVue once
  useEffect(() => {
    const nv = new Niivue({
      isResizeCanvas: false,
      isColorbar: true,
      dragAndDropEnabled: true,
    } as Partial<NVConfigOptions>);
    nvRef.current = nv;

    (async () => {
      if ((nv as any).attachToCanvas) {
        await (nv as any).attachToCanvas(canvasRef.current!);
      } else {
        (nv as any).attachToCanvas?.(canvasRef.current!);
      }
      // default slice layout
      nv.setSliceType(SLICE_TYPE.MULTIPLANAR);

      // default orientation convention: let's start neurological (LEFT=LEFT)
      // In Niivue this usually means isRadiologicalConvention = false
      (nv as any).opts.isRadiologicalConvention = false;

      if (alwaysShowRender) {
        (nv as any).opts.multiplanarShowRender =
          (nv as any).SHOW_RENDER?.ALWAYS ?? 2;
      }

      nv.drawScene();
    })();

    return () => {
      nvRef.current?.cleanup?.();
      nvRef.current = null;
    };
  }, [alwaysShowRender]);

  // 2) Canvas sizing watcher (unchanged)
  useEffect(() => {
    const parent = containerRef.current!;
    const canvas = canvasRef.current!;
    const nv     = nvRef.current!;
    const ro = new ResizeObserver(() => {
      const rect = parent.getBoundingClientRect();
      const dpr  = Math.min(window.devicePixelRatio || 1, maxDevicePixelRatio);
      canvas.style.width  = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      const pxW = Math.max(1, Math.round(rect.width  * dpr));
      const pxH = Math.max(1, Math.round(rect.height * dpr));
      if (canvas.width !== pxW || canvas.height !== pxH) {
        canvas.width  = pxW;
        canvas.height = pxH;
      }
      nv.drawScene();
    });
    ro.observe(parent);
    return () => ro.disconnect();
  }, [maxDevicePixelRatio]);

  // 3) Clipboard paste (unchanged)
  useEffect(() => {
    const host = containerRef.current!;
    const onPaste = async (ev: ClipboardEvent) => {
      const nv = nvRef.current!;
      if (!ev.clipboardData) return;
      if (ev.clipboardData.files && ev.clipboardData.files.length > 0) {
        ev.preventDefault();
        await nv.loadFromFile(ev.clipboardData.files[0]);
        nv.drawScene();
        return;
      }
      const text = ev.clipboardData.getData("text/plain");
      if (
        text &&
        /^https?:\/\/\S+\.(nii(\.gz)?|nrrd|mgh|mgz|mhd|mif)$/i.test(
          text.trim()
        )
      ) {
        ev.preventDefault();
        await nv.loadVolumes([{ url: text.trim() }]);
        nv.drawScene();
      }
    };
    host.addEventListener("paste", onPaste as any);
    return () => host.removeEventListener("paste", onPaste as any);
  }, []);

  // 4) Expose functions to parent (UPDATED)
  useImperativeHandle(ref, () => ({
    loadUrl: async (url: string) => {
      const nv = nvRef.current!;
      await nv.loadVolumes([
        { url, name: url.split("/").pop() || "image.nii.gz" },
      ]);
      nv.drawScene();
    },
    loadFile: async (file: File) => {
      const nv = nvRef.current!;
      await nv.loadFromFile(file);
      nv.drawScene();
    },
    setSliceType: (slice) => {
      nvRef.current?.setSliceType(slice);
      nvRef.current?.drawScene();
    },
    setRadiological: (isRadiological: boolean) => {
      const nv = nvRef.current!;
      // flip orientation convention
      (nv as any).opts.isRadiologicalConvention = isRadiological;
      nv.drawScene();
    },
    setMultiplanarShowRender: (show: boolean) => {
      const nv = nvRef.current!;
      // flip orientation convention
      (nv as any).opts.multiplanarShowRender = show ? 2 : 0;
      nv.drawScene();
    },
  }));

  return (
    <div
      ref={containerRef}
      className={`viewer ${className || ""}`}
      tabIndex={0}
      title="Drop, paste (Ctrl/Cmd-V), or use the Open button to load a file"
    >
      <canvas ref={canvasRef} />
      <div className="paste-hint">
        Tip: click here then paste a .nii/.nii.gz (works best in Chrome)
      </div>
    </div>
  );
});

export default NiiVueViewer;

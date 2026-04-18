import React, { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { GridPattern } from "./components/ui/grid-pattern";
import {
  PromptInput,
  PromptInputTextarea,
  PromptInputActions,
  PromptInputAction,
} from "./components/ui/prompt-input";
import { Button } from "./components/ui/button";
import { ArrowUp, Paperclip, Square, X } from "lucide-react";
import { cn } from "./lib/utils";

/* ── Skeleton "analysis" placeholder ─────────────── */
const skeletonBars = [
  { width: "80%", height: "22px", delay: 0 },
  { width: "95%", height: "22px", delay: 0.08 },
  { width: "60%", height: "22px", delay: 0.16 },
  { width: "72%", height: "22px", delay: 0.24 },
];

function SkeletonAnalysis() {
  return (
    <motion.div
      key="skeleton"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex flex-col items-center gap-4 w-full max-w-md"
    >
      {/* Small label above the bars */}
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15, duration: 0.3 }}
        className="text-xs font-medium tracking-widest uppercase text-gray-400"
      >
        Preparing analysis…
      </motion.span>

      {skeletonBars.map((bar, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, scaleX: 0.7 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{
            delay: bar.delay,
            duration: 0.4,
            ease: [0.22, 1, 0.36, 1],
          }}
          style={{ width: bar.width, height: bar.height }}
          className="rounded-full bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 animate-shimmer origin-left"
        />
      ))}
    </motion.div>
  );
}

/* ── Prompt input (receives lifted state via props) ─ */
function PromptInputWithActions({
  input,
  setInput,
  isLoading,
  setIsLoading,
}) {
  const [files, setFiles] = useState([]);
  const uploadInputRef = useRef(null);

  const handleSubmit = () => {
    if (input.trim() || files.length > 0) {
      setIsLoading(true);
      setTimeout(() => {
        setIsLoading(false);
        setInput("");
        setFiles([]);
      }, 2000);
    }
  };

  const handleFileChange = (event) => {
    if (event.target.files) {
      const newFiles = Array.from(event.target.files);
      setFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const handleRemoveFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    if (uploadInputRef?.current) {
      uploadInputRef.current.value = "";
    }
  };

  return (
    <PromptInput
      value={input}
      onValueChange={setInput}
      isLoading={isLoading}
      onSubmit={handleSubmit}
      className="w-full max-w-[620px] shadow-lg"
    >
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 pb-2">
          {files.map((file, index) => (
            <div
              key={index}
              className="bg-gray-100 flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700"
            >
              <Paperclip className="h-4 w-4" />
              <span className="max-w-[120px] truncate">{file.name}</span>
              <button
                onClick={() => handleRemoveFile(index)}
                className="hover:bg-gray-200 rounded-full p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <PromptInputTextarea placeholder="Ask me anything..." />

      <PromptInputActions className="flex items-center justify-between gap-2 pt-2">
        <PromptInputAction tooltip="Attach files">
          <label
            htmlFor="file-upload"
            className="hover:bg-gray-100 flex h-8 w-8 cursor-pointer items-center justify-center rounded-2xl transition-colors"
          >
            <input
              type="file"
              multiple
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
              ref={uploadInputRef}
            />
            <Paperclip className="text-gray-500 h-5 w-5" />
          </label>
        </PromptInputAction>

        <PromptInputAction
          tooltip={isLoading ? "Stop generation" : "Send message"}
        >
          <Button
            variant="default"
            size="icon"
            className="h-8 w-8 rounded-full"
            onClick={handleSubmit}
          >
            {isLoading ? (
              <Square className="h-4 w-4 fill-current" />
            ) : (
              <ArrowUp className="h-4 w-4" />
            )}
          </Button>
        </PromptInputAction>
      </PromptInputActions>
    </PromptInput>
  );
}

/* ── App ─────────────────────────────────────────── */
function App() {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const showWelcome = !isLoading;

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center relative overflow-hidden">
      <GridPattern
        squares={[
          [4, 4],
          [5, 1],
          [8, 2],
          [5, 3],
          [5, 5],
          [10, 10],
          [12, 15],
          [15, 10],
          [10, 15],
        ]}
        className={cn(
          "[mask-image:radial-gradient(800px_circle_at_center,white,transparent)]",
          "inset-x-0 inset-y-[-30%] h-[200%] skew-y-12"
        )}
      />

      {/* ─ Main Content ─ */}
      <main className="relative z-10 w-full flex flex-col items-center px-4 max-w-4xl">

        {/* ─ Crossfade zone: welcome ↔ skeleton ─ */}
        <div className="mb-12 min-h-[140px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {showWelcome ? (
              <motion.div
                key="welcome"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="text-center"
              >
                <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl mb-6 bg-clip-text text-transparent bg-gradient-to-br from-gray-900 via-gray-800 to-gray-500">
                  Crisis Intelligence
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                  Real-time verification &amp; risk analysis engine. <br />
                  Ask a question or submit a claim to begin analysis.
                </p>
              </motion.div>
            ) : (
              <SkeletonAnalysis />
            )}
          </AnimatePresence>
        </div>

        <div className="w-full flex justify-center">
          <PromptInputWithActions
            input={input}
            setInput={setInput}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        </div>
      </main>
    </div>
  );
}

export default App;

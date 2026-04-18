import { cn } from "../../lib/utils";

export function CleanBackground({ children, className }) {
  return (
    <div className={cn("min-h-screen w-full bg-gray-50 relative", className)}>
      {/* Grid pattern */}
      <div
        className="absolute inset-0 -z-10"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(71,85,105,0.08) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(71,85,105,0.08) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
        }}
      />
      {/* Soft purple radial glow */}
      <div
        className="absolute inset-0 -z-10"
        style={{
          background: "radial-gradient(circle 800px at 80% 200px, rgba(139,92,246,0.06), transparent 70%)",
        }}
      />
      {/* Content */}
      {children}
    </div>
  );
}
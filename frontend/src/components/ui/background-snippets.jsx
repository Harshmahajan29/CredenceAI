import { cn } from "../../lib/utils";

export function BackgroundGrid({ className }) {
  return (
    <div className={cn("fixed inset-0 -z-10 overflow-hidden", className)} style={{ background: "#050508" }}>
      {/* Grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255,255,255,0.5) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255,255,255,0.5) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
        }}
      />
      {/* Fading mask on grid */}
      <div
        className="absolute inset-0"
        style={{
          background: "radial-gradient(ellipse 80% 60% at 50% 0%, transparent 40%, #050508 100%)",
        }}
      />
      {/* Animated orbs */}
      <div className="animate-orb-1 absolute -top-[200px] -left-[100px] h-[600px] w-[600px] rounded-full bg-violet-600/[0.07] blur-[120px]" />
      <div className="animate-orb-2 absolute -bottom-[100px] -right-[100px] h-[500px] w-[500px] rounded-full bg-cyan-500/[0.05] blur-[120px]" />
      <div className="animate-orb-2 absolute top-[40%] left-[60%] h-[300px] w-[300px] rounded-full bg-fuchsia-500/[0.03] blur-[100px]" />
      {/* Noise texture overlay */}
      <div className="absolute inset-0 opacity-[0.015]" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
      }} />
    </div>
  );
}

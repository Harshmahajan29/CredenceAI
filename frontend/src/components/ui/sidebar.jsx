// import React from "react";
// import { cn } from "../../lib/utils";
// import {
//   ShieldCheck,
//   Radio,
//   Network,
//   BarChart3,
//   Eye,
//   Share2,
//   AlertTriangle,
//   History,
//   TrendingDown,
//   Landmark,
//   Activity,
//   FileText,
//   Settings,
//   PanelLeftClose,
//   PanelLeftOpen,
//   User,
//   Zap,
// } from "lucide-react";

// const menuSections = [
//   {
//     title: "Core Analysis",
//     items: [
//       { icon: ShieldCheck, label: "Verify Claim", id: "verify" },
//       { icon: Radio, label: "Live Feed", id: "live-feed", badge: "LIVE" },
//       { icon: Network, label: "Evidence Graph", id: "evidence-graph" },
//       { icon: BarChart3, label: "Truth Probability", id: "truth-prob" },
//     ],
//   },
//   {
//     title: "Intelligence",
//     items: [
//       { icon: Eye, label: "Source Behavior", id: "source-behavior" },
//       { icon: Share2, label: "Propagation", id: "propagation" },
//       { icon: AlertTriangle, label: "Conflict Detection", id: "conflict", badge: "3" },
//       { icon: History, label: "Historical", id: "historical" },
//     ],
//   },
//   {
//     title: "Financial Risk",
//     items: [
//       { icon: TrendingDown, label: "Risk Dashboard", id: "risk-dashboard" },
//       { icon: Landmark, label: "Market Impact", id: "market-impact" },
//       { icon: Activity, label: "Sentiment", id: "sentiment" },
//     ],
//   },
//   {
//     title: "System",
//     items: [
//       { icon: FileText, label: "API Logs", id: "api-logs" },
//       { icon: Settings, label: "Settings", id: "settings" },
//     ],
//   },
// ];

// export function Sidebar({ collapsed, onToggle, activeItem, onItemClick }) {
//   return (
//     <aside
//       className={cn(
//         "fixed left-0 top-0 bottom-0 z-40 flex flex-col bg-white border-r border-gray-200 transition-all duration-300",
//         collapsed ? "w-[60px]" : "w-[240px]"
//       )}
//     >
//       {/* ─ Logo ─ */}
//       <div className={cn(
//         "relative flex items-center gap-2.5 border-b border-gray-200 transition-all duration-300",
//         collapsed ? "px-0 justify-center py-4" : "px-4 py-4"
//       )}>
//         <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gray-900 shadow-sm">
//           <Zap className="h-4 w-4 text-white" />
//         </div>
//         <div className={cn(
//           "overflow-hidden transition-all duration-300",
//           collapsed ? "w-0 opacity-0" : "w-auto opacity-100"
//         )}>
//           <h1 className="text-[13px] font-semibold text-gray-900 whitespace-nowrap leading-none tracking-tight">
//             CredenceAI
//           </h1>
//         </div>
//       </div>

//       {/* ─ Nav ─ */}
//       <nav className="relative flex-1 overflow-y-auto overflow-x-hidden py-3 space-y-4">
//         {menuSections.map((section) => (
//           <div key={section.title}>
//             {/* Section label */}
//             <div className={cn(
//               "mb-1 transition-all duration-300",
//               collapsed ? "flex justify-center px-0" : "px-4"
//             )}>
//               {collapsed ? (
//                 <div className="h-px w-4 bg-gray-200 rounded-full" />
//               ) : (
//                 <span className="text-[10px] font-semibold uppercase tracking-[0.05em] text-gray-400">
//                   {section.title}
//                 </span>
//               )}
//             </div>

//             <div className="space-y-px px-2">
//               {section.items.map((item) => {
//                 const Icon = item.icon;
//                 const isActive = activeItem === item.id;
//                 return (
//                   <button
//                     key={item.id}
//                     onClick={() => onItemClick?.(item.id)}
//                     title={collapsed ? item.label : undefined}
//                     className={cn(
//                       "group relative flex w-full items-center rounded-md transition-all duration-150 cursor-pointer",
//                       collapsed ? "justify-center px-0 py-2.5 mx-auto" : "gap-2.5 px-2.5 py-1.5",
//                       isActive
//                         ? "bg-gray-100 text-gray-900 font-medium"
//                         : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
//                     )}
//                   >
//                     <div className="relative flex-shrink-0">
//                       <Icon className={cn(
//                         "h-4 w-4 transition-colors duration-150",
//                         isActive ? "text-gray-900" : "text-gray-400 group-hover:text-gray-600"
//                       )} strokeWidth={1.5} />
//                     </div>

//                     <span className={cn(
//                       "text-[13px] truncate transition-all duration-300",
//                       collapsed ? "w-0 opacity-0 absolute" : "w-auto opacity-100"
//                     )}>
//                       {item.label}
//                     </span>

//                     {!collapsed && item.badge && (
//                       <span className={cn(
//                         "ml-auto flex-shrink-0 text-[10px] font-medium rounded-full px-1.5 py-0.5 tracking-wide",
//                         item.badge === "LIVE"
//                           ? "bg-red-50 text-red-600"
//                           : "bg-gray-100 text-gray-500"
//                       )}>
//                         {item.badge}
//                       </span>
//                     )}
//                   </button>
//                 );
//               })}
//             </div>
//           </div>
//         ))}
//       </nav>

//       {/* ─ Footer ─ */}
//       <div className="relative border-t border-gray-200 p-2">
//         <div className={cn(
//           "flex items-center rounded-lg hover:bg-gray-50 transition-colors cursor-pointer",
//           collapsed ? "justify-center p-2" : "gap-2.5 px-2.5 py-1.5"
//         )}>
//           <div className="h-7 w-7 flex-shrink-0 rounded-full bg-gray-200 border border-gray-300 flex items-center justify-center">
//             <User className="h-3.5 w-3.5 text-gray-500" strokeWidth={1.5} />
//           </div>
//           <div className={cn(
//             "overflow-hidden transition-all duration-300",
//             collapsed ? "w-0 opacity-0 absolute" : "w-auto opacity-100"
//           )}>
//             <p className="text-[12px] font-medium text-gray-700 whitespace-nowrap">Operator</p>
//           </div>
//         </div>
//       </div>

//       {/* ─ Collapse ─ */}
//       <button
//         onClick={onToggle}
//         className="absolute -right-3 top-16 z-50 flex h-6 w-6 items-center justify-center rounded-full bg-white border border-gray-200 text-gray-500 hover:text-gray-900 hover:bg-gray-50 transition-all shadow-sm cursor-pointer"
//       >
//         {collapsed ? (
//           <PanelLeftOpen className="h-3 w-3" />
//         ) : (
//           <PanelLeftClose className="h-3 w-3" />
//         )}
//       </button>
//     </aside>
//   );
// }

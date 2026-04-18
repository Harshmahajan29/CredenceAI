// import React from "react";
// import { cn } from "../../lib/utils";
// import {
//   Search,
//   ShieldCheck,
//   Radio,
//   Network,
//   Eye,
//   TrendingDown,
//   Bell,
//   User,
// } from "lucide-react";

// const navItems = [
//   { icon: ShieldCheck, label: "Verify", id: "verify" },
//   { icon: Radio, label: "Live Feed", id: "live-feed" },
//   { icon: Network, label: "Evidence", id: "evidence-graph" },
//   { icon: Eye, label: "Sources", id: "source-behavior" },
//   { icon: TrendingDown, label: "Risk", id: "risk-dashboard" },
// ];

// export function Header({ activeItem, onItemClick, sidebarCollapsed }) {
//   return (
//     <header
//       className={cn(
//         "fixed top-0 right-0 z-30 transition-all duration-300 bg-white border-b border-gray-200",
//         sidebarCollapsed ? "left-[60px]" : "left-[240px]"
//       )}
//     >
//       <div className="h-[48px] flex items-center justify-between px-4">
//         {/* Left: nav */}
//         <nav className="hidden md:flex items-center gap-1">
//           {navItems.map((item) => {
//             const Icon = item.icon;
//             const isActive = activeItem === item.id;
//             return (
//               <button
//                 key={item.id}
//                 onClick={() => onItemClick?.(item.id)}
//                 className={cn(
//                   "relative flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[13px] transition-all duration-150 cursor-pointer",
//                   isActive
//                     ? "bg-gray-100 text-gray-900 font-medium"
//                     : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
//                 )}
//               >
//                 <Icon className="h-3.5 w-3.5" strokeWidth={1.5} />
//                 <span>{item.label}</span>
//               </button>
//             );
//           })}
//         </nav>

//         {/* Right */}
//         <div className="flex items-center gap-3 ml-auto">
//           {/* Search */}
//           <div className="hidden sm:flex items-center gap-1.5 rounded-md bg-gray-50 border border-gray-200 px-2 py-1 w-[200px]">
//             <Search className="h-3.5 w-3.5 text-gray-400" />
//             <input
//               type="text"
//               placeholder="Search..."
//               className="w-full bg-transparent text-[13px] text-gray-900 placeholder:text-gray-400 outline-none"
//             />
//             <kbd className="hidden lg:flex items-center text-[10px] text-gray-400 font-sans border border-gray-200 rounded px-1 bg-white">
//               ⌘K
//             </kbd>
//           </div>

//           <div className="h-4 w-px bg-gray-200 mx-1" />

//           {/* Bell */}
//           <button className="relative flex items-center justify-center h-8 w-8 rounded-md text-gray-500 hover:text-gray-900 hover:bg-gray-50 transition-colors cursor-pointer">
//             <Bell className="h-4 w-4" strokeWidth={1.5} />
//           </button>

//           {/* Avatar */}
//           <div className="h-7 w-7 rounded-full bg-gray-200 border border-gray-300 flex items-center justify-center cursor-pointer hover:bg-gray-300 transition-colors">
//             <User className="h-3.5 w-3.5 text-gray-500" strokeWidth={1.5} />
//           </div>
//         </div>
//       </div>
//     </header>
//   );
// }

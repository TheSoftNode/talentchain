"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { TopNavigation } from "@/components/layout/top-navigation";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const pathname = usePathname();

  // Handle responsive behavior
  useEffect(() => {
    const checkScreenSize = () => {
      const desktop = window.innerWidth >= 1024;
      setIsDesktop(desktop);

      // If switching to desktop, ensure sidebar is "closed" for mobile state
      // but it will be visible via CSS on desktop
      if (desktop) {
        setSidebarOpen(false);
      }
    };

    // Initial check
    checkScreenSize();

    // Add resize listener
    window.addEventListener('resize', checkScreenSize);

    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  // Close mobile sidebar on route change
  useEffect(() => {
    if (!isDesktop) {
      setSidebarOpen(false);
    }
  }, [pathname, isDesktop]);

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarCollapse = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={handleSidebarToggle}
        onClose={handleSidebarClose}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={handleSidebarCollapse}
        isDesktop={isDesktop}
      />

      {/* Main content area - Dynamic margin based on sidebar state and screen size */}
      <div
        className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${isDesktop
          ? (sidebarCollapsed ? 'lg:ml-20' : 'lg:ml-[280px]')
          : 'ml-0'
          }`}
      >
        {/* Top navigation */}
        <TopNavigation
          onSidebarToggle={handleSidebarToggle}
          sidebarCollapsed={sidebarCollapsed}
        />

        {/* Page content */}
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
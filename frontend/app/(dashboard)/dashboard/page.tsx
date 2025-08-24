"use client";

import { motion } from "framer-motion";
import {
  DashboardOverview,
  SkillTokensWidget,
  JobPoolsWidget,
  ReputationWidget,
  TransactionHistoryWidget
} from "@/components/dashboard";
import { GovernanceWidget } from "@/components/dashboard/governance-widget";

import { useAuth } from "@/hooks/useAuth";
import { WifiOff } from "lucide-react";

// Dashboard page component with proper sidebar layout
export default function DashboardPage() {
  const { isConnected } = useAuth();

  return (
    <div className="w-full">
      {/* Dashboard Container - No centering, works with sidebar */}
      <div className="">

        {/* Dashboard Overview Section - Full Width */}
        <div className="mb-8 lg:mb-12">
          <DashboardOverview />
        </div>

        {/* Main Dashboard Content - Only show when connected */}
        {isConnected ? (
          <div className="space-y-8 lg:space-y-12">

            {/* Primary Dashboard Grid - Skills and Jobs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="grid grid-cols-1 xl:grid-cols-12 gap-6 lg:gap-8"
            >
              {/* Skills Management - Takes up more space */}
              <div className="xl:col-span-8 space-y-6">
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                  <SkillTokensWidget />
                </div>
              </div>

              {/* Job Opportunities - Sidebar style */}
              <div className="xl:col-span-4 space-y-6">
                <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                  <JobPoolsWidget />
                </div>
              </div>
            </motion.div>

            {/* Secondary Dashboard Grid - Reputation and Transactions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8"
            >

              {/* AI Reputation Tracking */}
              <div className="bg-white dark:bg-slate-800 h-fit rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <ReputationWidget />
              </div>

              {/* Blockchain Transaction History */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <TransactionHistoryWidget />
              </div>

            </motion.div>

            {/* Tertiary Dashboard Grid - Governance */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="grid grid-cols-1 gap-6 lg:gap-8"
            >

              {/* Governance Participation - Full Width */}
              <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <GovernanceWidget walletAddress={isConnected ? "mock-address" : undefined} />
              </div>

            </motion.div>



          </div>
        ) : (
          /* Connection Prompt - Centered when not connected */
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex items-center justify-center min-h-[60vh]"
          >
            <div className="text-center max-w-md mx-auto">
              <div className="w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center">
                <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center">
                  <WifiOff className="w-8 h-8 text-slate-400" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
                Connect Your Wallet
              </h2>
              <p className="text-slate-600 dark:text-slate-400 mb-6 leading-relaxed">
                Connect your Hedera wallet to access your TalentChain Pro dashboard and start building your professional reputation.
              </p>
              <div className="inline-flex items-center gap-2 text-sm text-hedera-600 dark:text-hedera-400">
                <div className="w-2 h-2 bg-hedera-500 rounded-full animate-pulse"></div>
                Waiting for wallet connection...
              </div>
            </div>
          </motion.div>
        )}

      </div>
    </div>
  );
}


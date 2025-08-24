"use client";

import { motion } from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VideoModal } from "@/components/ui/video-modal";
import { useVideoModal } from "@/hooks/useVideoModal";
import { VIDEO_CONFIG } from "@/lib/config/video";

export function CTASection() {
  const { isOpen, videoUrl, title, description, openModal, closeModal } = useVideoModal();

  const handleWatchDemo = () => {
    openModal(
      VIDEO_CONFIG.CTA_VIDEO_URL,
      VIDEO_CONFIG.DEMO_VIDEO_TITLE,
      VIDEO_CONFIG.DEMO_VIDEO_DESCRIPTION
    );
  };

  return (
    <>
      <section className="relative py-8 sm:py-12 lg:py-16 bg-gradient-to-b from-slate-50/80 to-white dark:from-slate-950/80 dark:to-slate-900 overflow-hidden">
        {/* Consistent Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-hedera-50/20 via-pink-50/10 to-slate-50/20 dark:from-hedera-900/20 dark:via-pink-900/10 dark:to-slate-900/20">
          <div className="absolute inset-0 bg-gradient-to-t from-white/10 to-transparent dark:from-black/20 dark:to-transparent"></div>
        </div>

        {/* Subtle Background Pattern */}
        <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]">
          <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="cta-pattern" x="0" y="0" width="80" height="80" patternUnits="userSpaceOnUse">
                <path d="M40 10L65 25v30L40 70L15 55V25L40 10z" stroke="currentColor" strokeWidth="0.3" fill="none" className="text-hedera-400" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#cta-pattern)" />
          </svg>
        </div>

        <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              viewport={{ once: true }}
              className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-hedera-50 dark:bg-hedera-950/50 border border-hedera-200/30 dark:border-hedera-800/30 mb-4 sm:mb-6"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-hedera-600 dark:text-hedera-400"
              >
                <g fill="currentColor">
                  <path d="M12 2L15.5 4V8L12 10L8.5 8V4L12 2Z" opacity="0.9" />
                  <path d="M6 8L9.5 10V14L6 16L2.5 14V10L6 8Z" opacity="0.7" />
                  <path d="M18 8L21.5 10V14L18 16L14.5 14V10L18 8Z" opacity="0.7" />
                  <path d="M12 14L15.5 16V20L12 22L8.5 20V16L12 14Z" opacity="0.9" />
                  <path d="M12 10L12 14" stroke="currentColor" strokeWidth="1.5" opacity="0.6" />
                  <path d="M9.5 12L14.5 12" stroke="currentColor" strokeWidth="1.5" opacity="0.6" />
                </g>
              </svg>
              <span className="text-sm font-medium text-hedera-700 dark:text-hedera-300">
                Transform Your Career
              </span>
            </motion.div>

            {/* Main Content */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: true }}
            >
              <h2 className="text-xl sm:text-2xl lg:text-3xl xl:text-4xl font-black tracking-tight leading-tight mb-3 sm:mb-4 flex flex-col gap-1">
                <span className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 dark:from-white dark:via-slate-100 dark:to-white bg-clip-text text-transparent">
                  Ready to Build Your
                </span>
                <span className="relative text-hedera-600 dark:text-hedera-400 font-extrabold">
                  <span className="relative z-10">Digital Identity</span>
                  <span className="absolute -inset-1 bg-hedera-100/20 dark:bg-hedera-900/20 blur-sm rounded-lg -z-10"></span>
                </span>
                <span className="text-pink-600 dark:text-pink-400 font-medium text-base sm:text-lg lg:text-xl tracking-[0.1em] px-2 py-0.5 border-l-2 border-pink-500 bg-pink-50/30 dark:bg-pink-950/20 backdrop-blur-sm self-center">
                  ON-CHAIN?
                </span>
              </h2>

              <p className="text-sm sm:text-base lg:text-lg text-slate-600 dark:text-slate-300 max-w-xl lg:max-w-2xl mx-auto mb-4 sm:mb-6 leading-relaxed">
                Join thousands of professionals who are already building their future with verifiable skills, AI-powered matching, and blockchain-secured reputation.
              </p>

              {/* CTA Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                viewport={{ once: true }}
                className="flex flex-col sm:flex-row gap-3 justify-center items-center"
              >
                <Button
                  size="lg"
                  className="group relative bg-hedera-600 hover:bg-hedera-700 text-white shadow-lg shadow-hedera-500/25 hover:shadow-hedera-600/30 transition-all duration-300 font-semibold px-5 py-2.5 sm:px-6 sm:py-3 text-sm sm:text-base min-w-[180px]"
                >
                  <span className="relative z-10 flex items-center">
                    Get Started Free
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-200" />
                  </span>
                  <div className="absolute inset-0 bg-hedera-500 rounded-md blur opacity-0 group-hover:opacity-20 transition-opacity duration-300" />
                </Button>

                <Button
                  variant="outline"
                  size="lg"
                  onClick={handleWatchDemo}
                  className="group border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:border-hedera-300 dark:hover:border-hedera-600 hover:text-hedera-600 dark:hover:text-hedera-400 backdrop-blur-sm px-5 py-2.5 sm:px-6 sm:py-3 text-sm sm:text-base font-medium min-w-[180px] transition-all duration-300"
                >
                  <Play className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform duration-200" />
                  Watch Demo
                </Button>
              </motion.div>

              {/* Trust Indicators */}
              <motion.div
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                transition={{ duration: 0.8, delay: 0.6 }}
                viewport={{ once: true }}
                className="mt-6 sm:mt-8 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-6 text-slate-500 dark:text-slate-400 text-xs sm:text-sm"
              >
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span>Powered by Hedera Hashgraph</span>
                </div>
                <div className="hidden sm:block w-1 h-1 bg-slate-300 dark:bg-slate-600 rounded-full"></div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-pink-400 rounded-full animate-pulse"></div>
                  <span>Zero Gas Fees</span>
                </div>
                <div className="hidden sm:block w-1 h-1 bg-slate-300 dark:bg-slate-600 rounded-full"></div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                  <span>Enterprise Ready</span>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Video Modal */}
      <VideoModal
        isOpen={isOpen}
        onClose={closeModal}
        videoUrl={videoUrl}
        title={title}
        description={description}
      />
    </>
  );
}
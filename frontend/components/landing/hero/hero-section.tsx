"use client";

import { motion } from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BlockchainBackground } from "./blockchain-background";
import { TalentDemo } from "./talent-demo";
import { VideoModal } from "@/components/ui/video-modal";
import { useVideoModal } from "@/hooks/useVideoModal";
import { VIDEO_CONFIG } from "@/lib/config/video";

export function HeroSection(): JSX.Element {
  const { isOpen, videoUrl, title, description, openModal, closeModal } = useVideoModal();

  const handleWatchDemo = () => {
    openModal(
      VIDEO_CONFIG.HERO_VIDEO_URL,
      VIDEO_CONFIG.DEMO_VIDEO_TITLE,
      VIDEO_CONFIG.DEMO_VIDEO_DESCRIPTION
    );
  };

  return (
    <>
      <section className="relative min-h-screen flex items-center py-20 sm:py-12 md:py-16 lg:py-20 overflow-hidden">
        {/* Sophisticated Background */}
        <BlockchainBackground />

        <div className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="grid lg:grid-cols-2 gap-8 sm:gap-12 lg:gap-16 items-center max-w-7xl mx-auto">
            {/* Left Content */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="text-center lg:text-left space-y-4 sm:space-y-6"
            >
              {/* Badge */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="inline-flex items-center space-x-2 px-3 py-1.5 sm:px-4 sm:py-2 rounded-full bg-hedera-50 dark:bg-hedera-950/50 border border-hedera-200/30 dark:border-hedera-800/30"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="text-hedera-600 dark:text-hedera-400"
                >
                  {/* Talent Chain Symbol - Interconnected hexagons */}
                  <g fill="currentColor">
                    {/* Top Hexagon */}
                    <path d="M12 2L15.5 4V8L12 10L8.5 8V4L12 2Z" opacity="0.9" />
                    {/* Middle Left Hexagon */}
                    <path d="M6 8L9.5 10V14L6 16L2.5 14V10L6 8Z" opacity="0.7" />
                    {/* Middle Right Hexagon */}
                    <path d="M18 8L21.5 10V14L18 16L14.5 14V10L18 8Z" opacity="0.7" />
                    {/* Bottom Hexagon */}
                    <path d="M12 14L15.5 16V20L12 22L8.5 20V16L12 14Z" opacity="0.9" />

                    {/* Connection Lines */}
                    <path d="M12 10L12 14" stroke="currentColor" strokeWidth="1.5" opacity="0.6" />
                    <path d="M9.5 12L14.5 12" stroke="currentColor" strokeWidth="1.5" opacity="0.6" />
                  </g>
                </svg>
                <span className="text-xs sm:text-sm font-medium text-hedera-700 dark:text-hedera-300">
                  Powered by Hedera Blockchain
                </span>
              </motion.div>

              {/* Main Heading */}
              <motion.h1
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.3 }}
                className="text-2xl flex flex-col gap-1 sm:gap-2 sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black tracking-tight leading-tight"
              >
                <span className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 dark:from-white dark:via-slate-100 dark:to-white bg-clip-text text-transparent">
                  Build Your
                </span>
                {/* <br /> */}
                <span className="relative text-hedera-600 dark:text-hedera-400 font-extrabold tracking-wide">
                  <span className="relative z-10">Talent Identity</span>
                  <span className="absolute -inset-1 bg-hedera-100/30 dark:bg-hedera-900/30 blur-sm rounded-lg -z-10"></span>
                </span>
                <span className="text-pink-600 dark:text-pink-400 font-medium text-sm sm:text-base md:text-lg tracking-[0.15em] px-2 py-0.5 sm:px-2.5 border-l-2 sm:border-l-3 border-pink-500 bg-pink-50/30 dark:bg-pink-950/20 backdrop-blur-sm self-start">
                  ON-CHAIN
                </span>
              </motion.h1>

              {/* Description */}
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.5 }}
                className="text-sm sm:text-base lg:text-lg text-slate-600 dark:text-slate-300 max-w-lg sm:max-w-xl mx-auto lg:mx-0 leading-relaxed"
              >
                Create verifiable skill soulbound tokens, connect with AI-powered talent matching,
                and build your professional reputation on the most sustainable blockchain.
              </motion.p>

              {/* CTA Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.7 }}
                className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center lg:justify-start pt-2"
              >
                <Button
                  size="lg"
                  className="group relative bg-hedera-600 hover:bg-hedera-700 text-white shadow-lg shadow-hedera-500/25 hover:shadow-hedera-600/30 transition-all duration-300 font-semibold px-4 py-2.5 sm:px-6 sm:py-3 text-sm sm:text-base"
                >
                  <span className="relative z-10 flex items-center">
                    Get Started
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform duration-200" />
                  </span>
                  <div className="absolute inset-0 bg-hedera-500 rounded-md blur opacity-0 group-hover:opacity-20 transition-opacity duration-300" />
                </Button>

                <Button
                  variant="outline"
                  size="lg"
                  onClick={handleWatchDemo}
                  className="group border-slate-300 dark:border-slate-600 hover:border-hedera-300 dark:hover:border-hedera-600 text-slate-700 dark:text-slate-300 hover:text-hedera-600 dark:hover:text-hedera-400 px-4 py-2.5 sm:px-6 sm:py-3 text-sm sm:text-base"
                >
                  <Play className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform duration-200" />
                  Watch Demo
                </Button>
              </motion.div>
            </motion.div>

            {/* Right Demo */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
              className="flex justify-center lg:justify-center"
            >
              <div className="relative">
                {/* Demo sits directly without container or floating badges */}
                <TalentDemo />

                {/* Subtle Background Glow */}
                <div className="absolute inset-0 bg-gradient-to-r from-hedera-200/8 to-pink-200/8 dark:from-hedera-800/8 dark:to-pink-800/8 rounded-full blur-3xl -z-10 scale-110" />
              </div>
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
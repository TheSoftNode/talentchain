"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Play, Pause, Volume2, VolumeX, Maximize2, Minimize2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface VideoModalProps {
    isOpen: boolean;
    onClose: () => void;
    videoUrl?: string;
    title?: string;
    description?: string;
}

export function VideoModal({
    isOpen,
    onClose,
    videoUrl = "https://www.youtube.com/embed/dQw4w9WgXcQ", // Default demo video
    title = "TalentChain Pro Demo",
    description = "See how TalentChain Pro revolutionizes professional identity and skill verification on the blockchain."
}: VideoModalProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [showControls, setShowControls] = useState(true);
    const [controlsTimeout, setControlsTimeout] = useState<NodeJS.Timeout | null>(null);

    // Handle escape key
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape" && isOpen) {
                onClose();
            }
        };

        if (isOpen) {
            document.addEventListener("keydown", handleEscape);
            document.body.style.overflow = "hidden";
        }

        return () => {
            document.removeEventListener("keydown", handleEscape);
            document.body.style.overflow = "unset";
        };
    }, [isOpen, onClose]);

    // Auto-hide controls
    useEffect(() => {
        if (controlsTimeout) {
            clearTimeout(controlsTimeout);
        }

        if (showControls) {
            const timeout = setTimeout(() => {
                setShowControls(false);
            }, 3000);
            setControlsTimeout(timeout);
        }

        return () => {
            if (controlsTimeout) {
                clearTimeout(controlsTimeout);
            }
        };
    }, [showControls]);

    const handleMouseMove = () => {
        setShowControls(true);
    };

    const handleMouseLeave = () => {
        setShowControls(false);
    };

    const togglePlayPause = () => {
        setIsPlaying(!isPlaying);
    };

    const toggleMute = () => {
        setIsMuted(!isMuted);
    };

    const toggleFullscreen = () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            setIsFullscreen(true);
        } else {
            document.exitFullscreen();
            setIsFullscreen(false);
        }
    };

    const resetVideo = () => {
        setCurrentTime(0);
        setIsPlaying(false);
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-3 md:p-4 bg-black/80 backdrop-blur-sm"
                onClick={onClose}
            >
                {/* Modal Container - More compact sizing */}
                <motion.div
                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.9, opacity: 0, y: 20 }}
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    className="relative w-full max-w-4xl lg:max-w-5xl xl:max-w-6xl bg-white dark:bg-slate-900 rounded-xl shadow-2xl overflow-hidden"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header - More compact */}
                    <div className="flex items-center justify-between p-3 sm:p-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-900">
                        <div className="flex-1 min-w-0">
                            <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white truncate">
                                {title}
                            </h2>
                            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1 truncate">
                                {description}
                            </p>
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onClose}
                            className="h-7 w-7 p-0 hover:bg-slate-100 dark:hover:bg-slate-800 ml-2 flex-shrink-0"
                        >
                            <X className="h-3 w-3" />
                        </Button>
                    </div>

                    {/* Video Container - Responsive aspect ratio */}
                    <div
                        className="relative bg-black group"
                        onMouseMove={handleMouseMove}
                        onMouseLeave={handleMouseLeave}
                    >
                        {/* Video Player - More compact aspect ratio */}
                        <div className="relative aspect-[16/10] w-full">
                            <iframe
                                src={videoUrl}
                                title={title}
                                className="w-full h-full"
                                frameBorder="0"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                            />

                            {/* Custom Controls Overlay - More compact */}
                            <AnimatePresence>
                                {showControls && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 20 }}
                                        className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-2 sm:p-3"
                                    >
                                        {/* Progress Bar */}
                                        <div className="w-full bg-slate-600/30 rounded-full h-1 mb-2 sm:mb-3 cursor-pointer">
                                            <div
                                                className="bg-hedera-500 h-1 rounded-full transition-all duration-200"
                                                style={{ width: `${(currentTime / duration) * 100}%` }}
                                            />
                                        </div>

                                        {/* Control Buttons - More compact */}
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-1 sm:space-x-2">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={togglePlayPause}
                                                    className="h-6 w-6 sm:h-7 sm:w-7 p-0 text-white hover:bg-white/20"
                                                >
                                                    {isPlaying ? (
                                                        <Pause className="h-3 w-3 sm:h-4 sm:w-4" />
                                                    ) : (
                                                        <Play className="h-3 w-3 sm:h-4 sm:w-4" />
                                                    )}
                                                </Button>

                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={toggleMute}
                                                    className="h-6 w-6 sm:h-7 sm:w-7 p-0 text-white hover:bg-white/20"
                                                >
                                                    {isMuted ? (
                                                        <VolumeX className="h-3 w-3 sm:h-4 sm:w-4" />
                                                    ) : (
                                                        <Volume2 className="h-3 w-3 sm:h-4 sm:w-4" />
                                                    )}
                                                </Button>

                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={resetVideo}
                                                    className="h-6 w-6 sm:h-7 sm:w-7 p-0 text-white hover:bg-white/20"
                                                >
                                                    <RotateCcw className="h-3 w-3 sm:h-4 sm:w-4" />
                                                </Button>

                                                <span className="text-white text-xs sm:text-sm ml-1 sm:ml-2">
                                                    {formatTime(currentTime)} / {formatTime(duration)}
                                                </span>
                                            </div>

                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={toggleFullscreen}
                                                className="h-6 w-6 sm:h-7 sm:w-7 p-0 text-white hover:bg-white/20"
                                            >
                                                {isFullscreen ? (
                                                    <Minimize2 className="h-3 w-3 sm:h-4 sm:w-4" />
                                                ) : (
                                                    <Maximize2 className="h-3 w-3 sm:h-4 sm:w-4" />
                                                )}
                                            </Button>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            {/* Play Button Overlay (when not playing) - More compact */}
                            {!isPlaying && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="absolute inset-0 flex items-center justify-center"
                                >
                                    <Button
                                        size="lg"
                                        onClick={togglePlayPause}
                                        className="h-12 w-12 sm:h-14 sm:w-14 rounded-full bg-hedera-600 hover:bg-hedera-700 text-white shadow-2xl hover:scale-110 transition-all duration-300"
                                    >
                                        <Play className="h-6 w-6 sm:h-7 sm:w-7 ml-0.5" />
                                    </Button>
                                </motion.div>
                            )}
                        </div>
                    </div>

                    {/* Footer - More compact */}
                    <div className="p-3 sm:p-4 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-900 border-t border-slate-200 dark:border-slate-700">
                        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-4">
                            <div className="flex items-center space-x-3 sm:space-x-4 text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                                <div className="flex items-center space-x-1 sm:space-x-2">
                                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-hedera-500 rounded-full animate-pulse"></div>
                                    <span>Live Demo</span>
                                </div>
                                <div className="flex items-center space-x-1 sm:space-x-2">
                                    <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-pink-500 rounded-full animate-pulse"></div>
                                    <span>Interactive</span>
                                </div>
                            </div>

                            <Button
                                variant="outline"
                                onClick={onClose}
                                size="sm"
                                className="border-hedera-300 text-hedera-700 hover:bg-hedera-50 dark:border-hedera-600 dark:text-hedera-300 dark:hover:bg-hedera-900/50 text-xs sm:text-sm px-3 py-1.5 sm:px-4 sm:py-2"
                            >
                                Close Demo
                            </Button>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}

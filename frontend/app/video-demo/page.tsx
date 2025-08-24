"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { VideoModal } from "@/components/ui/video-modal";
import { useVideoModal } from "@/hooks/useVideoModal";
import { VIDEO_CONFIG } from "@/lib/config/video";
import { Play, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function VideoDemoPage() {
    const { isOpen, videoUrl, title, description, openModal, closeModal } = useVideoModal();

    const handleWatchDemo = () => {
        openModal(
            VIDEO_CONFIG.DEMO_VIDEO_URL,
            VIDEO_CONFIG.DEMO_VIDEO_TITLE,
            VIDEO_CONFIG.DEMO_VIDEO_DESCRIPTION
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-background via-background to-hedera-50/50 dark:to-hedera-950/50">
            {/* Header */}
            <div className="container mx-auto px-4 py-6">
                <Link
                    href="/"
                    className="inline-flex items-center text-hedera-600 hover:text-hedera-700 dark:text-hedera-400 dark:hover:text-hedera-300 mb-8"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Home
                </Link>

                <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
                    Video Modal Demo
                </h1>
                <p className="text-slate-600 dark:text-slate-400 mb-8">
                    Test the responsive video modal component that fits perfectly within the viewport.
                </p>
            </div>

            {/* Demo Section */}
            <div className="container mx-auto px-4 py-8">
                <div className="max-w-2xl mx-auto text-center space-y-6">
                    <div className="bg-white dark:bg-slate-800 rounded-xl p-8 border border-slate-200 dark:border-slate-700 shadow-lg">
                        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
                            Test the Video Modal
                        </h2>
                        <p className="text-slate-600 dark:text-slate-400 mb-6">
                            Click the button below to open the video modal. The modal is designed to be compact and fit within the viewport without being cut off by the navbar or footer.
                        </p>

                        <Button
                            size="lg"
                            onClick={handleWatchDemo}
                            className="bg-hedera-600 hover:bg-hedera-700 text-white"
                        >
                            <Play className="w-4 h-4 mr-2" />
                            Watch Demo Video
                        </Button>
                    </div>

                    <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-6 border border-slate-200 dark:border-slate-700">
                        <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-3">
                            Features
                        </h3>
                        <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-2 text-left">
                            <li>• Responsive design that fits any screen size</li>
                            <li>• Compact layout to avoid viewport overflow</li>
                            <li>• Professional controls with auto-hide functionality</li>
                            <li>• Keyboard shortcuts (ESC to close)</li>
                            <li>• Fullscreen support</li>
                            <li>• Dark mode compatible</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Video Modal */}
            <VideoModal
                isOpen={isOpen}
                onClose={closeModal}
                videoUrl={videoUrl}
                title={title}
                description={description}
            />
        </div>
    );
}


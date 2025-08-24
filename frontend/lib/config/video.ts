// Video configuration for demo videos
export const VIDEO_CONFIG = {
    // Main demo video URL - replace with your actual demo video
    DEMO_VIDEO_URL: "https://www.youtube.com/embed/dQw4w9WgXcQ",

    // Video titles and descriptions
    DEMO_VIDEO_TITLE: "TalentChain Pro Demo",
    DEMO_VIDEO_DESCRIPTION: "See how TalentChain Pro revolutionizes professional identity and skill verification on the blockchain.",

    // Alternative video URLs for different sections
    HERO_VIDEO_URL: "https://www.youtube.com/embed/dQw4w9WgXcQ",
    CTA_VIDEO_URL: "https://www.youtube.com/embed/dQw4w9WgXcQ",

    // Video settings
    AUTOPLAY: false,
    MUTED: true,
    CONTROLS: true,
    FULLSCREEN: true,

    // Modal settings for better viewport fit
    MODAL_MAX_WIDTH: "max-w-4xl lg:max-w-5xl xl:max-w-6xl",
    MODAL_PADDING: "p-2 sm:p-3 md:p-4",
    VIDEO_ASPECT_RATIO: "aspect-[16/10]",
} as const;

// Helper function to get video URL with parameters
export function getVideoUrl(url: string, options?: {
    autoplay?: boolean;
    muted?: boolean;
    controls?: boolean;
    fullscreen?: boolean;
}) {
    const params = new URLSearchParams();

    if (options?.autoplay) params.append('autoplay', '1');
    if (options?.muted) params.append('muted', '1');
    if (!options?.controls) params.append('controls', '0');
    if (options?.fullscreen) params.append('allowfullscreen', '1');

    const queryString = params.toString();
    return queryString ? `${url}?${queryString}` : url;
}

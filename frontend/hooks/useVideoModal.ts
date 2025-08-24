import { useState, useCallback } from 'react';

interface UseVideoModalReturn {
  isOpen: boolean;
  videoUrl: string;
  title: string;
  description: string;
  openModal: (url?: string, title?: string, description?: string) => void;
  closeModal: () => void;
}

export function useVideoModal(): UseVideoModalReturn {
  const [isOpen, setIsOpen] = useState(false);
  const [videoUrl, setVideoUrl] = useState('https://www.youtube.com/embed/dQw4w9WgXcQ');
  const [title, setTitle] = useState('TalentChain Pro Demo');
  const [description, setDescription] = useState('See how TalentChain Pro revolutionizes professional identity and skill verification on the blockchain.');

  const openModal = useCallback((url?: string, title?: string, description?: string) => {
    if (url) setVideoUrl(url);
    if (title) setTitle(title);
    if (description) setDescription(description);
    setIsOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    setIsOpen(false);
  }, []);

  return {
    isOpen,
    videoUrl,
    title,
    description,
    openModal,
    closeModal,
  };
}


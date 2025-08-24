"use client";

import { motion } from "framer-motion";
import { Bell, CheckCircle, AlertCircle, Info, Clock, Search, Check, Trash2, Archive } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { WalletConnectionPrompt } from "@/components/dashboard/wallet-connection-prompt";

// Mock notification data - replace with real data from your backend
const notifications = [
    {
        id: 1,
        type: 'success',
        title: 'Skill Token Created',
        message: 'Your Blockchain Development skill token has been successfully minted on the Hedera network. The transaction has been confirmed and your skill is now visible to potential employers.',
        time: '2 minutes ago',
        read: false,
        category: 'skills'
    },
    {
        id: 2,
        type: 'info',
        title: 'New Job Opportunity',
        message: 'A new Smart Contract Developer position at DeFiCorp matches your skills perfectly. The role offers competitive compensation and remote work options.',
        time: '1 hour ago',
        read: false,
        category: 'jobs'
    },
    {
        id: 3,
        type: 'warning',
        title: 'Reputation Update',
        message: 'Your AI reputation score has been updated based on recent work submissions. Your score increased by 15 points due to high-quality code reviews.',
        time: '3 hours ago',
        read: true,
        category: 'reputation'
    },
    {
        id: 4,
        type: 'success',
        title: 'Application Submitted',
        message: 'Your application for Senior Developer at TechCorp has been successfully submitted. The hiring team will review your profile and get back to you within 48 hours.',
        time: '1 day ago',
        read: true,
        category: 'applications'
    },
    {
        id: 5,
        type: 'info',
        title: 'Network Update',
        message: 'Hedera network maintenance scheduled for tomorrow at 2 AM UTC. Services will be temporarily unavailable for approximately 30 minutes.',
        time: '2 days ago',
        read: true,
        category: 'system'
    },
    {
        id: 6,
        type: 'success',
        title: 'Skill Level Increased',
        message: 'Congratulations! Your React Development skill level has increased from 7 to 8. This improvement is based on recent project submissions and peer reviews.',
        time: '3 days ago',
        read: true,
        category: 'skills'
    }
];

const categories = [
    { id: 'all', name: 'All', count: notifications.length },
    { id: 'skills', name: 'Skills', count: notifications.filter(n => n.category === 'skills').length },
    { id: 'jobs', name: 'Jobs', count: notifications.filter(n => n.category === 'jobs').length },
    { id: 'reputation', name: 'Reputation', count: notifications.filter(n => n.category === 'reputation').length },
    { id: 'applications', name: 'Applications', count: notifications.filter(n => n.category === 'applications').length },
    { id: 'system', name: 'System', count: notifications.filter(n => n.category === 'system').length }
];

export default function NotificationsPage() {
    const { isConnected } = useAuth();
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedNotifications, setSelectedNotifications] = useState<number[]>([]);

    if (!isConnected) {
        return (
            <WalletConnectionPrompt
                title="Connect to View Notifications"
                description="Connect your Hedera wallet to view your notifications and stay updated on your professional activities."
            />
        );
    }

    const filteredNotifications = notifications.filter(notification => {
        const matchesCategory = selectedCategory === 'all' || notification.category === selectedCategory;
        const matchesSearch = notification.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            notification.message.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesCategory && matchesSearch;
    });

    const unreadCount = filteredNotifications.filter(n => !n.read).length;

    const getNotificationIcon = (type: string) => {
        switch (type) {
            case 'success':
                return <CheckCircle className="w-5 h-5 text-emerald-500" />;
            case 'warning':
                return <AlertCircle className="w-5 h-5 text-yellow-500" />;
            case 'info':
                return <Info className="w-5 h-5 text-blue-500" />;
            default:
                return <Info className="w-5 h-5 text-slate-500" />;
        }
    };

    const getCategoryColor = (category: string) => {
        switch (category) {
            case 'skills':
                return 'bg-hedera-100 text-hedera-700 dark:bg-hedera-900/30 dark:text-hedera-300';
            case 'jobs':
                return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300';
            case 'reputation':
                return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300';
            case 'applications':
                return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300';
            case 'system':
                return 'bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-300';
            default:
                return 'bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-300';
        }
    };

    const toggleNotificationSelection = (id: number) => {
        setSelectedNotifications(prev =>
            prev.includes(id)
                ? prev.filter(n => n !== id)
                : [...prev, id]
        );
    };

    const markAsRead = (ids: number[]) => {
        // In a real app, this would call your API
        console.log('Marking as read:', ids);
    };

    const deleteNotifications = (ids: number[]) => {
        // In a real app, this would call your API
        console.log('Deleting notifications:', ids);
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
            <div className="">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="mb-8"
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 bg-gradient-to-br from-hedera-500 to-pink-500 rounded-lg flex items-center justify-center">
                            <Bell className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                                Notifications
                            </h1>
                            <p className="text-slate-600 dark:text-slate-400">
                                Stay updated with your TalentChain Pro activity
                            </p>
                        </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 rounded-lg p-4">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-hedera-100 dark:bg-hedera-900/30 rounded-lg flex items-center justify-center">
                                    <Bell className="w-4 h-4 text-hedera-600 dark:text-hedera-400" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                                        {notifications.length}
                                    </p>
                                    <p className="text-sm text-slate-600 dark:text-slate-400">Total</p>
                                </div>
                            </div>
                        </div>
                        <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 rounded-lg p-4">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg flex items-center justify-center">
                                    <AlertCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                                        {unreadCount}
                                    </p>
                                    <p className="text-sm text-slate-600 dark:text-slate-400">Unread</p>
                                </div>
                            </div>
                        </div>
                        <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 rounded-lg p-4">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center">
                                    <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                                        {notifications.filter(n => n.read).length}
                                    </p>
                                    <p className="text-sm text-slate-600 dark:text-slate-400">Read</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Filters and Actions */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                    className="mb-6"
                >
                    <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                        <CardContent className="p-6">
                            <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
                                {/* Search and Filters */}
                                <div className="flex flex-col sm:flex-row gap-4 flex-1">
                                    <div className="relative flex-1 max-w-md">
                                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <Input
                                            type="text"
                                            placeholder="Search notifications..."
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            className="pl-10"
                                        />
                                    </div>

                                    {/* Category Filter */}
                                    <div className="flex flex-wrap gap-2">
                                        {categories.map((category) => (
                                            <Button
                                                key={category.id}
                                                variant={selectedCategory === category.id ? "default" : "outline"}
                                                size="sm"
                                                onClick={() => setSelectedCategory(category.id)}
                                                className={cn(
                                                    selectedCategory === category.id
                                                        ? "bg-hedera-600 hover:bg-hedera-700"
                                                        : "hover:bg-slate-100 dark:hover:bg-slate-700"
                                                )}
                                            >
                                                {category.name}
                                                <Badge variant="secondary" className="ml-2 text-xs">
                                                    {category.count}
                                                </Badge>
                                            </Button>
                                        ))}
                                    </div>
                                </div>

                                {/* Bulk Actions */}
                                {selectedNotifications.length > 0 && (
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => markAsRead(selectedNotifications)}
                                            className="flex items-center gap-2"
                                        >
                                            <Check className="w-4 h-4" />
                                            Mark as read
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => deleteNotifications(selectedNotifications)}
                                            className="flex items-center gap-2 text-red-600 hover:text-red-700"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                            Delete
                                        </Button>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Notifications List */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="space-y-4"
                >
                    {filteredNotifications.length === 0 ? (
                        <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                            <CardContent className="p-12 text-center">
                                <Bell className="w-16 h-16 mx-auto text-slate-400 mb-4" />
                                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                                    No notifications found
                                </h3>
                                <p className="text-slate-600 dark:text-slate-400">
                                    {searchTerm || selectedCategory !== 'all'
                                        ? 'Try adjusting your search or filters'
                                        : 'You\'re all caught up! Check back later for new updates.'
                                    }
                                </p>
                            </CardContent>
                        </Card>
                    ) : (
                        filteredNotifications.map((notification, index) => (
                            <motion.div
                                key={notification.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.1 * index }}
                            >
                                <Card className={cn(
                                    "bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 transition-all duration-200 hover:shadow-md hover:border-hedera-300/50 dark:hover:border-hedera-700/50",
                                    !notification.read && "ring-2 ring-hedera-200 dark:ring-hedera-800 bg-hedera-50/30 dark:bg-hedera-950/20"
                                )}>
                                    <CardContent className="p-6">
                                        <div className="flex items-start gap-4">
                                            {/* Checkbox */}
                                            <input
                                                type="checkbox"
                                                checked={selectedNotifications.includes(notification.id)}
                                                onChange={() => toggleNotificationSelection(notification.id)}
                                                className="mt-1 w-4 h-4 text-hedera-600 border-slate-300 rounded focus:ring-hedera-500 focus:ring-2"
                                            />

                                            {/* Icon */}
                                            <div className="flex-shrink-0 mt-1">
                                                {getNotificationIcon(notification.type)}
                                            </div>

                                            {/* Content */}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-start justify-between gap-4 mb-2">
                                                    <div className="flex-1">
                                                        <h3 className={cn(
                                                            "text-lg font-semibold mb-1",
                                                            !notification.read
                                                                ? "text-slate-900 dark:text-white"
                                                                : "text-slate-700 dark:text-slate-300"
                                                        )}>
                                                            {notification.title}
                                                        </h3>
                                                        <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                                                            {notification.message}
                                                        </p>
                                                    </div>

                                                    {/* Unread indicator */}
                                                    {!notification.read && (
                                                        <div className="w-3 h-3 bg-hedera-500 rounded-full flex-shrink-0 mt-2" />
                                                    )}
                                                </div>

                                                {/* Footer */}
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3">
                                                        <Badge
                                                            variant="secondary"
                                                            className={cn("text-xs", getCategoryColor(notification.category))}
                                                        >
                                                            {notification.category}
                                                        </Badge>
                                                        <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-500">
                                                            <Clock className="w-3 h-3" />
                                                            {notification.time}
                                                        </div>
                                                    </div>

                                                    {/* Actions */}
                                                    <div className="flex items-center gap-2">
                                                        {!notification.read && (
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() => markAsRead([notification.id])}
                                                                className="text-xs text-hedera-600 hover:text-hedera-700"
                                                            >
                                                                Mark as read
                                                            </Button>
                                                        )}
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="text-xs text-slate-500 hover:text-slate-700"
                                                        >
                                                            <Archive className="w-3 h-3 mr-1" />
                                                            Archive
                                                        </Button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        ))
                    )}
                </motion.div>
            </div>
        </div>
    );
}

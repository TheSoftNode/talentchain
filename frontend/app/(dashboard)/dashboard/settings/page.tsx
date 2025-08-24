"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
    User,
    Shield,
    Bell,
    Globe,
    Wallet,
    Key,
    Trash2,
    Save,
    Edit3,
    Eye,
    EyeOff,
    CheckCircle,
    AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";
import { WalletConnectionPrompt } from "@/components/dashboard/wallet-connection-prompt";

export default function SettingsPage() {
    const { isConnected, user, disconnectWallet } = useAuth();
    const [activeTab, setActiveTab] = useState("profile");
    const [isEditing, setIsEditing] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);

    // Form state
    const [profileData, setProfileData] = useState({
        firstName: user?.profile?.name?.split(' ')[0] || "",
        lastName: user?.profile?.name?.split(' ').slice(1).join(' ') || "",
        email: user?.profile?.email || "",
        bio: user?.profile?.experience || "",
        location: "",
        website: "",
        company: user?.profile?.companyName || "",
        title: user?.profile?.industry || ""
    });

    const [notificationSettings, setNotificationSettings] = useState({
        emailNotifications: true,
        pushNotifications: true,
        jobAlerts: true,
        skillUpdates: true,
        reputationChanges: true,
        weeklyDigest: false
    });

    const [privacySettings, setPrivacySettings] = useState({
        profileVisibility: "public",
        skillVisibility: "public",
        workHistoryVisibility: "connections",
        allowSkillEndorsements: true,
        allowCompanyReviews: true,
        showOnlineStatus: true
    });

    const [walletSettings, setWalletSettings] = useState({
        autoConnect: true,
        rememberConnections: true,
        showBalances: true,
        confirmTransactions: true
    });

    const tabs = [
        { id: "profile", name: "Profile", icon: User },
        { id: "notifications", name: "Notifications", icon: Bell },
        { id: "privacy", name: "Privacy", icon: Shield },
        { id: "wallet", name: "Wallet", icon: Wallet },
        { id: "security", name: "Security", icon: Key }
    ];

    const handleSave = async () => {
        setIsSaving(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        setIsSaving(false);
        setSaveSuccess(true);
        setIsEditing(false);

        // Hide success message after 3 seconds
        setTimeout(() => setSaveSuccess(false), 3000);
    };

    const handleDisconnect = async () => {
        await disconnectWallet();
    };

    if (!isConnected) {
        return (
            <WalletConnectionPrompt
                title="Connect to Access Settings"
                description="Connect your Hedera wallet to manage your account settings and preferences."
            />
        );
    }

    return (
        <div className="w-full">
            <div className="">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="mb-8"
                >
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                        <div>
                            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                                Account Settings
                            </h1>
                            <p className="text-slate-600 dark:text-slate-400 mt-2">
                                Manage your profile, preferences, and account security
                            </p>
                        </div>
                        <div className="flex items-center gap-3">
                            {isEditing && (
                                <>
                                    <Button variant="outline" onClick={() => setIsEditing(false)}>
                                        Cancel
                                    </Button>
                                    <Button onClick={handleSave} disabled={isSaving}>
                                        <Save className="w-4 h-4 mr-2" />
                                        {isSaving ? 'Saving...' : 'Save Changes'}
                                    </Button>
                                </>
                            )}
                            {!isEditing && (
                                <Button onClick={() => setIsEditing(true)}>
                                    <Edit3 className="w-4 h-4 mr-2" />
                                    Edit Profile
                                </Button>
                            )}
                        </div>
                    </div>

                    {/* Success Message */}
                    {saveSuccess && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mt-4 p-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg"
                        >
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-5 h-5 text-green-500" />
                                <span className="text-green-700 dark:text-green-300">
                                    Settings saved successfully!
                                </span>
                            </div>
                        </motion.div>
                    )}
                </motion.div>

                {/* Settings Tabs */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.1 }}
                    className="mb-8"
                >
                    <div className="flex flex-wrap gap-2 border-b border-slate-200 dark:border-slate-700">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${activeTab === tab.id
                                    ? 'bg-hedera-100 dark:bg-hedera-900/50 text-hedera-700 dark:text-hedera-300 border-b-2 border-hedera-500'
                                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                                    }`}
                            >
                                <tab.icon className="w-4 h-4" />
                                {tab.name}
                            </button>
                        ))}
                    </div>
                </motion.div>

                {/* Tab Content */}
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                >
                    {/* Profile Tab */}
                    {activeTab === "profile" && (
                        <div className="space-y-6">
                            <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <User className="w-5 h-5" />
                                        Personal Information
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <Label htmlFor="firstName">First Name</Label>
                                            <Input
                                                id="firstName"
                                                value={profileData.firstName}
                                                onChange={(e) => setProfileData({ ...profileData, firstName: e.target.value })}
                                                disabled={!isEditing}
                                            />
                                        </div>
                                        <div>
                                            <Label htmlFor="lastName">Last Name</Label>
                                            <Input
                                                id="lastName"
                                                value={profileData.lastName}
                                                onChange={(e) => setProfileData({ ...profileData, lastName: e.target.value })}
                                                disabled={!isEditing}
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <Label htmlFor="email">Email</Label>
                                        <Input
                                            id="email"
                                            type="email"
                                            value={profileData.email}
                                            onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                                            disabled={!isEditing}
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="bio">Bio</Label>
                                        <Textarea
                                            id="bio"
                                            value={profileData.bio}
                                            onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
                                            disabled={!isEditing}
                                            rows={3}
                                            placeholder="Tell us about yourself..."
                                        />
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Globe className="w-5 h-5" />
                                        Professional Information
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <Label htmlFor="company">Company</Label>
                                            <Input
                                                id="company"
                                                value={profileData.company}
                                                onChange={(e) => setProfileData({ ...profileData, company: e.target.value })}
                                                disabled={!isEditing}
                                            />
                                        </div>
                                        <div>
                                            <Label htmlFor="title">Job Title</Label>
                                            <Input
                                                id="title"
                                                value={profileData.title}
                                                onChange={(e) => setProfileData({ ...profileData, title: e.target.value })}
                                                disabled={!isEditing}
                                            />
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <Label htmlFor="location">Location</Label>
                                            <Input
                                                id="location"
                                                value={profileData.location}
                                                onChange={(e) => setProfileData({ ...profileData, location: e.target.value })}
                                                disabled={!isEditing}
                                            />
                                        </div>
                                        <div>
                                            <Label htmlFor="website">Website</Label>
                                            <Input
                                                id="website"
                                                value={profileData.website}
                                                onChange={(e) => setProfileData({ ...profileData, website: e.target.value })}
                                                disabled={!isEditing}
                                                placeholder="https://..."
                                            />
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {/* Notifications Tab */}
                    {activeTab === "notifications" && (
                        <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Bell className="w-5 h-5" />
                                    Notification Preferences
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                {Object.entries(notificationSettings).map(([key, value]) => (
                                    <div key={key} className="flex items-center justify-between">
                                        <div>
                                            <Label className="text-sm font-medium">
                                                {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                                            </Label>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                Receive notifications for {key.toLowerCase().replace(/([A-Z])/g, ' $1').toLowerCase()}
                                            </p>
                                        </div>
                                        <Switch
                                            checked={value}
                                            onCheckedChange={(checked) =>
                                                setNotificationSettings({ ...notificationSettings, [key]: checked })
                                            }
                                        />
                                    </div>
                                ))}
                            </CardContent>
                        </Card>
                    )}

                    {/* Privacy Tab */}
                    {activeTab === "privacy" && (
                        <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Shield className="w-5 h-5" />
                                    Privacy Settings
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div>
                                    <Label>Profile Visibility</Label>
                                    <Select
                                        value={privacySettings.profileVisibility}
                                        onValueChange={(value) => setPrivacySettings({ ...privacySettings, profileVisibility: value })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="public">Public</SelectItem>
                                            <SelectItem value="connections">Connections Only</SelectItem>
                                            <SelectItem value="private">Private</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div>
                                    <Label>Skill Visibility</Label>
                                    <Select
                                        value={privacySettings.skillVisibility}
                                        onValueChange={(value) => setPrivacySettings({ ...privacySettings, skillVisibility: value })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="public">Public</SelectItem>
                                            <SelectItem value="connections">Connections Only</SelectItem>
                                            <SelectItem value="private">Private</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <Separator />

                                {Object.entries(privacySettings).slice(3).map(([key, value]) => (
                                    <div key={key} className="flex items-center justify-between">
                                        <div>
                                            <Label className="text-sm font-medium">
                                                {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                                            </Label>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                Allow others to {key.toLowerCase().replace(/([A-Z])/g, ' $1').toLowerCase()}
                                            </p>
                                        </div>
                                        <Switch
                                            checked={typeof value === 'boolean' ? value : false}
                                            onCheckedChange={(checked) =>
                                                setPrivacySettings({ ...privacySettings, [key]: checked })
                                            }
                                        />
                                    </div>
                                ))}
                            </CardContent>
                        </Card>
                    )}

                    {/* Wallet Tab */}
                    {activeTab === "wallet" && (
                        <div className="space-y-6">
                            <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Wallet className="w-5 h-5" />
                                        Wallet Settings
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    {Object.entries(walletSettings).map(([key, value]) => (
                                        <div key={key} className="flex items-center justify-between">
                                            <div>
                                                <Label className="text-sm font-medium">
                                                    {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                                                </Label>
                                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                                    {key === 'autoConnect' && 'Automatically connect wallet on page load'}
                                                    {key === 'rememberConnections' && 'Remember wallet connections across sessions'}
                                                    {key === 'showBalances' && 'Display wallet balances in the interface'}
                                                    {key === 'confirmTransactions' && 'Require confirmation for all transactions'}
                                                </p>
                                            </div>
                                            <Switch
                                                checked={value}
                                                onCheckedChange={(checked) =>
                                                    setWalletSettings({ ...walletSettings, [key]: checked })
                                                }
                                            />
                                        </div>
                                    ))}
                                </CardContent>
                            </Card>

                            <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <AlertCircle className="w-5 h-5 text-orange-500" />
                                        Wallet Connection
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-sm font-medium text-slate-900 dark:text-white">
                                                Connected Wallet
                                            </p>
                                            <p className="text-sm text-slate-500 dark:text-slate-400">
                                                {user?.accountId || 'No wallet connected'}
                                            </p>
                                        </div>
                                        <Button variant="outline" onClick={handleDisconnect}>
                                            Disconnect
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {/* Security Tab */}
                    {activeTab === "security" && (
                        <div className="space-y-6">
                            <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Key className="w-5 h-5" />
                                        Security Settings
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div>
                                        <Label htmlFor="currentPassword">Current Password</Label>
                                        <div className="relative">
                                            <Input
                                                id="currentPassword"
                                                type={showPassword ? "text" : "password"}
                                                placeholder="Enter current password"
                                                disabled={!isEditing}
                                            />
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                size="sm"
                                                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                                onClick={() => setShowPassword(!showPassword)}
                                            >
                                                {showPassword ? (
                                                    <EyeOff className="w-4 h-4" />
                                                ) : (
                                                    <Eye className="w-4 h-4" />
                                                )}
                                            </Button>
                                        </div>
                                    </div>
                                    <div>
                                        <Label htmlFor="newPassword">New Password</Label>
                                        <Input
                                            id="newPassword"
                                            type="password"
                                            placeholder="Enter new password"
                                            disabled={!isEditing}
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor="confirmPassword">Confirm New Password</Label>
                                        <Input
                                            id="confirmPassword"
                                            type="password"
                                            placeholder="Confirm new password"
                                            disabled={!isEditing}
                                        />
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
                                        <Trash2 className="w-5 h-5" />
                                        Danger Zone
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-4">
                                        <div>
                                            <p className="text-sm font-medium text-slate-900 dark:text-white mb-2">
                                                Delete Account
                                            </p>
                                            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                                                Once you delete your account, there is no going back. Please be certain.
                                            </p>
                                            <Button variant="destructive" size="sm">
                                                <Trash2 className="w-4 h-4 mr-2" />
                                                Delete Account
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}
                </motion.div>
            </div>
        </div>
    );
}

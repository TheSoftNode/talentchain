"use client";

import { useState, useEffect } from "react";
import { Award, Sparkles, User, Hash, Loader2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/lib/api/client";

interface ContractSkillForm {
    recipient_address: string;  // address recipient
    category: string;           // string category  
    subcategory: string;        // string subcategory
    level: number;              // uint8 level
    expiry_date: number;        // uint64 expiryDate (0 for default)
    metadata: string;           // string metadata
    uri: string;                // string tokenURIData
}

interface ContractCreateSkillDialogProps {
    onSkillCreated?: (skillData: ContractSkillForm) => void;
    triggerButton?: React.ReactNode;
}

const skillCategories = [
    "Frontend Development",
    "Backend Development",
    "Smart Contracts",
    "UI/UX Design",
    "DevOps",
    "Data Science",
    "Mobile Development",
    "Blockchain Development",
    "Cybersecurity",
    "Project Management",
    "Quality Assurance",
    "Cloud Architecture"
];

const levelDescriptions = {
    1: "Novice - Just starting to learn",
    2: "Beginner - Basic understanding",
    3: "Developing - Some practical experience",
    4: "Competent - Can work independently",
    5: "Intermediate - Solid practical skills",
    6: "Proficient - Advanced practical skills",
    7: "Advanced - Expert level skills",
    8: "Superior - Industry expert",
    9: "Master - Thought leader",
    10: "Legendary - Pioneer in the field"
};

export function ContractCreateSkillDialog({
    onSkillCreated,
    triggerButton
}: ContractCreateSkillDialogProps) {
    const { user, isConnected } = useAuth();
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [isCreating, setIsCreating] = useState(false);
    const [formData, setFormData] = useState<ContractSkillForm>({
        recipient_address: "",
        category: "",
        subcategory: "",
        level: 1,
        expiry_date: 0, // 0 means use default expiry date
        metadata: "",
        uri: ""
    });
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Auto-populate recipient address when user connects
    useEffect(() => {
        if (user?.accountId) {
            setFormData(prev => ({ ...prev, recipient_address: user.accountId }));
        }
    }, [user?.accountId]);

    const handleCreateSkill = async () => {
        if (!isConnected || !user?.accountId) {
            alert("Please connect your wallet to create a skill token");
            return;
        }

        if (!formData.category || !formData.recipient_address) {
            alert("Please fill in all required fields");
            return;
        }

        setIsCreating(true);
        setError(null);

        try {
            // Create skill token using the API client
            const response = await apiClient.createSkillToken({
                recipient_address: formData.recipient_address,
                skill_name: formData.category,
                skill_category: formData.subcategory || formData.category,
                level: formData.level,
                description: formData.metadata,
                metadata_uri: formData.uri
            });

            if (response.success) {
                setSuccess(true);
                setFormData({
                    recipient_address: "",
                    category: "",
                    subcategory: "",
                    level: 1,
                    expiry_date: 0,
                    metadata: "",
                    uri: ""
                });

                // Call the callback to refresh the parent component
                if (onSkillCreated) {
                    onSkillCreated(response.data);
                }

                // Auto-close after success
                setTimeout(() => {
                    setIsDialogOpen(false);
                    setSuccess(false);
                }, 2000);
            } else {
                setError(response.error || "Failed to create skill token");
            }
        } catch (err) {
            console.error("Error creating skill token:", err);
            setError("Failed to create skill token. Please try again.");
        } finally {
            setIsCreating(false);
        }
    };

    const getSkillLevelColor = (level: number) => {
        if (level >= 9) return "from-purple-500 to-pink-500";
        if (level >= 7) return "from-hedera-500 to-web3-pink-500";
        if (level >= 5) return "from-blue-500 to-hedera-500";
        if (level >= 3) return "from-green-500 to-blue-500";
        return "from-gray-400 to-green-500";
    };

    return (
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
                {triggerButton || (
                    <Button className="bg-gradient-to-r from-hedera-600 to-web3-pink-600 hover:from-hedera-700 hover:to-web3-pink-700 text-white shadow-lg">
                        <Award className="w-4 h-4 mr-2" />
                        Create Skill Token
                    </Button>
                )}
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
                <DialogHeader className="space-y-3">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 bg-gradient-to-r from-hedera-500 to-web3-pink-500 rounded-lg flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <DialogTitle className="text-lg font-bold bg-gradient-to-r from-hedera-600 to-web3-pink-600 bg-clip-text text-transparent">
                                Create Skill Token
                            </DialogTitle>
                            <DialogDescription className="text-sm text-slate-600 dark:text-slate-400">
                                Mint a soulbound skill token on Hedera
                            </DialogDescription>
                        </div>
                    </div>
                </DialogHeader>

                <div className="space-y-4">{/* Reduced from space-y-6 */}
                    {/* Connection Status */}
                    <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:border-hedera-300/50 dark:hover:border-hedera-700/50">
                        <CardContent className="p-3">{/* Reduced from p-4 */}
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <User className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                                    <span className="text-sm text-slate-600 dark:text-slate-400">Recipient</span>
                                </div>
                                {isConnected ? (
                                    <div className="flex items-center gap-2">
                                        <CheckCircle className="w-4 h-4 text-green-500" />
                                        <span className="text-sm font-mono text-slate-900 dark:text-white">
                                            {user?.accountId?.slice(0, 8)}...{user?.accountId?.slice(-6)}
                                        </span>
                                    </div>
                                ) : (
                                    <Badge variant="outline" className="text-amber-600 border-amber-600">
                                        Connect Wallet
                                    </Badge>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Skill Category */}
                    <div className="space-y-1.5">{/* Reduced from space-y-2 */}
                        <Label htmlFor="category" className="text-sm font-medium text-slate-900 dark:text-white">
                            Skill Category *
                        </Label>
                        <Select
                            value={formData.category}
                            onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
                        >
                            <SelectTrigger className="h-10 border-slate-200 dark:border-slate-700 focus:border-hedera-500">
                                <SelectValue placeholder="Select your expertise area" />
                            </SelectTrigger>
                            <SelectContent>
                                {skillCategories.map((category) => (
                                    <SelectItem key={category} value={category}>
                                        {category}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Subcategory */}
                    <div className="space-y-1.5">{/* Reduced from space-y-2 */}
                        <Label htmlFor="subcategory" className="text-sm font-medium text-slate-900 dark:text-white">
                            Specific Skill *
                        </Label>
                        <Input
                            id="subcategory"
                            placeholder="e.g., React.js, Solidity Smart Contracts, Figma Design"
                            value={formData.subcategory}
                            onChange={(e) => setFormData(prev => ({ ...prev, subcategory: e.target.value }))}
                            className="h-10 border-slate-200 dark:border-slate-700 focus:border-hedera-500"
                        />
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                            Be specific about your exact skill (e.g., &quot;React.js&quot; instead of just &quot;Frontend&quot;)
                        </p>
                    </div>

                    {/* Metadata */}
                    <div className="space-y-1.5">{/* Reduced from space-y-2 */}
                        <Label htmlFor="metadata" className="text-sm font-medium text-slate-900 dark:text-white">
                            Additional Information
                        </Label>
                        <Textarea
                            id="metadata"
                            placeholder="Describe your experience, certifications, or any relevant details..."
                            value={formData.metadata}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData(prev => ({ ...prev, metadata: e.target.value }))}
                            rows={2}
                            className="border-slate-200 dark:border-slate-700 focus:border-hedera-500 resize-none"
                        />
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                            Optional: Add context about your skill background
                        </p>
                    </div>

                    {/* Skill Level */}
                    <div className="space-y-2">{/* Reduced from space-y-3 */}
                        <Label htmlFor="level" className="text-sm font-medium text-slate-900 dark:text-white">
                            Skill Level *
                        </Label>
                        <div className="space-y-2">{/* Reduced from space-y-3 */}
                            <Select
                                value={formData.level.toString()}
                                onValueChange={(value) => setFormData(prev => ({ ...prev, level: parseInt(value) }))}
                            >
                                <SelectTrigger className="h-10 border-slate-200 dark:border-slate-700 focus:border-hedera-500">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {Array.from({ length: 10 }, (_, i) => i + 1).map((level) => (
                                        <SelectItem key={level} value={level.toString()}>
                                            <div className="flex items-center gap-3">
                                                <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${getSkillLevelColor(level)}`} />
                                                <span>Level {level}</span>
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>

                            {formData.level > 0 && (
                                <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                                    <div className="flex items-center gap-2 mb-1">
                                        <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${getSkillLevelColor(formData.level)}`} />
                                        <span className="text-sm font-medium text-slate-900 dark:text-white">
                                            Level {formData.level}
                                        </span>
                                    </div>
                                    <p className="text-xs text-slate-600 dark:text-slate-400">
                                        {levelDescriptions[formData.level as keyof typeof levelDescriptions]}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Metadata URI Preview */}
                    {formData.category && (
                        <div className="space-y-1.5">{/* Reduced from space-y-2 */}
                            <Label className="text-sm font-medium text-slate-900 dark:text-white">
                                Metadata URI Preview
                            </Label>
                            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                                <div className="flex items-center gap-2">
                                    <Hash className="w-4 h-4 text-slate-500" />
                                    <span className="text-xs font-mono text-slate-600 dark:text-slate-400">
                                        ipfs://skill-{formData.category.toLowerCase().replace(/[^a-z0-9]/g, '-')}-***-level-{formData.level}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Contract Parameters Summary */}
                    {formData.category && isConnected && (
                        <Card className="border-hedera-200 dark:border-hedera-800 bg-gradient-to-r from-hedera-50/50 to-web3-pink-50/50 dark:from-hedera-950/30 dark:to-web3-pink-950/30">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-hedera-900 dark:text-hedera-100">
                                    Smart Contract Parameters
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-0 space-y-1.5">
                                <div className="grid grid-cols-2 gap-2.5 text-xs">
                                    <div>
                                        <span className="text-slate-600 dark:text-slate-400">recipient:</span>
                                        <p className="font-mono text-slate-900 dark:text-white truncate">
                                            {user?.accountId}
                                        </p>
                                    </div>
                                    <div>
                                        <span className="text-slate-600 dark:text-slate-400">category:</span>
                                        <p className="font-medium text-slate-900 dark:text-white">
                                            {formData.category}
                                        </p>
                                    </div>
                                    <div>
                                        <span className="text-slate-600 dark:text-slate-400">level:</span>
                                        <p className="font-medium text-slate-900 dark:text-white">
                                            {formData.level}
                                        </p>
                                    </div>
                                    <div>
                                        <span className="text-slate-600 dark:text-slate-400">uri:</span>
                                        <p className="font-mono text-slate-900 dark:text-white">
                                            ipfs://...
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center gap-3 pt-3">
                        <Button
                            variant="outline"
                            onClick={() => setIsDialogOpen(false)}
                            disabled={isCreating}
                            className="flex-1"
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleCreateSkill}
                            disabled={!isConnected || !formData.category || formData.level < 1 || isCreating}
                            className="flex-1 bg-gradient-to-r from-hedera-600 to-web3-pink-600 hover:from-hedera-700 hover:to-web3-pink-700 text-white"
                        >
                            {isCreating ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Minting...
                                </>
                            ) : (
                                <>
                                    <Award className="w-4 h-4 mr-2" />
                                    Create Token
                                </>
                            )}
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

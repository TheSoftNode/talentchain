"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Trophy,
  Search,
  Filter,
  ArrowUpRight,
  Star,
  Award,
  BookOpen,
  Target,
  TrendingUp,
  Plus,
  AlertCircle,
  Hash
} from "lucide-react";
import { Card, CardContent, } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/hooks/useAuth";
import { SkillTokenInfo } from "@/lib/types/wallet";
import { ContractCreateSkillDialog } from "@/components/skills/contract-create-skill-dialog";
import { UpdateSkillTokenDialog } from "@/components/skills/update-skill-token-dialog";
import { ViewSkillTokenDialog } from "@/components/skills/view-skill-token-dialog";
import { WalletConnectionPrompt } from "@/components/dashboard/wallet-connection-prompt";
import { apiClient } from "@/lib/api/client";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSkillTokens } from "@/hooks/useSkillTokens";

// Skill categories for filtering
const skillCategories = [
  "Frontend Development",
  "Backend Development",
  "Smart Contracts",
  "UI/UX Design",
  "DevOps",
  "Data Science",
  "Mobile Development",
  "Game Development",
  "Cybersecurity",
  "Project Management"
];

export default function SkillsPage() {
  const { user, isConnected } = useAuth();
  const { skillTokens, isLoading, error, refetch, createSkillToken, updateSkillLevel } = useSkillTokens();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedSkill, setSelectedSkill] = useState<SkillTokenInfo | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showUpdateDialog, setShowUpdateDialog] = useState(false);
  const [showViewDialog, setShowViewDialog] = useState(false);

  const handleSkillCreated = async (skillData: any) => {
    // Refresh the skills list after creation
    await refetch();
    setShowCreateDialog(false);
  };

  const handleSkillUpdated = async (skillData: any) => {
    // Refresh the skills list after update
    await refetch();
    setShowUpdateDialog(false);
  };

  const handleViewSkill = (skill: SkillTokenInfo) => {
    setSelectedSkill(skill);
    setShowViewDialog(true);
  };

  const handleUpdateSkill = (skill: SkillTokenInfo) => {
    setSelectedSkill(skill);
    setShowUpdateDialog(true);
  };

  // Filter skills based on search and category
  const filteredSkills = skillTokens.filter(skill => {
    const matchesSearch = skill.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (skill.description || "").toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "all" || skill.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  if (!isConnected) {
    return <WalletConnectionPrompt />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            My Skills
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            Manage your skill tokens and showcase your expertise
          </p>
        </div>
        <Button
          onClick={() => setShowCreateDialog(true)}
          className="bg-hedera-600 hover:bg-hedera-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Skill Token
        </Button>
      </motion.div>

      {/* Search and Filter */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="flex flex-col sm:flex-row gap-4"
      >
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
          <Input
            placeholder="Search skills..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {skillCategories.map((category) => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </motion.div>

      {/* Skills Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {isLoading ? (
          // Loading state
          Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
              <CardContent className="p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4 mb-4"></div>
                  <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/2 mb-2"></div>
                  <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-2/3"></div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : error ? (
          // Error state
          <div className="col-span-full text-center py-12">
            <div className="text-red-600 dark:text-red-400 mb-4">
              <AlertCircle className="w-12 h-12 mx-auto" />
            </div>
            <p className="text-slate-600 dark:text-slate-400 mb-4">{error}</p>
            <Button onClick={refetch} variant="outline">
              Try Again
            </Button>
          </div>
        ) : filteredSkills.length === 0 ? (
          // Empty state
          <div className="col-span-full text-center py-12">
            <div className="text-slate-400 dark:text-slate-500 mb-4">
              <Trophy className="w-12 h-12 mx-auto" />
            </div>
            <p className="text-slate-600 dark:text-slate-400 mb-4">
              {searchTerm || selectedCategory !== "all"
                ? "No skills match your search criteria"
                : "You haven't created any skill tokens yet"}
            </p>
            {!searchTerm && selectedCategory === "all" && (
              <Button onClick={() => setShowCreateDialog(true)} className="bg-hedera-600 hover:bg-hedera-700">
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Skill Token
              </Button>
            )}
          </div>
        ) : (
          // Skills grid
          filteredSkills.map((skill, index) => (
            <motion.div
              key={skill.tokenId}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 * index }}
            >
              <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300 h-full">
                <CardContent className="p-6 h-full flex flex-col">
                  {/* Skill Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className="p-2 bg-hedera-100 dark:bg-hedera-900/30 rounded-lg">
                        <Trophy className="w-5 h-5 text-hedera-600 dark:text-hedera-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                          {skill.category}
                        </h3>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          Token #{skill.tokenId}
                        </p>
                      </div>
                    </div>
                    <Badge className="bg-hedera-100 text-hedera-700 dark:bg-hedera-900/30 dark:text-hedera-300">
                      Level {skill.level}
                    </Badge>
                  </div>

                  {/* Skill Description */}
                  {skill.description && (
                    <p className="text-slate-600 dark:text-slate-400 text-sm mb-4 flex-1">
                      {skill.description}
                    </p>
                  )}

                  {/* Skill Level Progress */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-slate-600 dark:text-slate-400">Skill Level</span>
                      <span className="font-medium text-slate-900 dark:text-slate-100">
                        {skill.level}/10
                      </span>
                    </div>
                    <Progress value={skill.level * 10} className="h-2" />
                  </div>

                  {/* Skill Metadata */}
                  {skill.uri && (
                    <div className="mb-4 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                        <Hash className="w-4 h-4" />
                        <span className="truncate">{skill.uri}</span>
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-2 mt-auto">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewSkill(skill)}
                      className="flex-1"
                    >
                      <BookOpen className="w-4 h-4 mr-2" />
                      View
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleUpdateSkill(skill)}
                      className="flex-1"
                    >
                      <Target className="w-4 h-4 mr-2" />
                      Update
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))
        )}
      </motion.div>

      {/* Dialogs */}
      <ContractCreateSkillDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSkillCreated={handleSkillCreated}
      />

      {selectedSkill && (
        <>
          <UpdateSkillTokenDialog
            open={showUpdateDialog}
            onOpenChange={setShowUpdateDialog}
            skillToken={selectedSkill}
            onSkillUpdated={handleSkillUpdated}
          />

          <ViewSkillTokenDialog
            open={showViewDialog}
            onOpenChange={setShowViewDialog}
            skillToken={selectedSkill}
          />
        </>
      )}
    </div>
  );
}
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Star,
  Brain,
  Clock,
  ChevronRight,
  BarChart3,
  AlertCircle,
  RefreshCw,
  Sparkles,
  Trophy,
  Upload,
  Plus
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { DashboardWidget } from "./dashboard-widget";
import { useReputation, useSkillTokens } from "@/hooks/useDashboardData";
import { useAuth } from "@/hooks/useAuth";
import { dashboardApi } from "@/lib/api/dashboard-service";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api/client";

interface ReputationWidgetProps {
  className?: string;
}

export function ReputationWidget({ className }: ReputationWidgetProps) {
  const { user } = useAuth();
  const { reputation, history, isLoading, error, refetch } = useReputation();
  const { skillTokens } = useSkillTokens();

  const [isWorkSubmissionOpen, setIsWorkSubmissionOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const [workSubmission, setWorkSubmission] = useState({
    skillTokenId: "",
    workDescription: "",
    artifacts: [] as string[],
    selfAssessment: {} as Record<string, number>
  });

  const getReputationLevel = (score: number) => {
    if (score >= 90) return { label: "Expert", color: "text-purple-600 bg-purple-100 dark:bg-purple-900/30 dark:text-purple-300" };
    if (score >= 80) return { label: "Advanced", color: "text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-300" };
    if (score >= 70) return { label: "Proficient", color: "text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-300" };
    if (score >= 60) return { label: "Intermediate", color: "text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-300" };
    return { label: "Beginner", color: "text-slate-600 bg-slate-100 dark:bg-slate-900/30 dark:text-slate-300" };
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    return `${Math.floor(days / 30)} months ago`;
  };

  const handleWorkSubmission = async () => {
    if (!workSubmission.skillTokenId || !workSubmission.workDescription) return;

    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);

    try {
      const selectedSkill = skillTokens.find(s => s.tokenId.toString() === workSubmission.skillTokenId);
      if (!selectedSkill) throw new Error("Selected skill token not found");

      // Submit work evaluation using the API client
      const response = await apiClient.submitEvaluation({
        user: user?.accountId || "",
        skill_token_ids: [parseInt(workSubmission.skillTokenId)],
        work_description: workSubmission.workDescription,
        work_content: workSubmission.artifacts.join(", "),
        overall_score: Object.values(workSubmission.selfAssessment).reduce((a, b) => a + b, 0) / Object.keys(workSubmission.selfAssessment).length || 7,
        skill_scores: workSubmission.selfAssessment,
        feedback: "Self-assessment submitted",
        evidence: workSubmission.artifacts.join(", ")
      });

      if (response.success) {
        setSubmitSuccess(true);
        setWorkSubmission({
          skillTokenId: "",
          workDescription: "",
          artifacts: [],
          selfAssessment: {}
        });

        // Refresh reputation data
        await refetch();

        // Auto-close after success
        setTimeout(() => {
          setIsWorkSubmissionOpen(false);
          setSubmitSuccess(false);
        }, 3000);
      } else {
        setSubmitError(response.error || "Failed to submit work evaluation");
      }
    } catch (err) {
      console.error("Failed to submit work evaluation:", err);
      setSubmitError("Failed to submit work evaluation. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const addArtifactUrl = () => {
    setWorkSubmission(prev => ({
      ...prev,
      artifacts: [...prev.artifacts, ""]
    }));
  };

  const updateArtifactUrl = (index: number, url: string) => {
    setWorkSubmission(prev => ({
      ...prev,
      artifacts: prev.artifacts.map((artifact, i) => i === index ? url : artifact)
    }));
  };

  const reputationLevel = reputation ? getReputationLevel(reputation.overall_score) : null;

  return (
    <DashboardWidget
      title="AI Reputation Score"
      description="Track your AI-verified professional reputation and skill progression"
      icon={Brain}
      className={className}
      headerActions={
        <div className="flex items-center space-x-2">
          <Button size="sm" variant="outline" onClick={refetch} disabled={isLoading}>
            {isLoading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <BarChart3 className="w-4 h-4" />
            )}
          </Button>

          <Dialog open={isWorkSubmissionOpen} onOpenChange={setIsWorkSubmissionOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white">
                <Upload className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Submit Work</span>
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2">
                  <Brain className="w-5 h-5 text-purple-600" />
                  <span>Submit Work for AI Evaluation</span>
                </DialogTitle>
                <DialogDescription>
                  Our AI oracle will evaluate your work and update your skill levels and reputation score
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-6">
                {/* Skill Selection */}
                <div className="space-y-2">
                  <Label htmlFor="skillToken">Select Skill Token</Label>
                  <Select
                    value={workSubmission.skillTokenId}
                    onValueChange={(value) => setWorkSubmission({ ...workSubmission, skillTokenId: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose the skill this work demonstrates" />
                    </SelectTrigger>
                    <SelectContent>
                      {skillTokens.map((skill) => (
                        <SelectItem key={skill.tokenId} value={skill.tokenId.toString()}>
                          {skill.category} (Level {skill.level})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Work Description */}
                <div className="space-y-2">
                  <Label htmlFor="workDescription">Work Description</Label>
                  <Textarea
                    id="workDescription"
                    value={workSubmission.workDescription}
                    onChange={(e) => setWorkSubmission({ ...workSubmission, workDescription: e.target.value })}
                    placeholder="Describe the work you completed, technologies used, challenges solved, and outcomes achieved..."
                    rows={4}
                    className="resize-none"
                  />
                </div>

                {/* Artifacts */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Portfolio Links & Artifacts</Label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={addArtifactUrl}
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Add Link
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {workSubmission.artifacts.map((artifact, index) => (
                      <Input
                        key={index}
                        value={artifact}
                        onChange={(e) => updateArtifactUrl(index, e.target.value)}
                        placeholder={`Portfolio link ${index + 1} (GitHub, demo, etc.)`}
                      />
                    ))}
                    {workSubmission.artifacts.length === 0 && (
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        Add links to your GitHub repos, live demos, or other work samples
                      </p>
                    )}
                  </div>
                </div>

                {/* Error/Success Display */}
                {submitError && (
                  <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4 text-red-500 dark:text-red-400" />
                      <p className="text-sm text-red-600 dark:text-red-400">{submitError}</p>
                    </div>
                  </div>
                )}

                {submitSuccess && (
                  <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg p-3">
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-green-500 dark:text-green-400" />
                      <p className="text-sm text-green-600 dark:text-green-400">
                        Work submitted successfully! AI evaluation in progress...
                      </p>
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  onClick={handleWorkSubmission}
                  disabled={!workSubmission.skillTokenId || !workSubmission.workDescription || isSubmitting || submitSuccess}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                >
                  {isSubmitting ? (
                    <>
                      <Brain className="w-4 h-4 mr-2 animate-pulse" />
                      AI Evaluating...
                    </>
                  ) : submitSuccess ? (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Submitted!
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Submit for AI Evaluation
                    </>
                  )}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      }
    >
      {/* Loading State */}
      {isLoading ? (
        <div className="space-y-6">
          <div className="text-center space-y-4">
            <div className="w-24 h-24 bg-slate-200 dark:bg-slate-700 rounded-full mx-auto animate-pulse" />
            <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-32 mx-auto animate-pulse" />
            <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-48 mx-auto animate-pulse" />
          </div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-slate-50 dark:bg-slate-800/50 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      ) : error ? (
        <div className="text-center py-8">
          <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <p className="text-red-600 dark:text-red-400 font-medium mb-2">Failed to load reputation data</p>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{error}</p>
          <Button onClick={refetch} variant="outline">
            Try Again
          </Button>
        </div>
      ) : reputation ? (
        <div className="space-y-6">
          {/* Overall Score Display */}
          <div className="text-center">
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 260, damping: 20, delay: 0.2 }}
              className="relative w-24 h-24 mx-auto mb-4"
            >
              <div className="w-full h-full bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 rounded-full flex items-center justify-center border-4 border-purple-200 dark:border-purple-800">
                <div className="text-center">
                  <div className="text-2xl font-black text-purple-600 dark:text-purple-400">
                    {Math.round(reputation.overall_score)}
                  </div>
                  <div className="text-xs text-purple-500 dark:text-purple-400">
                    SCORE
                  </div>
                </div>
              </div>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 border-2 border-dashed border-purple-300 dark:border-purple-700 rounded-full"
              />
            </motion.div>

            <div className="space-y-2">
              {reputationLevel && (
                <Badge className={cn("text-sm font-bold px-3 py-1", reputationLevel.color)}>
                  <Star className="w-4 h-4 mr-1" />
                  {reputationLevel.label}
                </Badge>
              )}
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Based on {reputation.total_evaluations} AI evaluations
              </p>
            </div>
          </div>

          {/* Skill Breakdown */}
          {reputation.skill_scores && Object.keys(reputation.skill_scores).length > 0 && (
            <div>
              <h4 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center">
                <Trophy className="w-4 h-4 mr-2 text-yellow-600" />
                Skill Breakdown
              </h4>
              <div className="space-y-3">
                {Object.entries(reputation.skill_scores)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 5)
                  .map(([skill, score], index) => (
                    <motion.div
                      key={skill}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-slate-900 dark:text-white">
                            {skill}
                          </span>
                          <span className="text-sm font-bold text-slate-600 dark:text-slate-400">
                            {Math.round(score)}%
                          </span>
                        </div>
                        <Progress value={score} className="h-2" />
                      </div>
                    </motion.div>
                  ))}
              </div>
            </div>
          )}

          {/* Recent Evaluations */}
          <div>
            <h4 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center">
              <Clock className="w-4 h-4 mr-2 text-blue-600" />
              Recent AI Evaluations
            </h4>
            <div className="space-y-3">
              <AnimatePresence>
                {history.slice(0, 3).map((evaluation, index) => (
                  <motion.div
                    key={evaluation.evaluation_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    className="group p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-purple-300 dark:hover:border-purple-600 hover:bg-purple-50/50 dark:hover:bg-purple-950/20 transition-all duration-200"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Badge variant="outline" className="text-xs">
                            {evaluation.skill_category}
                          </Badge>
                          <Badge
                            className={cn(
                              "text-xs",
                              evaluation.score >= 80 ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" :
                                evaluation.score >= 60 ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300" :
                                  "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
                            )}
                          >
                            {evaluation.score}% Score
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
                          {evaluation.feedback}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-500 mt-2">
                          {formatTimeAgo(evaluation.timestamp)}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-purple-600 transition-colors" />
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {history.length === 0 && (
                <div className="text-center py-6">
                  <Brain className="w-12 h-12 mx-auto text-slate-400 mb-3" />
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    No evaluations yet. Submit your work to get AI-powered feedback!
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <Brain className="w-16 h-16 mx-auto text-slate-400 mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
            Build Your Reputation
          </h3>
          <p className="text-slate-600 dark:text-slate-400 mb-6">
            Submit your work for AI evaluation to build your professional reputation score
          </p>
          <Button
            onClick={() => setIsWorkSubmissionOpen(true)}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            disabled={skillTokens.length === 0}
          >
            <Upload className="w-4 h-4 mr-2" />
            Submit Your First Work
          </Button>
          {skillTokens.length === 0 && (
            <p className="text-xs text-slate-500 dark:text-slate-500 mt-2">
              Create skill tokens first to submit work for evaluation
            </p>
          )}
        </div>
      )}
    </DashboardWidget>
  );
}

export default ReputationWidget;
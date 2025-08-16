"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    Briefcase,
    Search,
    MapPin,
    Building,
    DollarSign,
    Clock,
    Users,
    Star,
    Bookmark,
    BookmarkPlus,
    CheckCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { useJobPools } from "@/hooks/useDashboardData";
import { ViewJobDetailsDialog } from "@/components/jobs/view-job-details-dialog";
import { ContractApplyToJobDialog } from "@/components/jobs/contract-apply-to-job-dialog";
import { WalletConnectionPrompt } from "@/components/dashboard/wallet-connection-prompt";

export default function JobsPage() {
    const { user, isConnected } = useAuth();
    const { jobPools, isLoading, error, refetch, applyToPool } = useJobPools();
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedType, setSelectedType] = useState("all");
    const [selectedLocation, setSelectedLocation] = useState("all");
    const [selectedJob, setSelectedJob] = useState<any>(null);
    const [showJobDetails, setShowJobDetails] = useState(false);
    const [showApplyDialog, setShowApplyDialog] = useState(false);

    // Transform job pools to match frontend format
    const transformedJobs = jobPools.map((job: any) => ({
        id: job.id || job.pool_id,
        title: job.title,
        company: job.company || "Company",
        location: job.location || "Remote",
        type: job.job_type || "Full-time",
        salary: job.salary || "$80k - $120k",
        posted: job.created_at ? new Date(job.created_at).toLocaleDateString() : "Recently",
        skills: job.required_skills || [],
        description: job.description,
        experience: job.experience_level || "3+ years",
        remote: job.is_remote || false,
        urgent: job.is_urgent || false,
        benefits: job.benefits || [],
        requirements: job.requirements || [],
        responsibilities: job.responsibilities || [],
        companyInfo: {
            description: job.company_description || "Leading company in the industry",
            size: job.company_size || "100-500 employees",
            industry: job.industry || "Technology",
            founded: job.founded_year || "2020",
            website: job.company_website || "https://company.com",
            rating: job.company_rating || 4.5,
            reviews: job.company_reviews || 50
        },
        applicationProcess: {
            steps: job.application_steps || ["Submit application", "Initial screening", "Interview"],
            timeline: job.application_timeline || "2-3 weeks",
            nextSteps: job.next_steps || "Applications reviewed within 48 hours"
        }
    }));

    const handleViewJob = (job: any) => {
        setSelectedJob(job);
        setShowJobDetails(true);
    };

    const handleApplyToJob = (job: any) => {
        setSelectedJob(job);
        setShowApplyDialog(true);
    };

    const handleApplicationSubmitted = async () => {
        // Refresh jobs list after application
        await refetch();
        setShowApplyDialog(false);
    };

    // Filter jobs based on search and filters
    const filteredJobs = transformedJobs.filter(job => {
        const matchesSearch = job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
            job.description.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesType = selectedType === "all" || job.type.toLowerCase() === selectedType.toLowerCase();
        const matchesLocation = selectedLocation === "all" ||
            (selectedLocation === "remote" && job.remote) ||
            (selectedLocation === "onsite" && !job.remote);
        return matchesSearch && matchesType && matchesLocation;
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
                        Job Opportunities
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-2">
                        Discover and apply to exciting positions in the blockchain ecosystem
                    </p>
                </div>
            </motion.div>

            {/* Search and Filters */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="flex flex-col sm:flex-row gap-4"
            >
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                    <Input
                        placeholder="Search jobs, companies, or skills..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                    />
                </div>
                <Select value={selectedType} onValueChange={setSelectedType}>
                    <SelectTrigger className="w-full sm:w-48">
                        <SelectValue placeholder="Job Type" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Types</SelectItem>
                        <SelectItem value="full-time">Full-time</SelectItem>
                        <SelectItem value="part-time">Part-time</SelectItem>
                        <SelectItem value="contract">Contract</SelectItem>
                        <SelectItem value="internship">Internship</SelectItem>
                    </SelectContent>
                </Select>
                <Select value={selectedLocation} onValueChange={setSelectedLocation}>
                    <SelectTrigger className="w-full sm:w-48">
                        <SelectValue placeholder="Location" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Locations</SelectItem>
                        <SelectItem value="remote">Remote</SelectItem>
                        <SelectItem value="onsite">On-site</SelectItem>
                    </SelectContent>
                </Select>
            </motion.div>

            {/* Jobs Grid */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="grid grid-cols-1 lg:grid-cols-2 gap-6"
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
                            <Briefcase className="w-12 h-12 mx-auto" />
                        </div>
                        <p className="text-slate-600 dark:text-slate-400 mb-4">{error}</p>
                        <Button onClick={refetch} variant="outline">
                            Try Again
                        </Button>
                    </div>
                ) : filteredJobs.length === 0 ? (
                    // Empty state
                    <div className="col-span-full text-center py-12">
                        <div className="text-slate-400 dark:text-slate-500 mb-4">
                            <Briefcase className="w-12 h-12 mx-auto" />
                        </div>
                        <p className="text-slate-600 dark:text-slate-400 mb-4">
                            {searchTerm || selectedType !== "all" || selectedLocation !== "all"
                                ? "No jobs match your search criteria"
                                : "No job opportunities available at the moment"}
                        </p>
                        {!searchTerm && selectedType === "all" && selectedLocation === "all" && (
                            <Button onClick={refetch} variant="outline">
                                Refresh Jobs
                            </Button>
                        )}
                    </div>
                ) : (
                    // Jobs grid
                    filteredJobs.map((job, index) => (
                        <motion.div
                            key={job.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.1 * index }}
                        >
                            <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300 h-full">
                                <CardContent className="p-6 h-full flex flex-col">
                                    {/* Job Header */}
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-2">
                                                {job.urgent && (
                                                    <Badge className="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300">
                                                        Urgent
                                                    </Badge>
                                                )}
                                                <Badge className="bg-hedera-100 text-hedera-700 dark:bg-hedera-900/30 dark:text-hedera-300">
                                                    {job.type}
                                                </Badge>
                                                {job.remote && (
                                                    <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                                                        Remote
                                                    </Badge>
                                                )}
                                            </div>
                                            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                                                {job.title}
                                            </h3>
                                            <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
                                                <div className="flex items-center gap-1">
                                                    <Building className="w-4 h-4" />
                                                    {job.company}
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <MapPin className="w-4 h-4" />
                                                    {job.location}
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <DollarSign className="w-4 h-4" />
                                                    {job.salary}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Job Description */}
                                    <p className="text-slate-600 dark:text-slate-400 text-sm mb-4 flex-1 line-clamp-3">
                                        {job.description}
                                    </p>

                                    {/* Required Skills */}
                                    {job.skills && job.skills.length > 0 && (
                                        <div className="mb-4">
                                            <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                                Required Skills:
                                            </p>
                                            <div className="flex flex-wrap gap-2">
                                                {job.skills.slice(0, 4).map((skill: string, skillIndex: number) => (
                                                    <Badge key={skillIndex} variant="outline" className="text-xs">
                                                        {skill}
                                                    </Badge>
                                                ))}
                                                {job.skills.length > 4 && (
                                                    <Badge variant="outline" className="text-xs">
                                                        +{job.skills.length - 4} more
                                                    </Badge>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Job Footer */}
                                    <div className="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-slate-700">
                                        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                                            <Clock className="w-4 h-4" />
                                            {job.posted}
                                        </div>
                                        <div className="flex gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleViewJob(job)}
                                            >
                                                <CheckCircle className="w-4 h-4 mr-2" />
                                                View Details
                                            </Button>
                                            <Button
                                                size="sm"
                                                onClick={() => handleApplyToJob(job)}
                                                className="bg-hedera-600 hover:bg-hedera-700"
                                            >
                                                <Users className="w-4 h-4 mr-2" />
                                                Apply Now
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ))
                )}
            </motion.div>

            {/* Dialogs */}
            {selectedJob && (
                <>
                    {/* Job Details Dialog */}
                    <ViewJobDetailsDialog
                        job={selectedJob}
                        triggerButton={
                            <Button variant="outline" size="sm">
                                View Details
                            </Button>
                        }
                    />

                    {/* Apply to Job Dialog */}
                    <ContractApplyToJobDialog
                        jobPool={{
                            id: selectedJob?.id || 0,
                            title: selectedJob?.title || "",
                            company: selectedJob?.company || "",
                            jobType: 0, // Default to full-time
                            requiredSkills: selectedJob?.skills || [],
                            minimumLevels: selectedJob?.skills.map(() => 1) || [],
                            salaryMin: 0,
                            salaryMax: 0,
                            deadline: Date.now() + 30 * 24 * 60 * 60 * 1000,
                            location: selectedJob?.location || "Remote",
                            isRemote: selectedJob?.remote || false,
                            description: selectedJob?.description || ""
                        }}
                        onApplicationSubmitted={handleApplicationSubmitted}
                        triggerButton={
                            <Button variant="default" size="sm">
                                Apply Now
                            </Button>
                        }
                    />
                </>
            )}
        </div>
    );
}

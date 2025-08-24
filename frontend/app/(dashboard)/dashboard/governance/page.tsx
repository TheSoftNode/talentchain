"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import {
    AlertTriangle,
    Users,
    Vote,
    Clock,
    Plus,
    TrendingUp,
    Shield,
    BarChart3,
    Zap,
    UserCheck,
    Activity,
    Award
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import {
    GovernanceProposal,
    VoteRecord,
    GovernanceMetrics,
    CreateProposalRequest
} from '@/lib/api/client';
import { formatDistanceToNow, format } from 'date-fns';
import { useAuth } from '@/hooks/useAuth';

export default function GovernancePage() {
    const { user } = useAuth();
    const [proposals, setProposals] = useState<GovernanceProposal[]>([]);
    const [emergencyProposals, setEmergencyProposals] = useState<GovernanceProposal[]>([]);
    const [userVotes, setUserVotes] = useState<VoteRecord[]>([]);
    const [metrics, setMetrics] = useState<GovernanceMetrics | null>(null);
    const [votingPower, setVotingPower] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [createProposalOpen, setCreateProposalOpen] = useState(false);
    const [createEmergencyOpen, setCreateEmergencyOpen] = useState(false);

    // Form states
    const [proposalForm, setProposalForm] = useState({
        title: '',
        description: '',
        targets: [''],
        values: [0],
        calldatas: [''],
        proposalType: 'STANDARD'
    });

    const [emergencyForm, setEmergencyForm] = useState({
        title: '',
        description: '',
        justification: '',
        targets: [''],
        values: [0],
        calldatas: [''],
        urgencyLevel: 'HIGH'
    });

    useEffect(() => {
        loadGovernanceData();
    }, [user?.walletAddress]);

    console.log('user', user);

    const loadGovernanceData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            // Load all governance data in parallel
            const [proposalsRes, votingPowerRes] = await Promise.all([
                apiClient.getProposals(1, 50),
                user?.walletAddress ? apiClient.getVotingPower(user.walletAddress) : null,
            ]);

            if (proposalsRes.success && proposalsRes.data) {
                setProposals(proposalsRes.data.items || []);

                // Separate emergency proposals
                const emergency = proposalsRes.data.items?.filter(
                    (p: GovernanceProposal) => p.proposalType === 1
                ) || [];
                setEmergencyProposals(emergency);
            } else {
                setError(proposalsRes.error || 'Failed to load proposals');
            }

            // Mock governance metrics for now
            setMetrics({
                totalProposals: proposals.length,
                activeProposals: proposals.filter(p => p.status === 'ACTIVE').length,
                totalVoters: 156,
                totalVotingPower: 10000,
                participationRate: 0.65,
                averageParticipation: 0.65
            });

            if (votingPowerRes?.success && votingPowerRes.data) {
                setVotingPower(votingPowerRes.data.voting_power);
            }

            // Mock user votes for now
            if (user?.walletAddress) {
                setUserVotes([]);
            }
        } catch (err) {
            console.error('Error loading governance data:', err);
            setError('Failed to load governance data');
        } finally {
            setLoading(false);
        }
    }, [user?.walletAddress]);

    const getProposalStatusColor = (status: string) => {
        switch (status) {
            case 'ACTIVE':
                return 'bg-blue-500';
            case 'SUCCEEDED':
                return 'bg-green-500';
            case 'DEFEATED':
                return 'bg-red-500';
            case 'EXECUTED':
                return 'bg-purple-500';
            case 'EXPIRED':
                return 'bg-gray-500';
            default:
                return 'bg-gray-500';
        }
    };

    const getUrgencyColor = (level: string) => {
        return level === 'CRITICAL' ? 'bg-red-600' : 'bg-orange-500';
    };

    const handleCreateProposal = async () => {
        if (!user?.walletAddress) return;

        try {
            const request: CreateProposalRequest = {
                title: proposalForm.title,
                description: proposalForm.description,
                targets: proposalForm.targets.filter(t => t.trim()),
                values: proposalForm.values,
                calldatas: proposalForm.calldatas.filter(c => c.trim()),
                ipfsHash: `ipfs://proposal-${Date.now()}`
            };

            // TODO: Call contract service
            console.log('Creating proposal:', request);
            setCreateProposalOpen(false);
            setProposalForm({
                title: '',
                description: '',
                targets: [''],
                values: [0],
                calldatas: [''],
                proposalType: 'STANDARD'
            });
        } catch (error) {
            console.error('Error creating proposal:', error);
        }
    };

    const handleVote = async (proposalId: number, vote: 'FOR' | 'AGAINST' | 'ABSTAIN') => {
        if (!user?.walletAddress) return;

        try {
            // TODO: Call contract service
            console.log('Voting on proposal:', proposalId, 'with vote:', vote);
        } catch (error) {
            console.error('Error voting:', error);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-hedera-500 mx-auto mb-4"></div>
                    <p className="text-slate-600 dark:text-slate-400">Loading governance data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                    <p className="text-red-600 dark:text-red-400">{error}</p>
                    <Button onClick={loadGovernanceData} className="mt-4">Retry</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Governance</h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-2">
                        Participate in platform decisions and shape the future of TalentChain Pro
                    </p>
                </div>
                <div className="flex gap-3">
                    <Dialog open={createProposalOpen} onOpenChange={setCreateProposalOpen}>
                        <DialogTrigger asChild>
                            <Button>
                                <Plus className="h-4 w-4 mr-2" />
                                Create Proposal
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                            <DialogHeader>
                                <DialogTitle>Create New Proposal</DialogTitle>
                                <DialogDescription>
                                    Submit a new governance proposal for the community to vote on.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                                <div>
                                    <Label htmlFor="title">Title</Label>
                                    <Input
                                        id="title"
                                        value={proposalForm.title}
                                        onChange={(e) => setProposalForm(prev => ({ ...prev, title: e.target.value }))}
                                        placeholder="Proposal title"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="description">Description</Label>
                                    <Textarea
                                        id="description"
                                        value={proposalForm.description}
                                        onChange={(e) => setProposalForm(prev => ({ ...prev, description: e.target.value }))}
                                        placeholder="Detailed description of the proposal"
                                        rows={4}
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="type">Proposal Type</Label>
                                    <Select
                                        value={proposalForm.proposalType}
                                        onValueChange={(value) => setProposalForm(prev => ({ ...prev, proposalType: value }))}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="STANDARD">Standard Proposal</SelectItem>
                                            <SelectItem value="EMERGENCY">Emergency Proposal</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setCreateProposalOpen(false)}>
                                    Cancel
                                </Button>
                                <Button onClick={handleCreateProposal}>Create Proposal</Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>

                    <Dialog open={createEmergencyOpen} onOpenChange={setCreateEmergencyOpen}>
                        <DialogTrigger asChild>
                            <Button variant="destructive">
                                <AlertTriangle className="h-4 w-4 mr-2" />
                                Emergency Proposal
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                            <DialogHeader>
                                <DialogTitle>Create Emergency Proposal</DialogTitle>
                                <DialogDescription>
                                    Submit an emergency proposal that requires immediate attention.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                                <div>
                                    <Label htmlFor="emergency-title">Title</Label>
                                    <Input
                                        id="emergency-title"
                                        value={emergencyForm.title}
                                        onChange={(e) => setEmergencyForm(prev => ({ ...prev, title: e.target.value }))}
                                        placeholder="Emergency proposal title"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="emergency-description">Description</Label>
                                    <Textarea
                                        id="emergency-description"
                                        value={emergencyForm.description}
                                        onChange={(e) => setEmergencyForm(prev => ({ ...prev, description: e.target.value }))}
                                        placeholder="Detailed description of the emergency"
                                        rows={4}
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="justification">Justification</Label>
                                    <Textarea
                                        id="justification"
                                        value={emergencyForm.justification}
                                        onChange={(e) => setEmergencyForm(prev => ({ ...prev, justification: e.target.value }))}
                                        placeholder="Why is this an emergency?"
                                        rows={3}
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="urgency">Urgency Level</Label>
                                    <Select
                                        value={emergencyForm.urgencyLevel}
                                        onValueChange={(value) => setEmergencyForm(prev => ({ ...prev, urgencyLevel: value }))}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="HIGH">High</SelectItem>
                                            <SelectItem value="CRITICAL">Critical</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setCreateEmergencyOpen(false)}>
                                    Cancel
                                </Button>
                                <Button variant="destructive" onClick={() => {
                                    // TODO: Handle emergency proposal creation
                                    setCreateEmergencyOpen(false);
                                }}>
                                    Create Emergency Proposal
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
                    <CardContent className="p-6">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                <Vote className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Proposals</p>
                                <p className="text-2xl font-bold text-slate-900 dark:text-white">{metrics?.totalProposals || 0}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
                    <CardContent className="p-6">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                                <Activity className="h-6 w-6 text-green-600 dark:text-green-400" />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Active Proposals</p>
                                <p className="text-2xl font-bold text-slate-900 dark:text-white">{metrics?.activeProposals || 0}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
                    <CardContent className="p-6">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                                <Users className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Voters</p>
                                <p className="text-2xl font-bold text-slate-900 dark:text-white">{metrics?.totalVoters || 0}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
                    <CardContent className="p-6">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                                <Award className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Your Voting Power</p>
                                <p className="text-2xl font-bold text-slate-900 dark:text-white">{votingPower}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Main Content Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="overview">
                        <BarChart3 className="h-4 w-4 mr-2" />
                        Overview
                    </TabsTrigger>
                    <TabsTrigger value="proposals">
                        <Vote className="h-4 w-4 mr-2" />
                        Proposals
                    </TabsTrigger>
                    <TabsTrigger value="emergency">
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Emergency
                    </TabsTrigger>
                    <TabsTrigger value="votes">
                        <TrendingUp className="h-4 w-4 mr-2" />
                        My Votes
                    </TabsTrigger>
                </TabsList>

                {/* Overview Tab */}
                <TabsContent value="overview" className="mt-6 space-y-6">
                    {/* Participation Chart */}
                    <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
                        <CardHeader>
                            <CardTitle>Voting Participation</CardTitle>
                            <CardDescription>Community engagement in governance decisions</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-slate-600 dark:text-slate-400">Average Participation</span>
                                    <span className="text-sm font-medium text-slate-900 dark:text-white">
                                        {((metrics?.averageParticipation || 0) * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <Progress value={(metrics?.averageParticipation || 0) * 100} className="h-2" />
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                        <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                                            {proposals.filter(p => p.status === 'SUCCEEDED').length}
                                        </div>
                                        <div className="text-slate-600 dark:text-slate-400">Approved</div>
                                    </div>
                                    <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                        <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                                            {proposals.filter(p => p.status === 'DEFEATED').length}
                                        </div>
                                        <div className="text-slate-600 dark:text-slate-400">Rejected</div>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Recent Activity */}
                    <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
                        <CardHeader>
                            <CardTitle>Recent Activity</CardTitle>
                            <CardDescription>Latest governance actions and proposals</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {proposals.slice(0, 5).map((proposal) => (
                                    <div key={proposal.id} className="flex items-center space-x-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                        <div className="w-2 h-2 bg-hedera-500 rounded-full"></div>
                                        <div className="flex-1">
                                            <p className="text-sm font-medium text-slate-900 dark:text-white">{proposal.title}</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                {formatDistanceToNow(new Date(proposal.created * 1000), { addSuffix: true })}
                                            </p>
                                        </div>
                                        <Badge className={getProposalStatusColor(proposal.status)}>
                                            {proposal.status}
                                        </Badge>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Proposals Tab */}
                <TabsContent value="proposals" className="mt-6">
                    <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
                        <CardHeader>
                            <CardTitle>Active Proposals</CardTitle>
                            <CardDescription>Vote on current proposals and shape the platform's future</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {proposals.filter(p => p.status === 'ACTIVE').length === 0 ? (
                                    <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                                        <Vote className="h-16 w-16 mx-auto mb-4 opacity-50" />
                                        <p className="text-lg font-medium">No active proposals</p>
                                        <p className="text-sm">Check back later for new proposals to vote on.</p>
                                    </div>
                                ) : (
                                    proposals.filter(p => p.status === 'ACTIVE').map((proposal) => (
                                        <div
                                            key={proposal.id}
                                            className="border border-slate-200 dark:border-slate-700 rounded-lg p-6 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                                        >
                                            <div className="flex items-start justify-between mb-4">
                                                <div className="flex-1">
                                                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">{proposal.title}</h3>
                                                    <p className="text-slate-600 dark:text-slate-400 mb-3">{proposal.description}</p>
                                                    <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
                                                        <span className="flex items-center gap-1">
                                                            <Clock className="h-4 w-4" />
                                                            Ends {formatDistanceToNow(new Date(proposal.deadline), { addSuffix: true })}
                                                        </span>
                                                        <span className="flex items-center gap-1">
                                                            <Users className="h-4 w-4" />
                                                            {proposal.forVotes + proposal.againstVotes + proposal.abstainVotes} total votes
                                                        </span>
                                                    </div>
                                                </div>
                                                <Badge className={`ml-4 ${getProposalStatusColor(proposal.status)} text-white`}>
                                                    {proposal.status}
                                                </Badge>
                                            </div>

                                            {/* Vote breakdown */}
                                            <div className="space-y-3 mb-4">
                                                <div className="flex items-center justify-between text-sm">
                                                    <span className="text-green-600 dark:text-green-400 font-medium">For: {proposal.forVotes}</span>
                                                    <span className="text-red-600 dark:text-red-400 font-medium">Against: {proposal.againstVotes}</span>
                                                    <span className="text-yellow-600 dark:text-yellow-400 font-medium">Abstain: {proposal.abstainVotes}</span>
                                                </div>
                                                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                                                    <div
                                                        className="bg-green-500 h-3 rounded-l-full transition-all duration-300"
                                                        style={{
                                                            width: `${(proposal.forVotes / Math.max(proposal.forVotes + proposal.againstVotes + proposal.abstainVotes, 1)) * 100}%`
                                                        }}
                                                    />
                                                </div>
                                            </div>

                                            {/* Voting buttons */}
                                            {user?.walletAddress && (
                                                <div className="flex gap-3">
                                                    <Button
                                                        onClick={() => handleVote(proposal.id, 'FOR')}
                                                        className="bg-green-600 hover:bg-green-700 text-white"
                                                    >
                                                        <TrendingUp className="h-4 w-4 mr-2" />
                                                        Vote For
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        onClick={() => handleVote(proposal.id, 'AGAINST')}
                                                        className="border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20"
                                                    >
                                                        Vote Against
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        onClick={() => handleVote(proposal.id, 'ABSTAIN')}
                                                    >
                                                        Abstain
                                                    </Button>
                                                </div>
                                            )}
                                        </div>
                                    ))
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Emergency Tab */}
                <TabsContent value="emergency" className="mt-6">
                    <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
                        <CardHeader>
                            <CardTitle>Emergency Proposals</CardTitle>
                            <CardDescription>Critical issues requiring immediate community attention</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {emergencyProposals.length === 0 ? (
                                    <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                                        <Shield className="h-16 w-16 mx-auto mb-4 opacity-50" />
                                        <p className="text-lg font-medium">No emergency proposals</p>
                                        <p className="text-sm">All systems are running smoothly.</p>
                                    </div>
                                ) : (
                                    emergencyProposals.map((proposal) => (
                                        <div
                                            key={proposal.id}
                                            className="border border-red-200 dark:border-red-800 rounded-lg p-6 bg-red-50 dark:bg-red-950/20"
                                        >
                                            <div className="flex items-start justify-between mb-4">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
                                                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{proposal.title}</h3>
                                                    </div>
                                                    <p className="text-slate-600 dark:text-slate-400 mb-3">{proposal.description}</p>
                                                    <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
                                                        <span className="flex items-center gap-1">
                                                            <Clock className="h-4 w-4" />
                                                            Ends {formatDistanceToNow(new Date(proposal.deadline), { addSuffix: true })}
                                                        </span>
                                                        <span className="flex items-center gap-1">
                                                            <Zap className="h-4 w-4" />
                                                            Emergency Level: {proposal.proposalType === 1 ? 'HIGH' : 'STANDARD'}
                                                        </span>
                                                    </div>
                                                </div>
                                                <Badge className="ml-4 bg-red-600 text-white">
                                                    EMERGENCY
                                                </Badge>
                                            </div>

                                            {/* Vote breakdown */}
                                            <div className="space-y-3 mb-4">
                                                <div className="flex items-center justify-between text-sm">
                                                    <span className="text-green-600 dark:text-green-400 font-medium">For: {proposal.forVotes}</span>
                                                    <span className="text-red-600 dark:text-red-400 font-medium">Against: {proposal.againstVotes}</span>
                                                    <span className="text-yellow-600 dark:text-yellow-400 font-medium">Abstain: {proposal.abstainVotes}</span>
                                                </div>
                                                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
                                                    <div
                                                        className="bg-green-500 h-3 rounded-l-full transition-all duration-300"
                                                        style={{
                                                            width: `${(proposal.forVotes / Math.max(proposal.forVotes + proposal.againstVotes + proposal.abstainVotes, 1)) * 100}%`
                                                        }}
                                                    />
                                                </div>
                                            </div>

                                            {/* Voting buttons */}
                                            {user?.walletAddress && (
                                                <div className="flex gap-3">
                                                    <Button
                                                        onClick={() => handleVote(proposal.id, 'FOR')}
                                                        className="bg-green-600 hover:bg-green-700 text-white"
                                                    >
                                                        <TrendingUp className="h-4 w-4 mr-2" />
                                                        Vote For
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        onClick={() => handleVote(proposal.id, 'AGAINST')}
                                                        className="border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20"
                                                    >
                                                        Vote Against
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        onClick={() => handleVote(proposal.id, 'ABSTAIN')}
                                                    >
                                                        Abstain
                                                    </Button>
                                                </div>
                                            )}
                                        </div>
                                    ))
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* My Votes Tab */}
                <TabsContent value="votes" className="mt-6">
                    <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-700/50 transition-all duration-300">
                        <CardHeader>
                            <CardTitle>My Voting History</CardTitle>
                            <CardDescription>Track your participation in governance decisions</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {!user?.walletAddress ? (
                                <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                                    <UserCheck className="h-16 w-16 mx-auto mb-4 opacity-50" />
                                    <p className="text-lg font-medium">Connect your wallet</p>
                                    <p className="text-sm">Connect your wallet to view your voting history.</p>
                                </div>
                            ) : userVotes.length === 0 ? (
                                <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                                    <Vote className="h-16 w-16 mx-auto mb-4 opacity-50" />
                                    <p className="text-lg font-medium">No votes yet</p>
                                    <p className="text-sm">Start participating in governance by voting on active proposals.</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {userVotes.map((vote) => (
                                        <div
                                            key={`${vote.proposalId}-${vote.voter}`}
                                            className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                                        >
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <p className="font-medium text-slate-900 dark:text-white">
                                                        Proposal #{vote.proposalId}
                                                    </p>
                                                    <p className="text-sm text-slate-500 dark:text-slate-400">
                                                        {format(new Date(vote.timestamp), 'MMM dd, yyyy')}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <Badge
                                                        className={
                                                            vote.support === 1 ? 'bg-green-500' :
                                                                vote.support === 0 ? 'bg-red-500' : 'bg-yellow-500'
                                                        }
                                                    >
                                                        {vote.support === 1 ? 'FOR' : vote.support === 0 ? 'AGAINST' : 'ABSTAIN'}
                                                    </Badge>
                                                    <span className="text-sm text-slate-500 dark:text-slate-400">
                                                        Power: {vote.votingPower || 0}
                                                    </span>
                                                </div>
                                            </div>
                                            {vote.reason && (
                                                <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 italic">
                                                    "{vote.reason}"
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}

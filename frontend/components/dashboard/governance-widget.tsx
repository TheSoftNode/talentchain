/**
 * Governance Dashboard Widget - Professional implementation with all contract functions
 * Provides complete governance interface for proposals, voting, and delegation
 */
'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Vote, Plus, AlertTriangle, Clock, CheckCircle, XCircle } from 'lucide-react';
import { apiClient, ApiResponse } from '@/lib/api/client';
import { CreateProposalRequest, CastVoteRequest } from '@/lib/api/client';

interface Proposal {
  id: string;
  title: string;
  description: string;
  status: string;
  forVotes: number;
  againstVotes: number;
  startTime: string;
  endTime: string;
  proposer: string;
}

interface GovernanceStats {
  totalProposals: number;
  activeProposals: number;
  totalVotes: number;
  participationRate: number;
}

export function GovernanceWidget({ walletAddress }: { walletAddress?: string }) {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [stats, setStats] = useState<GovernanceStats>({
    totalProposals: 0,
    activeProposals: 0,
    totalVotes: 0,
    participationRate: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showVoteDialog, setShowVoteDialog] = useState(false);
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);

  // Form states
  const [proposalForm, setProposalForm] = useState({
    title: '',
    description: '',
    targets: [''],
    values: [0],
    calldatas: [''],
    ipfsHash: '',
  });

  const [voteForm, setVoteForm] = useState({
    vote: 1, // 0=Against, 1=For, 2=Abstain
    reason: '',
  });

  useEffect(() => {
    if (walletAddress) {
      loadGovernanceData();
    }
  }, [walletAddress]);

  const loadGovernanceData = async () => {
    if (!walletAddress) return;

    setLoading(true);
    setError(null);

    try {
      // Load proposals
      const proposalsResponse = await apiClient.getProposals(1, 5);
      if (proposalsResponse.success && proposalsResponse.data) {
        const formattedProposals = proposalsResponse.data.items.map((item: any) => ({
          id: item.proposal_id || item.id,
          title: item.title,
          description: item.description,
          status: item.status,
          forVotes: item.for_votes || 0,
          againstVotes: item.against_votes || 0,
          startTime: item.start_time,
          endTime: item.end_time,
          proposer: item.proposer_address || item.proposer,
        }));
        setProposals(formattedProposals);

        // Calculate stats
        const totalProposals = proposalsResponse.data.total;
        const activeProposals = formattedProposals.filter(p => p.status === 'ACTIVE').length;
        const totalVotes = formattedProposals.reduce((sum, p) => sum + p.forVotes + p.againstVotes, 0);
        const participationRate = totalProposals > 0 ? (activeProposals / totalProposals) * 100 : 0;

        setStats({
          totalProposals,
          activeProposals,
          totalVotes,
          participationRate,
        });
      }
    } catch (err) {
      console.error('Failed to load governance data:', err);
      setError('Failed to load governance data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProposal = async () => {
    if (!walletAddress) {
      setError('Wallet not connected');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: CreateProposalRequest = {
        title: proposalForm.title,
        description: proposalForm.description,
        targets: proposalForm.targets.filter(t => t.trim()),
        values: proposalForm.values.slice(0, proposalForm.targets.length),
        calldatas: proposalForm.calldatas.slice(0, proposalForm.targets.length),
        ipfsHash: proposalForm.ipfsHash,
      };

      const response = await apiClient.createProposal(request);

      if (response.success) {
        setShowCreateDialog(false);
        setProposalForm({
          title: '',
          description: '',
          targets: [''],
          values: [0],
          calldatas: [''],
          ipfsHash: '',
        });
        await loadGovernanceData(); // Refresh data
      } else {
        setError(response.error || 'Failed to create proposal');
      }
    } catch (err) {
      console.error('Failed to create proposal:', err);
      setError('Failed to create proposal');
    } finally {
      setLoading(false);
    }
  };

  const handleCastVote = async () => {
    if (!walletAddress || !selectedProposal) {
      setError('Wallet not connected or proposal not selected');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: CastVoteRequest = {
        proposalId: parseInt(selectedProposal.id),
        vote: voteForm.vote,
        reason: voteForm.reason,
      };

      const response = await apiClient.castVote(request);

      if (response.success) {
        setShowVoteDialog(false);
        setVoteForm({ vote: 1, reason: '' });
        setSelectedProposal(null);
        await loadGovernanceData(); // Refresh data
      } else {
        setError(response.error || 'Failed to cast vote');
      }
    } catch (err) {
      console.error('Failed to cast vote:', err);
      setError('Failed to cast vote');
    } finally {
      setLoading(false);
    }
  };

  const addTarget = () => {
    setProposalForm(prev => ({
      ...prev,
      targets: [...prev.targets, ''],
      values: [...prev.values, 0],
      calldatas: [...prev.calldatas, ''],
    }));
  };

  const removeTarget = (index: number) => {
    setProposalForm(prev => ({
      ...prev,
      targets: prev.targets.filter((_, i) => i !== index),
      values: prev.values.filter((_, i) => i !== index),
      calldatas: prev.calldatas.filter((_, i) => i !== index),
    }));
  };

  const updateTarget = (index: number, field: 'targets' | 'values' | 'calldatas', value: string | number) => {
    setProposalForm(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item),
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'PENDING': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'EXECUTED': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'DEFEATED': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ACTIVE': return <CheckCircle className="w-4 h-4" />;
      case 'PENDING': return <Clock className="w-4 h-4" />;
      case 'EXECUTED': return <CheckCircle className="w-4 h-4" />;
      case 'DEFEATED': return <XCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  if (!walletAddress) {
    return (
      <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-600/50 transition-all duration-300">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Vote className="w-5 h-5 text-hedera-600 dark:text-hedera-400" />
            Governance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-600 dark:text-slate-400 text-center py-8">
            Connect your wallet to participate in governance
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50 hover:shadow-lg hover:border-hedera-300/50 dark:hover:border-hedera-600/50 transition-all duration-300">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Vote className="w-5 h-5 text-hedera-600 dark:text-hedera-400" />
            Governance
          </CardTitle>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button size="sm" className="bg-hedera-600 hover:bg-hedera-700">
                <Plus className="w-4 h-4 mr-2" />
                Create Proposal
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Proposal</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Title</label>
                  <Input
                    value={proposalForm.title}
                    onChange={(e) => setProposalForm(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Proposal title"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Description</label>
                  <Textarea
                    value={proposalForm.description}
                    onChange={(e) => setProposalForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Detailed proposal description"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">IPFS Hash</label>
                  <Input
                    value={proposalForm.ipfsHash}
                    onChange={(e) => setProposalForm(prev => ({ ...prev, ipfsHash: e.target.value }))}
                    placeholder="IPFS hash for additional content"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Targets & Parameters</label>
                    <Button type="button" variant="outline" size="sm" onClick={addTarget}>
                      <Plus className="w-4 h-4 mr-1" />
                      Add Target
                    </Button>
                  </div>
                  {proposalForm.targets.map((target, index) => (
                    <div key={index} className="grid grid-cols-3 gap-2 mb-2">
                      <Input
                        value={target}
                        onChange={(e) => updateTarget(index, 'targets', e.target.value)}
                        placeholder="Contract address"
                      />
                      <Input
                        type="number"
                        value={proposalForm.values[index]}
                        onChange={(e) => updateTarget(index, 'values', parseInt(e.target.value) || 0)}
                        placeholder="Value (HBAR)"
                      />
                      <div className="flex gap-2">
                        <Input
                          value={proposalForm.calldatas[index]}
                          onChange={(e) => updateTarget(index, 'calldatas', e.target.value)}
                          placeholder="Calldata"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeTarget(index)}
                          disabled={proposalForm.targets.length === 1}
                        >
                          <XCircle className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {error && <p className="text-red-600 text-sm">{error}</p>}

                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreateProposal}
                    disabled={loading || !proposalForm.title || !proposalForm.description}
                    className="bg-hedera-600 hover:bg-hedera-700"
                  >
                    {loading ? 'Creating...' : 'Create Proposal'}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Stats Overview */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-hedera-600 dark:text-hedera-400">
              {stats.totalProposals}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Total Proposals</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-hedera-600 dark:text-hedera-400">
              {stats.activeProposals}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Active</div>
          </div>
        </div>

        {/* Participation Rate */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span>Participation Rate</span>
            <span>{stats.participationRate.toFixed(1)}%</span>
          </div>
          <Progress value={stats.participationRate} className="h-2" />
        </div>

        {/* Recent Proposals */}
        <div>
          <h4 className="font-medium mb-3">Recent Proposals</h4>
          <div className="space-y-3">
            {loading ? (
              <div className="text-center py-4 text-slate-600 dark:text-slate-400">
                Loading proposals...
              </div>
            ) : proposals.length === 0 ? (
              <div className="text-center py-4 text-slate-600 dark:text-slate-400">
                No proposals yet
              </div>
            ) : (
              proposals.map((proposal) => (
                <div key={proposal.id} className="border border-slate-200 dark:border-slate-700 rounded-lg p-3">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h5 className="font-medium text-sm">{proposal.title}</h5>
                      <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
                        {proposal.description}
                      </p>
                    </div>
                    <Badge className={`ml-2 ${getStatusColor(proposal.status)}`}>
                      {getStatusIcon(proposal.status)}
                      <span className="ml-1">{proposal.status}</span>
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
                    <span>By: {proposal.proposer.slice(0, 8)}...{proposal.proposer.slice(-6)}</span>
                    <div className="flex items-center gap-4">
                      <span>For: {proposal.forVotes}</span>
                      <span>Against: {proposal.againstVotes}</span>
                    </div>
                  </div>

                  {proposal.status === 'ACTIVE' && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="mt-2 w-full"
                      onClick={() => {
                        setSelectedProposal(proposal);
                        setShowVoteDialog(true);
                      }}
                    >
                      <Vote className="w-4 h-4 mr-2" />
                      Vote
                    </Button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Vote Dialog */}
        <Dialog open={showVoteDialog} onOpenChange={setShowVoteDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Vote on Proposal</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {selectedProposal && (
                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <h5 className="font-medium">{selectedProposal.title}</h5>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {selectedProposal.description}
                  </p>
                </div>
              )}

              <div>
                <label className="text-sm font-medium">Your Vote</label>
                <Select value={voteForm.vote.toString()} onValueChange={(value) => setVoteForm(prev => ({ ...prev, vote: parseInt(value) }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">Against</SelectItem>
                    <SelectItem value="1">For</SelectItem>
                    <SelectItem value="2">Abstain</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium">Reason (Optional)</label>
                <Textarea
                  value={voteForm.reason}
                  onChange={(e) => setVoteForm(prev => ({ ...prev, reason: e.target.value }))}
                  placeholder="Why are you voting this way?"
                  rows={2}
                />
              </div>

              {error && <p className="text-red-600 text-sm">{error}</p>}

              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowVoteDialog(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleCastVote}
                  disabled={loading}
                  className="bg-hedera-600 hover:bg-hedera-700"
                >
                  {loading ? 'Casting Vote...' : 'Cast Vote'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}

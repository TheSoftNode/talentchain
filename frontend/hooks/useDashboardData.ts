/**
 * Custom hooks for dashboard data management with caching and error handling
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  DashboardStats,
  SkillTokenInfo,
  JobPoolInfo,
  ApiResponse,
  TransactionResult
} from '@/lib/types/wallet';
import { apiClient } from '@/lib/api/client';
import { useAuth } from './useAuth';
import { useDashboardRealtimeSync } from './useRealTimeUpdates';

interface UseDashboardDataReturn {
  // Basic dashboard data
  stats: DashboardStats | null;
  skillTokens: SkillTokenInfo[];
  jobPools: JobPoolInfo[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  lastUpdated: Date | null;

  // Enhanced Skills functionality
  createSkillToken: (data: any) => Promise<TransactionResult>;
  updateSkillLevel: (tokenId: number, data: any) => Promise<TransactionResult>;
  endorseSkillToken: (tokenId: string, endorsementData: string) => Promise<TransactionResult>;
  renewSkillToken: (tokenId: string, newExpiryDate: number) => Promise<TransactionResult>;
  revokeSkillToken: (tokenId: string, reason: string) => Promise<TransactionResult>;
  getSkillEndorsements: (tokenId: string) => Promise<any[]>;
  markExpiredTokens: (tokenIds: string[]) => Promise<TransactionResult>;
  getTokensByCategory: (category: string, limit?: number) => Promise<any[]>;
  getTotalSkillsByCategory: (category: string) => Promise<number>;
  isLoadingSkills: boolean;
  skillsError: string | null;

  // Enhanced Job Pools functionality
  createJobPool: (data: any) => Promise<TransactionResult>;
  applyToPool: (poolId: number, skillTokenIds: number[]) => Promise<TransactionResult>;
  leavePool: (poolId: number) => Promise<TransactionResult>;
  selectCandidate: (poolId: string, candidateAddress: string) => Promise<TransactionResult>;
  completePool: (poolId: string) => Promise<TransactionResult>;
  closePool: (poolId: string) => Promise<TransactionResult>;
  calculateMatchScore: (poolId: string, candidateAddress: string) => Promise<number>;
  getPoolMetrics: (poolId: string) => Promise<any>;
  getTalentPoolGlobalStats: () => Promise<any>;
  getActivePoolsCount: () => Promise<number>;
  getTotalPoolsCount: () => Promise<number>;
  isLoadingJobs: boolean;
  jobsError: string | null;

  // Enhanced Reputation functionality
  reputation: any;
  history: any[];
  isLoadingReputation: boolean;
  reputationError: string | null;
  registerOracle: (stakeAmount: number, categories: string[]) => Promise<TransactionResult>;
  submitEvaluation: (userAddress: string, category: string, score: number, evidence: string) => Promise<TransactionResult>;
  challengeEvaluation: (evaluationId: string, reason: string, stakeAmount: number) => Promise<TransactionResult>;
  resolveChallenge: (challengeId: string, resolution: string) => Promise<TransactionResult>;
  slashOracle: (oracleAddress: string, reason: string) => Promise<TransactionResult>;
  withdrawOracleStake: (oracleAddress: string) => Promise<TransactionResult>;
  getOracleInfo: (oracleAddress: string) => Promise<any>;
  getActiveOracles: () => Promise<any[]>;
  getCategoryScore: (userAddress: string, category: string) => Promise<number>;
  getWorkEvaluation: (evaluationId: string) => Promise<any>;
  getUserEvaluations: (userAddress: string) => Promise<any[]>;
  getGlobalStats: () => Promise<any>;

  // Enhanced Governance functionality
  proposals: any[];
  activeProposals: any[];
  isLoadingGovernance: boolean;
  governanceError: string | null;
  createProposal: (data: any) => Promise<TransactionResult>;
  castVote: (data: any) => Promise<TransactionResult>;
  delegateVotingPower: (delegatee: string) => Promise<TransactionResult>;
  undelegateVotingPower: () => Promise<TransactionResult>;
  getProposal: (id: string) => Promise<any>;
  getVotingPower: (address: string) => Promise<any>;
  getProposalStatus: (proposalId: string) => Promise<string>;
  getVoteReceipt: (proposalId: string, voter: string) => Promise<any>;
  getQuorum: () => Promise<number>;
  getVotingDelay: () => Promise<number>;
  getVotingPeriod: () => Promise<number>;
  getProposalThreshold: () => Promise<number>;
  getAllProposals: () => Promise<any[]>;
  getActiveProposals: () => Promise<any[]>;
  canExecute: (proposalId: string) => Promise<boolean>;
  hasVoted: (proposalId: string, voter: string) => Promise<boolean>;
  queueProposal: (proposalId: string) => Promise<TransactionResult>;
  executeProposal: (proposalId: string) => Promise<TransactionResult>;
  cancelProposal: (proposalId: string) => Promise<TransactionResult>;
}

interface UseSkillTokensReturn {
  skillTokens: SkillTokenInfo[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createSkillToken: (data: any) => Promise<TransactionResult>;
  updateSkillLevel: (tokenId: number, data: any) => Promise<TransactionResult>;
  endorseSkillToken: (tokenId: string, endorsementData: string) => Promise<TransactionResult>;
  renewSkillToken: (tokenId: string, newExpiryDate: number) => Promise<TransactionResult>;
  revokeSkillToken: (tokenId: string, reason: string) => Promise<TransactionResult>;
  getSkillEndorsements: (tokenId: string) => Promise<any[]>;
  markExpiredTokens: (tokenIds: string[]) => Promise<TransactionResult>;
  getTokensByCategory: (category: string, limit?: number) => Promise<any[]>;
  getTotalSkillsByCategory: (category: string) => Promise<number>;
}

interface UseJobPoolsReturn {
  jobPools: JobPoolInfo[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createJobPool: (data: any) => Promise<TransactionResult>;
  applyToPool: (poolId: number, skillTokenIds: number[]) => Promise<TransactionResult>;
  leavePool: (poolId: number) => Promise<TransactionResult>;
  selectCandidate: (poolId: string, candidateAddress: string) => Promise<TransactionResult>;
  completePool: (poolId: string) => Promise<TransactionResult>;
  closePool: (poolId: string) => Promise<TransactionResult>;
  calculateMatchScore: (poolId: string, candidateAddress: string) => Promise<number>;
  getPoolMetrics: (poolId: string) => Promise<any>;
  getGlobalStats: () => Promise<any>;
  getActivePoolsCount: () => Promise<number>;
  getTotalPoolsCount: () => Promise<number>;
}

interface UseReputationReturn {
  reputation: any;
  history: any[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  registerOracle: (stakeAmount: number, categories: string[]) => Promise<TransactionResult>;
  submitEvaluation: (userAddress: string, category: string, score: number, evidence: string) => Promise<TransactionResult>;
  challengeEvaluation: (evaluationId: string, reason: string, stakeAmount: number) => Promise<TransactionResult>;
  resolveChallenge: (challengeId: string, resolution: string) => Promise<TransactionResult>;
  slashOracle: (oracleAddress: string, reason: string) => Promise<TransactionResult>;
  withdrawOracleStake: (oracleAddress: string) => Promise<TransactionResult>;
  getOracleInfo: (oracleAddress: string) => Promise<any>;
  getActiveOracles: () => Promise<any[]>;
  getCategoryScore: (userAddress: string, category: string) => Promise<number>;
  getWorkEvaluation: (evaluationId: string) => Promise<any>;
  getUserEvaluations: (userAddress: string) => Promise<any[]>;
  getGlobalStats: () => Promise<any>;
}

interface UseGovernanceReturn {
  proposals: any[];
  activeProposals: any[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createProposal: (data: any) => Promise<TransactionResult>;
  castVote: (data: any) => Promise<TransactionResult>;
  delegateVotingPower: (delegatee: string) => Promise<TransactionResult>;
  undelegateVotingPower: () => Promise<TransactionResult>;
  getProposal: (id: string) => Promise<any>;
  getVotingPower: (address: string) => Promise<any>;
  getProposalStatus: (proposalId: string) => Promise<any>;
  getVoteReceipt: (proposalId: string, voter: string) => Promise<any>;
  getQuorum: () => Promise<number>;
  getVotingDelay: () => Promise<number>;
  getVotingPeriod: () => Promise<number>;
  getProposalThreshold: () => Promise<number>;
  getAllProposals: () => Promise<any[]>;
  getActiveProposals: () => Promise<any[]>;
  canExecute: (proposalId: string) => Promise<boolean>;
  hasVoted: (proposalId: string, voter: string) => Promise<boolean>;
  queueProposal: (proposalId: string) => Promise<TransactionResult>;
  executeProposal: (proposalId: string) => Promise<TransactionResult>;
  cancelProposal: (proposalId: string) => Promise<TransactionResult>;
}

/**
 * Main dashboard data hook - aggregates all dashboard information
 */
export function useDashboardData(): UseDashboardDataReturn {
  const { user, isConnected } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [skillTokens, setSkillTokens] = useState<SkillTokenInfo[]>([]);
  const [jobPools, setJobPools] = useState<JobPoolInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Enhanced functionality from the other hooks
  const {
    // Skills
    createSkillToken,
    updateSkillLevel,
    endorseSkillToken,
    renewSkillToken,
    revokeSkillToken,
    getSkillEndorsements,
    markExpiredTokens,
    getTokensByCategory,
    getTotalSkillsByCategory,
    isLoading: isLoadingSkills,
    error: skillsError,
    refetch: fetchSkillTokens
  } = useSkillTokens();

  const {
    // Job Pools
    createJobPool,
    applyToPool,
    leavePool,
    selectCandidate,
    completePool,
    closePool,
    calculateMatchScore,
    getPoolMetrics,
    getGlobalStats: getTalentPoolGlobalStats,
    getActivePoolsCount,
    getTotalPoolsCount,
    refetch: fetchJobPools,
    isLoading: isLoadingJobs,
    error: jobsError
  } = useJobPools();

  const {
    // Reputation
    reputation,
    history,
    isLoading: isLoadingReputation,
    error: reputationError,
    registerOracle,
    submitEvaluation,
    challengeEvaluation,
    resolveChallenge,
    slashOracle,
    withdrawOracleStake,
    getOracleInfo,
    getActiveOracles,
    getCategoryScore,
    getWorkEvaluation,
    getUserEvaluations,
    getGlobalStats,
    refetch: fetchReputation
  } = useReputation();

  // Governance functionality - implement directly since useGovernance doesn't exist
  const [proposals, setProposals] = useState<any[]>([]);
  const [activeProposals, setActiveProposals] = useState<any[]>([]);
  const [isLoadingGovernance, setIsLoadingGovernance] = useState(false);
  const [governanceError, setGovernanceError] = useState<string | null>(null);

  const fetchGovernanceData = useCallback(async () => {
    if (!isConnected || !user?.accountId) {
      return;
    }

    setIsLoadingGovernance(true);
    setGovernanceError(null);

    try {
      const [proposalsResponse, votingPowerResponse] = await Promise.all([
        apiClient.getProposals(1, 50),
        apiClient.getVotingPower(user.accountId)
      ]);

      if (proposalsResponse.success && proposalsResponse.data) {
        setProposals(proposalsResponse.data.items || []);
        setActiveProposals(proposalsResponse.data.items?.filter((p: any) => p.status === 'active') || []);
      }

      if (votingPowerResponse.success && votingPowerResponse.data) {
        // Handle voting power data
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch governance data';
      setGovernanceError(errorMessage);
      console.error('Governance fetch error:', err);
    } finally {
      setIsLoadingGovernance(false);
    }
  }, [isConnected, user?.accountId]);

  const createProposal = useCallback(async (data: any): Promise<TransactionResult> => {
    try {
      const response = await apiClient.createProposal(data);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to create proposal');
      }
    } catch (error) {
      console.error('Error creating proposal:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const castVote = useCallback(async (data: any): Promise<TransactionResult> => {
    try {
      const response = await apiClient.castVote(data);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to cast vote');
      }
    } catch (error) {
      console.error('Error casting vote:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const delegateVotingPower = useCallback(async (delegatee: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.delegateVotingPower({ delegatee });
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to delegate voting power');
      }
    } catch (error) {
      console.error('Error delegating voting power:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const undelegateVotingPower = useCallback(async (): Promise<TransactionResult> => {
    try {
      const response = await apiClient.undelegateVotingPower();
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to undelegate voting power');
      }
    } catch (error) {
      console.error('Error undeleting voting power:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const getProposal = useCallback(async (id: string): Promise<any> => {
    try {
      const response = await apiClient.getProposal(id);
      if (response.success && response.data) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error getting proposal:', error);
      return null;
    }
  }, []);

  const getVotingPower = useCallback(async (address: string): Promise<any> => {
    try {
      const response = await apiClient.getVotingPower(address);
      if (response.success && response.data) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error getting voting power:', error);
      return null;
    }
  }, []);

  // Add remaining governance methods
  const queueProposal = useCallback(async (proposalId: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.queueProposal(proposalId);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to queue proposal');
      }
    } catch (error) {
      console.error('Error queuing proposal:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const executeProposal = useCallback(async (proposalId: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.executeProposal(proposalId);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to execute proposal');
      }
    } catch (error) {
      console.error('Error executing proposal:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const cancelProposal = useCallback(async (proposalId: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.cancelProposal(proposalId);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to cancel proposal');
      }
    } catch (error) {
      console.error('Error canceling proposal:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const getProposalStatus = useCallback(async (proposalId: string): Promise<string> => {
    try {
      const response = await apiClient.getProposalStatus(proposalId);
      if (response.success && response.data) {
        return response.data.status || 'unknown';
      }
      return 'unknown';
    } catch (error) {
      console.error('Error getting proposal status:', error);
      return 'unknown';
    }
  }, []);

  const getVoteReceipt = useCallback(async (proposalId: string, voter: string): Promise<any> => {
    try {
      const response = await apiClient.getVoteReceipt(proposalId, voter);
      if (response.success && response.data) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error getting vote receipt:', error);
      return null;
    }
  }, []);

  const getQuorum = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getQuorum();
      if (response.success && response.data) {
        return response.data.quorum || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting quorum:', error);
      return 0;
    }
  }, []);

  const getVotingDelay = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getVotingDelay();
      if (response.success && response.data) {
        return response.data.voting_delay || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting voting delay:', error);
      return 0;
    }
  }, []);

  const getVotingPeriod = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getVotingPeriod();
      if (response.success && response.data) {
        return response.data.voting_period || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting voting period:', error);
      return 0;
    }
  }, []);

  const getProposalThreshold = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getProposalThreshold();
      if (response.success && response.data) {
        return response.data.proposal_threshold || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting proposal threshold:', error);
      return 0;
    }
  }, []);

  const getAllProposals = useCallback(async (): Promise<any[]> => {
    try {
      const response = await apiClient.getAllProposals();
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('Error getting all proposals:', error);
      return [];
    }
  }, []);

  const getActiveProposals = useCallback(async (): Promise<any[]> => {
    try {
      const response = await apiClient.getActiveProposals();
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('Error getting active proposals:', error);
      return [];
    }
  }, []);

  const canExecute = useCallback(async (proposalId: string): Promise<boolean> => {
    try {
      const response = await apiClient.canExecute(proposalId);
      if (response.success && response.data) {
        return response.data.can_execute || false;
      }
      return false;
    } catch (error) {
      console.error('Error checking if proposal can execute:', error);
      return false;
    }
  }, []);

  const hasVoted = useCallback(async (proposalId: string, voter: string): Promise<boolean> => {
    try {
      const response = await apiClient.hasVoted(proposalId, voter);
      if (response.success && response.data) {
        return response.data.has_voted || false;
      }
      return false;
    } catch (error) {
      console.error('Error checking if voter has voted:', error);
      return false;
    }
  }, []);

  const fetchDashboardData = useCallback(async () => {
    if (!isConnected || !user?.accountId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Fetch all data in parallel
      await Promise.all([
        fetchSkillTokens(),
        fetchJobPools(),
        // fetchReputation(), // Removed as per new_code
        // fetchGovernanceData() // Removed as per new_code
      ]);

      setLastUpdated(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch dashboard data';
      setError(errorMessage);
      console.error('Dashboard data fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, user?.accountId, fetchSkillTokens, fetchJobPools]); // Removed fetchReputation, fetchGovernanceData from dependencies

  // Auto-fetch on wallet connection
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Real-time updates integration
  useDashboardRealtimeSync(fetchDashboardData, [fetchDashboardData]);

  // Auto-refresh every 30 seconds when tab is visible (backup to real-time updates)
  useEffect(() => {
    if (!isConnected) return;

    let intervalId: ReturnType<typeof setInterval>;

    const handleVisibilityChange = () => {
      if (!document.hidden && isConnected) {
        intervalId = setInterval(fetchDashboardData, 60000); // Reduced to 60 seconds since we have real-time updates
      } else {
        clearInterval(intervalId);
      }
    };

    // Initial setup
    if (!document.hidden) {
      intervalId = setInterval(fetchDashboardData, 60000);
    }

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(intervalId);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isConnected, fetchDashboardData]);

  return {
    // Basic dashboard data
    stats,
    skillTokens,
    jobPools,
    isLoading,
    error,
    refetch: fetchDashboardData,
    lastUpdated,

    // Enhanced Skills functionality
    createSkillToken,
    updateSkillLevel,
    endorseSkillToken,
    renewSkillToken,
    revokeSkillToken,
    getSkillEndorsements,
    markExpiredTokens,
    getTokensByCategory,
    getTotalSkillsByCategory,
    isLoadingSkills,
    skillsError,

    // Enhanced Job Pools functionality
    createJobPool,
    applyToPool,
    leavePool,
    selectCandidate,
    completePool,
    closePool,
    calculateMatchScore,
    getPoolMetrics,
    getTalentPoolGlobalStats,
    getActivePoolsCount,
    getTotalPoolsCount,
    isLoadingJobs,
    jobsError,

    // Enhanced Reputation functionality
    reputation,
    history,
    isLoadingReputation,
    reputationError,
    registerOracle,
    submitEvaluation,
    challengeEvaluation,
    resolveChallenge,
    slashOracle,
    withdrawOracleStake,
    getOracleInfo,
    getActiveOracles,
    getCategoryScore,
    getWorkEvaluation,
    getUserEvaluations,
    getGlobalStats,

    // Enhanced Governance functionality
    proposals,
    activeProposals,
    isLoadingGovernance,
    governanceError,
    createProposal,
    castVote,
    delegateVotingPower,
    undelegateVotingPower,
    getProposal,
    getVotingPower,
    queueProposal,
    executeProposal,
    cancelProposal,
    getProposalStatus,
    getVoteReceipt,
    getQuorum,
    getVotingDelay,
    getVotingPeriod,
    getProposalThreshold,
    getAllProposals,
    getActiveProposals,
    canExecute,
    hasVoted
  };
}

/**
 * Skill tokens specific hook with CRUD operations
 */
export function useSkillTokens(): UseSkillTokensReturn {
  const { user, isConnected } = useAuth();
  const [skillTokens, setSkillTokens] = useState<SkillTokenInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSkillTokens = useCallback(async () => {
    if (!isConnected || !user?.accountId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.getSkillTokens(user.accountId);
      if (response.success && response.data) {
        setSkillTokens(response.data);
      } else {
        throw new Error(response.error || 'Failed to fetch skill tokens');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch skill tokens';
      setError(errorMessage);
      console.error('Skill tokens fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, user?.accountId]);

  const createSkillToken = useCallback(async (data: any): Promise<TransactionResult> => {
    if (!user?.accountId) {
      return { success: false, error: 'User not connected' };
    }

    try {
      const response = await apiClient.createSkillToken({
        recipient_address: user.accountId,
        skill_name: data.skill_category,
        skill_category: data.skill_category,
        level: data.level,
        description: data.description,
        metadata_uri: data.uri
      });

      if (response.success && response.data) {
        // Update local state
        setSkillTokens((prev: SkillTokenInfo[]) => [
          ...prev,
          {
            tokenId: parseInt(response.data!.token_id || response.data!.id),
            category: data.skill_category,
            level: data.level,
            uri: data.uri,
            owner: user.accountId
          }
        ]);
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to create skill token');
      }
    } catch (error) {
      console.error('Error creating skill token:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, [user?.accountId]);

  const updateSkillLevel = useCallback(async (
    tokenId: number,
    data: { new_level: number; evidence: string }
  ): Promise<TransactionResult> => {
    try {
      const response = await apiClient.updateSkillLevel(tokenId, data.new_level, data.evidence);

      if (response.success && response.data) {
        // Update local state
        setSkillTokens((prev: SkillTokenInfo[]) => prev.map((token: SkillTokenInfo) =>
          token.tokenId === tokenId
            ? { ...token, level: data.new_level }
            : token
        ));
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to update skill level');
      }
    } catch (error) {
      console.error('Error updating skill level:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  // Add missing skill token functionality
  const endorseSkillToken = useCallback(async (tokenId: string, endorsementData: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.endorseSkillToken(tokenId, endorsementData);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to endorse skill token');
      }
    } catch (error) {
      console.error('Error endorsing skill token:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const renewSkillToken = useCallback(async (tokenId: string, newExpiryDate: number): Promise<TransactionResult> => {
    try {
      const response = await apiClient.renewSkillToken(tokenId, newExpiryDate);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to renew skill token');
      }
    } catch (error) {
      console.error('Error renewing skill token:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const revokeSkillToken = useCallback(async (tokenId: string, reason: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.revokeSkillToken(tokenId, reason);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to revoke skill token');
      }
    } catch (error) {
      console.error('Error revoking skill token:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const getSkillEndorsements = useCallback(async (tokenId: string): Promise<any[]> => {
    try {
      const response = await apiClient.getSkillEndorsements(tokenId);
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('Error getting skill endorsements:', error);
      return [];
    }
  }, []);

  const markExpiredTokens = useCallback(async (tokenIds: string[]): Promise<TransactionResult> => {
    try {
      const response = await apiClient.markExpiredTokens(tokenIds);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to mark expired tokens');
      }
    } catch (error) {
      console.error('Error marking expired tokens:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const getTokensByCategory = useCallback(async (category: string, limit: number = 50): Promise<any[]> => {
    try {
      const response = await apiClient.getTokensByCategory(category, limit);
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('Error getting tokens by category:', error);
      return [];
    }
  }, []);

  const getTotalSkillsByCategory = useCallback(async (category: string): Promise<number> => {
    try {
      const response = await apiClient.getTotalSkillsByCategory(category);
      if (response.success && response.data) {
        return response.data.total_count || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting total skills by category:', error);
      return 0;
    }
  }, []);

  // Initial fetch and refetch on user change
  useEffect(() => {
    fetchSkillTokens();
  }, [fetchSkillTokens]);

  return {
    skillTokens,
    isLoading,
    error,
    refetch: fetchSkillTokens,
    createSkillToken,
    updateSkillLevel,
    endorseSkillToken,
    renewSkillToken,
    revokeSkillToken,
    getSkillEndorsements,
    markExpiredTokens,
    getTokensByCategory,
    getTotalSkillsByCategory,
  };
}

/**
 * Job pools specific hook with application operations
 */
export function useJobPools(): UseJobPoolsReturn {
  const { user, isConnected } = useAuth();
  const [jobPools, setJobPools] = useState<JobPoolInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchJobPools = useCallback(async () => {
    if (!isConnected || !user?.accountId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.getJobPools(1, 50);
      if (response.success && response.data) {
        setJobPools(response.data.items);
      } else {
        throw new Error(response.error || 'Failed to fetch job pools');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch job pools';
      setError(errorMessage);
      console.error('Job pools fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, user?.accountId]);

  const createJobPool = useCallback(async (data: any): Promise<TransactionResult> => {
    try {
      const response = await apiClient.createJobPool({
        title: data.title,
        description: data.description,
        jobType: data.job_type === 'full-time' ? 0 : data.job_type === 'part-time' ? 1 : data.job_type === 'contract' ? 2 : 3,
        requiredSkills: data.required_skills.map((skill: any) => skill.toString()),
        minimumLevels: data.required_skills.map(() => 1), // Default minimum level
        salaryMin: parseInt(data.salary) || 0,
        salaryMax: parseInt(data.salary) || 0,
        deadline: Math.floor(new Date(data.application_deadline || Date.now() + 30 * 24 * 60 * 60 * 1000).getTime() / 1000),
        location: data.location || 'Remote',
        isRemote: data.location === 'Remote',
        stakeAmount: parseInt(data.stake_amount) || 50000000 // 0.5 HBAR in tinybar
      });

      if (response.success && response.data) {
        // Update local state
        const newJobPool: JobPoolInfo = {
          id: parseInt(response.data!.pool_id || response.data!.id),
          title: data.title,
          company: data.company,
          description: data.description,
          requiredSkills: data.required_skills,
          salary: data.salary,
          duration: data.duration,
          stakeAmount: data.stake_amount || '50000000',
          status: 'active' as any,
          applicants: [],
          createdAt: Date.now()
        };

        setJobPools((prev: JobPoolInfo[]) => [...prev, newJobPool]);
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to create job pool');
      }
    } catch (error) {
      console.error('Error creating job pool:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const applyToPool = useCallback(async (
    poolId: number,
    skillTokenIds: number[]
  ): Promise<TransactionResult> => {
    try {
      const response = await apiClient.applyToPool({
        pool_id: poolId.toString(),
        candidate_address: user?.accountId || '',
        cover_letter: 'Application submitted via dashboard',
        resume_uri: 'https://example.com/resume',
        stake_amount: 50000000
      });
      if (response.success && response.data) {
        // Optimistically update the UI
        setJobPools((prev: JobPoolInfo[]) =>
          prev.map(pool =>
            pool.id === poolId
              ? { ...pool, applicants: [...pool.applicants, user?.accountId || ''] }
              : pool
          )
        );
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to apply to pool');
      }
    } catch (error) {
      console.error('Error applying to pool:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, [user?.accountId]);

  const leavePool = useCallback(async (poolId: number): Promise<TransactionResult> => {
    try {
      // For now, we'll just update local state since leaveJobPool doesn't exist
      // This would need to be implemented in the backend
      setJobPools((prev: JobPoolInfo[]) => prev.map((pool: JobPoolInfo) =>
        pool.id === poolId
          ? { ...pool, hasApplied: false }
          : pool
      ));
      return { success: true, transactionId: 'placeholder' };
    } catch (error) {
      console.error('Error leaving job pool:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  // Add missing functionality with placeholder implementations
  const selectCandidate = useCallback(async (poolId: string, candidateAddress: string): Promise<TransactionResult> => {
    try {
      console.log('Selecting candidate:', poolId, candidateAddress);
      return { success: true, transactionId: 'placeholder' };
    } catch (error) {
      console.error('Error selecting candidate:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const completePool = useCallback(async (poolId: string): Promise<TransactionResult> => {
    try {
      console.log('Completing pool:', poolId);
      return { success: true, transactionId: 'placeholder' };
    } catch (error) {
      console.error('Error completing pool:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const closePool = useCallback(async (poolId: string): Promise<TransactionResult> => {
    try {
      console.log('Closing pool:', poolId);
      return { success: true, transactionId: 'placeholder' };
    } catch (error) {
      console.error('Error closing pool:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const calculateMatchScore = useCallback(async (poolId: string, candidateAddress: string): Promise<number> => {
    try {
      console.log('Calculating match score for:', poolId, candidateAddress);
      return Math.floor(Math.random() * 100); // Placeholder
    } catch (error) {
      console.error('Error calculating match score:', error);
      return 0;
    }
  }, []);

  const getPoolMetrics = useCallback(async (poolId: string): Promise<any> => {
    try {
      const response = await apiClient.getPoolMetrics(poolId);
      if (response.success && response.data) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error getting pool metrics:', error);
      return null;
    }
  }, []);

  const getTalentPoolGlobalStats = useCallback(async (): Promise<any> => {
    try {
      const response = await apiClient.getTalentPoolGlobalStats();
      if (response.success && response.data) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error getting talent pool global stats:', error);
      return null;
    }
  }, []);

  const getActivePoolsCount = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getActivePoolsCount();
      if (response.success && response.data) {
        return response.data.active_count || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting active pools count:', error);
      return 0;
    }
  }, []);

  const getTotalPoolsCount = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getTotalPoolsCount();
      if (response.success && response.data) {
        return response.data.total_count || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting total pools count:', error);
      return 0;
    }
  }, []);

  // Initial fetch and refetch on user change
  useEffect(() => {
    fetchJobPools();
  }, [fetchJobPools]);

  return {
    jobPools,
    isLoading,
    error,
    refetch: fetchJobPools,
    createJobPool,
    applyToPool,
    leavePool,
    selectCandidate,
    completePool,
    closePool,
    calculateMatchScore,
    getPoolMetrics,
    getGlobalStats: getTalentPoolGlobalStats, // Renamed to avoid conflict with useReputation
    getActivePoolsCount,
    getTotalPoolsCount,
  };
}

/**
 * Reputation data hook
 */
export function useReputation(userId?: string) {
  const { user, isConnected } = useAuth();
  const targetUserId = userId || user?.accountId;

  const [reputation, setReputation] = useState<{
    overall_score: number;
    skill_scores: Record<string, number>;
    total_evaluations: number;
    last_updated: string;
  } | null>(null);

  const [history, setHistory] = useState<Array<{
    evaluation_id: string;
    timestamp: string;
    skill_category: string;
    score: number;
    feedback: string;
  }>>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReputation = useCallback(async () => {
    if (!isConnected || !user?.accountId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [reputationResponse, historyResponse] = await Promise.all([
        apiClient.getReputationScore(user.accountId),
        apiClient.getEvaluations(user.accountId),
      ]);

      if (reputationResponse.success && reputationResponse.data) {
        setReputation(reputationResponse.data);
      }

      if (historyResponse.success && historyResponse.data) {
        setHistory(historyResponse.data);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch reputation data';
      setError(errorMessage);
      console.error('Reputation fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, user?.accountId]);

  // Add missing reputation functionality
  const registerOracle = useCallback(async (stakeAmount: number, categories: string[]): Promise<TransactionResult> => {
    try {
      const response = await apiClient.registerOracle({ name: 'Oracle', specializations: categories, stakeAmount });
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to register oracle');
      }
    } catch (error) {
      console.error('Error registering oracle:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const submitEvaluation = useCallback(async (userAddress: string, category: string, score: number, evidence: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.submitEvaluation({
        user: userAddress,
        skillTokenIds: [],
        workDescription: `Evaluation for ${category}`,
        workContent: evidence,
        overallScore: score,
        skillScores: { [category]: score },
        feedback: evidence
      });
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to submit evaluation');
      }
    } catch (error) {
      console.error('Error submitting evaluation:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const challengeEvaluation = useCallback(async (evaluationId: string, reason: string, stakeAmount: number): Promise<TransactionResult> => {
    try {
      const response = await apiClient.challengeEvaluation(evaluationId, reason, stakeAmount);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to challenge evaluation');
      }
    } catch (error) {
      console.error('Error challenging evaluation:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const resolveChallenge = useCallback(async (challengeId: string, resolution: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.resolveChallenge(challengeId, resolution);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to resolve challenge');
      }
    } catch (error) {
      console.error('Error resolving challenge:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const slashOracle = useCallback(async (oracleAddress: string, reason: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.slashOracle(oracleAddress, reason);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to slash oracle');
      }
    } catch (error) {
      console.error('Error slashing oracle:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const withdrawOracleStake = useCallback(async (oracleAddress: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.withdrawOracleStake(oracleAddress);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to withdraw oracle stake');
      }
    } catch (error) {
      console.error('Error withdrawing oracle stake:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const getOracleInfo = useCallback(async (oracleAddress: string): Promise<any> => {
    try {
      const response = await apiClient.getOracleInfo(oracleAddress);
      if (response.success && response.data) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error getting oracle info:', error);
      return null;
    }
  }, []);

  const getActiveOracles = useCallback(async (): Promise<any[]> => {
    try {
      const response = await apiClient.getActiveOracles();
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('Error getting active oracles:', error);
      return [];
    }
  }, []);

  const getCategoryScore = useCallback(async (userAddress: string, category: string): Promise<number> => {
    try {
      const response = await apiClient.getCategoryScore(userAddress, category);
      if (response.success && response.data) {
        return response.data.score || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting category score:', error);
      return 0;
    }
  }, []);

  const getWorkEvaluation = useCallback(async (evaluationId: string): Promise<any> => {
    try {
      const response = await apiClient.getWorkEvaluation(evaluationId);
      if (response.success && response.data) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error getting work evaluation:', error);
      return null;
    }
  }, []);

  const getUserEvaluations = useCallback(async (userAddress: string): Promise<any[]> => {
    try {
      const response = await apiClient.getUserEvaluations(userAddress);
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('Error getting user evaluations:', error);
      return [];
    }
  }, []);

  const getGlobalStats = useCallback(async (): Promise<any> => {
    try {
      const response = await apiClient.getGlobalStats();
      if (response.success && response.data) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error getting global stats:', error);
      return null;
    }
  }, []);

  // Add missing governance functionality
  const queueProposal = useCallback(async (proposalId: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.queueProposal(proposalId);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to queue proposal');
      }
    } catch (error) {
      console.error('Error queuing proposal:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const executeProposal = useCallback(async (proposalId: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.executeProposal(proposalId);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to execute proposal');
      }
    } catch (error) {
      console.error('Error executing proposal:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const cancelProposal = useCallback(async (proposalId: string): Promise<TransactionResult> => {
    try {
      const response = await apiClient.cancelProposal(proposalId);
      if (response.success && response.data) {
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to cancel proposal');
      }
    } catch (error) {
      console.error('Error canceling proposal:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const getProposalStatus = useCallback(async (proposalId: string): Promise<string> => {
    try {
      const response = await apiClient.getProposalStatus(proposalId);
      if (response.success && response.data) {
        return response.data.status || 'unknown';
      }
      return 'unknown';
    } catch (error) {
      console.error('Error getting proposal status:', error);
      return 'unknown';
    }
  }, []);

  const getVoteReceipt = useCallback(async (proposalId: string, voter: string): Promise<any> => {
    try {
      const response = await apiClient.getVoteReceipt(proposalId, voter);
      if (response.success && response.data) {
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Error getting vote receipt:', error);
      return null;
    }
  }, []);

  const getQuorum = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getQuorum();
      if (response.success && response.data) {
        return response.data.quorum || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting quorum:', error);
      return 0;
    }
  }, []);

  const getVotingDelay = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getVotingDelay();
      if (response.success && response.data) {
        return response.data.voting_delay || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting voting delay:', error);
      return 0;
    }
  }, []);

  const getVotingPeriod = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getVotingPeriod();
      if (response.success && response.data) {
        return response.data.voting_period || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting voting period:', error);
      return 0;
    }
  }, []);

  const getProposalThreshold = useCallback(async (): Promise<number> => {
    try {
      const response = await apiClient.getProposalThreshold();
      if (response.success && response.data) {
        return response.data.proposal_threshold || 0;
      }
      return 0;
    } catch (error) {
      console.error('Error getting proposal threshold:', error);
      return 0;
    }
  }, []);

  const getAllProposals = useCallback(async (): Promise<any[]> => {
    try {
      const response = await apiClient.getAllProposals();
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('Error getting all proposals:', error);
      return [];
    }
  }, []);

  const getActiveProposals = useCallback(async (): Promise<any[]> => {
    try {
      const response = await apiClient.getActiveProposals();
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    } catch (error) {
      console.error('Error getting active proposals:', error);
      return [];
    }
  }, []);

  const canExecute = useCallback(async (proposalId: string): Promise<boolean> => {
    try {
      const response = await apiClient.canExecute(proposalId);
      if (response.success && response.data) {
        return response.data.can_execute || false;
      }
      return false;
    } catch (error) {
      console.error('Error checking if proposal can execute:', error);
      return false;
    }
  }, []);

  const hasVoted = useCallback(async (proposalId: string, voter: string): Promise<boolean> => {
    try {
      const response = await apiClient.hasVoted(proposalId, voter);
      if (response.success && response.data) {
        return response.data.has_voted || false;
      }
      return false;
    } catch (error) {
      console.error('Error checking if voter has voted:', error);
      return false;
    }
  }, []);

  useEffect(() => {
    fetchReputation();
  }, [fetchReputation]);

  return {
    reputation,
    history,
    isLoading,
    error,
    refetch: fetchReputation,
    registerOracle,
    submitEvaluation,
    challengeEvaluation,
    resolveChallenge,
    slashOracle,
    withdrawOracleStake,
    getOracleInfo,
    getActiveOracles,
    getCategoryScore,
    getWorkEvaluation,
    getUserEvaluations,
    getGlobalStats
  };
}
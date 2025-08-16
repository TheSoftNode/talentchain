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
  stats: DashboardStats | null;
  skillTokens: SkillTokenInfo[];
  jobPools: JobPoolInfo[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  lastUpdated: Date | null;
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
  submitWorkEvaluation: (data: any) => Promise<TransactionResult>;
  getReputationScore: (userAddress: string) => Promise<any>;
  getCategoryScore: (userAddress: string, category: string) => Promise<any>;
  getWorkEvaluation: (evaluationId: string) => Promise<any>;
  getUserEvaluations: (userAddress: string) => Promise<any[]>;
  getGlobalStats: () => Promise<any>;
  registerOracle: (data: any) => Promise<TransactionResult>;
  resolveChallenge: (challengeId: string, resolution: string) => Promise<TransactionResult>;
  slashOracle: (oracleAddress: string, reason: string) => Promise<TransactionResult>;
  withdrawOracleStake: (oracleAddress: string) => Promise<TransactionResult>;
  getOraclePerformance: (oracleAddress: string) => Promise<any>;
  updateOracleStatus: (oracleAddress: string, isActive: boolean, reason: string) => Promise<TransactionResult>;
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

  const fetchDashboardData = useCallback(async () => {
    if (!isConnected || !user?.accountId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Fetch skill tokens
      const skillsResponse = await apiClient.getSkillTokens(user.accountId);
      if (skillsResponse.success && skillsResponse.data) {
        setSkillTokens(skillsResponse.data);
      } else {
        console.warn('Failed to fetch skill tokens:', skillsResponse.error);
        setSkillTokens([]);
      }

      // Fetch job pools (both created by user and applied to)
      const poolsResponse = await apiClient.getJobPools(1, 20);
      if (poolsResponse.success && poolsResponse.data) {
        setJobPools(poolsResponse.data.items);
      } else {
        console.warn('Failed to fetch job pools:', poolsResponse.error);
        setJobPools([]);
      }

      setLastUpdated(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch dashboard data';
      setError(errorMessage);
      console.error('Dashboard data fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, user?.accountId]);

  // Auto-fetch on wallet connection
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Real-time updates integration
  useDashboardRealtimeSync(fetchDashboardData, [fetchDashboardData]);

  // Auto-refresh every 30 seconds when tab is visible (backup to real-time updates)
  useEffect(() => {
    if (!isConnected) return;

    let intervalId: NodeJS.Timeout;

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
    stats,
    skillTokens,
    jobPools,
    isLoading,
    error,
    refetch: fetchDashboardData,
    lastUpdated,
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
      // This would need to be added to the backend API - for now return placeholder
      console.log('Endorsing skill token:', tokenId, endorsementData);
      return { success: true, transactionId: 'placeholder' };
    } catch (error) {
      console.error('Error endorsing skill token:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const renewSkillToken = useCallback(async (tokenId: string, newExpiryDate: number): Promise<TransactionResult> => {
    try {
      // This would need to be added to the backend API - for now return placeholder
      console.log('Renewing skill token:', tokenId, newExpiryDate);
      return { success: true, transactionId: 'placeholder' };
    } catch (error) {
      console.error('Error renewing skill token:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const revokeSkillToken = useCallback(async (tokenId: string, reason: string): Promise<TransactionResult> => {
    try {
      // This would need to be added to the backend API - for now return placeholder
      console.log('Revoking skill token:', tokenId, reason);
      return { success: true, transactionId: 'placeholder' };
    } catch (error) {
      console.error('Error revoking skill token:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const getSkillEndorsements = useCallback(async (tokenId: string): Promise<any[]> => {
    try {
      // This would need to be added to the backend API - for now return placeholder
      console.log('Getting skill endorsements for:', tokenId);
      return [];
    } catch (error) {
      console.error('Error getting skill endorsements:', error);
      return [];
    }
  }, []);

  const markExpiredTokens = useCallback(async (tokenIds: string[]): Promise<TransactionResult> => {
    try {
      // This would need to be added to the backend API - for now return placeholder
      console.log('Marking expired tokens:', tokenIds);
      return { success: true, transactionId: 'placeholder' };
    } catch (error) {
      console.error('Error marking expired tokens:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }, []);

  const getTokensByCategory = useCallback(async (category: string, limit: number = 50): Promise<any[]> => {
    try {
      // This would need to be added to the backend API - for now return placeholder
      console.log('Getting tokens by category:', category, limit);
      return [];
    } catch (error) {
      console.error('Error getting tokens by category:', error);
      return [];
    }
  }, []);

  const getTotalSkillsByCategory = useCallback(async (category: string): Promise<number> => {
    try {
      // This would need to be added to the backend API - for now return placeholder
      console.log('Getting total skills by category:', category);
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
        poolId: poolId,
        applicantAddress: user?.accountId || '',
        expectedSalary: 0,
        availabilityDate: Math.floor(Date.now() / 1000),
        coverLetter: '',
        stakeAmount: 50000000 // 0.5 HBAR in tinybar
      });

      if (response.success && response.data) {
        // Update local state to show application
        setJobPools((prev: JobPoolInfo[]) => prev.map((pool: JobPoolInfo) =>
          pool.id === poolId
            ? { ...pool, hasApplied: true }
            : pool
        ));
        return { success: true, transactionId: response.data!.transaction_id };
      } else {
        throw new Error(response.error || 'Failed to apply to job pool');
      }
    } catch (error) {
      console.error('Error applying to job pool:', error);
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
      console.log('Getting pool metrics for:', poolId);
      return { applications: 0, matchScore: 0, status: 'active' };
    } catch (error) {
      console.error('Error getting pool metrics:', error);
      return {};
    }
  }, []);

  const getGlobalStats = useCallback(async (): Promise<any> => {
    try {
      console.log('Getting global stats');
      return { totalPools: jobPools.length, activePools: jobPools.filter(p => p.status === 'active').length };
    } catch (error) {
      console.error('Error getting global stats:', error);
      return {};
    }
  }, [jobPools]);

  const getActivePoolsCount = useCallback(async (): Promise<number> => {
    try {
      return jobPools.filter(pool => pool.status === 'active').length;
    } catch (error) {
      console.error('Error getting active pools count:', error);
      return 0;
    }
  }, [jobPools]);

  const getTotalPoolsCount = useCallback(async (): Promise<number> => {
    try {
      return jobPools.length;
    } catch (error) {
      console.error('Error getting total pools count:', error);
      return 0;
    }
  }, [jobPools]);

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
    getGlobalStats,
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

  useEffect(() => {
    fetchReputation();
  }, [fetchReputation]);

  return {
    reputation,
    history,
    isLoading,
    error,
    refetch: fetchReputation,
  };
}
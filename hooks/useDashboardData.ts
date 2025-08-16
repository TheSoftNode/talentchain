/**
 * Custom hooks for dashboard data management with caching and error handling
 */

import { useState, useEffect, useCallback } from 'react';
import {
    DashboardStats,
    SkillTokenInfo,
    JobPoolInfo,
    TransactionResult
} from '@/lib/types/wallet';
import { api } from '@/lib/api/client';
import { useAuth } from './useAuth';

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
}

interface UseJobPoolsReturn {
    jobPools: JobPoolInfo[];
    isLoading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
    createJobPool: (data: any) => Promise<TransactionResult>;
    applyToPool: (poolId: number, skillTokenIds: number[]) => Promise<TransactionResult>;
    leavePool: (poolId: number) => Promise<TransactionResult>;
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
            // Fetch dashboard stats
            const statsResponse = await api.dashboard.getDashboardStats(user.accountId);
            if (statsResponse.success && statsResponse.data) {
                setStats(statsResponse.data);
            } else {
                throw new Error(statsResponse.error || 'Failed to fetch dashboard stats');
            }

            // Fetch skill tokens
            const skillsResponse = await api.skills.getUserSkillTokens(user.accountId);
            if (skillsResponse.success && skillsResponse.data) {
                setSkillTokens(skillsResponse.data);
            } else {
                console.warn('Failed to fetch skill tokens:', skillsResponse.error);
                setSkillTokens([]);
            }

            // Fetch job pools (both created by user and applied to)
            const poolsResponse = await api.talentPools.getJobPools({ page: 0, size: 20 });
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

    // Initial fetch and refetch on user change
    useEffect(() => {
        fetchDashboardData();
    }, [fetchDashboardData]);

    // Auto-refresh every 30 seconds when tab is visible
    useEffect(() => {
        if (!isConnected) return;

        let intervalId: ReturnType<typeof setInterval>;

        const handleVisibilityChange = () => {
            if (!document.hidden && isConnected) {
                intervalId = setInterval(fetchDashboardData, 30000); // 30 seconds
            } else {
                clearInterval(intervalId);
            }
        };

        // Initial setup
        if (!document.hidden) {
            intervalId = setInterval(fetchDashboardData, 30000);
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
 * Hook for managing skill tokens
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
            const response = await api.skills.getUserSkillTokens(user.accountId);
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
            const response = await api.skills.createSkillToken({
                recipient: user.accountId,
                skill_data: {
                    category: data.skill_category,
                    subcategory: data.skill_category,
                    level: data.level,
                    expiry_date: Math.floor(Date.now() / 1000) + (365 * 24 * 60 * 60), // 1 year from now
                    metadata: {
                        description: data.description,
                        evidence: data.evidence
                    }
                },
                token_uri: data.uri
            });

            if (response.success && response.data) {
                // Update local state
                setSkillTokens((prev: SkillTokenInfo[]) => [
                    ...prev,
                    {
                        tokenId: parseInt(response.data!.token_id),
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
            const response = await api.skills.updateSkillLevel(tokenId.toString(), data.new_level, data.evidence);

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
    };
}

/**
 * Hook for managing job pools
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
            const response = await api.talentPools.getJobPools({ page: 0, size: 50 });
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
            const response = await api.talentPools.createJobPool({
                title: data.title,
                description: data.description,
                job_type: data.job_type || 'full-time',
                required_skills: data.required_skills.map((skill: any) => skill.toString()),
                minimum_levels: data.required_skills.map(() => 1), // Default minimum level
                salary_min: parseInt(data.salary) || 0,
                salary_max: parseInt(data.salary) || 0,
                deadline: Math.floor(new Date(data.application_deadline || Date.now() + 30 * 24 * 60 * 60 * 1000).getTime() / 1000),
                location: data.location || 'Remote',
                is_remote: data.location === 'Remote'
            });

            if (response.success && response.data) {
                // Update local state
                setJobPools((prev: JobPoolInfo[]) => [
                    ...prev,
                    {
                        id: parseInt(response.data!.pool_id),
                        title: data.title,
                        company: data.company,
                        description: data.description,
                        required_skills: data.required_skills,
                        salary: data.salary,
                        duration: data.duration,
                        stake_amount: data.stake_amount,
                        status: 'active'
                    }
                ]);
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
            const response = await api.talentPools.applyToPool({
                pool_id: poolId.toString(),
                skill_token_ids: skillTokenIds.map(id => id.toString()),
                cover_letter: '',
                portfolio: ''
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
    }, []);

    const leavePool = useCallback(async (poolId: number): Promise<TransactionResult> => {
        try {
            const response = await api.talentPools.withdrawApplication(poolId.toString());

            if (response.success && response.data) {
                // Update local state to remove application
                setJobPools((prev: JobPoolInfo[]) => prev.map((pool: JobPoolInfo) =>
                    pool.id === poolId
                        ? { ...pool, hasApplied: false }
                        : pool
                ));
                return { success: true, transactionId: response.data!.transaction_id };
            } else {
                throw new Error(response.error || 'Failed to leave job pool');
            }
        } catch (error) {
            console.error('Error leaving job pool:', error);
            return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
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
    };
}

/**
 * Hook for managing reputation data
 */
export function useReputation(): {
    reputation: any;
    history: any[];
    isLoading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
} {
    const { user, isConnected } = useAuth();
    const [reputation, setReputation] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
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
                api.reputation.getReputationScore(user.accountId),
                api.reputation.getUserEvaluations(user.accountId),
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

    // Initial fetch and refetch on user change
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

/**
 * Hook for managing governance data
 */
export function useGovernance(): {
    proposals: any[];
    activeProposals: any[];
    isLoading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
    createProposal: (data: any) => Promise<TransactionResult>;
    castVote: (data: any) => Promise<TransactionResult>;
    getProposalStatus: (proposalId: string) => Promise<any>;
    canExecute: (proposalId: string) => Promise<boolean>;
    hasVoted: (proposalId: string) => Promise<boolean>;
} {
    const { user, isConnected } = useAuth();
    const [proposals, setProposals] = useState<any[]>([]);
    const [activeProposals, setActiveProposals] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchGovernanceData = useCallback(async () => {
        if (!isConnected || !user?.accountId) {
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const [allProposalsResponse, activeProposalsResponse] = await Promise.all([
                api.governance.getAllProposals(),
                api.governance.getActiveProposals(),
            ]);

            if (allProposalsResponse.success && allProposalsResponse.data) {
                setProposals(allProposalsResponse.data);
            }

            if (activeProposalsResponse.success && activeProposalsResponse.data) {
                setActiveProposals(activeProposalsResponse.data);
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to fetch governance data';
            setError(errorMessage);
            console.error('Governance fetch error:', err);
        } finally {
            setIsLoading(false);
        }
    }, [isConnected, user?.accountId]);

    const createProposal = useCallback(async (data: any): Promise<TransactionResult> => {
        try {
            const response = await api.governance.createProposal({
                title: data.title,
                description: data.description,
                targets: data.targets || [],
                values: data.values || [],
                calldatas: data.calldatas || [],
                ipfs_hash: data.ipfs_hash || ''
            });

            if (response.success && response.data) {
                // Refresh governance data
                await fetchGovernanceData();
                return { success: true, transactionId: response.data!.transaction_id };
            } else {
                throw new Error(response.error || 'Failed to create proposal');
            }
        } catch (error) {
            console.error('Error creating proposal:', error);
            return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
        }
    }, [fetchGovernanceData]);

    const castVote = useCallback(async (data: any): Promise<TransactionResult> => {
        try {
            const response = await api.governance.castVote({
                proposal_id: data.proposal_id,
                vote: data.vote,
                reason: data.reason
            });

            if (response.success && response.data) {
                // Refresh governance data
                await fetchGovernanceData();
                return { success: true, transactionId: response.data!.transaction_id };
            } else {
                throw new Error(response.error || 'Failed to cast vote');
            }
        } catch (error) {
            console.error('Error casting vote:', error);
            return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
        }
    }, [fetchGovernanceData]);

    const getProposalStatus = useCallback(async (proposalId: string): Promise<any> => {
        try {
            const response = await api.governance.getProposalStatus(proposalId);
            if (response.success && response.data) {
                return response.data;
            }
            throw new Error(response.error || 'Failed to get proposal status');
        } catch (error) {
            console.error('Error getting proposal status:', error);
            return null;
        }
    }, []);

    const canExecute = useCallback(async (proposalId: string): Promise<boolean> => {
        try {
            const response = await api.governance.canExecute(proposalId);
            if (response.success && response.data) {
                return response.data.can_execute;
            }
            return false;
        } catch (error) {
            console.error('Error checking if proposal can execute:', error);
            return false;
        }
    }, []);

    const hasVoted = useCallback(async (proposalId: string): Promise<boolean> => {
        if (!user?.accountId) return false;

        try {
            const response = await api.governance.hasVoted(proposalId, user.accountId);
            if (response.success && response.data) {
                return response.data.has_voted;
            }
            return false;
        } catch (error) {
            console.error('Error checking if user has voted:', error);
            return false;
        }
    }, [user?.accountId]);

    // Initial fetch and refetch on user change
    useEffect(() => {
        fetchGovernanceData();
    }, [fetchGovernanceData]);

    return {
        proposals,
        activeProposals,
        isLoading,
        error,
        refetch: fetchGovernanceData,
        createProposal,
        castVote,
        getProposalStatus,
        canExecute,
        hasVoted,
    };
}

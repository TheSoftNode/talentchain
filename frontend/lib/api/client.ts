/**
 * TalentChain Pro Unified API Client
 * 
 * This module provides a comprehensive client for interacting with the backend API,
 * including authentication, contract operations, and error handling.
 */

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Response Types
export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

export interface PaginatedApiResponse<T> extends ApiResponse<{
    items: T[];
    total: number;
    page: number;
    size: number;
    hasNext: boolean;
    hasPrevious: boolean;
}> { }

// Error Types
export class ApiError extends Error {
    constructor(
        message: string,
        public status: number,
        public code?: string
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

// Authentication Types
export interface AuthContext {
    user_address: string;
    user_id?: string;
    permissions: string[];
    authenticated_at: string;
}

// Request Types (simplified for now)
export interface CreateProposalRequest {
    title: string;
    description: string;
    targets: string[];
    values: number[];
    calldatas: string[];
    ipfsHash: string;
}

export interface CastVoteRequest {
    proposalId: number;
    vote: number; // 0 = against, 1 = for, 2 = abstain
    reason?: string;
}

export interface DelegateVotesRequest {
    delegatee: string;
}

export interface RegisterOracleRequest {
    name: string;
    specializations: string[];
    stakeAmount: number;
}

export interface SubmitEvaluationRequest {
    user: string;
    skillTokenIds: number[];
    workDescription: string;
    workContent: string;
    overallScore: number;
    skillScores: Record<string, number>;
    feedback: string;
    evidence?: string;
}

export interface CreateSkillTokenRequest {
    recipient_address: string;
    skill_name: string;
    skill_category: string;
    level: number;
    description: string;
    metadata_uri: string;
}

export interface CreateJobPoolRequest {
    title: string;
    description: string;
    jobType: number;
    requiredSkills: string[];
    minimumLevels: number[];
    salaryMin: number;
    salaryMax: number;
    deadline: number;
    location: string;
    isRemote: boolean;
    stakeAmount: number;
}

export interface ApplyToPoolRequest {
    pool_id: string;
    candidate_address: string;
    cover_letter: string;
    resume_uri: string;
    stake_amount: number;
}

export interface WorkEvaluationRequest {
    token_id: string;
    work_description: string;
    quality_score: number;
    evidence_uri: string;
    evaluator_address: string;
}

// Governance Types
export interface GovernanceProposal {
    id: number;
    title: string;
    description: string;
    proposer: string;
    targets: string[];
    values: number[];
    calldatas: string[];
    proposalType: number;
    status: string;
    created: number;
    deadline: number;
    executed: boolean;
    canceled: boolean;
    forVotes: number;
    againstVotes: number;
    abstainVotes: number;
}

export interface EmergencyProposal extends GovernanceProposal {
    justification: string;
    emergencyType: number;
}

export interface VoteRecord {
    proposalId: number;
    voter: string;
    support: number;
    reason: string;
    timestamp: number;
    vote: string; // 'FOR', 'AGAINST', 'ABSTAIN'
    votingPower: number;
}

export interface GovernanceMetrics {
    totalProposals: number;
    activeProposals: number;
    totalVoters: number;
    totalVotingPower: number;
    participationRate: number;
    averageParticipation: number;
}

export interface GovernanceSettings {
    votingDelay: number;
    votingPeriod: number;
    proposalThreshold: number;
    quorumVotes: number;
    emergencyVotingPeriod: number;
}

// Reputation Types
export interface WorkEvaluation {
    id: number;
    oracleAddress: string;
    userAddress: string;
    workId: string;
    score: number;
    ipfsHash: string;
    evaluationType: number;
    status: string;
    created: number;
    updated: number;
}

export interface OracleInfo {
    address: string;
    name: string;
    specializations: string[];
    stakeAmount: number;
    isActive: boolean;
    totalEvaluations: number;
    averageScore: number;
    registered: number;
}

export interface Challenge {
    id: number;
    evaluationId: number;
    challenger: string;
    reason: string;
    stakeAmount: number;
    status: string;
    created: number;
    resolved: number;
}

export interface ReputationScore {
    userAddress: string;
    category: string;
    score: number;
    lastUpdated: number;
    totalEvaluations: number;
    averageScore: number;
}

// API Client Class
export class TalentChainApiClient {
    private baseUrl: string;
    private authToken: string | null = null;
    private walletAddress: string | null = null;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
        this.loadAuthFromStorage();
    }

    // Authentication Methods
    setAuthToken(token: string) {
        this.authToken = token;
        localStorage.setItem('talentchain_auth_token', token);
    }

    setWalletAddress(address: string) {
        this.walletAddress = address;
        localStorage.setItem('talentchain_wallet_address', address);
    }

    clearAuth() {
        this.authToken = null;
        this.walletAddress = null;
        localStorage.removeItem('talentchain_auth_token');
        localStorage.removeItem('talentchain_wallet_address');
    }

    private loadAuthFromStorage() {
        this.authToken = localStorage.getItem('talentchain_auth_token');
        this.walletAddress = localStorage.getItem('talentchain_wallet_address');
    }

    // Request Helper Methods
    private async makeRequest<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        // Prepare headers
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };

        // Add authentication headers
        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }

        if (this.walletAddress) {
            headers['X-Wallet-Address'] = this.walletAddress;
        }

        // Merge with existing headers
        if (options.headers) {
            Object.assign(headers, options.headers);
        }

        // Prepare request options
        const requestOptions: RequestInit = {
            ...options,
            headers,
        };

        try {
            const response = await fetch(url, requestOptions);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new ApiError(
                    errorData.detail || `HTTP ${response.status}`,
                    response.status,
                    errorData.code
                );
            }

            const data = await response.json();
            return data;
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError(
                error instanceof Error ? error.message : 'Network error',
                0
            );
        }
    }

    // Health Check Methods
    async checkHealth(): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/health');
    }

    async checkContractHealth(): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/health/contracts');
    }

    // Governance Methods
    async createProposal(request: CreateProposalRequest): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/governance/create-proposal', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async castVote(request: CastVoteRequest): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/governance/cast-vote', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async delegateVotingPower(request: DelegateVotesRequest): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/governance/delegate', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async undelegateVotingPower(): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/governance/undelegate', {
            method: 'POST',
        });
    }

    async getProposals(page: number = 1, size: number = 10): Promise<PaginatedApiResponse<any>> {
        const endpoint = `/api/v1/governance/proposals?page=${page}&size=${size}`;
        return this.makeRequest<PaginatedApiResponse<any>>(endpoint);
    }

    async getProposal(id: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/governance/proposals/${id}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getVotingPower(address: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/governance/voting-power/${address}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    // Reputation Methods
    async registerOracle(request: RegisterOracleRequest): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/reputation/register-oracle', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async submitEvaluation(request: SubmitEvaluationRequest): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/reputation/submit-evaluation', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async updateReputationScore(userAddress: string, category: string, newScore: number, evidence: string): Promise<ApiResponse> {
        const request = { user: userAddress, category, new_score: newScore, evidence };
        return this.makeRequest<ApiResponse>('/api/v1/reputation/update-score', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getReputationScore(address: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/reputation/score/${address}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getEvaluations(address: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/reputation/evaluations/${address}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    // Skills Methods
    async createSkillToken(request: CreateSkillTokenRequest): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/skills/create-token', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async updateSkillLevel(tokenId: number, newLevel: number, metadataUri: string): Promise<ApiResponse> {
        const request = { token_id: tokenId, new_level: newLevel, new_metadata_uri: metadataUri };
        return this.makeRequest<ApiResponse>('/api/v1/skills/update-level', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getSkillTokens(address: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/skills/tokens/${address}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getSkillToken(id: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/skills/tokens/${id}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    // Enhanced Skills Methods - Missing from original
    async endorseSkillToken(tokenId: string, endorsementData: string): Promise<ApiResponse> {
        const request = { token_id: tokenId, endorsement_data: endorsementData };
        return this.makeRequest<ApiResponse>('/api/v1/skills/endorse', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async renewSkillToken(tokenId: string, newExpiryDate: number): Promise<ApiResponse> {
        const request = { token_id: tokenId, new_expiry_date: newExpiryDate };
        return this.makeRequest<ApiResponse>('/api/v1/skills/renew', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async revokeSkillToken(tokenId: string, reason: string): Promise<ApiResponse> {
        const request = { token_id: tokenId, reason };
        return this.makeRequest<ApiResponse>('/api/v1/skills/revoke', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getSkillEndorsements(tokenId: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/skills/${tokenId}/endorsements`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async markExpiredTokens(tokenIds: string[]): Promise<ApiResponse> {
        const request = { token_ids: tokenIds };
        return this.makeRequest<ApiResponse>('/api/v1/skills/mark-expired', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getTokensByCategory(category: string, limit: number = 50): Promise<ApiResponse> {
        const endpoint = `/api/v1/skills/category/${category}?limit=${limit}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getTotalSkillsByCategory(category: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/skills/category/${category}/total`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async batchCreateSkillTokens(requests: CreateSkillTokenRequest[]): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/skills/batch-create', {
            method: 'POST',
            body: JSON.stringify({ requests }),
        });
    }

    async submitWorkEvaluation(request: WorkEvaluationRequest): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/skills/work-evaluation', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    // Enhanced Reputation Methods - Missing from original
    async challengeEvaluation(evaluationId: string, reason: string, stakeAmount: number): Promise<ApiResponse> {
        const request = { evaluation_id: evaluationId, reason, stake_amount: stakeAmount };
        return this.makeRequest<ApiResponse>('/api/v1/reputation/challenge', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async resolveChallenge(challengeId: string, resolution: string): Promise<ApiResponse> {
        const request = { challenge_id: challengeId, resolution };
        return this.makeRequest<ApiResponse>('/api/v1/reputation/resolve-challenge', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async slashOracle(oracleAddress: string, reason: string): Promise<ApiResponse> {
        const request = { oracle_address: oracleAddress, reason };
        return this.makeRequest<ApiResponse>('/api/v1/reputation/slash-oracle', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async withdrawOracleStake(oracleAddress: string): Promise<ApiResponse> {
        const request = { oracle_address: oracleAddress };
        return this.makeRequest<ApiResponse>('/api/v1/reputation/withdraw-stake', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getOracleInfo(oracleAddress: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/reputation/oracle/${oracleAddress}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getActiveOracles(): Promise<ApiResponse> {
        const endpoint = '/api/v1/reputation/oracles/active';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getCategoryScore(userAddress: string, category: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/reputation/category/${userAddress}/${category}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getWorkEvaluation(evaluationId: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/reputation/evaluation/${evaluationId}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getUserEvaluations(userAddress: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/reputation/user/${userAddress}/evaluations`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getGlobalStats(): Promise<ApiResponse> {
        const endpoint = '/api/v1/reputation/stats/global';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async submitForConsensus(evaluationId: string): Promise<ApiResponse> {
        const request = { evaluation_id: evaluationId };
        return this.makeRequest<ApiResponse>('/api/v1/reputation/consensus/submit', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async voteOnConsensus(consensusId: string, vote: number, reason?: string): Promise<ApiResponse> {
        const request = { consensus_id: consensusId, vote, reason };
        return this.makeRequest<ApiResponse>('/api/v1/reputation/consensus/vote', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async finalizeConsensus(consensusId: string): Promise<ApiResponse> {
        const request = { consensus_id: consensusId };
        return this.makeRequest<ApiResponse>('/api/v1/reputation/consensus/finalize', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    // Enhanced Governance Methods - Missing from original
    async queueProposal(proposalId: string): Promise<ApiResponse> {
        const request = { proposal_id: proposalId };
        return this.makeRequest<ApiResponse>('/api/v1/governance/queue-proposal', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async executeProposal(proposalId: string): Promise<ApiResponse> {
        const request = { proposal_id: proposalId };
        return this.makeRequest<ApiResponse>('/api/v1/governance/execute-proposal', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async cancelProposal(proposalId: string): Promise<ApiResponse> {
        const request = { proposal_id: proposalId };
        return this.makeRequest<ApiResponse>('/api/v1/governance/cancel-proposal', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getProposalStatus(proposalId: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/governance/proposal/${proposalId}/status`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getVoteReceipt(proposalId: string, voter: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/governance/proposal/${proposalId}/vote-receipt/${voter}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getQuorum(): Promise<ApiResponse> {
        const endpoint = '/api/v1/governance/quorum';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getVotingDelay(): Promise<ApiResponse> {
        const endpoint = '/api/v1/governance/voting-delay';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getVotingPeriod(): Promise<ApiResponse> {
        const endpoint = '/api/v1/governance/voting-period';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getProposalThreshold(): Promise<ApiResponse> {
        const endpoint = '/api/v1/governance/proposal-threshold';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getAllProposals(): Promise<ApiResponse> {
        const endpoint = '/api/v1/governance/proposals/all';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getActiveProposals(): Promise<ApiResponse> {
        const endpoint = '/api/v1/governance/proposals/active';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async canExecute(proposalId: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/governance/proposal/${proposalId}/can-execute`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async hasVoted(proposalId: string, voter: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/governance/proposal/${proposalId}/has-voted/${voter}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    // Enhanced Pools Methods - Missing from original
    async selectCandidate(poolId: string, candidateAddress: string): Promise<ApiResponse> {
        const request = { pool_id: poolId, candidate: candidateAddress };
        return this.makeRequest<ApiResponse>('/api/v1/pools/select-candidate', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    // Original Pools Methods
    async createJobPool(request: CreateJobPoolRequest): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/pools/create-pool', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async applyToPool(request: ApplyToPoolRequest): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/api/v1/pools/apply', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async getJobPools(page: number = 1, size: number = 10): Promise<PaginatedApiResponse<any>> {
        const endpoint = `/api/v1/pools?page=${page}&size=${size}`;
        return this.makeRequest<PaginatedApiResponse<any>>(endpoint);
    }

    async getJobPool(id: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/pools/${id}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getPoolApplications(poolId: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/pools/${poolId}/applications`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async completePool(poolId: string): Promise<ApiResponse> {
        const request = { pool_id: poolId };
        return this.makeRequest<ApiResponse>('/api/v1/pools/complete', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async closePool(poolId: string): Promise<ApiResponse> {
        const request = { pool_id: poolId };
        return this.makeRequest<ApiResponse>('/api/v1/pools/close', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async withdrawApplication(poolId: string): Promise<ApiResponse> {
        const request = { pool_id: poolId };
        return this.makeRequest<ApiResponse>('/api/v1/pools/withdraw', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    async calculateMatchScore(poolId: string, candidateAddress: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/pools/${poolId}/match-score/${candidateAddress}`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getPoolMetrics(poolId: string): Promise<ApiResponse> {
        const endpoint = `/api/v1/pools/${poolId}/metrics`;
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getTalentPoolGlobalStats(): Promise<ApiResponse> {
        const endpoint = '/api/v1/pools/stats/global';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getActivePoolsCount(): Promise<ApiResponse> {
        const endpoint = '/api/v1/pools/stats/active-count';
        return this.makeRequest<ApiResponse>(endpoint);
    }

    async getTotalPoolsCount(): Promise<ApiResponse> {
        const endpoint = '/api/v1/pools/stats/total-count';
        return this.makeRequest<ApiResponse>(endpoint);
    }
}

// Export singleton instance
export const apiClient = new TalentChainApiClient();

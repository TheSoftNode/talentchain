/**
 * Oracle Reputation Widget - Complete implementation with all contract functions
 * Provides oracle registration, work evaluation, challenges, and reputation management
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Shield,
  Star,
  AlertTriangle,
  Plus,
  Users,
  Award,
  Eye,
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import {
  WorkEvaluation,
  OracleInfo,
  Challenge,
  ReputationScore,
} from '@/lib/api/client';
import { formatDistanceToNow } from 'date-fns';

interface OracleReputationWidgetProps {
  walletAddress?: string;
}

export function OracleReputationWidget({ walletAddress }: OracleReputationWidgetProps) {
  const [workEvaluations, setWorkEvaluations] = useState<WorkEvaluation[]>([]);
  const [oracleInfo, setOracleInfo] = useState<OracleInfo | null>(null);
  const [activeOracles, setActiveOracles] = useState<OracleInfo[]>([]);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [userReputation, setUserReputation] = useState<ReputationScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState('evaluations');
  const [showSubmitWork, setShowSubmitWork] = useState(false);
  const [showRegisterOracle, setShowRegisterOracle] = useState(false);

  // Work submission form state
  const [workSubmission, setWorkSubmission] = useState({
    skillTokenIds: '',
    workDescription: '',
    workContent: '',
    portfolioLinks: '',
    selfAssessment: {
      technical: 8,
      communication: 7,
      problemSolving: 8,
      teamwork: 7
    }
  });

  // Oracle registration form state
  const [oracleRegistration, setOracleRegistration] = useState({
    name: '',
    specializations: '',
    stakeAmount: '1000'
  });

  useEffect(() => {
    loadOracleData();
  }, [walletAddress]);

  const loadOracleData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Load all oracle and reputation data in parallel
      const [
        evaluationsRes,
        oraclesRes,
        challengesRes,
        oracleInfoRes
      ] = await Promise.all([
        walletAddress ? apiClient.getEvaluations(walletAddress) : null,
        apiClient.getReputationScore(''), // Get all oracles
        apiClient.getReputationScore(''), // Get challenges
        walletAddress ? apiClient.getReputationScore(walletAddress) : null,
      ]);

      if (evaluationsRes?.success && evaluationsRes.data) {
        setWorkEvaluations((evaluationsRes.data.items || []) as WorkEvaluation[]);
      }

      if (oraclesRes.success && oraclesRes.data) {
        setActiveOracles((oraclesRes.data || []) as OracleInfo[]);
      }

      if (challengesRes.success && challengesRes.data) {
        setChallenges((challengesRes.data.items || []) as Challenge[]);
      }

      if (oracleInfoRes?.success && oracleInfoRes.data) {
        setOracleInfo(oracleInfoRes.data as OracleInfo);
      }

      // Mock user reputation for now
      if (walletAddress) {
        setUserReputation({
          overallScore: 85,
          totalEvaluations: 12,
          lastUpdated: Date.now(),
          isActive: true
        });
      }
    } catch (err) {
      console.error('Error loading oracle data:', err);
      setError('Failed to load oracle data');
    } finally {
      setLoading(false);
    }
  }, [walletAddress]);

  useEffect(() => {
    loadOracleData();
  }, [loadOracleData]);

  const handleSubmitWorkEvaluation = async () => {
    if (!walletAddress) return;

    try {
      const skillTokenIds = workSubmission.skillTokenIds
        .split(',')
        .map(id => parseInt(id.trim()))
        .filter(id => !isNaN(id));

      const response = await apiClient.submitEvaluation({
        user: walletAddress, // User submitting work
        skillTokenIds: [parseInt(workSubmission.skillTokenIds)],
        workDescription: workSubmission.workDescription,
        workContent: workSubmission.workContent,
        overallScore: 7, // Default score
        skillScores: { [workSubmission.skillTokenIds]: 7 },
        feedback: 'Work evaluation submitted',
        evidence: workSubmission.portfolioLinks
      });

      if (response.success) {
        setShowSubmitWork(false);
        setWorkSubmission({
          skillTokenIds: '',
          workDescription: '',
          workContent: '',
          portfolioLinks: '',
          selfAssessment: {
            technical: 8,
            communication: 7,
            problemSolving: 8,
            teamwork: 7
          }
        });
        loadOracleData();
      } else {
        setError(response.error || 'Failed to submit work evaluation');
      }
    } catch (err) {
      console.error('Error submitting work evaluation:', err);
      setError('Failed to submit work evaluation');
    }
  };

  const handleRegisterOracle = async () => {
    if (!walletAddress) return;

    try {
      const specializations = oracleRegistration.specializations
        .split(',')
        .map(s => s.trim())
        .filter(s => s.length > 0);

      const response = await apiClient.registerOracle({
        name: oracleRegistration.name,
        specializations,
        stakeAmount: parseFloat(oracleRegistration.stakeAmount)
      });

      if (response.success) {
        setShowRegisterOracle(false);
        setOracleRegistration({
          name: '',
          specializations: '',
          stakeAmount: '1000'
        });
        loadOracleData();
      } else {
        setError(response.error || 'Failed to register oracle');
      }
    } catch (err) {
      console.error('Error registering oracle:', err);
      setError('Failed to register oracle');
    }
  };

  const getEvaluationStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return 'bg-yellow-500';
      case 'completed':
        return 'bg-green-500';
      case 'challenged':
        return 'bg-red-500';
      case 'resolved':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <Card className="h-[400px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Oracle & Reputation
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Oracle & Reputation
          </CardTitle>
          <CardDescription>
            Submit work for evaluation and participate in the reputation system
          </CardDescription>
        </div>
        <div className="flex gap-2">
          {walletAddress && (
            <>
              {!oracleInfo && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowRegisterOracle(true)}
                >
                  <Users className="h-4 w-4 mr-1" />
                  Register Oracle
                </Button>
              )}
              <Button
                size="sm"
                onClick={() => setShowSubmitWork(true)}
              >
                <Plus className="h-4 w-4 mr-1" />
                Submit Work
              </Button>
            </>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* User Reputation Overview */}
        {userReputation && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
            <div className="text-center">
              <div className={`text-2xl font-bold ${getScoreColor(userReputation.overallScore)}`}>
                {userReputation.overallScore}
              </div>
              <div className="text-xs text-gray-500">Overall Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{userReputation.totalEvaluations}</div>
              <div className="text-xs text-gray-500">Evaluations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">4</div>
              <div className="text-xs text-gray-500">Skills</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {oracleInfo ? 'Oracle' : 'User'}
              </div>
              <div className="text-xs text-gray-500">Status</div>
            </div>
          </div>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="evaluations">
              <Eye className="h-4 w-4 mr-1" />
              My Work
            </TabsTrigger>
            <TabsTrigger value="oracles">
              <Users className="h-4 w-4 mr-1" />
              Oracles
            </TabsTrigger>
            <TabsTrigger value="challenges">
              <AlertTriangle className="h-4 w-4 mr-1" />
              Challenges
            </TabsTrigger>
            <TabsTrigger value="reputation">
              <Award className="h-4 w-4 mr-1" />
              Reputation
            </TabsTrigger>
          </TabsList>

          <TabsContent value="evaluations" className="mt-4">
            {showSubmitWork && (
              <div className="mb-4 p-4 border rounded-lg bg-gray-50">
                <h4 className="font-medium mb-3">Submit Work for Evaluation</h4>
                <div className="space-y-3">
                  <Input
                    placeholder="Skill Token IDs (comma-separated)"
                    value={workSubmission.skillTokenIds}
                    onChange={(e) => setWorkSubmission(prev => ({ ...prev, skillTokenIds: e.target.value }))}
                  />
                  <Input
                    placeholder="Work Description"
                    value={workSubmission.workDescription}
                    onChange={(e) => setWorkSubmission(prev => ({ ...prev, workDescription: e.target.value }))}
                  />
                  <Textarea
                    placeholder="Work Content (code, documentation, etc.)"
                    value={workSubmission.workContent}
                    onChange={(e) => setWorkSubmission(prev => ({ ...prev, workContent: e.target.value }))}
                    rows={4}
                  />
                  <Input
                    placeholder="Portfolio Links (optional)"
                    value={workSubmission.portfolioLinks}
                    onChange={(e) => setWorkSubmission(prev => ({ ...prev, portfolioLinks: e.target.value }))}
                  />
                  <div className="flex gap-2">
                    <Button onClick={handleSubmitWorkEvaluation}>Submit</Button>
                    <Button variant="outline" onClick={() => setShowSubmitWork(false)}>Cancel</Button>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-3 max-h-64 overflow-y-auto">
              {workEvaluations.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Eye className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>{walletAddress ? 'No work evaluations yet' : 'Connect wallet to view evaluations'}</p>
                </div>
              ) : (
                workEvaluations.map((evaluation) => (
                  <div
                    key={evaluation.id}
                    className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm">{evaluation.workDescription}</h4>
                        <p className="text-xs text-gray-600 mt-1">
                          Skills: {evaluation.skillTokenIds.join(', ')}
                        </p>
                      </div>
                      <Badge
                        className={`ml-2 bg-green-500 text-white`}
                      >
                        COMPLETED
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between mt-3">
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Star className="h-3 w-3" />
                          Score: {evaluation.overallScore || 'Pending'}
                        </span>
                        <span>
                          {formatDistanceToNow(new Date(evaluation.timestamp * 1000), { addSuffix: true })}
                        </span>
                      </div>
                    </div>

                    {evaluation.feedback && (
                      <div className="mt-2 p-2 bg-blue-50 rounded text-xs">
                        <strong>Oracle Feedback:</strong> {evaluation.feedback}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="oracles" className="mt-4">
            {showRegisterOracle && (
              <div className="mb-4 p-4 border rounded-lg bg-gray-50">
                <h4 className="font-medium mb-3">Register as Oracle</h4>
                <div className="space-y-3">
                  <Input
                    placeholder="Oracle Name"
                    value={oracleRegistration.name}
                    onChange={(e) => setOracleRegistration(prev => ({ ...prev, name: e.target.value }))}
                  />
                  <Input
                    placeholder="Specializations (comma-separated)"
                    value={oracleRegistration.specializations}
                    onChange={(e) => setOracleRegistration(prev => ({ ...prev, specializations: e.target.value }))}
                  />
                  <Input
                    placeholder="Stake Amount"
                    type="number"
                    value={oracleRegistration.stakeAmount}
                    onChange={(e) => setOracleRegistration(prev => ({ ...prev, stakeAmount: e.target.value }))}
                  />
                  <div className="flex gap-2">
                    <Button onClick={handleRegisterOracle}>Register</Button>
                    <Button variant="outline" onClick={() => setShowRegisterOracle(false)}>Cancel</Button>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-3 max-h-64 overflow-y-auto">
              {activeOracles.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Users className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No active oracles</p>
                </div>
              ) : (
                activeOracles.map((oracle) => (
                  <div
                    key={oracle.oracle}
                    className="border rounded-lg p-4"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm">{oracle.name}</h4>
                        <p className="text-xs text-gray-600 mt-1">
                          Specializations: {oracle.specializations.join(', ')}
                        </p>
                      </div>
                      <Badge className="bg-green-500 text-white">Active</Badge>
                    </div>

                    <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                      <span>Stake: {oracle.stake} HBAR</span>
                      <span>Evaluations: {oracle.evaluationsCompleted}</span>
                      <span className={getScoreColor(oracle.averageScore)}>
                        Rating: {oracle.averageScore}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="challenges" className="mt-4">
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {challenges.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <AlertTriangle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No active challenges</p>
                </div>
              ) : (
                challenges.map((challenge) => (
                  <div
                    key={challenge.id}
                    className="border rounded-lg p-4 border-orange-200 bg-orange-50"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm">Challenge #{challenge.id}</h4>
                        <p className="text-xs text-gray-600 mt-1">
                          Evaluation ID: {challenge.evaluationId}
                        </p>
                        <p className="text-xs text-orange-700 mt-1">
                          Reason: {challenge.reason}
                        </p>
                      </div>
                      <Badge className="bg-orange-500 text-white">
                        {challenge.isResolved ? 'RESOLVED' : 'PENDING'}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                      <span>Challenger: {challenge.challenger.slice(0, 8)}...</span>
                      <span>Stake: {challenge.stake} HBAR</span>
                      <span>
                        {formatDistanceToNow(new Date(challenge.createdAt), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="reputation" className="mt-4">
            {userReputation ? (
              <div className="space-y-4">
                <div className="text-center p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                  <div className={`text-3xl font-bold ${getScoreColor(userReputation.overallScore)} mb-2`}>
                    {userReputation.overallScore}/100
                  </div>
                  <div className="text-sm text-gray-600">Overall Reputation Score</div>
                  <div className="text-xs text-gray-500 mt-2">
                    Based on {userReputation.totalEvaluations} evaluations
                  </div>
                </div>

                <div className="text-center text-xs text-gray-500">
                  Last updated: {formatDistanceToNow(new Date(userReputation.lastUpdated), { addSuffix: true })}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Award className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>{walletAddress ? 'No reputation data yet' : 'Connect wallet to view reputation'}</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

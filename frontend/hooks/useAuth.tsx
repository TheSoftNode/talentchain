"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
    walletConnector,
    WalletConnector,
    WalletType,
    WalletConnection
} from '../lib/wallet/wallet-connector';

export type UserRole = 'talent' | 'employer' | 'oracle' | null;

export interface User {
    walletAddress: string;
    accountId: string;
    walletType: WalletType;
    balance: string;
    role: UserRole;
    profile: {
        name?: string;
        email?: string;
        skills?: string[];
        experience?: string;
        companyName?: string;
        industry?: string;
        reputation?: number;
    };
}

interface AuthContextType {
    user: User | null;
    isConnected: boolean;
    isLoading: boolean;
    connectWallet: (walletType: WalletType) => Promise<void>;
    disconnectWallet: () => void;
    setUserRole: (role: UserRole) => void;
    updateProfile: (profile: Partial<User['profile']>) => void;
    updateBalance: () => Promise<void>;
    getAvailableWallets: () => Promise<WalletType[]>;
    connection: WalletConnection | null;
    restoreConnection: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [connection, setConnection] = useState<WalletConnection | null>(null);

    // Initialize wallet listeners on mount
    useEffect(() => {
        if (typeof window !== 'undefined') {
            initializeWalletListeners();
            checkExistingSession();
        }
    }, []);

    const initializeWalletListeners = () => {
        // Listen for wallet events
        walletConnector.on('connected', (data: unknown) => {
            const connection = data as WalletConnection;
            setConnection(connection);
            setIsConnected(true);

            // Check if there's an existing user profile
            const existingUser = localStorage.getItem(`user_${connection.accountId}`);
            if (existingUser) {
                const userProfile = JSON.parse(existingUser);
                setUser(userProfile);
            } else {
                // Create new user
                const newUser: User = {
                    walletAddress: connection.address,
                    accountId: connection.accountId,
                    walletType: connection.type,
                    balance: connection.balance || '0',
                    role: null,
                    profile: {}
                };
                setUser(newUser);
            }
        });

        walletConnector.on('disconnected', () => {
            setConnection(null);
            setIsConnected(false);
            setUser(null);
        });

        walletConnector.on('accountsChanged', (data: unknown) => {
            const accounts = data as string[];
            if (accounts.length === 0) {
                // User disconnected
                setConnection(null);
                setIsConnected(false);
                setUser(null);
            } else {
                // Account changed, update the connection
                const currentConnection = walletConnector.getConnection();
                if (currentConnection) {
                    setConnection(currentConnection);
                    // Update user with new account info
                    if (user) {
                        const updatedUser = {
                            ...user,
                            walletAddress: currentConnection.address,
                            accountId: currentConnection.accountId,
                            balance: currentConnection.balance || '0'
                        };
                        setUser(updatedUser);
                        // Save updated user profile
                        localStorage.setItem(`user_${currentConnection.accountId}`, JSON.stringify(updatedUser));
                    }
                }
            }
        });

        walletConnector.on('chainChanged', (data: unknown) => {
            const chainId = data as string;
            console.log('Chain changed:', chainId);
            // Handle network changes if needed
        });

        walletConnector.on('networkMismatch', (data: unknown) => {
            const networkData = data as { current: string; expected: string };
            console.warn('Network mismatch detected:', networkData);
            // Could show a notification to user about network mismatch
        });
    };

    const checkExistingSession = async () => {
        try {
            console.log('🔍 Checking for existing wallet session...');
            const currentConnection = walletConnector.getConnection();

            if (currentConnection) {
                console.log('Found saved connection:', currentConnection);

                // Check if the connection can be restored without user interaction
                const canRestore = await walletConnector.canRestoreConnection();

                if (canRestore) {
                    console.log('✅ Connection can be restored automatically');

                    // Check if the connection is still healthy
                    const isHealthy = await walletConnector.checkConnectionHealth();

                    if (isHealthy) {
                        console.log('✅ Connection is healthy, restoring session...');
                        setConnection(currentConnection);
                        setIsConnected(true);

                        // Check for existing user profile
                        const existingUser = localStorage.getItem(`user_${currentConnection.accountId}`);
                        if (existingUser) {
                            const userProfile = JSON.parse(existingUser);
                            setUser(userProfile);
                            console.log('✅ User profile restored');
                        } else {
                            console.log('No existing user profile found');
                        }
                    } else {
                        console.log('❌ Connection is unhealthy, clearing...');
                        walletConnector.resetConnectionState();
                    }
                } else {
                    console.log('⚠️ Connection cannot be restored automatically (MetaMask might be locked)');
                    // Don't clear the connection, just don't mark as connected
                    // The user will need to unlock MetaMask to restore
                }
            } else {
                console.log('No saved connection found');
            }
        } catch (error) {
            console.error('Error checking existing session:', error);
            // If there's an error, reset the connection state
            walletConnector.resetConnectionState();
        } finally {
            setIsLoading(false);
        }
    };

    const connectWallet = async (walletType: WalletType) => {
        try {
            setIsLoading(true);
            const connection = await walletConnector.connect(walletType);

            // Connection is handled by the event listener
            console.log('Wallet connected successfully:', connection);
        } catch (error) {
            console.error('Failed to connect wallet:', error);
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    const disconnectWallet = () => {
        try {
            walletConnector.disconnect();
            // Disconnection is handled by the event listener
        } catch (error) {
            console.error('Failed to disconnect wallet:', error);
        }
    };

    const setUserRole = (role: UserRole) => {
        if (user) {
            const updatedUser = { ...user, role };
            setUser(updatedUser);

            // Save to localStorage
            if (connection) {
                localStorage.setItem(`user_${connection.accountId}`, JSON.stringify(updatedUser));
            }
        }
    };

    const updateProfile = (profile: Partial<User['profile']>) => {
        if (user) {
            const updatedUser = {
                ...user,
                profile: { ...user.profile, ...profile }
            };
            setUser(updatedUser);

            // Save to localStorage
            if (connection) {
                localStorage.setItem(`user_${connection.accountId}`, JSON.stringify(updatedUser));
            }
        }
    };

    const updateBalance = async () => {
        try {
            if (connection) {
                const balance = await walletConnector.getBalance();

                // Update connection balance
                const updatedConnection = { ...connection, balance };
                setConnection(updatedConnection);

                // Update user balance
                if (user) {
                    const updatedUser = { ...user, balance };
                    setUser(updatedUser);

                    // Save to localStorage
                    localStorage.setItem(`user_${connection.accountId}`, JSON.stringify(updatedUser));
                }
            }
        } catch (error) {
            console.error('Failed to update balance:', error);
        }
    };

    const getAvailableWallets = async (): Promise<WalletType[]> => {
        return await WalletConnector.getAvailableWallets();
    };

    const restoreConnection = async () => {
        try {
            console.log('🔄 Attempting to restore connection...');
            const currentConnection = walletConnector.getConnection();

            if (currentConnection) {
                const canRestore = await walletConnector.canRestoreConnection();

                if (canRestore) {
                    const isHealthy = await walletConnector.checkConnectionHealth();

                    if (isHealthy) {
                        setConnection(currentConnection);
                        setIsConnected(true);

                        // Check for existing user profile
                        const existingUser = localStorage.getItem(`user_${currentConnection.accountId}`);
                        if (existingUser) {
                            const userProfile = JSON.parse(existingUser);
                            setUser(userProfile);
                        }

                        console.log('✅ Connection restored successfully');
                        return true;
                    }
                }
            }

            console.log('❌ Connection cannot be restored');
            return false;
        } catch (error) {
            console.error('Error restoring connection:', error);
            return false;
        }
    };

    const value: AuthContextType = {
        user,
        isConnected,
        isLoading,
        connectWallet,
        disconnectWallet,
        setUserRole,
        updateProfile,
        updateBalance,
        getAvailableWallets,
        connection,
        restoreConnection
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextType {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

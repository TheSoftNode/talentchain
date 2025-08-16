import { ethers } from 'ethers';
import { EthereumProvider } from '@walletconnect/ethereum-provider';
import { DAppConnector } from '@hashgraph/hedera-wallet-connect';
import { Client, AccountId, AccountBalanceQuery, Hbar, LedgerId } from '@hashgraph/sdk';
import { EventEmitter } from 'events';
import { MetaMaskInpageProvider } from '@metamask/providers';

// Types
interface WalletProvider {
    connect?(): Promise<void>;
    disconnect?(): Promise<void>;
    request?(args: { method: string; params?: unknown[] }): Promise<unknown>;
    on?(event: string, listener: (...args: unknown[]) => void): void;
    removeListener?(event: string, listener: (...args: unknown[]) => void): void;
}

export enum WalletType {
    HASHPACK = 'hashpack',
    METAMASK = 'metamask',
    WALLETCONNECT = 'walletconnect'
}

export interface WalletConnection {
    type: WalletType;
    accountId: string;
    address: string;
    signer?: ethers.Signer;
    provider?: ethers.Provider;
    balance?: string;
    network?: string;
    chainId?: number;
}

export interface NetworkConfig {
    chainId: number;
    name: string;
    rpcUrl: string;
    currency: {
        name: string;
        symbol: string;
        decimals: number;
    };
    blockExplorerUrl: string;
}

// Network configurations
export const HEDERA_NETWORKS: Record<string, NetworkConfig> = {
    testnet: {
        chainId: 296,
        name: 'Hedera Testnet',
        rpcUrl: 'https://testnet.hashio.io/api',
        currency: {
            name: 'HBAR',
            symbol: 'HBAR',
            decimals: 18
        },
        blockExplorerUrl: 'https://hashscan.io/testnet'
    },
    mainnet: {
        chainId: 295,
        name: 'Hedera Mainnet',
        rpcUrl: 'https://mainnet.hashio.io/api',
        currency: {
            name: 'HBAR',
            symbol: 'HBAR',
            decimals: 18
        },
        blockExplorerUrl: 'https://hashscan.io/mainnet'
    }
};

export class WalletConnector {
    private connection: WalletConnection | null = null;
    private listeners: { [event: string]: Array<(data?: unknown) => void> } = {};
    private hederaClient: Client | null = null;
    private walletConnectProvider: WalletProvider | null = null;
    private hashPackConnector: DAppConnector | null = null;
    private hederaWalletConnectProvider: DAppConnector | null = null;

    constructor() {
        if (typeof window !== 'undefined') {
            this.initializeHederaClient();
            this.loadSavedConnection();
        }
    }

    // Event handling
    on(event: string, callback: (data?: unknown) => void) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event: string, callback: (data?: unknown) => void) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    private emit(event: string, data?: unknown) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }

    private initializeHederaClient() {
        const network = process.env.NEXT_PUBLIC_HEDERA_NETWORK || 'testnet';
        this.hederaClient = new Client({
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            network: network as any
        });
    }

    // Helper method to get ethereum provider with proper typing
    private get ethereum(): MetaMaskInpageProvider | undefined {
        if (typeof window !== 'undefined' && window.ethereum) {
            return window.ethereum as unknown as MetaMaskInpageProvider;
        }
        return undefined;
    }

    // Debug method to check environment variables
    private debugEnvironmentVariables(): void {
        console.log('🔍 Environment Variables Debug:');
        console.log('NEXT_PUBLIC_HEDERA_NETWORK:', process.env.NEXT_PUBLIC_HEDERA_NETWORK);
        console.log('NEXT_PUBLIC_METAMASK_CHAIN_ID:', process.env.NEXT_PUBLIC_METAMASK_CHAIN_ID);
        console.log('NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID:', process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID);
        console.log('NEXT_PUBLIC_APP_URL:', process.env.NEXT_PUBLIC_APP_URL);
        console.log('NODE_ENV:', process.env.NODE_ENV);

        // Check if we're in browser
        if (typeof window !== 'undefined') {
            console.log('Window location:', window.location.href);
            console.log('MetaMask available:', !!window.ethereum?.isMetaMask);
        }
    }

    // HashPack Integration
    async connectHashPack(): Promise<WalletConnection> {
        try {
            console.log('🔗 Connecting to HashPack wallet via WalletConnect...');

            // HashPack works through WalletConnect according to their documentation
            // https://docs.hashpack.app/dapp-developers/walletconnect
            console.log('Using HashPack WalletConnect integration...');
            return await this.connectHashPackWalletConnect();
        } catch (error) {
            console.error('HashPack connection error:', error);
            throw error;
        }
    }

    // HashPack WalletConnect Integration
    private async connectHashPackWalletConnect(): Promise<WalletConnection> {
        try {
            // Initialize HashPack connector
            if (!this.hashPackConnector) {
                const network = process.env.NEXT_PUBLIC_HEDERA_NETWORK === 'mainnet' ? LedgerId.MAINNET : LedgerId.TESTNET;

                this.hashPackConnector = new DAppConnector({
                    name: process.env.NEXT_PUBLIC_HASHPACK_APP_NAME || 'TalentChain Pro',
                    description: process.env.NEXT_PUBLIC_HASHPACK_APP_DESCRIPTION || 'Blockchain-based talent ecosystem on Hedera',
                    url: process.env.NEXT_PUBLIC_HASHPACK_APP_URL || 'https://talentchainpro.com',
                    icons: ['https://talentchainpro.com/icon.png']
                }, network, process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID!);
            }

            // Initialize the connector
            await this.hashPackConnector.init();

            // Connect to HashPack using extension
            const session = await this.hashPackConnector.connectExtension('hashpack');

            // Get the first available signer
            const signers = this.hashPackConnector.signers;
            if (signers.length === 0) {
                throw new Error('No signers available after connection');
            }

            const signer = signers[0];
            const accountId = signer.getAccountId().toString();

            // Set the provider for use in signing and transactions
            this.hederaWalletConnectProvider = this.hashPackConnector;

            // Get account balance
            let balance = '0';
            try {
                if (this.hederaClient) {
                    const query = new AccountBalanceQuery()
                        .setAccountId(AccountId.fromString(accountId));
                    const accountBalance = await query.execute(this.hederaClient);
                    balance = accountBalance.hbars.toString();
                }
            } catch (error) {
                console.warn('Could not fetch balance:', error);
            }

            const connection: WalletConnection = {
                type: WalletType.HASHPACK,
                accountId,
                address: accountId, // HashPack uses account IDs
                balance,
                network: process.env.NEXT_PUBLIC_HEDERA_NETWORK || 'testnet',
                chainId: HEDERA_NETWORKS[process.env.NEXT_PUBLIC_HEDERA_NETWORK || 'testnet']?.chainId
            };

            this.connection = connection;
            this.saveConnection();
            this.emit('connected', connection);

            return connection;
        } catch (error) {
            console.error('HashPack WalletConnect connection error:', error);
            throw error;
        }
    }

    // MetaMask Integration
    async connectMetaMask(): Promise<WalletConnection> {
        try {
            const ethereum = this.ethereum;
            if (!ethereum?.isMetaMask) {
                throw new Error('MetaMask is not installed. Please install MetaMask extension.');
            }

            console.log('🔗 Connecting to MetaMask...');
            this.debugEnvironmentVariables();

            // Check if MetaMask is responsive and available
            try {
                // Test if MetaMask is responsive by checking if it's available
                // This doesn't require user permission and won't throw if locked
                if (!ethereum.isMetaMask || typeof ethereum.request !== 'function') {
                    throw new Error('MetaMask is not responsive. Please check if MetaMask is unlocked.');
                }

                // Additional check: try to get chainId without requesting accounts
                // This helps verify MetaMask is truly responsive
                try {
                    const currentChainId = await ethereum.request({ method: 'eth_chainId' });
                    console.log('Current MetaMask chainId:', currentChainId);
                } catch (chainError) {
                    console.warn('Could not get current chainId (MetaMask might be locked):', chainError);
                    // Don't throw here, continue with connection attempt
                }
            } catch (unlockError: unknown) {
                const error = unlockError as { code?: number; message?: string };
                if (error.code === 4001) {
                    throw new Error('MetaMask connection was rejected. Please approve the connection request.');
                } else if (error.message?.includes('locked')) {
                    throw new Error('MetaMask is locked. Please unlock MetaMask and try again.');
                }
                // Continue with the connection process
            }

            // Request account access with timeout
            console.log('Requesting account access...');
            const connectionPromise = ethereum.request({ method: 'eth_requestAccounts' });
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('MetaMask connection timeout. Please try again.')), 30000)
            );

            const accounts = await Promise.race([connectionPromise, timeoutPromise]) as string[] | null | undefined;

            if (!accounts || !Array.isArray(accounts) || accounts.length === 0) {
                throw new Error('No accounts found. Please make sure you have accounts in MetaMask.');
            }

            const account = accounts[0];
            console.log('Connected account:', account);

            // Check if we're on the correct network
            const chainId = await ethereum.request({ method: 'eth_chainId' }) as string | null | undefined;
            const expectedChainId = process.env.NEXT_PUBLIC_METAMASK_CHAIN_ID || '296';
            const expectedChainIdHex = `0x${parseInt(expectedChainId).toString(16)}`;

            // Fallback chain ID if environment variable is not set
            if (!process.env.NEXT_PUBLIC_METAMASK_CHAIN_ID) {
                console.warn('⚠️ NEXT_PUBLIC_METAMASK_CHAIN_ID not set, using default: 296 (Hedera Testnet)');
            }

            console.log('Network check:', {
                current: chainId,
                expected: expectedChainIdHex,
                expectedDecimal: expectedChainId
            });

            if (!chainId || chainId !== expectedChainIdHex) {
                console.log('Switching to correct network...');
                // Request network switch
                try {
                    await ethereum.request({
                        method: 'wallet_switchEthereumChain',
                        params: [{ chainId: expectedChainIdHex }]
                    });
                    console.log('Successfully switched to correct network');
                } catch (switchError: unknown) {
                    const error = switchError as { code?: number };
                    // If the network doesn't exist, add it
                    if (error.code === 4902) {
                        console.log('Adding new network...');
                        const networkConfig = HEDERA_NETWORKS[process.env.NEXT_PUBLIC_HEDERA_NETWORK || 'testnet'];
                        await ethereum.request({
                            method: 'wallet_addEthereumChain',
                            params: [{
                                chainId: expectedChainIdHex,
                                chainName: networkConfig.name,
                                nativeCurrency: networkConfig.currency,
                                rpcUrls: [networkConfig.rpcUrl],
                                blockExplorerUrls: [networkConfig.blockExplorerUrl]
                            }]
                        });
                        console.log('Successfully added new network');
                    } else {
                        console.error('Network switch error:', switchError);
                        throw switchError;
                    }
                }
            }

            // Create provider and signer
            console.log('Creating provider and signer...');
            const provider = new ethers.BrowserProvider(ethereum);
            const signer = await provider.getSigner();

            // Get balance
            console.log('Fetching balance...');
            const balance = await provider.getBalance(account);
            const balanceInEther = ethers.formatEther(balance);
            console.log('Balance:', balanceInEther);

            const connection: WalletConnection = {
                type: WalletType.METAMASK,
                accountId: account,
                address: account,
                signer,
                provider,
                balance: balanceInEther,
                network: process.env.NEXT_PUBLIC_HEDERA_NETWORK || 'testnet',
                chainId: parseInt(expectedChainId)
            };

            this.connection = connection;
            this.saveConnection();
            this.emit('connected', connection);

            // Set up event listeners
            this.setupMetaMaskListeners();

            console.log('MetaMask connection successful!');
            return connection;
        } catch (error) {
            console.error('MetaMask connection error:', error);

            // Provide better error messages for common issues
            if (error instanceof Error) {
                if (error.message.includes('rejected')) {
                    throw new Error('MetaMask connection was rejected. Please approve the connection request.');
                } else if (error.message.includes('timeout')) {
                    throw new Error('MetaMask connection timeout. Please try again.');
                } else if (error.message.includes('No accounts found')) {
                    throw new Error('No accounts found in MetaMask. Please add an account and try again.');
                } else if (error.message.includes('not responsive')) {
                    throw new Error('MetaMask is not responding. Please check if MetaMask is unlocked and try again.');
                } else if (error.message.includes('environment')) {
                    throw new Error('Configuration issue detected. Please check your environment variables.');
                }
            }

            // If it's a timeout or connection issue, try to reset state
            if (error instanceof Error && error.message.includes('timeout')) {
                console.log('Connection timeout detected, resetting state...');
                this.resetConnectionState();
            }

            // Check if environment variables are missing
            if (!process.env.NEXT_PUBLIC_METAMASK_CHAIN_ID || !process.env.NEXT_PUBLIC_HEDERA_NETWORK) {
                console.error('❌ Missing required environment variables for MetaMask connection');
                throw new Error('Configuration error: Missing required environment variables. Please check your .env.local file.');
            }

            throw error;
        }
    }

    // WalletConnect Integration
    async connectWalletConnect(): Promise<WalletConnection> {
        try {
            console.log('🔗 Connecting via WalletConnect...');

            // Debug: Check environment variables
            const projectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID;
            console.log('WalletConnect Project ID:', projectId);
            console.log('Project ID length:', projectId?.length);
            console.log('Project ID valid format:', /^[a-f0-9]{32}$/.test(projectId || ''));

            if (!projectId) {
                throw new Error('WalletConnect Project ID is missing. Please check your environment variables.');
            }

            if (!this.walletConnectProvider) {
                console.log('Creating WalletConnect provider...');
                // Initialize WalletConnect v2 provider
                this.walletConnectProvider = await EthereumProvider.init({
                    projectId: projectId,
                    chains: [parseInt(process.env.NEXT_PUBLIC_METAMASK_CHAIN_ID || '296')],
                    showQrModal: true,
                    metadata: {
                        name: 'TalentChain Pro',
                        description: 'Blockchain-based talent ecosystem on Hedera',
                        url: 'https://talentchainpro.com',
                        icons: ['https://talentchainpro.com/icon.png']
                    }
                });
                console.log('WalletConnect provider created successfully');
            }

            console.log('Attempting to connect...');
            // Connect
            if (!this.walletConnectProvider?.connect) {
                throw new Error('WalletConnect provider not properly initialized');
            }
            await this.walletConnectProvider.connect();
            console.log('WalletConnect connection successful');

            // Get accounts
            if (!this.walletConnectProvider?.request) {
                throw new Error('WalletConnect provider request method not available');
            }
            const accounts = await this.walletConnectProvider.request({ method: 'eth_accounts' }) as string[];
            const account = accounts[0];

            if (!account) {
                throw new Error('No accounts found');
            }

            // Create provider and signer
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const provider = new ethers.BrowserProvider(this.walletConnectProvider as any);
            const signer = await provider.getSigner();

            // Get balance
            const balance = await provider.getBalance(account);
            const balanceInEther = ethers.formatEther(balance);

            const connection: WalletConnection = {
                type: WalletType.WALLETCONNECT,
                accountId: account,
                address: account,
                signer,
                provider,
                balance: balanceInEther,
                network: process.env.NEXT_PUBLIC_HEDERA_NETWORK || 'testnet',
                chainId: parseInt(process.env.NEXT_PUBLIC_METAMASK_CHAIN_ID || '296')
            };

            this.connection = connection;
            this.saveConnection();
            this.emit('connected', connection);

            // Set up event listeners
            this.setupWalletConnectListeners();

            return connection;
        } catch (error) {
            console.error('WalletConnect connection error:', error);
            throw error;
        }
    }

    private setupMetaMaskListeners() {
        const ethereum = this.ethereum;
        if (ethereum) {
            ethereum.on('accountsChanged', (accounts: unknown) => {
                const accountArray = accounts as string[];
                this.emit('accountsChanged', accountArray);
                if (accountArray.length === 0) {
                    this.disconnect();
                } else {
                    // Update connection with new account
                    this.updateConnection(accountArray[0]);
                }
            });

            ethereum.on('chainChanged', (chainId: unknown) => {
                const chainIdStr = chainId as string;
                this.emit('chainChanged', chainIdStr);
                // Check if we need to reconnect
                const expectedChainId = process.env.NEXT_PUBLIC_METAMASK_CHAIN_ID || '296';
                if (parseInt(chainIdStr, 16).toString() !== expectedChainId) {
                    this.emit('networkMismatch', { current: chainIdStr, expected: expectedChainId });
                }
            });
        }
    }

    private setupWalletConnectListeners() {
        if (this.walletConnectProvider?.on) {
            this.walletConnectProvider.on('accountsChanged', (...args: unknown[]) => {
                const accounts = args[0] as string[];
                this.emit('accountsChanged', accounts);
                if (accounts.length === 0) {
                    this.disconnect();
                } else {
                    this.updateConnection(accounts[0]);
                }
            });

            this.walletConnectProvider.on('chainChanged', (...args: unknown[]) => {
                const chainId = args[0] as string;
                this.emit('chainChanged', chainId);
            });

            this.walletConnectProvider.on('disconnect', () => {
                this.disconnect();
            });
        }
    }

    private async updateConnection(newAccount: string) {
        if (!this.connection) return;

        try {
            if (this.connection.type === WalletType.METAMASK && this.connection.provider) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const signer = await (this.connection.provider as any).getSigner();
                const balance = await this.connection.provider.getBalance(newAccount);
                const balanceInEther = ethers.formatEther(balance);

                const updatedConnection: WalletConnection = {
                    ...this.connection,
                    accountId: newAccount,
                    address: newAccount,
                    signer,
                    balance: balanceInEther
                };

                this.connection = updatedConnection;
                this.saveConnection();
                this.emit('accountChanged', updatedConnection);
            }
        } catch (error) {
            console.error('Error updating connection:', error);
        }
    }

    // Main connect method
    async connect(walletType: WalletType): Promise<WalletConnection> {
        try {
            let connection: WalletConnection;

            switch (walletType) {
                case WalletType.HASHPACK:
                    connection = await this.connectHashPack();
                    break;
                case WalletType.METAMASK:
                    connection = await this.connectMetaMask();
                    break;
                case WalletType.WALLETCONNECT:
                    connection = await this.connectWalletConnect();
                    break;
                default:
                    throw new Error(`Unsupported wallet type: ${walletType}`);
            }

            return connection;
        } catch (error) {
            console.error('Connection error:', error);
            throw error;
        }
    }

    async disconnect() {
        if (this.connection) {
            const connection = this.connection;

            // Disconnect from specific wallet
            if (this.connection.type === WalletType.HASHPACK) {
                // HashPack disconnection is handled by WalletConnect
                console.log('Disconnecting HashPack via WalletConnect...');
            } else if (this.connection.type === WalletType.WALLETCONNECT && this.walletConnectProvider?.disconnect) {
                await this.walletConnectProvider.disconnect();
            } else if (this.connection.type === WalletType.METAMASK) {
                // MetaMask doesn't have a disconnect method, but we can clean up our state
                console.log('Disconnecting MetaMask...');
                // Remove event listeners
                if (this.ethereum) {
                    this.ethereum.removeAllListeners();
                }
            }

            // Clear connection state
            this.connection = null;
            this.clearSavedConnection();

            // Reset wallet-specific providers
            if (connection.type === WalletType.METAMASK) {
                this.walletConnectProvider = null;
            }

            this.emit('disconnected', connection);
        }
    }

    // Force reset connection state (useful for recovery)
    resetConnectionState() {
        console.log('🔄 Resetting connection state...');
        this.connection = null;
        this.walletConnectProvider = null;
        this.hashPackConnector = null;
        this.hederaWalletConnectProvider = null;
        this.clearSavedConnection();
        this.emit('disconnected', null);
    }

    getConnection(): WalletConnection | null {
        return this.connection;
    }

    isConnected(): boolean {
        return this.connection !== null;
    }

    async checkConnectionHealth(): Promise<boolean> {
        if (!this.connection) {
            return false;
        }

        try {
            if (this.connection.type === WalletType.METAMASK && this.connection.provider) {
                // Test if MetaMask is still responsive
                const balance = await this.connection.provider.getBalance(this.connection.address);
                return true;
            } else if (this.connection.type === WalletType.WALLETCONNECT && this.walletConnectProvider?.request) {
                // Test WalletConnect connection
                const accounts = await this.walletConnectProvider.request({ method: 'eth_accounts' });
                return Array.isArray(accounts) && accounts.length > 0;
            }
            return true;
        } catch (error) {
            console.warn('Connection health check failed:', error);
            return false;
        }
    }

    // Check if connection can be restored without user interaction
    async canRestoreConnection(): Promise<boolean> {
        if (!this.connection) {
            return false;
        }

        try {
            if (this.connection.type === WalletType.METAMASK) {
                const ethereum = this.ethereum;
                if (!ethereum?.isMetaMask) {
                    return false;
                }

                // Check if we can get accounts without requesting permission
                const accounts = await ethereum.request({ method: 'eth_accounts' }) as string[] | null | undefined;
                if (accounts && Array.isArray(accounts) && accounts.length > 0) {
                    const currentAccount = accounts[0].toLowerCase();
                    const savedAccount = this.connection.address.toLowerCase();
                    return currentAccount === savedAccount;
                }
                return false;
            }
            return false;
        } catch (error) {
            console.warn('Connection restoration check failed:', error);
            return false;
        }
    }

    async getBalance(): Promise<string> {
        if (!this.connection) {
            throw new Error('No wallet connected');
        }

        try {
            if (this.connection.type === WalletType.HASHPACK) {
                if (this.hederaClient) {
                    const query = new AccountBalanceQuery()
                        .setAccountId(AccountId.fromString(this.connection.accountId));
                    const accountBalance = await query.execute(this.hederaClient);
                    return accountBalance.hbars.toString();
                }
            } else if (this.connection.provider) {
                const balance = await this.connection.provider.getBalance(this.connection.address);
                return ethers.formatEther(balance);
            }

            return this.connection.balance || '0';
        } catch (error) {
            console.error('Error fetching balance:', error);
            return '0';
        }
    }

    async signMessage(message: string): Promise<string> {
        if (!this.connection) {
            throw new Error('No wallet connected');
        }

        try {
            if (this.connection.type === WalletType.HASHPACK) {
                // HashPack signing through WalletConnect
                if (this.hederaWalletConnectProvider) {
                    try {
                        // Use the correct DAppConnector API for signing
                        const signer = this.hederaWalletConnectProvider.getSigner(AccountId.fromString(this.connection.accountId));
                        const signature = await signer.sign([new TextEncoder().encode(message)]);
                        return Buffer.from(signature[0].signature).toString('hex');
                    } catch (error) {
                        console.error('HashPack WalletConnect signing failed:', error);
                        throw new Error('Failed to sign message with HashPack');
                    }
                } else {
                    throw new Error('HashPack WalletConnect provider not available');
                }
            } else if (this.connection.signer) {
                // For MetaMask and other EVM wallets
                const signature = await this.connection.signer.signMessage(message);
                return signature;
            } else {
                throw new Error('No signer available for message signing');
            }
        } catch (error) {
            console.error('Error signing message:', error);
            throw error;
        }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    async sendTransaction(transaction: any): Promise<string> {
        if (!this.connection) {
            throw new Error('No wallet connected');
        }

        try {
            if (this.connection.type === WalletType.HASHPACK) {
                // HashPack transaction signing through WalletConnect
                if (this.hederaWalletConnectProvider) {
                    try {
                        // Use the correct DAppConnector API for transaction signing
                        const signer = this.hederaWalletConnectProvider.getSigner(AccountId.fromString(this.connection.accountId));
                        const signedTransaction = await signer.signTransaction(transaction);
                        if (this.hederaClient) {
                            const result = await signedTransaction.execute(this.hederaClient);
                            return result.transactionId.toString();
                        } else {
                            throw new Error('Hedera client not available');
                        }
                    } catch (error) {
                        console.error('HashPack WalletConnect transaction failed:', error);
                        throw new Error('Failed to send transaction with HashPack');
                    }
                } else {
                    throw new Error('HashPack WalletConnect provider not available');
                }
            } else if (this.connection.signer) {
                // For MetaMask and other EVM wallets
                const tx = await this.connection.signer.sendTransaction(transaction);
                const receipt = await tx.wait();
                if (receipt) {
                    return receipt.hash;
                } else {
                    throw new Error('Transaction receipt is null');
                }
            } else {
                throw new Error('No signer available for transaction signing');
            }
        } catch (error) {
            console.error('Error sending transaction:', error);
            throw error;
        }
    }

    getNetworkInfo(): NetworkConfig | null {
        const network = process.env.NEXT_PUBLIC_HEDERA_NETWORK || 'testnet';
        return HEDERA_NETWORKS[network] || null;
    }

    // Utility methods
    static isHashPackInstalled(): boolean {
        if (typeof window === 'undefined') return false;

        // HashPack works through WalletConnect, not as a direct extension
        // According to HashPack docs: https://docs.hashpack.app/dapp-developers/walletconnect
        // "HashPack is fully compatible with WalletConnect - either using the native WalletConnect/ReOwn sdk's, or the Hedera WalletConnect wrapper"

        // HashPack is always available through WalletConnect integration
        console.log('HashPack available through WalletConnect integration');
        return true;
    }

    static isMetaMaskInstalled(): boolean {
        if (typeof window === 'undefined') return false;

        // Check if MetaMask extension exists
        const hasMetaMask = !!window.ethereum?.isMetaMask;
        console.log('MetaMask extension detected:', hasMetaMask);

        return hasMetaMask;
    }

    static async isMetaMaskAvailable(): Promise<boolean> {
        try {
            // First check if MetaMask extension is installed
            if (!this.isMetaMaskInstalled()) {
                console.log('MetaMask extension not found');
                return false;
            }

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const ethereum = window.ethereum as any;

            // Check if MetaMask is unlocked and responsive
            // We'll use a non-intrusive method that doesn't require user permission
            try {
                // Check if MetaMask is responsive by checking if it's available
                // This doesn't require user permission
                if (ethereum.isMetaMask && typeof ethereum.request === 'function') {
                    console.log('MetaMask is installed and responsive');
                    return true;
                }

                console.log('MetaMask is installed but not responsive');
                return false;
            } catch (error) {
                console.warn('MetaMask responsiveness check failed:', error);
                // Even if the responsiveness check fails, if we detected the extension, 
                // it's likely available (user might just need to unlock it)
                return true;
            }
        } catch (error) {
            console.warn('MetaMask availability check failed:', error);
            return false;
        }
    }

    static async getAvailableWallets(): Promise<WalletType[]> {
        const wallets: WalletType[] = [];

        console.log('Checking HashPack installation...');
        const hashpackInstalled = WalletConnector.isHashPackInstalled();
        console.log('HashPack installed:', hashpackInstalled);

        console.log('Checking MetaMask availability...');
        const metamaskAvailable = await WalletConnector.isMetaMaskAvailable();
        console.log('MetaMask available:', metamaskAvailable);

        // Check HashPack extension
        if (hashpackInstalled) {
            wallets.push(WalletType.HASHPACK);
        }

        // Check MetaMask
        if (metamaskAvailable) {
            wallets.push(WalletType.METAMASK);
        }

        // WalletConnect is always available as a fallback
        wallets.push(WalletType.WALLETCONNECT);

        console.log('Available wallets:', wallets);
        return wallets;
    }

    static formatAddress(address: string): string {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }

    // Persistence
    private saveConnection() {
        if (this.connection && typeof window !== 'undefined') {
            localStorage.setItem('talentchain_wallet_connection', JSON.stringify(this.connection));
        }
    }

    private loadSavedConnection() {
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('talentchain_wallet_connection');
            if (saved) {
                try {
                    console.log('📥 Loading saved connection from localStorage...');
                    this.connection = JSON.parse(saved);
                    console.log('Saved connection found:', this.connection);

                    // If we have a saved connection, try to restore it
                    if (this.connection) {
                        // For MetaMask, check if the account is still accessible
                        if (this.connection.type === WalletType.METAMASK) {
                            // Use setTimeout to ensure MetaMask is fully loaded
                            setTimeout(() => {
                                this.restoreMetaMaskConnection();
                            }, 1000);
                        } else if (this.connection.type === WalletType.HASHPACK) {
                            this.restoreHashPackConnection();
                        }
                        // For WalletConnect, the connection might need to be re-established
                    }
                } catch (error) {
                    console.error('Error loading saved connection:', error);
                    this.clearSavedConnection();
                }
            } else {
                console.log('📭 No saved connection found in localStorage');
            }
        }
    }

    private async restoreMetaMaskConnection() {
        try {
            console.log('🔄 Attempting to restore MetaMask connection...');

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const ethereum = window.ethereum as any;
            if (!ethereum || !ethereum.isMetaMask) {
                console.log('MetaMask not available during restoration');
                this.clearSavedConnection();
                return;
            }

            // Check if the saved account is still accessible using eth_accounts
            // This method returns the currently connected accounts without requesting permission
            const accounts = await ethereum.request({ method: 'eth_accounts' });

            if (accounts && accounts.length > 0) {
                const currentAccount = accounts[0].toLowerCase();
                const savedAccount = this.connection?.address.toLowerCase();

                console.log('Account check:', { current: currentAccount, saved: savedAccount });

                if (currentAccount === savedAccount) {
                    // Account is still accessible, restore the connection with full provider/signer
                    console.log('✅ Restoring MetaMask connection...');

                    try {
                        // Recreate provider and signer
                        const provider = new ethers.BrowserProvider(ethereum);
                        const signer = await provider.getSigner();

                        // Get current balance
                        const balance = await provider.getBalance(currentAccount);
                        const balanceInEther = ethers.formatEther(balance);

                        // Update connection with fresh provider/signer
                        const restoredConnection: WalletConnection = {
                            ...this.connection!,
                            signer,
                            provider,
                            balance: balanceInEther
                        };

                        this.connection = restoredConnection;
                        this.saveConnection();

                        // Emit connected event
                        this.emit('connected', restoredConnection);
                        console.log('✅ MetaMask connection restored successfully');

                        // Set up event listeners
                        this.setupMetaMaskListeners();

                    } catch (restoreError) {
                        console.error('Error recreating provider/signer:', restoreError);
                        this.clearSavedConnection();
                    }
                } else {
                    console.log('Saved account no longer matches current account, clearing connection');
                    this.clearSavedConnection();
                }
            } else {
                console.log('No accounts currently connected, clearing saved connection');
                this.clearSavedConnection();
            }
        } catch (error) {
            console.error('Error restoring MetaMask connection:', error);
            // Don't clear connection on error during restoration, just log it
            // The user might need to unlock MetaMask
            console.log('MetaMask restoration failed, but connection data preserved');
        }
    }

    private async restoreHashPackConnection() {
        try {
            // For HashPack, we might need to check if the extension is still available
            // and if the account is still accessible
            if (WalletConnector.isHashPackInstalled()) {
                console.log('Restoring HashPack connection...');
                this.emit('connected', this.connection);
            } else {
                console.log('HashPack extension not available, clearing connection');
                this.clearSavedConnection();
            }
        } catch (error) {
            console.error('Error restoring HashPack connection:', error);
            this.clearSavedConnection();
        }
    }

    private clearSavedConnection() {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('talentchain_wallet_connection');
        }
    }
}

// Export singleton instance
export const walletConnector = new WalletConnector();

import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../lib/api';

interface User {
    id: string;
    email: string;
}

interface AuthContextType {
    user: User | null;
    accessToken: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, confirmPassword: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [accessToken, setAccessToken] = useState<string | null>(localStorage.getItem('accessToken'));
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Initial check - if we have a token, we consider them logged in for now
        // In a real app, you might validate the token with a /me endpoint
        if (accessToken) {
            // Decode token or fetch user details if endpoints exist
            // For now, we'll just set a dummy user or derive from token if needed
            // setUser({ email: 'user@example.com' }); 
        }
        setIsLoading(false);
    }, [accessToken]);

    const login = async (email: string, password: string) => {
        const response = await api.post('/auth/login', { email, password });
        const { access, refresh } = response.data;

        localStorage.setItem('accessToken', access);
        localStorage.setItem('refreshToken', refresh);
        setAccessToken(access);
        setUser({ id: 'uuid', email }); // Ideally get this from response or decode token
    };

    const register = async (email: string, password: string, confirmPassword: string) => {
        await api.post('/auth/register', {
            email,
            password,
            confirm_password: confirmPassword
        });
        // Auto login after register or redirect to login? 
        // Usually redirect to login, but let's assume we want them to login manually for now
    };

    const logout = () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        setAccessToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{
            user,
            accessToken,
            isAuthenticated: !!accessToken,
            isLoading,
            login,
            register,
            logout
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

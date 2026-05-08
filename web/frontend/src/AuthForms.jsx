import React, { useState } from 'react';
import { Mail, Lock, User, ArrowLeft, Loader2 } from 'lucide-react';
import { useTranslation } from './LanguageContext';
import LegalPages from './LegalPages';

const API_URL = '';

export default function AuthForms({ onLogin, onSwitchToMain }) {
    const { t, lang, setLang } = useTranslation();
    const [mode, setMode] = useState('login'); // 'login', 'register', 'forgot', 'reset'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [legalPage, setLegalPage] = useState(null); // 'impressum', 'privacy', 'license' or null

    const getErrorMessage = (data, defaultMsg) => {
        if (!data.detail) return defaultMsg;
        if (typeof data.detail === 'string') return data.detail;
        if (Array.isArray(data.detail)) return data.detail.map(e => e.msg).join(', ');
        return JSON.stringify(data.detail);
    };

    // Form fields
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [selectedLang, setSelectedLang] = useState(lang);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            if (mode === 'login') {
                const response = await fetch(`${API_URL}/api/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(getErrorMessage(data, 'Login failed'));
                }

                // Store token and user info
                sessionStorage.setItem('auth_token', data.access_token);
                sessionStorage.setItem('user', JSON.stringify(data.user));
                setLang(data.user.language);
                onLogin(data);

            } else if (mode === 'register') {
                if (password !== confirmPassword) {
                    throw new Error(t('auth.passwords_not_match'));
                }

                const response = await fetch(`${API_URL}/api/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, language: selectedLang })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(getErrorMessage(data, 'Registration failed'));
                }

                setSuccess(t('auth.check_email'));
                setMode('login');

            } else if (mode === 'forgot') {
                const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(getErrorMessage(data, 'Request failed'));
                }

                setSuccess(t('auth.reset_email_sent'));
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleLogin = async (credentialResponse) => {
        setError('');
        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/auth/google`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ credential: credentialResponse.credential })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(getErrorMessage(data, 'Google login failed'));
            }

            sessionStorage.setItem('auth_token', data.access_token);
            sessionStorage.setItem('user', JSON.stringify(data.user));
            setLang(data.user.language);
            onLogin(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Initialize Google Sign-In
    React.useEffect(() => {
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        document.body.appendChild(script);

        script.onload = () => {
            if (window.google && window.GOOGLE_CLIENT_ID) {
                window.google.accounts.id.initialize({
                    client_id: window.GOOGLE_CLIENT_ID,
                    callback: handleGoogleLogin
                });
                window.google.accounts.id.renderButton(
                    document.getElementById('google-signin-button'),
                    { theme: 'filled_black', size: 'large', width: '100%', text: 'continue_with' }
                );
            }
        };

        return () => {
            document.body.removeChild(script);
        };
    }, [mode]);

    return (
        <div className="min-h-screen bg-slate-950 flex font-sans">
            {/* Left Panel - Branding */}
            <div className="hidden lg:flex flex-1 relative bg-slate-900 items-center justify-center overflow-hidden">
                <div className="aurora-bg"></div>
                <div className="relative z-10 text-center px-12">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-tr from-indigo-500 to-violet-600 shadow-2xl shadow-indigo-500/30 mb-8">
                        <User size={40} className="text-white" />
                    </div>
                    <h1 className="text-5xl font-bold text-white mb-6">VDV463 Validator</h1>
                    <p className="text-slate-400 text-lg max-w-md mx-auto">
                        {t('auth.tagline')}
                    </p>
                </div>
            </div>

            {/* Right Panel - Forms */}
            <div className="w-full lg:w-[480px] bg-slate-950 flex flex-col p-8 lg:p-12 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 blur-[100px] rounded-full -mr-32 -mt-32"></div>

                <div className="relative z-10 my-auto">
                    {/* Back button for non-login modes */}
                    {mode !== 'login' && (
                        <button
                            onClick={() => { setMode('login'); setError(''); setSuccess(''); }}
                            className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
                        >
                            <ArrowLeft size={16} />
                            {t('auth.back_to_login')}
                        </button>
                    )}

                    {/* Header */}
                    <div className="mb-10 text-center lg:text-left">
                        <h2 className="text-3xl font-bold text-white mb-3">
                            {mode === 'login' && t('auth.login_title')}
                            {mode === 'register' && t('auth.register_title')}
                            {mode === 'forgot' && t('auth.forgot_title')}
                        </h2>
                        <p className="text-slate-400">
                            {mode === 'login' && t('auth.login_subtitle')}
                            {mode === 'register' && t('auth.register_subtitle')}
                            {mode === 'forgot' && t('auth.forgot_subtitle')}
                        </p>
                    </div>

                    {/* Messages */}
                    {error && (
                        <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400 text-sm">
                            {success}
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Email */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300 ml-1">{t('auth.email')}</label>
                            <div className="relative">
                                <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    autoComplete="username"
                                    className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-12 pr-4 py-3.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-slate-600"
                                    placeholder="email@example.com"
                                />
                            </div>
                        </div>

                        {/* Password (not for forgot mode) */}
                        {mode !== 'forgot' && (
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-slate-300 ml-1">{t('auth.password')}</label>
                                <div className="relative">
                                    <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={8}
                                        autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                                        className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-12 pr-4 py-3.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-slate-600"
                                        placeholder="••••••••"
                                    />
                                </div>
                                {mode === 'register' && (
                                    <p className="text-xs text-slate-500 ml-1">{t('auth.password_requirements')}</p>
                                )}
                            </div>
                        )}

                        {/* Confirm Password (only for register) */}
                        {mode === 'register' && (
                            <>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300 ml-1">{t('auth.confirm_password')}</label>
                                    <div className="relative">
                                        <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                                        <input
                                            type="password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            required
                                            minLength={8}
                                            autoComplete="new-password"
                                            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-12 pr-4 py-3.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-slate-600"
                                            placeholder="••••••••"
                                        />
                                    </div>
                                </div>

                                {/* Language Selection */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-300 ml-1">{t('auth.language')}</label>
                                    <select
                                        value={selectedLang}
                                        onChange={(e) => setSelectedLang(e.target.value)}
                                        className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                                    >
                                        <option value="de">Deutsch</option>
                                        <option value="en">English</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {/* Forgot Password Link */}
                        {mode === 'login' && (
                            <div className="text-right">
                                <button
                                    type="button"
                                    onClick={() => { setMode('forgot'); setError(''); }}
                                    className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
                                >
                                    {t('auth.forgot_password')}
                                </button>
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-indigo-500/20 transform transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {loading && <Loader2 size={18} className="animate-spin" />}
                            {mode === 'login' && t('auth.signin')}
                            {mode === 'register' && t('auth.register')}
                            {mode === 'forgot' && t('auth.send_reset_link')}
                        </button>
                    </form>

                    {/* Google Login (only for login mode) */}
                    {mode === 'login' && (
                        <>
                            <div className="relative my-8">
                                <div className="absolute inset-0 flex items-center">
                                    <div className="w-full border-t border-slate-800"></div>
                                </div>
                                <div className="relative flex justify-center text-sm">
                                    <span className="px-4 bg-slate-950 text-slate-500">{t('auth.or')}</span>
                                </div>
                            </div>

                            <div id="google-signin-button" className="flex justify-center"></div>
                        </>
                    )}

                    {/* Switch Mode Links */}
                    <div className="mt-8 text-center">
                        {mode === 'login' && (
                            <p className="text-slate-400">
                                {t('auth.no_account')}{' '}
                                <button
                                    onClick={() => { setMode('register'); setError(''); }}
                                    className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
                                >
                                    {t('auth.register_now')}
                                </button>
                            </p>
                        )}
                        {mode === 'register' && (
                            <p className="text-slate-400">
                                {t('auth.have_account')}{' '}
                                <button
                                    onClick={() => { setMode('login'); setError(''); }}
                                    className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
                                >
                                    {t('auth.login_now')}
                                </button>
                            </p>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="relative z-10 pt-8 mt-12 border-t border-slate-900">
                    <div className="flex flex-wrap gap-4 items-center justify-between mb-4">
                        <p className="text-slate-600 text-xs">© 2024 VDV463 Validator</p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setLang('de')}
                                className={`text-xs px-2 py-1 rounded transition-colors ${lang === 'de' ? 'bg-indigo-500/20 text-indigo-400' : 'text-slate-500 hover:text-slate-300'}`}
                            >
                                DE
                            </button>
                            <button
                                onClick={() => setLang('en')}
                                className={`text-xs px-2 py-1 rounded transition-colors ${lang === 'en' ? 'bg-indigo-500/20 text-indigo-400' : 'text-slate-500 hover:text-slate-300'}`}
                            >
                                EN
                            </button>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-500">
                        <button onClick={() => setLegalPage('impressum')} className="hover:text-slate-300 transition-colors">{t('footer.impressum')}</button>
                        <button onClick={() => setLegalPage('privacy')} className="hover:text-slate-300 transition-colors">{t('footer.privacy')}</button>
                        <button onClick={() => setLegalPage('license')} className="hover:text-slate-300 transition-colors">{t('footer.license')}</button>
                    </div>
                </div>

                {/* Legal Pages Modal */}
                {legalPage && (
                    <LegalPages
                        page={legalPage}
                        onClose={() => setLegalPage(null)}
                    />
                )}
            </div>
        </div>
    );
}

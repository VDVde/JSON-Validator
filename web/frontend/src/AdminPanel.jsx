import React, { useState, useEffect } from 'react';
import {
    Users, UserPlus, Shield, ShieldCheck, Trash2, Edit,
    Check, X, Loader2, Search, ChevronDown, Mail, Globe
} from 'lucide-react';
import { useTranslation } from './LanguageContext';

const API_URL = '';

export default function AdminPanel({ authToken, currentUser, onClose }) {
    const { t } = useTranslation();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [editingUser, setEditingUser] = useState(null);

    // New user form
    const [newUser, setNewUser] = useState({
        email: '',
        password: '',
        role: 'user',
        language: 'de',
        is_verified: false
    });

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const response = await fetch(`${API_URL}/api/admin/users`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch users');
            }

            const data = await response.json();
            setUsers(data.users);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const createUser = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        try {
            const response = await fetch(`${API_URL}/api/admin/users`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newUser)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to create user');
            }

            setSuccess(t('admin.user_created'));
            setShowCreateModal(false);
            setNewUser({ email: '', password: '', role: 'user', language: 'de', is_verified: false });
            fetchUsers();
        } catch (err) {
            setError(err.message);
        }
    };

    const updateUser = async (userId, updates) => {
        setError('');

        try {
            const response = await fetch(`${API_URL}/api/admin/users/${userId}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to update user');
            }

            setSuccess(t('admin.user_updated'));
            setEditingUser(null);
            fetchUsers();
        } catch (err) {
            setError(err.message);
        }
    };

    const deleteUser = async (userId) => {
        if (!confirm(t('admin.confirm_delete'))) return;

        setError('');

        try {
            const response = await fetch(`${API_URL}/api/admin/users/${userId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${authToken}` }
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to delete user');
            }

            setSuccess(t('admin.user_deleted'));
            fetchUsers();
        } catch (err) {
            setError(err.message);
        }
    };

    const filteredUsers = users.filter(user =>
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-500/20 rounded-xl">
                            <Users size={24} className="text-indigo-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">{t('admin.title')}</h2>
                            <p className="text-sm text-slate-400">{t('admin.subtitle')}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Messages */}
                {error && (
                    <div className="mx-6 mt-4 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">
                        {error}
                    </div>
                )}
                {success && (
                    <div className="mx-6 mt-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400 text-sm">
                        {success}
                    </div>
                )}

                {/* Toolbar */}
                <div className="p-6 flex items-center justify-between gap-4">
                    <div className="relative flex-1 max-w-md">
                        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                        <input
                            type="text"
                            placeholder={t('admin.search_users')}
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-12 pr-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                        />
                    </div>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="flex items-center gap-2 px-4 py-2.5 bg-indigo-500 hover:bg-indigo-600 text-white font-medium rounded-xl transition-all"
                    >
                        <UserPlus size={18} />
                        {t('admin.add_user')}
                    </button>
                </div>

                {/* Users Table */}
                <div className="flex-1 overflow-auto px-6 pb-6">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 size={32} className="animate-spin text-indigo-400" />
                        </div>
                    ) : (
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                                    <th className="pb-4 pr-4">{t('admin.col_email')}</th>
                                    <th className="pb-4 pr-4">{t('admin.col_role')}</th>
                                    <th className="pb-4 pr-4">{t('admin.col_language')}</th>
                                    <th className="pb-4 pr-4">{t('admin.col_status')}</th>
                                    <th className="pb-4 pr-4">{t('admin.col_created')}</th>
                                    <th className="pb-4">{t('admin.col_actions')}</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {filteredUsers.map(user => (
                                    <tr key={user.id} className="group hover:bg-slate-800/50 transition-colors">
                                        <td className="py-4 pr-4">
                                            <div className="flex items-center gap-3">
                                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${user.role === 'admin' ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700 text-slate-300'
                                                    }`}>
                                                    {user.email[0].toUpperCase()}
                                                </div>
                                                <span className="text-white">{user.email}</span>
                                            </div>
                                        </td>
                                        <td className="py-4 pr-4">
                                            {editingUser === user.id ? (
                                                <select
                                                    defaultValue={user.role}
                                                    onChange={(e) => updateUser(user.id, { role: e.target.value })}
                                                    className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white text-sm"
                                                >
                                                    <option value="user">{t('auth.user')}</option>
                                                    <option value="admin">Admin</option>
                                                </select>
                                            ) : (
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${user.role === 'admin'
                                                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                                        : 'bg-slate-700 text-slate-300'
                                                    }`}>
                                                    {user.role === 'admin' ? <ShieldCheck size={12} /> : <Shield size={12} />}
                                                    {user.role === 'admin' ? 'Admin' : t('auth.user')}
                                                </span>
                                            )}
                                        </td>
                                        <td className="py-4 pr-4">
                                            <span className="inline-flex items-center gap-1.5 text-slate-400 text-sm">
                                                <Globe size={14} />
                                                {user.language.toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="py-4 pr-4">
                                            <div className="flex flex-col gap-1">
                                                <span className={`inline-flex items-center gap-1.5 text-xs ${user.is_active ? 'text-emerald-400' : 'text-rose-400'
                                                    }`}>
                                                    {user.is_active ? <Check size={12} /> : <X size={12} />}
                                                    {user.is_active ? t('admin.active') : t('admin.inactive')}
                                                </span>
                                                <span className={`inline-flex items-center gap-1.5 text-xs ${user.is_verified ? 'text-sky-400' : 'text-slate-500'
                                                    }`}>
                                                    <Mail size={12} />
                                                    {user.is_verified ? t('admin.verified') : t('admin.unverified')}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="py-4 pr-4 text-sm text-slate-400">
                                            {new Date(user.created_at).toLocaleDateString()}
                                        </td>
                                        <td className="py-4">
                                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                {user.id !== currentUser.id && (
                                                    <>
                                                        <button
                                                            onClick={() => setEditingUser(editingUser === user.id ? null : user.id)}
                                                            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-all"
                                                            title={t('admin.edit')}
                                                        >
                                                            <Edit size={16} />
                                                        </button>
                                                        <button
                                                            onClick={() => updateUser(user.id, { is_active: !user.is_active })}
                                                            className={`p-1.5 rounded transition-all ${user.is_active
                                                                    ? 'text-rose-400 hover:bg-rose-500/20'
                                                                    : 'text-emerald-400 hover:bg-emerald-500/20'
                                                                }`}
                                                            title={user.is_active ? t('admin.deactivate') : t('admin.activate')}
                                                        >
                                                            {user.is_active ? <X size={16} /> : <Check size={16} />}
                                                        </button>
                                                        <button
                                                            onClick={() => deleteUser(user.id)}
                                                            className="p-1.5 text-rose-400 hover:bg-rose-500/20 rounded transition-all"
                                                            title={t('admin.delete')}
                                                        >
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </>
                                                )}
                                                {user.id === currentUser.id && (
                                                    <span className="text-xs text-slate-500 italic">{t('admin.you')}</span>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                {/* Create User Modal */}
                {showCreateModal && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center p-4">
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md">
                            <h3 className="text-lg font-bold text-white mb-6">{t('admin.create_user')}</h3>

                            <form onSubmit={createUser} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                        {t('auth.email')}
                                    </label>
                                    <input
                                        type="email"
                                        value={newUser.email}
                                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                                        required
                                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                        {t('auth.password')} ({t('admin.optional')})
                                    </label>
                                    <input
                                        type="password"
                                        value={newUser.password}
                                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                                        placeholder={t('admin.password_placeholder')}
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                            {t('admin.col_role')}
                                        </label>
                                        <select
                                            value={newUser.role}
                                            onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                                        >
                                            <option value="user">{t('auth.user')}</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                            {t('auth.language')}
                                        </label>
                                        <select
                                            value={newUser.language}
                                            onChange={(e) => setNewUser({ ...newUser, language: e.target.value })}
                                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                                        >
                                            <option value="de">Deutsch</option>
                                            <option value="en">English</option>
                                        </select>
                                    </div>
                                </div>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={newUser.is_verified}
                                        onChange={(e) => setNewUser({ ...newUser, is_verified: e.target.checked })}
                                        className="w-4 h-4 rounded border-slate-600 text-indigo-500 focus:ring-indigo-500/50 bg-slate-800"
                                    />
                                    <span className="text-sm text-slate-300">{t('admin.mark_verified')}</span>
                                </label>

                                <div className="flex gap-3 pt-4">
                                    <button
                                        type="button"
                                        onClick={() => setShowCreateModal(false)}
                                        className="flex-1 px-4 py-2.5 border border-slate-700 text-slate-300 hover:bg-slate-800 rounded-xl transition-all"
                                    >
                                        {t('admin.cancel')}
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 px-4 py-2.5 bg-indigo-500 hover:bg-indigo-600 text-white font-medium rounded-xl transition-all"
                                    >
                                        {t('admin.create')}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

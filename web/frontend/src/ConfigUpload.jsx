import React, { useState } from 'react';
import { Upload, Check, AlertCircle, FileCode } from 'lucide-react';
import axios from 'axios';
import { useTranslation } from './LanguageContext';

export default function ConfigUpload({ onConfigLoaded, authToken, authType }) {
    const { t } = useTranslation();
    const [status, setStatus] = useState('idle'); // idle, uploading, success, error
    const [fileName, setFileName] = useState('');

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setStatus('uploading');
        setFileName(file.name);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const authHeader = authType === 'jwt' ? `Bearer ${authToken}` : `Basic ${authToken}`;
            const response = await axios.post('/api/config', formData, {
                headers: {
                    'Authorization': authHeader,
                    'Content-Type': 'multipart/form-data'
                }
            });

            if (response.data.status === 'valid') {
                setStatus('success');
                onConfigLoaded(response.data.config);
            }
        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    };

    return (
        <div>
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                <FileCode size={14} /> {t('settings.custom_rules')}
            </label>

            <div className="relative">
                <input
                    type="file"
                    onChange={handleFileChange}
                    accept=".json,.yaml,.yml"
                    className="hidden"
                    id="config-upload"
                />
                <label
                    htmlFor="config-upload"
                    className={`flex items-center justify-between w-full px-4 py-3 border border-dashed rounded-xl cursor-pointer transition-all duration-300 group
                        ${status === 'error' ? 'border-red-500/50 bg-red-500/5 text-red-400' :
                            status === 'success' ? 'border-emerald-500/50 bg-emerald-500/5 text-emerald-400' :
                                'border-white/10 bg-white/5 text-slate-400 hover:border-indigo-500/50 hover:bg-white/10 hover:text-slate-200'}`}
                >
                    <div className="flex items-center gap-3">
                        {status === 'success' ? <Check size={18} /> :
                            status === 'error' ? <AlertCircle size={18} /> :
                                <Upload size={18} className="text-slate-500 group-hover:text-indigo-400 transition-colors" />}

                        <span className="text-sm font-medium">
                            {status === 'idle' && t('settings.upload_config')}
                            {status === 'uploading' && t('settings.uploading')}
                            {status === 'success' && fileName}
                            {status === 'error' && t('settings.invalid_config')}
                        </span>
                    </div>

                    {status === 'idle' && (
                        <span className="text-[10px] bg-white/10 px-2 py-0.5 rounded text-slate-500 group-hover:bg-indigo-500/20 group-hover:text-indigo-300 transition-colors">
                            .YAML / .JSON
                        </span>
                    )}
                </label>
            </div>
            {status === 'idle' && (
                <p className="text-xs text-slate-600 mt-2">{t('settings.custom_rules_desc')}</p>
            )}
        </div>
    );
}

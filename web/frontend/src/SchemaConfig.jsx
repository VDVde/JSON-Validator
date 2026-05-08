import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Settings2, ChevronDown } from 'lucide-react';
import { useTranslation } from './LanguageContext';

export default function SchemaConfig({ onConfigChange, authToken, authType }) {
    const { t } = useTranslation();
    const [versions, setVersions] = useState(['auto']);
    const [selectedVersion, setSelectedVersion] = useState('auto');
    const [schemaOnly, setSchemaOnly] = useState(false);

    useEffect(() => {
        const fetchSchemas = async () => {
            if (!authToken) return; // Don't fetch if no token

            try {
                const authHeader = authType === 'jwt' ? `Bearer ${authToken}` : `Basic ${authToken}`;
                const response = await axios.get('/api/schemas', {
                    headers: { 'Authorization': authHeader }
                });
                if (response.data.schemas) {
                    setVersions(['auto', ...response.data.schemas]);
                }
            } catch (err) {
                // Silently fail - schemas will just show 'auto' only
            }
        };
        fetchSchemas();
    }, [authToken]);

    const handleChangeVersion = (e) => {
        const ver = e.target.value;
        setSelectedVersion(ver);
        onConfigChange({ schemaVersion: ver, schemaOnly });
    };

    const handleSchemaOnly = (e) => {
        const checked = e.target.checked;
        setSchemaOnly(checked);
        onConfigChange({ schemaVersion: selectedVersion, schemaOnly: checked });
    };

    return (
        <div className="space-y-4">
            <div>
                <label className="flex items-center gap-2 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] mb-3">
                    <Settings2 size={12} /> {t('settings.title')}
                </label>

                <div className="space-y-4 glass-panel p-4 rounded-xl border border-white/5 bg-slate-950/40">
                    <div>
                        <label className="block text-xs font-bold text-slate-400 mb-2 uppercase tracking-wide">{t('settings.schema_version')}</label>
                        <div className="relative group">
                            <select
                                value={selectedVersion}
                                onChange={handleChangeVersion}
                                className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-sm text-white appearance-none cursor-pointer hover:bg-slate-800 hover:border-indigo-500/40 transition-all focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/10"
                            >
                                {versions.map(v => (
                                    <option key={v} value={v} className="bg-slate-900 text-slate-100 py-2">
                                        {v === 'auto' ? t('settings.schema_auto') : `VDV463 v${v}`}
                                    </option>
                                ))}
                            </select>
                            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500 group-hover:text-indigo-400 transition-colors">
                                <ChevronDown size={16} />
                            </div>
                        </div>
                    </div>

                    <label className="flex items-start gap-3 group cursor-pointer p-2 rounded-lg hover:bg-white/5 transition-all">
                        <div className="relative flex items-center mt-0.5">
                            <input
                                type="checkbox"
                                checked={schemaOnly}
                                onChange={handleSchemaOnly}
                                className="peer h-4 w-4 appearance-none rounded border border-slate-700 bg-slate-900 checked:border-indigo-500 checked:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all"
                            />
                            <svg className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 text-white opacity-0 peer-checked:opacity-100 pointer-events-none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        </div>
                        <div className="flex-1">
                            <span className="block text-xs font-bold text-slate-300 group-hover:text-white transition-colors">{t('settings.schema_only')}</span>
                            <span className="block text-[10px] text-slate-500 mt-1 leading-relaxed">{t('settings.schema_only_desc')}</span>
                        </div>
                    </label>
                </div>
            </div>
        </div>
    );
}

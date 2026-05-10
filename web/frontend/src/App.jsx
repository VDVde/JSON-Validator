import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import axios from 'axios';
import {
    FileJson,
    Upload,
    AlertCircle,
    CheckCircle2,
    Search,
    ChevronRight,
    Code2,
    FileCode,
    LayoutDashboard,
    LogOut,
    RefreshCcw,
    User,
    Shield,
    ChevronDown
} from 'lucide-react';
import { useTranslation } from './LanguageContext';

// Components
import JsonVisualizer from './JsonVisualizer';
import CodeEditor from './CodeEditor';
import SplashScreen from './SplashScreen';
import SchemaConfig from './SchemaConfig';
import ConfigUpload from './ConfigUpload';
import GraphicalJsonView from './GraphicalJsonView';
import AuthForms from './AuthForms';
import AdminPanel from './AdminPanel';
import LegalPages from './LegalPages';

const API_URL = ''; // Same origin

// Translate common jsonschema / backend validation error messages to German
function translateValidationMessage(msg, lang) {
    if (lang !== 'de' || !msg) return msg;

    const rules = [
        [/^'(.+)' is a required property$/,        (_, p) => `Pflichtfeld '${p}' fehlt`],
        [/^(.+) is not of type '(.+)'$/,           (_, v, t) => `'${v}' hat den falschen Typ (erwartet: ${t})`],
        [/^(.+) is not valid under any of the given schemas$/, (_, v) => `Ungültiger Wert: '${v}'`],
        [/^(.+) does not match '(.+)'$/,           (_, v, p) => `'${v}' entspricht nicht dem Muster '${p}'`],
        [/^(.+) is too long$/,                     (_, v) => `'${v}' ist zu lang`],
        [/^(.+) is too short$/,                    (_, v) => `'${v}' ist zu kurz`],
        [/^(.+) is less than the minimum of (.+)$/,(_, v, m) => `'${v}' ist kleiner als der Mindestwert ${m}`],
        [/^(.+) is greater than the maximum of (.+)$/,(_, v, m) => `'${v}' ist größer als der Maximalwert ${m}`],
        [/^(.+) is not one of \[(.+)\]$/,          (_, v, opts) => `'${v}' ist kein erlaubter Wert (erlaubt: ${opts})`],
        [/^Additional properties are not allowed \((.+)\)$/, (_, p) => `Unbekannte Eigenschaft: ${p}`],
        [/^Invalid JSON: (.+) at line (\d+)$/,     (_, e, l) => `Ungültiges JSON: ${e} in Zeile ${l}`],
        [/^Cannot detect message type/,             () => `Nachrichtentyp konnte nicht erkannt werden. Erwartet: 'depotInfoList', 'chargingRequestList' oder 'chargingStatusList'`],
        [/^Auto-detected schema version: (.+)$/,   (_, v) => `Schema-Version automatisch erkannt: ${v}`],
        [/^Required field (.+) is missing$/,       (_, f) => `Pflichtfeld '${f}' fehlt`],
        [/None is not of type/,                    () => `Wert darf nicht leer (null) sein`],
    ];

    for (const [pattern, replace] of rules) {
        const m = msg.match(pattern);
        if (m) return replace(...m);
    }
    return msg;
}

export default function App() {
    const { t, lang, setLang } = useTranslation();
    const [appLoaded, setAppLoaded] = useState(false);
    const [auth, setAuth] = useState(sessionStorage.getItem('auth_token'));
    const [currentUser, setCurrentUser] = useState(() => {
        const saved = sessionStorage.getItem('user');
        return saved ? JSON.parse(saved) : null;
    });
    const [authType, setAuthType] = useState(sessionStorage.getItem('auth_type') || 'basic'); // 'basic' or 'jwt'
    const [showAdminPanel, setShowAdminPanel] = useState(false);
    const [legalPage, setLegalPage] = useState(null); // 'impressum', 'privacy', 'license' or null
    const [showUserMenu, setShowUserMenu] = useState(false);
    const userMenuRef = useRef(null);
    const [files, setFiles] = useState([]);
    const [fileContents, setFileContents] = useState({});
    const [activeFileIndex, setActiveFileIndex] = useState(null);
    const [results, setResults] = useState({});
    const [isValidating, setIsValidating] = useState(false);
    const [activeTab, setActiveTab] = useState('editor'); // 'editor' or 'tree'
    const [activeErrorLine, setActiveErrorLine] = useState(null);
    const [activeErrorPath, setActiveErrorPath] = useState(null);
    const [validationConfig, setValidationConfig] = useState({ schemaVersion: 'auto', schemaOnly: false });
    const [customRules, setCustomRules] = useState(null);
    const [autoValidateTrigger, setAutoValidateTrigger] = useState(0);
    const [resultsFilter, setResultsFilter] = useState('');
    const [authDisabled, setAuthDisabled] = useState(false);
    const [showResults, setShowResults] = useState(true);

    // Auth effect
    useEffect(() => {
        if (auth) {
            sessionStorage.setItem('auth_token', auth);
            sessionStorage.setItem('auth_type', authType);
        } else {
            sessionStorage.removeItem('auth_token');
            sessionStorage.removeItem('auth_type');
            sessionStorage.removeItem('user');
        }
    }, [auth, authType]);

    // Fetch server configuration on startup to check if auth is disabled
    useEffect(() => {
        axios.get('/api/server-config').then(res => {
            if (res.data?.auth_disabled) {
                setAuthDisabled(true);
                if (!sessionStorage.getItem('auth_token')) {
                    setAuth('no-auth');
                    setAuthType('jwt');
                    setCurrentUser({ email: 'anonymous', role: 'user' });
                }
            }
        }).catch(() => { /* ignore */ });
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Auto-validate when new files are fully loaded
    useEffect(() => {
        if (autoValidateTrigger > 0 && files.length > 0 && (auth || authDisabled)) {
            validate();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [autoValidateTrigger]);

    // Auto-validate when schema version or config changes
    useEffect(() => {
        if (files.length > 0 && activeFileIndex !== null && (auth || authDisabled)) {
            validate();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [validationConfig]);

    // Close user menu on outside click
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
                setShowUserMenu(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Memoize the parsed JSON data to prevent unnecessary re-renders of the TreeView
    const activeFileData = useMemo(() => {
        const activeFile = files[activeFileIndex];
        if (!activeFile) return null;
        const content = fileContents[activeFile.name];
        if (!content) return null;
        try {
            return JSON.parse(content);
        } catch (e) {
            return null;
        }
    }, [files, activeFileIndex, fileContents]);

    // Legacy Basic Auth login (fallback)
    const handleBasicLogin = (e) => {
        e.preventDefault();
        const username = e.target.username.value;
        const password = e.target.password.value;
        const token = btoa(`${username}:${password}`);
        setAuth(token);
        setAuthType('basic');
        setCurrentUser({ email: username, role: 'user', language: lang });
    };

    // JWT Auth login (new user management)
    const handleJwtLogin = (data) => {
        setAuth(data.access_token);
        setAuthType('jwt');
        setCurrentUser(data.user);
        sessionStorage.setItem('user', JSON.stringify(data.user));
        if (data.user.language) {
            setLang(data.user.language);
        }
    };

    const handleLogout = () => {
        setAuth(null);
        setAuthType('basic');
        setCurrentUser(null);
        setFiles([]);
        setFileContents({});
        setResults({});
        setShowUserMenu(false);
    };

    const onDrop = useCallback((e) => {
        e.preventDefault();
        const droppedFiles = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.json'));
        handleFiles(droppedFiles);
    }, []);

    const handleFileSelect = (e) => {
        const selectedFiles = Array.from(e.target.files).filter(f => f.name.endsWith('.json'));
        handleFiles(selectedFiles);
    };

    const handleFiles = (newFiles) => {
        const updatedFiles = [...files];
        const filesToRead = [];

        newFiles.forEach(file => {
            if (!files.find(f => f.name === file.name)) {
                updatedFiles.push(file);
                filesToRead.push(file);
            }
        });

        if (filesToRead.length === 0) return;

        setFiles(updatedFiles);
        if (activeFileIndex === null && updatedFiles.length > 0) {
            setActiveFileIndex(0);
        }

        // Read all files, then auto-validate once all are loaded
        let loadedCount = 0;
        const newContents = {};
        filesToRead.forEach(file => {
            const reader = new FileReader();
            reader.onload = (e) => {
                newContents[file.name] = e.target.result;
                loadedCount++;
                setFileContents(prev => ({ ...prev, [file.name]: e.target.result }));
                if (loadedCount === filesToRead.length) {
                    // All files loaded — trigger validation
                    setAutoValidateTrigger(t => t + 1);
                }
            };
            reader.readAsText(file);
        });
    };

    const validate = useCallback(async () => {
        if (files.length === 0) return;

        setIsValidating(true);
        setActiveErrorLine(null);
        setActiveErrorPath(null);

        const authHeader = authType === 'jwt' ? `Bearer ${auth}` : `Basic ${auth}`;
        const newResults = {};
        let hasAuthError = false;

        try {
            await Promise.all(files.map(async (file) => {
                const content = fileContents[file.name];
                if (!content) return;

                const formData = new FormData();
                formData.append('file', new File([content], file.name, { type: 'application/json' }));
                formData.append('schema_version', validationConfig.schemaVersion);
                formData.append('schema_only', validationConfig.schemaOnly);
                if (customRules) {
                    formData.append('config_content', JSON.stringify(customRules));
                }

                try {
                    const response = await axios.post(`${API_URL}/api/validate`, formData, {
                        headers: {
                            'Authorization': authHeader,
                            'Content-Type': 'multipart/form-data',
                        },
                    });
                    // Translate error messages for the current UI language
                    const result = response.data;
                    if (result?.issues) {
                        result.issues = result.issues.map(issue => ({
                            ...issue,
                            message: translateValidationMessage(issue.message, lang)
                        }));
                    }
                    newResults[file.name] = result;
                } catch (err) {
                    console.error(`Validation error for ${file.name}`, err);
                    if (err.response?.status === 401) {
                        hasAuthError = true;
                    }
                }
            }));

            if (hasAuthError) {
                handleLogout();
            } else {
                setResults(prev => ({
                    ...prev,
                    ...newResults
                }));
            }
        } catch (err) {
            console.error("Global validation error", err);
        } finally {
            setIsValidating(false);
        }
    }, [files, fileContents, auth, authType, validationConfig, customRules, lang]);

    const activeFile = files[activeFileIndex];
    const activeResults = activeFile ? results[activeFile.name] : null;

    const exportResultsCSV = () => {
        if (!activeResults?.issues?.length) return;
        const header = 'Schweregrad;Pfad;Meldung;Zeile\n';
        const rows = activeResults.issues.map(issue =>
            [issue.severity, issue.path, `"${(issue.message || '').replace(/"/g, '""')}"`, issue.line_number || ''].join(';')
        ).join('\n');
        const blob = new Blob(['\uFEFF' + header + rows], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url;
        a.download = `${activeFile?.name?.replace('.json','') || 'results'}_validation.csv`;
        a.click(); URL.revokeObjectURL(url);
    };

    const exportResultsJSON = () => {
        if (!activeResults) return;
        const blob = new Blob([JSON.stringify(activeResults, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url;
        a.download = `${activeFile?.name?.replace('.json','') || 'results'}_validation.json`;
        a.click(); URL.revokeObjectURL(url);
    };

    const filteredIssues = useMemo(() => {
        if (!activeResults?.issues) return [];
        if (!resultsFilter.trim()) return activeResults.issues;
        const q = resultsFilter.toLowerCase();
        return activeResults.issues.filter(issue =>
            (issue.message || '').toLowerCase().includes(q) ||
            (issue.path || '').toLowerCase().includes(q) ||
            (issue.severity || '').toLowerCase().includes(q)
        );
    }, [activeResults, resultsFilter]);

    const findLineFromPath = (path) => {
        const activeFile = files[activeFileIndex];
        if (!path || !activeFile) return null;
        const fileContent = fileContents[activeFile.name];
        if (!fileContent) return null;

        const cleanPath = path.replace(/\[\d+\]/g, '');
        const keys = cleanPath.split('.').filter(k => k);
        const lastKey = keys[keys.length - 1];

        if (!lastKey) return null;

        const lines = fileContent.split('\n');
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes(`"${lastKey}"`)) {
                return i + 1;
            }
        }
        return null;
    };

    const handleIssueClick = (path) => {
        setActiveErrorPath(path);
        const line = findLineFromPath(path);
        if (line) {
            setActiveErrorLine(line);
        }
        // Fehler werden in allen Ansichten markiert, ohne die aktuelle Ansicht zu wechseln
    };

    if (!appLoaded) {
        return <SplashScreen onComplete={() => setAppLoaded(true)} />;
    }

    if (!auth && !authDisabled) {
        return <AuthForms onLogin={handleJwtLogin} onSwitchToMain={() => { }} />;
    }

    return (
        <div className="relative min-h-screen bg-slate-950 text-slate-200 overflow-hidden font-sans">
            <div className="aurora-bg" />
            
            {/* Top Navigation Bar */}
            <header className="h-16 px-6 flex items-center justify-between border-b border-white/5 bg-slate-900/40 backdrop-blur-md z-50">
                <div className="flex items-center gap-4">
                    <div className="p-2 bg-indigo-500/20 rounded-xl">
                        <Shield className="text-indigo-400" size={24} />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold tracking-tight text-white leading-none">{t('app.title')}</h1>
                        <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">{t('app.subtitle')}</p>
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    <div className="flex gap-1 bg-slate-950/40 p-1 rounded-xl border border-white/5">
                        <button
                            onClick={() => setActiveTab('editor')}
                            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'editor' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-slate-300'}`}
                        >
                            <Code2 size={14} />
                            {t('editor.raw')}
                        </button>
                        <button
                            onClick={() => setActiveTab('tree')}
                            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'tree' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-slate-300'}`}
                        >
                            <FileCode size={14} />
                            {t('editor.tree')}
                        </button>
                        <button
                            onClick={() => setActiveTab('graph')}
                            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === 'graph' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-slate-300'}`}
                        >
                            <LayoutDashboard size={14} />
                            {t('editor.graph')}
                        </button>
                    </div>

                    <div className="h-6 w-px bg-white/10" />

                    <button
                        onClick={() => setShowResults(!showResults)}
                        className={`p-2 rounded-xl border transition-all flex items-center gap-2 ${showResults ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400' : 'bg-slate-900/40 border-white/5 text-slate-500 hover:text-slate-300'}`}
                        title={showResults ? "Hide Results" : "Show Results"}
                    >
                        <Shield size={16} />
                        <span className="text-xs font-bold hidden md:block">{t('panel.audit_report')}</span>
                    </button>

                    <div className="h-6 w-px bg-white/10" />

                    <div className="relative" ref={userMenuRef}>
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            className="flex items-center gap-3 pl-1 pr-3 py-1 rounded-full bg-white/5 border border-white/10 hover:border-white/20 transition-all"
                        >
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-xs font-bold text-white">
                                {currentUser?.email?.charAt(0).toUpperCase() || 'U'}
                            </div>
                            <span className="text-xs font-bold hidden sm:block">{currentUser?.email || 'User'}</span>
                            <ChevronDown size={14} className={`text-slate-500 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
                        </button>

                        {showUserMenu && (
                            <div className="absolute right-0 top-full mt-2 w-56 panel-card z-50 animate-in fade-in slide-in-from-top-2">
                                <div className="p-4 border-b border-white/5">
                                    <p className="text-xs font-bold text-white truncate">{currentUser?.email}</p>
                                    <p className="text-[10px] text-slate-500 uppercase mt-1">{currentUser?.role === 'admin' ? 'Admin' : t('auth.user')}</p>
                                </div>
                                <div className="p-1">
                                    {currentUser?.role === 'admin' && (
                                        <button
                                            onClick={() => { setShowAdminPanel(true); setShowUserMenu(false); }}
                                            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/5 transition-all"
                                        >
                                            <User size={16} /> {t('menu.admin')}
                                        </button>
                                    )}
                                    <button
                                        onClick={handleLogout}
                                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-rose-400 hover:bg-rose-500/10 transition-all"
                                    >
                                        <LogOut size={16} /> {t('auth.logout')}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* Workspace Grid */}
            <main className="flex flex-col lg:flex-row h-auto lg:h-[calc(100vh-64px)] p-4 gap-4 overflow-y-auto lg:overflow-hidden">
                {/* Explorer & Config Panel */}
                <aside className="w-full lg:w-80 flex flex-col gap-4 shrink-0 min-h-0">
                    <section className="panel-card flex-1">
                        <div className="p-4 border-b border-white/5 flex items-center justify-between">
                            <h2 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">{t('panel.workspace')}</h2>
                            <button className="p-1.5 hover:bg-white/5 rounded-lg text-slate-500 transition-colors">
                                <RefreshCcw size={14} />
                            </button>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                            {files.length === 0 ? (
                                <div className="p-8 text-center">
                                    <Upload className="mx-auto text-slate-700 mb-3" size={32} />
                                    <p className="text-xs text-slate-600 italic">{t('settings.no_file')}</p>
                                </div>
                            ) : (
                                files.map((file, idx) => (
                                    <button
                                        key={file.name + idx}
                                        onClick={() => setActiveFileIndex(idx)}
                                        className={`w-full group flex items-center justify-between p-2.5 rounded-xl transition-all border ${
                                            activeFileIndex === idx 
                                            ? 'bg-indigo-500/10 border-indigo-500/30 text-white' 
                                            : 'hover:bg-white/5 border-transparent text-slate-400'
                                        }`}
                                    >
                                        <div className="flex items-center gap-3 truncate">
                                            <FileCode size={16} className={activeFileIndex === idx ? 'text-indigo-400' : 'text-slate-600'} />
                                            <span className="text-sm font-medium truncate">{file.name}</span>
                                        </div>
                                        {results[file.name] && (
                                            results[file.name].valid ?
                                                <CheckCircle2 size={14} className="text-emerald-500 shrink-0" /> :
                                                <AlertCircle size={14} className="text-rose-500 shrink-0" />
                                        )}
                                    </button>
                                ))
                            )}
                        </div>

                        <div className="p-3 bg-slate-950/40 border-t border-white/5">
                            <div className="relative h-24 group border-2 border-dashed border-white/5 rounded-xl flex flex-col items-center justify-center transition-all hover:border-indigo-500/30 hover:bg-indigo-500/5 cursor-pointer">
                                <Upload size={18} className="text-slate-600 group-hover:text-indigo-400 transition-colors" />
                                <span className="text-[10px] font-bold text-slate-600 mt-2">{t('toolbar.open_files')}</span>
                                <input type="file" onChange={handleFileSelect} multiple accept=".json" className="absolute inset-0 opacity-0 cursor-pointer" />
                            </div>
                        </div>
                    </section>

                    <section className="panel-card p-4 space-y-4">
                        <SchemaConfig onConfigChange={setValidationConfig} authToken={auth} authType={authType} />
                        <ConfigUpload onConfigLoaded={setCustomRules} authToken={auth} authType={authType} />
                    </section>
                </aside>

                {/* Main Content Area */}
                <div className="flex-1 flex flex-col gap-4 min-w-0">
                    <div className="panel-card flex-1 relative">
                        {activeFile ? (
                            <>
                                <div className="absolute top-4 left-4 z-10 flex items-center gap-3 pointer-events-none">
                                    <div className="px-3 py-1 bg-slate-900/80 backdrop-blur-md rounded-full border border-white/10 shadow-xl">
                                        <p className="text-xs font-bold text-white flex items-center gap-2">
                                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                                            {activeFile.name}
                                        </p>
                                    </div>
                                </div>
                                <div className="absolute top-4 right-4 z-10">
                                    <button
                                        onClick={validate}
                                        disabled={isValidating}
                                        className="btn-premium"
                                    >
                                        {isValidating ? <RefreshCcw size={16} className="animate-spin" /> : <FileJson size={16} />}
                                        {t('toolbar.run_validation')}
                                    </button>
                                </div>
                                
                                <div className="flex-1 min-h-0 w-full relative">
                                    <div className="absolute inset-x-0 bottom-0 top-14">
                                        {activeTab === 'editor' && (
                                            <CodeEditor
                                                language="json"
                                                value={fileContents[activeFile.name] || ''}
                                                onChange={(val) => setFileContents(prev => ({ ...prev, [activeFile.name]: val }))}
                                                errorLine={activeErrorLine}
                                            />
                                        )}
                                        {activeTab === 'tree' && (
                                            <div className="h-full">
                                                <JsonVisualizer data={activeFileData} errorPath={activeErrorPath} />
                                            </div>
                                        )}
                                        {activeTab === 'graph' && (
                                            <div className="h-full">
                                                <GraphicalJsonView data={activeFileData} errorPath={activeErrorPath} />
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                                <div className="w-20 h-20 bg-indigo-500/10 rounded-3xl flex items-center justify-center mb-6">
                                    <FileJson size={40} className="text-indigo-400" />
                                </div>
                                <h3 className="text-xl font-bold text-white mb-2">No File Selected</h3>
                                <p className="text-slate-500 max-w-xs text-sm">Select a file from the explorer or upload a new one to begin validation.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Results Sidepanel */}
                {showResults && (
                    <aside className="w-full xl:w-[380px] shrink-0 min-h-0 animate-in slide-in-from-right duration-300">
                    <section className="panel-card h-full">
                        <div className="p-4 border-b border-white/5 flex items-center justify-between bg-slate-950/20">
                            <h2 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">{t('panel.audit_report')}</h2>
                            {activeResults?.issues?.length > 0 && (
                                <div className="flex gap-2">
                                    <button onClick={exportResultsCSV} className="p-1.5 hover:bg-white/5 rounded-lg text-slate-500 transition-colors" title="Export CSV"><FileCode size={14} /></button>
                                    <button onClick={exportResultsJSON} className="p-1.5 hover:bg-white/5 rounded-lg text-slate-500 transition-colors" title="Export JSON"><FileJson size={14} /></button>
                                </div>
                            )}
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar">
                            {!activeResults ? (
                                <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-600 italic">
                                    <Search size={40} className="mb-4 opacity-20" />
                                    <p className="text-sm">{t('results.empty_state')}</p>
                                </div>
                            ) : (
                                <div className="p-4 space-y-4 animate-slide-up">
                                    <div className={`p-4 rounded-2xl border ${activeResults.valid ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-rose-500/10 border-rose-500/20'}`}>
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 rounded-xl ${activeResults.valid ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                                                {activeResults.valid ? <CheckCircle2 size={24} /> : <AlertCircle size={24} />}
                                            </div>
                                            <div>
                                                <h4 className={`font-black text-sm uppercase tracking-tight ${activeResults.valid ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                    {activeResults.valid ? 'Validation Passed' : 'Validation Failed'}
                                                </h4>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className="glass-tag">v{activeResults.schema_version || 'auto'}</span>
                                                    <span className="glass-tag">{activeResults.message_type?.replace('Request', '') || 'Generic'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {activeResults.issues?.length > 0 && (
                                        <div className="space-y-2">
                                            <div className="relative mb-4">
                                                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                                                <input
                                                    type="text"
                                                    value={resultsFilter}
                                                    onChange={e => setResultsFilter(e.target.value)}
                                                    placeholder="Filter issues..."
                                                    className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/5 rounded-xl text-xs text-slate-300 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/30 transition-all"
                                                />
                                            </div>

                                            {filteredIssues.map((issue, i) => (
                                                <button
                                                    key={i}
                                                    onClick={() => handleIssueClick(issue.path)}
                                                    className="w-full text-left p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 hover:bg-white/[0.08] transition-all group relative overflow-hidden"
                                                >
                                                    <div className={`absolute left-0 top-0 bottom-0 w-1 ${issue.severity === 'ERROR' ? 'bg-rose-500' : 'bg-amber-500'}`} />
                                                    <div className="flex justify-between items-start mb-2">
                                                        <span className={`text-[10px] font-black px-2 py-0.5 rounded-lg border uppercase tracking-widest ${
                                                            issue.severity === 'ERROR' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                                                        }`}>
                                                            {issue.severity}
                                                        </span>
                                                        {issue.line_number && <span className="text-[10px] font-mono text-slate-500">L{issue.line_number}</span>}
                                                    </div>
                                                    <p className="text-sm text-slate-200 leading-relaxed mb-2 font-medium">{issue.message}</p>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-[10px] font-mono text-slate-500 truncate max-w-[200px]">{issue.path}</span>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </section>
                </aside>
                )}
            </main>

            <footer className="fixed bottom-0 left-0 right-0 h-8 bg-slate-950/80 backdrop-blur-md border-t border-white/5 px-6 flex items-center justify-between text-[10px] text-slate-600 font-bold uppercase tracking-widest z-50">
                <div className="flex gap-6">
                    <button onClick={() => setLegalPage('impressum')} className="hover:text-indigo-400 transition-colors">Impressum</button>
                    <button onClick={() => setLegalPage('privacy')} className="hover:text-indigo-400 transition-colors">Privacy Policy</button>
                </div>
                <div className="flex items-center gap-4">
                    <span className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                        {t('footer.system_online')}
                    </span>
                    <span className="text-slate-800">|</span>
                    <span>&copy; {new Date().getFullYear()} VDV463 Validator</span>
                </div>
            </footer>

            {legalPage && <LegalPages page={legalPage} onClose={() => setLegalPage(null)} />}
            {showAdminPanel && currentUser?.role === 'admin' && (
                <AdminPanel 
                    onClose={() => setShowAdminPanel(false)} 
                    authToken={auth} 
                    authType={authType} 
                    currentUser={currentUser}
                />
            )}
        </div>
    );
}

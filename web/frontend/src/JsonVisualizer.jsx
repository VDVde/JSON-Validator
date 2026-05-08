import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { ChevronRight, ChevronDown, ChevronsDownUp, ChevronsUpDown } from 'lucide-react';

// ─── helpers ────────────────────────────────────────────────────────────────

function getAllPaths(obj, prefix = '') {
    const paths = new Set();
    if (obj !== null && typeof obj === 'object') {
        const entries = Array.isArray(obj) ? obj.map((v, i) => [i, v]) : Object.entries(obj);
        entries.forEach(([key, val]) => {
            const path = prefix ? `${prefix}.${key}` : String(key);
            if (val !== null && typeof val === 'object' && !Array.isArray(val) ? Object.keys(val).length > 0 : Array.isArray(val) ? val.length > 0 : false) {
                paths.add(path);
                getAllPaths(val, path).forEach(p => paths.add(p));
            } else if (val !== null && typeof val === 'object') {
                paths.add(path);
                getAllPaths(val, path).forEach(p => paths.add(p));
            }
        });
    }
    return paths;
}

function getPathsToError(segments) {
    const paths = new Set();
    let current = '';
    segments.forEach(seg => {
        current = current ? `${current}.${seg}` : seg;
        paths.add(current);
    });
    return paths;
}

// ─── TreeNode ────────────────────────────────────────────────────────────────

function TreeNode({ name, value, path, expandedPaths, toggleExpand, errorPathSegments, depth, isLast }) {
    const isObject = value !== null && typeof value === 'object';
    const isArray = Array.isArray(value);
    const isExpanded = expandedPaths.has(path);

    const currentSegments = path.split('.').filter(s => s !== '');
    const isOnErrorPath = errorPathSegments.length > 0 &&
        currentSegments.length <= errorPathSegments.length &&
        currentSegments.every((seg, i) => seg === errorPathSegments[i]);
    const isErrorNode = errorPathSegments.length > 0 &&
        currentSegments.length === errorPathSegments.length &&
        currentSegments.every((seg, i) => seg === errorPathSegments[i]);

    // Value colour & display - using more harmonious colors
    const valueClass = typeof value === 'string' ? 'text-emerald-400' :
        typeof value === 'number' ? 'text-amber-400' :
        typeof value === 'boolean' ? 'text-sky-400' :
        value === null ? 'text-slate-500 italic' : 'text-slate-200';

    const displayValue = typeof value === 'string'
        ? (value.length > 80 ? `"${value.slice(0, 77)}…"` : `"${value}"`)
        : value === null ? 'null'
        : String(value);

    if (!isObject) {
        return (
            <div
                className={`group flex items-center min-h-[28px] rounded-lg px-2 relative transition-all duration-200 min-w-0 ${isErrorNode ? 'bg-rose-500/10 border border-rose-500/30' : 'hover:bg-white/5'}`}
                data-path={path}
            >
                <TreeConnector depth={depth} isLast={isLast} />
                <span className={`text-[13px] font-medium ${isErrorNode ? 'text-rose-400' : 'text-slate-400'} mr-2 transition-colors group-hover:text-slate-200 shrink-0`}>
                    {name}
                </span>
                <span className="text-slate-700 mr-2 text-[13px] shrink-0">:</span>
                <span className={`text-[13px] font-mono ${valueClass} whitespace-nowrap leading-none`}>{displayValue}</span>
                {isErrorNode && (
                    <div className="absolute right-2 flex items-center gap-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" />
                    </div>
                )}
            </div>
        );
    }

    const entries = isArray
        ? value.map((v, i) => [i, v])
        : Object.entries(value);
    const isEmpty = entries.length === 0;
    
    // Modern Type Badges
    const typeTag = isArray
        ? <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400/80 border border-emerald-500/10 mr-2 tracking-wider shrink-0 uppercase">Arr</span>
        : <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400/80 border border-indigo-500/10 mr-2 tracking-wider shrink-0 uppercase">Obj</span>;

    return (
        <div className="tree-node group/node" data-path={path}>
            {/* Row */}
            <div
                className={`flex items-center min-h-[30px] rounded-lg px-2 cursor-pointer select-none relative transition-all duration-200 min-w-0
                    ${isErrorNode ? 'bg-rose-500/10 border border-rose-500/30' : 'hover:bg-white/8'}
                    ${isOnErrorPath && !isErrorNode ? 'bg-amber-500/5' : ''}`}
                onClick={() => !isEmpty && toggleExpand(path)}
            >
                <TreeConnector depth={depth} isLast={isLast} />

                {/* Better expand arrow */}
                <span className={`w-5 h-5 flex items-center justify-center mr-1 shrink-0 transition-transform duration-200 ${isEmpty ? 'opacity-0' : 'text-slate-500 group-hover:text-slate-300'}`}>
                    {!isEmpty && (isExpanded ? <ChevronDown size={14} className="rotate-0" /> : <ChevronRight size={14} />)}
                </span>

                {typeTag}

                <span className={`text-[13px] font-semibold ${isErrorNode ? 'text-rose-400' : isOnErrorPath ? 'text-amber-400' : 'text-slate-200'} mr-2 shrink-0 group-hover:text-white transition-colors`}>
                    {name}
                </span>

                {(!isExpanded || isEmpty) && (
                    <span className="text-[10px] font-medium text-slate-500 bg-slate-900/80 px-2 py-0.5 rounded-md border border-white/5 shrink-0 ml-auto opacity-60 group-hover:opacity-100 transition-opacity">
                        {isArray ? `${entries.length} items` : `${entries.length} props`}
                    </span>
                )}
            </div>

            {/* children */}
            {isExpanded && !isEmpty && (
                <div className="relative">
                    {/* Improved vertical guide line */}
                    <div
                        className="absolute top-0 bottom-0 border-l border-slate-800 transition-colors group-hover/node:border-slate-700"
                        style={{ left: `${depth * 18 + 24}px` }}
                    />
                    <div className="pl-[2px]">
                        {entries.map(([key, val], idx) => {
                            const childPath = `${path}.${key}`;
                            return (
                                <TreeNode
                                    key={childPath}
                                    name={isArray ? `[${key}]` : String(key)}
                                    value={val}
                                    path={childPath}
                                    expandedPaths={expandedPaths}
                                    toggleExpand={toggleExpand}
                                    errorPathSegments={errorPathSegments}
                                    depth={depth + 1}
                                    isLast={idx === entries.length - 1}
                                />
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── TreeConnector ────────────────────────────────────────────────────────────
// Renders the horizontal "elbow" connector for this node at the given depth.

function TreeConnector({ depth, isLast }) {
    if (depth === 0) return null;
    return (
        <span
            className="shrink-0 inline-block relative"
            style={{ width: `${depth * 18}px`, height: '30px' }}
            aria-hidden
        >
            {/* horizontal arm */}
            <span
                className="absolute border-b border-slate-700/60"
                style={{
                    left: `${(depth - 1) * 18 + 8}px`,
                    right: 0,
                    top: '50%',
                }}
            />
        </span>
    );
}

// ─── Root ─────────────────────────────────────────────────────────────────────

function RootTree({ data, expandedPaths, toggleExpand, errorPathSegments }) {
    const isArray = Array.isArray(data);
    const entries = isArray ? data.map((v, i) => [i, v]) : Object.entries(data);
    const typeTag = isArray
        ? <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400/80 border border-emerald-500/10 mr-2 uppercase tracking-wider">Arr</span>
        : <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400/80 border border-indigo-500/10 mr-2 uppercase tracking-wider">Obj</span>;

    return (
        <div className="text-sm font-sans min-w-max">
            {/* root header */}
            <div className="flex items-center py-2 px-3 mb-2 rounded-xl bg-white/5 border border-white/5 shadow-sm">
                {typeTag}
                <span className="font-bold text-slate-100 mr-3 text-sm">Root</span>
                <span className="text-[10px] font-medium text-slate-500 bg-slate-900/80 px-2 py-0.5 rounded-md border border-white/5 ml-auto">
                    {isArray ? `${entries.length} items` : `${entries.length} props`}
                </span>
            </div>

            {/* children */}
            <div className="relative">
                <div className="absolute top-0 bottom-0 border-l border-slate-800" style={{ left: '24px' }} />
                {entries.map(([key, val], idx) => {
                    const childPath = String(key);
                    return (
                        <TreeNode
                            key={childPath}
                            name={isArray ? `[${key}]` : String(key)}
                            value={val}
                            path={childPath}
                            expandedPaths={expandedPaths}
                            toggleExpand={toggleExpand}
                            errorPathSegments={errorPathSegments}
                            depth={1}
                            isLast={idx === entries.length - 1}
                        />
                    );
                })}
            </div>
        </div>
    );
}

// ─── Main export ──────────────────────────────────────────────────────────────

export default function JsonVisualizer({ data, errorPath }) {
    const containerRef = useRef(null);
    const scrollableRef = useRef(null);
    const [expandedPaths, setExpandedPaths] = useState(new Set());
    const [zoom, setZoom] = useState(1);
    const prevErrorPathRef = useRef(null);
    const prevDataRef = useRef(null);

    const errorPathSegments = useMemo(() => {
        if (!errorPath) return [];
        let cleaned = errorPath.replace(/\[(\d+)\]/g, '.$1');
        cleaned = cleaned.replace(/^root\./, '').replace(/^\$\./, '').replace(/^\./, '');
        return cleaned.split('.').filter(s => s !== '');
    }, [errorPath]);

    // Handle Ctrl + Scroll Zoom
    useEffect(() => {
        const handleWheel = (e) => {
            if (e.ctrlKey && containerRef.current && containerRef.current.contains(e.target)) {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -0.05 : 0.05;
                setZoom(prev => {
                    const next = Math.min(Math.max(prev + delta, 0.5), 2.5);
                    return parseFloat(next.toFixed(2));
                });
            }
        };

        window.addEventListener('wheel', handleWheel, { passive: false });
        return () => window.removeEventListener('wheel', handleWheel);
    }, []);

    // Expand first 2 levels when data changes
    useEffect(() => {
        if (data && data !== prevDataRef.current) {
            prevDataRef.current = data;
            const initialPaths = new Set();
            const fill = (obj, prefix, d) => {
                if (d > 2 || !obj || typeof obj !== 'object') return;
                const entries = Array.isArray(obj) ? obj.map((v, i) => [i, v]) : Object.entries(obj);
                entries.forEach(([k, v]) => {
                    const p = prefix ? `${prefix}.${k}` : String(k);
                    if (v !== null && typeof v === 'object') {
                        initialPaths.add(p);
                        fill(v, p, d + 1);
                    }
                });
            };
            fill(data, '', 0);
            setExpandedPaths(initialPaths);
        }
    }, [data]);

    // Expand to error path
    useEffect(() => {
        if (errorPath && errorPath !== prevErrorPathRef.current && errorPathSegments.length > 0) {
            prevErrorPathRef.current = errorPath;
            const pathsToError = getPathsToError(errorPathSegments);
            setExpandedPaths(prev => {
                const next = new Set(prev);
                pathsToError.forEach(p => next.add(p));
                return next;
            });
            setTimeout(() => {
                if (scrollableRef.current) {
                    const el = scrollableRef.current.querySelector('.error-highlight, [data-path]');
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 300);
        }
    }, [errorPath, errorPathSegments]);

    const toggleExpand = useCallback((path) => {
        setExpandedPaths(prev => {
            const next = new Set(prev);
            const isExpanding = !next.has(path);
            
            if (next.has(path)) {
                // Collapse logic
                next.forEach(p => { if (p === path || p.startsWith(path + '.')) next.delete(p); });
            } else {
                // Expand logic
                next.add(path);
                
                // Auto-scroll to revealed content after a short delay for rendering
                setTimeout(() => {
                    const el = document.querySelector(`[data-path="${path}"]`);
                    if (el && scrollableRef.current) {
                        // Scroll so the expanded node is near the top to see children
                        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 150);
            }
            return next;
        });
    }, []);

    const expandAll = useCallback(() => {
        if (!data) return;
        setExpandedPaths(getAllPaths(data));
    }, [data]);

    const collapseAll = useCallback(() => {
        setExpandedPaths(new Set());
    }, []);

    if (!data) {
        return (
            <div className="p-8 text-slate-500 text-center italic text-sm">Keine Daten geladen</div>
        );
    }

    return (
        <div ref={containerRef} className="flex flex-col h-full bg-[#0d1117] rounded-lg border border-white/5 overflow-hidden">
            {/* Toolbar */}
            <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5 bg-slate-900/60 shrink-0">
                <button
                    onClick={expandAll}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white hover:bg-white/10 transition-all border border-transparent hover:border-white/10"
                    title="Alles aufklappen"
                >
                    <ChevronsUpDown size={13} />
                    Alles aufklappen
                </button>
                <button
                    onClick={collapseAll}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white hover:bg-white/10 transition-all border border-transparent hover:border-white/10"
                    title="Alles zuklappen"
                >
                    <ChevronsDownUp size={13} />
                    Alles zuklappen
                </button>

                <div className="h-4 w-px bg-white/10 mx-1" />
                
                <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Zoom</span>
                    <button 
                        onClick={() => setZoom(1)}
                        className="px-2 py-0.5 rounded bg-white/5 border border-white/5 text-[10px] font-bold text-indigo-400 hover:bg-indigo-500/10 transition-all"
                        title="Zoom zurücksetzen"
                    >
                        {Math.round(zoom * 100)}%
                    </button>
                </div>
            </div>

            {/* Tree */}
            <div
                id="json-tree-container"
                ref={scrollableRef}
                className="flex-1 overflow-auto p-4 custom-scrollbar min-w-0"
                style={{ zoom: zoom }}
            >
                <RootTree
                    data={data}
                    expandedPaths={expandedPaths}
                    toggleExpand={toggleExpand}
                    errorPathSegments={errorPathSegments}
                />
            </div>
        </div>
    );
}

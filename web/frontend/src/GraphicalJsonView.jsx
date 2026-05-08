import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
    ZoomIn,
    ZoomOut,
    Maximize2,
    RotateCcw,
    ChevronDown,
    ChevronRight,
    Home,
    Search,
    Expand,
    Shrink
} from 'lucide-react';

// Color scheme for different JSON types - matches Desktop UI dark theme from UI/theme.py
const TYPE_COLORS = {
    // Object: Grey/Dark (schema_object_bg_1: #303031, schema_object_bg_2: #3c3c3c)
    object: {
        bg: 'from-[#303031] to-[#3c3c3c]',
        border: 'border-[#4fc1ff]/50',
        icon: '⚙️',
        textColor: '#4fc1ff' // tree_object
    },
    // Array: Green-ish Dark (schema_array_bg_1: #25352a, schema_array_bg_2: #2d4535)
    array: {
        bg: 'from-[#25352a] to-[#2d4535]',
        border: 'border-[#dcdcaa]/50',
        icon: '📚',
        textColor: '#dcdcaa' // tree_array
    },
    // String: Yellow/Olive (schema_string_bg_1: #353525, schema_string_bg_2: #45452d)
    string: {
        bg: 'from-[#353525] to-[#45452d]',
        border: 'border-[#ce9178]/50',
        icon: '🅰️',
        textColor: '#ce9178' // tree_string
    },
    // Number: Blue-ish Dark (schema_number_bg_1: #253035, schema_number_bg_2: #2d3c45)
    number: {
        bg: 'from-[#253035] to-[#2d3c45]',
        border: 'border-[#b5cea8]/50',
        icon: '🔢',
        textColor: '#b5cea8' // tree_number
    },
    // Boolean: Red-ish Dark (schema_boolean_bg_1: #352525, schema_boolean_bg_2: #452d2d)
    boolean: {
        bg: 'from-[#352525] to-[#452d2d]',
        border: 'border-[#569cd6]/50',
        icon: '⚪',
        textColor: '#569cd6' // tree_boolean
    },
    // Null: Grey (tree_null: #808080)
    null: {
        bg: 'from-[#2d2d2d] to-[#333333]',
        border: 'border-[#808080]/50',
        icon: '∅',
        textColor: '#808080' // tree_null
    },
};

// Get value type
const getType = (value) => {
    if (value === null) return 'null';
    if (Array.isArray(value)) return 'array';
    return typeof value;
};

// Get display value for primitives
const getDisplayValue = (value, type) => {
    if (type === 'string') {
        return value.length > 40 ? `"${value.substring(0, 37)}..."` : `"${value}"`;
    }
    if (type === 'boolean') return value ? 'true' : 'false';
    if (type === 'null') return 'null';
    if (type === 'number') return String(value);
    return '';
};

// Generate tooltip content for a node
const getTooltipContent = (name, value, type, path) => {
    const lines = [];

    // Name and type
    lines.push(`📍 ${name}`);
    lines.push(`📝 Typ: ${type}`);

    // Path
    const cleanPath = path.replace(/^root\.?/, '').replace(/\./g, ' > ') || '/';
    lines.push(`📂 Pfad: ${cleanPath}`);

    // Type-specific info
    if (type === 'object' && value !== null) {
        const keys = Object.keys(value);
        lines.push(`🔢 Eigenschaften: ${keys.length}`);
        if (keys.length > 0 && keys.length <= 10) {
            lines.push(`📋 Felder: ${keys.join(', ')}`);
        } else if (keys.length > 10) {
            lines.push(`📋 Felder: ${keys.slice(0, 10).join(', ')}...`);
        }
    } else if (type === 'array') {
        const len = Array.isArray(value) ? value.length : 0;
        lines.push(`🔢 Elemente: ${len}`);
        if (len > 0) {
            const itemTypes = [...new Set(value.map(v => getType(v)))];
            lines.push(`📋 Element-Typen: ${itemTypes.join(', ')}`);
        }
    } else if (type === 'string') {
        lines.push(`📏 Länge: ${value.length} Zeichen`);
        if (value.length <= 100) {
            lines.push(`💬 Wert: "${value}"`);
        } else {
            lines.push(`💬 Wert: "${value.substring(0, 100)}..."`);
        }
    } else if (type === 'number') {
        lines.push(`💬 Wert: ${value}`);
        if (Number.isInteger(value)) {
            lines.push(`📋 Format: Integer`);
        } else {
            lines.push(`📋 Format: Decimal`);
        }
    } else if (type === 'boolean') {
        lines.push(`💬 Wert: ${value ? 'true' : 'false'}`);
    } else if (type === 'null') {
        lines.push(`💬 Wert: null`);
    }

    return lines.join('\n');
};

// Node Component
const JsonNode = ({
    name,
    value,
    path,
    depth,
    isExpanded,
    onToggle,
    isHighlighted,
    onNodeHover,
    nodePositions,
    registerNode,
    onExpandSubtree,
    onCollapseSubtree
}) => {
    const nodeRef = useRef(null);
    const [showTooltip, setShowTooltip] = useState(false);
    const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
    const [showContextMenu, setShowContextMenu] = useState(false);
    const [contextMenuPos, setContextMenuPos] = useState({ x: 0, y: 0 });

    const type = getType(value);
    const colors = TYPE_COLORS[type] || TYPE_COLORS.object;
    const hasChildren = type === 'object' || type === 'array';
    const childCount = hasChildren ? (Array.isArray(value) ? value.length : Object.keys(value).length) : 0;

    // Register node position for connection lines
    useEffect(() => {
        if (nodeRef.current && registerNode) {
            const rect = nodeRef.current.getBoundingClientRect();
            registerNode(path, {
                left: nodeRef.current.offsetLeft,
                top: nodeRef.current.offsetTop,
                width: nodeRef.current.offsetWidth,
                height: nodeRef.current.offsetHeight
            });
        }
    }, [path, registerNode, isExpanded]);

    const displayValue = hasChildren
        ? (type === 'array' ? `[${childCount}]` : `{${childCount}}`)
        : getDisplayValue(value, type);

    const tooltipContent = getTooltipContent(name, value, type, path);

    const handleMouseEnter = (e) => {
        onNodeHover && onNodeHover(path);
        setShowTooltip(true);
        // Position tooltip near mouse
        const rect = e.currentTarget.getBoundingClientRect();
        setTooltipPos({ x: rect.right + 10, y: rect.top });
    };

    const handleMouseLeave = () => {
        onNodeHover && onNodeHover(null);
        setShowTooltip(false);
    };

    // Close context menu when clicking elsewhere
    useEffect(() => {
        const handleClickOutside = () => setShowContextMenu(false);
        if (showContextMenu) {
            window.addEventListener('click', handleClickOutside);
            return () => window.removeEventListener('click', handleClickOutside);
        }
    }, [showContextMenu]);

    const handleContextMenu = (e) => {
        if (hasChildren) {
            e.preventDefault();
            e.stopPropagation();
            setShowContextMenu(true);
            setContextMenuPos({ x: e.clientX, y: e.clientY });
        }
    };

    return (
        <div className="relative">
            <div
                ref={nodeRef}
                data-path={path}
                className={`
                    relative inline-flex flex-col min-w-[160px] max-w-[400px]
                    rounded-lg shadow-lg transition-all duration-200
                    bg-gradient-to-b ${colors.bg}
                    border-2 ${isHighlighted
                        ? 'border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.6)] ring-2 ring-red-500/50 animate-pulse'
                        : colors.border}
                    ${hasChildren ? 'cursor-pointer hover:scale-[1.02]' : ''}
                `}
                onClick={() => hasChildren && onToggle(path)}
                onContextMenu={handleContextMenu}
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
            >
                {/* Error Indicator Badge */}
                {isHighlighted && (
                    <div className="absolute -top-2 -right-2 z-10">
                        <div className="flex items-center justify-center w-6 h-6 bg-red-500 rounded-full shadow-lg animate-bounce">
                            <span className="text-white text-xs font-bold">!</span>
                        </div>
                    </div>
                )}

                {/* Header */}
                <div className={`flex items-center gap-2 px-3 py-2 border-b ${isHighlighted ? 'border-red-400/30 bg-red-500/10' : 'border-white/10'}`}>
                    {hasChildren && (
                        <span className="text-white/70">
                            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        </span>
                    )}
                    <span className="text-lg">{colors.icon}</span>
                    <span className={`font-bold text-sm truncate ${isHighlighted ? 'text-red-300' : 'text-white'}`}>{name}</span>
                </div>

                {/* Content */}
                <div className="px-3 py-2">
                    <span className={`text-xs italic ${isHighlighted ? 'text-red-300/80' : 'text-white/80'}`}>{type}</span>
                    {displayValue && (
                        <div className={`text-xs mt-1 truncate font-mono ${isHighlighted ? 'text-red-200/90' : 'text-white/90'}`}>
                            {displayValue}
                        </div>
                    )}
                </div>
            </div>

            {/* Tooltip */}
            {showTooltip && !showContextMenu && (
                <div
                    className="fixed z-50 max-w-sm p-3 bg-slate-900 border border-slate-600 rounded-lg shadow-2xl pointer-events-none"
                    style={{
                        left: tooltipPos.x,
                        top: tooltipPos.y,
                        transform: 'translateY(-50%)'
                    }}
                >
                    <div className="text-xs text-slate-200 whitespace-pre-line font-mono leading-relaxed">
                        {tooltipContent}
                    </div>
                </div>
            )}

            {/* Context Menu */}
            {showContextMenu && hasChildren && (
                <div
                    className="fixed z-[100] bg-slate-800 border border-slate-600 rounded-lg shadow-2xl py-1 min-w-[180px]"
                    style={{ left: contextMenuPos.x, top: contextMenuPos.y }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <button
                        className="w-full px-4 py-2 text-left text-sm text-slate-200 hover:bg-slate-700 flex items-center gap-2"
                        onClick={() => {
                            onExpandSubtree && onExpandSubtree(path);
                            setShowContextMenu(false);
                        }}
                    >
                        <Expand size={14} />
                        Unterbaum aufklappen
                    </button>
                    <button
                        className="w-full px-4 py-2 text-left text-sm text-slate-200 hover:bg-slate-700 flex items-center gap-2"
                        onClick={() => {
                            onCollapseSubtree && onCollapseSubtree(path);
                            setShowContextMenu(false);
                        }}
                    >
                        <Shrink size={14} />
                        Unterbaum zuklappen
                    </button>
                </div>
            )}
        </div>
    );
};


// Recursive Tree Layout Component
const TreeLevel = ({
    data,
    name,
    path,
    depth,
    expandedNodes,
    toggleNode,
    highlightedPath,
    onNodeHover,
    maxDepth = 10,
    registerNode,
    parentType = null,
    onExpandSubtree,
    onCollapseSubtree
}) => {
    const type = getType(data);
    const isExpanded = expandedNodes.has(path);
    const hasChildren = (type === 'object' || type === 'array') && data !== null;
    const children = hasChildren
        ? (Array.isArray(data) ? data.map((v, i) => [i, v]) : Object.entries(data))
        : [];

    const isHighlighted = highlightedPath && path && highlightedPath.startsWith(path);
    const isExactMatch = highlightedPath === path;

    if (depth > maxDepth) {
        return (
            <div className="text-slate-500 text-sm italic px-4">
                (max depth reached)
            </div>
        );
    }

    return (
        <div className="flex items-start gap-12">
            {/* Current Node */}
            <JsonNode
                name={name}
                value={data}
                path={path}
                depth={depth}
                isExpanded={isExpanded}
                onToggle={toggleNode}
                isHighlighted={isExactMatch}
                onNodeHover={onNodeHover}
                registerNode={registerNode}
                onExpandSubtree={onExpandSubtree}
                onCollapseSubtree={onCollapseSubtree}
            />

            {/* Children */}
            {hasChildren && isExpanded && children.length > 0 && (
                <div className="flex flex-col gap-4 relative">
                    {/* Vertical connector line */}
                    <div className="absolute left-0 top-0 bottom-0 w-px bg-slate-500/30 -translate-x-4" />

                    {children.map(([key, value], index) => {
                        const childPath = path ? `${path}.${key}` : String(key);
                        const childType = getType(value);

                        // Calculate cardinality for this child
                        // For arrays: show index range, for objects: show "1" (required) or count
                        let cardinality = '';
                        if (Array.isArray(data)) {
                            // This is an array element, show its index
                            cardinality = `${index + 1}`;
                        } else {
                            // This is an object property
                            if (childType === 'array') {
                                const len = Array.isArray(value) ? value.length : 0;
                                cardinality = len === 0 ? '0' : `1..${len}`;
                            } else if (childType === 'object') {
                                cardinality = '1';
                            } else {
                                cardinality = '1';
                            }
                        }

                        return (
                            <div key={childPath} className="relative">
                                {/* Horizontal connector with cardinality label */}
                                <div className="absolute left-0 top-1/2 w-8 h-px bg-slate-500/40 -translate-x-8" />

                                {/* Cardinality badge on the line */}
                                <div className="absolute -left-6 top-1/2 -translate-y-1/2 -translate-x-1/2 z-10">
                                    <span className="px-1.5 py-0.5 bg-slate-800 border border-slate-600 rounded text-[10px] font-bold text-slate-300 whitespace-nowrap">
                                        [{cardinality}]
                                    </span>
                                </div>

                                {/* Arrow */}
                                <div className="absolute -left-2 top-1/2 -translate-y-1/2 w-0 h-0 border-l-4 border-l-slate-500/50 border-y-4 border-y-transparent" />

                                <TreeLevel
                                    data={value}
                                    name={Array.isArray(data) ? `[${key}]` : String(key)}
                                    path={childPath}
                                    depth={depth + 1}
                                    expandedNodes={expandedNodes}
                                    toggleNode={toggleNode}
                                    highlightedPath={highlightedPath}
                                    onNodeHover={onNodeHover}
                                    maxDepth={maxDepth}
                                    registerNode={registerNode}
                                    parentType={type}
                                    onExpandSubtree={onExpandSubtree}
                                    onCollapseSubtree={onCollapseSubtree}
                                />
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

// Main Component
export default function GraphicalJsonView({ data, errorPath, onPathHover }) {
    const containerRef = useRef(null);
    const contentRef = useRef(null);

    // State
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 50, y: 50 });
    const [isPanning, setIsPanning] = useState(false);
    const [panStart, setPanStart] = useState({ x: 0, y: 0 });
    const [expandedNodes, setExpandedNodes] = useState(new Set(['root']));
    const [hoveredPath, setHoveredPath] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [nodePositions, setNodePositions] = useState({});

    // Initialize with first level expanded
    useEffect(() => {
        if (data) {
            const initialExpanded = new Set(['root']);
            // Expand first level
            if (typeof data === 'object' && data !== null) {
                Object.keys(data).forEach(key => {
                    initialExpanded.add(`root.${key}`);
                });
            }
            setExpandedNodes(initialExpanded);
            // Reset view
            setZoom(1);
            setPan({ x: 50, y: 50 });
        }
    }, [data]);

    // Native wheel listener for zoom (to prevent browser zoom)
    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        const handleWheelNative = (e) => {
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                const delta = e.deltaY > 0 ? 0.9 : 1.1;
                setZoom(z => {
                    const next = Math.min(Math.max(z * delta, 0.25), 3);
                    return parseFloat(next.toFixed(3));
                });
            }
        };

        container.addEventListener('wheel', handleWheelNative, { passive: false });
        return () => container.removeEventListener('wheel', handleWheelNative);
    }, []);

    // Expand path to error when errorPath changes
    useEffect(() => {
        if (errorPath && data) {
            const pathParts = errorPath.replace(/\[(\d+)\]/g, '.$1').split('.').filter(Boolean);
            const newExpanded = new Set(expandedNodes);
            let currentPath = 'root';
            newExpanded.add(currentPath);

            pathParts.forEach(part => {
                currentPath = `${currentPath}.${part}`;
                newExpanded.add(currentPath);
            });

            setExpandedNodes(newExpanded);

            // Pan to show the error node (with a slight delay for layout)
            setTimeout(() => {
                const errorNode = document.querySelector(`[data-path="root.${pathParts.join('.')}"]`);
                if (errorNode && containerRef.current) {
                    const containerRect = containerRef.current.getBoundingClientRect();
                    const nodeRect = errorNode.getBoundingClientRect();

                    // Center the node in view
                    const newX = pan.x - (nodeRect.left - containerRect.left - containerRect.width / 2) / zoom;
                    const newY = pan.y - (nodeRect.top - containerRect.top - containerRect.height / 2) / zoom;
                    setPan({ x: newX, y: newY });
                }
            }, 100);
        }
    }, [errorPath, data]);

    // Toggle node expansion
    const toggleNode = useCallback((path) => {
        setExpandedNodes(prev => {
            const next = new Set(prev);
            if (next.has(path)) {
                next.delete(path);
            } else {
                next.add(path);
            }
            return next;
        });
    }, []);

    // Expand all nodes
    const expandAll = useCallback(() => {
        if (!data) return;

        const allPaths = new Set(['root']);

        const traverse = (obj, path) => {
            if (typeof obj !== 'object' || obj === null) return;

            if (Array.isArray(obj)) {
                obj.forEach((item, index) => {
                    const childPath = `${path}.${index}`;
                    allPaths.add(childPath);
                    traverse(item, childPath);
                });
            } else {
                Object.entries(obj).forEach(([key, value]) => {
                    const childPath = `${path}.${key}`;
                    allPaths.add(childPath);
                    traverse(value, childPath);
                });
            }
        };

        traverse(data, 'root');
        setExpandedNodes(allPaths);
    }, [data]);

    // Collapse all nodes (keep root expanded)
    const collapseAll = useCallback(() => {
        setExpandedNodes(new Set(['root']));
    }, []);

    // Expand a specific subtree
    const expandSubtree = useCallback((startPath) => {
        if (!data) return;

        const getDataAtPath = (obj, pathParts) => {
            let current = obj;
            for (const part of pathParts) {
                if (current === null || typeof current !== 'object') return null;
                current = Array.isArray(current) ? current[parseInt(part)] : current[part];
            }
            return current;
        };

        const pathParts = startPath.replace(/^root\.?/, '').split('.').filter(Boolean);
        const startData = pathParts.length === 0 ? data : getDataAtPath(data, pathParts);

        if (!startData || typeof startData !== 'object') return;

        setExpandedNodes(prev => {
            const next = new Set(prev);
            next.add(startPath);

            const traverse = (obj, path) => {
                if (typeof obj !== 'object' || obj === null) return;
                next.add(path);

                if (Array.isArray(obj)) {
                    obj.forEach((item, index) => {
                        traverse(item, `${path}.${index}`);
                    });
                } else {
                    Object.entries(obj).forEach(([key, value]) => {
                        traverse(value, `${path}.${key}`);
                    });
                }
            };

            traverse(startData, startPath);
            return next;
        });
    }, [data]);

    // Collapse a specific subtree
    const collapseSubtree = useCallback((startPath) => {
        setExpandedNodes(prev => {
            const next = new Set(prev);
            // Remove all paths that start with startPath (except startPath itself to keep parent visible)
            for (const path of prev) {
                if (path.startsWith(startPath + '.')) {
                    next.delete(path);
                }
            }
            next.delete(startPath);
            return next;
        });
    }, []);

    // Zoom controls
    const handleZoomIn = () => setZoom(z => Math.min(z * 1.2, 3));
    const handleZoomOut = () => setZoom(z => Math.max(z / 1.2, 0.25));
    const handleResetZoom = () => setZoom(1);
    const handleFitView = () => {
        setZoom(0.8);
        setPan({ x: 50, y: 50 });
    };

    // Pan handlers
    const handleMouseDown = (e) => {
        if (e.button === 0 || e.button === 1) { // Left or middle click
            setIsPanning(true);
            setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
        }
    };

    const handleMouseMove = (e) => {
        if (isPanning) {
            setPan({
                x: e.clientX - panStart.x,
                y: e.clientY - panStart.y
            });
        }
    };

    const handleMouseUp = () => {
        setIsPanning(false);
    };



    // Register node position callback
    const registerNode = useCallback((path, position) => {
        setNodePositions(prev => ({ ...prev, [path]: position }));
    }, []);

    // Convert errorPath to internal format
    const highlightPath = useMemo(() => {
        if (!errorPath) return null;
        return 'root.' + errorPath.replace(/\[(\d+)\]/g, '.$1');
    }, [errorPath]);

    // Breadcrumb path display
    const breadcrumbPath = hoveredPath
        ? hoveredPath.replace(/^root\.?/, '').replace(/\./g, ' > ') || 'Root'
        : 'Path: /';

    if (!data) {
        return (
            <div className="h-full flex items-center justify-center text-slate-500">
                <p>No data to display</p>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-slate-900/50 rounded-xl overflow-hidden">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-slate-900/80">
                <div className="flex items-center gap-2">
                    {/* Navigation */}
                    <button
                        onClick={() => {
                            setZoom(1);
                            setPan({ x: 50, y: 50 });
                            setExpandedNodes(new Set(['root']));
                        }}
                        className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                        title="Home"
                    >
                        <Home size={16} />
                    </button>

                    <div className="w-px h-6 bg-white/10 mx-1" />

                    {/* Expand/Collapse */}
                    <button
                        onClick={expandAll}
                        className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                        title="Expand All"
                    >
                        <Expand size={16} />
                    </button>
                    <button
                        onClick={collapseAll}
                        className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                        title="Collapse All"
                    >
                        <Shrink size={16} />
                    </button>

                    <div className="w-px h-6 bg-white/10 mx-1" />

                    {/* Zoom controls */}
                    <button
                        onClick={handleZoomOut}
                        className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                        title="Zoom Out"
                    >
                        <ZoomOut size={16} />
                    </button>
                    <span className="text-xs text-slate-400 min-w-[50px] text-center">
                        {Math.round(zoom * 100)}%
                    </span>
                    <button
                        onClick={handleZoomIn}
                        className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                        title="Zoom In"
                    >
                        <ZoomIn size={16} />
                    </button>
                    <button
                        onClick={handleResetZoom}
                        className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                        title="Reset Zoom"
                    >
                        <RotateCcw size={16} />
                    </button>
                    <button
                        onClick={handleFitView}
                        className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                        title="Fit View"
                    >
                        <Maximize2 size={16} />
                    </button>
                </div>

                {/* Search */}
                <div className="relative">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search..."
                        className="pl-9 pr-4 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/50 w-48"
                    />
                </div>
            </div>

            {/* Breadcrumb */}
            <div className="px-4 py-1.5 border-b border-white/5 bg-slate-900/40">
                <p className="text-xs text-slate-400 font-mono">{breadcrumbPath}</p>
            </div>

            {/* Canvas */}
            <div
                ref={containerRef}
                className="flex-1 overflow-auto cursor-grab active:cursor-grabbing custom-scrollbar"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
            >
                <div
                    ref={contentRef}
                    className="p-8 min-w-max"
                    style={{
                        transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                        transformOrigin: 'top left',
                        transition: isPanning ? 'none' : 'transform 0.1s ease-out'
                    }}
                >
                    <TreeLevel
                        data={data}
                        name="Root"
                        path="root"
                        depth={0}
                        expandedNodes={expandedNodes}
                        toggleNode={toggleNode}
                        highlightedPath={highlightPath}
                        onNodeHover={setHoveredPath}
                        registerNode={registerNode}
                        onExpandSubtree={expandSubtree}
                        onCollapseSubtree={collapseSubtree}
                    />
                </div>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 px-4 py-2 border-t border-white/10 bg-slate-900/80 overflow-x-auto">
                {Object.entries(TYPE_COLORS).map(([type, colors]) => (
                    <div key={type} className="flex items-center gap-1.5 shrink-0">
                        <div className={`w-4 h-4 rounded bg-gradient-to-b ${colors.bg} ${colors.border} border`} />
                        <span className="text-xs text-slate-400 capitalize">{type}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

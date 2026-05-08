import React, { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';

export default function CodeEditor({ value, onChange, language = 'json', errorLine }) {
    const editorRef = useRef(null);
    const decorationsRef = useRef([]);

    function handleEditorDidMount(editor, monaco) {
        editorRef.current = editor;

        // Define a premium dark theme "Midnight Aurora"
        monaco.editor.defineTheme('midnight-aurora', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: 'string.key.json', foreground: '818cf8', fontStyle: 'bold' }, // Indigo-400
                { token: 'string.value.json', foreground: '34d399' }, // Emerald-400
                { token: 'number', foreground: 'fbbf24' }, // Amber-400
                { token: 'keyword', foreground: 'fb7185' }, // Rose-400
                { token: 'delimiter', foreground: '94a3b8' }, // Slate-400
            ],
            colors: {
                'editor.background': '#020617', // Slate-950
                'editor.lineHighlightBackground': '#1e293b40',
                'editorLineNumber.foreground': '#475569',
                'editorLineNumber.activeForeground': '#818cf8',
                'editorIndentGuide.background': '#1e293b',
                'editorIndentGuide.activeBackground': '#334155',
                'editor.selectionBackground': '#33415580',
            }
        });

        monaco.editor.setTheme('midnight-aurora');
    }

    // Effect to handle error line highlighting
    useEffect(() => {
        if (!editorRef.current) return;

        const editor = editorRef.current;
        const model = editor.getModel();
        if (!model) return;

        const newDecorations = [];
        if (errorLine && errorLine > 0) {
            newDecorations.push({
                range: {
                    startLineNumber: errorLine,
                    startColumn: 1,
                    endLineNumber: errorLine,
                    endColumn: 1
                },
                options: {
                    isWholeLine: true,
                    className: 'error-line-highlight', // Defined in index.css
                    glyphMarginClassName: 'error-glyph-margin',
                    linesDecorationsClassName: 'error-line-decoration'
                }
            });

            // Scroll to the line with some padding
            editor.revealLineInCenter(errorLine, 0); // 0 = Smooth
        }

        decorationsRef.current = editor.deltaDecorations(decorationsRef.current, newDecorations);
    }, [errorLine]);

    return (
        <div id="monaco-editor-wrapper" className="h-full w-full animate-in fade-in duration-500">
            <Editor
                height="100%"
                defaultLanguage={language}
                language={language}
                value={value}
                onChange={onChange}
                onMount={handleEditorDidMount}
                options={{
                    minimap: { enabled: true, scale: 1, renderCharacters: false, side: 'right' },
                    fontSize: 14,
                    lineHeight: 22,
                    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                    fontLigatures: true,
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    padding: { top: 20, bottom: 20 },
                    renderLineHighlight: 'all',
                    lineNumbers: 'on',
                    glyphMargin: true,
                    folding: true,
                    links: true,
                    cursorSmoothCaretAnimation: 'on',
                    cursorBlinking: 'smooth',
                    smoothScrolling: true,
                }}
                theme="midnight-aurora"
            />
        </div>
    );
}

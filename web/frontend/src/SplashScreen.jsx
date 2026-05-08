import React, { useEffect, useState } from 'react';

export default function SplashScreen({ onComplete }) {
    const [stage, setStage] = useState(0);

    useEffect(() => {
        const timer1 = setTimeout(() => setStage(1), 500);
        const timer2 = setTimeout(() => setStage(2), 1500);
        const timer3 = setTimeout(() => onComplete(), 2200);

        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
            clearTimeout(timer3);
        };
    }, [onComplete]);

    return (
        <div className="fixed inset-0 bg-[#020617] flex flex-col items-center justify-center z-50 text-white transition-opacity duration-500">
            {/* Ambient Background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-500/20 rounded-full blur-[100px] opacity-50 animate-pulse"></div>
            </div>

            <div className="relative z-10 flex flex-col items-center">
                {/* Logo */}
                <div className={`mb-8 transition-all duration-1000 transform ${stage >= 1 ? 'scale-100 opacity-100' : 'scale-90 opacity-0'}`}>
                    <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/30 to-purple-500/30 rounded-3xl blur-2xl"></div>
                        <img
                            src="/logo.png"
                            alt="VDV463 Validator Logo"
                            className="relative w-32 h-32 object-contain drop-shadow-2xl"
                        />
                    </div>
                </div>

                <h1 className="text-4xl font-bold font-display tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                    VDV463 Validator
                </h1>

                <div className="mt-8 w-48 h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full bg-gradient-to-r from-indigo-500 to-blue-500 transition-all duration-[2000ms] ease-out ${stage > 0 ? 'w-full' : 'w-0'}`}></div>
                </div>

                <p className="text-slate-500 text-sm mt-4 font-medium tracking-wide uppercase">
                    Initializing Core
                </p>
            </div>
        </div>
    );
}

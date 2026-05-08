import React from 'react';
import { ArrowLeft, Scale, Shield, FileText } from 'lucide-react';
import { useTranslation } from './LanguageContext';

export default function LegalPages({ page, onClose }) {
    const { t, lang } = useTranslation();

    const impressumDE = (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Impressum</h2>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">Angaben gemäß § 5 TMG</h3>
                <p className="text-slate-300">
                    <strong className="text-white">[Ihr Unternehmen / Ihr Name]</strong><br />
                    [Straße und Hausnummer]<br />
                    [PLZ] [Ort]<br />
                    Deutschland
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">Kontakt</h3>
                <p className="text-slate-300">
                    Telefon: [Ihre Telefonnummer]<br />
                    E-Mail: [Ihre E-Mail-Adresse]
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">Umsatzsteuer-ID</h3>
                <p className="text-slate-300">
                    Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:<br />
                    DE [Ihre USt-ID]
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h3>
                <p className="text-slate-300">
                    [Name des Verantwortlichen]<br />
                    [Adresse wie oben]
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">Haftung für Inhalte</h3>
                <p className="text-slate-300">
                    Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten
                    nach den allgemeinen Gesetzen verantwortlich.
                </p>
            </section>
        </div>
    );

    const impressumEN = (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Legal Notice</h2>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">Information pursuant to § 5 TMG</h3>
                <p className="text-slate-300">
                    <strong className="text-white">[Your Company / Your Name]</strong><br />
                    [Street and House Number]<br />
                    [Postal Code] [City]<br />
                    Germany
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">Contact</h3>
                <p className="text-slate-300">
                    Phone: [Your Phone Number]<br />
                    Email: [Your Email Address]
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">Liability for Content</h3>
                <p className="text-slate-300">
                    As a service provider, we are responsible for our own content on these pages in accordance
                    with general laws pursuant to § 7 Abs.1 TMG.
                </p>
            </section>
        </div>
    );

    const datenschutzDE = (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Datenschutzerklärung</h2>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">1. Datenschutz auf einen Blick</h3>
                <p className="text-slate-300">
                    Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren
                    personenbezogenen Daten passiert, wenn Sie diese Website benutzen.
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">2. Datenerfassung</h3>
                <p className="text-slate-300">
                    Bei der Nutzung dieser Anwendung werden folgende Daten verarbeitet:
                </p>
                <ul className="list-disc list-inside text-slate-300 space-y-1">
                    <li>E-Mail-Adresse (bei Registrierung)</li>
                    <li>Passwort (verschlüsselt gespeichert)</li>
                    <li>Spracheinstellung</li>
                    <li>Hochgeladene JSON-Dateien zur Validierung (werden nicht dauerhaft gespeichert)</li>
                </ul>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">3. Ihre Rechte</h3>
                <p className="text-slate-300">
                    Sie haben jederzeit das Recht auf Auskunft, Berichtigung oder Löschung Ihrer Daten.
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">4. SSL/TLS-Verschlüsselung</h3>
                <p className="text-slate-300">
                    Diese Seite nutzt aus Sicherheitsgründen eine SSL- bzw. TLS-Verschlüsselung bei der
                    Übertragung von Daten. Eine verschlüsselte Verbindung erkennen Sie daran, dass die
                    Adresszeile des Browsers von „http://" auf „https://" wechselt.
                </p>
            </section>
        </div>
    );

    const datenschutzEN = (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Privacy Policy</h2>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">1. Privacy at a Glance</h3>
                <p className="text-slate-300">
                    The following notes provide a simple overview of what happens to your personal
                    data when you use this website.
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">2. Data Collection</h3>
                <p className="text-slate-300">
                    When using this application, the following data is processed:
                </p>
                <ul className="list-disc list-inside text-slate-300 space-y-1">
                    <li>Email address (upon registration)</li>
                    <li>Password (stored encrypted)</li>
                    <li>Language preference</li>
                    <li>Uploaded JSON files for validation (not permanently stored)</li>
                </ul>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">3. Your Rights</h3>
                <p className="text-slate-300">
                    You have the right to information, correction or deletion of your data at any time.
                </p>
            </section>

            <section className="space-y-2">
                <h3 className="text-lg font-semibold text-indigo-400">4. SSL/TLS Encryption</h3>
                <p className="text-slate-300">
                    This site uses SSL or TLS encryption for security reasons when transmitting data.
                    You can recognize an encrypted connection by the fact that the address line of the
                    browser changes from "http://" to "https://".
                </p>
            </section>
        </div>
    );

    const licenseDE = (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Lizenz & Hinweise</h2>

            <section className="space-y-4">
                <h3 className="text-lg font-semibold text-indigo-400">Software-Lizenz</h3>
                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                    <p className="text-white font-semibold mb-2">Apache License 2.0</p>
                    <p className="text-slate-300 text-sm">
                        Diese Software ist unter der Apache License, Version 2.0 lizenziert.
                        Sie dürfen diese Software nutzen, kopieren, modifizieren und verteilen,
                        vorausgesetzt, Sie erfüllen die Lizenzbedingungen.
                    </p>
                    <a
                        href="https://www.apache.org/licenses/LICENSE-2.0"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block mt-3 text-indigo-400 hover:underline text-sm"
                    >
                        → Vollständiger Lizenztext
                    </a>
                </div>
            </section>

            <section className="space-y-4">
                <h3 className="text-lg font-semibold text-indigo-400">VDV 463 Spezifikation</h3>
                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                    <p className="text-slate-300 text-sm mb-3">
                        Diese Anwendung implementiert die <strong className="text-white">VDV-Schrift 463</strong>
                        {' '}zur Beschreibung der Ladeinfrastruktur für Elektrobusse. Die Spezifikation
                        wurde vom <strong className="text-white">Verband Deutscher Verkehrsunternehmen (VDV)</strong>
                        {' '}entwickelt.
                    </p>
                    <p className="text-slate-300 text-sm mb-3">
                        VDV 463 definiert ein standardisiertes JSON-Format für den Austausch von
                        Informationen über Ladestationen, Depot-Layouts und Betriebsparameter für
                        die Elektrifizierung von ÖPNV-Flotten.
                    </p>
                    <div className="flex flex-wrap gap-3 mt-4">
                        <a
                            href="https://www.vdv.de"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-500/20 text-indigo-400 rounded-lg hover:bg-indigo-500/30 transition-colors text-sm"
                        >
                            VDV Website
                        </a>
                        <a
                            href="https://www.vdv.de/oepnv.aspx"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors text-sm"
                        >
                            VDV ÖPNV Standards
                        </a>
                    </div>
                </div>
            </section>

            <section className="space-y-4">
                <h3 className="text-lg font-semibold text-indigo-400">Haftungsausschluss</h3>
                <p className="text-slate-300 text-sm">
                    Diese Software wird "wie besehen" bereitgestellt, ohne jegliche ausdrückliche oder
                    stillschweigende Garantie. Der VDV463 Validator ist ein unabhängiges Tool und steht
                    in keiner offiziellen Verbindung zum VDV. Die Validierungsergebnisse dienen nur zur
                    Orientierung und ersetzen keine offizielle Zertifizierung.
                </p>
            </section>

            <section className="space-y-4">
                <h3 className="text-lg font-semibold text-indigo-400">Open Source</h3>
                <p className="text-slate-300 text-sm">
                    Der Quellcode dieser Anwendung ist auf GitHub verfügbar. Beiträge und Verbesserungsvorschläge
                    sind willkommen!
                </p>
                <a
                    href="https://github.com/martinfrenzel/vdv463-validator"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors text-sm"
                >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                    </svg>
                    GitHub Repository
                </a>
            </section>
        </div>
    );

    const licenseEN = (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">License & References</h2>

            <section className="space-y-4">
                <h3 className="text-lg font-semibold text-indigo-400">Software License</h3>
                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                    <p className="text-white font-semibold mb-2">Apache License 2.0</p>
                    <p className="text-slate-300 text-sm">
                        This software is licensed under the Apache License, Version 2.0.
                        You may use, copy, modify, and distribute this software, provided
                        you comply with the license terms.
                    </p>
                    <a
                        href="https://www.apache.org/licenses/LICENSE-2.0"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block mt-3 text-indigo-400 hover:underline text-sm"
                    >
                        → Full License Text
                    </a>
                </div>
            </section>

            <section className="space-y-4">
                <h3 className="text-lg font-semibold text-indigo-400">VDV 463 Specification</h3>
                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                    <p className="text-slate-300 text-sm mb-3">
                        This application implements the <strong className="text-white">VDV-Schrift 463</strong>
                        {' '}for describing the charging infrastructure for electric buses. The specification
                        was developed by the <strong className="text-white">Verband Deutscher Verkehrsunternehmen (VDV)</strong>
                        {' '}(Association of German Transport Companies).
                    </p>
                    <p className="text-slate-300 text-sm mb-3">
                        VDV 463 defines a standardized JSON format for exchanging information about
                        charging stations, depot layouts, and operational parameters for the
                        electrification of public transit fleets.
                    </p>
                    <div className="flex flex-wrap gap-3 mt-4">
                        <a
                            href="https://www.vdv.de"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-500/20 text-indigo-400 rounded-lg hover:bg-indigo-500/30 transition-colors text-sm"
                        >
                            VDV Website
                        </a>
                        <a
                            href="https://www.vdv.de/oepnv.aspx"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors text-sm"
                        >
                            VDV Public Transit Standards
                        </a>
                    </div>
                </div>
            </section>

            <section className="space-y-4">
                <h3 className="text-lg font-semibold text-indigo-400">Disclaimer</h3>
                <p className="text-slate-300 text-sm">
                    This software is provided "as is", without warranty of any kind, express or
                    implied. The VDV463 Validator is an independent tool and has no official
                    affiliation with VDV. The validation results serve only as guidance and do
                    not replace official certification.
                </p>
            </section>

            <section className="space-y-4">
                <h3 className="text-lg font-semibold text-indigo-400">Open Source</h3>
                <p className="text-slate-300 text-sm">
                    The source code of this application is available on GitHub. Contributions and
                    improvement suggestions are welcome!
                </p>
                <a
                    href="https://github.com/martinfrenzel/vdv463-validator"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors text-sm"
                >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                    </svg>
                    GitHub Repository
                </a>
            </section>
        </div>
    );

    const getContent = () => {
        if (page === 'impressum') {
            return lang === 'de' ? impressumDE : impressumEN;
        }
        if (page === 'license') {
            return lang === 'de' ? licenseDE : licenseEN;
        }
        return lang === 'de' ? datenschutzDE : datenschutzEN;
    };

    const getIcon = () => {
        if (page === 'impressum') return <Scale size={24} className="text-indigo-400" />;
        if (page === 'license') return <FileText size={24} className="text-indigo-400" />;
        return <Shield size={24} className="text-indigo-400" />;
    };

    const getTitle = () => {
        if (page === 'impressum') return lang === 'de' ? 'Impressum' : 'Legal Notice';
        if (page === 'license') return lang === 'de' ? 'Lizenz & Hinweise' : 'License & References';
        return lang === 'de' ? 'Datenschutz' : 'Privacy Policy';
    };

    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-500/20 rounded-xl">
                            {getIcon()}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">{getTitle()}</h2>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="flex items-center gap-2 px-4 py-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all"
                    >
                        <ArrowLeft size={16} />
                        {lang === 'de' ? 'Zurück' : 'Back'}
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                    {getContent()}

                    {page !== 'license' && (
                        <div className="mt-8 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                            <p className="text-amber-400 text-sm">
                                <strong>{lang === 'de' ? 'Hinweis:' : 'Note:'}</strong>{' '}
                                {lang === 'de'
                                    ? 'Die Platzhalter in eckigen Klammern [] müssen mit Ihren tatsächlichen Daten ersetzt werden.'
                                    : 'The placeholders in square brackets [] must be replaced with your actual data.'
                                }
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

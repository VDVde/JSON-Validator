import React, { createContext, useContext, useState, useEffect } from 'react';

const translations = {
    en: {
        // App
        'app.title': 'VDV463 Validator',
        'app.subtitle': 'Validate your VDV463 messages with precision.',

        // Toolbar
        'toolbar.open_files': 'Open File',
        'toolbar.save_json': 'Save JSON',
        'toolbar.validate': 'Validate',
        'toolbar.run_validation': 'Run Validation',
        'toolbar.format_json': 'Format JSON',
        'toolbar.clear_results': 'Clear Results',
        'toolbar.tooltip_open': 'Open a VDV463 JSON file (Ctrl+O)',
        'toolbar.tooltip_save': 'Save current content (Ctrl+S)',
        'toolbar.tooltip_validate': 'Run validation (Ctrl+Enter)',
        'toolbar.tooltip_format': 'Format JSON (Ctrl+Shift+F)',

        // Panels
        'panel.files': 'Files & Configuration',
        'panel.workspace': 'Workspace',
        'panel.editor': 'Editor',
        'panel.results': 'Validation Results',
        'panel.audit_report': 'Audit Report',

        // Settings / File Panel
        'settings.title': 'Configuration',
        'settings.schema_version': 'Schema Version',
        'settings.schema_auto': 'Auto Detect',
        'settings.schema_only': 'Schema Check Only',
        'settings.schema_only_desc': 'Ignore business rules.',
        'settings.custom_rules': 'Custom Rules',
        'settings.custom_rules_desc': 'Upload a .json or .yaml file to apply specific validation rules.',
        'settings.upload_config': 'Upload Rules',
        'settings.uploading': 'Uploading...',
        'settings.invalid_config': 'Invalid Config',
        'settings.current_file': 'Current File',
        'settings.no_file': 'No file loaded',
        'settings.size': 'Size',

        // Editor
        'editor.raw': 'JSON',
        'editor.tree': 'Tree',
        'editor.graph': 'Schema',
        'editor.empty': 'No content to display',

        // Results
        'results.title': 'Validation Report',
        'results.no_issues': 'No critical issues found.',
        'results.check_issues': 'Detailed Issues',
        'results.errors': 'Errors',
        'results.warnings': 'Warnings',
        'results.success_msg': 'Validation Successful',
        'results.success_desc': 'The file complies with the selected VDV463 schema.',
        'results.empty_state': 'Run validation to see results here.',

        // Auth - Basic
        'auth.login_title': 'Welcome back',
        'auth.login_subtitle': 'Sign in to continue',
        'auth.register_title': 'Create account',
        'auth.register_subtitle': 'Register for a new account',
        'auth.forgot_title': 'Forgot password?',
        'auth.forgot_subtitle': 'Enter your email to receive a reset link',
        'auth.username': 'Username',
        'auth.email': 'Email address',
        'auth.password': 'Password',
        'auth.confirm_password': 'Confirm password',
        'auth.language': 'Language',
        'auth.signin': 'Sign In',
        'auth.register': 'Register',
        'auth.send_reset_link': 'Send reset link',
        'auth.forgot_password': 'Forgot password?',
        'auth.or': 'or',
        'auth.no_account': 'Don\'t have an account?',
        'auth.register_now': 'Register now',
        'auth.have_account': 'Already have an account?',
        'auth.login_now': 'Sign in now',
        'auth.back_to_login': 'Back to login',
        'auth.check_email': 'Please check your email to verify your account.',
        'auth.reset_email_sent': 'If the email exists, you will receive a reset link.',
        'auth.passwords_not_match': 'Passwords do not match.',
        'auth.password_requirements': 'At least 8 characters, 1 uppercase, 1 number, 1 special character',
        'auth.logout': 'Logout',
        'auth.profile': 'Profile',
        'auth.welcome_back': 'Welcome Back',
        'auth.tagline': 'Validate your VDV463 messages securely and easily.',

        // Admin Panel
        'admin.title': 'User Management',
        'admin.subtitle': 'Manage all registered users',
        'admin.search_users': 'Search users...',
        'admin.add_user': 'Add user',
        'admin.col_email': 'Email',
        'admin.col_role': 'Role',
        'admin.col_language': 'Language',
        'admin.col_status': 'Status',
        'admin.col_created': 'Created',
        'admin.col_actions': 'Actions',
        'admin.active': 'Active',
        'admin.inactive': 'Inactive',
        'admin.verified': 'Verified',
        'admin.unverified': 'Unverified',
        'admin.edit': 'Edit',
        'admin.delete': 'Delete',
        'admin.activate': 'Activate',
        'admin.deactivate': 'Deactivate',
        'admin.you': '(you)',
        'admin.create_user': 'Create new user',
        'admin.optional': 'optional',
        'admin.password_placeholder': 'Leave empty for OAuth users',
        'admin.mark_verified': 'Mark as verified',
        'admin.cancel': 'Cancel',
        'admin.create': 'Create',
        'admin.user_created': 'User created successfully.',
        'admin.user_updated': 'User updated successfully.',
        'admin.user_deleted': 'User deleted successfully.',
        'admin.confirm_delete': 'Are you sure you want to delete this user?',

        // User Menu
        'menu.admin': 'Admin Panel',
        'menu.settings': 'Settings',
        'menu.logout': 'Logout',

        // Footer / Legal
        'footer.impressum': 'Legal Notice',
        'footer.privacy': 'Privacy Policy',
        'footer.license': 'License',
        'footer.system_online': 'System Online',
    },
    de: {
        // App
        'app.title': 'VDV463 Validator',
        'app.subtitle': 'Validieren Sie Ihre VDV463-Nachrichten präzise.',

        // Toolbar
        'toolbar.open_files': 'Datei öffnen',
        'toolbar.save_json': 'Speichern',
        'toolbar.validate': 'Validieren',
        'toolbar.run_validation': 'Validierung starten',
        'toolbar.format_json': 'Formatieren',
        'toolbar.clear_results': 'Ergebnisse löschen',
        'toolbar.tooltip_open': 'VDV463 JSON Datei öffnen (Ctrl+O)',
        'toolbar.tooltip_save': 'Inhalt speichern (Ctrl+S)',
        'toolbar.tooltip_validate': 'Validierung ausführen (Ctrl+Enter)',
        'toolbar.tooltip_format': 'JSON formatieren (Ctrl+Shift+F)',

        // Panels
        'panel.files': 'Dateien & Konfiguration',
        'panel.workspace': 'Arbeitsbereich',
        'panel.editor': 'Editor',
        'panel.results': 'Validierungsergebnisse',
        'panel.audit_report': 'Prüfbericht',

        // Settings / File Panel
        'settings.title': 'Konfiguration',
        'settings.schema_version': 'Schema Version',
        'settings.schema_auto': 'Automatisch',
        'settings.schema_only': 'Nur Schema prüfen',
        'settings.schema_only_desc': 'Geschäftsregeln ignorieren.',
        'settings.custom_rules': 'Benutzerdefinierte Regeln',
        'settings.custom_rules_desc': 'Laden Sie eine .json oder .yaml Datei hoch, um spezifische Regeln anzuwenden.',
        'settings.upload_config': 'Regeln hochladen',
        'settings.uploading': 'Wird hochgeladen...',
        'settings.invalid_config': 'Ungültige Konfiguration',
        'settings.current_file': 'Aktuelle Datei',
        'settings.no_file': 'Keine Datei geladen',
        'settings.size': 'Größe',

        // Editor
        'editor.raw': 'JSON',
        'editor.tree': 'Baum',
        'editor.graph': 'Schema',
        'editor.empty': 'Kein Inhalt anzuzeigen',

        // Results
        'results.title': 'Validierungsbericht',
        'results.no_issues': 'Keine kritischen Probleme gefunden.',
        'results.check_issues': 'Detaillierte Probleme',
        'results.errors': 'Fehler',
        'results.warnings': 'Warnungen',
        'results.success_msg': 'Validierung erfolgreich',
        'results.success_desc': 'Die Datei entspricht dem gewählten VDV463-Schema.',
        'results.empty_state': 'Starten Sie die Validierung für Ergebnisse.',

        // Auth - Basic
        'auth.login_title': 'Willkommen zurück',
        'auth.login_subtitle': 'Melden Sie sich an, um fortzufahren',
        'auth.register_title': 'Konto erstellen',
        'auth.register_subtitle': 'Registrieren Sie sich für ein neues Konto',
        'auth.forgot_title': 'Passwort vergessen?',
        'auth.forgot_subtitle': 'Geben Sie Ihre E-Mail-Adresse ein, um einen Reset-Link zu erhalten',
        'auth.username': 'Benutzername',
        'auth.email': 'E-Mail-Adresse',
        'auth.password': 'Passwort',
        'auth.confirm_password': 'Passwort bestätigen',
        'auth.language': 'Sprache',
        'auth.signin': 'Anmelden',
        'auth.register': 'Registrieren',
        'auth.send_reset_link': 'Reset-Link senden',
        'auth.forgot_password': 'Passwort vergessen?',
        'auth.or': 'oder',
        'auth.no_account': 'Noch kein Konto?',
        'auth.register_now': 'Jetzt registrieren',
        'auth.have_account': 'Bereits ein Konto?',
        'auth.login_now': 'Jetzt anmelden',
        'auth.back_to_login': 'Zurück zur Anmeldung',
        'auth.check_email': 'Bitte überprüfen Sie Ihre E-Mails, um Ihr Konto zu verifizieren.',
        'auth.reset_email_sent': 'Wenn die E-Mail-Adresse existiert, erhalten Sie einen Reset-Link.',
        'auth.passwords_not_match': 'Die Passwörter stimmen nicht überein.',
        'auth.password_requirements': 'Mindestens 8 Zeichen, 1 Großbuchstabe, 1 Zahl, 1 Sonderzeichen',
        'auth.logout': 'Abmelden',
        'auth.profile': 'Profil',
        'auth.welcome_back': 'Willkommen zurück',
        'auth.tagline': 'Validieren Sie Ihre VDV463-Nachrichten sicher und einfach.',

        // Admin Panel
        'admin.title': 'Benutzerverwaltung',
        'admin.subtitle': 'Verwalten Sie alle registrierten Benutzer',
        'admin.search_users': 'Benutzer suchen...',
        'admin.add_user': 'Benutzer hinzufügen',
        'admin.col_email': 'E-Mail',
        'admin.col_role': 'Rolle',
        'admin.col_language': 'Sprache',
        'admin.col_status': 'Status',
        'admin.col_created': 'Erstellt',
        'admin.col_actions': 'Aktionen',
        'admin.active': 'Aktiv',
        'admin.inactive': 'Inaktiv',
        'admin.verified': 'Verifiziert',
        'admin.unverified': 'Nicht verifiziert',
        'admin.edit': 'Bearbeiten',
        'admin.delete': 'Löschen',
        'admin.activate': 'Aktivieren',
        'admin.deactivate': 'Deaktivieren',
        'admin.you': '(Sie)',
        'admin.create_user': 'Neuen Benutzer erstellen',
        'admin.optional': 'optional',
        'admin.password_placeholder': 'Leer lassen für OAuth-Benutzer',
        'admin.mark_verified': 'Als verifiziert markieren',
        'admin.cancel': 'Abbrechen',
        'admin.create': 'Erstellen',
        'admin.user_created': 'Benutzer erfolgreich erstellt.',
        'admin.user_updated': 'Benutzer erfolgreich aktualisiert.',
        'admin.user_deleted': 'Benutzer erfolgreich gelöscht.',
        'admin.confirm_delete': 'Sind Sie sicher, dass Sie diesen Benutzer löschen möchten?',

        // User Menu
        'menu.admin': 'Admin-Panel',
        'menu.settings': 'Einstellungen',
        'menu.logout': 'Abmelden',

        // Footer / Legal
        'footer.impressum': 'Impressum',
        'footer.privacy': 'Datenschutz',
        'footer.license': 'Lizenz',
        'footer.system_online': 'System Online',
    }
};

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
    const [lang, setLang] = useState(() => {
        // Check localStorage first, then browser language
        const saved = localStorage.getItem('language');
        if (saved && (saved === 'de' || saved === 'en')) {
            return saved;
        }
        const browserLang = navigator.language.toLowerCase();
        return browserLang.startsWith('de') ? 'de' : 'en';
    });

    useEffect(() => {
        localStorage.setItem('language', lang);
    }, [lang]);

    const t = (key) => translations[lang][key] || key;

    const toggleLanguage = () => {
        setLang(prev => prev === 'en' ? 'de' : 'en');
    };

    return (
        <LanguageContext.Provider value={{ lang, setLang, t, toggleLanguage }}>
            {children}
        </LanguageContext.Provider>
    );
}

export function useTranslation() {
    const context = useContext(LanguageContext);
    if (!context) {
        throw new Error('useTranslation must be used within a LanguageProvider');
    }
    return context;
}

export default LanguageContext;

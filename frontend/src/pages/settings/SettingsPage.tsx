import { Container } from '../../components/layout';

export const SettingsPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <Container className="py-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-8">
          Settings
        </h1>
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
          <p className="text-slate-600 dark:text-slate-400">
            Application settings will be implemented here.
          </p>
        </div>
      </Container>
    </div>
  );
};
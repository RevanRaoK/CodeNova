import { Container } from '../../components/layout';

export const LoginPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
      <Container>
        <div className="max-w-md mx-auto bg-white dark:bg-slate-800 rounded-lg shadow-lg p-8">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 text-center">
            Sign In
          </h1>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Email
              </label>
              <input
                type="email"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-slate-700 dark:text-slate-100"
                placeholder="Enter your email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Password
              </label>
              <input
                type="password"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-slate-700 dark:text-slate-100"
                placeholder="Enter your password"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md font-medium transition-colors"
            >
              Sign In
            </button>
          </form>
        </div>
      </Container>
    </div>
  );
};
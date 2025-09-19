import { Container } from '../../components/layout';

export const HomePage = () => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <Container className="py-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-6">
            Welcome to CodeReview AI
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 mb-8 max-w-2xl mx-auto">
            Intelligent code review with pattern learning to help you write better code.
          </p>
          <div className="space-x-4">
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors">
              Get Started
            </button>
            <button className="border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 px-6 py-3 rounded-lg font-medium hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
              Learn More
            </button>
          </div>
        </div>
      </Container>
    </div>
  );
};
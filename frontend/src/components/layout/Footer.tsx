import { clsx } from 'clsx';
import { Container } from './Container';
import { Icon } from '../ui/Icon';

interface FooterProps {
  className?: string;
}

export const Footer = ({ className }: FooterProps) => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className={clsx(
      'bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 mt-auto',
      className
    )}>
      <Container>
        <div className="py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Brand and Description */}
            <div className="md:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <Icon 
                  name="code-bracket" 
                  size="lg" 
                  className="text-blue-600 dark:text-blue-400" 
                />
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  CodeReview AI
                </h3>
              </div>
              <p className="text-slate-600 dark:text-slate-400 mb-4 max-w-md">
                Intelligent code review with pattern learning. Improve your code quality 
                with AI-powered suggestions and personalized feedback.
              </p>
              <div className="flex space-x-4">
                <a 
                  href="#" 
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                  aria-label="GitHub"
                >
                  <Icon name="link" size="sm" />
                </a>
                <a 
                  href="#" 
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                  aria-label="Twitter"
                >
                  <Icon name="share" size="sm" />
                </a>
                <a 
                  href="#" 
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                  aria-label="LinkedIn"
                >
                  <Icon name="link" size="sm" />
                </a>
              </div>
            </div>

            {/* Product Links */}
            <div>
              <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
                Product
              </h4>
              <ul className="space-y-3">
                <li>
                  <a 
                    href="/features" 
                    className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a 
                    href="/pricing" 
                    className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <a 
                    href="/integrations" 
                    className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
                  >
                    Integrations
                  </a>
                </li>
                <li>
                  <a 
                    href="/api" 
                    className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
                  >
                    API
                  </a>
                </li>
              </ul>
            </div>

            {/* Support Links */}
            <div>
              <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">
                Support
              </h4>
              <ul className="space-y-3">
                <li>
                  <a 
                    href="/docs" 
                    className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
                  >
                    Documentation
                  </a>
                </li>
                <li>
                  <a 
                    href="/help" 
                    className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
                  >
                    Help Center
                  </a>
                </li>
                <li>
                  <a 
                    href="/contact" 
                    className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
                  >
                    Contact Us
                  </a>
                </li>
                <li>
                  <a 
                    href="/status" 
                    className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
                  >
                    Status
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom section */}
          <div className="border-t border-slate-200 dark:border-slate-800 mt-8 pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
              <div className="flex flex-col md:flex-row items-center space-y-2 md:space-y-0 md:space-x-6">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  © {currentYear} CodeReview AI. All rights reserved.
                </p>
                <div className="flex space-x-6">
                  <a 
                    href="/privacy" 
                    className="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300 transition-colors"
                  >
                    Privacy Policy
                  </a>
                  <a 
                    href="/terms" 
                    className="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300 transition-colors"
                  >
                    Terms of Service
                  </a>
                  <a 
                    href="/cookies" 
                    className="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300 transition-colors"
                  >
                    Cookie Policy
                  </a>
                </div>
              </div>
              
              <div className="flex items-center space-x-2 text-sm text-slate-500 dark:text-slate-400">
                <span>Made with</span>
                <Icon name="heart" size="xs" className="text-red-500" />
                <span>for developers</span>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </footer>
  );
};
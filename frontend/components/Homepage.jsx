import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
     ArrowRightIcon,
     BrainIcon,
     LineChartIcon,
     ShieldIcon,
     CheckIcon,
     UsersIcon,
     TrendingUpIcon,
     GitBranchIcon,
     MailIcon,
     PhoneIcon,
     MapPinIcon
} from 'lucide-react';
import contactService from '../services/contactService';

export function Homepage() {
     const [contactForm, setContactForm] = useState({
          name: '',
          email: '',
          company: '',
          message: '',
          subject: 'general'
     });
     const [isSubmitting, setIsSubmitting] = useState(false);
     const [submitStatus, setSubmitStatus] = useState(null);
     const [errors, setErrors] = useState({});

     // Track page visit for analytics
     useEffect(() => {
          const trackPageVisit = async () => {
               try {
                    await contactService.trackVisit({
                         page: 'homepage',
                         timestamp: new Date().toISOString(),
                         userAgent: navigator.userAgent,
                         referrer: document.referrer
                    });
               } catch (error) {
                    console.log('Analytics tracking failed:', error);
               }
          };

          trackPageVisit();
     }, []);

     const validateForm = () => {
          const newErrors = {};

          if (!contactForm.name.trim()) {
               newErrors.name = 'Name is required';
          }

          if (!contactForm.email.trim()) {
               newErrors.email = 'Email is required';
          } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactForm.email)) {
               newErrors.email = 'Please enter a valid email address';
          }

          if (!contactForm.message.trim()) {
               newErrors.message = 'Message is required';
          } else if (contactForm.message.trim().length < 10) {
               newErrors.message = 'Message must be at least 10 characters long';
          }

          setErrors(newErrors);
          return Object.keys(newErrors).length === 0;
     };

     const handleContactSubmit = async (e) => {
          e.preventDefault();

          if (!validateForm()) {
               return;
          }

          setIsSubmitting(true);
          setSubmitStatus(null);

          try {
               await contactService.submitContactForm({
                    ...contactForm,
                    timestamp: new Date().toISOString()
               });

               setSubmitStatus('success');
               setContactForm({
                    name: '',
                    email: '',
                    company: '',
                    message: '',
                    subject: 'general'
               });
               setErrors({});
          } catch (error) {
               console.error('Contact form submission failed:', error);
               setSubmitStatus('error');
          } finally {
               setIsSubmitting(false);
          }
     };

     const handleInputChange = (e) => {
          const { name, value } = e.target;
          setContactForm(prev => ({
               ...prev,
               [name]: value
          }));

          // Clear error when user starts typing
          if (errors[name]) {
               setErrors(prev => ({
                    ...prev,
                    [name]: ''
               }));
          }
     };

     const pricingTiers = [
          {
               name: 'Starter',
               price: 'Free',
               description: 'Perfect for individual developers and small projects',
               features: [
                    'Up to 10 code reviews per month',
                    'Basic AI suggestions',
                    'Standard security scanning',
                    'Email support',
                    'Community access'
               ],
               buttonText: 'Get Started',
               buttonLink: '/signup',
               popular: false
          },
          {
               name: 'Professional',
               price: '$29',
               period: '/month',
               description: 'Ideal for growing teams and regular development work',
               features: [
                    'Unlimited code reviews',
                    'Advanced AI suggestions with learning',
                    'Priority security scanning',
                    'GitHub integration',
                    'Team analytics dashboard',
                    'Priority email support',
                    'Custom rejection reasons'
               ],
               buttonText: 'Start Free Trial',
               buttonLink: '/signup?plan=professional',
               popular: true
          },
          {
               name: 'Enterprise',
               price: 'Custom',
               description: 'For large organizations with advanced requirements',
               features: [
                    'Everything in Professional',
                    'Custom AI model training',
                    'Advanced team management',
                    'SSO integration',
                    'Custom integrations',
                    'Dedicated support',
                    'SLA guarantees',
                    'On-premise deployment options'
               ],
               buttonText: 'Contact Sales',
               buttonLink: '#contact',
               popular: false
          }
     ];

     return (
          <div className="bg-white">

               {/* Hero Section */}
               <section className="bg-gradient-to-r from-indigo-600 to-purple-600 py-20">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                         <div className="text-center">
                              <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
                                   Next-Generation Code Review
                                   <span className="block text-indigo-200">with CodeNova AI</span>
                              </h1>
                              <p className="text-xl md:text-2xl text-indigo-100 mb-8 max-w-3xl mx-auto">
                                   Revolutionize your development process with CodeNova's intelligent AI that learns from your codebase,
                                   provides contextual feedback, and elevates your team's coding standards.
                              </p>
                              <div className="flex flex-col sm:flex-row justify-center gap-4 mb-12">
                                   <Link
                                        to="/signup"
                                        className="bg-white text-indigo-600 hover:bg-gray-100 px-8 py-4 rounded-lg font-semibold text-lg flex items-center justify-center transition-colors"
                                   >
                                        Start Free Trial
                                        <ArrowRightIcon className="ml-2 h-5 w-5" />
                                   </Link>
                                   <Link
                                        to="/login"
                                        className="bg-indigo-700 hover:bg-indigo-800 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-colors"
                                   >
                                        Sign In
                                   </Link>
                              </div>

                              {/* Stats */}
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
                                   <div className="text-center">
                                        <div className="text-3xl font-bold text-white mb-2">500+</div>
                                        <div className="text-indigo-200">Code Reviews Completed</div>
                                   </div>
                                   <div className="text-center">
                                        <div className="text-3xl font-bold text-white mb-2">95%</div>
                                        <div className="text-indigo-200">Bug Detection Rate</div>
                                   </div>
                                   <div className="text-center">
                                        <div className="text-3xl font-bold text-white mb-2">50%</div>
                                        <div className="text-indigo-200">Faster Review Process</div>
                                   </div>
                              </div>
                         </div>
                    </div>
               </section>

               {/* Features Section */}
               <section id="features" className="py-20 bg-gray-50">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                         <div className="text-center mb-16">
                              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                                   Powerful Features for Modern Development
                              </h2>
                              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                                   Our AI-powered platform provides comprehensive code analysis with intelligent learning capabilities
                              </p>
                         </div>

                         <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
                              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                                   <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-6">
                                        <BrainIcon className="h-6 w-6 text-indigo-600" />
                                   </div>
                                   <h3 className="text-xl font-semibold mb-4 text-gray-900">AI-Powered Analysis</h3>
                                   <p className="text-gray-600">
                                        Advanced machine learning algorithms analyze your code for bugs, security vulnerabilities,
                                        and optimization opportunities with unprecedented accuracy.
                                   </p>
                              </div>

                              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                                   <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-6">
                                        <TrendingUpIcon className="h-6 w-6 text-indigo-600" />
                                   </div>
                                   <h3 className="text-xl font-semibold mb-4 text-gray-900">Pattern Learning</h3>
                                   <p className="text-gray-600">
                                        Our system continuously learns from code patterns across projects to provide
                                        increasingly relevant and personalized recommendations.
                                   </p>
                              </div>

                              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                                   <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-6">
                                        <GitBranchIcon className="h-6 w-6 text-indigo-600" />
                                   </div>
                                   <h3 className="text-xl font-semibold mb-4 text-gray-900">GitHub Integration</h3>
                                   <p className="text-gray-600">
                                        Seamlessly integrate with your GitHub workflow. Automatic PR analysis,
                                        issue creation, and comment posting keep your team in sync.
                                   </p>
                              </div>

                              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                                   <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-6">
                                        <LineChartIcon className="h-6 w-6 text-indigo-600" />
                                   </div>
                                   <h3 className="text-xl font-semibold mb-4 text-gray-900">Analytics Dashboard</h3>
                                   <p className="text-gray-600">
                                        Comprehensive analytics and reporting help you track code quality improvements,
                                        team performance, and AI model learning progress over time.
                                   </p>
                              </div>

                              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                                   <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-6">
                                        <ShieldIcon className="h-6 w-6 text-indigo-600" />
                                   </div>
                                   <h3 className="text-xl font-semibold mb-4 text-gray-900">Security Scanning</h3>
                                   <p className="text-gray-600">
                                        Advanced security vulnerability detection with actionable remediation guidance
                                        helps keep your codebase secure and compliant.
                                   </p>
                              </div>

                              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                                   <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-6">
                                        <UsersIcon className="h-6 w-6 text-indigo-600" />
                                   </div>
                                   <h3 className="text-xl font-semibold mb-4 text-gray-900">Team Management</h3>
                                   <p className="text-gray-600">
                                        Powerful admin controls for user management, role assignment, and team analytics
                                        provide complete oversight of your development process.
                                   </p>
                              </div>
                         </div>
                    </div>
               </section>

               {/* Pricing Section */}
               <section id="pricing" className="py-20 bg-white">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                         <div className="text-center mb-16">
                              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                                   Simple, Transparent Pricing
                              </h2>
                              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                                   Choose the plan that fits your team size and requirements. All plans include our core AI features.
                              </p>
                         </div>

                         <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                              {pricingTiers.map((tier, index) => (
                                   <div
                                        key={index}
                                        className={`relative bg-white rounded-2xl shadow-lg border-2 p-8 ${tier.popular
                                             ? 'border-indigo-500 ring-2 ring-indigo-200'
                                             : 'border-gray-200'
                                             }`}
                                   >
                                        {tier.popular && (
                                             <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                                                  <span className="bg-indigo-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                                                       Most Popular
                                                  </span>
                                             </div>
                                        )}

                                        <div className="text-center mb-8">
                                             <h3 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                                             <div className="mb-4">
                                                  <span className="text-4xl font-bold text-gray-900">{tier.price}</span>
                                                  {tier.period && <span className="text-gray-600">{tier.period}</span>}
                                             </div>
                                             <p className="text-gray-600">{tier.description}</p>
                                        </div>

                                        <ul className="space-y-4 mb-8">
                                             {tier.features.map((feature, featureIndex) => (
                                                  <li key={featureIndex} className="flex items-start">
                                                       <CheckIcon className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                                                       <span className="text-gray-700">{feature}</span>
                                                  </li>
                                             ))}
                                        </ul>

                                        <div className="text-center">
                                             {tier.buttonLink.startsWith('#') ? (
                                                  <a
                                                       href={tier.buttonLink}
                                                       className={`w-full inline-block px-6 py-3 rounded-lg font-semibold transition-colors ${tier.popular
                                                            ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                                                            : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
                                                            }`}
                                                  >
                                                       {tier.buttonText}
                                                  </a>
                                             ) : (
                                                  <Link
                                                       to={tier.buttonLink}
                                                       className={`w-full inline-block px-6 py-3 rounded-lg font-semibold transition-colors ${tier.popular
                                                            ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                                                            : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
                                                            }`}
                                                  >
                                                       {tier.buttonText}
                                                  </Link>
                                             )}
                                        </div>
                                   </div>
                              ))}
                         </div>
                    </div>
               </section>

               {/* Contact Section */}
               <section id="contact" className="py-20 bg-gray-50">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                         <div className="text-center mb-16">
                              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                                   Get in Touch
                              </h2>
                              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                                   Have questions about our platform? Want to discuss enterprise solutions?
                                   We'd love to hear from you.
                              </p>
                         </div>

                         <div className="grid lg:grid-cols-2 gap-12">
                              {/* Contact Form */}
                              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
                                   <h3 className="text-2xl font-semibold text-gray-900 mb-6">Send us a message</h3>

                                   {submitStatus === 'success' && (
                                        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                                             <p className="text-green-800">
                                                  Thank you for your message! We'll get back to you within 24 hours.
                                             </p>
                                        </div>
                                   )}

                                   {submitStatus === 'error' && (
                                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                                             <p className="text-red-800">
                                                  Sorry, there was an error sending your message. Please try again or contact us directly.
                                             </p>
                                        </div>
                                   )}

                                   <form onSubmit={handleContactSubmit} className="space-y-6">
                                        <div className="grid md:grid-cols-2 gap-6">
                                             <div>
                                                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                                                       Name *
                                                  </label>
                                                  <input
                                                       type="text"
                                                       id="name"
                                                       name="name"
                                                       value={contactForm.name}
                                                       onChange={handleInputChange}
                                                       className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${errors.name ? 'border-red-300' : 'border-gray-300'
                                                            }`}
                                                       placeholder="Your full name"
                                                  />
                                                  {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
                                             </div>

                                             <div>
                                                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                                                       Email *
                                                  </label>
                                                  <input
                                                       type="email"
                                                       id="email"
                                                       name="email"
                                                       value={contactForm.email}
                                                       onChange={handleInputChange}
                                                       className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${errors.email ? 'border-red-300' : 'border-gray-300'
                                                            }`}
                                                       placeholder="your.email@company.com"
                                                  />
                                                  {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
                                             </div>
                                        </div>

                                        <div className="grid md:grid-cols-2 gap-6">
                                             <div>
                                                  <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-2">
                                                       Company
                                                  </label>
                                                  <input
                                                       type="text"
                                                       id="company"
                                                       name="company"
                                                       value={contactForm.company}
                                                       onChange={handleInputChange}
                                                       className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                                       placeholder="Your company name"
                                                  />
                                             </div>

                                             <div>
                                                  <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
                                                       Subject
                                                  </label>
                                                  <select
                                                       id="subject"
                                                       name="subject"
                                                       value={contactForm.subject}
                                                       onChange={handleInputChange}
                                                       className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                                  >
                                                       <option value="general">General Inquiry</option>
                                                       <option value="sales">Sales</option>
                                                       <option value="support">Technical Support</option>
                                                       <option value="partnership">Partnership</option>
                                                       <option value="enterprise">Enterprise Solutions</option>
                                                  </select>
                                             </div>
                                        </div>

                                        <div>
                                             <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
                                                  Message *
                                             </label>
                                             <textarea
                                                  id="message"
                                                  name="message"
                                                  rows={6}
                                                  value={contactForm.message}
                                                  onChange={handleInputChange}
                                                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${errors.message ? 'border-red-300' : 'border-gray-300'
                                                       }`}
                                                  placeholder="Tell us about your project, questions, or how we can help..."
                                             />
                                             {errors.message && <p className="mt-1 text-sm text-red-600">{errors.message}</p>}
                                        </div>

                                        <button
                                             type="submit"
                                             disabled={isSubmitting}
                                             className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center"
                                        >
                                             {isSubmitting ? (
                                                  <>
                                                       <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                                                       Sending...
                                                  </>
                                             ) : (
                                                  <>
                                                       Send Message
                                                       <ArrowRightIcon className="ml-2 h-5 w-5" />
                                                  </>
                                             )}
                                        </button>
                                   </form>
                              </div>

                              {/* Contact Information */}
                              <div className="space-y-8">
                                   <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
                                        <h3 className="text-2xl font-semibold text-gray-900 mb-6">Contact Information</h3>

                                        <div className="space-y-6">
                                             <div className="flex items-start">
                                                  <MailIcon className="h-6 w-6 text-indigo-600 mr-4 mt-1" />
                                                  <div>
                                                       <h4 className="font-semibold text-gray-900">Email</h4>
                                                       <p className="text-gray-600">kokkiralarevan2005@gmail.com</p>
                                                       <p className="text-gray-600">rachapranavanadh@gmail.com</p>
                                                  </div>
                                             </div>

                                             <div className="flex items-start">
                                                  <PhoneIcon className="h-6 w-6 text-indigo-600 mr-4 mt-1" />
                                                  <div>
                                                       <h4 className="font-semibold text-gray-900">Phone</h4>
                                                       <p className="text-gray-600">+91 77020 27178</p>
                                                       <p className="text-sm text-gray-500">Mon-Fri 9AM-6PM PST</p>
                                                  </div>
                                             </div>

                                             <div className="flex items-start">
                                                  <MapPinIcon className="h-6 w-6 text-indigo-600 mr-4 mt-1" />
                                                  <div>
                                                       <h4 className="font-semibold text-gray-900">Office</h4>
                                                       <p className="text-gray-600">
                                                            Keshav Memorial Institute of Technology,
                                                            <br />
                                                            Narayanguda, Hyderabad-500029, Telanagana, India.
                                                       </p>
                                                  </div>
                                             </div>
                                        </div>
                                   </div>

                                   <div className="bg-indigo-50 rounded-xl border border-indigo-200 p-8">
                                        <h3 className="text-xl font-semibold text-indigo-900 mb-4">
                                             Enterprise Solutions
                                        </h3>
                                        <p className="text-indigo-700 mb-6">
                                             Looking for custom integrations, on-premise deployment, or dedicated support?
                                             Our enterprise team is ready to help.
                                        </p>
                                        <a
                                             href="mailto:enterprise@codenova.com"
                                             className="inline-flex items-center bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                                        >
                                             Contact Enterprise Sales
                                             <ArrowRightIcon className="ml-2 h-5 w-5" />
                                        </a>
                                   </div>
                              </div>
                         </div>
                    </div>
               </section>

               {/* Footer */}
               <footer className="bg-gray-900 text-white py-12">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                         <div className="grid md:grid-cols-4 gap-8">
                              <div>
                                   <div className="mb-4">
                                        <img
                                             src="https://codenova-uploads.blr1.cdn.digitaloceanspaces.com/icons/1759674511937.png"
                                             alt="CodeNova Logo"
                                             className="h-12 w-auto"
                                             style={{ aspectRatio: '3160/1166' }}
                                        />
                                   </div>
                                   <p className="text-gray-300 mb-4">
                                        Next-generation code review powered by AI. Transform your development workflow
                                        with intelligent analysis and continuous learning.
                                   </p>
                                   <div className="flex space-x-4">
                                        <a href="#" className="text-gray-400 hover:text-white transition-colors">
                                             <span className="sr-only">Twitter</span>
                                             <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                                                  <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                                             </svg>
                                        </a>
                                        <a href="#" className="text-gray-400 hover:text-white transition-colors">
                                             <span className="sr-only">GitHub</span>
                                             <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                                                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                                             </svg>
                                        </a>
                                        <a href="#" className="text-gray-400 hover:text-white transition-colors">
                                             <span className="sr-only">LinkedIn</span>
                                             <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                                                  <path fillRule="evenodd" d="M19 0H5a5 5 0 00-5 5v14a5 5 0 005 5h14a5 5 0 005-5V5a5 5 0 00-5-5zM8 19H5V8h3v11zM6.5 6.732c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zM20 19h-3v-5.604c0-3.368-4-3.113-4 0V19h-3V8h3v1.765c1.396-2.586 7-2.777 7 2.476V19z" clipRule="evenodd" />
                                             </svg>
                                        </a>
                                   </div>
                              </div>

                              <div>
                                   <h4 className="text-lg font-semibold mb-4">Product</h4>
                                   <ul className="space-y-2">
                                        <li><a href="#features" className="text-gray-300 hover:text-white transition-colors">Features</a></li>
                                        <li><a href="#pricing" className="text-gray-300 hover:text-white transition-colors">Pricing</a></li>
                                        <li><Link to="/signup" className="text-gray-300 hover:text-white transition-colors">Sign Up</Link></li>
                                        <li><Link to="/login" className="text-gray-300 hover:text-white transition-colors">Sign In</Link></li>
                                   </ul>
                              </div>

                              <div>
                                   <h4 className="text-lg font-semibold mb-4">Support</h4>
                                   <ul className="space-y-2">
                                        <li><a href="#contact" className="text-gray-300 hover:text-white transition-colors">Contact Us</a></li>
                                        <li><a href="#" className="text-gray-300 hover:text-white transition-colors">Documentation</a></li>
                                        <li><a href="#" className="text-gray-300 hover:text-white transition-colors">API Reference</a></li>
                                        <li><a href="#" className="text-gray-300 hover:text-white transition-colors">Status Page</a></li>
                                   </ul>
                              </div>

                              <div>
                                   <h4 className="text-lg font-semibold mb-4">Company</h4>
                                   <ul className="space-y-2">
                                        <li><a href="#" className="text-gray-300 hover:text-white transition-colors">About Us</a></li>
                                        <li><a href="#" className="text-gray-300 hover:text-white transition-colors">Blog</a></li>
                                        <li><a href="#" className="text-gray-300 hover:text-white transition-colors">Careers</a></li>
                                        <li><a href="#" className="text-gray-300 hover:text-white transition-colors">Privacy Policy</a></li>
                                        <li><a href="#" className="text-gray-300 hover:text-white transition-colors">Terms of Service</a></li>
                                   </ul>
                              </div>
                         </div>
                    </div>
               </footer>
          </div>
     );
}
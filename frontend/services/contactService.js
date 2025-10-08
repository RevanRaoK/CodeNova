import httpClient from './httpClient.js';

/**
 * Contact service for handling contact form submissions and visitor tracking
 */
class ContactService {
     /**
      * Submit contact form
      * @param {Object} contactData - Contact form data
      * @param {string} contactData.name - Contact name
      * @param {string} contactData.email - Contact email
      * @param {string} contactData.company - Company name (optional)
      * @param {string} contactData.subject - Subject category
      * @param {string} contactData.message - Message content
      * @param {string} contactData.timestamp - Submission timestamp
      * @returns {Promise<Object>} Submission response
      */
     async submitContactForm(contactData) {
          try {
               const response = await httpClient.post('/contact', contactData);
               return {
                    success: true,
                    data: response.data,
                    message: 'Contact form submitted successfully'
               };
          } catch (error) {
               console.error('Failed to submit contact form:', error);
               throw this.handleContactError(error);
          }
     }

     /**
      * Track visitor analytics for homepage
      * @param {Object} visitData - Visit tracking data
      * @param {string} visitData.page - Page identifier
      * @param {string} visitData.timestamp - Visit timestamp
      * @param {string} visitData.userAgent - Browser user agent
      * @param {string} visitData.referrer - Referrer URL
      * @param {Object} [visitData.metadata] - Additional metadata
      * @returns {Promise<Object>} Tracking response
      */
     async trackVisit(visitData) {
          try {
               const response = await httpClient.post('/analytics/track-visit', visitData);
               return {
                    success: true,
                    data: response.data
               };
          } catch (error) {
               // Don't throw errors for analytics tracking - fail silently
               console.log('Analytics tracking failed:', error);
               return {
                    success: false,
                    error: error.message
               };
          }
     }

     /**
      * Track user interactions on homepage
      * @param {Object} interactionData - Interaction data
      * @param {string} interactionData.action - Action type (click, scroll, form_view, etc.)
      * @param {string} interactionData.element - Element identifier
      * @param {string} interactionData.timestamp - Interaction timestamp
      * @param {Object} [interactionData.metadata] - Additional metadata
      * @returns {Promise<Object>} Tracking response
      */
     async trackInteraction(interactionData) {
          try {
               const response = await httpClient.post('/analytics/track-interaction', interactionData);
               return {
                    success: true,
                    data: response.data
               };
          } catch (error) {
               // Don't throw errors for analytics tracking - fail silently
               console.log('Interaction tracking failed:', error);
               return {
                    success: false,
                    error: error.message
               };
          }
     }

     /**
      * Get contact form submission statistics (for admin use)
      * @param {Object} [options] - Query options
      * @param {string} [options.timeframe] - Time frame for data
      * @param {string} [options.subject] - Filter by subject
      * @returns {Promise<Object>} Contact statistics
      */
     async getContactStatistics(options = {}) {
          try {
               const params = new URLSearchParams();
               if (options.timeframe) params.append('timeframe', options.timeframe);
               if (options.subject) params.append('subject', options.subject);

               const response = await httpClient.get(`/admin/contact-statistics?${params}`);
               return this.processContactStatistics(response.data);
          } catch (error) {
               console.error('Failed to fetch contact statistics:', error);
               throw this.handleContactError(error);
          }
     }

     /**
      * Get visitor analytics data (for admin use)
      * @param {Object} [options] - Query options
      * @param {string} [options.timeframe] - Time frame for data
      * @param {string} [options.page] - Filter by page
      * @returns {Promise<Object>} Visitor analytics
      */
     async getVisitorAnalytics(options = {}) {
          try {
               const params = new URLSearchParams();
               if (options.timeframe) params.append('timeframe', options.timeframe);
               if (options.page) params.append('page', options.page);

               const response = await httpClient.get(`/admin/visitor-analytics?${params}`);
               return this.processVisitorAnalytics(response.data);
          } catch (error) {
               console.error('Failed to fetch visitor analytics:', error);
               throw this.handleContactError(error);
          }
     }

     /**
      * Process contact statistics response
      * @param {Object} data - Raw API response
      * @returns {Object} Processed contact statistics
      */
     processContactStatistics(data) {
          return {
               overview: {
                    totalSubmissions: data.total_submissions || 0,
                    responseRate: data.response_rate || 0,
                    averageResponseTime: data.average_response_time || 0,
                    conversionRate: data.conversion_rate || 0
               },
               bySubject: (data.by_subject || []).map(item => ({
                    subject: item.subject,
                    count: item.count || 0,
                    percentage: item.percentage || 0
               })),
               byTimeframe: (data.by_timeframe || []).map(item => ({
                    date: item.date,
                    submissions: item.submissions || 0,
                    responses: item.responses || 0
               })),
               trends: data.trends || [],
               topCompanies: (data.top_companies || []).map(item => ({
                    company: item.company,
                    submissions: item.submissions || 0
               }))
          };
     }

     /**
      * Process visitor analytics response
      * @param {Object} data - Raw API response
      * @returns {Object} Processed visitor analytics
      */
     processVisitorAnalytics(data) {
          return {
               overview: {
                    totalVisitors: data.total_visitors || 0,
                    uniqueVisitors: data.unique_visitors || 0,
                    pageViews: data.page_views || 0,
                    averageSessionDuration: data.average_session_duration || 0,
                    bounceRate: data.bounce_rate || 0
               },
               byPage: (data.by_page || []).map(item => ({
                    page: item.page,
                    visitors: item.visitors || 0,
                    pageViews: item.page_views || 0,
                    averageDuration: item.average_duration || 0
               })),
               byTimeframe: (data.by_timeframe || []).map(item => ({
                    date: item.date,
                    visitors: item.visitors || 0,
                    pageViews: item.page_views || 0
               })),
               referrers: (data.referrers || []).map(item => ({
                    source: item.source,
                    visitors: item.visitors || 0,
                    percentage: item.percentage || 0
               })),
               interactions: (data.interactions || []).map(item => ({
                    action: item.action,
                    element: item.element,
                    count: item.count || 0
               }))
          };
     }

     /**
      * Handle contact service errors
      * @param {Error} error - The error to handle
      * @returns {Error} Processed error with user-friendly message
      */
     handleContactError(error) {
          if (error.response) {
               const { status, data } = error.response;

               switch (status) {
                    case 400:
                         return new Error(data.detail || 'Invalid contact form data. Please check your input.');
                    case 401:
                         return new Error('Authentication required.');
                    case 403:
                         return new Error('Access forbidden.');
                    case 429:
                         return new Error('Too many requests. Please try again later.');
                    case 500:
                         return new Error('Server error. Please try again later.');
                    default:
                         return new Error(data.detail || 'Contact form submission failed. Please try again.');
               }
          } else if (error.request) {
               return new Error('Network error. Please check your connection and try again.');
          } else {
               return new Error(error.message || 'An unexpected error occurred.');
          }
     }

     /**
      * Validate contact form data
      * @param {Object} contactData - Contact form data to validate
      * @returns {Object} Validation result with errors
      */
     validateContactForm(contactData) {
          const errors = {};

          if (!contactData.name || !contactData.name.trim()) {
               errors.name = 'Name is required';
          } else if (contactData.name.trim().length < 2) {
               errors.name = 'Name must be at least 2 characters long';
          }

          if (!contactData.email || !contactData.email.trim()) {
               errors.email = 'Email is required';
          } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactData.email)) {
               errors.email = 'Please enter a valid email address';
          }

          if (!contactData.message || !contactData.message.trim()) {
               errors.message = 'Message is required';
          } else if (contactData.message.trim().length < 10) {
               errors.message = 'Message must be at least 10 characters long';
          } else if (contactData.message.trim().length > 2000) {
               errors.message = 'Message must be less than 2000 characters';
          }

          if (contactData.company && contactData.company.length > 100) {
               errors.company = 'Company name must be less than 100 characters';
          }

          return {
               isValid: Object.keys(errors).length === 0,
               errors
          };
     }

     /**
      * Get available subject options for contact form
      * @returns {Array} List of subject options
      */
     getSubjectOptions() {
          return [
               { value: 'general', label: 'General Inquiry', description: 'General questions about our platform' },
               { value: 'sales', label: 'Sales', description: 'Pricing and sales inquiries' },
               { value: 'support', label: 'Technical Support', description: 'Technical help and support' },
               { value: 'partnership', label: 'Partnership', description: 'Partnership opportunities' },
               { value: 'enterprise', label: 'Enterprise Solutions', description: 'Enterprise and custom solutions' }
          ];
     }
}

// Export singleton instance
const contactService = new ContactService();
export default contactService;
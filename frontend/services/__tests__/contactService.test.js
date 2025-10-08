import { vi } from 'vitest';
import contactService from '../contactService';
import httpClient from '../httpClient';

// Mock the httpClient
vi.mock('../httpClient', () => ({
     default: {
          post: vi.fn(),
          get: vi.fn(),
     }
}));

describe('ContactService', () => {
     beforeEach(() => {
          vi.clearAllMocks();
     });

     describe('submitContactForm', () => {
          const mockContactData = {
               name: 'John Doe',
               email: 'john@example.com',
               company: 'Test Company',
               subject: 'general',
               message: 'This is a test message',
               timestamp: '2024-01-01T00:00:00.000Z'
          };

          test('submits contact form successfully', async () => {
               const mockResponse = {
                    data: {
                         id: '123',
                         status: 'submitted',
                         message: 'Contact form submitted successfully'
                    }
               };
               httpClient.post.mockResolvedValue(mockResponse);

               const result = await contactService.submitContactForm(mockContactData);

               expect(httpClient.post).toHaveBeenCalledWith('/contact', mockContactData);
               expect(result).toEqual({
                    success: true,
                    data: mockResponse.data,
                    message: 'Contact form submitted successfully'
               });
          });

          test('handles submission error with specific status codes', async () => {
               const mockError = {
                    response: {
                         status: 400,
                         data: {
                              detail: 'Invalid email format'
                         }
                    }
               };
               httpClient.post.mockRejectedValue(mockError);

               await expect(contactService.submitContactForm(mockContactData))
                    .rejects.toThrow('Invalid email format');
          });

          test('handles network error', async () => {
               const mockError = {
                    request: {}
               };
               httpClient.post.mockRejectedValue(mockError);

               await expect(contactService.submitContactForm(mockContactData))
                    .rejects.toThrow('Network error. Please check your connection and try again.');
          });

          test('handles generic error', async () => {
               const mockError = new Error('Something went wrong');
               httpClient.post.mockRejectedValue(mockError);

               await expect(contactService.submitContactForm(mockContactData))
                    .rejects.toThrow('Something went wrong');
          });
     });

     describe('trackVisit', () => {
          const mockVisitData = {
               page: 'homepage',
               timestamp: '2024-01-01T00:00:00.000Z',
               userAgent: 'Mozilla/5.0...',
               referrer: 'https://google.com'
          };

          test('tracks visit successfully', async () => {
               const mockResponse = {
                    data: {
                         id: '456',
                         tracked: true
                    }
               };
               httpClient.post.mockResolvedValue(mockResponse);

               const result = await contactService.trackVisit(mockVisitData);

               expect(httpClient.post).toHaveBeenCalledWith('/analytics/track-visit', mockVisitData);
               expect(result).toEqual({
                    success: true,
                    data: mockResponse.data
               });
          });

          test('handles tracking error gracefully', async () => {
               const mockError = new Error('Tracking failed');
               httpClient.post.mockRejectedValue(mockError);

               const result = await contactService.trackVisit(mockVisitData);

               expect(result).toEqual({
                    success: false,
                    error: 'Tracking failed'
               });
          });
     });

     describe('trackInteraction', () => {
          const mockInteractionData = {
               action: 'click',
               element: 'pricing-button',
               timestamp: '2024-01-01T00:00:00.000Z',
               metadata: { section: 'pricing' }
          };

          test('tracks interaction successfully', async () => {
               const mockResponse = {
                    data: {
                         id: '789',
                         tracked: true
                    }
               };
               httpClient.post.mockResolvedValue(mockResponse);

               const result = await contactService.trackInteraction(mockInteractionData);

               expect(httpClient.post).toHaveBeenCalledWith('/analytics/track-interaction', mockInteractionData);
               expect(result).toEqual({
                    success: true,
                    data: mockResponse.data
               });
          });

          test('handles interaction tracking error gracefully', async () => {
               const mockError = new Error('Interaction tracking failed');
               httpClient.post.mockRejectedValue(mockError);

               const result = await contactService.trackInteraction(mockInteractionData);

               expect(result).toEqual({
                    success: false,
                    error: 'Interaction tracking failed'
               });
          });
     });

     describe('getContactStatistics', () => {
          test('fetches contact statistics successfully', async () => {
               const mockResponse = {
                    data: {
                         total_submissions: 100,
                         response_rate: 0.85,
                         average_response_time: 24,
                         conversion_rate: 0.15,
                         by_subject: [
                              { subject: 'general', count: 50, percentage: 50 },
                              { subject: 'sales', count: 30, percentage: 30 }
                         ],
                         by_timeframe: [
                              { date: '2024-01-01', submissions: 10, responses: 8 }
                         ],
                         trends: [],
                         top_companies: [
                              { company: 'Test Corp', submissions: 5 }
                         ]
                    }
               };
               httpClient.get.mockResolvedValue(mockResponse);

               const result = await contactService.getContactStatistics({ timeframe: '30d' });

               expect(httpClient.get).toHaveBeenCalledWith('/admin/contact-statistics?timeframe=30d');
               expect(result.overview.totalSubmissions).toBe(100);
               expect(result.overview.responseRate).toBe(0.85);
               expect(result.bySubject).toHaveLength(2);
               expect(result.byTimeframe).toHaveLength(1);
          });

          test('handles statistics fetch error', async () => {
               const mockError = {
                    response: {
                         status: 403,
                         data: {
                              detail: 'Access forbidden'
                         }
                    }
               };
               httpClient.get.mockRejectedValue(mockError);

               await expect(contactService.getContactStatistics())
                    .rejects.toThrow('Access forbidden');
          });
     });

     describe('getVisitorAnalytics', () => {
          test('fetches visitor analytics successfully', async () => {
               const mockResponse = {
                    data: {
                         total_visitors: 1000,
                         unique_visitors: 800,
                         page_views: 1500,
                         average_session_duration: 180,
                         bounce_rate: 0.3,
                         by_page: [
                              { page: 'homepage', visitors: 500, page_views: 600, average_duration: 200 }
                         ],
                         by_timeframe: [
                              { date: '2024-01-01', visitors: 100, page_views: 150 }
                         ],
                         referrers: [
                              { source: 'google.com', visitors: 300, percentage: 30 }
                         ],
                         interactions: [
                              { action: 'click', element: 'signup-button', count: 50 }
                         ]
                    }
               };
               httpClient.get.mockResolvedValue(mockResponse);

               const result = await contactService.getVisitorAnalytics({ timeframe: '7d', page: 'homepage' });

               expect(httpClient.get).toHaveBeenCalledWith('/admin/visitor-analytics?timeframe=7d&page=homepage');
               expect(result.overview.totalVisitors).toBe(1000);
               expect(result.overview.uniqueVisitors).toBe(800);
               expect(result.byPage).toHaveLength(1);
               expect(result.referrers).toHaveLength(1);
               expect(result.interactions).toHaveLength(1);
          });
     });

     describe('validateContactForm', () => {
          test('validates valid form data', () => {
               const validData = {
                    name: 'John Doe',
                    email: 'john@example.com',
                    message: 'This is a valid message with enough characters',
                    company: 'Test Company'
               };

               const result = contactService.validateContactForm(validData);

               expect(result.isValid).toBe(true);
               expect(result.errors).toEqual({});
          });

          test('validates required fields', () => {
               const invalidData = {
                    name: '',
                    email: '',
                    message: '',
                    company: 'Test Company'
               };

               const result = contactService.validateContactForm(invalidData);

               expect(result.isValid).toBe(false);
               expect(result.errors.name).toBe('Name is required');
               expect(result.errors.email).toBe('Email is required');
               expect(result.errors.message).toBe('Message is required');
          });

          test('validates email format', () => {
               const invalidData = {
                    name: 'John Doe',
                    email: 'invalid-email',
                    message: 'This is a valid message with enough characters'
               };

               const result = contactService.validateContactForm(invalidData);

               expect(result.isValid).toBe(false);
               expect(result.errors.email).toBe('Please enter a valid email address');
          });

          test('validates message length', () => {
               const shortMessageData = {
                    name: 'John Doe',
                    email: 'john@example.com',
                    message: 'Short'
               };

               const longMessageData = {
                    name: 'John Doe',
                    email: 'john@example.com',
                    message: 'a'.repeat(2001)
               };

               const shortResult = contactService.validateContactForm(shortMessageData);
               const longResult = contactService.validateContactForm(longMessageData);

               expect(shortResult.isValid).toBe(false);
               expect(shortResult.errors.message).toBe('Message must be at least 10 characters long');

               expect(longResult.isValid).toBe(false);
               expect(longResult.errors.message).toBe('Message must be less than 2000 characters');
          });

          test('validates name length', () => {
               const invalidData = {
                    name: 'J',
                    email: 'john@example.com',
                    message: 'This is a valid message with enough characters'
               };

               const result = contactService.validateContactForm(invalidData);

               expect(result.isValid).toBe(false);
               expect(result.errors.name).toBe('Name must be at least 2 characters long');
          });

          test('validates company length', () => {
               const invalidData = {
                    name: 'John Doe',
                    email: 'john@example.com',
                    message: 'This is a valid message with enough characters',
                    company: 'a'.repeat(101)
               };

               const result = contactService.validateContactForm(invalidData);

               expect(result.isValid).toBe(false);
               expect(result.errors.company).toBe('Company name must be less than 100 characters');
          });
     });

     describe('getSubjectOptions', () => {
          test('returns correct subject options', () => {
               const options = contactService.getSubjectOptions();

               expect(options).toHaveLength(5);
               expect(options[0]).toEqual({
                    value: 'general',
                    label: 'General Inquiry',
                    description: 'General questions about our platform'
               });
               expect(options[1]).toEqual({
                    value: 'sales',
                    label: 'Sales',
                    description: 'Pricing and sales inquiries'
               });
          });
     });

     describe('error handling', () => {
          test('handles 400 error', async () => {
               const mockError = {
                    response: {
                         status: 400,
                         data: { detail: 'Bad request' }
                    }
               };
               httpClient.post.mockRejectedValue(mockError);

               await expect(contactService.submitContactForm({}))
                    .rejects.toThrow('Bad request');
          });

          test('handles 401 error', async () => {
               const mockError = {
                    response: {
                         status: 401,
                         data: {}
                    }
               };
               httpClient.post.mockRejectedValue(mockError);

               await expect(contactService.submitContactForm({}))
                    .rejects.toThrow('Authentication required.');
          });

          test('handles 403 error', async () => {
               const mockError = {
                    response: {
                         status: 403,
                         data: {}
                    }
               };
               httpClient.post.mockRejectedValue(mockError);

               await expect(contactService.submitContactForm({}))
                    .rejects.toThrow('Access forbidden.');
          });

          test('handles 429 error', async () => {
               const mockError = {
                    response: {
                         status: 429,
                         data: {}
                    }
               };
               httpClient.post.mockRejectedValue(mockError);

               await expect(contactService.submitContactForm({}))
                    .rejects.toThrow('Too many requests. Please try again later.');
          });

          test('handles 500 error', async () => {
               const mockError = {
                    response: {
                         status: 500,
                         data: {}
                    }
               };
               httpClient.post.mockRejectedValue(mockError);

               await expect(contactService.submitContactForm({}))
                    .rejects.toThrow('Server error. Please try again later.');
          });

          test('handles unknown status code', async () => {
               const mockError = {
                    response: {
                         status: 418,
                         data: { detail: 'I am a teapot' }
                    }
               };
               httpClient.post.mockRejectedValue(mockError);

               await expect(contactService.submitContactForm({}))
                    .rejects.toThrow('I am a teapot');
          });
     });
});
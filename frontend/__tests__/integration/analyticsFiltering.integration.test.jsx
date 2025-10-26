import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdminAnalyticsDashboard from '../../components/admin/AdminAnalyticsDashboard';
import adminService from '../../services/adminService';
import { toast } from '../../utils/toastNotifications';

// Mock the services and utilities
vi.mock('../../services/adminService', () => ({
    default: {
        getAllTeams: vi.fn(),
        getDashboardMetrics: vi.fn(),
        getPlatformStats: vi.fn(),
        getGlobalTrends: vi.fn(),
        getFeedbackStatistics: vi.fn(),
        getAllReviews: vi.fn()
    }
}));

vi.mock('../../utils/toastNotifications', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
        warning: vi.fn(),
        loading: vi.fn(() => 'loading-toast-id'),
        remove: vi.fn()
    }
}));

// Mock recharts components to avoid rendering issues in tests
vi.mock('recharts', () => ({
    BarChart: ({ children }) => <div data-testid="bar-chart">{children}</div>,
    Bar: () => <div data-testid="bar" />,
    XAxis: () => <div data-testid="x-axis" />,
    YAxis: () => <div data-testid="y-axis" />,
    CartesianGrid: () => <div data-testid="cartesian-grid" />,
    Tooltip: () => <div data-testid="tooltip" />,
    ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>,
    LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
    Line: () => <div data-testid="line" />,
    PieChart: ({ children }) => <div data-testid="pie-chart">{children}</div>,
    Pie: () => <div data-testid="pie" />,
    Cell: () => <div data-testid="cell" />,
    Legend: () => <div data-testid="legend" />
}));

describe('Analytics Filtering Integration Tests', () => {
    const mockTeams = [
        { id: 'team-1', name: 'Backend Team' },
        { id: 'team-2', name: 'Frontend Team' },
        { id: 'team-3', name: 'DevOps Team' }
    ];

    const mockCurrentUser = {
        id: 1,
        role: 'admin',
        full_name: 'Admin User',
        email: 'admin@example.com'
    };

    // Mock data for "All Users" (no team filter)
    const mockAllUsersPlatformStats = {
        total_users: 25,
        active_users: 20,
        total_teams: 3,
        total_reviews: 150,
        total_analyses: 150,
        reviews_today: 8,
        avg_issues_per_review: 3.2,
        total_issues_found: 480,
        recent_activities: [
            { id: 1, type: 'review_completed', user_name: 'John Doe', description: 'Completed code review', timestamp: '2025-01-04T10:00:00Z' },
            { id: 2, type: 'user_created', user_name: 'Jane Smith', description: 'New user registered', timestamp: '2025-01-04T09:30:00Z' }
        ]
    };

    const mockAllUsersGlobalTrends = {
        data_points: [
            { date: '2025-01-01', errors: 45, warnings: 32, security_issues: 8, reviews: 12 },
            { date: '2025-01-02', errors: 38, warnings: 28, security_issues: 6, reviews: 15 },
            { date: '2025-01-03', errors: 42, warnings: 35, security_issues: 9, reviews: 18 },
            { date: '2025-01-04', errors: 35, warnings: 25, security_issues: 5, reviews: 20 }
        ]
    };

    const mockAllUsersFeedbackStats = {
        total_feedback: 120,
        acceptance_rate: 0.75,
        rejection_rate: 0.15,
        modification_rate: 0.10,
        total_accepted: 90,
        total_rejected: 18,
        total_modified: 12
    };

    // Mock data for specific team filter (Backend Team)
    const mockTeamPlatformStats = {
        total_users: 8,
        active_users: 7,
        total_teams: 1,
        total_reviews: 45,
        total_analyses: 45,
        reviews_today: 3,
        avg_issues_per_review: 2.8,
        total_issues_found: 126,
        recent_activities: [
            { id: 1, type: 'review_completed', user_name: 'Backend Dev 1', description: 'Completed API review', timestamp: '2025-01-04T10:00:00Z' }
        ]
    };

    const mockTeamGlobalTrends = {
        data_points: [
            { date: '2025-01-01', errors: 15, warnings: 12, security_issues: 3, reviews: 4 },
            { date: '2025-01-02', errors: 12, warnings: 10, security_issues: 2, reviews: 5 },
            { date: '2025-01-03', errors: 14, warnings: 13, security_issues: 4, reviews: 6 },
            { date: '2025-01-04', errors: 11, warnings: 8, security_issues: 2, reviews: 7 }
        ]
    };

    const mockTeamFeedbackStats = {
        total_feedback: 35,
        acceptance_rate: 0.80,
        rejection_rate: 0.12,
        modification_rate: 0.08,
        total_accepted: 28,
        total_rejected: 4,
        total_modified: 3
    };

    const mockDashboardMetrics = {
        reviews_today: 8
    };

    beforeEach(() => {
        vi.clearAllMocks();

        // Setup default mock responses for "All Users" view
        adminService.getAllTeams.mockResolvedValue({ teams: mockTeams });
        adminService.getDashboardMetrics.mockResolvedValue(mockDashboardMetrics);
        adminService.getPlatformStats.mockResolvedValue(mockAllUsersPlatformStats);
        adminService.getGlobalTrends.mockResolvedValue(mockAllUsersGlobalTrends);
        adminService.getFeedbackStatistics.mockResolvedValue(mockAllUsersFeedbackStats);
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    describe('"All Users" Filter Shows Aggregated Data', () => {
        it('should display aggregated data across all users when "All Users" is selected', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load with "All Users" selected by default
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Wait for overview data to load (component defaults to overview)
            await waitFor(() => {
                expect(screen.getByText('Total Users')).toBeInTheDocument(); // Wait for the metrics section to appear
            }, { timeout: 5000 });

            // Debug: Check if the component is in loading state
            expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument();

            // Verify team filter shows "All Users" as default
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            expect(teamFilter.value).toBe('');
            expect(within(teamFilter).getByText('All Users')).toBeInTheDocument();

            // Verify API calls were made without team_id parameter
            await waitFor(() => {
                expect(adminService.getPlatformStats).toHaveBeenCalledWith({
                    dateRange: '30d',
                    teamId: null
                });
                expect(adminService.getGlobalTrends).toHaveBeenCalledWith({
                    dateRange: '30d',
                    teamId: null
                });
                expect(adminService.getFeedbackStatistics).toHaveBeenCalledWith({
                    teamId: null
                });
            });

            // Verify aggregated metrics are displayed - wait for each one individually
            await waitFor(() => {
                expect(screen.getByText('25')).toBeInTheDocument(); // Total users
            }, { timeout: 3000 });

            await waitFor(() => {
                expect(screen.getByText('150')).toBeInTheDocument(); // Total reviews
            }, { timeout: 3000 });

            await waitFor(() => {
                expect(screen.getByText('8')).toBeInTheDocument(); // Reviews today
            }, { timeout: 3000 });

            await waitFor(() => {
                expect(screen.getByText('3')).toBeInTheDocument(); // Active teams
            }, { timeout: 3000 });

            // Verify feedback statistics
            await waitFor(() => {
                expect(screen.getByText('120')).toBeInTheDocument(); // Total feedback
            }, { timeout: 3000 });

            await waitFor(() => {
                expect(screen.getByText('75.0%')).toBeInTheDocument(); // Acceptance rate
            }, { timeout: 3000 });

            await waitFor(() => {
                expect(screen.getByText('15.0%')).toBeInTheDocument(); // Rejection rate
            }, { timeout: 3000 });

            await waitFor(() => {
                expect(screen.getByText('10.0%')).toBeInTheDocument(); // Modification rate
            }, { timeout: 3000 });
        });

        it('should show "All Users" as the first option in team filter dropdown', async () => {
            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            const options = within(teamFilter).getAllByRole('option');

            // First option should be "All Users"
            expect(options[0]).toHaveTextContent('All Users');
            expect(options[0].value).toBe('');

            // Followed by actual teams
            expect(options[1]).toHaveTextContent('Backend Team');
            expect(options[2]).toHaveTextContent('Frontend Team');
            expect(options[3]).toHaveTextContent('DevOps Team');
        });

        it('should default to "All Users" selection on initial load', async () => {
            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            expect(teamFilter.value).toBe(''); // Empty value represents "All Users"

            // Verify the displayed text shows "All Users"
            expect(screen.getByDisplayValue('')).toBeInTheDocument();
        });
    });

    describe('Specific Team Filter Shows Only Team Data', () => {
        it('should display only team-specific data when a specific team is selected', async () => {
            const user = userEvent.setup();

            // Setup mock responses for team-specific data
            adminService.getPlatformStats.mockImplementation((options) => {
                if (options.teamId === 'team-1') {
                    return Promise.resolve(mockTeamPlatformStats);
                }
                return Promise.resolve(mockAllUsersPlatformStats);
            });

            adminService.getGlobalTrends.mockImplementation((options) => {
                if (options.teamId === 'team-1') {
                    return Promise.resolve(mockTeamGlobalTrends);
                }
                return Promise.resolve(mockAllUsersGlobalTrends);
            });

            adminService.getFeedbackStatistics.mockImplementation((options) => {
                if (options.teamId === 'team-1') {
                    return Promise.resolve(mockTeamFeedbackStats);
                }
                return Promise.resolve(mockAllUsersFeedbackStats);
            });

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab
            // Select Backend Team from dropdown
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            // Verify API calls were made with team_id parameter
            await waitFor(() => {
                expect(adminService.getPlatformStats).toHaveBeenCalledWith({
                    dateRange: '30d',
                    teamId: 'team-1'
                });
                expect(adminService.getGlobalTrends).toHaveBeenCalledWith({
                    dateRange: '30d',
                    teamId: 'team-1'
                });
                expect(adminService.getFeedbackStatistics).toHaveBeenCalledWith({
                    teamId: 'team-1'
                });
            });

            // Wait for overview data to load first
            await waitFor(() => {
                expect(screen.getByText('Total Users')).toBeInTheDocument();
            });

            // Verify team-specific metrics are displayed (different from "All Users")
            await waitFor(() => {
                // Find the Total Users metric specifically
                const totalUsersSection = screen.getByText('Total Users').parentElement;
                expect(totalUsersSection).toHaveTextContent('8');
                
                // Find the Total Reviews metric specifically  
                const totalReviewsSection = screen.getByText('Total Reviews').parentElement;
                expect(totalReviewsSection).toHaveTextContent('45');
                
                // Find the Reviews Today metric specifically
                const reviewsTodaySection = screen.getByText('Reviews Today').parentElement;
                expect(reviewsTodaySection).toHaveTextContent('3');
                
                // Find the Active Teams metric specifically
                const activeTeamsSection = screen.getByText('Active Teams').parentElement;
                expect(activeTeamsSection).toHaveTextContent('1');
            }, { timeout: 3000 });

            // Verify team-specific feedback statistics
            await waitFor(() => {
                expect(screen.getByText('35')).toBeInTheDocument(); // Team feedback (not 120)
                expect(screen.getByText('80.0%')).toBeInTheDocument(); // Team acceptance rate (not 75%)
                expect(screen.getByText('12.0%')).toBeInTheDocument(); // Team rejection rate (not 15%)
                expect(screen.getByText('8.0%')).toBeInTheDocument(); // Team modification rate (not 10%)
            });
        });

        it('should update chart data when team filter changes', async () => {
            const user = userEvent.setup();

            // Setup mock responses for different teams
            adminService.getGlobalTrends.mockImplementation((options) => {
                if (options.teamId === 'team-2') {
                    return Promise.resolve({
                        data_points: [
                            { date: '2025-01-01', errors: 20, warnings: 15, security_issues: 4, reviews: 6 },
                            { date: '2025-01-02', errors: 18, warnings: 12, security_issues: 3, reviews: 8 }
                        ]
                    });
                }
                return Promise.resolve(mockAllUsersGlobalTrends);
            });

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Verify initial chart is rendered (wait for it to load)
            await waitFor(() => {
                expect(screen.getByTestId('line-chart')).toBeInTheDocument();
            }, { timeout: 3000 });

            // Change to Frontend Team
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-2');

            // Verify API was called with new team ID
            await waitFor(() => {
                expect(adminService.getGlobalTrends).toHaveBeenCalledWith({
                    dateRange: '30d',
                    teamId: 'team-2'
                });
            });

            // Chart should still be rendered (with new data)
            expect(screen.getByTestId('line-chart')).toBeInTheDocument();
        });

        it('should maintain team selection when switching between views', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Select a specific team
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            // Switch to feedback view
            const feedbackTab = screen.getByRole('button', { name: /all feedback/i });
            await user.click(feedbackTab);

            // Team filter should maintain selection
            expect(teamFilter.value).toBe('team-1');

            // Switch back to overview
            const overviewTab = screen.getByRole('button', { name: /overview/i });
            await user.click(overviewTab);

            // Team filter should still be maintained
            expect(teamFilter.value).toBe('team-1');
        });
    });

    describe('Date Range Filter Affects Data Correctly', () => {
        it('should update data when date range filter changes', async () => {
            const user = userEvent.setup();

            // Setup mock responses for different date ranges
            adminService.getPlatformStats.mockImplementation((options) => {
                if (options.dateRange === '7d') {
                    return Promise.resolve({
                        ...mockAllUsersPlatformStats,
                        total_reviews: 35, // Less reviews for shorter period
                        total_analyses: 35, // Match total_reviews
                        reviews_today: 5
                    });
                }
                return Promise.resolve(mockAllUsersPlatformStats);
            });

            adminService.getGlobalTrends.mockImplementation((options) => {
                if (options.dateRange === '7d') {
                    return Promise.resolve({
                        data_points: [
                            { date: '2025-01-03', errors: 42, warnings: 35, security_issues: 9, reviews: 18 },
                            { date: '2025-01-04', errors: 35, warnings: 25, security_issues: 5, reviews: 20 }
                        ]
                    });
                }
                return Promise.resolve(mockAllUsersGlobalTrends);
            });

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load (30d default)
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab
            await waitFor(() => {
                expect(screen.getByText('Total Reviews')).toBeInTheDocument(); // Wait for metrics section
            }, { timeout: 3000 });

            // Verify initial 30d data is displayed
            await waitFor(() => {
                expect(screen.getByText('150')).toBeInTheDocument(); // 30d reviews
            }, { timeout: 3000 });

            // Change date range to 7 days
            const dateRangeLabel = screen.getByText('Date Range');
            const dateRangeFilter = dateRangeLabel.parentElement.querySelector('select');
            await user.selectOptions(dateRangeFilter, '7d');

            // Verify API calls were made with new date range
            await waitFor(() => {
                expect(adminService.getPlatformStats).toHaveBeenCalledWith({
                    dateRange: '7d',
                    teamId: null
                });
                expect(adminService.getGlobalTrends).toHaveBeenCalledWith({
                    dateRange: '7d',
                    teamId: null
                });
            });

            // Verify updated metrics are displayed
            await waitFor(() => {
                expect(screen.getByText('35')).toBeInTheDocument(); // 7d reviews (not 150)
                expect(screen.getByText('5')).toBeInTheDocument(); // Updated reviews today
            }, { timeout: 3000 });
        });

        it('should support all date range options (7d, 30d, 90d)', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab
            const dateRangeLabel = screen.getByText('Date Range');
            const dateRangeFilter = dateRangeLabel.parentElement.querySelector('select');
            const options = within(dateRangeFilter).getAllByRole('option');

            // Verify all date range options are available
            expect(options).toHaveLength(3);
            expect(options[0]).toHaveTextContent('Last 7 days');
            expect(options[0].value).toBe('7d');
            expect(options[1]).toHaveTextContent('Last 30 days');
            expect(options[1].value).toBe('30d');
            expect(options[2]).toHaveTextContent('Last 90 days');
            expect(options[2].value).toBe('90d');

            // Test each option
            await user.selectOptions(dateRangeFilter, '7d');
            expect(dateRangeFilter.value).toBe('7d');

            await user.selectOptions(dateRangeFilter, '90d');
            expect(dateRangeFilter.value).toBe('90d');

            await user.selectOptions(dateRangeFilter, '30d');
            expect(dateRangeFilter.value).toBe('30d');
        });

        it('should default to 30 days date range', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab
            const dateRangeLabel = screen.getByText('Date Range');
            const dateRangeFilter = dateRangeLabel.parentElement.querySelector('select');
            expect(dateRangeFilter.value).toBe('30d');

            // Verify initial API calls use 30d
            expect(adminService.getPlatformStats).toHaveBeenCalledWith({
                dateRange: '30d',
                teamId: null
            });
        });
    });

    describe('Combining Team and Date Filters', () => {
        it('should apply both team and date filters simultaneously', async () => {
            const user = userEvent.setup();

            // Setup mock for combined filters
            adminService.getPlatformStats.mockImplementation((options) => {
                if (options.teamId === 'team-1' && options.dateRange === '7d') {
                    return Promise.resolve({
                        ...mockTeamPlatformStats,
                        total_reviews: 12, // Team + 7d specific data
                        reviews_today: 2
                    });
                }
                return Promise.resolve(mockAllUsersPlatformStats);
            });

            adminService.getGlobalTrends.mockImplementation((options) => {
                if (options.teamId === 'team-1' && options.dateRange === '7d') {
                    return Promise.resolve({
                        data_points: [
                            { date: '2025-01-03', errors: 14, warnings: 13, security_issues: 4, reviews: 6 },
                            { date: '2025-01-04', errors: 11, warnings: 8, security_issues: 2, reviews: 6 }
                        ]
                    });
                }
                return Promise.resolve(mockAllUsersGlobalTrends);
            });

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab
            // Apply team filter first
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            // Then apply date range filter
            const dateRangeLabel = screen.getByText('Date Range');
            const dateRangeFilter = dateRangeLabel.parentElement.querySelector('select');
            await user.selectOptions(dateRangeFilter, '7d');

            // Verify API calls were made with both filters
            await waitFor(() => {
                expect(adminService.getPlatformStats).toHaveBeenCalledWith({
                    dateRange: '7d',
                    teamId: 'team-1'
                });
                expect(adminService.getGlobalTrends).toHaveBeenCalledWith({
                    dateRange: '7d',
                    teamId: 'team-1'
                });
                expect(adminService.getFeedbackStatistics).toHaveBeenCalledWith({
                    teamId: 'team-1'
                });
            });

            // Verify combined filter results
            await waitFor(() => {
                expect(screen.getByText('Total Reviews')).toBeInTheDocument(); // Wait for metrics section
            }, { timeout: 3000 });

            // Check for the combined filter results
            await waitFor(() => {
                expect(screen.getByText('12')).toBeInTheDocument(); // Combined team + 7d reviews
                expect(screen.getByText('2')).toBeInTheDocument(); // Combined reviews today
            }, { timeout: 3000 });
        });

        it('should reset to "All Users" when team filter is changed back', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Select a specific team
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            // Change back to "All Users"
            await user.selectOptions(teamFilter, '');

            // Verify API calls were made without team filter
            await waitFor(() => {
                expect(adminService.getPlatformStats).toHaveBeenLastCalledWith({
                    dateRange: '30d',
                    teamId: null
                });
                expect(adminService.getGlobalTrends).toHaveBeenLastCalledWith({
                    dateRange: '30d',
                    teamId: null
                });
                expect(adminService.getFeedbackStatistics).toHaveBeenLastCalledWith({
                    teamId: null
                });
            });
        });

        it('should maintain date range when team filter changes', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab
            // Set date range to 7d
            const dateRangeLabel = screen.getByText('Date Range');
            const dateRangeFilter = dateRangeLabel.parentElement.querySelector('select');
            await user.selectOptions(dateRangeFilter, '7d');

            // Change team filter
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            // Verify both filters are applied
            await waitFor(() => {
                expect(adminService.getPlatformStats).toHaveBeenLastCalledWith({
                    dateRange: '7d',
                    teamId: 'team-1'
                });
            });

            // Date range should still be 7d
            expect(dateRangeFilter.value).toBe('7d');
        });
    });

    describe('Chart Data Updates When Filters Change', () => {
        it('should show loading state during filter changes', async () => {
            const user = userEvent.setup();

            // Mock delayed response to test loading state
            adminService.getPlatformStats.mockImplementation(() =>
                new Promise(resolve => setTimeout(() => resolve(mockAllUsersPlatformStats), 100))
            );

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab
            // Change filter to trigger loading
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            // Verify loading state is shown
            expect(screen.getByText('Loading analytics...')).toBeInTheDocument();

            // Wait for loading to complete
            await waitFor(() => {
                expect(screen.queryByText('Loading analytics...')).not.toBeInTheDocument();
            }, { timeout: 2000 });
        });

        it('should disable filters during loading', async () => {
            const user = userEvent.setup();

            // Mock delayed response
            adminService.getPlatformStats.mockImplementation(() =>
                new Promise(resolve => setTimeout(() => resolve(mockAllUsersPlatformStats), 100))
            );

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab
            // Change filter to trigger loading
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            const dateRangeLabel = screen.getByText('Date Range');
            const dateRangeFilter = dateRangeLabel.parentElement.querySelector('select');

            await user.selectOptions(teamFilter, 'team-1');

            // Verify filters are disabled during loading
            expect(teamFilter).toBeDisabled();
            expect(dateRangeFilter).toBeDisabled();

            // Wait for loading to complete
            await waitFor(() => {
                expect(teamFilter).not.toBeDisabled();
                expect(dateRangeFilter).not.toBeDisabled();
            }, { timeout: 2000 });
        });

        it('should update all chart components when filters change', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab

            // Verify charts are rendered initially
            await waitFor(() => {
                expect(screen.getByTestId('line-chart')).toBeInTheDocument();
            });

            // Change team filter
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            // Wait for update to complete
            await waitFor(() => {
                expect(adminService.getPlatformStats).toHaveBeenCalledWith({
                    dateRange: '30d',
                    teamId: 'team-1'
                });
            });

            // Charts should still be rendered (with updated data)
            expect(screen.getByTestId('line-chart')).toBeInTheDocument();
        });

        it('should handle filter changes in different view tabs', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Switch to feedback view
            const feedbackTab = screen.getByRole('button', { name: /all feedback/i });
            await user.click(feedbackTab);

            // Change team filter while in feedback view
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            // Verify feedback statistics API was called with team filter
            await waitFor(() => {
                expect(adminService.getFeedbackStatistics).toHaveBeenCalledWith({
                    teamId: 'team-1'
                });
            });

            // Switch back to overview
            const overviewTab = screen.getByRole('button', { name: /overview/i });
            await user.click(overviewTab);

            // All APIs should have been called with the team filter
            expect(adminService.getPlatformStats).toHaveBeenCalledWith({
                dateRange: '30d',
                teamId: 'team-1'
            });
        });

        it('should preserve chart data on API errors', async () => {
            const user = userEvent.setup();

            // Setup initial successful load
            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Component defaults to overview tab

            await waitFor(() => {
                expect(screen.getByText('Total Reviews')).toBeInTheDocument(); // Wait for metrics section
                expect(screen.getByText('150')).toBeInTheDocument(); // Initial data
            }, { timeout: 3000 });

            // Mock API error for filter change
            adminService.getPlatformStats.mockRejectedValueOnce(new Error('Network error'));

            // Change filter
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            // Verify error handling
            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Failed to load platform statistics');
            });

            // Previous data should be preserved
            expect(screen.getByText('150')).toBeInTheDocument(); // Original data still shown
        });
    });

    describe('Error Handling During Filter Operations', () => {
        it('should handle team loading errors gracefully', async () => {
            adminService.getAllTeams.mockRejectedValue(new Error('Failed to load teams'));

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Failed to load teams. Please try again.');
            });

            // Team filter should still be rendered with just "All Users"
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            expect(teamFilter).toBeInTheDocument();
            expect(teamFilter.value).toBe('');
        });

        it('should handle analytics API errors during filter changes', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Mock API error
            adminService.getGlobalTrends.mockRejectedValue(new Error('Trends API error'));

            // Change filter
            const dateRangeLabel = screen.getByText('Date Range');
            const dateRangeFilter = dateRangeLabel.parentElement.querySelector('select');
            await user.selectOptions(dateRangeFilter, '7d');

            // Verify error is handled
            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Failed to load trend data');
            });

            // Dashboard should still be functional
            expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
        });

        it('should recover from errors when filters are changed again', async () => {
            const user = userEvent.setup();

            render(
                <AdminAnalyticsDashboard
                    onError={vi.fn()}
                    onSuccess={vi.fn()}
                    currentUser={mockCurrentUser}
                />
            );

            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Global Analytics Dashboard')).toBeInTheDocument();
            });

            // Mock API error for first filter change
            adminService.getPlatformStats
                .mockRejectedValueOnce(new Error('Network error'))
                .mockResolvedValueOnce(mockTeamPlatformStats);

            // Change filter (should fail)
            const teamFilterLabel = screen.getByText('Team Filter');
            const teamFilter = teamFilterLabel.parentElement.querySelector('select');
            await user.selectOptions(teamFilter, 'team-1');

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith('Failed to load platform statistics');
            });

            // Change filter again (should succeed)
            await user.selectOptions(teamFilter, 'team-2');

            await waitFor(() => {
                expect(adminService.getPlatformStats).toHaveBeenCalledWith({
                    dateRange: '30d',
                    teamId: 'team-2'
                });
            });

            // Should not show error toast for successful call
            expect(toast.error).toHaveBeenCalledTimes(1);
        });
    });
});
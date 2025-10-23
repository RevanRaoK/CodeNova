import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAdminAnalytics } from '../useAdminAnalytics';
import adminService from '../../services/adminService';

// Mock dependencies
vi.mock('../../services/adminService');
vi.mock('../../contexts/NotificationContext', () => ({
  useNotification: () => ({
    showError: vi.fn()
  })
}));
vi.mock('../../utils/environment', () => ({
  logger: {
    debug: vi.fn(),
    error: vi.fn()
  }
}));

describe('useAdminAnalytics', () => {
  const mockPlatformStats = {
    total_users: 150,
    total_teams: 12,
    total_reviews: 5420
  };

  const mockGlobalTrends = {
    timeframe: '30d',
    data_points: [
      { date: '2025-10-01', reviews: 45, errors: 89 }
    ]
  };

  const mockTeamComparison = {
    teams: [
      { team_id: 'team-1', team_name: 'Backend Team', total_reviews: 450 }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    
    adminService.getPlatformStats.mockResolvedValue(mockPlatformStats);
    adminService.getGlobalTrends.mockResolvedValue(mockGlobalTrends);
    adminService.getTeamComparison.mockResolvedValue(mockTeamComparison);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('should initialize with null data', () => {
    const { result } = renderHook(() => useAdminAnalytics({ autoFetch: false }));

    expect(result.current.platformStats).toBeNull();
    expect(result.current.globalTrends).toBeNull();
    expect(result.current.teamComparison).toBeNull();
  });

  it('should auto-fetch data on mount', async () => {
    const { result } = renderHook(() => useAdminAnalytics({ autoFetch: true }));

    await waitFor(() => {
      expect(result.current.platformStats).toEqual(mockPlatformStats);
    });
  });

  it('should fetch platform stats', async () => {
    const { result } = renderHook(() => useAdminAnalytics({ autoFetch: false }));

    await act(async () => {
      await result.current.fetchPlatformStats();
    });

    expect(adminService.getPlatformStats).toHaveBeenCalled();
    expect(result.current.platformStats).toEqual(mockPlatformStats);
  });
});

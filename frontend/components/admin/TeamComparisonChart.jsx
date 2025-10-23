import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, Activity, Award } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import adminService from '../../services/adminService.js';

/**
 * Team comparison chart showing performance metrics across teams
 * Requirements: 9.1, 9.2, 9.3, 9.4
 */
const TeamComparisonChart = ({ dateRange, teamId, onError, onSuccess, currentUser }) => {
     const [teamsData, setTeamsData] = useState([]);
     const [loading, setLoading] = useState(false);
     const [viewMode, setViewMode] = useState('bar'); // bar, radar, table
     const [sortBy, setSortBy] = useState('total_reviews');
     const [sortOrder, setSortOrder] = useState('desc');

     const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

     useEffect(() => {
          loadTeamComparison();
     }, [dateRange, teamId]);

     const loadTeamComparison = async () => {
          try {
               setLoading(true);
               const response = await adminService.getTeamComparison({ 
                    dateRange, 
                    teamId: teamId // Pass team filter to API call
               });
               setTeamsData(response.teams || []);
          } catch (error) {
               onError(error);
          } finally {
               setLoading(false);
          }
     };

     const formatNumber = (num) => {
          if (num >= 1000000) {
               return (num / 1000000).toFixed(1) + 'M';
          } else if (num >= 1000) {
               return (num / 1000).toFixed(1) + 'K';
          }
          return num?.toString() || '0';
     };

     const formatPercentage = (value) => {
          return `${(value * 100).toFixed(1)}%`;
     };

     const sortedTeams = [...teamsData].sort((a, b) => {
          const aValue = a[sortBy] || 0;
          const bValue = b[sortBy] || 0;
          return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
     });

     // Prepare data for radar chart
     const radarData = teamsData.slice(0, 5).map(team => ({
          team: team.team_name,
          reviews: team.total_reviews || 0,
          acceptance: (team.feedback_acceptance_rate || 0) * 100,
          quality: ((team.avg_issues_per_review || 0) > 0 ? 100 / team.avg_issues_per_review : 100),
          activity: team.active_members || 0
     }));

     const viewModes = [
          { id: 'bar', label: 'Bar Chart', icon: BarChart3 },
          { id: 'radar', label: 'Radar Chart', icon: Activity },
          { id: 'table', label: 'Table View', icon: Users }
     ];

     const sortOptions = [
          { value: 'total_reviews', label: 'Total Reviews' },
          { value: 'avg_issues_per_review', label: 'Avg Issues' },
          { value: 'feedback_acceptance_rate', label: 'Acceptance Rate' },
          { value: 'active_members', label: 'Active Members' }
     ];

     return (
          <div className="space-y-6">
               {/* Header */}
               <div className="bg-white rounded-lg shadow-sm border p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                         <div>
                              <h3 className="text-lg font-medium text-gray-900">Team Performance Comparison</h3>
                              <p className="text-gray-600 mt-1">Compare metrics across all teams</p>
                         </div>

                         <div className="flex items-center space-x-3">
                              {/* View Mode Selector */}
                              <div className="flex space-x-1 bg-gray-100 rounded-md p-1">
                                   {viewModes.map((mode) => {
                                        const Icon = mode.icon;
                                        return (
                                             <button
                                                  key={mode.id}
                                                  onClick={() => setViewMode(mode.id)}
                                                  className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                                                       viewMode === mode.id
                                                            ? 'bg-white text-blue-600 shadow-sm'
                                                            : 'text-gray-600 hover:text-gray-900'
                                                  }`}
                                                  title={mode.label}
                                             >
                                                  <Icon className="h-4 w-4" />
                                             </button>
                                        );
                                   })}
                              </div>

                              {/* Sort Options */}
                              {viewMode === 'table' && (
                                   <select
                                        value={sortBy}
                                        onChange={(e) => setSortBy(e.target.value)}
                                        className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                   >
                                        {sortOptions.map((option) => (
                                             <option key={option.value} value={option.value}>
                                                  Sort by {option.label}
                                             </option>
                                        ))}
                                   </select>
                              )}
                         </div>
                    </div>
               </div>

               {loading ? (
                    <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                         <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                         <p className="text-gray-600 mt-4">Loading team comparison...</p>
                    </div>
               ) : teamsData.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                         <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                         <h3 className="text-lg font-medium text-gray-900 mb-2">No Team Data</h3>
                         <p className="text-gray-600">No team data available for comparison</p>
                    </div>
               ) : (
                    <>
                         {/* Bar Chart View */}
                         {viewMode === 'bar' && (
                              <div className="bg-white rounded-lg shadow-sm border p-6">
                                   <h3 className="text-lg font-medium text-gray-900 mb-4">Reviews by Team</h3>
                                   <div className="h-96">
                                        <ResponsiveContainer width="100%" height="100%">
                                             <BarChart data={teamsData}>
                                                  <CartesianGrid strokeDasharray="3 3" />
                                                  <XAxis
                                                       dataKey="team_name"
                                                       tick={{ fontSize: 12 }}
                                                       angle={-45}
                                                       textAnchor="end"
                                                       height={100}
                                                  />
                                                  <YAxis tick={{ fontSize: 12 }} />
                                                  <Tooltip
                                                       formatter={(value, name) => [
                                                            name === 'total_reviews' ? value :
                                                                 name === 'feedback_acceptance_rate' ? formatPercentage(value) :
                                                                      value.toFixed(2),
                                                            name === 'total_reviews' ? 'Total Reviews' :
                                                                 name === 'avg_issues_per_review' ? 'Avg Issues' :
                                                                      name === 'feedback_acceptance_rate' ? 'Acceptance Rate' :
                                                                           name
                                                       ]}
                                                  />
                                                  <Legend />
                                                  <Bar dataKey="total_reviews" fill="#3B82F6" name="Total Reviews" />
                                                  <Bar dataKey="avg_issues_per_review" fill="#F59E0B" name="Avg Issues" />
                                             </BarChart>
                                        </ResponsiveContainer>
                                   </div>
                              </div>
                         )}

                         {/* Radar Chart View */}
                         {viewMode === 'radar' && radarData.length > 0 && (
                              <div className="bg-white rounded-lg shadow-sm border p-6">
                                   <h3 className="text-lg font-medium text-gray-900 mb-4">Team Performance Radar (Top 5)</h3>
                                   <div className="h-96">
                                        <ResponsiveContainer width="100%" height="100%">
                                             <RadarChart data={radarData}>
                                                  <PolarGrid />
                                                  <PolarAngleAxis dataKey="team" tick={{ fontSize: 12 }} />
                                                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                                                  <Tooltip />
                                                  <Legend />
                                                  <Radar
                                                       name="Reviews"
                                                       dataKey="reviews"
                                                       stroke="#3B82F6"
                                                       fill="#3B82F6"
                                                       fillOpacity={0.3}
                                                  />
                                                  <Radar
                                                       name="Acceptance %"
                                                       dataKey="acceptance"
                                                       stroke="#10B981"
                                                       fill="#10B981"
                                                       fillOpacity={0.3}
                                                  />
                                                  <Radar
                                                       name="Code Quality"
                                                       dataKey="quality"
                                                       stroke="#F59E0B"
                                                       fill="#F59E0B"
                                                       fillOpacity={0.3}
                                                  />
                                             </RadarChart>
                                        </ResponsiveContainer>
                                   </div>
                              </div>
                         )}

                         {/* Table View */}
                         {viewMode === 'table' && (
                              <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
                                   <div className="overflow-x-auto">
                                        <table className="min-w-full divide-y divide-gray-200">
                                             <thead className="bg-gray-50">
                                                  <tr>
                                                       <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Rank
                                                       </th>
                                                       <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Team
                                                       </th>
                                                       <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Members
                                                       </th>
                                                       <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Total Reviews
                                                       </th>
                                                       <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Avg Issues
                                                       </th>
                                                       <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Acceptance Rate
                                                       </th>
                                                       <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Active Members
                                                       </th>
                                                  </tr>
                                             </thead>
                                             <tbody className="bg-white divide-y divide-gray-200">
                                                  {sortedTeams.map((team, index) => (
                                                       <tr key={team.team_id} className="hover:bg-gray-50 transition-colors">
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                 <div className="flex items-center">
                                                                      {index < 3 ? (
                                                                           <Award className={`h-5 w-5 ${
                                                                                index === 0 ? 'text-yellow-500' :
                                                                                     index === 1 ? 'text-gray-400' :
                                                                                          'text-orange-600'
                                                                           }`} />
                                                                      ) : (
                                                                           <span className="text-sm font-medium text-gray-500">
                                                                                #{index + 1}
                                                                           </span>
                                                                      )}
                                                                 </div>
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                 <div className="text-sm font-medium text-gray-900">
                                                                      {team.team_name}
                                                                 </div>
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                                 {team.member_count || 0}
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                 <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                                                                      {formatNumber(team.total_reviews || 0)}
                                                                 </span>
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                 <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                                                      (team.avg_issues_per_review || 0) > 5 ? 'bg-red-100 text-red-800' :
                                                                           (team.avg_issues_per_review || 0) > 2 ? 'bg-yellow-100 text-yellow-800' :
                                                                                'bg-green-100 text-green-800'
                                                                 }`}>
                                                                      {(team.avg_issues_per_review || 0).toFixed(1)}
                                                                 </span>
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap">
                                                                 <div className="flex items-center">
                                                                      <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                                                           <div
                                                                                className="bg-green-500 h-2 rounded-full"
                                                                                style={{
                                                                                     width: `${(team.feedback_acceptance_rate || 0) * 100}%`
                                                                                }}
                                                                           ></div>
                                                                      </div>
                                                                      <span className="text-sm font-medium text-gray-900">
                                                                           {formatPercentage(team.feedback_acceptance_rate || 0)}
                                                                      </span>
                                                                 </div>
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                                 {team.active_members || 0} / {team.member_count || 0}
                                                            </td>
                                                       </tr>
                                                  ))}
                                             </tbody>
                                        </table>
                                   </div>
                              </div>
                         )}

                         {/* Summary Statistics */}
                         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                              <div className="bg-white rounded-lg shadow-sm border p-6">
                                   <div className="flex items-center">
                                        <div className="bg-blue-100 rounded-full p-3">
                                             <Users className="h-6 w-6 text-blue-600" />
                                        </div>
                                        <div className="ml-4">
                                             <p className="text-sm font-medium text-gray-600">Total Teams</p>
                                             <p className="text-2xl font-bold text-gray-900">
                                                  {teamsData.length}
                                             </p>
                                        </div>
                                   </div>
                              </div>

                              <div className="bg-white rounded-lg shadow-sm border p-6">
                                   <div className="flex items-center">
                                        <div className="bg-green-100 rounded-full p-3">
                                             <Activity className="h-6 w-6 text-green-600" />
                                        </div>
                                        <div className="ml-4">
                                             <p className="text-sm font-medium text-gray-600">Total Reviews</p>
                                             <p className="text-2xl font-bold text-gray-900">
                                                  {formatNumber(teamsData.reduce((sum, team) => sum + (team.total_reviews || 0), 0))}
                                             </p>
                                        </div>
                                   </div>
                              </div>

                              <div className="bg-white rounded-lg shadow-sm border p-6">
                                   <div className="flex items-center">
                                        <div className="bg-yellow-100 rounded-full p-3">
                                             <TrendingUp className="h-6 w-6 text-yellow-600" />
                                        </div>
                                        <div className="ml-4">
                                             <p className="text-sm font-medium text-gray-600">Avg Acceptance</p>
                                             <p className="text-2xl font-bold text-gray-900">
                                                  {formatPercentage(
                                                       teamsData.reduce((sum, team) => sum + (team.feedback_acceptance_rate || 0), 0) / teamsData.length
                                                  )}
                                             </p>
                                        </div>
                                   </div>
                              </div>

                              <div className="bg-white rounded-lg shadow-sm border p-6">
                                   <div className="flex items-center">
                                        <div className="bg-purple-100 rounded-full p-3">
                                             <Award className="h-6 w-6 text-purple-600" />
                                        </div>
                                        <div className="ml-4">
                                             <p className="text-sm font-medium text-gray-600">Top Team</p>
                                             <p className="text-lg font-bold text-gray-900 truncate">
                                                  {sortedTeams[0]?.team_name || 'N/A'}
                                             </p>
                                        </div>
                                   </div>
                              </div>
                         </div>
                    </>
               )}
          </div>
     );
};

export default TeamComparisonChart;

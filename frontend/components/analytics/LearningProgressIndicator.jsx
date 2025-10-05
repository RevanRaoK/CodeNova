import React from 'react';
import {
     ResponsiveContainer,
     LineChart,
     Line,
     XAxis,
     YAxis,
     CartesianGrid,
     Tooltip,
     Legend,
     RadialBarChart,
     RadialBar,
     PieChart,
     Pie,
     Cell
} from 'recharts';
import { BrainIcon, TrendingUpIcon, CheckCircleIcon, AlertCircleIcon } from 'lucide-react';

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6'];

export function LearningProgressIndicator({ data, loading = false }) {
     // Transform data for charts
     const modelVersionsData = data.modelVersions?.map((item, index) => ({
          version: item.version,
          accuracy: item.accuracy * 100,
          precision: item.precision * 100,
          recall: item.recall * 100,
          f1Score: item.f1Score * 100,
          feedbackCount: item.feedbackCount,
          isActive: item.isActive,
          trainingDate: item.trainingDate,
          color: COLORS[index % COLORS.length]
     })) || [];

     const learningTrendsData = data.learningTrends?.map(item => ({
          date: item.date,
          accuracy: item.accuracy * 100,
          feedbackVolume: item.feedbackVolume,
          modelVersion: item.modelVersion,
          formattedDate: formatDate(item.date)
     })) || [];

     // Current model data for radial chart
     const currentModel = modelVersionsData.find(model => model.isActive) || modelVersionsData[0];
     const radialData = currentModel ? [
          { name: 'Accuracy', value: currentModel.accuracy, fill: '#10B981' },
          { name: 'Precision', value: currentModel.precision, fill: '#3B82F6' },
          { name: 'Recall', value: currentModel.recall, fill: '#F59E0B' },
          { name: 'F1 Score', value: currentModel.f1Score, fill: '#8B5CF6' }
     ] : [];

     const CustomTooltip = ({ active, payload, label }) => {
          if (active && payload && payload.length) {
               return (
                    <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                         <p className="font-medium mb-2">{label}</p>
                         {payload.map((entry, index) => (
                              <p key={index} className="text-sm" style={{ color: entry.color }}>
                                   {entry.name}: <span className="font-medium">{entry.value.toFixed(1)}</span>
                                   {entry.name !== 'Feedback Volume' && '%'}
                              </p>
                         ))}
                    </div>
               );
          }
          return null;
     };

     const CustomRadialTooltip = ({ active, payload }) => {
          if (active && payload && payload.length) {
               const data = payload[0];
               return (
                    <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                         <p className="font-medium">{data.payload.name}</p>
                         <p className="text-sm text-gray-600">
                              Score: <span className="font-medium">{data.value.toFixed(1)}%</span>
                         </p>
                    </div>
               );
          }
          return null;
     };

     if (loading) {
          return (
               <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                    <div className="animate-pulse">
                         <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                         <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                         <div className="h-64 bg-gray-200 rounded"></div>
                    </div>
               </div>
          );
     }

     return (
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
               <div className="mb-4">
                    <h3 className="text-lg font-medium text-gray-900 flex items-center">
                         <BrainIcon className="h-5 w-5 mr-2 text-purple-600" />
                         Learning Progress
                    </h3>
                    <p className="text-sm text-gray-500">
                         AI model performance and improvement metrics
                    </p>
               </div>

               {modelVersionsData.length === 0 ? (
                    <div className="h-64 flex items-center justify-center text-gray-500">
                         <div className="text-center">
                              <p className="text-lg font-medium">No learning data</p>
                              <p className="text-sm">No model performance data available</p>
                         </div>
                    </div>
               ) : (
                    <div className="space-y-6">
                         {/* Current Model Performance - Radial Chart */}
                         {currentModel && (
                              <div className="h-48">
                                   <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                        Current Model Performance
                                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                             {currentModel.version}
                                        </span>
                                   </h4>
                                   <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full">
                                        {/* Radial Chart */}
                                        <div className="h-full">
                                             <ResponsiveContainer width="100%" height="100%">
                                                  <RadialBarChart
                                                       cx="50%"
                                                       cy="50%"
                                                       innerRadius="20%"
                                                       outerRadius="80%"
                                                       data={radialData}
                                                  >
                                                       <RadialBar
                                                            minAngle={15}
                                                            label={{ position: 'insideStart', fill: '#fff', fontSize: 12 }}
                                                            background
                                                            clockWise
                                                            dataKey="value"
                                                       />
                                                       <Tooltip content={<CustomRadialTooltip />} />
                                                  </RadialBarChart>
                                             </ResponsiveContainer>
                                        </div>

                                        {/* Metrics List */}
                                        <div className="flex flex-col justify-center space-y-3">
                                             {radialData.map((metric, index) => (
                                                  <div key={index} className="flex items-center justify-between">
                                                       <div className="flex items-center">
                                                            <div
                                                                 className="w-3 h-3 rounded-full mr-2"
                                                                 style={{ backgroundColor: metric.fill }}
                                                            ></div>
                                                            <span className="text-sm text-gray-700">{metric.name}</span>
                                                       </div>
                                                       <span className="text-sm font-medium text-gray-900">
                                                            {metric.value.toFixed(1)}%
                                                       </span>
                                                  </div>
                                             ))}
                                        </div>
                                   </div>
                              </div>
                         )}

                         {/* Learning Trends */}
                         {learningTrendsData.length > 0 && (
                              <div className="h-64">
                                   <h4 className="text-sm font-medium text-gray-700 mb-2">Learning Trends</h4>
                                   <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={learningTrendsData}>
                                             <CartesianGrid strokeDasharray="3 3" />
                                             <XAxis
                                                  dataKey="formattedDate"
                                                  tick={{ fontSize: 12 }}
                                                  angle={-45}
                                                  textAnchor="end"
                                                  height={60}
                                             />
                                             <YAxis
                                                  yAxisId="accuracy"
                                                  domain={[0, 100]}
                                                  tick={{ fontSize: 12 }}
                                                  label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
                                             />
                                             <YAxis
                                                  yAxisId="feedback"
                                                  orientation="right"
                                                  tick={{ fontSize: 12 }}
                                                  label={{ value: 'Feedback Volume', angle: 90, position: 'insideRight' }}
                                             />
                                             <Tooltip content={<CustomTooltip />} />
                                             <Legend />
                                             <Line
                                                  yAxisId="accuracy"
                                                  type="monotone"
                                                  dataKey="accuracy"
                                                  stroke="#10B981"
                                                  strokeWidth={2}
                                                  dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                                                  name="Accuracy"
                                             />
                                             <Line
                                                  yAxisId="feedback"
                                                  type="monotone"
                                                  dataKey="feedbackVolume"
                                                  stroke="#8B5CF6"
                                                  strokeWidth={2}
                                                  dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
                                                  name="Feedback Volume"
                                             />
                                        </LineChart>
                                   </ResponsiveContainer>
                              </div>
                         )}

                         {/* Model Versions Comparison */}
                         {modelVersionsData.length > 1 && (
                              <div className="h-64">
                                   <h4 className="text-sm font-medium text-gray-700 mb-2">Model Versions Comparison</h4>
                                   <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={modelVersionsData}>
                                             <CartesianGrid strokeDasharray="3 3" />
                                             <XAxis
                                                  dataKey="version"
                                                  tick={{ fontSize: 12 }}
                                                  angle={-45}
                                                  textAnchor="end"
                                                  height={60}
                                             />
                                             <YAxis
                                                  domain={[0, 100]}
                                                  tick={{ fontSize: 12 }}
                                                  label={{ value: 'Performance (%)', angle: -90, position: 'insideLeft' }}
                                             />
                                             <Tooltip content={<CustomTooltip />} />
                                             <Legend />
                                             <Line
                                                  type="monotone"
                                                  dataKey="accuracy"
                                                  stroke="#10B981"
                                                  strokeWidth={2}
                                                  dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                                                  name="Accuracy"
                                             />
                                             <Line
                                                  type="monotone"
                                                  dataKey="precision"
                                                  stroke="#3B82F6"
                                                  strokeWidth={2}
                                                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                                                  name="Precision"
                                             />
                                             <Line
                                                  type="monotone"
                                                  dataKey="recall"
                                                  stroke="#F59E0B"
                                                  strokeWidth={2}
                                                  dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
                                                  name="Recall"
                                             />
                                             <Line
                                                  type="monotone"
                                                  dataKey="f1Score"
                                                  stroke="#8B5CF6"
                                                  strokeWidth={2}
                                                  dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
                                                  name="F1 Score"
                                             />
                                        </LineChart>
                                   </ResponsiveContainer>
                              </div>
                         )}
                    </div>
               )}

               {/* Improvement Metrics */}
               {data.improvementMetrics && (
                    <div className="mt-6 pt-4 border-t border-gray-200">
                         <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                              <TrendingUpIcon className="h-4 w-4 mr-1" />
                              Improvement Metrics
                         </h4>
                         <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div className="text-center p-3 bg-green-50 rounded-lg">
                                   <div className="flex items-center justify-center mb-1">
                                        {data.improvementMetrics.accuracyImprovement >= 0 ? (
                                             <CheckCircleIcon className="h-4 w-4 text-green-600" />
                                        ) : (
                                             <AlertCircleIcon className="h-4 w-4 text-red-600" />
                                        )}
                                   </div>
                                   <p className={`text-lg font-semibold ${data.improvementMetrics.accuracyImprovement >= 0 ? 'text-green-900' : 'text-red-900'
                                        }`}>
                                        {data.improvementMetrics.accuracyImprovement >= 0 ? '+' : ''}
                                        {(data.improvementMetrics.accuracyImprovement * 100).toFixed(1)}%
                                   </p>
                                   <p className="text-sm text-gray-500">Accuracy</p>
                              </div>

                              <div className="text-center p-3 bg-blue-50 rounded-lg">
                                   <div className="flex items-center justify-center mb-1">
                                        {data.improvementMetrics.precisionImprovement >= 0 ? (
                                             <CheckCircleIcon className="h-4 w-4 text-blue-600" />
                                        ) : (
                                             <AlertCircleIcon className="h-4 w-4 text-red-600" />
                                        )}
                                   </div>
                                   <p className={`text-lg font-semibold ${data.improvementMetrics.precisionImprovement >= 0 ? 'text-blue-900' : 'text-red-900'
                                        }`}>
                                        {data.improvementMetrics.precisionImprovement >= 0 ? '+' : ''}
                                        {(data.improvementMetrics.precisionImprovement * 100).toFixed(1)}%
                                   </p>
                                   <p className="text-sm text-gray-500">Precision</p>
                              </div>

                              <div className="text-center p-3 bg-yellow-50 rounded-lg">
                                   <div className="flex items-center justify-center mb-1">
                                        {data.improvementMetrics.recallImprovement >= 0 ? (
                                             <CheckCircleIcon className="h-4 w-4 text-yellow-600" />
                                        ) : (
                                             <AlertCircleIcon className="h-4 w-4 text-red-600" />
                                        )}
                                   </div>
                                   <p className={`text-lg font-semibold ${data.improvementMetrics.recallImprovement >= 0 ? 'text-yellow-900' : 'text-red-900'
                                        }`}>
                                        {data.improvementMetrics.recallImprovement >= 0 ? '+' : ''}
                                        {(data.improvementMetrics.recallImprovement * 100).toFixed(1)}%
                                   </p>
                                   <p className="text-sm text-gray-500">Recall</p>
                              </div>

                              <div className="text-center p-3 bg-purple-50 rounded-lg">
                                   <div className="flex items-center justify-center mb-1">
                                        {data.improvementMetrics.f1Improvement >= 0 ? (
                                             <CheckCircleIcon className="h-4 w-4 text-purple-600" />
                                        ) : (
                                             <AlertCircleIcon className="h-4 w-4 text-red-600" />
                                        )}
                                   </div>
                                   <p className={`text-lg font-semibold ${data.improvementMetrics.f1Improvement >= 0 ? 'text-purple-900' : 'text-red-900'
                                        }`}>
                                        {data.improvementMetrics.f1Improvement >= 0 ? '+' : ''}
                                        {(data.improvementMetrics.f1Improvement * 100).toFixed(1)}%
                                   </p>
                                   <p className="text-sm text-gray-500">F1 Score</p>
                              </div>
                         </div>
                    </div>
               )}

               {/* Model Versions Summary */}
               {modelVersionsData.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                         <h4 className="text-sm font-medium text-gray-700 mb-2">Model Versions</h4>
                         <div className="space-y-2">
                              {modelVersionsData.slice(0, 3).map((model, index) => (
                                   <div key={index} className={`flex items-center justify-between p-2 rounded ${model.isActive ? 'bg-green-50 border border-green-200' : 'bg-gray-50'
                                        }`}>
                                        <div className="flex items-center">
                                             <span className={`text-sm font-medium ${model.isActive ? 'text-green-900' : 'text-gray-900'
                                                  }`}>
                                                  {model.version}
                                             </span>
                                             {model.isActive && (
                                                  <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                       Active
                                                  </span>
                                             )}
                                        </div>
                                        <div className="text-right">
                                             <span className="text-sm font-medium text-gray-900">
                                                  {model.accuracy.toFixed(1)}%
                                             </span>
                                             <span className="text-xs text-gray-500 ml-1">accuracy</span>
                                        </div>
                                   </div>
                              ))}
                         </div>
                    </div>
               )}
          </div>
     );
}

function formatDate(dateString) {
     const date = new Date(dateString);
     return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
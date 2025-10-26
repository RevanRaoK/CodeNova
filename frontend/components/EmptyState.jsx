import React from 'react';

/**
 * Reusable empty state component for displaying when no data is available
 * Requirements: 1.6, 3.3, 12.3
 */
const EmptyState = ({ 
     icon: Icon, 
     title, 
     description, 
     actionText, 
     onAction, 
     className = "" 
}) => {
     return (
          <div className={`text-center py-12 ${className}`}>
               {Icon && (
                    <Icon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
               )}
               <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
               <p className="text-gray-600 mb-4">{description}</p>
               {actionText && onAction && (
                    <button
                         onClick={onAction}
                         className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                    >
                         {actionText}
                    </button>
               )}
          </div>
     );
};

export default EmptyState;
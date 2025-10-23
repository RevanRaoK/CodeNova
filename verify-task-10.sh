#!/bin/bash

# Verification script for Task 10 implementation
# Checks that all required files exist

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

passed=0
failed=0

echo -e "${BLUE}=== Task 10 Implementation Verification ===${NC}\n"

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((passed++))
    else
        echo -e "${RED}✗${NC} $2 - File not found: $1"
        ((failed++))
    fi
}

check_content() {
    if [ -f "$1" ]; then
        if grep -q "$2" "$1"; then
            echo -e "${GREEN}✓${NC} $3"
            ((passed++))
        else
            echo -e "${RED}✗${NC} $3 - Missing: $2"
            ((failed++))
        fi
    else
        echo -e "${RED}✗${NC} $3 - File not found: $1"
        ((failed++))
    fi
}

# Check new components
echo -e "${YELLOW}Checking new components...${NC}"
check_file "frontend/components/FileUploadIntegration.jsx" "FileUploadIntegration component"
check_file "frontend/components/FeedbackLearningIntegration.jsx" "FeedbackLearningIntegration component"
check_file "frontend/components/LoadingState.jsx" "LoadingState component"
check_file "frontend/pages/IntegrationDemo.jsx" "IntegrationDemo page"

# Check modified files
echo -e "\n${YELLOW}Checking modified files...${NC}"
check_file "frontend/src/App.tsx" "App.tsx exists"
check_file "frontend/components/ProtectedRoute.jsx" "ProtectedRoute.jsx exists"
check_file "frontend/components/AdminRouter.jsx" "AdminRouter.jsx exists"
check_file "frontend/components/Layout/Sidebar.jsx" "Sidebar.jsx exists"

# Check routing updates
echo -e "\n${YELLOW}Checking routing updates...${NC}"
check_content "frontend/src/App.tsx" "IntegrationDemo" "App.tsx imports IntegrationDemo"
check_content "frontend/src/App.tsx" "/integration-demo" "App.tsx has integration-demo route"
check_content "frontend/src/App.tsx" "/analysis-history" "App.tsx has analysis-history route"

# Check ProtectedRoute enhancements
echo -e "\n${YELLOW}Checking ProtectedRoute enhancements...${NC}"
check_content "frontend/components/ProtectedRoute.jsx" "allowedRoles" "ProtectedRoute has allowedRoles prop"
check_content "frontend/components/ProtectedRoute.jsx" "redirectTo" "ProtectedRoute has redirectTo prop"
check_content "frontend/components/ProtectedRoute.jsx" "Loader2" "ProtectedRoute uses Loader2 icon"

# Check Sidebar enhancements
echo -e "\n${YELLOW}Checking Sidebar enhancements...${NC}"
check_content "frontend/components/Layout/Sidebar.jsx" "isAdmin" "Sidebar has admin check"
check_content "frontend/components/Layout/Sidebar.jsx" "Administration" "Sidebar has Administration section"
check_content "frontend/components/Layout/Sidebar.jsx" "/analysis-history" "Sidebar has analysis-history link"

# Check AdminRouter updates
echo -e "\n${YELLOW}Checking AdminRouter updates...${NC}"
check_content "frontend/components/AdminRouter.jsx" "ProtectedRoute" "AdminRouter imports ProtectedRoute"
check_content "frontend/components/AdminRouter.jsx" "allowedRoles" "AdminRouter uses allowedRoles"

# Check FileUploadIntegration
echo -e "\n${YELLOW}Checking FileUploadIntegration...${NC}"
check_content "frontend/components/FileUploadIntegration.jsx" "uploadMultipleFiles" "FileUploadIntegration calls uploadMultipleFiles"
check_content "frontend/components/FileUploadIntegration.jsx" "pollBatchStatus" "FileUploadIntegration has pollBatchStatus"
check_content "frontend/components/FileUploadIntegration.jsx" "onAnalysisComplete" "FileUploadIntegration has onAnalysisComplete callback"

# Check FeedbackLearningIntegration
echo -e "\n${YELLOW}Checking FeedbackLearningIntegration...${NC}"
check_content "frontend/components/FeedbackLearningIntegration.jsx" "accept" "FeedbackLearningIntegration has accept feedback"
check_content "frontend/components/FeedbackLearningIntegration.jsx" "reject" "FeedbackLearningIntegration has reject feedback"
check_content "frontend/components/FeedbackLearningIntegration.jsx" "modify" "FeedbackLearningIntegration has modify feedback"
check_content "frontend/components/FeedbackLearningIntegration.jsx" "learningImpact" "FeedbackLearningIntegration shows learning impact"

# Check LoadingState
echo -e "\n${YELLOW}Checking LoadingState...${NC}"
check_content "frontend/components/LoadingState.jsx" "LoadingState" "LoadingState component exists"
check_content "frontend/components/LoadingState.jsx" "EmptyState" "EmptyState component exists"
check_content "frontend/components/LoadingState.jsx" "ErrorState" "ErrorState component exists"
check_content "frontend/components/LoadingState.jsx" "spinner" "LoadingState has spinner variant"
check_content "frontend/components/LoadingState.jsx" "skeleton" "LoadingState has skeleton variant"

# Check documentation
echo -e "\n${YELLOW}Checking documentation...${NC}"
check_file "frontend/ROUTING_NAVIGATION_GUIDE.md" "Routing guide documentation"
check_file "TASK_10_IMPLEMENTATION_SUMMARY.md" "Implementation summary"

# Summary
echo -e "\n${BLUE}=== Verification Summary ===${NC}\n"
echo -e "${GREEN}Passed: $passed${NC}"
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}Failed: $failed${NC}"
    echo -e "\n${GREEN}✓ All checks passed! Task 10 implementation is complete.${NC}"
    exit 0
else
    echo -e "${RED}Failed: $failed${NC}"
    echo -e "\n${RED}✗ Some checks failed. Please review the errors above.${NC}"
    exit 1
fi

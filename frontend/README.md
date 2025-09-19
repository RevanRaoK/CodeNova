# Intelligent Code Review Bot - Frontend

A modern React-based frontend for the AI-powered code review system with pattern learning capabilities.

## Tech Stack

- **React 18** with TypeScript for type safety
- **Vite** for fast development and optimized builds
- **Tailwind CSS** for utility-first styling
- **React Router v6** for client-side routing (to be added)
- **React Query** for server state management (to be added)
- **Zustand** for client-side state management (to be added)

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Basic UI components (Button, Input, etc.)
│   ├── forms/          # Form components
│   ├── layout/         # Layout components (Header, Footer, Sidebar)
│   └── common/         # Common components (Loading, Error, etc.)
├── pages/              # Page components
│   ├── auth/           # Authentication pages
│   ├── home/           # Home page
│   ├── review/         # Code review pages
│   ├── history/        # Review history
│   ├── patterns/       # Pattern learning
│   ├── profile/        # User profile
│   └── settings/       # Application settings
├── hooks/              # Custom React hooks
│   ├── api/            # API-related hooks
│   ├── auth/           # Authentication hooks
│   └── common/         # Utility hooks
├── services/           # API services and utilities
├── store/              # State management
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── constants/          # Application constants
```

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues

## Features

- 🎨 Modern UI with Tailwind CSS
- 📱 Responsive design for all devices
- ♿ Accessibility-first approach
- 🔒 JWT-based authentication
- 📝 Multiple code submission methods (editor, upload, GitHub)
- 📊 Pattern learning dashboard
- 📈 Review history and analytics
- ⚙️ User profile and settings management

## Configuration

### Tailwind CSS

Custom theme configuration with:
- Extended color palette for primary, secondary, success, warning, and error states
- Custom fonts (Inter for UI, JetBrains Mono for code)
- Responsive breakpoints
- Custom animations and utilities

### TypeScript

Strict mode enabled with:
- Type checking for unused variables and parameters
- Strict null checks
- No implicit any
- Path aliases (`@/` for `src/`)

### ESLint & Prettier

Configured for:
- React best practices
- TypeScript strict rules
- Consistent code formatting
- Import organization
# Personal Daily Reading Digest - Periscope

## Project Overview
Create a modern, professional web application UI for the Personal Daily Reading Digest platform: Periscope - a content curation service that helps busy professionals stay informed through personalized daily email digests from their preferred news sources and blogs.

## Core User Journey
Design interfaces for a busy professional who:
1. Signs up and configures preferred news sources (RSS feeds, blogs)
2. Sets delivery preferences (time, summary style)
3. Creates an interest profile with keywords
4. Receives and manages daily email digests
5. Monitors delivery status and adjusts settings

## Required Pages/Components

### 1. Landing Page
- **Hero Section**: Clear value proposition highlighting time-saving, personalization, and reliability
- **Features Grid**: Time-saving, personalized content, reliable delivery, AI-powered summarization
- **How It Works**: 3-step process (Configure → Receive → Stay Informed)
- **CTA**: "Start Your Free Digest" button
- **Modern, clean design** with professional color scheme

### 2. Authentication Pages
- **Sign Up Form**: Email, password, timezone selection
- **Login Form**: Email/password with "Remember me" option
- **Email Verification**: Confirmation message and resend option
- **Password Reset**: Email input and confirmation flow

### 3. Onboarding Flow
- **Welcome Screen**: Brief introduction to the platform
- **Source Configuration**:
  - Pre-populated popular RSS feeds (TechCrunch, BBC News, etc.)
  - Custom RSS/blog URL input with validation
  - Visual source cards with enable/disable toggles
  - Maximum 20 sources per user
- **Delivery Preferences**:
  - Time picker for daily delivery (with timezone display)
  - Summary style options (Brief, Detailed, Headlines Only)
- **Interest Profile Setup**:
  - Keyword input field with tags/chips display
  - Suggested keywords by category (Technology, Business, Science, etc.)
  - Maximum 50 keywords with counter
- **Setup Complete**: Summary of configuration with "Start Receiving Digests" CTA

### 4. Main Dashboard
- **Header**: Logo, user menu, settings icon
- **Status Overview Card**:
  - Next digest delivery time
  - Last successful delivery status
  - Quick stats (sources active, delivery success rate)
- **Recent Digests**:
  - List of last 7 digests with delivery status
  - Preview/view digest content option
- **Quick Actions**:
  - "Add Source" button
  - "Update Preferences" button
  - "View All Sources" button

### 5. Source Management
- **Active Sources Grid**:
  - Card layout showing source name, URL, status (active/error)
  - Last fetch timestamp
  - Enable/disable toggle
  - Remove source option
- **Add New Source Form**:
  - URL input with RSS/blog validation
  - Source name field (auto-populated from feed)
  - Test connection button
- **Source Details Modal**:
  - Recent articles preview
  - Fetch history and error logs
  - Source statistics

### 6. Settings & Preferences
- **Delivery Settings**:
  - Time picker with timezone display
  - Summary style radio buttons
  - Email format options (HTML/Plain text)
- **Interest Profile Management**:
  - Keyword tags with remove option
  - Add new keywords input
  - Keyword usage statistics
- **Account Settings**:
  - Email change (with verification)
  - Password change
  - Timezone update
  - Account deletion option

### 7. Digest Preview/History
- **Digest List**: Chronological list with date, delivery status, article count
- **Digest Content View**:
  - Email-style layout
  - Article summaries with source attribution
  - "Read Full Article" links
  - Interest category labels

## Design Requirements

### Visual Style
- **Modern, clean aesthetic** suitable for business professionals
- **Professional color palette**: Blues, grays, whites with accent colors
- **Typography**: Clean, readable fonts (Inter, Roboto, or similar)
- **Responsive design**: Mobile-first approach, works on desktop, tablet, mobile
- **Accessibility**: WCAG 2.1 AA compliance, proper contrast ratios

### UI Components Needed
- **Form inputs**: Text fields, dropdowns, time pickers, toggles
- **Cards**: For sources, digests, status information
- **Buttons**: Primary, secondary, icon buttons
- **Navigation**: Top navigation bar, breadcrumbs
- **Status indicators**: Success/error states, loading spinners
- **Modals**: For confirmations, detailed views
- **Tags/Chips**: For keywords and categories
- **Data tables**: For source lists, digest history

### UX Principles
- **Minimal cognitive load**: Clear information hierarchy
- **Progressive disclosure**: Show relevant information at the right time
- **Error prevention**: Input validation, clear error messages
- **Feedback**: Loading states, success confirmations, error handling
- **Efficiency**: Quick access to common actions, keyboard shortcuts

### Key User Flows to Optimize
1. **New user onboarding**: Should be completable in under 5 minutes
2. **Adding a new source**: One-click process with validation
3. **Updating preferences**: Quick access from dashboard
4. **Viewing digest status**: Clear visibility of delivery status and issues

### Mobile Considerations
- **Touch-friendly**: Buttons and interactive elements sized for touch
- **Simplified navigation**: Collapsible menu, swipe gestures where appropriate
- **Readable text**: Appropriate font sizes for mobile screens
- **Fast loading**: Optimized images and minimal data usage

### Data States to Design For
- **Empty states**: New user with no sources, no digest history
- **Loading states**: Source validation, digest generation in progress
- **Error states**: Failed source fetching, delivery failures
- **Success states**: Successful configuration, digest delivered

## Technical Constraints
- **Frontend Framework**: Designed for Svelte implementation
- **Build Tool**: Compatible with Vite
- **API Integration**: RESTful API endpoints
- **Real-time Updates**: Consider WebSocket integration for status updates

## Success Metrics to Design For
- **User Engagement**: Interface should encourage daily interaction
- **Configuration Completion**: Onboarding flow should have high completion rates
- **Error Recovery**: Clear paths to resolve configuration issues
- **User Retention**: Dashboard should provide value and encourage return visits

Create a complete, production-ready UI/UX design that balances professional aesthetics with user-friendly functionality, ensuring the platform serves busy professionals who need efficient, reliable access to their personalized content digests.
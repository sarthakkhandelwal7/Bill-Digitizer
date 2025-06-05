# Bill Digitizer Frontend

A modern React frontend for the Bill Digitizer application. Upload bill images and get structured data using AI.

## Features

-   **Drag & Drop Upload**: Easy bill image upload with drag and drop support
-   **Real-time Processing**: Live feedback during bill analysis
-   **Responsive Design**: Works on desktop, tablet, and mobile devices
-   **Modern UI**: Clean, professional interface using Tailwind CSS
-   **Bill Management**: View all processed bills with detailed breakdowns

## Technology Stack

-   **React 18**: Modern React with hooks
-   **Tailwind CSS**: Utility-first CSS framework
-   **React Router**: Client-side routing
-   **Axios**: HTTP client for API calls
-   **React Dropzone**: File upload with drag & drop
-   **Lucide React**: Beautiful icons
-   **Nginx**: Production web server

## Available Pages

### Home Page (`/`)

-   Main landing page with upload functionality
-   Drag & drop bill image upload
-   Feature highlights and instructions

### Bills Page (`/bills`)

-   List of all processed bills
-   Card-based layout with key information
-   Quick actions to view bill details

### Bill Detail Page (`/bills/:id`)

-   Detailed view of individual bills
-   Merchant information
-   Itemized breakdown
-   Payment and transaction details
-   Amount summary

## Development

The frontend is containerized and runs on port 3000. All API requests are automatically proxied to the backend service.

### Local URLs

-   **Frontend**: http://localhost:3000
-   **API (via proxy)**: http://localhost:3000/api/v1/
-   **Direct Backend**: http://localhost:8000

## API Integration

The frontend integrates with the FastAPI backend through:

-   **POST /api/v1/bills/analyze** - Upload and process bill images
-   **GET /api/v1/bills** - Retrieve all bills
-   **GET /api/v1/bills/{id}** - Get specific bill details

## Mobile Support

The application is responsive and works well on mobile devices. Future plans include:

-   Progressive Web App (PWA) features
-   React Native mobile app using shared components
-   Camera integration for direct photo capture

## File Structure

```
frontend/
├── public/           # Static files
├── src/
│   ├── components/   # Reusable components
│   ├── pages/        # Page components
│   ├── App.js        # Main app component
│   └── index.js      # Entry point
├── Dockerfile        # Container build instructions
├── nginx.conf        # Web server configuration
└── package.json      # Dependencies and scripts
```

# 🌍 Decarbonization Platform - Frontend Dashboard

A modern, professional carbon accounting dashboard for tracking, analyzing, and reducing organizational carbon emissions.

## ✨ Features

### Carbon Tracking & Analytics
- **Real-time Emissions Dashboard** - Live updates of total emissions and scope breakdowns
- **Interactive Visualizations** - Trend lines, pie charts, and category breakdowns
- **Scope 1, 2, 3 Breakdown** - Detailed analysis by emission categories
- **Historical Trends** - 6, 12, and 24-month trend analysis

### AI-Powered Insights
- **Carbon Copilot** - Natural language chatbot for data queries
- **Anomaly Detection** - Automatic detection of unusual emission patterns
- **Predictive Forecasting** - ML-powered emission predictions
- **Reduction Recommendations** - AI-suggested actions to reduce carbon footprint

### Reporting & Compliance
- **PDF Report Generation** - Professional stakeholder reports
- **Target Tracking** - Monitor progress toward net-zero goals
- **Audit Trail** - Complete transaction history for compliance

## 🎨 Design Features

- **Modern UI/UX** - Clean, professional interface inspired by Salesforce Net Zero Cloud
- **Glassmorphism Effects** - Premium visual design with frosted glass effects
- **Smooth Animations** - Polished micro-interactions and transitions
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **Dark Sidebar** - Professional navigation with gradient accents
- **Custom Color Palette** - HSL-based design tokens for easy theming

## 🚀 Quick Start

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Backend API running on `http://localhost:8000`

### Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd decarbonization-frontend
   ```

2. **Open in browser:**
   
   Simply open `index.html` in your browser, or use a local server:
   
   ```bash
   # Using Python
   python -m http.server 3000
   
   # Using Node.js
   npx http-server -p 3000
   
   # Using VS Code Live Server extension
   # Right-click index.html → "Open with Live Server"
   ```

3. **Access the dashboard:**
   ```
   http://localhost:3000
   ```

### First Time Login

If you don't have an account, register by:
1. Click "Register" on the login screen
2. Enter your email, username, password, and organization name
3. Submit to create your account
4. Login with your credentials

## 📁 Project Structure

```
decarbonization-frontend/
├── index.html              # Main application entry point
├── css/
│   └── styles.css         # Complete styling with design system
├── js/
│   ├── config.js          # API configuration
│   ├── auth.js            # Authentication service
│   ├── api.js             # API communication layer
│   ├── charts.js          # Chart.js configuration
│   └── main.js            # Main application logic
└── README.md              # This file
```

## 🔌 API Integration

The frontend connects to the backend API with the following endpoints:

### Authentication
- `POST /auth/token` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user

### Dashboard
- `GET /api/v1/dashboard` - Main dashboard data
- `GET /api/v1/emissions` - Emissions transactions
- `GET /api/v1/anomalies` - Detected anomalies
- `GET /api/v1/forecast` - Emission forecasts

### AI Features
- `POST /api/v1/copilot/query` - Ask AI copilot
- `GET /api/v1/targets/progress` - Target tracking

### Reports
- `GET /api/v1/reports/pdf` - Generate PDF report

## 🎯 Key Components

### Dashboard Pages

1. **Overview** - Main dashboard with key metrics and charts
2. **Emissions Data** - Detailed transaction-level tracking
3. **Targets & Goals** - Net-zero progress monitoring
4. **AI Copilot** - Interactive chat interface
5. **Reports** - Export and compliance documentation
6. **Insights** - AI recommendations and anomalies

### Charts

- **Trend Chart** - Line chart showing emissions over time
- **Scope Breakdown** - Doughnut chart of Scope 1, 2, 3
- **Category Analysis** - Horizontal bar chart of top categories

## 🎨 Customization

### Change Colors

Edit the CSS custom properties in `css/styles.css`:

```css
:root {
    --primary-hue: 158; /* Change to adjust primary color */
    --primary-500: hsl(var(--primary-hue), 64%, 50%);
    /* ... more color variables */
}
```

### Configure API

Update `js/config.js` to point to your backend:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://your-api-url.com',
    // ... other settings
};
```

## 📱 Responsive Breakpoints

- **Desktop**: > 1024px - Full sidebar and charts
- **Tablet**: 768px - 1024px - Adjusted layouts
- **Mobile**: < 768px - Collapsible sidebar, stacked charts

## 🔒 Security Features

- **JWT Authentication** - Secure token-based auth
- **Local Storage** - Encrypted token storage
- **Auto Logout** - Session expiry handling
- **Protected Routes** - Auth-required pages

## 🌐 Browser Support

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

## 📊 Technologies Used

- **HTML5** - Semantic markup
- **CSS3** - Modern styling with custom properties
- **JavaScript (ES6+)** - Vanilla JS, no framework overhead
- **Chart.js 4.x** - Interactive visualizations
- **Fetch API** - Modern HTTP requests
- **LocalStorage API** - Client-side state management

## 🎓 Development Tips

### Add New Pages

1. Add navigation item in `index.html`:
   ```html
   <li class="nav-item" data-page="newpage">...</li>
   ```

2. Add page container:
   ```html
   <div id="newpagePage" class="page"></div>
   ```

3. Implement in `main.js`:
   ```javascript
   loadNewpagePage() {
       // Page implementation
   }
   ```

### Add New API Endpoints

1. Update `config.js` with endpoint
2. Add method in `api.js`
3. Call from page logic in `main.js`

## 🐛 Troubleshooting

### Login Issues
- Check backend is running on port 8000
- Verify CORS is enabled in backend
- Check browser console for errors

### Charts Not Displaying
- Ensure Chart.js CDN is accessible
- Check data format matches expected structure
- Verify canvas elements exist in DOM

### API Errors
- Check network tab for failed requests
- Verify API base URL in config.js
- Ensure authentication token is valid

## 📝 License

Part of the Decarbonization Platform project.

## 🤝 Contributing

This is a demonstration project. For production use, consider:
- Adding comprehensive error handling
- Implementing data caching
- Adding unit tests
- Setting up proper build pipeline
- Implementing PWA features

## 📧 Support

For issues or questions about the Decarbonization Platform, please refer to the main project documentation.

---

Built with ❤️ for a sustainable future 🌱

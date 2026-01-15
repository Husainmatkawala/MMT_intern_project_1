# MMT Travel Experience System

A React-based frontend application for MakeMyTrip's Incentivized & Verified User Travel Experience System. Users can submit detailed travel experiences with proof validation to earn rewards.

## Features

- 📝 Comprehensive travel experience submission form
- 🏨 Hotel reviews with bill upload validation
- 📸 Attraction reviews with geo-tagged photo uploads
- 🍽️ Food & dining experiences
- 🚗 Local commute information
- 💰 Cost breakdown and budget tracking
- 🛡️ Safety tips and concerns
- ✨ Modern, blog-like UI with Tailwind CSS
- ✅ Form validation and file upload handling

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Icons** - Icon library

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
sample/
├── src/
│   ├── components/
│   │   └── TravelExperienceForm.jsx  # Main form component
│   ├── App.jsx                        # Root component
│   ├── main.jsx                       # Entry point
│   └── index.css                      # Global styles with Tailwind
├── index.html                         # HTML template
├── package.json                       # Dependencies
├── vite.config.js                     # Vite configuration
├── tailwind.config.js                 # Tailwind configuration
└── postcss.config.js                  # PostCSS configuration
```

## Form Sections

1. **Basic Information** - Title, destination, travel date
2. **Hotel Experience** - Hotel name, review, rating, bill upload (required if hotel mentioned)
3. **Attractions & Places** - Places visited, reviews, geo-tagged photos (required if places mentioned)
4. **Food & Dining** - Restaurants, food reviews, costs
5. **Local Commute** - Transportation modes, reviews, costs
6. **Travel Costs** - Total budget and breakdown
7. **Safety & Security** - Safety tips and concerns
8. **Travel Tips** - General recommendations
9. **Overall Experience** - Main review content (required)

## Validation Rules

- Title, destination, travel date, and overall experience are required
- If hotel name is provided, hotel bill upload is required
- If attractions are mentioned, at least one geo-tagged photo is required
- File uploads accept images (JPEG/PNG) and PDFs for bills
- Attraction photos accept image files only

## Future Enhancements

- Backend API integration
- Real-time form validation
- Image preview functionality
- Progress indicator for form completion
- Draft saving functionality
- Reward points display
- User authentication

## License

This project is created for MakeMyTrip's Travel Experience System.
